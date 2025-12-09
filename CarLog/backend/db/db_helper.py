"""
CarLog Database Helper
======================
Provides database connection management and utility functions.
Implements context managers for safe connection handling.
"""

import sqlite3
import os
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Union

# Setup logging
logger = logging.getLogger(__name__)

# Database path
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "carlog.db")


def get_connection() -> sqlite3.Connection:
    """
    Get a database connection with row factory enabled.
    Returns dict-like rows for easy JSON serialization.
    
    Note: Caller is responsible for closing the connection.
    For automatic handling, use the `connection()` context manager.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connection():
    """
    Context manager for database connections.
    Automatically handles commit/rollback and closing.
    
    Usage:
        with connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vehicles")
            results = cursor.fetchall()
    """
    conn = None
    try:
        conn = get_connection()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


@contextmanager
def transaction():
    """
    Context manager for explicit transactions.
    Use for operations that need atomic commits.
    
    Usage:
        with transaction() as conn:
            conn.execute("INSERT INTO ...")
            conn.execute("UPDATE ...")
            # Auto-commits on success, rolls back on error
    """
    conn = None
    try:
        conn = get_connection()
        conn.execute("BEGIN TRANSACTION")
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Transaction error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a sqlite3.Row to a dictionary."""
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    """Convert a list of sqlite3.Row objects to a list of dictionaries."""
    return [dict(row) for row in rows]


def execute_query(
    query: str, 
    params: tuple = (), 
    fetch_one: bool = False,
    fetch_all: bool = True
) -> Union[Dict[str, Any], List[Dict[str, Any]], int, None]:
    """
    Execute a query and return results.
    
    Args:
        query: SQL query string
        params: Query parameters
        fetch_one: If True, return single row
        fetch_all: If True, return all rows (default)
        
    Returns:
        - For SELECT with fetch_one: dict or None
        - For SELECT with fetch_all: list of dicts
        - For INSERT/UPDATE/DELETE: affected row count
    """
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        # Check if it's a SELECT query
        if query.strip().upper().startswith("SELECT"):
            if fetch_one:
                row = cursor.fetchone()
                return row_to_dict(row) if row else None
            else:
                return rows_to_list(cursor.fetchall())
        else:
            # For INSERT, UPDATE, DELETE
            return cursor.rowcount


def execute_insert(
    table: str,
    data: Dict[str, Any],
    return_id: bool = True
) -> Union[int, bool]:
    """
    Insert a row into a table.
    
    Args:
        table: Table name
        data: Dictionary of column -> value
        return_id: If True, return the last inserted row ID
        
    Returns:
        Last inserted row ID if return_id=True, else True on success
    """
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(data.values()))
        return cursor.lastrowid if return_id else True


def execute_update(
    table: str,
    data: Dict[str, Any],
    where: str,
    where_params: tuple = ()
) -> int:
    """
    Update rows in a table.
    
    Args:
        table: Table name
        data: Dictionary of column -> value to update
        where: WHERE clause (without 'WHERE' keyword)
        where_params: Parameters for WHERE clause
        
    Returns:
        Number of affected rows
    """
    set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
    query = f"UPDATE {table} SET {set_clause}, updated_at = datetime('now') WHERE {where}"
    params = tuple(data.values()) + where_params
    
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.rowcount


def execute_delete(
    table: str,
    where: str,
    where_params: tuple = ()
) -> int:
    """
    Delete rows from a table.
    
    Args:
        table: Table name
        where: WHERE clause (without 'WHERE' keyword)
        where_params: Parameters for WHERE clause
        
    Returns:
        Number of deleted rows
    """
    query = f"DELETE FROM {table} WHERE {where}"
    
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, where_params)
        return cursor.rowcount


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
    result = execute_query(query, (table_name,), fetch_one=True)
    return result is not None


def get_table_columns(table_name: str) -> List[str]:
    """Get list of column names for a table."""
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]


