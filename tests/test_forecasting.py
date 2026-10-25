from datetime import date, timedelta
from math import ceil
import pytest


def forecast_payload(**overrides):
    payload = {
        "forecast_date": (date.today() + timedelta(days=7)).isoformat(),
        "expected_occupancy": 120,
        "guests_included": 90,
        "guests_other": 30,
        "event_expected_covers": 0,
        "is_holiday": True,
        "group_booking_guests": 30,
        "special_event": True,
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def seeded_history(client):
    """Seed 35 days of history so at least 4 matching weekdays exist for any day."""
    client.post("/api/history/seed?days=35")


def test_forecast_compares_models_with_chronological_evaluation(client, seeded_history):
    response = client.post("/api/forecast", json=forecast_payload())

    assert response.status_code == 200
    data = response.json()
    assert data["synthetic_training_data"] is True
    assert data["training_days"] + data["evaluation_days"] == 1096
    assert data["evaluation_start_date"] < data["evaluation_end_date"]
    assert {result["model"] for result in data["model_comparison"]} == {
        "Historical Average",
        "Random Forest Regressor",
        "Gradient Boosting Regressor",
    }
    assert all(result["mae"] >= 0 and result["rmse"] >= 0 for result in data["model_comparison"])
    assert data["forecasted_breakfast_guests"] >= 0
    assert data["selected_model"] == "Two-Rate Capture Rate"
    assert data["calculation_breakdown"] is not None


def test_forecast_uses_configurable_portion_assumptions(client, seeded_history):
    response = client.post(
        "/api/forecast",
        json=forecast_payload(portion_assumptions={"idli": 2.0, "dosa": 0.5}),
    )

    assert response.status_code == 200
    data = response.json()
    portions = data["food_portions"]
    assert "idli" in portions
    assert "dosa" in portions
    assert "sambar" in portions
    assert portions["idli"]["servings_per_guest"] == 2.0
    # Portions include default 10% buffer
    forecasted = data["forecasted_breakfast_guests"]
    assert portions["idli"]["estimated_portions"] == ceil(round(forecasted * 2.0 * 1.10, 4))
    assert portions["dosa"]["servings_per_guest"] == 0.5


@pytest.mark.parametrize(
    "overrides",
    [
        {"forecast_date": (date.today() - timedelta(days=1)).isoformat()},
        {"forecast_date": "2026-02-31"},
        {"expected_occupancy": 49},
        {"expected_occupancy": 201},
        {"group_booking_guests": 121},
        {"portion_assumptions": {"unknown": 1.0}},
        {"portion_assumptions": {"idli": -0.1}},
        {"portion_assumptions": {"idli": 3.1}},
        {"buffer_percent": -1.0},
        {"buffer_percent": 26.0},
    ],
)
def test_forecast_rejects_invalid_request_values(client, overrides):
    response = client.post("/api/forecast", json=forecast_payload(**overrides))
    assert response.status_code == 422


def test_forecast_does_not_change_historical_records(client, seeded_history):
    occupancy_before = client.get("/api/occupancy").json()
    consumption_before = client.get("/api/consumption").json()

    response = client.post("/api/forecast", json=forecast_payload())

    assert response.status_code == 200
    assert client.get("/api/occupancy").json() == occupancy_before
    assert client.get("/api/consumption").json() == consumption_before


def test_forecast_two_rate_capture_rate_calculation(client, seeded_history):
    """Test transparent calculation of two-rate capture forecast."""
    target_date = (date.today() + timedelta(days=7)).isoformat()
    response = client.post(
        "/api/forecast",
        json={
            "forecast_date": target_date,
            "guests_included": 100,
            "guests_other": 40,
            "event_expected_covers": 15,
            "buffer_percent": 10.0,
        },
    )

    assert response.status_code == 200
    data = response.json()
    breakdown = data["calculation_breakdown"]
    assert breakdown is not None
    assert len(breakdown["historical_dates_used"]) >= 1
    assert breakdown["sum_guests_included"] > 0
    assert breakdown["sum_guests_other"] > 0
    assert 0.0 <= breakdown["capture_rate_included"] <= 1.0
    assert 0.0 <= breakdown["capture_rate_other"] <= 1.0

    # Verify math
    expected_resident = (100 * breakdown["capture_rate_included"]) + (40 * breakdown["capture_rate_other"])
    assert abs(breakdown["resident_covers"] - round(expected_resident, 1)) <= 0.2
    expected_final = int(round(expected_resident + 15))
    assert data["forecasted_breakfast_guests"] == expected_final


def test_forecast_error_when_no_matching_weekdays(client):
    """Test clear validation error (400) when no historical data exists."""
    client.post("/api/history/clear")
    target_date = (date.today() + timedelta(days=7)).isoformat()
    response = client.post(
        "/api/forecast",
        json={
            "forecast_date": target_date,
            "expected_occupancy": 100,
        },
    )
    assert response.status_code == 400
    assert "No eligible historical data exists" in response.json()["detail"]


def test_forecast_warning_when_fewer_than_four_weekdays(client):
    """Test warning issued when fewer than 4 matching weekdays exist."""
    client.post("/api/history/clear")
    # Seed only 10 days so matching weekdays are fewer than 4
    client.post("/api/history/seed?days=10")
    target_date = (date.today() + timedelta(days=7)).isoformat()
    response = client.post(
        "/api/forecast",
        json={
            "forecast_date": target_date,
            "expected_occupancy": 100,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["warning"] is not None
    assert "Fewer than 4 matching weekdays available" in data["warning"]


def test_forecast_zero_guests_on_forecast_date(client, seeded_history):
    """Test that if a guest group has zero guests on the forecast date, it simply adds 0 covers."""
    target_date = (date.today() + timedelta(days=7)).isoformat()
    response = client.post(
        "/api/forecast",
        json={
            "forecast_date": target_date,
            "guests_included": 100,
            "guests_other": 0,
            "event_expected_covers": 0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    breakdown = data["calculation_breakdown"]
    expected_resident = int(round(100 * breakdown["capture_rate_included"]))
    assert data["forecasted_breakfast_guests"] == expected_resident


def test_forecast_prevents_future_data_leakage(client, seeded_history):
    """Ensure records on or after the forecast date are strictly excluded from capture rate calculations."""
    target_date = (date.today() + timedelta(days=7)).isoformat()
    # Insert dummy records far in the future
    future_date = (date.today() + timedelta(days=14)).isoformat()
    client.post("/api/occupancy", json={"date": future_date, "expected_occupancy": 150})

    response = client.post(
        "/api/forecast",
        json={"forecast_date": target_date, "expected_occupancy": 120},
    )
    assert response.status_code == 200
    data = response.json()
    for used_date in data["calculation_breakdown"]["historical_dates_used"]:
        assert used_date < target_date


def test_forecast_separate_guest_groups_and_total_resident(client, seeded_history):
    """Test separate guest groups (included vs other) and sum display as total resident guests."""
    target_date = (date.today() + timedelta(days=7)).isoformat()
    response = client.post(
        "/api/forecast",
        json={
            "forecast_date": target_date,
            "guests_included": 85,
            "guests_other": 35,
            "event_expected_covers": 12,
            "buffer_percent": 10.0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_resident_guests"] == 120
    assert data["guests_included"] == 85
    assert data["guests_other"] == 35
    assert data["event_expected_covers"] == 12

    b = data["calculation_breakdown"]
    expected_resident = (85 * b["capture_rate_included"]) + (35 * b["capture_rate_other"])
    assert abs(b["resident_covers"] - round(expected_resident, 1)) <= 0.2
    expected_final = int(round(expected_resident + 12))
    assert data["forecasted_breakfast_guests"] == expected_final


def test_forecast_rejects_negative_guest_counts(client):
    """Reject negative guest counts and negative event covers with 422."""
    target_date = (date.today() + timedelta(days=7)).isoformat()
    bad_payloads = [
        {"forecast_date": target_date, "guests_included": -10, "guests_other": 60},
        {"forecast_date": target_date, "guests_included": 60, "guests_other": -5},
        {"forecast_date": target_date, "guests_included": 60, "guests_other": 40, "event_expected_covers": -1},
    ]
    for p in bad_payloads:
        res = client.post("/api/forecast", json=p)
        assert res.status_code == 422


def test_group_booking_guests_does_not_substitute_guest_categories(client, seeded_history):
    """Ensure group booking guests do not substitute or overwrite either guest category."""
    target_date = (date.today() + timedelta(days=7)).isoformat()
    response = client.post(
        "/api/forecast",
        json={
            "forecast_date": target_date,
            "guests_included": 80,
            "guests_other": 30,
            "group_booking_guests": 25,
            "event_expected_covers": 0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    b = data["calculation_breakdown"]
    # Capture rate calculation is strictly based on guests_included and guests_other
    expected_resident = (80 * b["capture_rate_included"]) + (30 * b["capture_rate_other"])
    assert abs(b["resident_covers"] - round(expected_resident, 1)) <= 0.2

    # Overly large group booking exceeding resident capacity is rejected
    invalid_res = client.post(
        "/api/forecast",
        json={
            "forecast_date": target_date,
            "guests_included": 80,
            "guests_other": 30,
            "group_booking_guests": 150,
        },
    )
    assert invalid_res.status_code == 422


def test_forecast_error_zero_denominators(client):
    """Raise 400 error when historical guest count in window is zero."""
    client.post("/api/history/clear")
    target_date = (date.today() + timedelta(days=7)).isoformat()
    target_weekday = date.fromisoformat(target_date).weekday()

    # Find 2 past dates matching the target weekday
    past_dates = []
    d = date.today() - timedelta(days=1)
    while len(past_dates) < 2:
        if d.weekday() == target_weekday:
            past_dates.append(d.isoformat())
        d -= timedelta(days=1)

    # Insert records with zero guests_included
    from app.database import get_db
    with get_db() as conn:
        for p_date in past_dates:
            conn.execute(
                "INSERT INTO occupancy_records (date, expected_occupancy, guests_included, guests_other) VALUES (?, 30, 0, 30)",
                (p_date,),
            )
            conn.execute(
                "INSERT INTO consumption_records (date, actual_consumption, covers_included, covers_other) VALUES (?, 20, 0, 20)",
                (p_date,),
            )

    res = client.post(
        "/api/forecast",
        json={"forecast_date": target_date, "guests_included": 80, "guests_other": 30},
    )
    assert res.status_code == 400
    assert "Historical included-breakfast guest count is zero" in res.json()["detail"]


def test_forecast_error_missing_historical_split_data(client):
    """Raise 400 error when required historical split fields are NULL in matching window."""
    client.post("/api/history/clear")
    target_date = (date.today() + timedelta(days=7)).isoformat()
    target_weekday = date.fromisoformat(target_date).weekday()

    d = date.today() - timedelta(days=1)
    matching_date = None
    while not matching_date:
        if d.weekday() == target_weekday:
            matching_date = d.isoformat()
        d -= timedelta(days=1)

    from app.database import get_db
    with get_db() as conn:
        conn.execute(
            "INSERT INTO occupancy_records (date, expected_occupancy, guests_included, guests_other) VALUES (?, 100, NULL, 30)",
            (matching_date,),
        )
        conn.execute(
            "INSERT INTO consumption_records (date, actual_consumption, covers_included, covers_other) VALUES (?, 80, 60, 20)",
            (matching_date,),
        )

    res = client.post(
        "/api/forecast",
        json={"forecast_date": target_date, "guests_included": 80, "guests_other": 30},
    )
    assert res.status_code == 400
    assert "Required guest-group data is missing" in res.json()["detail"]


def test_food_portions_units_and_increment_rounding(client, seeded_history):
    """Verify correct item units, default menu without bread, and rounding increments (1 piece, 0.1 kg, 0.5 L)."""
    target_date = (date.today() + timedelta(days=7)).isoformat()
    res = client.post(
        "/api/forecast",
        json={
            "forecast_date": target_date,
            "guests_included": 90,
            "guests_other": 30,
            "buffer_percent": 10.0,
            "portion_assumptions": {
                "idli": 1.2,
                "dosa": 0.35,
                "poori": 0.3,
                "pongal": 0.35,
                "sambar": 0.4,
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    portions = data["food_portions"]

    # Verify documented 5-item menu without bread
    assert "bread" not in portions
    assert set(portions.keys()) == {"idli", "dosa", "poori", "pongal", "sambar"}

    # Units
    assert portions["idli"]["unit"] == "pieces"
    assert portions["dosa"]["unit"] == "pieces"
    assert portions["poori"]["unit"] == "pieces"
    assert portions["pongal"]["unit"] == "kg"
    assert portions["sambar"]["unit"] == "litres"

    # Verify rounding UP increments
    # Idli: whole piece (increment 1.0)
    assert portions["idli"]["estimated_portions"] == float(int(portions["idli"]["estimated_portions"]))

    # Pongal: 0.1 kg increment
    pongal_val = portions["pongal"]["estimated_portions"]
    assert round(pongal_val * 10) == round(pongal_val, 1) * 10

    # Sambar: 0.5 litre increment
    sambar_val = portions["sambar"]["estimated_portions"]
    assert round((sambar_val * 2) % 1, 3) in (0.0, 1.0)


def test_food_portions_buffer_bounds_and_amounts(client, seeded_history):
    """Verify 0% and 25% buffer boundaries and buffer_amount differences."""
    target_date = (date.today() + timedelta(days=7)).isoformat()

    # 0% buffer
    res_0 = client.post(
        "/api/forecast",
        json={"forecast_date": target_date, "guests_included": 80, "guests_other": 30, "buffer_percent": 0.0},
    )
    assert res_0.status_code == 200
    portions_0 = res_0.json()["food_portions"]
    for item in ["idli", "dosa", "poori", "pongal", "sambar"]:
        assert portions_0[item]["buffer_percent"] == 0.0
        assert portions_0[item]["estimated_portions"] == portions_0[item]["base_portions"]
        assert portions_0[item]["buffer_amount"] == 0.0

    # 25% buffer
    res_25 = client.post(
        "/api/forecast",
        json={"forecast_date": target_date, "guests_included": 80, "guests_other": 30, "buffer_percent": 25.0},
    )
    assert res_25.status_code == 200
    portions_25 = res_25.json()["food_portions"]
    for item in ["idli", "dosa", "poori", "pongal", "sambar"]:
        assert portions_25[item]["buffer_percent"] == 25.0
        assert portions_25[item]["estimated_portions"] >= portions_25[item]["base_portions"]


def test_honest_synthetic_metrics_labelling(client, seeded_history):
    """Verify honest synthetic training data labeling across comparative models."""
    target_date = (date.today() + timedelta(days=7)).isoformat()
    res = client.post(
        "/api/forecast",
        json={"forecast_date": target_date, "guests_included": 90, "guests_other": 30},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["synthetic_training_data"] is True
    for m in data["model_comparison"]:
        assert "synthetic" in m["data_source"].lower()


def test_forecast_excludes_anomalous_records_and_prevents_distortion(client):
    """Regression test: prove that an anomalous record like 2026-10-24 cannot distort the forecast."""
    client.post("/api/history/clear")
    target_date = (date.today() + timedelta(days=7)).isoformat()
    target_weekday = date.fromisoformat(target_date).weekday()

    # Find 3 past matching dates
    past_dates = []
    d = date.today() - timedelta(days=1)
    while len(past_dates) < 3:
        if d.weekday() == target_weekday:
            past_dates.append(d.isoformat())
        d -= timedelta(days=1)

    from app.database import get_db
    with get_db() as conn:
        # Day 1: Valid record (80 guests, 72 covers = 90% included)
        conn.execute(
            "INSERT INTO occupancy_records (date, expected_occupancy, guests_included, guests_other) VALUES (?, 110, 80, 30)",
            (past_dates[0],),
        )
        conn.execute(
            "INSERT INTO consumption_records (date, actual_consumption, covers_included, covers_other) VALUES (?, 93, 72, 21)",
            (past_dates[0],),
        )
        # Day 2: Valid record (90 guests, 81 covers = 90% included)
        conn.execute(
            "INSERT INTO occupancy_records (date, expected_occupancy, guests_included, guests_other) VALUES (?, 120, 90, 30)",
            (past_dates[1],),
        )
        conn.execute(
            "INSERT INTO consumption_records (date, actual_consumption, covers_included, covers_other) VALUES (?, 102, 81, 21)",
            (past_dates[1],),
        )
        # Day 3: Anomalous record like 2026-10-24 (11 guests, 95 covers!)
        conn.execute(
            "INSERT INTO occupancy_records (date, expected_occupancy, guests_included, guests_other) VALUES (?, 15, 11, 4)",
            (past_dates[2],),
        )
        conn.execute(
            "INSERT INTO consumption_records (date, actual_consumption, covers_included, covers_other) VALUES (?, 119, 95, 24)",
            (past_dates[2],),
        )

    res = client.post(
        "/api/forecast",
        json={
            "forecast_date": target_date,
            "guests_included": 90,
            "guests_other": 30,
            "event_expected_covers": 10,
        },
    )
    assert res.status_code == 200
    data = res.json()
    b = data["calculation_breakdown"]

    # 1. Anomalous date is excluded from calculation
    assert past_dates[2] in b["excluded_dates"]
    assert past_dates[2] not in b["historical_dates_used"]
    assert len(b["historical_dates_used"]) == 2
    assert past_dates[0] in b["historical_dates_used"]
    assert past_dates[1] in b["historical_dates_used"]

    # 2. Excluded detail explains why
    assert len(b["excluded_days_detail"]) == 1
    assert b["excluded_days_detail"][0]["date"] == past_dates[2]
    assert "exceed resident guests" in b["excluded_days_detail"][0]["reason"].lower()

    # 3. Calculation is purely from valid records and NOT distorted
    expected_sum_inc_guests = 80 + 90  # 170
    expected_sum_inc_covers = 72 + 81  # 153
    expected_rate_inc = expected_sum_inc_covers / expected_sum_inc_guests  # 0.90 (90%)
    assert b["capture_rate_included"] == 0.9
    assert b["capture_rate_included_percent"] == 90.0

    # 4. Resident covers and final forecast are protected from distortion
    expected_resident = (90 * 0.9) + (30 * 0.7)  # 81 + 21 = 102
    assert b["resident_covers"] == 102.0
    assert data["forecasted_breakfast_guests"] == 112  # 102 resident + 10 event

    # 5. Warning clearly explains the exclusion
    assert "Excluded from calculation" in data["warning"]
    assert past_dates[2] in data["warning"]


def test_forecast_insufficient_history_when_all_matching_records_are_anomalous(client):
    """Verify clear 400 error when all matching records are anomalous (cannot invent values)."""
    client.post("/api/history/clear")
    target_date = (date.today() + timedelta(days=7)).isoformat()
    target_weekday = date.fromisoformat(target_date).weekday()

    d = date.today() - timedelta(days=1)
    matching_date = None
    while not matching_date:
        if d.weekday() == target_weekday:
            matching_date = d.isoformat()
        d -= timedelta(days=1)

    from app.database import get_db
    with get_db() as conn:
        conn.execute(
            "INSERT INTO occupancy_records (date, expected_occupancy, guests_included, guests_other) VALUES (?, 15, 11, 4)",
            (matching_date,),
        )
        conn.execute(
            "INSERT INTO consumption_records (date, actual_consumption, covers_included, covers_other) VALUES (?, 119, 95, 24)",
            (matching_date,),
        )

    res = client.post(
        "/api/forecast",
        json={"forecast_date": target_date, "guests_included": 80, "guests_other": 30},
    )
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "No valid historical data exists" in detail
    assert "excluded due to invalid guest-to-cover relationships" in detail
    assert matching_date in detail


def test_forecast_original_database_records_remain_unchanged_after_forecast(client):
    """Verify that original records in database are completely preserved and untouched."""
    client.post("/api/history/clear")
    target_date = (date.today() + timedelta(days=7)).isoformat()
    target_weekday = date.fromisoformat(target_date).weekday()

    d = date.today() - timedelta(days=1)
    matching_date = None
    while not matching_date:
        if d.weekday() == target_weekday:
            matching_date = d.isoformat()
        d -= timedelta(days=1)

    from app.database import get_db
    with get_db() as conn:
        conn.execute(
            "INSERT INTO occupancy_records (date, expected_occupancy, guests_included, guests_other) VALUES (?, 15, 11, 4)",
            (matching_date,),
        )
        conn.execute(
            "INSERT INTO consumption_records (date, actual_consumption, covers_included, covers_other) VALUES (?, 119, 95, 24)",
            (matching_date,),
        )

    # Inspect records before
    with get_db() as conn:
        occ_before = dict(conn.execute("SELECT * FROM occupancy_records WHERE date = ?", (matching_date,)).fetchone())
        cons_before = dict(conn.execute("SELECT * FROM consumption_records WHERE date = ?", (matching_date,)).fetchone())

    # Execute forecast (fails with 400 because only invalid record exists)
    client.post("/api/forecast", json={"forecast_date": target_date, "guests_included": 80, "guests_other": 30})

    # Inspect records after
    with get_db() as conn:
        occ_after = dict(conn.execute("SELECT * FROM occupancy_records WHERE date = ?", (matching_date,)).fetchone())
        cons_after = dict(conn.execute("SELECT * FROM consumption_records WHERE date = ?", (matching_date,)).fetchone())

    assert occ_after == occ_before
    assert cons_after == cons_before
