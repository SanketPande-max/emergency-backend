/**
 * Sensor collection service for accident detection.
 * Collects: Geolocation (lat, lng, speed), DeviceMotion (accelerometer), DeviceMotion.rotationRate (gyroscope)
 * Sends to backend every SEND_INTERVAL_MS when enabled.
 *
 * SHAKE+STOP detection:
 *  - Tracks recent accel magnitudes in a rolling window.
 *  - If a strong shake is detected (accel magnitude spike), records the shake time.
 *  - Once the phone becomes still (low accel) for STILL_DURATION_MS after a shake, sets shake_stop_detected=true.
 *  - The flag is sent to the backend so the detector can trigger emergency.
 */
import { submitSensorReading } from '../api/sensorApi';

const SEND_INTERVAL_MS = 3000;  // Send every 3s (was 5s) for faster detection
const ACCEL_SCALE = 1;   // m/s²
const GYRO_SCALE = 1;    // deg/s

// Shake detection config
const SHAKE_ACCEL_THRESHOLD = 15;     // m/s² magnitude to count as "shaking" (gravity ~9.8)
const STILL_ACCEL_THRESHOLD = 12;     // m/s² magnitude below which phone is "still" (close to gravity only)
const STILL_DURATION_MS = 10000;      // Phone must be still for 10 seconds after shake
const MOTION_STALE_MS = 1500;         // If no motion event for 1.5s, assume phone is still

let watchId = null;
let motionHandler = null;
let sendTimer = null;
let lastPosition = null;
let lastSpeed = 0;
let accel = { x: 0, y: 0, z: 0 };
let gyro = { x: 0, y: 0, z: 0 };
let enabled = false;

// Shake+stop tracking
let lastMotionEventTime = 0;
let shakeDetectedTime = 0;       // timestamp when last strong shake was detected
let stillStartTime = 0;          // timestamp when phone became still after shake
let shakeStopDetected = false;   // true = shake happened, then phone was still for 10s
let peakAccelMag = 0;            // peak accel magnitude in current window
let recentAccelMags = [];        // rolling window of [timestamp, magnitude]

function getSpeedFromPosition(prev, curr) {
  if (!prev?.coords || !curr?.coords) return null;
  const R = 6371000; // meters
  const lat1 = (prev.coords.latitude * Math.PI) / 180;
  const lat2 = (curr.coords.latitude * Math.PI) / 180;
  const dlat = ((curr.coords.latitude - prev.coords.latitude) * Math.PI) / 180;
  const dlng = ((curr.coords.longitude - prev.coords.longitude) * Math.PI) / 180;
  const a = Math.sin(dlat/2)**2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dlng/2)**2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  const distM = R * c;
  const timeSec = (curr.timestamp - prev.timestamp) / 1000;
  if (timeSec <= 0) return null;
  return (distM / 1000) / (timeSec / 3600); // km/h
}

function onPosition(position) {
  const prev = lastPosition;
  lastPosition = { coords: position.coords, timestamp: position.timestamp };
  let speedKmh = position.coords.speed != null ? position.coords.speed * 3.6 : null;
  if (speedKmh == null && prev) {
    speedKmh = getSpeedFromPosition(prev, lastPosition);
  }
  if (speedKmh != null) lastSpeed = speedKmh;
}

function onMotion(event) {
  const now = Date.now();
  lastMotionEventTime = now;

  const a = event.accelerationIncludingGravity || event.acceleration || {};
  accel.x = (a.x ?? 0) * ACCEL_SCALE;
  accel.y = (a.y ?? 0) * ACCEL_SCALE;
  accel.z = (a.z ?? 0) * ACCEL_SCALE;

  const r = event.rotationRate || {};
  gyro.x = (r.alpha ?? 0) * GYRO_SCALE;
  gyro.y = (r.beta ?? 0) * GYRO_SCALE;
  gyro.z = (r.gamma ?? 0) * GYRO_SCALE;

  // Calculate current accel magnitude
  const mag = Math.sqrt(accel.x ** 2 + accel.y ** 2 + accel.z ** 2);

  // Track in rolling window (keep last 30s)
  recentAccelMags.push([now, mag]);
  recentAccelMags = recentAccelMags.filter(([t]) => now - t < 30000);

  // Track peak
  if (mag > peakAccelMag) peakAccelMag = mag;

  // Detect shake: magnitude well above gravity (9.8 m/s²)
  if (mag >= SHAKE_ACCEL_THRESHOLD) {
    shakeDetectedTime = now;
    stillStartTime = 0;  // reset still timer when shaking
    shakeStopDetected = false;
  }

  // After a shake was detected, check if phone is now still
  if (shakeDetectedTime > 0 && mag < STILL_ACCEL_THRESHOLD) {
    if (stillStartTime === 0) {
      stillStartTime = now;
    }
    // Check if still for STILL_DURATION_MS
    if (now - stillStartTime >= STILL_DURATION_MS) {
      shakeStopDetected = true;
    }
  } else if (shakeDetectedTime > 0 && mag >= STILL_ACCEL_THRESHOLD) {
    // Phone is moving again — if it's a new shake, update shakeDetectedTime
    stillStartTime = 0;
    if (mag >= SHAKE_ACCEL_THRESHOLD) {
      shakeStopDetected = false; // reset if shaking again
    }
  }
}

