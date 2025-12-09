"""
Repairs API Routes
==================
RESTful endpoints for repair management.
"""

from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.repair_service import RepairService
from services.base_service import ValidationError, NotFoundError

repairs_bp = Blueprint('repairs', __name__)


@repairs_bp.route('', methods=['GET'])
def get_repairs():
    """
    Get repairs, optionally filtered by VIN.
    Query params: vin, limit, offset
    """
    try:
        vin = request.args.get('vin')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if vin:
            repairs = RepairService.get_by_vin(vin, limit=limit, offset=offset)
        else:
            repairs = RepairService.get_all(limit=limit, offset=offset, order_by='date')
        
        return jsonify({
            'success': True,
            'data': repairs,
            'count': len(repairs)
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@repairs_bp.route('/vehicle/<vin>', methods=['GET'])
def get_repairs_by_vehicle(vin):
    """Get all repairs for a specific vehicle."""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        repairs = RepairService.get_by_vin(vin, limit=limit, offset=offset)
        total_cost = RepairService.get_total_cost(vin)
        
        return jsonify({
            'success': True,
            'data': repairs,
            'count': len(repairs),
            'total_cost': total_cost
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@repairs_bp.route('/<int:repair_id>', methods=['GET'])
def get_repair(repair_id):
    """Get a single repair by ID."""
    try:
        repair = RepairService.get_by_id(repair_id)
        
        if not repair:
            return jsonify({
                'success': False,
                'error': 'Repair not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': repair
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@repairs_bp.route('', methods=['POST'])
def create_repair():
    """Create a new repair record."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        repair = RepairService.create(data)
        
        return jsonify({
            'success': True,
            'data': repair,
            'message': 'Repair created successfully'
        }), 201
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@repairs_bp.route('/<int:repair_id>', methods=['PUT', 'PATCH'])
def update_repair(repair_id):
    """Update a repair record."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        repair = RepairService.update(repair_id, data)
        
        return jsonify({
            'success': True,
            'data': repair,
            'message': 'Repair updated successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@repairs_bp.route('/<int:repair_id>', methods=['DELETE'])
def delete_repair(repair_id):
    """Delete a repair record."""
    try:
        RepairService.delete(repair_id)
        
        return jsonify({
            'success': True,
            'message': 'Repair deleted successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@repairs_bp.route('/cleanup-orphaned', methods=['POST'])
def cleanup_orphaned_repairs():
    """Clean up repairs for vehicles that no longer exist."""
    try:
        from db.db_helper import execute_query, execute_delete
        
        # Find orphaned repairs
        orphaned = execute_query("""
            SELECT id FROM repairs 
            WHERE vin NOT IN (SELECT vin FROM vehicles)
        """)
        
        if orphaned:
            deleted = execute_delete(
                'repairs', 
                'vin NOT IN (SELECT vin FROM vehicles)',
                ()
            )
            return jsonify({
                'success': True,
                'message': f'Cleaned up {deleted} orphaned repair records'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No orphaned repairs found'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@repairs_bp.route('/vehicle/<vin>/summary', methods=['GET'])
def get_repair_summary(vin):
    """Get repair cost summary for a vehicle."""
    try:
        summary = RepairService.get_cost_summary(vin)
        
        return jsonify({
            'success': True,
            'data': summary
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@repairs_bp.route('/vehicle/<vin>/recent', methods=['GET'])
def get_recent_repairs(vin):
    """Get recent repairs for a vehicle."""
    try:
        limit = request.args.get('limit', 5, type=int)
        repairs = RepairService.get_recent(vin, limit=limit)
        
        return jsonify({
            'success': True,
            'data': repairs
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

