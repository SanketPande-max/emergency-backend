from datetime import datetime, timedelta
import random
from utils.time_utils import get_ist_now_naive

class OTPModel:
    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP"""
        return str(random.randint(100000, 999999))
    
    @staticmethod
    def create_otp(db, phone, otp, expiry_minutes=5, role='user'):
        """Create OTP document with expiry. role: 'user' or 'ambulance'."""
        now = get_ist_now_naive()
        expires_at = now + timedelta(minutes=expiry_minutes)
        otp_doc = {
            'phone': phone,
            'otp': otp,
            'role': role,
            'created_at': now,
            'expires_at': expires_at,
            'verified': False
        }
        db.otps.delete_many({'phone': phone, 'role': role})
        result = db.otps.insert_one(otp_doc)
        return result.inserted_id

    @staticmethod
    def verify_otp(db, phone, otp, role='user'):
        """Verify OTP for given role (user or ambulance)."""
        otp_doc = db.otps.find_one({
            'phone': phone,
            'otp': otp,
            'role': role,
            'verified': False
        })
        
        if not otp_doc:
            return False
        
        # Check if OTP has expired
        if get_ist_now_naive() > otp_doc['expires_at']:
            db.otps.delete_one({'_id': otp_doc['_id']})
            return False
        
        # Mark as verified
        db.otps.update_one(
            {'_id': otp_doc['_id']},
            {'$set': {'verified': True}}
        )
        
        # Delete the OTP after verification
        db.otps.delete_one({'_id': otp_doc['_id']})
        
        return True
    
    @staticmethod
    def cleanup_expired_otps(db):
        """Remove expired OTPs"""
        db.otps.delete_many({'expires_at': {'$lt': get_ist_now_naive()}})
