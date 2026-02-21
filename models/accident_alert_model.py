"""Accident alerts from auto-detection (pending verification or confirmed)."""
from bson import ObjectId
from utils.time_utils import get_ist_now_naive


class AccidentAlertModel:
    STATUS_PENDING_VERIFICATION = 'pending_verification'
    STATUS_FALSE_POSITIVE = 'false_positive'
    STATUS_CONFIRMED = 'confirmed'

    @staticmethod
    def create(db, user_id, lat, lng, trigger_reasons=None):
        doc = {
            'user_id': ObjectId(user_id),
            'location': {'lat': float(lat), 'lng': float(lng)},
            'status': AccidentAlertModel.STATUS_PENDING_VERIFICATION,
            'trigger_reasons': trigger_reasons or [],
            'verification_calls': [],
            'request_id': None,
            'created_at': get_ist_now_naive(),
            'updated_at': get_ist_now_naive(),
        }
        result = db.accident_alerts.insert_one(doc)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(db, alert_id):
        try:
            return db.accident_alerts.find_one({'_id': ObjectId(alert_id)})
        except Exception:
            return None

    @staticmethod
    def add_verification_call(db, alert_id, call_sid, answered):
        db.accident_alerts.update_one(
            {'_id': ObjectId(alert_id)},
            {
                '$push': {'verification_calls': {'call_sid': call_sid, 'answered': answered, 'at': get_ist_now_naive()}},
                '$set': {'updated_at': get_ist_now_naive()}
            }
        )

    @staticmethod
    def mark_false_positive(db, alert_id):
        db.accident_alerts.update_one(
            {'_id': ObjectId(alert_id)},
            {'$set': {'status': AccidentAlertModel.STATUS_FALSE_POSITIVE, 'updated_at': get_ist_now_naive()}}
        )

    @staticmethod
    def mark_confirmed(db, alert_id, request_id):
        db.accident_alerts.update_one(
            {'_id': ObjectId(alert_id)},
            {
                '$set': {
                    'status': AccidentAlertModel.STATUS_CONFIRMED,
                    'request_id': ObjectId(request_id),
                    'updated_at': get_ist_now_naive()
                }
            }
        )

    @staticmethod
    def get_pending_for_user(db, user_id):
        """Check if user has pending verification (avoid duplicate alerts)."""
        return db.accident_alerts.find_one({
            'user_id': ObjectId(user_id),
            'status': AccidentAlertModel.STATUS_PENDING_VERIFICATION
        })
