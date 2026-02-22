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
    if accel_spike >= 11 and seconds_stopped >= 10:
        reasons.append('shake_and_stop')
    if gyro_spike >= 50 and accel_spike >= 10:
        reasons.append('high_impact')
    if speed_before >= 1 and speed_drop >= 1:
        reasons.append('speed_drop')
    if accel_spike >= 5:
        reasons.append('accel_spike')
    if gyro_spike >= 15:
        reasons.append('gyro_spike')
    if seconds_stopped >= 10:
        reasons.append('stopped_10s')
    return reasons


def init_sensor_routes(app, db):
    sensor_bp.db = db
    app.register_blueprint(sensor_bp, url_prefix='/sensor')


@sensor_bp.route('/submit', methods=['POST'])
@jwt_required()
@role_required('user')
def submit_readings():
    """
    Submit sensor data. If accident detected, create request and assign ambulance (no verification calls).
    Accepts shake_stop_detected flag from frontend for demo-mode detection.
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

        # Read frontend shake+stop flag
        shake_stop_flag = bool(data.get('shake_stop_detected', False))
        peak_accel = data.get('peak_accel', 0)

        SensorReadingModel.add(
            sensor_bp.db, user_id,
            lat=lat, lng=lng,
            speed_kmh=data.get('speed_kmh'),
            accel_x=data.get('accel_x'), accel_y=data.get('accel_y'), accel_z=data.get('accel_z'),
            gyro_x=data.get('gyro_x'), gyro_y=data.get('gyro_y'), gyro_z=data.get('gyro_z'),
        )

        readings = SensorReadingModel.get_recent_for_user(sensor_bp.db, user_id)
        if len(readings) < 1 and not shake_stop_flag:
            return jsonify({'message': 'Reading saved', 'accident_detected': False}), 200

        # Pass shake_stop_flag to the predictor — this enables Path 0 (demo mode)
        is_accident, prob = predict(readings, shake_stop_flag=shake_stop_flag)
        if not is_accident:
            return jsonify({
                'message': 'Reading saved',
                'accident_detected': False,
                'probability': prob,
                'shake_stop_flag': shake_stop_flag,
                'readings_count': len(readings),
            }), 200

        if UserModel.is_blacklisted(sensor_bp.db, user_id):
            return jsonify({'error': 'Account blacklisted'}), 403

        from datetime import timedelta
        from bson import ObjectId
        from utils.time_utils import get_ist_now_naive
        recent = sensor_bp.db.requests.find_one({
            'user_id': ObjectId(user_id),
            'source': 'auto_detected',
            'status': {'$in': ['pending', 'assigned', 'to_hospital']},
            'created_at': {'$gte': get_ist_now_naive() - timedelta(seconds=ALERT_COOLDOWN_SECONDS)}
        })
        if recent:
            return jsonify({'message': 'Cooldown active', 'accident_detected': True}), 200

        # No verification calls - directly create request and assign ambulance
        reasons = _get_trigger_reasons(readings)
        if shake_stop_flag:
            reasons.append('shake_stop_detected_by_frontend')

        request_id = RequestModel.create_request(sensor_bp.db, user_id, lat, lng, source='auto_detected')
        UserModel.update_location(sensor_bp.db, user_id, lat, lng)

        # Clean up old sensor readings after emergency is created
        SensorReadingModel.cleanup_old(sensor_bp.db, max_age_seconds=10)

        ambulances = AmbulanceModel.get_all_with_location(sensor_bp.db, exclude_assigned=True)
        nearest = find_nearest_ambulance(ambulances, lat, lng, prefer_active=True)
        if nearest:
            RequestModel.assign_ambulance(sensor_bp.db, str(request_id), str(nearest['_id']))

        return jsonify({
            'message': 'Accident detected. Emergency request created and ambulance assigned.',
            'accident_detected': True,
            'request_id': str(request_id),
            'ambulance_assigned': bool(nearest),
            'trigger_reasons': reasons,
        }), 201
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
