"""
Twilio Voice: place verification calls for accident confirmation.
If user answers -> false positive. If no answer after 2 calls -> confirmed accident.
"""
from config import Config


def get_twiml_for_verification(alert_id=None):
    """
    TwiML: say message, wait for user input (press 1 = safe, no press = emergency).
    If user presses 1, redirect to safe handler. Otherwise, proceed to emergency.
    """
    gather_url = f"/accident-webhook/voice-gather?alert_id={alert_id}" if alert_id else "/accident-webhook/voice-gather"
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">This is an automated call from Emergency Response. We detected a possible accident at your location.</Say>
    <Gather numDigits="1" action="{gather_url}" method="POST" timeout="10">
        <Say voice="alice">If you are safe and do not need help, please press 1 now. If you need assistance, do nothing and we will send help immediately.</Say>
    </Gather>
    <Say voice="alice">No response detected. We are sending help to your location immediately.</Say>
    <Redirect>/accident-webhook/voice-status?alert_id={alert_id}&amp;call_index=1&amp;user_response=no_answer</Redirect>
</Response>'''


def place_verification_call(to_phone: str, callback_base_url: str, alert_id: str, call_index: int = 1):
    """
    Place a Twilio voice call to user for verification.
    callback_base_url: e.g. https://your-api.com (no trailing slash)
    alert_id: accident alert ID for webhook
    call_index: 1 (single call system)
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

        # URL for TwiML that plays message and gathers user input
        url = f"{callback_base_url}/accident-webhook/voice-greeting?alert_id={alert_id}"
        # Status callback to handle call completion
        status_callback = f"{callback_base_url}/accident-webhook/voice-status?alert_id={alert_id}&call_index={call_index}"

        call = client.calls.create(
            to=to_number,
            from_=Config.TWILIO_PHONE_NUMBER,
            url=url,
            status_callback=status_callback,
            status_callback_event=['completed', 'no-answer', 'busy', 'failed', 'canceled'],
            timeout=30,  # Ring for 30 seconds before timeout
        )
        return True, call.sid, ""
    except Exception as e:
        return False, None, str(e)
