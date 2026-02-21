"""
Accident detection: load ML model and predict from sensor readings.
Uses rule-based fallback if model not found.

Detection paths:
  Path 0 (Demo): Frontend detected shake+stop → immediate trigger
  Path 1 (Shake+Stop): High accel spike + stopped 10s at same spot
  Path 2 (High Impact): Very high gyro + accel = strong impact/rotation
  Path 3 (Full): Speed drop + impact + tilt + stopped
"""
import math
from pathlib import Path

_MODEL_CACHE = None

def _load_model():
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    try:
        import joblib
        model_path = Path(__file__).resolve().parent / "accident_model.joblib"
        if model_path.exists():
            _MODEL_CACHE = joblib.load(model_path)
            return _MODEL_CACHE
    except Exception:
        pass
    return None

def extract_features(readings):
    """
    Extract feature vector from sensor readings window.
    readings: list of dicts with speed_kmh, accel_x/y/z, gyro_x/y/z, lat, lng, timestamp
    """
    if not readings:
        return None

    speeds = [r.get('speed_kmh') for r in readings if r.get('speed_kmh') is not None]
    max_speed = max(speeds) if speeds else 0
    min_speed = min(speeds) if speeds else 0
    speed_drop = max_speed - min_speed

    last_speeds = speeds[-3:] if len(speeds) >= 3 else speeds
    speed_drop_rate = (last_speeds[0] - last_speeds[-1]) / max(0.1, (len(last_speeds) - 1) * 2) if len(last_speeds) >= 2 else 0

    accel_mags = []
    for r in readings:
        ax = r.get('accel_x') or 0
        ay = r.get('accel_y') or 0
        az = r.get('accel_z') or 0
        accel_mags.append(math.sqrt(ax*ax + ay*ay + az*az))
    accel_spike = max(accel_mags) if accel_mags else 0

    # Also compute recent accel (last 3 readings) to detect if phone is NOW still
    recent_accel_mags = accel_mags[-3:] if len(accel_mags) >= 3 else accel_mags
    recent_accel_avg = sum(recent_accel_mags) / len(recent_accel_mags) if recent_accel_mags else 0

    gyro_mags = []
    for r in readings:
        gx = r.get('gyro_x') or 0
        gy = r.get('gyro_y') or 0
        gz = r.get('gyro_z') or 0
        gyro_mags.append(math.sqrt(gx*gx + gy*gy + gz*gz))
    gyro_spike = max(gyro_mags) if gyro_mags else 0

    timestamps = []
    for r in readings:
        ts = r.get('timestamp')
        if ts is not None:
            if hasattr(ts, 'timestamp'):
                timestamps.append(ts.timestamp())
            elif hasattr(ts, 'total_seconds'):
                timestamps.append(ts.total_seconds())
            elif isinstance(ts, (int, float)):
                timestamps.append(float(ts))
    window_span = (max(timestamps) - min(timestamps)) if len(timestamps) >= 2 else 0

    lats = [r.get('lat') for r in readings if r.get('lat') is not None]
    lngs = [r.get('lng') for r in readings if r.get('lng') is not None]
    if lats and lngs:
        lat_diff = (max(lats) - min(lats)) * 111320
        avg_lat = sum(lats) / len(lats)
        lng_diff = (max(lngs) - min(lngs)) * 111320 * math.cos(math.radians(avg_lat))
        location_change_m = math.sqrt(lat_diff**2 + lng_diff**2)
    else:
        location_change_m = 0

    # FIXED: Calculate seconds_stopped from the RECENT readings only
    # Look at last N readings where location barely changed
    # Instead of a binary 0/window_span, compute how long the phone has been
    # approximately in the same spot based on timestamps
    seconds_stopped = 0
    if len(timestamps) >= 2 and len(lats) >= 2 and len(lngs) >= 2:
        # Check location change using only the most recent readings
        # Use last half of readings to see if phone stopped recently
        half = max(len(readings) // 2, 1)
        recent_readings = readings[half:]
        recent_lats = [r.get('lat') for r in recent_readings if r.get('lat') is not None]
        recent_lngs = [r.get('lng') for r in recent_readings if r.get('lng') is not None]
        if recent_lats and recent_lngs:
            r_lat_diff = (max(recent_lats) - min(recent_lats)) * 111320
            r_avg_lat = sum(recent_lats) / len(recent_lats)
            r_lng_diff = (max(recent_lngs) - min(recent_lngs)) * 111320 * math.cos(math.radians(r_avg_lat))
            recent_loc_change = math.sqrt(r_lat_diff**2 + r_lng_diff**2)
        else:
            recent_loc_change = 0

        recent_ts = []
        for r in recent_readings:
            ts = r.get('timestamp')
            if ts is not None:
                if hasattr(ts, 'timestamp'):
                    recent_ts.append(ts.timestamp())
                elif isinstance(ts, (int, float)):
                    recent_ts.append(float(ts))

        if recent_loc_change < 50 and len(recent_ts) >= 2:
            seconds_stopped = max(recent_ts) - min(recent_ts)
        # Fallback: if overall location change is small and window is long enough
        elif location_change_m < 50 and window_span >= 10:
            seconds_stopped = window_span

    return [speed_drop, speed_drop_rate, accel_spike, gyro_spike, seconds_stopped, location_change_m, max_speed, min_speed]

def rule_based_predict(readings, shake_stop_flag=False):
    """
    Rule-based accident detection with multiple paths.
    Path 0 (Demo): Frontend-detected shake+stop → immediate trigger
    Path 1 (Shake+Stop): accel spike + stayed still 10s
    Path 2 (High Impact): gyro + accel extreme values
    Path 3 (Full): speed + impact + tilt + stopped
    """
    feat = extract_features(readings)
    if feat is None:
        return False, 0.0
    speed_drop, _, accel_spike, gyro_spike, seconds_stopped, loc_change, speed_before, _ = feat

    # Path 0 (DEMO): Frontend explicitly detected shake + stop for 10s
    # This is the most reliable path for demo because the frontend tracks it in real-time
    if shake_stop_flag:
        return True, 0.95

    # Path 1 (Shake+Stop): High accel (phone was shaken/impacted) + stopped 10s at same spot
    # Lowered accel threshold from 11 to 9.5 to be more sensitive to phone shaking
    if accel_spike >= 9.5 and seconds_stopped >= 8 and loc_change < 50:
        return True, 0.9

    # Path 2: Very high gyro + accel = strong impact/rotation
    if gyro_spike >= 50 and accel_spike >= 10:
        return True, 0.9

    # Path 3: Full conditions - movement, drop, spikes, stopped 10+ sec
    if speed_before >= 1 and speed_drop >= 1 and accel_spike >= 5 and gyro_spike >= 15 and seconds_stopped >= 10:
        return True, 0.9

    # Path 4: Moderate gyro + accel + stopped (relaxed thresholds for demo)
    if gyro_spike >= 10 and accel_spike >= 5 and seconds_stopped >= 8 and loc_change < 50:
        return True, 0.75

    # Path 5: Vehicle accident — large speed drop + high impact (doesn't need seconds_stopped)
    if speed_before >= 25 and speed_drop >= 20 and accel_spike >= 10:
        return True, 0.85

    return False, 0.0

def predict(readings, shake_stop_flag=False):
    """
    Predict if accident from sensor readings.
    Returns: (is_accident: bool, probability: float)

    shake_stop_flag: if True, frontend has already detected shake+stop pattern
    """
    # Path 0: If frontend detected shake+stop, trust it immediately
    if shake_stop_flag:
        return True, 0.95

    # Require minimum 3 readings for ML prediction to avoid false positives from tiny windows
    if len(readings) < 3:
        return rule_based_predict(readings, shake_stop_flag)

    model_data = _load_model()
    feat = extract_features(readings)
    if feat is None:
        return False, 0.0

    if model_data and 'model' in model_data:
        import numpy as np
        clf = model_data['model']
        X = np.array([feat])
        try:
            proba = clf.predict_proba(X)[0]
            idx = list(clf.classes_).index(1) if 1 in clf.classes_ else 0
            p = float(proba[idx])
            if p >= 0.5:
                return True, p
        except Exception:
            pass

    # Always fall through to rule-based (which also handles shake_stop_flag)
    return rule_based_predict(readings, shake_stop_flag)
