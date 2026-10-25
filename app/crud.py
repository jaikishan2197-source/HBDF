import sqlite3
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from app.models import (
    OccupancyCreate, OccupancyUpdate,
    ConsumptionCreate, ConsumptionUpdate,
    HistoricalRecordItem, HistorySummaryStats,
    DishRecordCreate, DishRecordUpdate, DishRecordResponse,
    DayAccuracyEvaluation, ForecastAccuracyResponse,
    DishWasteSummary, WasteAnalysisResponse,
    SUPPORTED_DISHES, DISH_UNITS, DISH_DISPLAY_NAMES
)

# ==========================================
# Story 1: Occupancy CRUD
# ==========================================
def upsert_occupancy(conn: sqlite3.Connection, data: OccupancyCreate) -> Tuple[Dict[str, Any], bool]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM occupancy_records WHERE date = ?", (data.date,))
    existing = cursor.fetchone()
    now_iso = datetime.now().isoformat()

    guests_inc = data.guests_included
    guests_oth = data.guests_other
    event_cov = data.event_expected_covers if data.event_expected_covers is not None else 0

    if existing:
        record_id = existing["id"]
        # Preserve existing fields if omitted in update request
        final_rooms = data.total_rooms if data.total_rooms is not None else existing["total_rooms"]
        final_notes = data.notes if (data.notes is not None and data.notes != "") else existing["notes"]
        final_guests_inc = guests_inc if guests_inc is not None else existing["guests_included"]
        final_guests_oth = guests_oth if guests_oth is not None else existing["guests_other"]
        final_event_cov = event_cov if data.event_expected_covers is not None else existing["event_expected_covers"]

        cursor.execute(
            """
            UPDATE occupancy_records
            SET expected_occupancy = ?, guests_included = ?, guests_other = ?, event_expected_covers = ?, total_rooms = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (data.expected_occupancy, final_guests_inc, final_guests_oth, final_event_cov, final_rooms, final_notes or "", now_iso, record_id)
        )
        is_created = False
    else:
        cursor.execute(
            """
            INSERT INTO occupancy_records (date, expected_occupancy, guests_included, guests_other, event_expected_covers, total_rooms, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (data.date, data.expected_occupancy, guests_inc, guests_oth, event_cov, data.total_rooms, data.notes or "", now_iso, now_iso)
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
    inc_cov = int(round(data.actual_consumption * 0.80))
    oth_cov = data.actual_consumption - inc_cov

    if existing:
        record_id = existing["id"]
        # Preserve existing actual_occupancy and notes if omitted in update request
        final_actual_occ = data.actual_occupancy if data.actual_occupancy is not None else existing["actual_occupancy"]
        final_notes = data.notes if (data.notes is not None and data.notes != "") else existing["notes"]

        cursor.execute(
            """
            UPDATE consumption_records
            SET actual_consumption = ?, actual_occupancy = ?,
                covers_included = COALESCE(covers_included, ?),
                covers_other = COALESCE(covers_other, ?),
                notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (data.actual_consumption, final_actual_occ, inc_cov, oth_cov, final_notes or "", now_iso, record_id)
        )
        is_created = False
    else:
        cursor.execute(
            """
            INSERT INTO consumption_records (date, actual_consumption, actual_occupancy, covers_included, covers_other, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (data.date, data.actual_consumption, data.actual_occupancy, inc_cov, oth_cov, data.notes or "", now_iso, now_iso)
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
        requires_verification = False
        verification_reason = None

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

            if act_cons > exp_occ:
                requires_verification = True
                verification_reason = f"Actual breakfast served ({act_cons}) exceeds expected resident occupancy ({exp_occ})"
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
            consumption_notes=row["cons_notes"],
            requires_verification=requires_verification,
            verification_reason=verification_reason
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
    cursor.execute("DELETE FROM dish_daily_records")

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
        
        # Realistic breakfast split
        inc_guests = int(round(base_occ * 0.75))
        oth_guests = base_occ - inc_guests
        evt_expected = random.randint(10, 25) if random.random() < 0.25 else 0

        inc_covers = min(inc_guests, int(round(inc_guests * random.uniform(0.85, 0.93))))
        oth_covers = min(oth_guests, int(round(oth_guests * random.uniform(0.24, 0.36))))
        evt_covers = evt_expected
        actual_cons = inc_covers + oth_covers + evt_covers

        cursor.execute("""
            INSERT INTO occupancy_records (date, expected_occupancy, total_rooms, guests_included, guests_other, event_expected_covers, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                expected_occupancy = excluded.expected_occupancy,
                total_rooms = excluded.total_rooms,
                guests_included = excluded.guests_included,
                guests_other = excluded.guests_other,
                event_expected_covers = excluded.event_expected_covers,
                notes = excluded.notes,
                updated_at = excluded.updated_at
        """, (cur_date, base_occ, rooms_booked, inc_guests, oth_guests, evt_expected, "Sample occupancy entry" if is_weekend else "Standard weekday", now_iso, now_iso))

        # For the last 2 days (today and tomorrow), simulate only occupancy entered
        if i < days - 2:
            cursor.execute("""
                INSERT INTO consumption_records (date, actual_consumption, actual_occupancy, covers_included, covers_other, event_covers, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    actual_consumption = excluded.actual_consumption,
                    actual_occupancy = excluded.actual_occupancy,
                    covers_included = excluded.covers_included,
                    covers_other = excluded.covers_other,
                    event_covers = excluded.event_covers,
                    notes = excluded.notes,
                    updated_at = excluded.updated_at
            """, (cur_date, actual_cons, base_occ - random.randint(0, 4), inc_covers, oth_covers, evt_covers, "Buffet service recorded", now_iso, now_iso))

            # Realistic dish consumption, prep, waste, and occasional stock-out
            dish_configs = [
                ("idli", 1.2, 1.0, 1.08),
                ("dosa", 0.35, 1.0, 1.10),
                ("poori", 0.3, 1.0, 1.08),
                ("pongal", 0.35, 0.1, 1.08),
                ("sambar", 0.4, 0.5, 1.10),
            ]
            is_stockout_day = (i == 4)  # Day 4 has a stock-out for dosa
            for dish_name, per_guest, inc, surplus in dish_configs:
                raw_consumed = actual_cons * per_guest
                if inc == 1.0:
                    cons_qty = float(round(raw_consumed))
                    prep_qty = float(round(cons_qty * surplus))
                else:
                    cons_qty = round(round(raw_consumed / inc) * inc, 1)
                    prep_qty = round(round((cons_qty * surplus) / inc) * inc, 1)

                stockout = 0
                notes = "Buffet service recorded"
                if is_stockout_day and dish_name == "dosa":
                    stockout = 1
                    prep_qty = cons_qty
                    waste_qty = 0.0
                    notes = "Dosa ran out due to unexpected walk-in rush"
                else:
                    waste_qty = round(prep_qty - cons_qty, 1) if inc != 1.0 else float(int(prep_qty - cons_qty))

                cursor.execute("""
                    INSERT INTO dish_daily_records (date, dish, quantity_prepared, quantity_consumed, quantity_discarded, stock_out, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(date, dish) DO UPDATE SET
                        quantity_prepared = excluded.quantity_prepared,
                        quantity_consumed = excluded.quantity_consumed,
                        quantity_discarded = excluded.quantity_discarded,
                        stock_out = excluded.stock_out,
                        notes = excluded.notes,
                        updated_at = excluded.updated_at
                """, (cur_date, dish_name, prep_qty, cons_qty, waste_qty, stockout, notes, now_iso, now_iso))

        seeded_count += 1

    return seeded_count


# ==========================================
# User Account CRUD
# ==========================================
def get_user_by_username(conn: sqlite3.Connection, username: str) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username.strip(),))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_user_by_email(conn: sqlite3.Connection, email: str) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip().lower(),))
    row = cursor.fetchone()
    return dict(row) if row else None