def count_rows(table: str, where: str = None, params: tuple = ()) -> int:
    """Count rows in a table, optionally with a WHERE clause."""
    query = f"SELECT COUNT(*) as count FROM {table}"
    if where:
        query += f" WHERE {where}"
    result = execute_query(query, params, fetch_one=True)
    return result['count'] if result else 0


# Database initialization check
def ensure_initialized():
    """
    Ensure the database is initialized.
    Call this on app startup.
    """
    needs_full_init = not os.path.exists(DB_PATH) or not table_exists('vehicles')
    
    if needs_full_init:
        logger.warning("Database not initialized. Creating tables...")
        _create_tables_inline()
        logger.info("Database initialized successfully")
    else:
        # Check and upgrade tables if needed
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Check maintenance_intervals table
            cursor.execute("PRAGMA table_info(maintenance_intervals)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'next_due_mileage' not in columns:
                logger.warning("Upgrading maintenance_intervals table...")
                cursor.execute("DROP TABLE IF EXISTS maintenance_intervals")
                cursor.execute('''
                    CREATE TABLE maintenance_intervals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vin TEXT NOT NULL,
                        service_type TEXT NOT NULL,
                        interval_miles INTEGER,
                        interval_months INTEGER,
                        last_performed_mileage INTEGER,
                        last_performed_date TEXT,
                        next_due_mileage INTEGER,
                        next_due_date TEXT,
                        is_custom INTEGER DEFAULT 0,
                        notes TEXT,
                        created_at TEXT DEFAULT (datetime('now')),
                        updated_at TEXT DEFAULT (datetime('now'))
                    )
                ''')
                conn.commit()
                logger.info("maintenance_intervals table upgraded")
            
            # Check trips table - needs start_mileage and end_mileage columns
            if table_exists('trips'):
                cursor.execute("PRAGMA table_info(trips)")
                trips_columns = [col[1] for col in cursor.fetchall()]
                
                if 'start_mileage' not in trips_columns or 'end_mileage' not in trips_columns:
                    logger.warning("Upgrading trips table...")
                    # Backup existing trips data
                    cursor.execute("SELECT * FROM trips")
                    old_trips = cursor.fetchall()
                    old_columns = [col[1] for col in cursor.execute("PRAGMA table_info(trips)").fetchall()]
                    
                    # Create new table with correct schema
                    cursor.execute("DROP TABLE IF EXISTS trips")
                    cursor.execute('''
                        CREATE TABLE trips (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            vin TEXT NOT NULL,
                            start_location TEXT,
                            end_location TEXT,
                            start_mileage INTEGER,
                            end_mileage INTEGER,
                            distance REAL,
                            date TEXT NOT NULL,
                            purpose TEXT,
                            is_business INTEGER DEFAULT 0,
                            notes TEXT,
                            created_at TEXT DEFAULT (datetime('now')),
                            updated_at TEXT DEFAULT (datetime('now')),
                            FOREIGN KEY (vin) REFERENCES vehicles(vin) ON DELETE CASCADE
                        )
                    ''')
                    
                    # Restore trips data if any
                    if old_trips:
                        for trip in old_trips:
                            trip_dict = dict(zip(old_columns, trip))
                            cursor.execute('''
                                INSERT INTO trips (vin, start_location, end_location, start_mileage, end_mileage, distance, date, purpose, is_business, notes, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                trip_dict.get('vin'),
                                trip_dict.get('start_location'),
                                trip_dict.get('end_location'),
                                trip_dict.get('start_mileage'),
                                trip_dict.get('end_mileage'),
                                trip_dict.get('distance'),
                                trip_dict.get('date'),
                                trip_dict.get('purpose'),
                                trip_dict.get('is_business', 0),
                                trip_dict.get('notes'),
                                trip_dict.get('created_at'),
                                trip_dict.get('updated_at'),
                            ))
                    conn.commit()
                    logger.info("trips table upgraded")
            
            # Check settings table - needs user_id column
            cursor.execute("PRAGMA table_info(settings)")
            settings_columns = [col[1] for col in cursor.fetchall()]
            
            if 'user_id' not in settings_columns or 'id' not in settings_columns:
                logger.warning("Upgrading settings table...")
                # Backup existing settings
                cursor.execute("SELECT key, value FROM settings")
                old_settings = cursor.fetchall()
                
                cursor.execute("DROP TABLE IF EXISTS settings")
                cursor.execute('''
                    CREATE TABLE settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT NOT NULL,
                        value TEXT,
                        user_id INTEGER,
                        created_at TEXT DEFAULT (datetime('now')),
                        updated_at TEXT DEFAULT (datetime('now')),
                        UNIQUE(key, user_id)
                    )
                ''')
                
                # Restore settings
                for key, value in old_settings:
                    cursor.execute(
                        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                        (key, value)
                    )
                conn.commit()
                logger.info("settings table upgraded")
            
        finally:
            conn.close()
    return True


def _create_tables_inline():
    """Create all required tables inline (no import dependencies)."""
    schema = '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
    
    CREATE TABLE IF NOT EXISTS vehicles (
        vin TEXT PRIMARY KEY,
        year INTEGER NOT NULL,
        make TEXT NOT NULL,
        model TEXT NOT NULL,
        trim TEXT,
        engine_type TEXT,
        color TEXT,
        purchase_date TEXT,
        purchase_price REAL,
        current_mileage INTEGER DEFAULT 0,
        user_id INTEGER,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
    
    CREATE TABLE IF NOT EXISTS repairs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vin TEXT NOT NULL,
        service TEXT NOT NULL,
        description TEXT,
        cost REAL NOT NULL DEFAULT 0,
        mileage INTEGER,
        date TEXT NOT NULL,
        shop_name TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
    
    CREATE TABLE IF NOT EXISTS fuel_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vin TEXT NOT NULL,
        gallons REAL NOT NULL,
        price_per_gallon REAL NOT NULL,
        total_cost REAL NOT NULL,
        odometer INTEGER NOT NULL,
        date TEXT NOT NULL,
        station TEXT,
        fuel_type TEXT DEFAULT 'Regular',
        full_tank INTEGER DEFAULT 1,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
    
    CREATE TABLE IF NOT EXISTS maintenance_intervals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vin TEXT NOT NULL,
        service_type TEXT NOT NULL,
        interval_miles INTEGER,
        interval_months INTEGER,
        last_performed_mileage INTEGER,
        last_performed_date TEXT,
        next_due_mileage INTEGER,
        next_due_date TEXT,
        is_custom INTEGER DEFAULT 0,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
    
    CREATE TABLE IF NOT EXISTS mileage_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vin TEXT NOT NULL,
        mileage INTEGER NOT NULL,
        date TEXT NOT NULL,
        source TEXT DEFAULT 'manual',
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    
    CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vin TEXT NOT NULL,
        start_location TEXT,
        end_location TEXT,
        start_mileage INTEGER,
        end_mileage INTEGER,
        distance REAL,
        date TEXT NOT NULL,
        purpose TEXT,
        is_business INTEGER DEFAULT 0,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
    
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT NOT NULL,
        value TEXT,
        user_id INTEGER,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        UNIQUE(key, user_id)
    );
    '''
    
    conn = get_connection()
    try:
        conn.executescript(schema)
        conn.commit()
        logger.info("All tables created successfully")
        
        # Skip auto-seeding for fresh user experience
        # To add demo data, call _seed_sample_data(conn) manually
        # _seed_sample_data(conn)
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise
    finally:
        conn.close()


def _seed_sample_data(conn):
    """Add sample vehicles and data for demo."""
    # Check if already seeded
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM vehicles")
    if cursor.fetchone()[0] > 0:
        return
    
    # Sample vehicles
    vehicles = [
        ('1HGCM82633A004352', 2020, 'Honda', 'Civic', 'EX', 'Gas', 'Silver', 45000),
        ('WBAJ71M202A123456', 2021, 'BMW', '3 Series', '330i', 'Gas', 'Black', 28000),
        ('1F1J7J2033A123456', 2019, 'Hyundai', 'Elantra', 'SEL', 'Gas', 'White', 62000),
        ('1F1J7J2033A123457', 2022, 'Toyota', 'Camry', 'LE', 'Gas', 'Blue', 35000),
        ('1T3CHJ6033A123456', 2018, 'Tesla', 'Model 3', 'Long Range', 'Electric', 'Red', 78000),
        ('1N3CHJ3033A123456', 2023, 'Nissan', 'Altima', 'SV', 'Gas', 'Gray', 15000),
        ('1N5KJ62F25A123456', 2020, 'Ford', 'F-150', 'XLT', 'Gas', 'White', 52000),
        ('2HGCG225X8A123456', 2021, 'Chevrolet', 'Malibu', 'LT', 'Gas', 'Black', 41000),
        ('WDCV21M423A123456', 2022, 'Mercedes-Benz', 'C-Class', 'C300', 'Gas', 'Silver', 33000),
        ('5YFBURHE5HP123456', 2019, 'Toyota', 'Corolla', 'SE', 'Gas', 'Blue', 55000),
    ]
    
    for v in vehicles:
        cursor.execute('''
            INSERT OR IGNORE INTO vehicles (vin, year, make, model, trim, engine_type, color, current_mileage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', v)
    
    # Sample maintenance intervals for vehicles
    # (vin, service_type, interval_miles, interval_months, last_mileage, last_date, next_due_mileage)
    maintenance = [
        ('1HGCM82633A004352', 'Oil Change', 5000, 6, 42000, '2024-08-15', 47000),
        ('1HGCM82633A004352', 'Tire Rotation', 7500, 6, 40000, '2024-07-01', 47500),
        ('1HGCM82633A004352', 'Brake Inspection', 15000, 12, 40000, '2024-06-01', 55000),
        ('1HGCM82633A004352', 'Air Filter', 15000, 12, 35000, '2024-03-01', 50000),
        ('WBAJ71M202A123456', 'Oil Change', 7500, 12, 24000, '2024-10-01', 31500),
        ('WBAJ71M202A123456', 'Brake Inspection', 20000, 24, 20000, '2024-05-01', 40000),
        ('1F1J7J2033A123456', 'Oil Change', 5000, 6, 58000, '2024-09-01', 63000),
        ('1F1J7J2033A123456', 'Transmission Fluid', 30000, 36, 35000, '2023-06-01', 65000),
        ('1F1J7J2033A123457', 'Oil Change', 5000, 6, 32000, '2024-10-01', 37000),
        ('1T3CHJ6033A123456', 'Tire Rotation', 10000, 12, 70000, '2024-07-01', 80000),
        ('1N3CHJ3033A123456', 'Oil Change', 5000, 6, 12000, '2024-11-01', 17000),
        ('5YFBURHE5HP123456', 'Oil Change', 5000, 6, 52000, '2024-08-01', 57000),
    ]
    
    for m in maintenance:
        cursor.execute('''
            INSERT OR IGNORE INTO maintenance_intervals 
            (vin, service_type, interval_miles, interval_months, last_performed_mileage, last_performed_date, next_due_mileage)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', m)
    
    # Sample repairs
    repairs = [
        ('1HGCM82633A004352', 'Oil Change', 45.99, 42000, '2024-08-15'),
        ('1HGCM82633A004352', 'Brake Pads Replacement', 289.00, 40000, '2024-06-01'),
        ('1HGCM82633A004352', 'Tire Rotation', 25.00, 40000, '2024-07-01'),
        ('WBAJ71M202A123456', 'Oil Change', 89.99, 24000, '2024-10-01'),
        ('1F1J7J2033A123456', 'Battery Replacement', 185.00, 55000, '2024-04-15'),
    ]
    
    for r in repairs:
        cursor.execute('''
            INSERT OR IGNORE INTO repairs (vin, service, cost, mileage, date)
            VALUES (?, ?, ?, ?, ?)
        ''', r)
    
    conn.commit()
    logger.info("Sample data seeded successfully")
