"""
Fuel Logs API Routes
====================
RESTful endpoints for fuel log management.
"""

from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.fuel_log_service import FuelLogService
from services.base_service import ValidationError, NotFoundError

fuel_logs_bp = Blueprint('fuel_logs', __name__)


@fuel_logs_bp.route('', methods=['GET'])
def get_fuel_logs():
    """
    Get fuel logs, optionally filtered by VIN.
    Query params: vin, limit, offset
    """
    try:
        vin = request.args.get('vin')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if vin:
            logs = FuelLogService.get_by_vin(vin, limit=limit, offset=offset)
        else:
            logs = FuelLogService.get_all(limit=limit, offset=offset, order_by='date')
        
        return jsonify({
            'success': True,
            'data': logs,
            'count': len(logs)
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@fuel_logs_bp.route('/vehicle/<vin>', methods=['GET'])
def get_fuel_logs_by_vehicle(vin):
    """Get all fuel logs for a specific vehicle."""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        logs = FuelLogService.get_by_vin(vin, limit=limit, offset=offset)
        summary = FuelLogService.get_cost_summary(vin)
        
        return jsonify({
            'success': True,
            'data': logs,
            'count': len(logs),
            'summary': summary
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@fuel_logs_bp.route('/<int:log_id>', methods=['GET'])
def get_fuel_log(log_id):
    """Get a single fuel log by ID."""
    try:
        log = FuelLogService.get_by_id(log_id)
        
        if not log:
            return jsonify({
                'success': False,
                'error': 'Fuel log not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': log
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@fuel_logs_bp.route('', methods=['POST'])
def create_fuel_log():
    """Create a new fuel log entry."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        log = FuelLogService.create(data)
        
        return jsonify({
            'success': True,
            'data': log,
            'message': 'Fuel log created successfully'
        }), 201
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@fuel_logs_bp.route('/<int:log_id>', methods=['PUT', 'PATCH'])
def update_fuel_log(log_id):
    """Update a fuel log entry."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        log = FuelLogService.update(log_id, data)
        
        return jsonify({
            'success': True,
            'data': log,
            'message': 'Fuel log updated successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@fuel_logs_bp.route('/<int:log_id>', methods=['DELETE'])
def delete_fuel_log(log_id):
    """Delete a fuel log entry."""
    try:
        FuelLogService.delete(log_id)
        
        return jsonify({
            'success': True,
            'message': 'Fuel log deleted successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@fuel_logs_bp.route('/vehicle/<vin>/mpg', methods=['GET'])
def get_mpg(vin):
    """Calculate MPG for a vehicle."""
    try:
        limit = request.args.get('limit', 10, type=int)
        mpg_data = FuelLogService.calculate_mpg(vin, limit=limit)
        
        return jsonify({
            'success': True,
            'data': mpg_data
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@fuel_logs_bp.route('/vehicle/<vin>/summary', methods=['GET'])
def get_fuel_summary(vin):
    """Get fuel cost summary for a vehicle."""
    try:
        summary = FuelLogService.get_cost_summary(vin)
        
        return jsonify({
            'success': True,
            'data': summary
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

