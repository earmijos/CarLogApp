"""
Repair Service
==============
Handles all repair-related business logic and data access.
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


class RepairService(BaseService):
    """Service for repair CRUD operations."""
    
    table_name = "repairs"
    primary_key = "id"
    required_fields = ["vin", "service", "date"]
    allowed_fields = [
        "vin", "service", "description", "cost", "mileage", 
        "date", "shop_name", "notes"
    ]
    
    @classmethod
    def get_by_vin(
        cls, 
        vin: str, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all repairs for a vehicle."""
        vin = validate_vin(vin)
        
        query = """
            SELECT * FROM repairs 
            WHERE vin = ?
            ORDER BY date DESC, id DESC
            LIMIT ? OFFSET ?
        """
        return execute_query(query, (vin, limit, offset))
    
    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new repair record."""
        # Validate VIN
        data['vin'] = validate_vin(data.get('vin', ''))
        
        # Validate date
        data['date'] = validate_date(data.get('date', ''))
        
        # Validate cost
        if 'cost' in data and data['cost'] is not None:
            data['cost'] = validate_positive_number(data['cost'], 'Cost')
        else:
            data['cost'] = 0
        
        # Validate mileage
        if 'mileage' in data and data['mileage'] is not None:
            data['mileage'] = int(validate_positive_number(data['mileage'], 'Mileage'))
        
        return super().create(data)
    
    @classmethod
    def update(cls, repair_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a repair record."""
        # Don't allow VIN updates
        data.pop('vin', None)
        
        # Validate date if provided
        if 'date' in data:
            data['date'] = validate_date(data['date'])
        
        # Validate cost if provided
        if 'cost' in data and data['cost'] is not None:
            data['cost'] = validate_positive_number(data['cost'], 'Cost')
        
        return super().update(repair_id, data)
    
    @classmethod
    def get_total_cost(cls, vin: str) -> float:
        """Get total repair cost for a vehicle."""
        vin = validate_vin(vin)
        
        result = execute_query(
            "SELECT COALESCE(SUM(cost), 0) as total FROM repairs WHERE vin = ?",
            (vin,), fetch_one=True
        )
        return result['total'] if result else 0
    
    @classmethod
    def get_by_date_range(
        cls, 
        vin: str, 
        start_date: str, 
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Get repairs within a date range."""
        vin = validate_vin(vin)
        start_date = validate_date(start_date)
        end_date = validate_date(end_date)
        
        query = """
            SELECT * FROM repairs 
            WHERE vin = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC
        """
        return execute_query(query, (vin, start_date, end_date))
    
    @classmethod
    def get_recent(cls, vin: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most recent repairs for a vehicle."""
        vin = validate_vin(vin)
        
        query = """
            SELECT * FROM repairs 
            WHERE vin = ?
            ORDER BY date DESC, id DESC
            LIMIT ?
        """
        return execute_query(query, (vin, limit))
    
    @classmethod
    def get_cost_summary(cls, vin: str) -> Dict[str, Any]:
        """Get cost summary by service type."""
        vin = validate_vin(vin)
        
        query = """
            SELECT 
                service,
                COUNT(*) as count,
                SUM(cost) as total_cost,
                AVG(cost) as avg_cost,
                MAX(date) as last_date
            FROM repairs 
            WHERE vin = ?
            GROUP BY service
            ORDER BY total_cost DESC
        """
        services = execute_query(query, (vin,))
        
        total = execute_query(
            "SELECT COALESCE(SUM(cost), 0) as total FROM repairs WHERE vin = ?",
            (vin,), fetch_one=True
        )
        
        return {
            'by_service': [dict(s) for s in services],
            'total_cost': total['total'] if total else 0,
            'repair_count': sum(s['count'] for s in services)
        }


# Legacy functions for backward compatibility
def get_repairs_by_vin(vin: str) -> List[Dict[str, Any]]:
    """Legacy function - use RepairService.get_by_vin() instead."""
    try:
        repairs = RepairService.get_by_vin(vin)
        # Return in legacy format
        return [
            {"service": r['service'], "cost": r['cost'], "date": r['date']}
            for r in repairs
        ]
    except ValidationError:
        return []


def add_repair(vin: str, service: str, cost: float, date: str) -> bool:
    """Legacy function - use RepairService.create() instead."""
    try:
        RepairService.create({
            'vin': vin,
            'service': service,
            'cost': cost,
            'date': date
        })
        return True
    except (ValidationError, Exception):
        return False
