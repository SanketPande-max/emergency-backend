from models.otp_model import OTPModel
from config import Config
from utils.twilio_sms import send_sms, normalize_phone

def send_otp_logic(db, phone, role='user'):
    """Generate OTP, store in DB, send via Twilio. role: 'user' or 'ambulance'."""
    otp = OTPModel.generate_otp()
    OTPModel.create_otp(db, phone, otp, Config.OTP_EXPIRY_MINUTES, role=role)
    to_number = normalize_phone(phone)
    body = f"Your Emergency App verification code is: {otp}. Valid for {Config.OTP_EXPIRY_MINUTES} minutes."
    ok, err = send_sms(to_number, body)
    if not ok:
        raise RuntimeError(f"SMS failed: {err}")
    return otp  # not returned to client; used only for tests if needed
