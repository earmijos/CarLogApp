"""
Mileage API Routes
==================
RESTful endpoints for mileage history management.
"""

from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.mileage_service import MileageService
from services.base_service import ValidationError, NotFoundError

mileage_bp = Blueprint('mileage', __name__)


@mileage_bp.route('', methods=['GET'])
def get_mileage():
    """
    Get mileage history, optionally filtered by VIN.
    Query params: vin, limit, offset
    """
    try:
        vin = request.args.get('vin')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if vin:
            history = MileageService.get_by_vin(vin, limit=limit, offset=offset)
        else:
            history = MileageService.get_all(limit=limit, offset=offset, order_by='date')
        
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history)
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@mileage_bp.route('/vehicle/<vin>', methods=['GET'])
def get_mileage_by_vehicle(vin):
    """Get mileage history for a specific vehicle."""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        history = MileageService.get_by_vin(vin, limit=limit, offset=offset)
        latest = MileageService.get_latest(vin)
        
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history),
            'latest': latest
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@mileage_bp.route('/<int:entry_id>', methods=['GET'])
def get_mileage_entry(entry_id):
    """Get a single mileage entry by ID."""
    try:
        entry = MileageService.get_by_id(entry_id)
        
        if not entry:
            return jsonify({
                'success': False,
                'error': 'Mileage entry not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': entry
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@mileage_bp.route('', methods=['POST'])
def create_mileage():
    """Record a new mileage entry."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        entry = MileageService.create(data)
        
        return jsonify({
            'success': True,
            'data': entry,
            'message': 'Mileage recorded successfully'
        }), 201
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@mileage_bp.route('/<int:entry_id>', methods=['DELETE'])
def delete_mileage(entry_id):
    """Delete a mileage entry."""
    try:
        MileageService.delete(entry_id)
        
        return jsonify({
            'success': True,
            'message': 'Mileage entry deleted successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@mileage_bp.route('/vehicle/<vin>/average', methods=['GET'])
def get_average_daily_miles(vin):
    """Get average daily miles for a vehicle."""
    try:
        days = request.args.get('days', 30, type=int)
        stats = MileageService.calculate_average_daily_miles(vin, days=days)
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@mileage_bp.route('/vehicle/<vin>/monthly', methods=['GET'])
def get_monthly_mileage(vin):
    """Get monthly mileage summary for a vehicle."""
    try:
        months = request.args.get('months', 6, type=int)
        summary = MileageService.get_monthly_summary(vin, months=months)
        
        return jsonify({
            'success': True,
            'data': summary
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

