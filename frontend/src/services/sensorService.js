/**
 * Sensor collection service for accident detection.
 * Collects: Geolocation (lat, lng, speed), DeviceMotion (accelerometer), DeviceMotion.rotationRate (gyroscope)
 * Sends to backend every SEND_INTERVAL_MS when enabled.
 */
import { submitSensorReading } from '../api/sensorApi';

const SEND_INTERVAL_MS = 5000;
const ACCEL_SCALE = 1;   // m/s²
const GYRO_SCALE = 1;    // deg/s

let watchId = null;
let motionHandler = null;
let sendTimer = null;
let lastPosition = null;
let lastSpeed = 0;
let accel = { x: 0, y: 0, z: 0 };
let gyro = { x: 0, y: 0, z: 0 };
let enabled = false;

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
  const a = event.accelerationIncludingGravity || event.acceleration || {};
  accel.x = (a.x ?? 0) * ACCEL_SCALE;
  accel.y = (a.y ?? 0) * ACCEL_SCALE;
  accel.z = (a.z ?? 0) * ACCEL_SCALE;
  const r = event.rotationRate || {};
  gyro.x = (r.alpha ?? 0) * GYRO_SCALE;
  gyro.y = (r.beta ?? 0) * GYRO_SCALE;
  gyro.z = (r.gamma ?? 0) * GYRO_SCALE;
}

function sendReading() {
  if (!enabled || !lastPosition) return;
  const coords = lastPosition.coords;
  submitSensorReading({
    lat: coords.latitude,
    lng: coords.longitude,
    speed_kmh: lastSpeed || undefined,
    accel_x: accel.x || undefined,
    accel_y: accel.y || undefined,
    accel_z: accel.z || undefined,
    gyro_x: gyro.x || undefined,
    gyro_y: gyro.y || undefined,
    gyro_z: gyro.z || undefined,
  }).catch(() => {});
}

function start() {
  if (enabled) return;
  enabled = true;
  lastPosition = null;
  lastSpeed = 0;

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
}

export const sensorService = { start, stop, isEnabled: () => enabled };
