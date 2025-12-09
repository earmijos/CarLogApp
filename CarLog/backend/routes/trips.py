"""
Trips API Routes
================
RESTful endpoints for trip management.
"""

from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.trip_service import TripService
from services.base_service import ValidationError, NotFoundError

trips_bp = Blueprint('trips', __name__)


@trips_bp.route('', methods=['GET'])
def get_trips():
    """
    Get trips, optionally filtered by VIN.
    Query params: vin, limit, offset
    """
    try:
        vin = request.args.get('vin')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if vin:
            trips = TripService.get_by_vin(vin, limit=limit, offset=offset)
        else:
            trips = TripService.get_all(limit=limit, offset=offset, order_by='date')
        
        return jsonify({
            'success': True,
            'data': trips,
            'count': len(trips)
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@trips_bp.route('/vehicle/<vin>', methods=['GET'])
def get_trips_by_vehicle(vin):
    """Get all trips for a specific vehicle."""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        trips = TripService.get_by_vin(vin, limit=limit, offset=offset)
        summary = TripService.get_mileage_summary(vin)
        
        return jsonify({
            'success': True,
            'data': trips,
            'count': len(trips),
            'summary': summary
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@trips_bp.route('/<int:trip_id>', methods=['GET'])
def get_trip(trip_id):
    """Get a single trip by ID."""
    try:
        trip = TripService.get_by_id(trip_id)
        
        if not trip:
            return jsonify({
                'success': False,
                'error': 'Trip not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': trip
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@trips_bp.route('', methods=['POST'])
def create_trip():
    """Create a new trip record."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        trip = TripService.create(data)
        
        return jsonify({
            'success': True,
            'data': trip,
            'message': 'Trip created successfully'
        }), 201
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@trips_bp.route('/<int:trip_id>', methods=['PUT', 'PATCH'])
def update_trip(trip_id):
    """Update a trip record."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        trip = TripService.update(trip_id, data)
        
        return jsonify({
            'success': True,
            'data': trip,
            'message': 'Trip updated successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@trips_bp.route('/<int:trip_id>', methods=['DELETE'])
def delete_trip(trip_id):
    """Delete a trip record."""
    try:
        TripService.delete(trip_id)
        
        return jsonify({
            'success': True,
            'message': 'Trip deleted successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@trips_bp.route('/vehicle/<vin>/business', methods=['GET'])
def get_business_trips(vin):
    """Get business trips for a vehicle."""
    try:
        year = request.args.get('year', type=int)
        trips = TripService.get_business_trips(vin, year=year)
        summary = TripService.get_mileage_summary(vin, year=year)
        
        return jsonify({
            'success': True,
            'data': trips,
            'count': len(trips),
            'summary': summary
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@trips_bp.route('/vehicle/<vin>/summary', methods=['GET'])
def get_trip_summary(vin):
    """Get trip mileage summary for a vehicle."""
    try:
        year = request.args.get('year', type=int)
        summary = TripService.get_mileage_summary(vin, year=year)
        
        return jsonify({
            'success': True,
            'data': summary
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@trips_bp.route('/vehicle/<vin>/breakdown', methods=['GET'])
def get_trip_breakdown(vin):
    """Get trip breakdown by purpose."""
    try:
        breakdown = TripService.get_purpose_breakdown(vin)
        
        return jsonify({
            'success': True,
            'data': breakdown
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

