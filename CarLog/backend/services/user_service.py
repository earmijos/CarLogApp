"""
User Service
============
Handles local user management.
"""

from typing import Optional, List, Dict, Any
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.db_helper import connection, execute_query
from services.base_service import BaseService, ValidationError, NotFoundError


class UserService(BaseService):
    """Service for user CRUD operations."""
    
    table_name = "users"
    primary_key = "id"
    required_fields = ["name"]
    allowed_fields = ["name", "email"]
    
    @classmethod
    def get_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        """Get a user by email."""
        if not email:
            return None
        
        query = "SELECT * FROM users WHERE email = ?"
        return execute_query(query, (email.lower().strip(),), fetch_one=True)
    
    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        if not data.get('name'):
            raise ValidationError("Name is required")
        
        data['name'] = data['name'].strip()
        
        if 'email' in data and data['email']:
            data['email'] = data['email'].lower().strip()
            
            # Check for duplicate email
            existing = cls.get_by_email(data['email'])
            if existing:
                raise ValidationError(f"User with email {data['email']} already exists")
        
        return super().create(data)
    
    @classmethod
    def update(cls, user_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a user."""
        if 'name' in data:
            data['name'] = data['name'].strip()
            if not data['name']:
                raise ValidationError("Name cannot be empty")
        
        if 'email' in data and data['email']:
            data['email'] = data['email'].lower().strip()
            
            # Check for duplicate email (excluding this user)
            existing = cls.get_by_email(data['email'])
            if existing and existing['id'] != user_id:
                raise ValidationError(f"User with email {data['email']} already exists")
        
        return super().update(user_id, data)
    
    @classmethod
    def get_default_user(cls) -> Dict[str, Any]:
        """Get or create the default user."""
        # Try to get existing default user
        user = execute_query(
            "SELECT * FROM users ORDER BY id ASC LIMIT 1",
            fetch_one=True
        )
        
        if user:
            return dict(user)
        
        # Create default user
        return cls.create({
            'name': 'Default User',
            'email': 'user@carlog.local'
        })
    
    @classmethod
    def get_user_vehicles(cls, user_id: int) -> List[Dict[str, Any]]:
        """Get all vehicles for a user."""
        query = """
            SELECT * FROM vehicles 
            WHERE user_id = ?
            ORDER BY make, model
        """
        return execute_query(query, (user_id,))
    
    @classmethod
    def get_user_stats(cls, user_id: int) -> Dict[str, Any]:
        """Get statistics for a user."""
        # Get vehicle count
        vehicles = execute_query(
            "SELECT COUNT(*) as count FROM vehicles WHERE user_id = ?",
            (user_id,), fetch_one=True
        )
        
        # Get total repair cost
        repairs = execute_query("""
            SELECT COUNT(*) as count, COALESCE(SUM(cost), 0) as total
            FROM repairs r
            JOIN vehicles v ON r.vin = v.vin
            WHERE v.user_id = ?
        """, (user_id,), fetch_one=True)
        
        # Get total fuel cost
        fuel = execute_query("""
            SELECT COUNT(*) as count, COALESCE(SUM(total_cost), 0) as total
            FROM fuel_logs f
            JOIN vehicles v ON f.vin = v.vin
            WHERE v.user_id = ?
        """, (user_id,), fetch_one=True)
        
        return {
            'vehicle_count': vehicles['count'] if vehicles else 0,
            'repair_count': repairs['count'] if repairs else 0,
            'repair_total_cost': round(repairs['total'] if repairs else 0, 2),
            'fuel_log_count': fuel['count'] if fuel else 0,
            'fuel_total_cost': round(fuel['total'] if fuel else 0, 2),
            'total_cost': round(
                (repairs['total'] if repairs else 0) + 
                (fuel['total'] if fuel else 0), 2
            )
        }


# Convenience function
def get_or_create_default_user() -> Dict[str, Any]:
    """Get or create the default user."""
    return UserService.get_default_user()

