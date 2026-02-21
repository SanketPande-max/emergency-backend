"""
Twilio Voice: place verification calls for accident confirmation.
If user answers -> false positive. If no answer after 2 calls -> confirmed accident.
"""
from config import Config


def get_twiml_for_verification():
    """TwiML: say message and hang up (just to verify user answered)."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">This is an automated call from Emergency Response. We detected a possible accident at your location. If you are safe and do not need help, please press 1 now.</Say>
    <Pause length="5"/>
    <Say voice="alice">If you did not press 1, we will assume you need assistance and send help.</Say>
    <Pause length="3"/>
</Response>'''


def place_verification_call(to_phone: str, callback_base_url: str, alert_id: str, call_index: int):
    """
    Place a Twilio voice call to user.
    callback_base_url: e.g. https://your-api.com (no trailing slash)
    alert_id: accident alert ID for webhook
    call_index: 1 or 2 (first or second call)
    Returns (success: bool, call_sid: str or None, error: str)
    """
    if not Config.TWILIO_ACCOUNT_SID or not Config.TWILIO_AUTH_TOKEN:
        return False, None, "Twilio not configured"

    from utils.twilio_sms import normalize_phone
    to_number = normalize_phone(to_phone)
    if not to_number:
        return False, None, "Invalid phone number"

    try:
        from twilio.rest import Client
        client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)

        status_callback = f"{callback_base_url}/accident-webhook/voice-status?alert_id={alert_id}&call_index={call_index}"
        url = f"{callback_base_url}/accident-webhook/voice-greeting"

        call = client.calls.create(
            to=to_number,
            from_=Config.TWILIO_PHONE_NUMBER,
            url=url,
            status_callback=status_callback,
            status_callback_event=['completed'],
            timeout=30,
        )
        return True, call.sid, ""
    except Exception as e:
        return False, None, str(e)
