"""
CarLog Database Initialization
==============================
Handles database creation, migration, and seeding.
Run this script to initialize or reset the database.
"""

import sqlite3
import os
import shutil
from datetime import datetime, timedelta

from schema import SCHEMA, CURRENT_VERSION, DEFAULT_MAINTENANCE_INTERVALS, TABLES

# Database paths
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "carlog.db")
BACKUP_PATH = os.path.join(DB_DIR, "carlog_backup.db")


def get_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def backup_database():
    """Create a backup of the current database."""
    if os.path.exists(DB_PATH):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"carlog_backup_{timestamp}.db"
        backup_path = os.path.join(DB_DIR, backup_name)
        shutil.copy2(DB_PATH, backup_path)
        print(f"✓ Backed up database to: {backup_name}")
        return backup_path
    return None


def get_schema_version(conn):
    """Get the current schema version from database."""
    try:
        cursor = conn.execute("SELECT MAX(version) FROM schema_version")
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0
    except sqlite3.OperationalError:
        return 0


def migrate_old_data(conn):
    """
    Migrate data from old schema to new schema.
    Handles the transition from the legacy table structure.
    """
    cursor = conn.cursor()
    
    # Check if old vehicles table exists with old schema
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
    if not cursor.fetchone():
        return False
    
    # Check if it's the old schema (has "Oil Change" column)
    cursor.execute("PRAGMA table_info(vehicles)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "Oil Change" not in columns:
        # Already new schema or empty
        return False
    
    print("  → Migrating old vehicle data...")
    
    # Get old vehicle data
    cursor.execute("""
        SELECT VIN, Year, Make, Model, "Engine Type", Trim,
               "Oil Change", "Transmission Fluid Change", 
               "Brake Service", "Air Filter Check"
        FROM vehicles
    """)
    old_vehicles = cursor.fetchall()
    
    # Get old repairs data
    cursor.execute("SELECT * FROM repairs")
    old_repairs = cursor.fetchall()
    
    # Drop old tables
    cursor.execute("DROP TABLE IF EXISTS repairs")
    cursor.execute("DROP TABLE IF EXISTS vehicles")
    
    # Create new schema
    cursor.executescript(SCHEMA)
    
    # Create default user
    cursor.execute("""
        INSERT INTO users (name, email) VALUES ('Default User', 'user@carlog.local')
    """)
    user_id = cursor.lastrowid
    
    # Migrate vehicles
    for v in old_vehicles:
        vin = v[0]
        cursor.execute("""
            INSERT INTO vehicles (vin, year, make, model, engine_type, trim, user_id, current_mileage)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (vin, v[1], v[2], v[3], v[4], v[5], user_id))
        
        # Create maintenance intervals from old data
        maintenance_data = [
            ('Oil Change', v[6]),
            ('Transmission Fluid', v[7]),
            ('Brake Inspection', v[8]),
            ('Air Filter', v[9])
        ]
        
        for service_type, interval_miles in maintenance_data:
            if interval_miles:
                cursor.execute("""
                    INSERT INTO maintenance_intervals 
                    (vin, service_type, interval_miles, interval_months)
                    VALUES (?, ?, ?, ?)
                """, (vin, service_type, interval_miles, 
                      DEFAULT_MAINTENANCE_INTERVALS.get(service_type, {}).get('months', 12)))
    
    # Migrate repairs
    for r in old_repairs:
        cursor.execute("""
            INSERT INTO repairs (id, vin, service, cost, date)
            VALUES (?, ?, ?, ?, ?)
        """, (r[0], r[1], r[2], r[3], r[4]))
    
    # Record schema version
    cursor.execute("""
        INSERT INTO schema_version (version, description)
        VALUES (?, 'Migrated from legacy schema')
    """, (CURRENT_VERSION,))
    
    conn.commit()
    print(f"  → Migrated {len(old_vehicles)} vehicles and {len(old_repairs)} repairs")
    return True


def create_tables(conn):
    """Create all tables from schema."""
    cursor = conn.cursor()
    cursor.executescript(SCHEMA)
    
    # Record schema version if not exists
    version = get_schema_version(conn)
    if version == 0:
        cursor.execute("""
            INSERT INTO schema_version (version, description)
            VALUES (?, 'Initial schema creation')
        """, (CURRENT_VERSION,))
    
    conn.commit()


def seed_default_user(conn):
    """Create a default user if none exists."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO users (name, email) 
            VALUES ('Default User', 'user@carlog.local')
        """)
        conn.commit()
        print("  → Created default user")
        return cursor.lastrowid
    return None


def seed_sample_vehicles(conn):
    """Seed sample vehicles if database is empty."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM vehicles")
    if cursor.fetchone()[0] > 0:
        return  # Already has data
    
    # Get default user
    cursor.execute("SELECT id FROM users LIMIT 1")
    user_row = cursor.fetchone()
    user_id = user_row[0] if user_row else 1
    
    sample_vehicles = [
        ('1HGCM82633A123456', 2023, 'Toyota', 'Camry', 'SE', 'V6', 'Silver', 45000),
        ('1FTEB37S33A123456', 2022, 'Honda', 'Civic', 'EX', 'I4 Turbo', 'Blue', 32000),
        ('1N3CHJ3033A123456', 2023, 'Ford', 'Mustang', 'GT', 'V8', 'Red', 18000),
        ('1T3CHJ6033A123456', 2021, 'Chevrolet', 'Impala', 'LT', 'V6', 'Black', 55000),
        ('1N5KJ62F25A123456', 2023, 'Nissan', 'Altima', 'SV', 'I4', 'White', 28000),
        ('1F1J7J2033A123456', 2022, 'Hyundai', 'Elantra', 'SEL', 'I4', 'Gray', 38000),
        ('WBAJ71M202A123456', 2023, 'BMW', '3 Series', '330i', 'I4 Turbo', 'Blue', 22000),
        ('WDCV21M423A123456', 2021, 'Mercedes-Benz', 'C-Class', 'C300', 'I4 Turbo', 'Black', 41000),
        ('5N4K5H2033A123456', 2023, 'Subaru', 'Outback', 'Premium', 'H4', 'Green', 35000),
        ('1F1J7J2033A123457', 2022, 'Ford', 'F-150', 'XLT', 'V6 EcoBoost', 'White', 48000),
    ]
    
    for vin, year, make, model, trim, engine, color, mileage in sample_vehicles:
        cursor.execute("""
            INSERT INTO vehicles (vin, year, make, model, trim, engine_type, color, current_mileage, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (vin, year, make, model, trim, engine, color, mileage, user_id))
        
        # Add default maintenance intervals
        for service_type, intervals in DEFAULT_MAINTENANCE_INTERVALS.items():
            cursor.execute("""
                INSERT INTO maintenance_intervals 
                (vin, service_type, interval_miles, interval_months, next_due_mileage)
                VALUES (?, ?, ?, ?, ?)
            """, (vin, service_type, intervals['miles'], intervals['months'], 
                  mileage + intervals['miles']))
    
    conn.commit()
    print(f"  → Seeded {len(sample_vehicles)} sample vehicles with maintenance intervals")


def seed_sample_data(conn):
    """Seed sample repairs, fuel logs, and trips."""
    cursor = conn.cursor()
    
    # Check if already has sample data
    cursor.execute("SELECT COUNT(*) FROM repairs")
    if cursor.fetchone()[0] > 5:
        return  # Already has enough data
    
    # Get a vehicle
    cursor.execute("SELECT vin FROM vehicles LIMIT 3")
    vehicles = [row[0] for row in cursor.fetchall()]
    
    if not vehicles:
        return
    
    today = datetime.now()
    
    # Sample repairs
    repairs = [
        (vehicles[0], 'Oil Change', 'Full synthetic oil change', 75.00, 42000, (today - timedelta(days=90)).strftime('%Y-%m-%d'), 'Quick Lube'),
        (vehicles[0], 'Brake Pads', 'Front brake pad replacement', 250.00, 43500, (today - timedelta(days=45)).strftime('%Y-%m-%d'), 'Midas'),
        (vehicles[0], 'Tire Rotation', 'Rotate and balance all tires', 40.00, 44000, (today - timedelta(days=30)).strftime('%Y-%m-%d'), 'Discount Tire'),
    ]
    
    if len(vehicles) > 1:
        repairs.extend([
            (vehicles[1], 'Oil Change', 'Conventional oil change', 45.00, 30000, (today - timedelta(days=60)).strftime('%Y-%m-%d'), 'Jiffy Lube'),
            (vehicles[1], 'Air Filter', 'Engine air filter replacement', 35.00, 31000, (today - timedelta(days=30)).strftime('%Y-%m-%d'), 'AutoZone'),
        ])
    
    for repair in repairs:
        cursor.execute("""
            INSERT INTO repairs (vin, service, description, cost, mileage, date, shop_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, repair)
    
    # Sample fuel logs
    fuel_logs = [
        (vehicles[0], 12.5, 3.45, 43.13, 43000, (today - timedelta(days=21)).strftime('%Y-%m-%d'), 'Shell', 'Regular'),
        (vehicles[0], 13.2, 3.52, 46.46, 43350, (today - timedelta(days=14)).strftime('%Y-%m-%d'), 'Chevron', 'Regular'),
        (vehicles[0], 12.8, 3.39, 43.39, 43700, (today - timedelta(days=7)).strftime('%Y-%m-%d'), 'Costco', 'Regular'),
    ]
    
    if len(vehicles) > 1:
        fuel_logs.extend([
            (vehicles[1], 10.5, 3.45, 36.23, 31500, (today - timedelta(days=10)).strftime('%Y-%m-%d'), 'BP', 'Regular'),
            (vehicles[1], 11.0, 3.55, 39.05, 31850, (today - timedelta(days=3)).strftime('%Y-%m-%d'), 'Shell', 'Regular'),
        ])
    
    for fuel in fuel_logs:
        cursor.execute("""
            INSERT INTO fuel_logs (vin, gallons, price_per_gallon, total_cost, odometer, date, station, fuel_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, fuel)
    
    # Sample trips
    trips = [
        (vehicles[0], 'Home', 'Office', 44500, 44525, 25, (today - timedelta(days=5)).strftime('%Y-%m-%d'), 'Commute', 0),
        (vehicles[0], 'Office', 'Home', 44525, 44550, 25, (today - timedelta(days=5)).strftime('%Y-%m-%d'), 'Commute', 0),
        (vehicles[0], 'Home', 'Client Meeting', 44600, 44680, 80, (today - timedelta(days=3)).strftime('%Y-%m-%d'), 'Business', 1),
    ]
    
    for trip in trips:
        cursor.execute("""
            INSERT INTO trips (vin, start_location, end_location, start_mileage, end_mileage, distance, date, purpose, is_business)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, trip)
    
    # Sample mileage history
    for vin in vehicles[:2]:
        cursor.execute("SELECT current_mileage FROM vehicles WHERE vin = ?", (vin,))
        current = cursor.fetchone()[0] or 30000
        
        for i in range(6):
            date = (today - timedelta(days=30 * (5-i))).strftime('%Y-%m-%d')
            mileage = current - (5-i) * 800  # ~800 miles per month
            cursor.execute("""
                INSERT INTO mileage_history (vin, mileage, date, source)
                VALUES (?, ?, ?, 'manual')
            """, (vin, max(0, mileage), date))
    
    # Default settings
    settings = [
        ('distance_unit', 'miles', None),
        ('currency', 'USD', None),
        ('fuel_unit', 'gallons', None),
        ('theme', 'light', None),
        ('notifications_enabled', 'true', None),
    ]
    
    for key, value, user_id in settings:
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value, user_id)
            VALUES (?, ?, ?)
        """, (key, value, user_id))
    
    conn.commit()
    print(f"  → Seeded sample repairs, fuel logs, trips, and mileage history")


def verify_tables(conn):
    """Verify all tables were created successfully."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    existing_tables = {row[0] for row in cursor.fetchall()}
    
    missing = set(TABLES) - existing_tables - {'sqlite_sequence'}
    if missing:
        print(f"  ⚠ Missing tables: {missing}")
        return False
    
    # Print table counts
    print("\n  Table Statistics:")
    for table in TABLES:
        if table in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"    • {table}: {count} rows")
    
    return True


