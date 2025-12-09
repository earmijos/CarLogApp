"""
CarLog Database Schema
======================
Defines all table schemas for the CarLog application.
Production-ready with proper relationships, indexes, and constraints.
"""

# SQL statements for creating all tables
SCHEMA = """
-- ============================================
-- USERS TABLE
-- Local user management for multi-user support
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================
-- VEHICLES TABLE
-- Core vehicle information
-- ============================================
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
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_vehicles_user ON vehicles(user_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_make_model ON vehicles(make, model);

-- ============================================
-- REPAIRS TABLE
-- Track all repairs and services performed
-- ============================================
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
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (vin) REFERENCES vehicles(vin) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_repairs_vin ON repairs(vin);
CREATE INDEX IF NOT EXISTS idx_repairs_date ON repairs(date DESC);
CREATE INDEX IF NOT EXISTS idx_repairs_vin_date ON repairs(vin, date DESC);

-- ============================================
-- FUEL_LOGS TABLE
-- Track fuel purchases and calculate MPG
-- ============================================
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
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (vin) REFERENCES vehicles(vin) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_fuel_logs_vin ON fuel_logs(vin);
CREATE INDEX IF NOT EXISTS idx_fuel_logs_date ON fuel_logs(date DESC);
CREATE INDEX IF NOT EXISTS idx_fuel_logs_vin_date ON fuel_logs(vin, date DESC);

-- ============================================
-- MAINTENANCE_INTERVALS TABLE
-- Recommended maintenance schedules per vehicle
-- ============================================
CREATE TABLE IF NOT EXISTS maintenance_intervals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vin TEXT NOT NULL,
    service_type TEXT NOT NULL,
    interval_miles INTEGER,
    interval_months INTEGER,
    last_performed_date TEXT,
    last_performed_mileage INTEGER,
    next_due_date TEXT,
    next_due_mileage INTEGER,
    is_custom INTEGER DEFAULT 0,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (vin) REFERENCES vehicles(vin) ON DELETE CASCADE,
    UNIQUE(vin, service_type)
);

CREATE INDEX IF NOT EXISTS idx_maintenance_vin ON maintenance_intervals(vin);
CREATE INDEX IF NOT EXISTS idx_maintenance_next_due ON maintenance_intervals(next_due_mileage);

-- ============================================
-- MILEAGE_HISTORY TABLE
-- Track odometer readings over time
-- ============================================
CREATE TABLE IF NOT EXISTS mileage_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vin TEXT NOT NULL,
    mileage INTEGER NOT NULL,
    date TEXT NOT NULL,
    source TEXT DEFAULT 'manual',
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (vin) REFERENCES vehicles(vin) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_mileage_vin ON mileage_history(vin);
CREATE INDEX IF NOT EXISTS idx_mileage_date ON mileage_history(date DESC);
CREATE INDEX IF NOT EXISTS idx_mileage_vin_date ON mileage_history(vin, date DESC);

-- ============================================
-- TRIPS TABLE
-- Track individual trips for mileage logging
-- ============================================
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
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (vin) REFERENCES vehicles(vin) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_trips_vin ON trips(vin);
CREATE INDEX IF NOT EXISTS idx_trips_date ON trips(date DESC);
CREATE INDEX IF NOT EXISTS idx_trips_business ON trips(is_business);

-- ============================================
-- SETTINGS TABLE
-- User and app settings (key-value store)
-- ============================================
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,
    value TEXT,
    user_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(key, user_id)
);

CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key);
CREATE INDEX IF NOT EXISTS idx_settings_user ON settings(user_id);

-- ============================================
-- SCHEMA VERSION TABLE
-- Track database migrations
-- ============================================
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT (datetime('now')),
    description TEXT
);
"""

# Current schema version
CURRENT_VERSION = 1

# List of all table names for reference
TABLES = [
    'users',
    'vehicles', 
    'repairs',
    'fuel_logs',
    'maintenance_intervals',
    'mileage_history',
    'trips',
    'settings',
    'schema_version'
]

# Default maintenance intervals (miles)
DEFAULT_MAINTENANCE_INTERVALS = {
    'Oil Change': {'miles': 5000, 'months': 6},
    'Transmission Fluid': {'miles': 60000, 'months': 48},
    'Brake Inspection': {'miles': 25000, 'months': 24},
    'Air Filter': {'miles': 15000, 'months': 12},
    'Tire Rotation': {'miles': 7500, 'months': 6},
    'Coolant Flush': {'miles': 30000, 'months': 36},
    'Spark Plugs': {'miles': 60000, 'months': 60},
    'Battery Check': {'miles': 25000, 'months': 24},
    'Brake Fluid': {'miles': 30000, 'months': 24},
    'Power Steering Fluid': {'miles': 50000, 'months': 48},
}

# Fuel types
FUEL_TYPES = ['Regular', 'Mid-Grade', 'Premium', 'Diesel', 'E85', 'Electric']

# Trip purposes
TRIP_PURPOSES = ['Commute', 'Business', 'Personal', 'Road Trip', 'Errand', 'Other']

