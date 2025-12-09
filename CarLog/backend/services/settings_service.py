"""
Settings Service
================
Handles user and application settings.
"""

from typing import Optional, List, Dict, Any
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.db_helper import connection, execute_query, execute_insert
from services.base_service import BaseService, ValidationError


# Default settings
DEFAULT_SETTINGS = {
    'distance_unit': 'miles',
    'fuel_unit': 'gallons', 
    'currency': 'USD',
    'currency_symbol': '$',
    'date_format': 'YYYY-MM-DD',
    'theme': 'light',
    'notifications_enabled': 'true',
    'maintenance_reminder_miles': '500',
    'fuel_grade_default': 'Regular',
}


class SettingsService(BaseService):
    """Service for settings CRUD operations."""
    
    table_name = "settings"
    primary_key = "id"
    required_fields = ["key"]
    allowed_fields = ["key", "value", "user_id"]
    
    @classmethod
    def get(cls, key: str, user_id: int = None) -> Optional[str]:
        """Get a setting value by key."""
        query = "SELECT value FROM settings WHERE key = ?"
        params = [key]
        
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        else:
            query += " AND user_id IS NULL"
        
        query += " ORDER BY user_id DESC LIMIT 1"
        
        result = execute_query(query, tuple(params), fetch_one=True)
        
        if result:
            return result['value']
        
        # Return default if exists
        return DEFAULT_SETTINGS.get(key)
    
    @classmethod
    def set(cls, key: str, value: str, user_id: int = None) -> Dict[str, Any]:
        """Set a setting value."""
        if not key:
            raise ValidationError("Setting key is required")
        
        # Check if setting exists
        query = "SELECT id FROM settings WHERE key = ?"
        params = [key]
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        else:
            query += " AND user_id IS NULL"
        
        existing = execute_query(query, tuple(params), fetch_one=True)
        
        if existing:
            # Update existing
            with connection() as conn:
                conn.execute(
                    "UPDATE settings SET value = ?, updated_at = datetime('now') WHERE id = ?",
                    (value, existing['id'])
                )
            return {'key': key, 'value': value, 'user_id': user_id}
        else:
            # Create new
            execute_insert('settings', {
                'key': key,
                'value': value,
                'user_id': user_id
            })
            return {'key': key, 'value': value, 'user_id': user_id}
    
    @classmethod
    def get_all(cls, user_id: int = None) -> Dict[str, str]:
        """Get all settings as a dictionary."""
        query = "SELECT key, value FROM settings"
        
        if user_id:
            query += " WHERE user_id = ? OR user_id IS NULL"
            results = execute_query(query, (user_id,))
        else:
            query += " WHERE user_id IS NULL"
            results = execute_query(query)
        
        # Start with defaults
        settings = dict(DEFAULT_SETTINGS)
        
        # Override with stored values
        for r in results:
            settings[r['key']] = r['value']
        
        return settings
    
    @classmethod
    def delete(cls, key: str, user_id: int = None) -> bool:
        """Delete a setting."""
        query = "DELETE FROM settings WHERE key = ?"
        params = [key]
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        else:
            query += " AND user_id IS NULL"
        
        with connection() as conn:
            cursor = conn.execute(query, tuple(params))
            return cursor.rowcount > 0
    
    @classmethod
    def reset_to_defaults(cls, user_id: int = None) -> Dict[str, str]:
        """Reset all settings to defaults."""
        # Delete user's settings
        query = "DELETE FROM settings"
        if user_id:
            query += " WHERE user_id = ?"
            with connection() as conn:
                conn.execute(query, (user_id,))
        else:
            query += " WHERE user_id IS NULL"
            with connection() as conn:
                conn.execute(query)
        
        # Insert defaults
        for key, value in DEFAULT_SETTINGS.items():
            execute_insert('settings', {
                'key': key,
                'value': value,
                'user_id': user_id
            })
        
        return dict(DEFAULT_SETTINGS)
    
    @classmethod
    def get_theme(cls, user_id: int = None) -> str:
        """Get the current theme setting."""
        return cls.get('theme', user_id) or 'light'
    
    @classmethod
    def set_theme(cls, theme: str, user_id: int = None) -> Dict[str, Any]:
        """Set the theme."""
        if theme not in ['light', 'dark', 'system']:
            raise ValidationError("Theme must be 'light', 'dark', or 'system'")
        return cls.set('theme', theme, user_id)
    
    @classmethod
    def get_units(cls, user_id: int = None) -> Dict[str, str]:
        """Get distance and fuel unit settings."""
        return {
            'distance': cls.get('distance_unit', user_id) or 'miles',
            'fuel': cls.get('fuel_unit', user_id) or 'gallons',
            'currency': cls.get('currency', user_id) or 'USD',
            'currency_symbol': cls.get('currency_symbol', user_id) or '$'
        }

