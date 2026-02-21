import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (same folder as config.py)
_env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(_env_path)

class Config:
    # MongoDB Configuration
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/emergodb')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # OTP Configuration
    OTP_EXPIRY_MINUTES = 5
    
    # Admin Credentials (should be in environment variables in production)
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'change-me')

    # Twilio (SMS OTP)
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '+19787561135')

    # Accident detection (Twilio Voice webhook base URL - must be publicly accessible)
    TWILIO_VOICE_WEBHOOK_BASE = os.getenv('TWILIO_VOICE_WEBHOOK_BASE', 'http://localhost:5000')
