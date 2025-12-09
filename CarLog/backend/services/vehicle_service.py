"""
Vehicle Service
===============
Handles all vehicle-related business logic and data access.
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
    validate_positive_number
)
from services.maintenance_service import MaintenanceService


class VehicleService(BaseService):
    """Service for vehicle CRUD operations."""
    
    table_name = "vehicles"
    primary_key = "vin"
    required_fields = ["vin", "year", "make", "model"]
    allowed_fields = [
        "vin", "year", "make", "model", "trim", "engine_type", 
        "color", "purchase_date", "purchase_price", "current_mileage", "user_id"
    ]
    
    @classmethod
    def get_all(
        cls, 
        limit: int = 100, 
        offset: int = 0,
        user_id: int = None
    ) -> List[Dict[str, Any]]:
        """Get all vehicles, optionally filtered by user."""
        query = "SELECT * FROM vehicles"
        params = []
        
        if user_id:
            query += " WHERE user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY make, model LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        return execute_query(query, tuple(params))
    
    @classmethod
    def get_by_vin(cls, vin: str) -> Optional[Dict[str, Any]]:
        """Get a vehicle by VIN."""
        vin = validate_vin(vin)
        return cls.get_by_id(vin)
    
    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new vehicle."""
        # Validate VIN
        data['vin'] = validate_vin(data.get('vin', ''))
        
        # Validate year
        year = data.get('year')
        if not year or not (1900 <= int(year) <= 2100):
            raise ValidationError("Year must be between 1900 and 2100")
        
        # Check if VIN already exists
        if cls.exists(data['vin']):
            raise ValidationError(f"Vehicle with VIN {data['vin']} already exists")
        
        # Validate mileage if provided
        if 'current_mileage' in data and data['current_mileage'] is not None:
            data['current_mileage'] = int(validate_positive_number(
                data['current_mileage'], 'Mileage'
            ))
        
        # Create the vehicle
        vehicle = super().create(data)
        
        # Auto-initialize maintenance intervals for the new vehicle
        try:
            MaintenanceService.initialize_for_vehicle(data['vin'])
        except Exception:
            pass  # Don't fail vehicle creation if maintenance init fails
        
        return vehicle
    
    @classmethod
    def update(cls, vin: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a vehicle."""
        vin = validate_vin(vin)
        
        # Don't allow VIN updates
        data.pop('vin', None)
        
        # Validate mileage if provided
        if 'current_mileage' in data and data['current_mileage'] is not None:
            data['current_mileage'] = int(validate_positive_number(
                data['current_mileage'], 'Mileage'
            ))
        
        return super().update(vin, data)
    
    @classmethod
    def delete(cls, vin: str) -> bool:
        """Delete a vehicle and all related data (cascades)."""
        vin = validate_vin(vin)
        
        # Explicitly delete related records to ensure cascade works
        # (SQLite foreign keys should handle this, but being explicit)
        from db.db_helper import execute_delete
        
        # Delete in order: trips, fuel_logs, repairs, maintenance_intervals, mileage_history
        execute_delete('trips', 'vin = ?', (vin,))
        execute_delete('fuel_logs', 'vin = ?', (vin,))
        execute_delete('repairs', 'vin = ?', (vin,))
        execute_delete('maintenance_intervals', 'vin = ?', (vin,))
        execute_delete('mileage_history', 'vin = ?', (vin,))
        
        # Finally delete the vehicle
        return super().delete(vin)
    
    @classmethod
    def update_mileage(cls, vin: str, mileage: int) -> Dict[str, Any]:
        """Update vehicle's current mileage."""
        vin = validate_vin(vin)
        mileage = int(validate_positive_number(mileage, 'Mileage'))
        
        vehicle = cls.get_by_vin(vin)
        if not vehicle:
            raise NotFoundError(f"Vehicle with VIN {vin} not found")
        
        # Mileage should not decrease
        current = vehicle.get('current_mileage', 0) or 0
        if mileage < current:
            raise ValidationError(
                f"New mileage ({mileage}) cannot be less than current ({current})"
            )
        
        return cls.update(vin, {'current_mileage': mileage})
    
    @classmethod
    def search(
        cls, 
        query: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search vehicles by make, model, or VIN."""
        search_query = """
            SELECT * FROM vehicles 
            WHERE vin LIKE ? OR make LIKE ? OR model LIKE ?
            ORDER BY year DESC, make, model
            LIMIT ?
        """
        pattern = f"%{query}%"
        return execute_query(search_query, (pattern, pattern, pattern, limit))
    
    @classmethod
    def get_summary(cls, vin: str) -> Dict[str, Any]:
        """Get a summary of vehicle with related stats."""
        vin = validate_vin(vin)
        
        vehicle = cls.get_by_vin(vin)
        if not vehicle:
            raise NotFoundError(f"Vehicle with VIN {vin} not found")
        
        # Get repair count and total cost
        repair_stats = execute_query("""
            SELECT COUNT(*) as count, COALESCE(SUM(cost), 0) as total_cost
            FROM repairs WHERE vin = ?
        """, (vin,), fetch_one=True)
        
        # Get fuel log count
        fuel_stats = execute_query("""
            SELECT COUNT(*) as count, COALESCE(SUM(total_cost), 0) as total_cost
            FROM fuel_logs WHERE vin = ?
        """, (vin,), fetch_one=True)
        
        # Get upcoming maintenance
        upcoming = execute_query("""
            SELECT service_type, next_due_mileage
            FROM maintenance_intervals 
            WHERE vin = ? AND next_due_mileage IS NOT NULL
            ORDER BY next_due_mileage ASC
            LIMIT 3
        """, (vin,))
        
        return {
            **dict(vehicle),
            'repair_count': repair_stats['count'],
            'repair_total_cost': repair_stats['total_cost'],
            'fuel_log_count': fuel_stats['count'],
            'fuel_total_cost': fuel_stats['total_cost'],
            'upcoming_maintenance': [dict(m) for m in upcoming]
        }


# Legacy function for backward compatibility
def get_vehicle_by_vin(vin: str) -> Optional[Dict[str, Any]]:
    """Legacy function - use VehicleService.get_by_vin() instead."""
    try:
        return VehicleService.get_by_vin(vin)
    except ValidationError:
        return None

