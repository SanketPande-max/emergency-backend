"""
Twilio Voice webhooks for accident verification calls.
CSRF exempt - Twilio posts form data.
"""
from flask import Blueprint, request, Response
from models.accident_alert_model import AccidentAlertModel
from models.user_model import UserModel
from models.request_model import RequestModel
from models.ambulance_model import AmbulanceModel
from utils.verification_calls import get_twiml_for_verification, place_verification_call
from utils.distance import find_nearest_ambulance

accident_webhook_bp = Blueprint('accident_webhook', __name__)


def init_accident_webhook_routes(app, db):
    accident_webhook_bp.db = db
    app.register_blueprint(accident_webhook_bp, url_prefix='/accident-webhook')


@accident_webhook_bp.route('/voice-greeting', methods=['GET', 'POST'])
def voice_greeting():
    """TwiML for the verification call (plays message and waits for user input)."""
    alert_id = request.args.get('alert_id') or request.form.get('alert_id')
    twiml = get_twiml_for_verification(alert_id)
    return Response(twiml, mimetype='application/xml')


@accident_webhook_bp.route('/voice-gather', methods=['POST'])
def voice_gather():
    """
    Handle user input from verification call.
    If user pressed 1 = safe (false positive).
    If no input or other key = emergency.
    """
    try:
        digits = request.form.get('Digits', '')
        alert_id = request.args.get('alert_id') or request.form.get('alert_id')
        
        if not alert_id:
            return Response('<?xml version="1.0" encoding="UTF-8"?><Response><Say>Error processing call.</Say></Response>', mimetype='application/xml')
        
        db = accident_webhook_bp.db
        alert = AccidentAlertModel.find_by_id(db, alert_id)
        
        if not alert or alert['status'] != AccidentAlertModel.STATUS_PENDING_VERIFICATION:
            return Response('<?xml version="1.0" encoding="UTF-8"?><Response><Say>Call already processed.</Say></Response>', mimetype='application/xml')
        
        # User pressed 1 = safe, mark as false positive
        if digits == '1':
            AccidentAlertModel.mark_false_positive(db, alert_id)
            return Response('<?xml version="1.0" encoding="UTF-8"?><Response><Say>Thank you for confirming you are safe. No emergency services will be dispatched.</Say></Response>', mimetype='application/xml')
        
        # User pressed other key or no key = emergency
        # Redirect to status handler to process emergency
        return Response(f'<?xml version="1.0" encoding="UTF-8"?><Response><Say>We are sending help to your location immediately.</Say><Redirect>/accident-webhook/voice-status?alert_id={alert_id}&amp;call_index=1&amp;user_response=emergency</Redirect></Response>', mimetype='application/xml')
    except Exception as e:
        return Response('<?xml version="1.0" encoding="UTF-8"?><Response><Say>Error processing call.</Say></Response>', mimetype='application/xml')


@accident_webhook_bp.route('/voice-status', methods=['POST'])
def voice_status():
    """
    Twilio status callback when call completes.
    Logic:
    - If user pressed 1 (handled in voice-gather) -> false positive (already marked)
    - If user answered but didn't press 1 -> emergency
    - If no answer or declined -> emergency
    - If call failed -> emergency (safety first)
    """
    try:
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')  # completed, busy, no-answer, failed, canceled
        duration = int(request.form.get('CallDuration', 0) or 0)
        alert_id = request.form.get('alert_id') or request.args.get('alert_id')
        user_response = request.form.get('user_response') or request.args.get('user_response')  # 'safe', 'emergency', 'no_answer'

        if not alert_id:
            return '', 200

        db = accident_webhook_bp.db
        alert = AccidentAlertModel.find_by_id(db, alert_id)
        if not alert or alert['status'] != AccidentAlertModel.STATUS_PENDING_VERIFICATION:
            return '', 200

        # If user_response is 'safe', it means user pressed 1 (already handled in voice-gather)
        if user_response == 'safe':
            return '', 200

        # Record the call
        answered = call_status == 'completed' and duration > 0
        AccidentAlertModel.add_verification_call(db, alert_id, call_sid, answered)

        # Determine if emergency based on call status and user response
        is_emergency = False
        
        if user_response == 'emergency':
            # User answered but didn't press 1 or pressed other key
            is_emergency = True
        elif call_status in ['no-answer', 'busy', 'failed', 'canceled']:
            # No answer, busy, failed, or canceled = emergency
            is_emergency = True
        elif call_status == 'completed' and duration > 0 and user_response != 'safe':
            # Call completed but user didn't confirm safety = emergency
            is_emergency = True
        else:
            # If answered and user confirmed safe (shouldn't reach here, but safety check)
            is_emergency = False

        if is_emergency:
            # Confirm accident and dispatch ambulance
            _confirm_accident_and_dispatch(db, alert_id, alert)
        
        return '', 200
    except Exception as e:
        # On error, proceed with emergency (safety first)
        try:
            alert_id = request.form.get('alert_id') or request.args.get('alert_id')
            if alert_id:
                db = accident_webhook_bp.db
                alert = AccidentAlertModel.find_by_id(db, alert_id)
                if alert and alert['status'] == AccidentAlertModel.STATUS_PENDING_VERIFICATION:
                    _confirm_accident_and_dispatch(db, alert_id, alert)
        except:
            pass
        return '', 200


def _confirm_accident_and_dispatch(db, alert_id, alert):
    """Create emergency request and assign nearest ambulance."""
    from models.sensor_reading_model import SensorReadingModel
    user_id = str(alert['user_id'])
    if UserModel.is_blacklisted(db, user_id):
        AccidentAlertModel.mark_false_positive(db, alert_id)
        return

    loc = alert.get('location') or {}
    lat = loc.get('lat')
    lng = loc.get('lng')
    if lat is None or lng is None:
        return

    request_id = RequestModel.create_request(db, user_id, lat, lng, source='auto_detected', requested_ambulance_type='any')
    UserModel.update_location(db, user_id, lat, lng)

    # Clean up old sensor readings after emergency is created
    SensorReadingModel.cleanup_old(db, max_age_seconds=10)

    ambulances = AmbulanceModel.get_all_with_location(db, exclude_assigned=True)
    nearest = find_nearest_ambulance(ambulances, lat, lng, prefer_active=True, requested_type='any')
    if nearest:
        RequestModel.assign_ambulance(db, str(request_id), str(nearest['_id']), send_notification=True)

    AccidentAlertModel.mark_confirmed(db, alert_id, str(request_id))

    from utils.twilio_sms import send_sms
    user = UserModel.find_by_id(db, user_id)
    if user and user.get('phone'):
        send_sms(user['phone'], "Emergency Response: We detected a possible accident and have dispatched help to your location. Stay calm.")
