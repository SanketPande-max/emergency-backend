from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt

def role_required(required_role):
    """Decorator to check user role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = claims.get('role')
            
            if role != required_role:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user_id():
    """Get current user ID from JWT"""
    return get_jwt_identity()

def get_current_role():
    """Get current user role from JWT"""
    claims = get_jwt()
    return claims.get('role')