def init_database(force_reset=False, seed_data=True):
    """
    Initialize the database.
    
    Args:
        force_reset: If True, backs up and recreates the database
        seed_data: If True, seeds sample data for testing
    """
    print("\n" + "=" * 50)
    print("  CarLog Database Initialization")
    print("=" * 50 + "\n")
    
    if force_reset and os.path.exists(DB_PATH):
        backup_database()
        os.remove(DB_PATH)
        print("✓ Removed old database")
    
    conn = get_connection()
    
    try:
        # Check for migration from old schema
        if not force_reset:
            migrated = migrate_old_data(conn)
            if migrated:
                print("✓ Migrated from legacy schema")
        
        # Create tables
        print("\n→ Creating tables...")
        create_tables(conn)
        print("✓ Tables created")
        
        # Seed data
        if seed_data:
            print("\n→ Seeding data...")
            seed_default_user(conn)
            seed_sample_vehicles(conn)
            seed_sample_data(conn)
            print("✓ Data seeded")
        
        # Verify
        print("\n→ Verifying database...")
        if verify_tables(conn):
            print("\n✓ Database initialized successfully!")
        else:
            print("\n⚠ Database initialization completed with warnings")
        
        # Get schema version
        version = get_schema_version(conn)
        print(f"\n  Schema Version: {version}")
        print(f"  Database Path: {DB_PATH}")
        
    finally:
        conn.close()
    
    print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    import sys
    
    force = "--force" in sys.argv or "-f" in sys.argv
    no_seed = "--no-seed" in sys.argv
    
    if force:
        confirm = input("This will reset the database. Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
    
    init_database(force_reset=force, seed_data=not no_seed)

