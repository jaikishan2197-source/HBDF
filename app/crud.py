import sqlite3
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from app.models import (
    OccupancyCreate, OccupancyUpdate,
    ConsumptionCreate, ConsumptionUpdate,
    HistoricalRecordItem, HistorySummaryStats
)

# ==========================================
# Story 1: Occupancy CRUD
# ==========================================
def upsert_occupancy(conn: sqlite3.Connection, data: OccupancyCreate) -> Tuple[Dict[str, Any], bool]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM occupancy_records WHERE date = ?", (data.date,))
    existing = cursor.fetchone()
    now_iso = datetime.now().isoformat()

    if existing:
        record_id = existing["id"]
        # Preserve existing total_rooms and notes if omitted in update request
        final_rooms = data.total_rooms if data.total_rooms is not None else existing["total_rooms"]
        final_notes = data.notes if (data.notes is not None and data.notes != "") else existing["notes"]
        
        cursor.execute(
            """
            UPDATE occupancy_records
            SET expected_occupancy = ?, total_rooms = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (data.expected_occupancy, final_rooms, final_notes or "", now_iso, record_id)
        )
        is_created = False
    else:
        cursor.execute(
            """
            INSERT INTO occupancy_records (date, expected_occupancy, total_rooms, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (data.date, data.expected_occupancy, data.total_rooms, data.notes or "", now_iso, now_iso)
        )
        record_id = cursor.lastrowid
        is_created = True

    cursor.execute("SELECT * FROM occupancy_records WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    return dict(row), is_created

def update_occupancy_partial(
    conn: sqlite3.Connection,
    record_id_or_date: str | int,
    data: OccupancyUpdate
) -> Optional[Dict[str, Any]]:
    """Update only the explicitly provided fields of an occupancy record."""
    cursor = conn.cursor()
    if isinstance(record_id_or_date, int) or str(record_id_or_date).isdigit():
        cursor.execute("SELECT * FROM occupancy_records WHERE id = ?", (int(record_id_or_date),))
    else:
        cursor.execute("SELECT * FROM occupancy_records WHERE date = ?", (str(record_id_or_date),))
    existing = cursor.fetchone()
    if not existing:
        return None

    fields = data.model_dump(exclude_unset=True)
    if not fields:
        return dict(existing)

    set_clauses = []
    values = []
    for key, val in fields.items():
        set_clauses.append(f"{key} = ?")
        values.append(val)

    now_iso = datetime.now().isoformat()
    set_clauses.append("updated_at = ?")
    values.append(now_iso)

    values.append(existing["id"])
    cursor.execute(f"UPDATE occupancy_records SET {', '.join(set_clauses)} WHERE id = ?", tuple(values))
    cursor.execute("SELECT * FROM occupancy_records WHERE id = ?", (existing["id"],))
    return dict(cursor.fetchone())

def get_occupancy_by_id(conn: sqlite3.Connection, record_id: int) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM occupancy_records WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_occupancy_by_date(conn: sqlite3.Connection, target_date: str) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM occupancy_records WHERE date = ?", (target_date,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_all_occupancy(conn: sqlite3.Connection, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM occupancy_records ORDER BY date DESC LIMIT ? OFFSET ?", (limit, offset))
    rows = cursor.fetchall()
    return [dict(r) for r in rows]

def delete_occupancy(conn: sqlite3.Connection, record_id_or_date: str | int) -> bool:
    cursor = conn.cursor()
    if isinstance(record_id_or_date, int) or str(record_id_or_date).isdigit():
        cursor.execute("DELETE FROM occupancy_records WHERE id = ?", (int(record_id_or_date),))
    else:
        cursor.execute("DELETE FROM occupancy_records WHERE date = ?", (str(record_id_or_date),))
    return cursor.rowcount > 0

# ==========================================
# Story 2: Breakfast Consumption CRUD
# ==========================================
def upsert_consumption(conn: sqlite3.Connection, data: ConsumptionCreate) -> Tuple[Dict[str, Any], bool]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM consumption_records WHERE date = ?", (data.date,))
    existing = cursor.fetchone()
    now_iso = datetime.now().isoformat()

    if existing:
        record_id = existing["id"]
        # Preserve existing actual_occupancy and notes if omitted in update request
        final_actual_occ = data.actual_occupancy if data.actual_occupancy is not None else existing["actual_occupancy"]
        final_notes = data.notes if (data.notes is not None and data.notes != "") else existing["notes"]

        cursor.execute(
            """
            UPDATE consumption_records
            SET actual_consumption = ?, actual_occupancy = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (data.actual_consumption, final_actual_occ, final_notes or "", now_iso, record_id)
        )
        is_created = False
    else:
        cursor.execute(
            """
            INSERT INTO consumption_records (date, actual_consumption, actual_occupancy, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (data.date, data.actual_consumption, data.actual_occupancy, data.notes or "", now_iso, now_iso)
        )
        record_id = cursor.lastrowid
        is_created = True

    cursor.execute("SELECT * FROM consumption_records WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    return dict(row), is_created

def update_consumption_partial(
    conn: sqlite3.Connection,
    record_id_or_date: str | int,
    data: ConsumptionUpdate
) -> Optional[Dict[str, Any]]:
    """Update only the explicitly provided fields of a consumption record."""
    cursor = conn.cursor()
    if isinstance(record_id_or_date, int) or str(record_id_or_date).isdigit():
        cursor.execute("SELECT * FROM consumption_records WHERE id = ?", (int(record_id_or_date),))
    else:
        cursor.execute("SELECT * FROM consumption_records WHERE date = ?", (str(record_id_or_date),))
    existing = cursor.fetchone()
    if not existing:
        return None

    fields = data.model_dump(exclude_unset=True)
    if not fields:
        return dict(existing)

    set_clauses = []
    values = []
    for key, val in fields.items():
        set_clauses.append(f"{key} = ?")
        values.append(val)

    now_iso = datetime.now().isoformat()
    set_clauses.append("updated_at = ?")
    values.append(now_iso)

    values.append(existing["id"])
    cursor.execute(f"UPDATE consumption_records SET {', '.join(set_clauses)} WHERE id = ?", tuple(values))
    cursor.execute("SELECT * FROM consumption_records WHERE id = ?", (existing["id"],))
    return dict(cursor.fetchone())

def get_consumption_by_id(conn: sqlite3.Connection, record_id: int) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM consumption_records WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_consumption_by_date(conn: sqlite3.Connection, target_date: str) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM consumption_records WHERE date = ?", (target_date,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_all_consumption(conn: sqlite3.Connection, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM consumption_records ORDER BY date DESC LIMIT ? OFFSET ?", (limit, offset))
    rows = cursor.fetchall()
    return [dict(r) for r in rows]

def delete_consumption(conn: sqlite3.Connection, record_id_or_date: str | int) -> bool:
    cursor = conn.cursor()
    if isinstance(record_id_or_date, int) or str(record_id_or_date).isdigit():
        cursor.execute("DELETE FROM consumption_records WHERE id = ?", (int(record_id_or_date),))
    else:
        cursor.execute("DELETE FROM consumption_records WHERE date = ?", (str(record_id_or_date),))
    return cursor.rowcount > 0

# ==========================================
# Story 3: Combined Historical View & KPIs
# ==========================================
def get_historical_records(
    conn: sqlite3.Connection,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_asc: bool = False
) -> Tuple[List[HistoricalRecordItem], HistorySummaryStats]:
    cursor = conn.cursor()

    # Query distinct dates unioned from both tables
    query = """
    SELECT 
        d.date as log_date,
        o.id as occ_id,
        o.expected_occupancy,
        o.total_rooms,
        o.notes as occ_notes,
        c.id as cons_id,
        c.actual_consumption,
        c.actual_occupancy,
        c.notes as cons_notes
    FROM (
        SELECT date FROM occupancy_records
        UNION
        SELECT date FROM consumption_records
    ) d
    LEFT JOIN occupancy_records o ON d.date = o.date
    LEFT JOIN consumption_records c ON d.date = c.date
    WHERE 1=1
    """
    params: List[Any] = []

    if start_date:
        query += " AND d.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND d.date <= ?"
        params.append(end_date)

    order_direction = "ASC" if sort_asc else "DESC"
    query += f" ORDER BY d.date {order_direction}"

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    records: List[HistoricalRecordItem] = []
    total_occ = 0
    count_occ = 0
    total_cons = 0
    count_cons = 0
    matched_total_occ = 0
    matched_total_cons = 0
    matched_count = 0
    min_date: Optional[str] = None
    max_date: Optional[str] = None

    for row in rows:
        d = row["log_date"]
        if min_date is None or d < min_date:
            min_date = d
        if max_date is None or d > max_date:
            max_date = d

        exp_occ = row["expected_occupancy"]
        act_cons = row["actual_consumption"]

        take_up: Optional[float] = None
        variance: Optional[int] = None
        status = "Unknown"

        if exp_occ is not None and act_cons is not None:
            status = "Complete"
            matched_count += 1
            variance = exp_occ - act_cons
            matched_total_occ += exp_occ
            matched_total_cons += act_cons
            if exp_occ > 0:
                take_up = round((act_cons / exp_occ) * 100, 1)
            else:
                take_up = 0.0
        elif exp_occ is not None:
            status = "Occupancy Only"
        elif act_cons is not None:
            status = "Consumption Only"

        if exp_occ is not None:
            total_occ += exp_occ
            count_occ += 1

        if act_cons is not None:
            total_cons += act_cons
            count_cons += 1

        records.append(HistoricalRecordItem(
            date=d,
            expected_occupancy=exp_occ,
            actual_consumption=act_cons,
            actual_occupancy=row["actual_occupancy"],
            total_rooms=row["total_rooms"],
            take_up_rate=take_up,
            variance=variance,
            status=status,
            occupancy_id=row["occ_id"],
            consumption_id=row["cons_id"],
            occupancy_notes=row["occ_notes"],
            consumption_notes=row["cons_notes"]
        ))

    # Calculate aggregate take-up rate across eligible matched dates
    if matched_count > 0:
        if matched_total_occ > 0:
            aggregate_take_up = round((matched_total_cons / matched_total_occ) * 100, 1)
        else:
            aggregate_take_up = 0.0
    else:
        aggregate_take_up = None

    summary = HistorySummaryStats(
        total_records=len(records),
        occupancy_logged_days=count_occ,
        consumption_logged_days=count_cons,
        matched_days=matched_count,
        avg_expected_occupancy=round(total_occ / count_occ, 1) if count_occ > 0 else None,
        avg_actual_consumption=round(total_cons / count_cons, 1) if count_cons > 0 else None,
        avg_take_up_rate=aggregate_take_up,
        min_date=min_date,
        max_date=max_date
    )

    return records, summary

def delete_history_date(conn: sqlite3.Connection, target_date: str) -> bool:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM occupancy_records WHERE date = ?", (target_date,))
    deleted_occ = cursor.rowcount
    cursor.execute("DELETE FROM consumption_records WHERE date = ?", (target_date,))
    deleted_cons = cursor.rowcount
    return (deleted_occ + deleted_cons) > 0

def clear_all_history(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM occupancy_records")
    cursor.execute("DELETE FROM consumption_records")

def seed_sample_hotel_data(conn: sqlite3.Connection, days: int = 14) -> int:
    """Populates realistic hotel historical data for demo and testing."""
    import random
    cursor = conn.cursor()
    today = date.today()
    start_day = today - timedelta(days=days)

    now_iso = datetime.now().isoformat()
    seeded_count = 0

    # Base realistic parameters
    base_rooms = 100
    for i in range(days):
        cur_date = (start_day + timedelta(days=i)).isoformat()
        
        # Day of week variation (weekend higher occupancy)
        weekday = (start_day + timedelta(days=i)).weekday()
        is_weekend = weekday in [4, 5] # Fri, Sat
        base_occ = random.randint(110, 150) if is_weekend else random.randint(65, 105)
        rooms_booked = min(base_rooms, int(base_occ / 1.5))
        
        # Realistic breakfast take-up rate ~ 75% to 92%
        takeup_percent = random.uniform(0.76, 0.92)
        actual_cons = max(0, int(base_occ * takeup_percent))

        cursor.execute("""
            INSERT INTO occupancy_records (date, expected_occupancy, total_rooms, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                expected_occupancy = excluded.expected_occupancy,
                total_rooms = excluded.total_rooms,
                notes = excluded.notes,
                updated_at = excluded.updated_at
        """, (cur_date, base_occ, rooms_booked, "Sample occupancy entry" if is_weekend else "Standard weekday", now_iso, now_iso))

        # For the last 2 days (today and tomorrow), simulate only occupancy entered
        if i < days - 2:
            cursor.execute("""
                INSERT INTO consumption_records (date, actual_consumption, actual_occupancy, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    actual_consumption = excluded.actual_consumption,
                    actual_occupancy = excluded.actual_occupancy,
                    notes = excluded.notes,
                    updated_at = excluded.updated_at
            """, (cur_date, actual_cons, base_occ - random.randint(0, 4), "Buffet service recorded", now_iso, now_iso))

        seeded_count += 1

    return seeded_count
