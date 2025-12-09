"""
Fuel Log Service
================
Handles fuel log tracking and MPG calculations.
"""

from typing import Optional, List, Dict, Any
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.db_helper import connection, execute_query
from services.base_service import (
    BaseService, 
    ValidationError, 
    NotFoundError,
    validate_vin,
    validate_date,
    validate_positive_number
)


class FuelLogService(BaseService):
    """Service for fuel log CRUD operations."""
    
    table_name = "fuel_logs"
    primary_key = "id"
    required_fields = ["vin", "gallons", "price_per_gallon", "odometer", "date"]
    allowed_fields = [
        "vin", "gallons", "price_per_gallon", "total_cost", "odometer",
        "date", "station", "fuel_type", "full_tank", "notes"
    ]
    
    @classmethod
    def get_by_vin(
        cls, 
        vin: str, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all fuel logs for a vehicle."""
        vin = validate_vin(vin)
        
        query = """
            SELECT * FROM fuel_logs 
            WHERE vin = ?
            ORDER BY date DESC, odometer DESC
            LIMIT ? OFFSET ?
        """
        return execute_query(query, (vin, limit, offset))
    
    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new fuel log entry."""
        # Validate VIN
        data['vin'] = validate_vin(data.get('vin', ''))
        
        # Validate date
        data['date'] = validate_date(data.get('date', ''))
        
        # Validate numeric fields
        data['gallons'] = validate_positive_number(data.get('gallons'), 'Gallons')
        data['price_per_gallon'] = validate_positive_number(
            data.get('price_per_gallon'), 'Price per gallon'
        )
        data['odometer'] = int(validate_positive_number(data.get('odometer'), 'Odometer'))
        
        # Calculate total cost if not provided
        if 'total_cost' not in data or data['total_cost'] is None:
            data['total_cost'] = round(data['gallons'] * data['price_per_gallon'], 2)
        
        # Default fuel type
        if 'fuel_type' not in data:
            data['fuel_type'] = 'Regular'
        
        # Default full tank
        if 'full_tank' not in data:
            data['full_tank'] = 1
        
        return super().create(data)
    
    @classmethod
    def update(cls, log_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a fuel log entry."""
        # Don't allow VIN updates
        data.pop('vin', None)
        
        # Validate date if provided
        if 'date' in data:
            data['date'] = validate_date(data['date'])
        
        # Validate numeric fields if provided
        if 'gallons' in data:
            data['gallons'] = validate_positive_number(data['gallons'], 'Gallons')
        if 'price_per_gallon' in data:
            data['price_per_gallon'] = validate_positive_number(
                data['price_per_gallon'], 'Price per gallon'
            )
        if 'odometer' in data:
            data['odometer'] = int(validate_positive_number(data['odometer'], 'Odometer'))
        
        # Recalculate total if gallons or price changed
        if 'gallons' in data or 'price_per_gallon' in data:
            existing = cls.get_by_id(log_id)
            gallons = data.get('gallons', existing['gallons'])
            price = data.get('price_per_gallon', existing['price_per_gallon'])
            data['total_cost'] = round(gallons * price, 2)
        
        return super().update(log_id, data)
    
    @classmethod
    def calculate_mpg(cls, vin: str, limit: int = 10) -> Dict[str, Any]:
        """Calculate MPG from recent fuel logs."""
        vin = validate_vin(vin)
        
        # Get fuel logs with full tanks, ordered by odometer
        logs = execute_query("""
            SELECT gallons, odometer, date
            FROM fuel_logs 
            WHERE vin = ? AND full_tank = 1
            ORDER BY odometer DESC
            LIMIT ?
        """, (vin, limit + 1))
        
        if len(logs) < 2:
            return {
                'average_mpg': None,
                'last_mpg': None,
                'logs_used': 0,
                'message': 'Need at least 2 full tank fill-ups to calculate MPG'
            }
        
        mpg_values = []
        for i in range(len(logs) - 1):
            miles = logs[i]['odometer'] - logs[i + 1]['odometer']
            gallons = logs[i]['gallons']
            if gallons > 0 and miles > 0:
                mpg_values.append(miles / gallons)
        
        if not mpg_values:
            return {
                'average_mpg': None,
                'last_mpg': None,
                'logs_used': 0,
                'message': 'Unable to calculate MPG from available data'
            }
        
        return {
            'average_mpg': round(sum(mpg_values) / len(mpg_values), 1),
            'last_mpg': round(mpg_values[0], 1),
            'best_mpg': round(max(mpg_values), 1),
            'worst_mpg': round(min(mpg_values), 1),
            'logs_used': len(mpg_values)
        }
    
    @classmethod
    def get_cost_summary(cls, vin: str) -> Dict[str, Any]:
        """Get fuel cost summary for a vehicle."""
        vin = validate_vin(vin)
        
        result = execute_query("""
            SELECT 
                COUNT(*) as fill_ups,
                COALESCE(SUM(gallons), 0) as total_gallons,
                COALESCE(SUM(total_cost), 0) as total_cost,
                COALESCE(AVG(price_per_gallon), 0) as avg_price,
                MIN(odometer) as first_odometer,
                MAX(odometer) as last_odometer
            FROM fuel_logs 
            WHERE vin = ?
        """, (vin,), fetch_one=True)
        
        if not result or result['fill_ups'] == 0:
            return {
                'fill_ups': 0,
                'total_gallons': 0,
                'total_cost': 0,
                'avg_price_per_gallon': 0,
                'total_miles': 0,
                'cost_per_mile': 0
            }
        
        total_miles = (result['last_odometer'] or 0) - (result['first_odometer'] or 0)
        cost_per_mile = (
            result['total_cost'] / total_miles if total_miles > 0 else 0
        )
        
        return {
            'fill_ups': result['fill_ups'],
            'total_gallons': round(result['total_gallons'], 2),
            'total_cost': round(result['total_cost'], 2),
            'avg_price_per_gallon': round(result['avg_price'], 3),
            'total_miles': total_miles,
            'cost_per_mile': round(cost_per_mile, 3)
        }
    
    @classmethod
    def get_recent(cls, vin: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most recent fuel logs for a vehicle."""
        return cls.get_by_vin(vin, limit=limit)
    
    @classmethod
    def get_by_date_range(
        cls, 
        vin: str, 
        start_date: str, 
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Get fuel logs within a date range."""
        vin = validate_vin(vin)
        start_date = validate_date(start_date)
        end_date = validate_date(end_date)
        
        query = """
            SELECT * FROM fuel_logs 
            WHERE vin = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC
        """
        return execute_query(query, (vin, start_date, end_date))


# Legacy function for backward compatibility
def get_all_fuel_log() -> List[Dict[str, Any]]:
    """Legacy function - use FuelLogService.get_all() instead."""
    return FuelLogService.get_all(limit=100)
