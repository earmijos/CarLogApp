"""
Base Service Class
==================
Provides common CRUD operations and utilities for all services.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.db_helper import (
    connection, 
    execute_query, 
    execute_insert, 
    execute_update, 
    execute_delete,
    count_rows
)

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Base exception for service errors."""
    def __init__(self, message: str, code: str = "SERVICE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(ServiceError):
    """Raised when validation fails."""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class NotFoundError(ServiceError):
    """Raised when a resource is not found."""
    def __init__(self, message: str):
        super().__init__(message, "NOT_FOUND")


class BaseService:
    """
    Base service class with common CRUD operations.
    Subclasses should define:
        - table_name: str
        - primary_key: str
        - required_fields: List[str]
        - allowed_fields: List[str]
    """
    
    table_name: str = None
    primary_key: str = "id"
    required_fields: List[str] = []
    allowed_fields: List[str] = []
    
    @classmethod
    def validate_required(cls, data: Dict[str, Any], fields: List[str] = None) -> None:
        """Validate that required fields are present."""
        fields = fields or cls.required_fields
        missing = [f for f in fields if f not in data or data[f] is None]
        if missing:
            raise ValidationError(f"Missing required fields: {', '.join(missing)}")
    
    @classmethod
    def filter_allowed(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter data to only include allowed fields."""
        if not cls.allowed_fields:
            return data
        return {k: v for k, v in data.items() if k in cls.allowed_fields}
    
    @classmethod
    def get_all(
        cls, 
        limit: int = 100, 
        offset: int = 0,
        order_by: str = None,
        order_dir: str = "DESC"
    ) -> List[Dict[str, Any]]:
        """Get all records with pagination."""
        query = f"SELECT * FROM {cls.table_name}"
        if order_by:
            query += f" ORDER BY {order_by} {order_dir}"
        query += f" LIMIT ? OFFSET ?"
        return execute_query(query, (limit, offset))
    
    @classmethod
    def get_by_id(cls, id_value: Any) -> Optional[Dict[str, Any]]:
        """Get a single record by primary key."""
        query = f"SELECT * FROM {cls.table_name} WHERE {cls.primary_key} = ?"
        return execute_query(query, (id_value,), fetch_one=True)
    
    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record."""
        cls.validate_required(data)
        filtered = cls.filter_allowed(data)
        
        new_id = execute_insert(cls.table_name, filtered)
        return cls.get_by_id(new_id)
    
    @classmethod
    def update(cls, id_value: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing record."""
        existing = cls.get_by_id(id_value)
        if not existing:
            raise NotFoundError(f"{cls.table_name} with {cls.primary_key}={id_value} not found")
        
        filtered = cls.filter_allowed(data)
        if not filtered:
            return existing
        
        execute_update(cls.table_name, filtered, f"{cls.primary_key} = ?", (id_value,))
        return cls.get_by_id(id_value)
    
    @classmethod
    def delete(cls, id_value: Any) -> bool:
        """Delete a record by primary key."""
        existing = cls.get_by_id(id_value)
        if not existing:
            raise NotFoundError(f"{cls.table_name} with {cls.primary_key}={id_value} not found")
        
        rows = execute_delete(cls.table_name, f"{cls.primary_key} = ?", (id_value,))
        return rows > 0
    
    @classmethod
    def count(cls, where: str = None, params: tuple = ()) -> int:
        """Count records, optionally with a filter."""
        return count_rows(cls.table_name, where, params)
    
    @classmethod
    def exists(cls, id_value: Any) -> bool:
        """Check if a record exists."""
        return cls.get_by_id(id_value) is not None


def validate_vin(vin: str) -> str:
    """Validate and normalize a VIN."""
    if not vin:
        raise ValidationError("VIN is required")
    
    vin = vin.strip().upper()
    
    if len(vin) != 17:
        raise ValidationError("VIN must be exactly 17 characters")
    
    # VINs cannot contain I, O, or Q
    invalid_chars = set('IOQ')
    if any(c in invalid_chars for c in vin):
        raise ValidationError("VIN cannot contain I, O, or Q")
    
    return vin


def validate_date(date_str: str) -> str:
    """Validate a date string in YYYY-MM-DD format."""
    if not date_str:
        raise ValidationError("Date is required")
    
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except ValueError:
        raise ValidationError("Date must be in YYYY-MM-DD format")


def validate_positive_number(value: Any, field_name: str) -> float:
    """Validate that a value is a positive number."""
    try:
        num = float(value)
        if num < 0:
            raise ValidationError(f"{field_name} must be a positive number")
        return num
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a valid number")

