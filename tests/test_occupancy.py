import pytest

def test_enter_expected_occupancy_valid(client):
    """Story 1: Enter valid expected occupancy for a date."""
    payload = {
        "date": "2026-10-24",
        "expected_occupancy": 125,
        "total_rooms": 80,
        "notes": "Wedding group checking in"
    }
    response = client.post("/api/occupancy", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["date"] == "2026-10-24"
    assert data["expected_occupancy"] == 125
    assert data["total_rooms"] == 80
    assert data["notes"] == "Wedding group checking in"
    assert "id" in data
    assert "created_at" in data

def test_enter_expected_occupancy_zero_allowed(client):
    """Story 1: Zero expected occupancy is valid (e.g. hotel closed for maintenance)."""
    payload = {
        "date": "2026-10-25",
        "expected_occupancy": 0,
        "notes": "Hotel closed for maintenance"
    }
    response = client.post("/api/occupancy", json=payload)
    assert response.status_code == 201
    assert response.json()["expected_occupancy"] == 0

def test_reject_negative_expected_occupancy(client):
    """Story 1: Reject negative expected occupancy count."""
    payload = {
        "date": "2026-10-24",
        "expected_occupancy": -15
    }
    response = client.post("/api/occupancy", json=payload)
    assert response.status_code == 422
    data = response.json()
    detail_str = str(data["detail"]).lower()
    assert "cannot be negative" in detail_str or "greater than or equal to 0" in detail_str

def test_reject_negative_total_rooms(client):
    """Story 1: Reject negative total rooms."""
    payload = {
        "date": "2026-10-24",
        "expected_occupancy": 50,
        "total_rooms": -10
    }
    response = client.post("/api/occupancy", json=payload)
    assert response.status_code == 422
    detail_str = str(response.json()["detail"]).lower()
    assert "cannot be negative" in detail_str or "greater than or equal to 0" in detail_str

def test_reject_invalid_date_format(client):
    """Story 1: Reject non-ISO date formats."""
    invalid_dates = ["24-10-2026", "2026/10/24", "yesterday", "invalid-str"]
    for bad_date in invalid_dates:
        payload = {
            "date": bad_date,
            "expected_occupancy": 100
        }
        response = client.post("/api/occupancy", json=payload)
        assert response.status_code == 422, f"Expected 422 for bad date: {bad_date}"

def test_reject_impossible_calendar_date(client):
    """Story 1: Reject impossible dates like Feb 31."""
    payload = {
        "date": "2026-02-31",
        "expected_occupancy": 100
    }
    response = client.post("/api/occupancy", json=payload)
    assert response.status_code == 422
    detail_str = str(response.json()["detail"]).lower()
    assert "not a valid calendar date" in detail_str

def test_occupancy_upsert_existing_date(client):
    """Story 1: Re-submitting for same date updates rather than duplicating, returning 200 OK and preserving fields."""
    payload1 = {
        "date": "2026-11-01",
        "expected_occupancy": 90,
        "total_rooms": 60,
        "notes": "Initial estimate"
    }
    res1 = client.post("/api/occupancy", json=payload1)
    assert res1.status_code == 201
    first_id = res1.json()["id"]

    # Updated estimate - total_rooms omitted, should be preserved!
    payload2 = {
        "date": "2026-11-01",
        "expected_occupancy": 115
    }
    res2 = client.post("/api/occupancy", json=payload2)
    assert res2.status_code == 200
    updated_data = res2.json()
    assert updated_data["id"] == first_id
    assert updated_data["expected_occupancy"] == 115
    assert updated_data["total_rooms"] == 60  # Preserved!
    assert updated_data["notes"] == "Initial estimate"  # Preserved!

    # Verify only 1 record exists
    list_res = client.get("/api/occupancy")
    assert len(list_res.json()) == 1

def test_reject_decimal_expected_occupancy(client):
    """Story 1: Reject decimal values without silent truncation."""
    payload = {
        "date": "2026-11-02",
        "expected_occupancy": 120.5
    }
    response = client.post("/api/occupancy", json=payload)
    assert response.status_code == 422
    data = response.json()
    detail_str = str(data["detail"]).lower()
    assert "fractional part" in detail_str or "valid integer" in detail_str

def test_reject_decimal_total_rooms(client):
    """Story 1: Reject decimal total rooms."""
    payload = {
        "date": "2026-11-02",
        "expected_occupancy": 100,
        "total_rooms": 50.7
    }
    response = client.post("/api/occupancy", json=payload)
    assert response.status_code == 422
    detail_str = str(response.json()["detail"]).lower()
    assert "fractional part" in detail_str or "valid integer" in detail_str

def test_put_occupancy_partial_update(client):
    """Story 1: PUT endpoint updates only specified fields."""
    client.post("/api/occupancy", json={
        "date": "2026-11-03",
        "expected_occupancy": 80,
        "total_rooms": 50,
        "notes": "Original note"
    })

    # Update only expected_occupancy
    put_res = client.put("/api/occupancy/2026-11-03", json={"expected_occupancy": 95})
    assert put_res.status_code == 200
    data = put_res.json()
    assert data["expected_occupancy"] == 95
    assert data["total_rooms"] == 50  # Preserved
    assert data["notes"] == "Original note"  # Preserved

def test_get_occupancy_by_date(client):
    """Story 1: Retrieve occupancy entry by date."""
    client.post("/api/occupancy", json={"date": "2026-10-28", "expected_occupancy": 75})
    res = client.get("/api/occupancy/2026-10-28")
    assert res.status_code == 200
    assert res.json()["expected_occupancy"] == 75

def test_get_occupancy_not_found(client):
    """Story 1: 404 when date not found."""
    res = client.get("/api/occupancy/2099-01-01")
    assert res.status_code == 404

def test_delete_occupancy(client):
    """Story 1: Delete occupancy entry."""
    client.post("/api/occupancy", json={"date": "2026-10-29", "expected_occupancy": 85})
    del_res = client.delete("/api/occupancy/2026-10-29")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify deleted
    get_res = client.get("/api/occupancy/2026-10-29")
    assert get_res.status_code == 404


def test_enter_expected_occupancy_with_separate_guest_groups(client):
    """Story 1: Enter expected occupancy using separate guest groups and event covers."""
    payload = {
        "date": "2026-11-20",
        "guests_included": 90,
        "guests_other": 30,
        "event_expected_covers": 15,
        "total_rooms": 75,
        "notes": "Corporate conference"
    }
    response = client.post("/api/occupancy", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["date"] == "2026-11-20"
    assert data["expected_occupancy"] == 120  # Sum of resident guest groups
    assert data["guests_included"] == 90
    assert data["guests_other"] == 30
    assert data["event_expected_covers"] == 15
    assert data["total_rooms"] == 75