function getCurrentAccelGyro() {
  const now = Date.now();
  // If no motion event recently, phone is still — decay values toward gravity-only
  if (lastMotionEventTime > 0 && (now - lastMotionEventTime) > MOTION_STALE_MS) {
    // Phone is still — report near-zero accel (above gravity) and zero gyro
    // Check if we had a shake before this stillness
    if (shakeDetectedTime > 0 && stillStartTime === 0) {
      stillStartTime = lastMotionEventTime;
    }
    if (shakeDetectedTime > 0 && stillStartTime > 0 && (now - stillStartTime) >= STILL_DURATION_MS) {
      shakeStopDetected = true;
    }
    return {
      accel_x: 0,
      accel_y: 0,
      accel_z: -9.8,  // gravity only = phone is still
      gyro_x: 0,
      gyro_y: 0,
      gyro_z: 0,
    };
  }
  return {
    accel_x: accel.x || undefined,
    accel_y: accel.y || undefined,
    accel_z: accel.z || undefined,
    gyro_x: gyro.x || undefined,
    gyro_y: gyro.y || undefined,
    gyro_z: gyro.z || undefined,
  };
}

function sendReading() {
  if (!enabled || !lastPosition) return;
  const coords = lastPosition.coords;
  const sensorValues = getCurrentAccelGyro();

  const payload = {
    lat: coords.latitude,
    lng: coords.longitude,
    speed_kmh: lastSpeed || 0,
    ...sensorValues,
    // Shake+stop flag for backend
    shake_stop_detected: shakeStopDetected,
    peak_accel: peakAccelMag,
  };

  submitSensorReading(payload)
    .then((res) => {
      // If emergency was created, reset shake tracking
      if (res?.data?.accident_detected && res?.data?.request_id) {
        resetShakeTracking();
      }
    })
    .catch(() => {});
}

function resetShakeTracking() {
  shakeDetectedTime = 0;
  stillStartTime = 0;
  shakeStopDetected = false;
  peakAccelMag = 0;
  recentAccelMags = [];
}

function start() {
  if (enabled) return;
  enabled = true;
  lastPosition = null;
  lastSpeed = 0;
  resetShakeTracking();

  if (navigator.geolocation) {
    watchId = navigator.geolocation.watchPosition(onPosition, () => {}, {
      enableHighAccuracy: true,
      maximumAge: 3000,
      timeout: 10000,
    });
  }

  if (typeof DeviceMotionEvent !== 'undefined') {
    if (typeof DeviceMotionEvent.requestPermission === 'function') {
      DeviceMotionEvent.requestPermission().then((p) => {
        if (p === 'granted') attachMotion();
      }).catch(() => attachMotion());
    } else {
      attachMotion();
    }
  }

  function attachMotion() {
    motionHandler = onMotion;
    window.addEventListener('devicemotion', motionHandler);
  }

  sendTimer = setInterval(sendReading, SEND_INTERVAL_MS);
}

function stop() {
  enabled = false;
  if (watchId != null && navigator.geolocation) {
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
  }
  if (motionHandler) {
    window.removeEventListener('devicemotion', motionHandler);
    motionHandler = null;
  }
  if (sendTimer) {
    clearInterval(sendTimer);
    sendTimer = null;
  }
  resetShakeTracking();
}

export const sensorService = { start, stop, isEnabled: () => enabled };
