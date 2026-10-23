from datetime import date, timedelta
import pytest

def test_record_breakfast_consumption_valid(client):
    """Story 2: Record valid breakfast consumption for a date."""
    past_date = (date.today() - timedelta(days=1)).isoformat()
    payload = {
        "date": past_date,
        "actual_consumption": 110,
        "actual_occupancy": 120,
        "notes": "Full continental and hot buffet"
    }
    response = client.post("/api/consumption", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["date"] == past_date
    assert data["actual_consumption"] == 110
    assert data["actual_occupancy"] == 120
    assert data["notes"] == "Full continental and hot buffet"
    assert "id" in data

def test_record_consumption_zero_allowed(client):
    """Story 2: Zero breakfast consumption is allowed (e.g., dining room closed)."""
    past_date = (date.today() - timedelta(days=2)).isoformat()
    payload = {
        "date": past_date,
        "actual_consumption": 0,
        "notes": "Kitchen maintenance day"
    }
    response = client.post("/api/consumption", json=payload)
    assert response.status_code == 201
    assert response.json()["actual_consumption"] == 0

def test_reject_future_date_consumption(client):
    """Story 2: Reject actual consumption recorded for future dates."""
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    next_month = (date.today() + timedelta(days=30)).isoformat()

    for future_d in [tomorrow, next_month]:
        payload = {
            "date": future_d,
            "actual_consumption": 85
        }
        response = client.post("/api/consumption", json=payload)
        assert response.status_code == 422, f"Expected 422 for future date {future_d}"
        detail_str = str(response.json()["detail"]).lower()
        assert "future date" in detail_str

def test_accept_today_and_past_consumption(client):
    """Story 2: Accept today's date and past dates for breakfast consumption."""
    today_str = date.today().isoformat()
    res_today = client.post("/api/consumption", json={
        "date": today_str,
        "actual_consumption": 75
    })
    assert res_today.status_code == 201
    assert res_today.json()["actual_consumption"] == 75

def test_reject_decimal_consumption(client):
    """Story 2: Reject decimal breakfast meals count without truncation."""
    past_date = (date.today() - timedelta(days=3)).isoformat()
    payload = {
        "date": past_date,
        "actual_consumption": 85.5
    }
    response = client.post("/api/consumption", json=payload)
    assert response.status_code == 422
    detail_str = str(response.json()["detail"]).lower()
    assert "fractional part" in detail_str or "valid integer" in detail_str

def test_reject_negative_breakfast_consumption(client):
    """Story 2: Reject negative breakfast meals count."""
    past_date = (date.today() - timedelta(days=1)).isoformat()
    payload = {
        "date": past_date,
        "actual_consumption": -5
    }
    response = client.post("/api/consumption", json=payload)
    assert response.status_code == 422
    detail_str = str(response.json()["detail"]).lower()
    assert "cannot be negative" in detail_str or "greater than or equal to 0" in detail_str

def test_reject_negative_actual_occupancy(client):
    """Story 2: Reject negative actual occupancy count."""
    past_date = (date.today() - timedelta(days=1)).isoformat()
    payload = {
        "date": past_date,
        "actual_consumption": 50,
        "actual_occupancy": -2
    }
    response = client.post("/api/consumption", json=payload)
    assert response.status_code == 422
    detail_str = str(response.json()["detail"]).lower()
    assert "cannot be negative" in detail_str or "greater than or equal to 0" in detail_str

def test_reject_invalid_date_in_consumption(client):
    """Story 2: Reject invalid dates."""
    payload = {
        "date": "invalid-date-format",
        "actual_consumption": 80
    }
    response = client.post("/api/consumption", json=payload)
    assert response.status_code == 422

def test_consumption_upsert_existing_date(client):
    """Story 2: Updating consumption for existing date returns 200 OK and preserves fields."""
    target_d = (date.today() - timedelta(days=4)).isoformat()
    payload1 = {
        "date": target_d,
        "actual_consumption": 95,
        "actual_occupancy": 110,
        "notes": "Preliminary head count"
    }
    res1 = client.post("/api/consumption", json=payload1)
    assert res1.status_code == 201
    first_id = res1.json()["id"]

    # Final register reconciliation - actual_occupancy omitted, should be preserved!
    payload2 = {
        "date": target_d,
        "actual_consumption": 98
    }
    res2 = client.post("/api/consumption", json=payload2)
    assert res2.status_code == 200
    updated_data = res2.json()
    assert updated_data["id"] == first_id
    assert updated_data["actual_consumption"] == 98
    assert updated_data["actual_occupancy"] == 110  # Preserved!
    assert updated_data["notes"] == "Preliminary head count"  # Preserved!

def test_get_consumption_by_date(client):
    """Story 2: Retrieve consumption record by date."""
    target_d = (date.today() - timedelta(days=5)).isoformat()
    client.post("/api/consumption", json={"date": target_d, "actual_consumption": 62})
    res = client.get(f"/api/consumption/{target_d}")
    assert res.status_code == 200
    assert res.json()["actual_consumption"] == 62

def test_delete_consumption(client):
    """Story 2: Delete consumption record."""
    target_d = (date.today() - timedelta(days=6)).isoformat()
    client.post("/api/consumption", json={"date": target_d, "actual_consumption": 70})
    del_res = client.delete(f"/api/consumption/{target_d}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    get_res = client.get(f"/api/consumption/{target_d}")
    assert get_res.status_code == 404
