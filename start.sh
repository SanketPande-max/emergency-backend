#!/bin/bash
# Startup script for production
# Cleans up expired OTPs and starts gunicorn

python -c "from app import app, mongo; from models.otp_model import OTPModel; app.app_context().push(); OTPModel.cleanup_expired_otps(mongo.db)"

gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
