"""
Trip Service
============
Handles trip tracking and mileage logging for business/personal trips.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
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

# Common trip purposes
TRIP_PURPOSES = ['Commute', 'Business', 'Personal', 'Road Trip', 'Errand', 'Medical', 'Other']


class TripService(BaseService):
    """Service for trip CRUD operations."""
    
    table_name = "trips"
    primary_key = "id"
    required_fields = ["vin", "date"]
    allowed_fields = [
        "vin", "start_location", "end_location", "start_mileage", 
        "end_mileage", "distance", "date", "purpose", "is_business", "notes"
    ]
    
    @classmethod
    def get_by_vin(
        cls, 
        vin: str, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all trips for a vehicle."""
        vin = validate_vin(vin)
        
        query = """
            SELECT * FROM trips 
            WHERE vin = ?
            ORDER BY date DESC, id DESC
            LIMIT ? OFFSET ?
        """
        return execute_query(query, (vin, limit, offset))
    
    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new trip record."""
        data['vin'] = validate_vin(data.get('vin', ''))
        data['date'] = validate_date(data.get('date', ''))
        
        # Validate mileage fields if provided
        if 'start_mileage' in data and data['start_mileage'] is not None:
            data['start_mileage'] = int(validate_positive_number(
                data['start_mileage'], 'Start mileage'
            ))
        
        if 'end_mileage' in data and data['end_mileage'] is not None:
            data['end_mileage'] = int(validate_positive_number(
                data['end_mileage'], 'End mileage'
            ))
        
        # Calculate distance if both mileages provided
        if data.get('start_mileage') and data.get('end_mileage'):
            if data['end_mileage'] < data['start_mileage']:
                raise ValidationError("End mileage cannot be less than start mileage")
            data['distance'] = data['end_mileage'] - data['start_mileage']
        elif 'distance' in data and data['distance'] is not None:
            data['distance'] = validate_positive_number(data['distance'], 'Distance')
        
        # Default is_business to 0
        if 'is_business' not in data:
            data['is_business'] = 0
        else:
            data['is_business'] = 1 if data['is_business'] else 0
        
        return super().create(data)
    
    @classmethod
    def update(cls, trip_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a trip record."""
        # Don't allow VIN updates
        data.pop('vin', None)
        
        if 'date' in data:
            data['date'] = validate_date(data['date'])
        
        if 'is_business' in data:
            data['is_business'] = 1 if data['is_business'] else 0
        
        # Recalculate distance if mileages updated
        if 'start_mileage' in data or 'end_mileage' in data:
            existing = cls.get_by_id(trip_id)
            start = data.get('start_mileage', existing.get('start_mileage'))
            end = data.get('end_mileage', existing.get('end_mileage'))
            if start and end:
                data['distance'] = end - start
        
        return super().update(trip_id, data)
    
    @classmethod
    def get_business_trips(
        cls, 
        vin: str, 
        year: int = None
    ) -> List[Dict[str, Any]]:
        """Get all business trips for a vehicle."""
        vin = validate_vin(vin)
        
        query = "SELECT * FROM trips WHERE vin = ? AND is_business = 1"
        params = [vin]
        
        if year:
            query += " AND strftime('%Y', date) = ?"
            params.append(str(year))
        
        query += " ORDER BY date DESC"
        return execute_query(query, tuple(params))
    
    @classmethod
    def get_mileage_summary(cls, vin: str, year: int = None) -> Dict[str, Any]:
        """Get trip mileage summary."""
        vin = validate_vin(vin)
        
        where_clause = "vin = ?"
        params = [vin]
        
        if year:
            where_clause += " AND strftime('%Y', date) = ?"
            params.append(str(year))
        
        query = f"""
            SELECT 
                COUNT(*) as total_trips,
                COALESCE(SUM(distance), 0) as total_miles,
                SUM(CASE WHEN is_business = 1 THEN distance ELSE 0 END) as business_miles,
                SUM(CASE WHEN is_business = 0 THEN distance ELSE 0 END) as personal_miles,
                SUM(CASE WHEN is_business = 1 THEN 1 ELSE 0 END) as business_trips,
                SUM(CASE WHEN is_business = 0 THEN 1 ELSE 0 END) as personal_trips
            FROM trips 
            WHERE {where_clause}
        """
        result = execute_query(query, tuple(params), fetch_one=True)
        
        if not result:
            return {
                'total_trips': 0,
                'total_miles': 0,
                'business_miles': 0,
                'personal_miles': 0,
                'business_trips': 0,
                'personal_trips': 0
            }
        
        return dict(result)
    
    @classmethod
    def get_by_purpose(cls, vin: str, purpose: str) -> List[Dict[str, Any]]:
        """Get trips by purpose."""
        vin = validate_vin(vin)
        
        query = """
            SELECT * FROM trips 
            WHERE vin = ? AND purpose = ?
            ORDER BY date DESC
        """
        return execute_query(query, (vin, purpose))
    
    @classmethod
    def get_by_date_range(
        cls, 
        vin: str, 
        start_date: str, 
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Get trips within a date range."""
        vin = validate_vin(vin)
        start_date = validate_date(start_date)
        end_date = validate_date(end_date)
        
        query = """
            SELECT * FROM trips 
            WHERE vin = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC
        """
        return execute_query(query, (vin, start_date, end_date))
    
    @classmethod
    def get_recent(cls, vin: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent trips."""
        return cls.get_by_vin(vin, limit=limit)
    
    @classmethod
    def get_purpose_breakdown(cls, vin: str) -> List[Dict[str, Any]]:
        """Get breakdown of trips by purpose."""
        vin = validate_vin(vin)
        
        query = """
            SELECT 
                purpose,
                COUNT(*) as trip_count,
                COALESCE(SUM(distance), 0) as total_miles
            FROM trips 
            WHERE vin = ?
            GROUP BY purpose
            ORDER BY trip_count DESC
        """
        return execute_query(query, (vin,))