def create_user(
    conn: sqlite3.Connection,
    full_name: str,
    username: str,
    email: str,
    password_hash: str
) -> Dict[str, Any]:
    now_iso = datetime.now().isoformat()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (full_name, username, email, password_hash, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (full_name.strip(), username.strip(), email.strip().lower(), password_hash, now_iso, now_iso)
    )
    user_id = cursor.lastrowid
    cursor.execute("SELECT id, full_name, username, email, created_at, updated_at FROM users WHERE id = ?", (user_id,))
    return dict(cursor.fetchone())


# ==========================================
# Epic 3 - Dish-wise Records, Waste & Accuracy CRUD
# ==========================================
def upsert_dish_record(conn: sqlite3.Connection, data: DishRecordCreate) -> Tuple[Dict[str, Any], bool]:
    cursor = conn.cursor()
    dish = data.dish.strip().lower()
    cursor.execute("SELECT * FROM dish_daily_records WHERE date = ? AND dish = ?", (data.date, dish))
    existing = cursor.fetchone()
    now_iso = datetime.now().isoformat()

    if existing:
        record_id = existing["id"]
        cursor.execute(
            """
            UPDATE dish_daily_records
            SET quantity_prepared = ?, quantity_consumed = ?, quantity_discarded = ?,
                stock_out = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (data.quantity_prepared, data.quantity_consumed, data.quantity_discarded,
             1 if data.stock_out else 0, data.notes or "", now_iso, record_id)
        )
        is_created = False
    else:
        cursor.execute(
            """
            INSERT INTO dish_daily_records (date, dish, quantity_prepared, quantity_consumed, quantity_discarded, stock_out, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (data.date, dish, data.quantity_prepared, data.quantity_consumed, data.quantity_discarded,
             1 if data.stock_out else 0, data.notes or "", now_iso, now_iso)
        )
        record_id = cursor.lastrowid
        is_created = True

    cursor.execute("SELECT * FROM dish_daily_records WHERE id = ?", (record_id,))
    row = dict(cursor.fetchone())
    row["stock_out"] = bool(row["stock_out"])
    row["unit"] = DISH_UNITS.get(row["dish"], "pieces")
    return row, is_created


def update_dish_record(
    conn: sqlite3.Connection,
    target_date: str,
    dish: str,
    data: DishRecordUpdate
) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor()
    dish_clean = dish.strip().lower()
    cursor.execute("SELECT * FROM dish_daily_records WHERE date = ? AND dish = ?", (target_date, dish_clean))
    existing = cursor.fetchone()
    if not existing:
        return None

    prep = data.quantity_prepared if data.quantity_prepared is not None else existing["quantity_prepared"]
    cons = data.quantity_consumed if data.quantity_consumed is not None else existing["quantity_consumed"]
    disc = data.quantity_discarded if data.quantity_discarded is not None else existing["quantity_discarded"]
    stockout = (1 if data.stock_out else 0) if data.stock_out is not None else existing["stock_out"]
    notes = data.notes if data.notes is not None else existing["notes"]

    if (cons + disc) > (prep + 1e-4):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail=f"Sum of consumed ({cons}) and discarded ({disc}) cannot exceed prepared quantity ({prep})."
        )

    now_iso = datetime.now().isoformat()
    cursor.execute(
        """
        UPDATE dish_daily_records
        SET quantity_prepared = ?, quantity_consumed = ?, quantity_discarded = ?,
            stock_out = ?, notes = ?, updated_at = ?
        WHERE id = ?
        """,
        (prep, cons, disc, stockout, notes or "", now_iso, existing["id"])
    )
    cursor.execute("SELECT * FROM dish_daily_records WHERE id = ?", (existing["id"],))
    row = dict(cursor.fetchone())
    row["stock_out"] = bool(row["stock_out"])
    row["unit"] = DISH_UNITS.get(row["dish"], "pieces")
    return row


