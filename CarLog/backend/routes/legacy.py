"""
Legacy API Routes
=================
Backward-compatible endpoints for existing Flutter app.
These routes maintain the old API structure while using new services.
"""

from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.vehicle_service import VehicleService
from services.repair_service import RepairService
from services.maintenance_service import MaintenanceService
from services.fuel_log_service import FuelLogService
from services.base_service import ValidationError

legacy_bp = Blueprint('legacy', __name__)


# =============================================================================
# Legacy Vehicle Routes (matches old /car/<vin>)
# =============================================================================

@legacy_bp.route('/car/<vin>', methods=['GET'])
def legacy_get_vehicle(vin):
    """Legacy: Get vehicle by VIN."""
    try:
        vehicle = VehicleService.get_by_vin(vin)
        
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Return in old format
        return jsonify({
            'VIN': vehicle['vin'],
            'Year': vehicle['year'],
            'Make': vehicle['make'],
            'Model': vehicle['model'],
            'Trim': vehicle.get('trim', ''),
            'engine_type': vehicle.get('engine_type', '')
        })
    except ValidationError:
        return jsonify({'error': 'Invalid VIN'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Legacy Maintenance Routes (matches old /maintenance/<vin>)
# =============================================================================

@legacy_bp.route('/maintenance/<vin>', methods=['GET'])
def legacy_get_maintenance(vin):
    """Legacy: Get maintenance intervals by VIN."""
    try:
        intervals = MaintenanceService.get_by_vin(vin)
        
        if not intervals:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Convert to old format
        result = {'VIN': vin}
        for interval in intervals:
            service = interval['service_type']
            if service == 'Oil Change':
                result['oil_change'] = interval['interval_miles']
            elif service == 'Transmission Fluid':
                result['transmission_fluid_change'] = interval['interval_miles']
            elif service == 'Brake Inspection':
                result['brake_service'] = interval['interval_miles']
            elif service == 'Air Filter':
                result['air_filter_check'] = interval['interval_miles']
        
        return jsonify(result)
    except ValidationError:
        return jsonify({'error': 'Invalid VIN'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Legacy Repair Routes (matches old /repair/repairs/<vin>)
# =============================================================================

@legacy_bp.route('/repair/repairs/<vin>', methods=['GET'])
def legacy_get_repairs(vin):
    """Legacy: Get repairs by VIN."""
    try:
        repairs = RepairService.get_by_vin(vin)
        
        # Return in old format (list of simplified repairs)
        return jsonify([
            {
                'service': r['service'],
                'cost': r['cost'],
                'date': r['date']
            }
            for r in repairs
        ]), 200
    except ValidationError:
        return jsonify([]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@legacy_bp.route('/repair/repairs', methods=['POST'])
def legacy_create_repair():
    """Legacy: Create a repair."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        vin = data.get('vin')
        service = data.get('service')
        cost = data.get('cost')
        date = data.get('date')
        
        if not all([vin, service, cost is not None, date]):
            return jsonify({
                'error': 'Missing required fields: vin, service, cost, date'
            }), 400
        
        RepairService.create({
            'vin': vin,
            'service': service,
            'cost': cost,
            'date': date
        })
        
        return jsonify({'message': 'Repair added successfully'}), 201
    except ValidationError as e:
        return jsonify({'error': e.message}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Legacy Fuel Log Routes (matches old /fuel/)
# =============================================================================

@legacy_bp.route('/fuel/', methods=['GET'])
def legacy_get_fuel_logs():
    """Legacy: Get all fuel logs."""
    try:
        logs = FuelLogService.get_all(limit=100)
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

