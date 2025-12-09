"""
Maintenance Service
===================
Handles maintenance intervals and scheduling.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.db_helper import connection, execute_query, execute_insert
from services.base_service import (
    BaseService, 
    ValidationError, 
    NotFoundError,
    validate_vin,
    validate_date,
    validate_positive_number
)

# Default maintenance intervals
DEFAULT_INTERVALS = {
    'Oil Change': {'miles': 5000, 'months': 6},
    'Transmission Fluid': {'miles': 60000, 'months': 48},
    'Brake Inspection': {'miles': 25000, 'months': 24},
    'Air Filter': {'miles': 15000, 'months': 12},
    'Tire Rotation': {'miles': 7500, 'months': 6},
    'Coolant Flush': {'miles': 30000, 'months': 36},
    'Spark Plugs': {'miles': 60000, 'months': 60},
    'Battery Check': {'miles': 25000, 'months': 24},
    'Brake Fluid': {'miles': 30000, 'months': 24},
    'Power Steering Fluid': {'miles': 50000, 'months': 48},
}


class MaintenanceService(BaseService):
    """Service for maintenance interval CRUD operations."""
    
    table_name = "maintenance_intervals"
    primary_key = "id"
    required_fields = ["vin", "service_type"]
    allowed_fields = [
        "vin", "service_type", "interval_miles", "interval_months",
        "last_performed_date", "last_performed_mileage",
        "next_due_date", "next_due_mileage", "is_custom", "notes"
    ]
    
    @classmethod
    def get_by_vin(cls, vin: str) -> List[Dict[str, Any]]:
        """Get all maintenance intervals for a vehicle."""
        vin = validate_vin(vin)
        
        query = """
            SELECT * FROM maintenance_intervals 
            WHERE vin = ?
            ORDER BY next_due_mileage ASC NULLS LAST
        """
        return execute_query(query, (vin,))
    
    @classmethod
    def get_maintenance_schedule(cls, vin: str) -> Dict[str, Any]:
        """Get maintenance schedule in a user-friendly format."""
        vin = validate_vin(vin)
        
        intervals = cls.get_by_vin(vin)
        
        # Get vehicle current mileage
        vehicle = execute_query(
            "SELECT current_mileage FROM vehicles WHERE vin = ?",
            (vin,), fetch_one=True
        )
        current_mileage = vehicle['current_mileage'] if vehicle else 0
        
        schedule = {
            'vin': vin,
            'current_mileage': current_mileage,
            'intervals': []
        }
        
        for interval in intervals:
            next_due = interval.get('next_due_mileage')
            status = 'unknown'
            miles_until = None
            
            if next_due is not None and current_mileage:
                miles_until = next_due - current_mileage
                if miles_until < 0:
                    status = 'overdue'
                elif miles_until < 500:
                    status = 'due_soon'
                else:
                    status = 'ok'
            
            schedule['intervals'].append({
                'id': interval['id'],
                'vin': interval.get('vin', ''),
                'service_type': interval['service_type'],
                'interval_miles': interval.get('interval_miles'),
                'interval_months': interval.get('interval_months'),
                'last_performed_date': interval.get('last_performed_date'),
                'last_performed_mileage': interval.get('last_performed_mileage'),
                'next_due_mileage': next_due,
                'next_due_date': interval.get('next_due_date'),
                'miles_until_due': miles_until,
                'status': status,
                'is_custom': interval.get('is_custom', 0),
                'notes': interval.get('notes'),
                'created_at': interval.get('created_at'),
                'updated_at': interval.get('updated_at'),
            })
        
        return schedule
    
    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new maintenance interval."""
        data['vin'] = validate_vin(data.get('vin', ''))
        
        if not data.get('service_type'):
            raise ValidationError("Service type is required")
        
        # Verify vehicle exists
        vehicle = execute_query(
            "SELECT current_mileage FROM vehicles WHERE vin = ?",
            (data['vin'],), fetch_one=True
        )
        if not vehicle:
            raise NotFoundError(f"Vehicle with VIN {data['vin']} not found")
        
        # Check for duplicate
        existing = execute_query("""
            SELECT id FROM maintenance_intervals 
            WHERE vin = ? AND service_type = ?
        """, (data['vin'], data['service_type']), fetch_one=True)
        
        if existing:
            raise ValidationError(
                f"Maintenance interval for '{data['service_type']}' already exists"
            )
        
        # Use defaults if not provided
        if 'interval_miles' not in data and data['service_type'] in DEFAULT_INTERVALS:
            data['interval_miles'] = DEFAULT_INTERVALS[data['service_type']]['miles']
            data['interval_months'] = DEFAULT_INTERVALS[data['service_type']]['months']
        
        # Calculate next_due_mileage if interval_miles is provided
        current_mileage = vehicle.get('current_mileage', 0) or 0
        if 'interval_miles' in data and data['interval_miles'] and not data.get('next_due_mileage'):
            data['next_due_mileage'] = current_mileage + data['interval_miles']
        
        return super().create(data)
    
    @classmethod
    def record_service(
        cls, 
        vin: str, 
        service_type: str, 
        date: str = None,
        mileage: int = None
    ) -> Dict[str, Any]:
        """Record that a maintenance service was performed."""
        vin = validate_vin(vin)
        
        if date:
            date = validate_date(date)
        else:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Get the interval record
        interval = execute_query("""
            SELECT * FROM maintenance_intervals 
            WHERE vin = ? AND service_type = ?
        """, (vin, service_type), fetch_one=True)
        
        if not interval:
            raise NotFoundError(f"No maintenance interval found for '{service_type}'")
        
        # Get vehicle mileage if not provided
        if mileage is None:
            vehicle = execute_query(
                "SELECT current_mileage FROM vehicles WHERE vin = ?",
                (vin,), fetch_one=True
            )
            mileage = vehicle['current_mileage'] if vehicle else 0
        else:
            mileage = int(validate_positive_number(mileage, 'Mileage'))
        
        # Calculate next due
        next_mileage = None
        next_date = None
        
        if interval['interval_miles']:
            next_mileage = mileage + interval['interval_miles']
        
        if interval['interval_months']:
            next_date = (
                datetime.strptime(date, '%Y-%m-%d') + 
                timedelta(days=interval['interval_months'] * 30)
            ).strftime('%Y-%m-%d')
        
        # Update the interval
        return cls.update(interval['id'], {
            'last_performed_date': date,
            'last_performed_mileage': mileage,
            'next_due_date': next_date,
            'next_due_mileage': next_mileage
        })
    
    @classmethod
    def get_upcoming(cls, vin: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get upcoming maintenance items."""
        vin = validate_vin(vin)
        
        query = """
            SELECT * FROM maintenance_intervals 
            WHERE vin = ? AND next_due_mileage IS NOT NULL
            ORDER BY next_due_mileage ASC
            LIMIT ?
        """
        return execute_query(query, (vin, limit))
    
    @classmethod
    def get_overdue(cls, vin: str) -> List[Dict[str, Any]]:
        """Get overdue maintenance items."""
        vin = validate_vin(vin)
        
        # Get vehicle current mileage
        vehicle = execute_query(
            "SELECT current_mileage FROM vehicles WHERE vin = ?",
            (vin,), fetch_one=True
        )
        
        if not vehicle or not vehicle['current_mileage']:
            return []
        
        current_mileage = vehicle['current_mileage']
        
        query = """
            SELECT * FROM maintenance_intervals 
            WHERE vin = ? AND next_due_mileage < ?
            ORDER BY next_due_mileage ASC
        """
        return execute_query(query, (vin, current_mileage))
    
    @classmethod
    def initialize_for_vehicle(cls, vin: str) -> List[Dict[str, Any]]:
        """Initialize default maintenance intervals for a new vehicle."""
        vin = validate_vin(vin)
        
        # Get vehicle to get current mileage
        vehicle = execute_query(
            "SELECT current_mileage FROM vehicles WHERE vin = ?",
            (vin,), fetch_one=True
        )
        
        if not vehicle:
            raise NotFoundError(f"Vehicle with VIN {vin} not found")
        
        current_mileage = vehicle['current_mileage'] or 0
        created = []
        
        for service_type, intervals in DEFAULT_INTERVALS.items():
            # Check if already exists
            existing = execute_query("""
                SELECT id FROM maintenance_intervals 
                WHERE vin = ? AND service_type = ?
            """, (vin, service_type), fetch_one=True)
            
            if not existing:
                next_mileage = current_mileage + intervals['miles']
                
                execute_insert('maintenance_intervals', {
                    'vin': vin,
                    'service_type': service_type,
                    'interval_miles': intervals['miles'],
                    'interval_months': intervals['months'],
                    'next_due_mileage': next_mileage
                })
                created.append(service_type)
        
        return cls.get_by_vin(vin)


# Legacy function for backward compatibility
def get_maintenance_by_vin(vin: str) -> Optional[Dict[str, Any]]:
    """Legacy function - returns maintenance in old format."""
    try:
        intervals = MaintenanceService.get_by_vin(vin)
        
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
        
        return result if len(result) > 1 else None
    except ValidationError:
        return None
