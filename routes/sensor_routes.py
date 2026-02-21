"""Sensor data and accident detection routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user_model import UserModel
from models.sensor_reading_model import SensorReadingModel
from models.accident_alert_model import AccidentAlertModel
from models.request_model import RequestModel
from models.ambulance_model import AmbulanceModel
from utils.auth import role_required
from utils.distance import find_nearest_ambulance
from ml.accident_detector import predict, extract_features

sensor_bp = Blueprint('sensor', __name__)

# Cooldown: don't create new alert for same user within 5 min
ALERT_COOLDOWN_SECONDS = 300


def _get_trigger_reasons(readings):
    """Extract human-readable trigger reasons from readings."""
    feat = extract_features(readings)
    if not feat:
        return []
    speed_drop, _, accel_spike, gyro_spike, seconds_stopped, loc_change, speed_before, _ = feat
    reasons = []
    if speed_before >= 20 and speed_drop >= 25:
        reasons.append('speed_drop')
    if accel_spike >= 12:
        reasons.append('accel_spike')
    if gyro_spike >= 3:
        reasons.append('gyro_spike')
    if seconds_stopped >= 15:
        reasons.append('stopped_15s')
    if loc_change < 20 and seconds_stopped >= 15:
        reasons.append('same_location')
    return reasons


def init_sensor_routes(app, db):
    sensor_bp.db = db
    app.register_blueprint(sensor_bp, url_prefix='/sensor')


@sensor_bp.route('/submit', methods=['POST'])
@jwt_required()
@role_required('user')
def submit_readings():
    """
    Submit sensor data. If accident detected and user has no pending alert, create alert and start verification.
    """
    try:
        user_id = get_jwt_identity()
        user = UserModel.find_by_id(sensor_bp.db, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if not user.get('accident_detection_enabled'):
            return jsonify({'error': 'Accident detection not enabled'}), 400

        data = request.get_json() or {}
        lat = data.get('lat')
        lng = data.get('lng')
        if lat is None or lng is None:
            return jsonify({'error': 'lat and lng required'}), 400

        SensorReadingModel.add(
            sensor_bp.db, user_id,
            lat=lat, lng=lng,
            speed_kmh=data.get('speed_kmh'),
            accel_x=data.get('accel_x'), accel_y=data.get('accel_y'), accel_z=data.get('accel_z'),
            gyro_x=data.get('gyro_x'), gyro_y=data.get('gyro_y'), gyro_z=data.get('gyro_z'),
        )

        readings = SensorReadingModel.get_recent_for_user(sensor_bp.db, user_id)
        if len(readings) < 5:
            return jsonify({'message': 'Reading saved', 'accident_detected': False}), 200

        is_accident, prob = predict(readings)
        if not is_accident:
            return jsonify({'message': 'Reading saved', 'accident_detected': False, 'probability': prob}), 200

        if UserModel.is_blacklisted(sensor_bp.db, user_id):
            return jsonify({'error': 'Account blacklisted'}), 403

        if AccidentAlertModel.get_pending_for_user(sensor_bp.db, user_id):
            return jsonify({'message': 'Verification already in progress', 'accident_detected': True}), 200

        from datetime import timedelta
        from utils.time_utils import get_ist_now_naive
        recent_alert = sensor_bp.db.accident_alerts.find_one({
            'user_id': user['_id'],
            'created_at': {'$gte': get_ist_now_naive() - timedelta(seconds=ALERT_COOLDOWN_SECONDS)}
        })
        if recent_alert:
            return jsonify({'message': 'Cooldown active', 'accident_detected': True}), 200

        reasons = _get_trigger_reasons(readings)
        alert_id = AccidentAlertModel.create(sensor_bp.db, user_id, lat, lng, trigger_reasons=reasons)

        from utils.verification_calls import place_verification_call
        import os
        base_url = os.getenv('TWILIO_VOICE_WEBHOOK_BASE', 'http://localhost:5000')
        ok, call_sid, err = place_verification_call(user['phone'], base_url, alert_id, 1)
        if not ok:
            AccidentAlertModel.mark_false_positive(sensor_bp.db, alert_id)
            return jsonify({'error': f'Verification call failed: {err}'}), 500

        AccidentAlertModel.add_verification_call(sensor_bp.db, alert_id, call_sid, False)

        return jsonify({
            'message': 'Potential accident detected. Verification call placed.',
            'accident_detected': True,
            'alert_id': alert_id,
            'verification_started': True,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sensor_bp.route('/submit-batch', methods=['POST'])
@jwt_required()
@role_required('user')
def submit_batch():
    """Submit multiple readings at once (e.g. from buffered mobile data)."""
    try:
        user_id = get_jwt_identity()
        user = UserModel.find_by_id(sensor_bp.db, user_id)
        if not user or not user.get('accident_detection_enabled'):
            return jsonify({'error': 'Accident detection not enabled'}), 400

        data = request.get_json() or {}
        readings = data.get('readings', [])
        if not readings:
            return jsonify({'error': 'readings array required'}), 400

        for r in readings:
            lat = r.get('lat')
            lng = r.get('lng')
            if lat is not None and lng is not None:
                SensorReadingModel.add(
                    sensor_bp.db, user_id,
                    lat=lat, lng=lng,
                    speed_kmh=r.get('speed_kmh'),
                    accel_x=r.get('accel_x'), accel_y=r.get('accel_y'), accel_z=r.get('accel_z'),
                    gyro_x=r.get('gyro_x'), gyro_y=r.get('gyro_y'), gyro_z=r.get('gyro_z'),
                )

        return jsonify({'message': f'Saved {len(readings)} readings'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sensor_bp.route('/status', methods=['GET'])
@jwt_required()
@role_required('user')
def alert_status():
    """Get current accident alert status for user."""
    try:
        user_id = get_jwt_identity()
        pending = AccidentAlertModel.get_pending_for_user(sensor_bp.db, user_id)
        if not pending:
            return jsonify({'alert': None}), 200
        return jsonify({
            'alert': {
                'id': str(pending['_id']),
                'status': pending['status'],
                'location': pending.get('location'),
                'verification_calls': len(pending.get('verification_calls', [])),
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
