"""
Train accident detection ML model on synthetic data.
Run: python -m ml.accident_train
Output: ml/accident_model.joblib
"""
import os
import sys
import random
import math
import numpy as np
from pathlib import Path

# Ensure project root in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def generate_synthetic_accident_sample():
    """Generate one accident sample: speed drop, accel spike, gyro spike, stopped 15s+."""
    # Before accident: speed 30-80 km/h
    speed_before = random.uniform(30, 80)
    # After: sudden drop to 0-5
    speed_after = random.uniform(0, 5)
    speed_drop = speed_before - speed_after
    speed_drop_rate = speed_drop / 3  # over ~3 sec

    # Accelerometer: high magnitude change (impact)
    accel_mag = random.uniform(15, 45)  # m/s^2 equivalent
    accel_x = random.gauss(0, 1) * accel_mag / 3
    accel_y = random.gauss(0, 1) * accel_mag / 3
    accel_z = random.gauss(-1, 0.5) * accel_mag / 3  # often downward
    accel_spike = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)

    # Gyroscope: tilt/rotation spike
    gyro_mag = random.uniform(2, 12)
    gyro_x = random.gauss(0, 1) * gyro_mag
    gyro_y = random.gauss(0, 1) * gyro_mag
    gyro_z = random.gauss(0, 1) * gyro_mag
    gyro_spike = math.sqrt(gyro_x**2 + gyro_y**2 + gyro_z**2)

    # Stopped at same location for 15+ sec
    seconds_stopped = random.uniform(15, 120)
    location_change_m = random.uniform(0, 5)  # minimal movement

    return [
        speed_drop,
        speed_drop_rate,
        accel_spike,
        gyro_spike,
        seconds_stopped,
        location_change_m,
        speed_before,
        speed_after,
    ]

def generate_synthetic_shake_stop_sample():
    """Generate one shake-at-standstill sample: phone shaken hard then stopped.
    Speed is ~0 (person standing/sitting), high accel, moderate gyro, stopped 10-60s.
    This represents the demo scenario where user shakes phone and places it down.
    """
    # Person is stationary - speed is near zero
    speed_before = random.uniform(0, 3)
    speed_after = random.uniform(0, 2)
    speed_drop = max(0, speed_before - speed_after)
    speed_drop_rate = speed_drop / 2

    # High accelerometer from shaking (above gravity ~9.8)
    accel_spike = random.uniform(10, 35)

    # Moderate gyroscope from rotation during shake
    gyro_spike = random.uniform(5, 40)

    # Phone stopped after shake for 10-60 sec
    seconds_stopped = random.uniform(10, 60)
    location_change_m = random.uniform(0, 10)  # person barely moves

    return [
        speed_drop,
        speed_drop_rate,
        accel_spike,
        gyro_spike,
        seconds_stopped,
        location_change_m,
        speed_before,
        speed_after,
    ]

def generate_synthetic_normal_sample():
    """Generate one normal driving sample: gradual changes, no impact."""
    # Normal speed variation
    speed = random.uniform(0, 80)
    speed_drop = random.uniform(-5, 5)  # small changes
    speed_drop_rate = random.uniform(-2, 2)

    # Low accel (normal driving)
    accel_spike = random.uniform(0, 8)

    # Low gyro
    gyro_spike = random.uniform(0, 2)

    # Either moving or short stop
    seconds_stopped = random.uniform(0, 8)
    location_change_m = random.uniform(0, 500)

    return [
        speed_drop,
        speed_drop_rate,
        accel_spike,
        gyro_spike,
        seconds_stopped,
        location_change_m,
        speed,
        max(0, speed + speed_drop),
    ]

def train_and_save(n_accidents=2000, n_shake_stop=1500, n_normal=4000):
    """Generate synthetic data including shake-stop samples, train model, save to joblib."""
    try:
        import joblib
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
    except ImportError:
        print("Install: pip install scikit-learn joblib")
        raise

    X_acc = [generate_synthetic_accident_sample() for _ in range(n_accidents)]
    X_shake = [generate_synthetic_shake_stop_sample() for _ in range(n_shake_stop)]
    X_norm = [generate_synthetic_normal_sample() for _ in range(n_normal)]

    # Both vehicle accidents and shake-stop are labeled as accident (1)
    X = np.array(X_acc + X_shake + X_norm)
    y = np.array([1] * n_accidents + [1] * n_shake_stop + [0] * n_normal)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    clf.fit(X_train, y_train)

    score = clf.score(X_test, y_test)
    print(f"Model accuracy: {score:.3f}")

    ml_dir = Path(__file__).resolve().parent
    model_path = ml_dir / "accident_model.joblib"
    joblib.dump({'model': clf, 'feature_names': [
        'speed_drop', 'speed_drop_rate', 'accel_spike', 'gyro_spike',
        'seconds_stopped', 'location_change_m', 'speed_before', 'speed_after'
    ]}, model_path)
    print(f"Saved to {model_path}")
    return model_path

if __name__ == '__main__':
    train_and_save()
