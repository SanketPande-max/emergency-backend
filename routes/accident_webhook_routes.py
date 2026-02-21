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
    """TwiML for the verification call (plays message)."""
    return Response(get_twiml_for_verification(), mimetype='application/xml')


@accident_webhook_bp.route('/voice-status', methods=['POST'])
def voice_status():
    """
    Twilio status callback when call completes.
    If answered -> false positive.
    If no-answer and call 1 -> place call 2.
    If no-answer and call 2 -> confirm accident, create request, assign ambulance.
    """
    try:
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        duration = int(request.form.get('CallDuration', 0) or 0)
        alert_id = request.form.get('alert_id') or request.args.get('alert_id')
        call_index = int(request.form.get('call_index') or request.args.get('call_index') or 1)

        if not alert_id:
            return '', 200

        db = accident_webhook_bp.db
        alert = AccidentAlertModel.find_by_id(db, alert_id)
        if not alert or alert['status'] != AccidentAlertModel.STATUS_PENDING_VERIFICATION:
            return '', 200

        answered = call_status == 'completed' and duration > 0

        AccidentAlertModel.add_verification_call(db, alert_id, call_sid, answered)

        if answered:
            AccidentAlertModel.mark_false_positive(db, alert_id)
            return '', 200

        if call_index == 1:
            user = UserModel.find_by_id(db, str(alert['user_id']))
            if user and user.get('phone'):
                import os
                base_url = os.getenv('TWILIO_VOICE_WEBHOOK_BASE', 'http://localhost:5000')
                ok, new_call_sid, _ = place_verification_call(user['phone'], base_url, alert_id, 2)
                if ok:
                    AccidentAlertModel.add_verification_call(db, alert_id, new_call_sid, False)
            return '', 200

        if call_index == 2:
            _confirm_accident_and_dispatch(db, alert_id, alert)
        return '', 200
    except Exception:
        return '', 200


def _confirm_accident_and_dispatch(db, alert_id, alert):
    """Create emergency request and assign nearest ambulance."""
    user_id = str(alert['user_id'])
    if UserModel.is_blacklisted(db, user_id):
        AccidentAlertModel.mark_false_positive(db, alert_id)
        return

    loc = alert.get('location') or {}
    lat = loc.get('lat')
    lng = loc.get('lng')
    if lat is None or lng is None:
        return

    request_id = RequestModel.create_request(db, user_id, lat, lng, source='auto_detected')
    UserModel.update_location(db, user_id, lat, lng)

    ambulances = AmbulanceModel.get_all_with_location(db, exclude_assigned=True)
    nearest = find_nearest_ambulance(ambulances, lat, lng, prefer_active=True)
    if nearest:
        RequestModel.assign_ambulance(db, str(request_id), str(nearest['_id']))

    AccidentAlertModel.mark_confirmed(db, alert_id, str(request_id))

    from utils.twilio_sms import send_sms
    user = UserModel.find_by_id(db, user_id)
    if user and user.get('phone'):
        send_sms(user['phone'], "Emergency Response: We detected a possible accident and have dispatched help to your location. Stay calm.")
