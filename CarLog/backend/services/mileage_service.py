"""
Mileage Service
===============
Handles mileage tracking and history.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.db_helper import connection, execute_query, execute_update
from services.base_service import (
    BaseService, 
    ValidationError, 
    NotFoundError,
    validate_vin,
    validate_date,
    validate_positive_number
)


class MileageService(BaseService):
    """Service for mileage history CRUD operations."""
    
    table_name = "mileage_history"
    primary_key = "id"
    required_fields = ["vin", "mileage", "date"]
    allowed_fields = ["vin", "mileage", "date", "source", "notes"]
    
    @classmethod
    def get_by_vin(
        cls, 
        vin: str, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get mileage history for a vehicle."""
        vin = validate_vin(vin)
        
        query = """
            SELECT * FROM mileage_history 
            WHERE vin = ?
            ORDER BY date DESC, mileage DESC
            LIMIT ? OFFSET ?
        """
        return execute_query(query, (vin, limit, offset))
    
    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a new mileage entry."""
        data['vin'] = validate_vin(data.get('vin', ''))
        data['date'] = validate_date(data.get('date', ''))
        data['mileage'] = int(validate_positive_number(data.get('mileage'), 'Mileage'))
        
        if 'source' not in data:
            data['source'] = 'manual'
        
        # Also update vehicle's current mileage if this is higher
        vehicle = execute_query(
            "SELECT current_mileage FROM vehicles WHERE vin = ?",
            (data['vin'],), fetch_one=True
        )
        
        if vehicle:
            current = vehicle['current_mileage'] or 0
            if data['mileage'] > current:
                execute_update(
                    'vehicles', 
                    {'current_mileage': data['mileage']},
                    'vin = ?',
                    (data['vin'],)
                )
        
        return super().create(data)
    
    @classmethod
    def get_latest(cls, vin: str) -> Optional[Dict[str, Any]]:
        """Get the latest mileage reading for a vehicle."""
        vin = validate_vin(vin)
        
        query = """
            SELECT * FROM mileage_history 
            WHERE vin = ?
            ORDER BY mileage DESC
            LIMIT 1
        """
        return execute_query(query, (vin,), fetch_one=True)
    
    @classmethod
    def get_by_date_range(
        cls, 
        vin: str, 
        start_date: str, 
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Get mileage history within a date range."""
        vin = validate_vin(vin)
        start_date = validate_date(start_date)
        end_date = validate_date(end_date)
        
        query = """
            SELECT * FROM mileage_history 
            WHERE vin = ? AND date BETWEEN ? AND ?
            ORDER BY date ASC
        """
        return execute_query(query, (vin, start_date, end_date))
    
    @classmethod
    def calculate_average_daily_miles(
        cls, 
        vin: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Calculate average daily miles driven."""
        vin = validate_vin(vin)
        
        # Get oldest and newest readings within the period
        query = """
            SELECT MIN(mileage) as min_mileage, MAX(mileage) as max_mileage,
                   MIN(date) as first_date, MAX(date) as last_date,
                   COUNT(*) as readings
            FROM mileage_history 
            WHERE vin = ? AND date >= date('now', ?)
        """
        result = execute_query(query, (vin, f'-{days} days'), fetch_one=True)
        
        if not result or result['readings'] < 2:
            return {
                'average_daily_miles': None,
                'total_miles': 0,
                'days_tracked': 0,
                'message': 'Not enough data to calculate'
            }
        
        total_miles = (result['max_mileage'] or 0) - (result['min_mileage'] or 0)
        
        # Calculate actual days between readings
        first = datetime.strptime(result['first_date'], '%Y-%m-%d')
        last = datetime.strptime(result['last_date'], '%Y-%m-%d')
        days_tracked = (last - first).days or 1
        
        return {
            'average_daily_miles': round(total_miles / days_tracked, 1),
            'total_miles': total_miles,
            'days_tracked': days_tracked,
            'estimated_yearly_miles': round((total_miles / days_tracked) * 365)
        }
    
    @classmethod
    def get_monthly_summary(cls, vin: str, months: int = 6) -> List[Dict[str, Any]]:
        """Get monthly mileage summary."""
        vin = validate_vin(vin)
        
        query = """
            SELECT 
                strftime('%Y-%m', date) as month,
                MIN(mileage) as start_mileage,
                MAX(mileage) as end_mileage,
                MAX(mileage) - MIN(mileage) as miles_driven,
                COUNT(*) as readings
            FROM mileage_history 
            WHERE vin = ? AND date >= date('now', ?)
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month DESC
        """
        return execute_query(query, (vin, f'-{months} months'))