def get_dish_records(
    conn: sqlite3.Connection,
    dish: Optional[str] = None,
    target_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    query = "SELECT * FROM dish_daily_records WHERE 1=1"
    params: List[Any] = []

    if dish:
        query += " AND dish = ? COLLATE NOCASE"
        params.append(dish.strip().lower())
    if target_date:
        query += " AND date = ?"
        params.append(target_date)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC, dish ASC"
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["stock_out"] = bool(d["stock_out"])
        d["unit"] = DISH_UNITS.get(d["dish"], "pieces")
        result.append(d)
    return result


def get_dish_record_single(conn: sqlite3.Connection, target_date: str, dish: str) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dish_daily_records WHERE date = ? AND dish = ? COLLATE NOCASE", (target_date, dish.strip().lower()))
    row = cursor.fetchone()
    if not row:
        return None
    d = dict(row)
    d["stock_out"] = bool(d["stock_out"])
    d["unit"] = DISH_UNITS.get(d["dish"], "pieces")
    return d


def delete_dish_record(conn: sqlite3.Connection, target_date: str, dish: str) -> bool:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dish_daily_records WHERE date = ? AND dish = ? COLLATE NOCASE", (target_date, dish.strip().lower()))
    return cursor.rowcount > 0


def calculate_leakage_free_prediction(
    conn: sqlite3.Connection,
    service_date: str
) -> Optional[int]:
    """
    Computes expected breakfast covers for service_date using strictly information
    available by 9 PM on the previous day (preventing any future data leakage).
    """
    cursor = conn.cursor()
    # 1. Look up planned occupancy for this service_date
    cursor.execute("SELECT * FROM occupancy_records WHERE date = ?", (service_date,))
    occ_row = cursor.fetchone()
    if not occ_row:
        return None

    g_inc = occ_row["guests_included"]
    g_oth = occ_row["guests_other"]
    evt_covers = occ_row["event_expected_covers"] or 0
    if g_inc is None or g_oth is None:
        return None

    # Target weekday
    target_dt = date.fromisoformat(service_date)
    target_weekday = target_dt.weekday()

    # 2. Look up historical records STRICTLY BEFORE service_date
    cursor.execute(
        """
        SELECT o.date, o.guests_included, o.guests_other, o.expected_occupancy,
               c.covers_included, c.covers_other, c.actual_consumption
        FROM occupancy_records o
        JOIN consumption_records c ON o.date = c.date
        WHERE o.date < ?
        ORDER BY o.date DESC
        """,
        (service_date,)
    )
    all_prior = cursor.fetchall()

    eligible_prior = []
    for r in all_prior:
        r_dt = date.fromisoformat(r["date"])
        if r_dt.weekday() != target_weekday:
            continue
        gi = r["guests_included"]
        if gi is None and r["expected_occupancy"] is not None:
            gi = int(round(r["expected_occupancy"] * 0.75))
        go = r["guests_other"]
        if go is None and r["expected_occupancy"] is not None:
            go = r["expected_occupancy"] - (gi or 0)

        ci = r["covers_included"]
        if ci is None and r["actual_consumption"] is not None:
            ci = int(round(r["actual_consumption"] * 0.80))
        co = r["covers_other"]
        if co is None and r["actual_consumption"] is not None:
            co = r["actual_consumption"] - (ci or 0)

        if gi is None or ci is None or go is None or co is None:
            continue
        # Anomaly exclusion check
        if ci > gi or co > go or gi < 0 or go < 0:
            continue
        eligible_prior.append({
            "guests_included": gi,
            "covers_included": ci,
            "guests_other": go,
            "covers_other": co,
        })
        if len(eligible_prior) >= 4:
            break

    if not eligible_prior:
        return None

    sum_gi = sum(r["guests_included"] for r in eligible_prior)
    sum_ci = sum(r["covers_included"] for r in eligible_prior)
    sum_go = sum(r["guests_other"] for r in eligible_prior)
    sum_co = sum(r["covers_other"] for r in eligible_prior)

    if sum_gi <= 0 or sum_go <= 0:
        return None

    r_i = sum_ci / sum_gi
    r_o = sum_co / sum_go
    predicted_covers = int(round((g_inc * r_i) + (g_oth * r_o) + evt_covers))
    return predicted_covers


def get_forecast_accuracy_evaluation(
    conn: sqlite3.Connection,
    days: int = 14
) -> ForecastAccuracyResponse:
    """
    Evaluates forecast accuracy for the latest eligible service days (up to 14).
    Strictly leakage-free: evaluates each historical date using only information
    known by 9 PM on the previous day.
    Stock-out days are excluded because true customer demand was censored/unknown.
    Zero-actual days are excluded from the MAPE denominator.
    """
    from app.forecasting import WEEKDAY_NAMES
    cursor = conn.cursor()

    # Find service dates with consumption recorded (latest first)
    today_iso = date.today().isoformat()
    cursor.execute(
        """
        SELECT date, actual_consumption
        FROM consumption_records
        WHERE date <= ?
        ORDER BY date DESC
        LIMIT ?
        """,
        (today_iso, days)
    )
    cons_rows = cursor.fetchall()

    evaluations: List[DayAccuracyEvaluation] = []
    zero_actual_days_count = 0
    stockout_days_count = 0

    for crow in cons_rows:
        s_date = crow["date"]
        s_dt = date.fromisoformat(s_date)
        weekday_name = WEEKDAY_NAMES[s_dt.weekday()]
        actual_cons = crow["actual_consumption"]

        # Check stock-out
        cursor.execute("SELECT 1 FROM dish_daily_records WHERE date = ? AND stock_out = 1", (s_date,))
        has_stockout = bool(cursor.fetchone())
        if has_stockout:
            stockout_days_count += 1

        # Check occupancy
        cursor.execute("SELECT * FROM occupancy_records WHERE date = ?", (s_date,))
        occ_row = cursor.fetchone()

        pred_covers = calculate_leakage_free_prediction(conn, s_date)

        if has_stockout:
            evaluations.append(DayAccuracyEvaluation(
                date=s_date,
                weekday=weekday_name,
                actual_covers=actual_cons,
                predicted_covers=pred_covers,
                absolute_error=abs(pred_covers - actual_cons) if pred_covers is not None else None,
                absolute_percentage_error=None,
                eligible=False,
                ineligibility_reason="Stock-out occurred; true demand unknown/censored",
                stock_out_occurred=True
            ))
        elif occ_row is None:
            evaluations.append(DayAccuracyEvaluation(
                date=s_date,
                weekday=weekday_name,
                actual_covers=actual_cons,
                predicted_covers=None,
                absolute_error=None,
                absolute_percentage_error=None,
                eligible=False,
                ineligibility_reason="No expected occupancy recorded prior to service",
                stock_out_occurred=False
            ))
        elif pred_covers is None:
            evaluations.append(DayAccuracyEvaluation(
                date=s_date,
                weekday=weekday_name,
                actual_covers=actual_cons,
                predicted_covers=None,
                absolute_error=None,
                absolute_percentage_error=None,
                eligible=False,
                ineligibility_reason="Insufficient matching weekday history strictly prior to service date",
                stock_out_occurred=False
            ))
        elif actual_cons == 0:
            zero_actual_days_count += 1
            evaluations.append(DayAccuracyEvaluation(
                date=s_date,
                weekday=weekday_name,
                actual_covers=actual_cons,
                predicted_covers=pred_covers,
                absolute_error=abs(pred_covers - actual_cons),
                absolute_percentage_error=None,
                eligible=False,
                ineligibility_reason="Actual covers are zero; excluded from MAPE denominator to prevent division by zero",
                stock_out_occurred=False
            ))
        else:
            abs_err = abs(pred_covers - actual_cons)
            ape = round((abs_err / actual_cons) * 100.0, 2)
            evaluations.append(DayAccuracyEvaluation(
                date=s_date,
                weekday=weekday_name,
                actual_covers=actual_cons,
                predicted_covers=pred_covers,
                absolute_error=abs_err,
                absolute_percentage_error=ape,
                eligible=True,
                ineligibility_reason=None,
                stock_out_occurred=False
            ))

    eligible_evals = [e for e in evaluations if e.eligible and e.absolute_percentage_error is not None]
    if eligible_evals:
        mape = round(sum(e.absolute_percentage_error for e in eligible_evals) / len(eligible_evals), 2)
        status_msg = f"Evaluated across {len(eligible_evals)} eligible service day(s) strictly prior to service (leakage-free)."
    else:
        mape = None
        status_msg = "Insufficient eligible historical service days to calculate MAPE."

    return ForecastAccuracyResponse(
        evaluation_days_count=len(evaluations),
        eligible_days_count=len(eligible_evals),
        excluded_stockout_days=stockout_days_count,
        zero_actual_days_excluded=zero_actual_days_count,
        mape=mape,
        evaluations=evaluations,
        status_message=status_msg,
        notice="SYNTHETIC DEMO DATA — NOT REAL HOTEL DATA"
    )


def get_waste_and_shortage_analysis(
    conn: sqlite3.Connection
) -> WasteAnalysisResponse:
    """
    Calculates dish-wise recorded waste and simulated waste/shortage.
    Units are kept distinct. Monetary values are never invented.
    Simulated metrics are strictly labeled as simulated.
    """
    from app.forecasting import DEFAULT_PORTION_ASSUMPTIONS, ITEM_INCREMENTS, _round_up_increment
    cursor = conn.cursor()

    dish_summaries: List[DishWasteSummary] = []

    for dish in SUPPORTED_DISHES:
        unit = DISH_UNITS.get(dish, "pieces")
        cursor.execute(
            "SELECT * FROM dish_daily_records WHERE dish = ? COLLATE NOCASE ORDER BY date ASC",
            (dish,)
        )
        records = [dict(r) for r in cursor.fetchall()]

        days_recorded = len(records)
        total_prep = round(sum(r["quantity_prepared"] for r in records), 2)
        total_cons = round(sum(r["quantity_consumed"] for r in records), 2)
        total_disc = round(sum(r["quantity_discarded"] for r in records), 2)
        stockout_days = sum(1 for r in records if r["stock_out"] == 1)

        waste_pct = round((total_disc / total_prep) * 100.0, 1) if total_prep > 0 else None

        # Simulation
        servings = DEFAULT_PORTION_ASSUMPTIONS.get(dish, 1.0)
        inc = ITEM_INCREMENTS.get(dish, 1.0)

        sim_wastes: List[float] = []
        sim_shortages: List[float] = []

        for r in records:
            pred_covers = calculate_leakage_free_prediction(conn, r["date"])
            if pred_covers is None:
                continue

            base_portions = pred_covers * servings
            buffered_prep = _round_up_increment(base_portions * 1.10, inc)
            act_cons = r["quantity_consumed"]

            if buffered_prep > act_cons:
                sim_wastes.append(buffered_prep - act_cons)
            elif buffered_prep < act_cons:
                sim_shortages.append(act_cons - buffered_prep)

        if sim_wastes or sim_shortages:
            sim_waste_val = round(sum(sim_wastes), 1) if inc != 1.0 else float(int(round(sum(sim_wastes))))
            sim_shortage_val = round(sum(sim_shortages), 1) if inc != 1.0 else float(int(round(sum(sim_shortages))))
            sim_status = "simulated"
        else:
            sim_waste_val = None
            sim_shortage_val = None
            sim_status = "insufficient_inputs"

        dish_summaries.append(DishWasteSummary(
            dish=DISH_DISPLAY_NAMES.get(dish, dish.capitalize()),
            unit=unit,
            days_recorded=days_recorded,
            total_prepared=total_prep,
            total_consumed=total_cons,
            total_discarded=total_disc,
            waste_percentage=waste_pct,
            stock_out_days=stockout_days,
            simulated_waste=sim_waste_val,
            simulated_shortage=sim_shortage_val,
            simulation_status=sim_status
        ))

    return WasteAnalysisResponse(
        dish_summaries=dish_summaries,
        notice="SYNTHETIC DEMO DATA — NOT REAL HOTEL DATA",
        notes="Recorded metrics reflect unverified synthetic demo entries. They must not be cited as real-world hotel waste or operational benchmarks. Simulated metrics model performance under a 10% buffered demand forecast. Dish units are kept strictly separate."
    )

