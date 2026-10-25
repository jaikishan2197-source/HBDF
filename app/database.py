import sqlite3
from contextlib import contextmanager
from typing import Generator
from app.config import get_database_path

_db_initialized = False

def init_db(db_path: str | None = None) -> None:
    global _db_initialized
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        
        # Story 1: Expected Occupancy table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS occupancy_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                expected_occupancy INTEGER NOT NULL CHECK (expected_occupancy >= 0),
                total_rooms INTEGER DEFAULT NULL CHECK (total_rooms IS NULL OR total_rooms >= 0),
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_occupancy_date ON occupancy_records(date);")

        # Story 2: Previous Breakfast Consumption table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consumption_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                actual_consumption INTEGER NOT NULL CHECK (actual_consumption >= 0),
                actual_occupancy INTEGER DEFAULT NULL CHECK (actual_occupancy IS NULL OR actual_occupancy >= 0),
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_consumption_date ON consumption_records(date);")

        # User accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")

        # Dish-wise daily records (waste, consumption, stock-outs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dish_daily_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                dish TEXT NOT NULL COLLATE NOCASE,
                quantity_prepared REAL NOT NULL CHECK (quantity_prepared >= 0),
                quantity_consumed REAL NOT NULL CHECK (quantity_consumed >= 0),
                quantity_discarded REAL NOT NULL CHECK (quantity_discarded >= 0),
                stock_out INTEGER NOT NULL DEFAULT 0 CHECK (stock_out IN (0, 1)),
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                UNIQUE(date, dish)
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dish_records_date ON dish_daily_records(date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dish_records_dish ON dish_daily_records(dish);")

        # Safe migration: ensure guest-group split columns exist in occupancy_records
        cursor.execute("PRAGMA table_info(occupancy_records);")
        occ_cols = [r["name"] for r in cursor.fetchall()]
        if "guests_included" not in occ_cols:
            cursor.execute("ALTER TABLE occupancy_records ADD COLUMN guests_included INTEGER DEFAULT NULL;")
        if "guests_other" not in occ_cols:
            cursor.execute("ALTER TABLE occupancy_records ADD COLUMN guests_other INTEGER DEFAULT NULL;")
        if "group_event" not in occ_cols:
            cursor.execute("ALTER TABLE occupancy_records ADD COLUMN group_event INTEGER DEFAULT 0;")
        if "event_expected_covers" not in occ_cols:
            cursor.execute("ALTER TABLE occupancy_records ADD COLUMN event_expected_covers INTEGER DEFAULT 0;")

        # Safe migration: ensure guest-group split columns exist in consumption_records
        cursor.execute("PRAGMA table_info(consumption_records);")
        cons_cols = [r["name"] for r in cursor.fetchall()]
        if "covers_included" not in cons_cols:
            cursor.execute("ALTER TABLE consumption_records ADD COLUMN covers_included INTEGER DEFAULT NULL;")
        if "covers_other" not in cons_cols:
            cursor.execute("ALTER TABLE consumption_records ADD COLUMN covers_other INTEGER DEFAULT NULL;")
        if "event_covers" not in cons_cols:
            cursor.execute("ALTER TABLE consumption_records ADD COLUMN event_covers INTEGER DEFAULT 0;")

        # Backfill legacy occupancy records where guests_included is NULL
        cursor.execute("""
            UPDATE occupancy_records 
            SET guests_included = CAST(ROUND(expected_occupancy * 0.75) AS INTEGER),
                guests_other = expected_occupancy - CAST(ROUND(expected_occupancy * 0.75) AS INTEGER)
            WHERE guests_included IS NULL AND expected_occupancy IS NOT NULL;
        """)

        # Backfill legacy consumption records where covers_included is NULL
        cursor.execute("""
            UPDATE consumption_records 
            SET covers_included = CAST(ROUND(actual_consumption * 0.80) AS INTEGER),
                covers_other = actual_consumption - CAST(ROUND(actual_consumption * 0.80) AS INTEGER)
            WHERE covers_included IS NULL AND actual_consumption IS NOT NULL;
        """)

        conn.commit()
        _db_initialized = True
    finally:
        conn.close()

def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    target_path = db_path if db_path is not None else get_database_path()
    conn = sqlite3.connect(target_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def get_db(db_path: str | None = None) -> Generator[sqlite3.Connection, None, None]:
    global _db_initialized
    if not _db_initialized:
        init_db(db_path)
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
