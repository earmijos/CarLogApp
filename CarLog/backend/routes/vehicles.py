"""
Vehicles API Routes
===================
RESTful endpoints for vehicle management.
"""

from flask import Blueprint, request, jsonify
import sys
import os
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.vehicle_service import VehicleService
from services.base_service import ValidationError, NotFoundError

vehicles_bp = Blueprint('vehicles', __name__)


@vehicles_bp.route('', methods=['GET'])
def get_vehicles():
    """
    Get all vehicles.
    Query params: limit, offset, user_id
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        user_id = request.args.get('user_id', type=int)
        
        vehicles = VehicleService.get_all(limit=limit, offset=offset, user_id=user_id)
        
        return jsonify({
            'success': True,
            'data': vehicles,
            'count': len(vehicles)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@vehicles_bp.route('/<vin>', methods=['GET'])
def get_vehicle(vin):
    """Get a single vehicle by VIN."""
    try:
        vehicle = VehicleService.get_by_vin(vin)
        
        if not vehicle:
            return jsonify({
                'success': False,
                'error': 'Vehicle not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': vehicle
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@vehicles_bp.route('/<vin>/summary', methods=['GET'])
def get_vehicle_summary(vin):
    """Get vehicle summary with stats."""
    try:
        summary = VehicleService.get_summary(vin)
        
        return jsonify({
            'success': True,
            'data': summary
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@vehicles_bp.route('', methods=['POST'])
def create_vehicle():
    """Create a new vehicle."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        vehicle = VehicleService.create(data)
        
        return jsonify({
            'success': True,
            'data': vehicle,
            'message': 'Vehicle created successfully'
        }), 201
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@vehicles_bp.route('/<vin>', methods=['PUT', 'PATCH'])
def update_vehicle(vin):
    """Update a vehicle."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        vehicle = VehicleService.update(vin, data)
        
        return jsonify({
            'success': True,
            'data': vehicle,
            'message': 'Vehicle updated successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@vehicles_bp.route('/<vin>', methods=['DELETE'])
def delete_vehicle(vin):
    """Delete a vehicle and all related data."""
    try:
        # Delete vehicle (which will cascade delete related records)
        # The VehicleService.delete() already explicitly deletes all related records
        VehicleService.delete(vin)
        
        return jsonify({
            'success': True,
            'message': 'Vehicle and all related data deleted successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@vehicles_bp.route('/<vin>/mileage', methods=['PUT'])
def update_mileage(vin):
    """Update vehicle mileage."""
    try:
        data = request.get_json()
        mileage = data.get('mileage') if data else None
        
        if mileage is None:
            return jsonify({
                'success': False,
                'error': 'Mileage is required'
            }), 400
        
        vehicle = VehicleService.update_mileage(vin, mileage)
        
        return jsonify({
            'success': True,
            'data': vehicle,
            'message': 'Mileage updated successfully'
        })
    except NotFoundError as e:
        return jsonify({'success': False, 'error': e.message}), 404
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@vehicles_bp.route('/search', methods=['GET'])
def search_vehicles():
    """Search vehicles by make, model, or VIN."""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 20, type=int)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        vehicles = VehicleService.search(query, limit=limit)
        
        return jsonify({
            'success': True,
            'data': vehicles,
            'count': len(vehicles)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@vehicles_bp.route('/decode-vin/<vin>', methods=['GET'])
def decode_vin(vin):
    """
    Decode a VIN using NHTSA API.
    This endpoint proxies the NHTSA VIN decoder to avoid CORS issues.
    """
    try:
        # Validate VIN length
        if len(vin) != 17:
            return jsonify({
                'success': False,
                'error': 'VIN must be exactly 17 characters'
            }), 400
        
        # Call NHTSA API
        nhtsa_url = f'https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json'
        
        try:
            response = requests.get(nhtsa_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse results
            results = data.get('Results', [])
            decoded = {}
            
            for item in results:
                variable = item.get('Variable')
                value = item.get('Value')
                if variable and value and value not in ['', 'Not Applicable']:
                    decoded[variable] = value
            
            # Check if we got valid data
            if not decoded.get('Make') and not decoded.get('Model'):
                return jsonify({
                    'success': False,
                    'error': 'VIN not recognized or invalid'
                }), 404
            
            return jsonify({
                'success': True,
                'data': {
                    'vin': vin.upper(),
                    'make': decoded.get('Make'),
                    'model': decoded.get('Model'),
                    'year': decoded.get('Model Year'),
                    'trim': decoded.get('Trim'),
                    'bodyClass': decoded.get('Body Class'),
                    'vehicleType': decoded.get('Vehicle Type'),
                    'driveType': decoded.get('Drive Type'),
                    'fuelType': decoded.get('Fuel Type - Primary'),
                    'engineCylinders': decoded.get('Engine Number of Cylinders'),
                    'engineDisplacement': decoded.get('Displacement (L)'),
                    'transmissionStyle': decoded.get('Transmission Style'),
                    'doors': decoded.get('Doors'),
                    'plantCountry': decoded.get('Plant Country'),
                    'plantCity': decoded.get('Plant City'),
                    'manufacturer': decoded.get('Manufacturer Name'),
                    'errorCode': decoded.get('Error Code'),
                    'errorText': decoded.get('Error Text'),
                    'raw': decoded  # Include raw data for completeness
                }
            })
            
        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'error': 'VIN lookup timed out. Please try again.'
            }), 504
        except requests.exceptions.RequestException as e:
            return jsonify({
                'success': False,
                'error': f'Failed to connect to VIN decoder service: {str(e)}'
            }), 503
            
    except ValidationError as e:
        return jsonify({'success': False, 'error': e.message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

