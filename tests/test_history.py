import pytest

def test_history_empty_state(client):
    """Story 3: Empty state when no records exist."""
    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    assert data["records"] == []
    assert data["total_count"] == 0
    assert data["summary"]["total_records"] == 0
    assert data["summary"]["avg_expected_occupancy"] is None
    assert data["summary"]["avg_actual_consumption"] is None
    assert data["summary"]["avg_take_up_rate"] is None

def test_history_combined_records_and_takeup_rate(client):
    """Story 3: Combined historical records calculate take-up rate and variance."""
    target_date = "2026-10-21"
    
    # Enter occupancy: 100 expected guests
    client.post("/api/occupancy", json={
        "date": target_date,
        "expected_occupancy": 100,
        "notes": "Occupancy note"
    })
    
    # Enter consumption: 85 meals served
    client.post("/api/consumption", json={
        "date": target_date,
        "actual_consumption": 85,
        "notes": "Consumption note"
    })

    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data["records"]) == 1
    
    record = data["records"][0]
    assert record["date"] == target_date
    assert record["expected_occupancy"] == 100
    assert record["actual_consumption"] == 85
    # Take-up rate = (85 / 100) * 100 = 85.0%
    assert record["take_up_rate"] == 85.0
    # Variance = expected - actual = 100 - 85 = 15
    assert record["variance"] == 15
    assert record["status"] == "Complete"
    assert record["occupancy_notes"] == "Occupancy note"
    assert record["consumption_notes"] == "Consumption note"

def test_history_unmatched_statuses(client):
    """Story 3: Unmatched dates have appropriate status badges."""
    # Date 1: Occupancy only
    client.post("/api/occupancy", json={"date": "2026-10-22", "expected_occupancy": 90})
    # Date 2: Consumption only
    client.post("/api/consumption", json={"date": "2026-10-23", "actual_consumption": 70})

    response = client.get("/api/history", params={"sort_asc": True})
    assert response.status_code == 200
    records = response.json()["records"]
    assert len(records) == 2

    r1 = records[0]
    assert r1["date"] == "2026-10-22"
    assert r1["status"] == "Occupancy Only"
    assert r1["expected_occupancy"] == 90
    assert r1["actual_consumption"] is None
    assert r1["take_up_rate"] is None

    r2 = records[1]
    assert r2["date"] == "2026-10-23"
    assert r2["status"] == "Consumption Only"
    assert r2["expected_occupancy"] is None
    assert r2["actual_consumption"] == 70
    assert r2["take_up_rate"] is None

def test_history_date_filtering(client):
    """Story 3: Filtering by start_date and end_date."""
    dates = ["2026-10-10", "2026-10-15", "2026-10-20", "2026-10-25"]
    for d in dates:
        client.post("/api/occupancy", json={"date": d, "expected_occupancy": 80})

    # Filter 2026-10-14 to 2026-10-21 (should include 10-15 and 10-20)
    response = client.get("/api/history", params={
        "start_date": "2026-10-14",
        "end_date": "2026-10-21"
    })
    assert response.status_code == 200
    records = response.json()["records"]
    assert len(records) == 2
    assert [r["date"] for r in records] == ["2026-10-20", "2026-10-15"]

def test_history_summary_kpis(client):
    """Story 3: Summary KPIs endpoint calculates true aggregate take-up rate."""
    # Day 1: 100 occ, 80 cons (Daily: 80.0%)
    client.post("/api/occupancy", json={"date": "2026-10-01", "expected_occupancy": 100})
    client.post("/api/consumption", json={"date": "2026-10-01", "actual_consumption": 80})

    # Day 2: 200 occ, 180 cons (Daily: 90.0%)
    client.post("/api/occupancy", json={"date": "2026-10-02", "expected_occupancy": 200})
    client.post("/api/consumption", json={"date": "2026-10-02", "actual_consumption": 180})

    res = client.get("/api/history/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_records"] == 2
    assert stats["matched_days"] == 2
    assert stats["avg_expected_occupancy"] == 150.0  # (100 + 200) / 2
    assert stats["avg_actual_consumption"] == 130.0   # (80 + 180) / 2
    # True aggregate = (80 + 180) / (100 + 200) * 100 = 260 / 300 * 100 = 86.7%
    assert stats["avg_take_up_rate"] == 86.7

