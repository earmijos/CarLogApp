"""
CarLog API Routes Package
=========================
RESTful API endpoints for all CarLog services.
"""

from flask import jsonify, Blueprint

# Import all blueprints
from .vehicles import vehicles_bp
from .repairs import repairs_bp
from .fuel_logs import fuel_logs_bp
from .maintenance import maintenance_bp
from .mileage import mileage_bp
from .trips import trips_bp
from .analytics import analytics_bp
from .settings import settings_bp
from .users import users_bp

# List of all blueprints to register
ALL_BLUEPRINTS = [
    (vehicles_bp, '/api/vehicles'),
    (repairs_bp, '/api/repairs'),
    (fuel_logs_bp, '/api/fuel-logs'),
    (maintenance_bp, '/api/maintenance'),
    (mileage_bp, '/api/mileage'),
    (trips_bp, '/api/trips'),
    (analytics_bp, '/api/analytics'),
    (settings_bp, '/api/settings'),
    (users_bp, '/api/users'),
]


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    for blueprint, url_prefix in ALL_BLUEPRINTS:
        app.register_blueprint(blueprint, url_prefix=url_prefix)
    
    # Register legacy routes for backward compatibility
    from .legacy import legacy_bp
    app.register_blueprint(legacy_bp)


def make_response(data=None, message=None, status=200):
    """Create a standardized API response."""
    response = {
        'success': 200 <= status < 300,
        'status': status
    }
    
    if message:
        response['message'] = message
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status


def error_response(message, status=400, code=None):
    """Create a standardized error response."""
    response = {
        'success': False,
        'status': status,
        'error': {
            'message': message
        }
    }
    
    if code:
        response['error']['code'] = code
    
    return jsonify(response), status


__all__ = [
    'register_blueprints',
    'make_response',
    'error_response',
    'ALL_BLUEPRINTS',
]

