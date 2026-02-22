import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
from routes.user_routes import init_user_routes
from routes.ambulance_routes import init_ambulance_routes
from routes.admin_routes import init_admin_routes
from routes.sensor_routes import init_sensor_routes
from models.otp_model import OTPModel

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
mongo = PyMongo(app)
jwt = JWTManager(app)
# CORS configuration - allow frontend domain in production
frontend_url = os.getenv('FRONTEND_URL', '*')
if frontend_url == '*':
    CORS(app)  # Allow all origins in development
else:
    CORS(app, origins=[frontend_url])  # Specific origin in production

# Initialize routes
init_user_routes(app, mongo.db)
init_ambulance_routes(app, mongo.db)
init_admin_routes(app, mongo.db)
init_sensor_routes(app, mongo.db)
init_accident_webhook_routes(app, mongo.db)

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        mongo.db.command('ping')
        return {
            'status': 'ok',
            'message': 'Emergency Response System API is running',
            'database': 'connected',
            'database_name': mongo.db.name
        }, 200
    except Exception as e:
        return {
            'status': 'error',
            'message': 'Emergency Response System API is running',
            'database': 'disconnected',
            'error': str(e)
        }, 200

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return {'error': 'Endpoint not found'}, 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return {'error': 'Internal server error'}, 500

# Cleanup expired OTPs on startup (for production with gunicorn)
def cleanup_on_startup():
    with app.app_context():
        OTPModel.cleanup_expired_otps(mongo.db)

# Run cleanup on app initialization
cleanup_on_startup()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