def test_aggregate_take_up_rate_unequal_occupancy_weights(client):
    """
    Story 3: Aggregate rate must correctly weight unequal occupancy.
    Day 1: 100 occ, 90 cons (90.0%)
    Day 2: 20 occ, 10 cons (50.0%)
    Simple average of daily % would be (90 + 50) / 2 = 70.0% (INCORRECT).
    True Aggregate = (90 + 10) / (100 + 20) * 100 = 100 / 120 * 100 = 83.3% (CORRECT).
    """
    client.post("/api/occupancy", json={"date": "2026-10-05", "expected_occupancy": 100})
    client.post("/api/consumption", json={"date": "2026-10-05", "actual_consumption": 90})

    client.post("/api/occupancy", json={"date": "2026-10-06", "expected_occupancy": 20})
    client.post("/api/consumption", json={"date": "2026-10-06", "actual_consumption": 10})

    res = client.get("/api/history/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["avg_take_up_rate"] == 83.3
    assert stats["avg_take_up_rate"] != 70.0

def test_aggregate_take_up_rate_ignores_unmatched_dates(client):
    """
    Story 3: Matched rate calculation must exclude days where only occupancy or only consumption is present.
    Missing consumption must NOT be treated as zero.
    """
    # Matched Day: 100 occ, 80 cons (80.0%)
    client.post("/api/occupancy", json={"date": "2026-10-07", "expected_occupancy": 100})
    client.post("/api/consumption", json={"date": "2026-10-07", "actual_consumption": 80})

    # Unmatched Day: Occupancy only (200 occ, no breakfast logged yet)
    client.post("/api/occupancy", json={"date": "2026-10-08", "expected_occupancy": 200})

    res = client.get("/api/history/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["matched_days"] == 1
    # Aggregate rate must be 80.0% (not 80 / 300 = 26.7%!)
    assert stats["avg_take_up_rate"] == 80.0

def test_aggregate_take_up_rate_zero_occupancy_safeguard(client):
    """Story 3: Zero occupancy does not cause division by zero."""
    client.post("/api/occupancy", json={"date": "2026-10-09", "expected_occupancy": 0})
    client.post("/api/consumption", json={"date": "2026-10-09", "actual_consumption": 0})

    res = client.get("/api/history/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["avg_take_up_rate"] == 0.0

def test_historical_edit_preserves_unrelated_fields(client):
    """
    Story 3: Editing one field of a record preserves other existing fields.
    Regression test for the audit finding.
    """
    test_d = "2026-10-15"
    # Create complete record with rooms, actual occupancy, and notes
    client.post("/api/occupancy", json={
        "date": test_d,
        "expected_occupancy": 120,
        "total_rooms": 75,
        "notes": "Original occupancy note"
    })
    client.post("/api/consumption", json={
        "date": test_d,
        "actual_consumption": 100,
        "actual_occupancy": 115,
        "notes": "Original consumption note"
    })

    # Now update only expected occupancy via POST upsert without sending total_rooms
    up_res = client.post("/api/occupancy", json={
        "date": test_d,
        "expected_occupancy": 130
    })
    assert up_res.status_code == 200
    up_occ = up_res.json()
    assert up_occ["expected_occupancy"] == 130
    assert up_occ["total_rooms"] == 75  # Preserved!
    assert up_occ["notes"] == "Original occupancy note"  # Preserved!

    # Check history view to verify consumption was also untouched
    h_res = client.get("/api/history")
    record = h_res.json()["records"][0]
    assert record["expected_occupancy"] == 130
    assert record["total_rooms"] == 75
    assert record["actual_consumption"] == 100
    assert record["actual_occupancy"] == 115
    assert record["occupancy_notes"] == "Original occupancy note"
    assert record["consumption_notes"] == "Original consumption note"
    assert record["status"] == "Complete"

def test_seed_sample_data_and_clear(client):
    """Story 3: Seeding sample hotel data and clearing all records."""
    # Initially empty
    res_empty = client.get("/api/history")
    assert res_empty.json()["total_count"] == 0

    # Seed 10 days
    seed_res = client.post("/api/history/seed?days=10")
    assert seed_res.status_code == 200
    assert seed_res.json()["success"] is True

    # Verify records populated
    res_seeded = client.get("/api/history")
    assert res_seeded.json()["total_count"] == 10

    # Clear all data
    clear_res = client.post("/api/history/clear")
    assert clear_res.status_code == 200
    assert clear_res.json()["success"] is True

    # Verify back to empty state
    res_after = client.get("/api/history")
    assert res_after.json()["total_count"] == 0

def test_delete_history_by_date(client):
    """Story 3: Deleting both occupancy and consumption for a target date."""
    d = "2026-10-30"
    client.post("/api/occupancy", json={"date": d, "expected_occupancy": 100})
    client.post("/api/consumption", json={"date": d, "actual_consumption": 90})

    del_res = client.delete(f"/api/history/{d}")
    assert del_res.status_code == 200

    # Verify both deleted
    assert client.get(f"/api/occupancy/{d}").status_code == 404
    assert client.get(f"/api/consumption/{d}").status_code == 404
