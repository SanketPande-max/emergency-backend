from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from models.user_model import UserModel
from models.ambulance_model import AmbulanceModel
from models.request_model import RequestModel, LocationTrackModel
from utils.auth import role_required
from config import Config
from bson import ObjectId

admin_bp = Blueprint('admin', __name__)

def init_admin_routes(app, db):
    admin_bp.db = db
    app.register_blueprint(admin_bp, url_prefix='/admin')

@admin_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        if username != Config.ADMIN_USERNAME or password != Config.ADMIN_PASSWORD:
            return jsonify({'error': 'Invalid credentials'}), 401
        access_token = create_access_token(
            identity='admin',
            additional_claims={'role': 'admin'}
        )
        return jsonify({'message': 'Login successful', 'token': access_token}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/all-users', methods=['GET'])
@jwt_required()
@role_required('admin')
def all_users():
    try:
        users = list(admin_bp.db.users.find())
        for u in users:
            u['_id'] = str(u['_id'])
        return jsonify({'users': users, 'count': len(users)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/all-ambulances', methods=['GET'])
@jwt_required()
@role_required('admin')
def all_ambulances():
    try:
        ambulances = list(admin_bp.db.ambulances.find())
        for a in ambulances:
            a['_id'] = str(a['_id'])
        return jsonify({'ambulances': ambulances, 'count': len(ambulances)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/all-requests', methods=['GET'])
@jwt_required()
@role_required('admin')
def all_requests():
    try:
        requests = RequestModel.get_all_requests(admin_bp.db)
        for r in requests:
            r['_id'] = str(r['_id'])
            r['user_id'] = str(r['user_id'])
            if r.get('assigned_ambulance_id'):
                r['assigned_ambulance_id'] = str(r['assigned_ambulance_id'])
        return jsonify({'requests': requests, 'count': len(requests)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/dashboard-map', methods=['GET'])
@jwt_required()
@role_required('admin')
def dashboard_map():
    """
    For central dashboard: each request as accident marker + assigned ambulance + ambulance track.
    Frontend can plot: accident at request.location, assigned ambulance, and track polyline.
    Excludes completed requests from map (but they remain in list view).
    """
    try:
        requests = RequestModel.get_all_requests(admin_bp.db)
        out = []
        # Color palette for different ambulances
        colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']
        ambulance_colors = {}  # Map ambulance_id to color
        
        for req in requests:
            # Skip completed requests from map (but keep in list)
            if req.get('status') == 'completed':
                continue
                
            r = {
                'id': str(req['_id']),
                'location': req.get('location'),
                'status': req.get('status'),
                'created_at': req.get('created_at').isoformat() if req.get('created_at') else None,
                'assigned_ambulance_id': str(req['assigned_ambulance_id']) if req.get('assigned_ambulance_id') else None,
                'assigned_ambulance': None,
                'track': [],
                'track_color': None
            }
            r['selected_hospital'] = req.get('selected_hospital')
            if req.get('assigned_ambulance_id'):
                amb_id_str = str(req['assigned_ambulance_id'])
                amb = AmbulanceModel.find_by_id(admin_bp.db, amb_id_str)
                if amb:
                    # Assign color to ambulance if not already assigned
                    if amb_id_str not in ambulance_colors:
                        color_idx = len(ambulance_colors) % len(colors)
                        ambulance_colors[amb_id_str] = colors[color_idx]
                    r['track_color'] = ambulance_colors[amb_id_str]
                    
                    r['assigned_ambulance'] = {
                        'id': amb_id_str,
                        'name': amb.get('name'),
                        'phone': amb.get('phone'),
                        'vehicle_number': amb.get('vehicle_number'),
                        'driving_license': amb.get('driving_license'),
                        'age': amb.get('age'),
                        'gender': amb.get('gender'),
                        'status': amb.get('status'),
                        'current_location': amb.get('current_location'),
                        'current_location_updated_at': amb.get('current_location_updated_at').isoformat() if amb.get('current_location_updated_at') else None,
                    }
                track = LocationTrackModel.get_track_for_request(admin_bp.db, r['id'])
                r['track'] = [
                    {'lat': t['lat'], 'lng': t['lng'], 'created_at': t.get('created_at').isoformat() if t.get('created_at') else None}
                    for t in track
                ]
            out.append(r)
        return jsonify({'requests': out, 'count': len(out)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
