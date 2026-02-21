"""
Accident detection: load ML model and predict from sensor readings.
Uses rule-based fallback if model not found.
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
    # For high-impact path (gyro+accel) we don't need speed; for full path we do
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

    # Stopped: little movement + enough time elapsed
    if location_change_m < 30 and window_span >= 10:
        seconds_stopped = window_span
    else:
        seconds_stopped = 0

    return [speed_drop, speed_drop_rate, accel_spike, gyro_spike, seconds_stopped, location_change_m, max_speed, min_speed]

def rule_based_predict(readings):
    feat = extract_features(readings)
    if feat is None:
        return False, 0.0

    speed_drop, _, accel_spike, gyro_spike, seconds_stopped, loc_change, speed_before, _ = feat

    # Step 1: Strong shake + rotation
    strong_motion = accel_spike >= 8 and gyro_spike >= 20

    # Step 2: Phone stopped for 5 seconds
    stopped_after = seconds_stopped >= 5 and loc_change < 20

    if strong_motion and stopped_after:
        return True, 0.98

    return False, 0.0

def predict(readings):
    """
    Predict if accident from sensor readings.
    Returns: (is_accident: bool, probability: float)
    """
    model_data = _load_model()
    feat = extract_features(readings)
    if feat is None:
        return False, 0.0

    if model_data and 'model' in model_data:
        import numpy as np
        clf = model_data['model']
        X = np.array([feat])
        proba = clf.predict_proba(X)[0]
        idx = list(clf.classes_).index(1) if 1 in clf.classes_ else 0
        p = float(proba[idx])
        return p >= 0.5, p

    return rule_based_predict(readings)
