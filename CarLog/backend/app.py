"""
CarLog Backend API
==================
Flask application with RESTful API for vehicle management.

API Endpoints:
- /api/vehicles - Vehicle management
- /api/repairs - Repair tracking
- /api/fuel-logs - Fuel log management
- /api/maintenance - Maintenance scheduling
- /api/mileage - Mileage history
- /api/trips - Trip tracking
- /api/analytics - Analytics and reports
- /api/settings - App settings
- /api/users - User management

Legacy endpoints (backward compatible):
- /car/<vin> - Get vehicle info
- /maintenance/<vin> - Get maintenance intervals
- /repair/repairs/<vin> - Get/create repairs
- /fuel/ - Get fuel logs
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('carlog_backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS

# Import route registration function
from routes import register_blueprints

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Register all blueprints (new API + legacy)
register_blueprints(app)

# Ensure database is initialized
try:
    from db.db_helper import ensure_initialized
    ensure_initialized()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.warning(f"Database initialization check failed: {e}")


# =============================================================================
# Root Routes
# =============================================================================

@app.route('/')
def home():
    """API root endpoint."""
    return jsonify({
        'name': 'CarLog API',
        'version': '2.0.0',
        'status': 'running',
        'endpoints': {
            'vehicles': '/api/vehicles',
            'repairs': '/api/repairs',
            'fuel_logs': '/api/fuel-logs',
            'maintenance': '/api/maintenance',
            'mileage': '/api/mileage',
            'trips': '/api/trips',
            'analytics': '/api/analytics',
            'settings': '/api/settings',
            'users': '/api/users'
        },
        'legacy_endpoints': {
            'vehicle': '/car/<vin>',
            'maintenance': '/maintenance/<vin>',
            'repairs': '/repair/repairs/<vin>',
            'fuel': '/fuel/'
        }
    })


@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'database': 'connected'
    })


@app.route('/api')
def api_info():
    """API information endpoint."""
    return jsonify({
        'name': 'CarLog API',
        'version': '2.0.0',
        'description': 'Vehicle maintenance and cost tracking API',
        'documentation': '/api/docs'
    })


# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Resource not found',
        'status': 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'status': 500
    }), 500


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'success': False,
        'error': 'Method not allowed',
        'status': 405
    }), 405


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == '__main__':
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    
    logger.info(f"Starting CarLog API on port {port} (debug={debug})")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
