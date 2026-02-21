from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.ambulance_model import AmbulanceModel
from models.request_model import RequestModel, LocationTrackModel
from models.user_model import UserModel
from models.otp_model import OTPModel
from utils.auth import role_required
from utils.otp import send_otp_logic
from utils.distance import find_nearest_ambulance
from bson import ObjectId

ambulance_bp = Blueprint('ambulance', __name__)

def _serialize_ambulance(a):
    if not a:
        return a
    a = dict(a)
    a['_id'] = str(a['_id'])
    return a

def init_ambulance_routes(app, db):
    ambulance_bp.db = db
    app.register_blueprint(ambulance_bp, url_prefix='/ambulance')

@ambulance_bp.route('/send-otp', methods=['POST'])
def send_otp():
    try:
        data = request.get_json() or {}
        phone = data.get('phone')
        if not phone:
            return jsonify({'error': 'Phone number is required'}), 400
        send_otp_logic(ambulance_bp.db, phone, role='ambulance')
        return jsonify({'message': 'OTP sent successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ambulance_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json() or {}
        phone = data.get('phone')
        otp = data.get('otp')
        if not phone or not otp:
            return jsonify({'error': 'Phone number and OTP are required'}), 400
        if not OTPModel.verify_otp(ambulance_bp.db, phone, otp, role='ambulance'):
            return jsonify({'error': 'Invalid or expired OTP'}), 400
        ambulance = AmbulanceModel.find_by_phone(ambulance_bp.db, phone)
        if not ambulance:
            AmbulanceModel.create_ambulance(ambulance_bp.db, phone)
            ambulance = AmbulanceModel.find_by_phone(ambulance_bp.db, phone)
        access_token = create_access_token(
            identity=str(ambulance['_id']),
            additional_claims={'role': 'ambulance'}
        )
        # Check if profile is completed
        profile_completed = ambulance.get('profile_completed', False)
        if not profile_completed:
            # Check if profile has required fields
            required_fields = ['name', 'age', 'date_of_birth', 'gender', 'vehicle_number', 'driving_license']
            if all(ambulance.get(f) for f in required_fields):
                profile_completed = True
                AmbulanceModel.update_profile(ambulance_bp.db, str(ambulance['_id']), {'profile_completed': True})
        
        return jsonify({
            'message': 'OTP verified successfully',
            'token': access_token,
            'ambulance_id': str(ambulance['_id']),
            'status': ambulance.get('status', 'inactive'),
            'ambulance': _serialize_ambulance(ambulance),
            'profile_completed': profile_completed
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ambulance_bp.route('/me', methods=['GET'])
@jwt_required()
@role_required('ambulance')
def get_me():
    """Get current ambulance profile (for pre-populating forms)."""
    try:
        ambulance_id = get_jwt_identity()
        ambulance = AmbulanceModel.find_by_id(ambulance_bp.db, ambulance_id)
        if not ambulance:
            return jsonify({'error': 'Ambulance not found'}), 404
        return jsonify({'ambulance': _serialize_ambulance(ambulance)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ambulance_bp.route('/update-profile', methods=['POST'])
@jwt_required()
@role_required('ambulance')
def update_profile():
    try:
        ambulance_id = get_jwt_identity()
        data = request.get_json() or {}
        update_data = {}
        for key in ('name', 'age', 'date_of_birth', 'gender', 'vehicle_number', 'driving_license', 'ambulance_type'):
            if key in data:
                update_data[key] = data[key]
        if not update_data:
            return jsonify({'error': 'No data provided for update'}), 400
        updated = AmbulanceModel.update_profile(ambulance_bp.db, ambulance_id, update_data)
        return jsonify({'message': 'Profile updated successfully', 'ambulance': _serialize_ambulance(updated)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ambulance_bp.route('/status', methods=['PUT'])
@jwt_required()
@role_required('ambulance')
def toggle_status():
    """Set status to active only if profile and location are set."""
    try:
        ambulance_id = get_jwt_identity()
        data = request.get_json() or {}
        status = data.get('status')
        if status not in ('active', 'inactive'):
            return jsonify({'error': 'Status must be "active" or "inactive"'}), 400

        ambulance = None
        # If trying to set active, validate profile and location
        if status == 'active':
            ambulance = AmbulanceModel.find_by_id(ambulance_bp.db, ambulance_id)
            if not ambulance:
                return jsonify({'error': 'Ambulance not found'}), 404
            
            # Check required profile fields
            required_fields = ['name', 'age', 'date_of_birth', 'gender', 'vehicle_number', 'driving_license']
            missing = [f for f in required_fields if not ambulance.get(f)]
            if missing:
                return jsonify({
                    'error': 'Cannot set status to active. Missing profile fields',
                    'missing_fields': missing
                }), 400
            
            # Check location is set
            if not ambulance.get('current_location'):
                return jsonify({'error': 'Cannot set status to active. Location not set. Please update location first.'}), 400

        updated = AmbulanceModel.update_status(ambulance_bp.db, ambulance_id, status)
        
        # If ambulance just became active, try to auto-assign nearest pending request (if any)
        assigned_request = None
        if status == 'active':
            # Reuse fetched ambulance document if available, otherwise fetch again
            if ambulance is None:
                ambulance = AmbulanceModel.find_by_id(ambulance_bp.db, ambulance_id)
            try:
                assigned_request = RequestModel.assign_nearest_pending_to_ambulance(ambulance_bp.db, ambulance)
            except Exception:
                assigned_request = None

        response = {
            'message': f'Status updated to {status}',
            'status': updated['status'],
        }
        if assigned_request:
            response['assigned_request_id'] = str(assigned_request['_id'])
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ambulance_bp.route('/update-location', methods=['POST'])
@jwt_required()
@role_required('ambulance')
def update_location():
    """Update current location for THIS ambulance only; if has active assigned request, log to track for dashboard."""
    try:
        ambulance_id = get_jwt_identity()
        # Verify ambulance exists
        ambulance = AmbulanceModel.find_by_id(ambulance_bp.db, ambulance_id)
        if not ambulance:
            return jsonify({'error': 'Ambulance not found'}), 404
        
        data = request.get_json() or {}
        lat = data.get('lat')
        lng = data.get('lng')
        if lat is None or lng is None:
            return jsonify({'error': 'lat and lng are required'}), 400
        lat, lng = float(lat), float(lng)
        
        # Update location for THIS specific ambulance only
        AmbulanceModel.update_location(ambulance_bp.db, ambulance_id, lat, lng)
        
        # Log to track if has active assignment
        assigned = list(ambulance_bp.db.requests.find({
            'assigned_ambulance_id': ObjectId(ambulance_id),
            'status': {'$in': ['assigned', 'to_hospital']}
        }).limit(1))
        if assigned:
            LocationTrackModel.add(ambulance_bp.db, str(assigned[0]['_id']), ambulance_id, lat, lng)
        
        return jsonify({'message': 'Location updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ambulance_bp.route('/my-requests', methods=['GET'])
@jwt_required()
@role_required('ambulance')
def my_requests():
    try:
        ambulance_id = get_jwt_identity()
        requests = RequestModel.get_by_ambulance(ambulance_bp.db, ambulance_id)
        out = []
        for req in requests:
            r = dict(req)
            r['_id'] = str(r['_id'])
            r['user_id'] = str(r['user_id'])
            r['assigned_ambulance_id'] = str(r['assigned_ambulance_id']) if r.get('assigned_ambulance_id') else None
            user = UserModel.find_by_id(ambulance_bp.db, r['user_id'])
            if user:
                r['user_name'] = user.get('name')
                r['user_phone'] = user.get('phone')
            r['accident_location'] = r.get('location')
            out.append(r)
        return jsonify({'requests': out, 'count': len(out)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ambulance_bp.route('/assigned-details', methods=['GET'])
@jwt_required()
@role_required('ambulance')
def assigned_details():
    """Get current assigned request: user name, phone, accident location, and directions (origin=ambulance, destination=accident)."""
    try:
        ambulance_id = get_jwt_identity()
        assigned = list(ambulance_bp.db.requests.find({
            'assigned_ambulance_id': ObjectId(ambulance_id),
            'status': {'$in': ['assigned', 'to_hospital']}
        }).sort('created_at', -1).limit(1))
        if not assigned:
            return jsonify({'assigned': None, 'message': 'No active assignment'}), 200
        req = assigned[0]
        user = UserModel.find_by_id(ambulance_bp.db, str(req['user_id']))
        amb = AmbulanceModel.find_by_id(ambulance_bp.db, ambulance_id)
        accident = req.get('location') or {}
        origin = (amb.get('current_location') or {}) if amb else {}
        dest = req.get('selected_hospital') if req.get('status') == 'to_hospital' else accident
        return jsonify({
            'assigned': {
                'request_id': str(req['_id']),
                'status': req.get('status'),
                'user_name': user.get('name') if user else None,
                'user_phone': user.get('phone') if user else None,
                'accident_location': accident,
                'selected_hospital': req.get('selected_hospital'),
                'directions': {
                    'origin': origin,
                    'destination': dest
                }
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ambulance_bp.route('/select-hospital', methods=['POST'])
@jwt_required()
@role_required('ambulance')
def select_hospital():
    try:
        ambulance_id = get_jwt_identity()
        data = request.get_json() or {}
        request_id = data.get('request_id')
        hospital = data.get('hospital')
        if not request_id or not hospital or not hospital.get('lat') or not hospital.get('lng'):
            return jsonify({'error': 'request_id and hospital (name, lat, lng) required'}), 400
        req = RequestModel.find_by_id(ambulance_bp.db, request_id)
        if not req:
            return jsonify({'error': 'Request not found'}), 404
        if str(req.get('assigned_ambulance_id')) != ambulance_id:
            return jsonify({'error': 'Unauthorized'}), 403
        RequestModel.select_hospital(ambulance_bp.db, request_id, {'name': hospital.get('name', 'Hospital'), 'lat': float(hospital['lat']), 'lng': float(hospital['lng'])})
        return jsonify({'message': 'Hospital selected', 'status': 'to_hospital'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ambulance_bp.route('/complete-request/<request_id>', methods=['PUT'])
@jwt_required()
@role_required('ambulance')
def complete_request(request_id):
    try:
        ambulance_id = get_jwt_identity()
        data = request.get_json() or {}
        lat = data.get('lat')
        lng = data.get('lng')
        
        # Validate request_id is valid ObjectId format
        try:
            ObjectId(request_id)
        except Exception:
            return jsonify({'error': 'Invalid request ID format'}), 400
        
        req = RequestModel.find_by_id(ambulance_bp.db, request_id)
        if not req:
            return jsonify({'error': 'Request not found'}), 404
        
        if str(req.get('assigned_ambulance_id')) != ambulance_id:
            return jsonify({'error': 'Unauthorized to complete this request'}), 403
        
        if req.get('status') == 'completed':
            return jsonify({'error': 'Request already completed'}), 400
        
        # Update location if provided (non-blocking - don't fail if this errors)
        if lat is not None and lng is not None:
            try:
                AmbulanceModel.update_location(ambulance_bp.db, ambulance_id, float(lat), float(lng))
            except Exception:
                pass
        
        # Mark request as completed - this is the critical operation
        completed = RequestModel.complete_request(ambulance_bp.db, request_id)
        if not completed:
            return jsonify({'error': 'Failed to update request status'}), 500
        
        # Set ambulance back to active (non-blocking)
        try:
            AmbulanceModel.update_status(ambulance_bp.db, ambulance_id, 'active')
        except Exception:
            pass
        
        completed['_id'] = str(completed['_id'])
        completed['user_id'] = str(completed['user_id'])
        completed['assigned_ambulance_id'] = str(completed['assigned_ambulance_id']) if completed.get('assigned_ambulance_id') else None
        return jsonify({'message': 'Request completed successfully', 'request': completed}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to complete request: {str(e)}'}), 500

@ambulance_bp.route('/report-issue/<request_id>', methods=['POST'])
@jwt_required()
@role_required('ambulance')
def report_issue(request_id):
    """Report an issue (engine failure, puncture, etc.) and reassign to nearest available ambulance."""
    try:
        from utils.twilio_sms import send_sms, normalize_phone
        
        ambulance_id = get_jwt_identity()
        data = request.get_json() or {}
        issue_description = data.get('issue_description', 'Technical issue')
        
        # Validate request_id
        try:
            ObjectId(request_id)
        except Exception:
            return jsonify({'error': 'Invalid request ID format'}), 400
        
        req = RequestModel.find_by_id(ambulance_bp.db, request_id)
        if not req:
            return jsonify({'error': 'Request not found'}), 404
        
        if str(req.get('assigned_ambulance_id')) != ambulance_id:
            return jsonify({'error': 'Unauthorized to report issue for this request'}), 403
        
        if req.get('status') in ['completed', 'fake']:
            return jsonify({'error': 'Request already processed'}), 400
        
        # Unassign current ambulance
        current_ambulance = AmbulanceModel.find_by_id(ambulance_bp.db, ambulance_id)
        ambulance_bp.db.requests.update_one(
            {'_id': ObjectId(request_id)},
            {'$set': {
                'assigned_ambulance_id': None,
                'status': 'pending',
                'assigned_at': None
            }}
        )
        
        # Set current ambulance to inactive temporarily
        AmbulanceModel.update_status(ambulance_bp.db, ambulance_id, 'inactive')
        
        # Find nearest available ambulance
        location = req.get('location', {})
        lat = location.get('lat')
        lng = location.get('lng')
        requested_type = req.get('requested_ambulance_type', 'any')
        
        if lat and lng:
            ambulances = AmbulanceModel.get_all_with_location(ambulance_bp.db, exclude_assigned=True)
            # Exclude the current ambulance
            ambulances = [a for a in ambulances if str(a['_id']) != ambulance_id]
            nearest = find_nearest_ambulance(ambulances, lat, lng, prefer_active=True, requested_type=requested_type)
            
            if nearest:
                RequestModel.assign_ambulance(ambulance_bp.db, request_id, str(nearest['_id']), send_notification=True)
                return jsonify({
                    'message': f'Issue reported. Request reassigned to nearest available ambulance.',
                    'reassigned_ambulance_id': str(nearest['_id'])
                }), 200
            else:
                return jsonify({
                    'message': 'Issue reported. Request set to pending. No available ambulances at the moment.',
                    'status': 'pending'
                }), 200
        else:
            return jsonify({
                'message': 'Issue reported. Request set to pending.',
                'status': 'pending'
            }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to report issue: {str(e)}'}), 500

@ambulance_bp.route('/report-fake/<request_id>', methods=['POST'])
@jwt_required()
@role_required('ambulance')
def report_fake(request_id):
    """Report that a request is fake (no accident at destination). Adds demerit point to user."""
    try:
        from models.user_model import UserModel
        ambulance_id = get_jwt_identity()
        
        # Validate request_id
        try:
            ObjectId(request_id)
        except Exception:
            return jsonify({'error': 'Invalid request ID format'}), 400
        
        req = RequestModel.find_by_id(ambulance_bp.db, request_id)
        if not req:
            return jsonify({'error': 'Request not found'}), 404
        
        if str(req.get('assigned_ambulance_id')) != ambulance_id:
            return jsonify({'error': 'Unauthorized to report this request'}), 403
        
        if req.get('status') in ['completed', 'fake']:
            return jsonify({'error': 'Request already processed'}), 400
        
        # Mark request as fake
        fake_req = RequestModel.mark_as_fake(ambulance_bp.db, request_id)
        
        # Add demerit point to user
        user_id = str(req['user_id'])
        updated_user = UserModel.add_demerit_point(ambulance_bp.db, user_id)
        
        # Set ambulance back to active
        try:
            AmbulanceModel.update_status(ambulance_bp.db, ambulance_id, 'active')
        except Exception:
            pass
        
        demerit_points = updated_user.get('demerit_points', 0) if updated_user else 0
        is_blacklisted = updated_user.get('is_blacklisted', False) if updated_user else False
        
        message = f'Fake request reported. User now has {demerit_points} demerit point(s).'
        if is_blacklisted:
            message += ' User has been blacklisted.'
        
        return jsonify({
            'message': message,
            'demerit_points': demerit_points,
            'is_blacklisted': is_blacklisted
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to report fake request: {str(e)}'}), 500
