"""Sensor readings from mobile device for accident detection."""
from bson import ObjectId
from utils.time_utils import get_ist_now_naive

# Keep last 2 minutes of readings per user (for detection window)
READINGS_TTL_SECONDS = 120
MAX_READINGS_PER_USER = 200


def _parse_ts(ts):
    if ts is None:
        return None
    if hasattr(ts, 'timestamp'):
        return ts
    return None


class SensorReadingModel:
    @staticmethod
    def add(db, user_id, lat, lng, speed_kmh=None, accel_x=None, accel_y=None, accel_z=None,
            gyro_x=None, gyro_y=None, gyro_z=None):
        doc = {
            'user_id': ObjectId(user_id),
            'lat': float(lat) if lat is not None else None,
            'lng': float(lng) if lng is not None else None,
            'speed_kmh': float(speed_kmh) if speed_kmh is not None else None,
            'accel_x': float(accel_x) if accel_x is not None else None,
            'accel_y': float(accel_y) if accel_y is not None else None,
            'accel_z': float(accel_z) if accel_z is not None else None,
            'gyro_x': float(gyro_x) if gyro_x is not None else None,
            'gyro_y': float(gyro_y) if gyro_y is not None else None,
            'gyro_z': float(gyro_z) if gyro_z is not None else None,
            'timestamp': get_ist_now_naive(),
        }
        db.sensor_readings.insert_one(doc)
        return doc

    @staticmethod
    def get_recent_for_user(db, user_id, limit=100):
        """Get recent readings for detection window."""
        readings = list(db.sensor_readings.find(
            {'user_id': ObjectId(user_id)}
        ).sort('timestamp', -1).limit(limit))
        return list(reversed(readings))  # oldest first

    @staticmethod
    def cleanup_old(db, max_age_seconds=300):
        """Remove readings older than max_age_seconds."""
        from datetime import datetime, timedelta
        cutoff = get_ist_now_naive() - timedelta(seconds=max_age_seconds)
        result = db.sensor_readings.delete_many({'timestamp': {'$lt': cutoff}})
        return result.deleted_count
