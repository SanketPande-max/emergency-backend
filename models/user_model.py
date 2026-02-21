from datetime import datetime
from bson import ObjectId
from utils.time_utils import get_ist_now_naive

class UserModel:
    @staticmethod
    def create_user(db, phone, name=None, date_of_birth=None, gender=None, email=None, location=None):
        """Create a new user document (minimal: phone)."""
        user = {
            'phone': phone,
            'name': name,
            'date_of_birth': date_of_birth,
            'gender': gender,
            'email': email,
            'location': location,
            'location_updated_at': None,
            'demerit_points': 0,
            'is_blacklisted': False,
            'accident_detection_enabled': False,
            'created_at': get_ist_now_naive()
        }
        result = db.users.insert_one(user)
        return result.inserted_id

    @staticmethod
    def find_by_phone(db, phone):
        return db.users.find_one({'phone': phone})

    @staticmethod
    def find_by_id(db, user_id):
        return db.users.find_one({'_id': ObjectId(user_id)})

    @staticmethod
    def update_profile(db, user_id, update_data):
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
        return db.users.find_one({'_id': ObjectId(user_id)})

    @staticmethod
    def update_location(db, user_id, lat, lng):
        now = get_ist_now_naive()
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {
                'location': {'lat': float(lat), 'lng': float(lng)},
                'location_updated_at': now
            }}
        )
        return db.users.find_one({'_id': ObjectId(user_id)})

    @staticmethod
    def add_demerit_point(db, user_id):
        """Add 1 demerit point. If >= 2, blacklist the user."""
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return None
        current_points = user.get('demerit_points', 0)
        new_points = current_points + 1
        is_blacklisted = new_points >= 2
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {
                'demerit_points': new_points,
                'is_blacklisted': is_blacklisted
            }}
        )
        return db.users.find_one({'_id': ObjectId(user_id)})

    @staticmethod
    def is_blacklisted(db, user_id):
        """Check if user is blacklisted."""
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return False
        return user.get('is_blacklisted', False) or user.get('demerit_points', 0) >= 2
