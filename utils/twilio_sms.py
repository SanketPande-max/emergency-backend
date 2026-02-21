"""
Send SMS via Twilio (e.g. OTP).
"""
from config import Config

def send_sms(to_number: str, body: str):
    """
    Send SMS using Twilio.
    to_number: E.164 format e.g. +919876543210
    Returns (success: bool, error_message: str or empty).
    """
    if not Config.TWILIO_ACCOUNT_SID or not Config.TWILIO_AUTH_TOKEN:
        return False, "Twilio not configured"
    try:
        from twilio.rest import Client
        client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=body,
            from_=Config.TWILIO_PHONE_NUMBER,
            to=to_number
        )
        return True, ""
    except Exception as e:
        return False, str(e)

def normalize_phone(phone: str) -> str:
    """Ensure phone has + prefix for Twilio (E.164)."""
    phone = (phone or "").strip()
    if not phone:
        return phone
    if not phone.startswith("+"):
        if phone.startswith("0"):
            phone = phone[1:]
        phone = "+91" + phone if len(phone) == 10 else "+" + phone
    return phone
