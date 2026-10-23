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
