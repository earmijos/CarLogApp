"""
Maintenance API Routes
======================
RESTful endpoints for maintenance interval management.
"""

from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.maintenance_service import MaintenanceService
from services.base_service import ValidationError, NotFoundError

maintenance_bp = Blueprint('maintenance', __name__)


@maintenance_bp.route('', methods=['GET'])
def get_maintenance():
    """
    Get maintenance intervals, optionally filtered by VIN.
    Query params: vin
    """
    try:
        vin = request.args.get('vin')
        
        if vin:
            intervals = MaintenanceService.get_by_vin(vin)
        else:
            intervals = MaintenanceService.get_all(limit=100)
        
        return jsonify({
            'success': True,
            'data': intervals,
            'count': len(intervals)
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/vehicle/<vin>', methods=['GET'])
def get_vehicle_maintenance(vin):
    """Get maintenance schedule for a specific vehicle."""
    try:
        schedule = MaintenanceService.get_maintenance_schedule(vin)
        
        return jsonify({
            'success': True,
            'data': schedule
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/<int:interval_id>', methods=['GET'])
def get_maintenance_interval(interval_id):
    """Get a single maintenance interval by ID."""
    try:
        interval = MaintenanceService.get_by_id(interval_id)
        
        if not interval:
            return jsonify({
                'success': False,
                'error': 'Maintenance interval not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': interval
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('', methods=['POST'])
def create_maintenance():
    """Create a new maintenance interval."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        interval = MaintenanceService.create(data)
        
        return jsonify({
            'success': True,
            'data': interval,
            'message': 'Maintenance interval created successfully'
        }), 201
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/<int:interval_id>', methods=['PUT', 'PATCH'])
def update_maintenance(interval_id):
    """Update a maintenance interval."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        interval = MaintenanceService.update(interval_id, data)
        
        return jsonify({
            'success': True,
            'data': interval,
            'message': 'Maintenance interval updated successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/<int:interval_id>', methods=['DELETE'])
def delete_maintenance(interval_id):
    """Delete a maintenance interval."""
    try:
        MaintenanceService.delete(interval_id)
        
        return jsonify({
            'success': True,
            'message': 'Maintenance interval deleted successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/vehicle/<vin>/record', methods=['POST'])
def record_service(vin):
    """Record that a maintenance service was performed."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        service_type = data.get('service_type')
        date = data.get('date')
        mileage = data.get('mileage')
        
        if not service_type:
            return jsonify({
                'success': False,
                'error': 'service_type is required'
            }), 400
        
        interval = MaintenanceService.record_service(
            vin, 
            service_type, 
            date=date, 
            mileage=mileage
        )
        
        return jsonify({
            'success': True,
            'data': interval,
            'message': f'{service_type} recorded successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/vehicle/<vin>/upcoming', methods=['GET'])
def get_upcoming_maintenance(vin):
    """Get upcoming maintenance items for a vehicle."""
    try:
        limit = request.args.get('limit', 5, type=int)
        upcoming = MaintenanceService.get_upcoming(vin, limit=limit)
        
        return jsonify({
            'success': True,
            'data': upcoming
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/vehicle/<vin>/overdue', methods=['GET'])
def get_overdue_maintenance(vin):
    """Get overdue maintenance items for a vehicle."""
    try:
        overdue = MaintenanceService.get_overdue(vin)
        
        return jsonify({
            'success': True,
            'data': overdue,
            'count': len(overdue)
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@maintenance_bp.route('/vehicle/<vin>/initialize', methods=['POST'])
def initialize_maintenance(vin):
    """Initialize default maintenance intervals for a vehicle."""
    try:
        intervals = MaintenanceService.initialize_for_vehicle(vin)
        
        return jsonify({
            'success': True,
            'data': intervals,
            'message': 'Maintenance intervals initialized successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
