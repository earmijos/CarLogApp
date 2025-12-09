"""
CarLog Database Package
=======================
Provides database access and management utilities.
"""

from .db_helper import (
    get_connection,
    connection,
    transaction,
    execute_query,
    execute_insert,
    execute_update,
    execute_delete,
    row_to_dict,
    rows_to_list,
    table_exists,
    count_rows,
    ensure_initialized,
)

__all__ = [
    'get_connection',
    'connection',
    'transaction', 
    'execute_query',
    'execute_insert',
    'execute_update',
    'execute_delete',
    'row_to_dict',
    'rows_to_list',
    'table_exists',
    'count_rows',
    'ensure_initialized',
]

