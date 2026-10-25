from datetime import date, timedelta
import pytest
from app.models import SUPPORTED_DISHES, DISH_UNITS


def test_save_dish_record_success(client):
    """Test saving a new dish daily service record."""
    target_date = (date.today() - timedelta(days=1)).isoformat()
    payload = {
        "date": target_date,
        "dish": "idli",
        "quantity_prepared": 150.0,
        "quantity_consumed": 135.0,
        "quantity_discarded": 10.0,
        "stock_out": False,
        "notes": "Standard breakfast service",
    }
    response = client.post("/api/dishes/records", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["date"] == target_date
    assert data["dish"] == "idli"
    assert data["unit"] == "pieces"
    assert data["quantity_prepared"] == 150.0
    assert data["quantity_consumed"] == 135.0
    assert data["quantity_discarded"] == 10.0
    assert data["stock_out"] is False

    # Retrieve single record
    get_res = client.get(f"/api/dishes/records/{target_date}/idli")
    assert get_res.status_code == 200
    assert get_res.json()["quantity_consumed"] == 135.0


def test_update_dish_record_success(client):
    """Test updating and correcting a dish record safely."""
    target_date = (date.today() - timedelta(days=2)).isoformat()
    # Create initial record
    client.post(
        "/api/dishes/records",
        json={
            "date": target_date,
            "dish": "pongal",
            "quantity_prepared": 12.0,
            "quantity_consumed": 10.5,
            "quantity_discarded": 1.2,
            "stock_out": False,
            "notes": "Initial log",
        },
    )

    # Correct discarded waste and notes
    update_res = client.put(
        f"/api/dishes/records/{target_date}/pongal",
        json={"quantity_discarded": 1.0, "notes": "Audited discarded weight"},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["quantity_discarded"] == 1.0
    assert updated_data["quantity_prepared"] == 12.0
    assert updated_data["unit"] == "kg"
    assert updated_data["notes"] == "Audited discarded weight"


def test_dish_record_rejects_invalid_quantities_and_unsupported_dish(client):
    """Validate non-negative quantities and sensible relationships."""
    target_date = (date.today() - timedelta(days=1)).isoformat()

    # Consumed + discarded exceeds prepared
    res1 = client.post(
        "/api/dishes/records",
        json={
            "date": target_date,
            "dish": "dosa",
            "quantity_prepared": 50.0,
            "quantity_consumed": 45.0,
            "quantity_discarded": 15.0,  # 45 + 15 = 60 > 50
        },
    )
    assert res1.status_code == 422
    assert "cannot exceed prepared quantity" in str(res1.json())

    # Negative quantity
    res2 = client.post(
        "/api/dishes/records",
        json={
            "date": target_date,
            "dish": "poori",
            "quantity_prepared": -10.0,
            "quantity_consumed": 0.0,
            "quantity_discarded": 0.0,
        },
    )
    assert res2.status_code == 422

    # Unsupported dish
    res3 = client.post(
        "/api/dishes/records",
        json={
            "date": target_date,
            "dish": "waffles",
            "quantity_prepared": 20.0,
            "quantity_consumed": 18.0,
            "quantity_discarded": 2.0,
        },
    )
    assert res3.status_code == 422
    assert "Unsupported dish" in str(res3.json())

    # Future date rejected
    future_date = (date.today() + timedelta(days=2)).isoformat()
    res4 = client.post(
        "/api/dishes/records",
        json={
            "date": future_date,
            "dish": "sambar",
            "quantity_prepared": 20.0,
            "quantity_consumed": 18.0,
            "quantity_discarded": 2.0,
        },
    )
    assert res4.status_code == 422
    assert "future date" in str(res4.json())


def test_dish_record_missing_required_values(client):
    """Ensure missing values are not silently assumed zero."""
    target_date = (date.today() - timedelta(days=1)).isoformat()
    res = client.post(
        "/api/dishes/records",
        json={
            "date": target_date,
            "dish": "idli",
            "quantity_prepared": 100.0,
            # quantity_consumed and quantity_discarded omitted
        },
    )
    assert res.status_code == 422


def test_stock_out_handling_excludes_from_accuracy_evaluation(client):
    """
    Test that dishes with stock_out=True are recorded and the day is
    excluded from forecast accuracy true-demand evaluation.
    """
    test_date = (date.today() - timedelta(days=3)).isoformat()

    # Record occupancy and consumption
    client.post(
        "/api/occupancy",
        json={
            "date": test_date,
            "guests_included": 90,
            "guests_other": 30,
            "event_expected_covers": 0,
        },
    )
    client.post(
        "/api/consumption",
        json={"date": test_date, "actual_consumption": 105},
    )

    # Record dish with stock-out
    client.post(
        "/api/dishes/records",
        json={
            "date": test_date,
            "dish": "dosa",
            "quantity_prepared": 40.0,
            "quantity_consumed": 40.0,
            "quantity_discarded": 0.0,
            "stock_out": True,
            "notes": "Ran out of batter early",
        },
    )

    acc_res = client.get("/api/accuracy?days=7")
    assert acc_res.status_code == 200
    acc_data = acc_res.json()
    eval_item = next((e for e in acc_data["evaluations"] if e["date"] == test_date), None)
    assert eval_item is not None
    assert eval_item["stock_out_occurred"] is True
    assert eval_item["eligible"] is False
    assert "Stock-out occurred" in eval_item["ineligibility_reason"]


def test_forecast_evaluation_without_future_data_leakage(client):
    """
    Verify that accuracy evaluation for a historical date T only uses
    data strictly prior to T (preventing future data leakage).
    """
    # Create 3 successive Mondays
    base_monday = date(2026, 10, 5)  # A Monday
    mon1 = (base_monday - timedelta(days=14)).isoformat()
    mon2 = (base_monday - timedelta(days=7)).isoformat()
    mon3 = base_monday.isoformat()

    for d, occ, cons in [
        (mon1, (80, 20), 85),
        (mon2, (85, 25), 90),
        (mon3, (90, 30), 100),
    ]:
        client.post(
            "/api/occupancy",
            json={
                "date": d,
                "guests_included": occ[0],
                "guests_other": occ[1],
                "event_expected_covers": 0,
            },
        )
        client.post(
            "/api/consumption",
            json={"date": d, "actual_consumption": cons},
        )

    res = client.get("/api/accuracy?days=30")
    assert res.status_code == 200
    data = res.json()

    # For mon1: No prior Mondays exist in DB -> Ineligible
    eval_mon1 = next((e for e in data["evaluations"] if e["date"] == mon1), None)
    assert eval_mon1 is not None
    assert eval_mon1["eligible"] is False
    assert "Insufficient matching weekday history" in eval_mon1["ineligibility_reason"]

    # For mon2: Strictly uses mon1
    eval_mon2 = next((e for e in data["evaluations"] if e["date"] == mon2), None)
    assert eval_mon2 is not None
    assert eval_mon2["eligible"] is True
    assert eval_mon2["predicted_covers"] is not None

    # For mon3: Strictly uses mon1 and mon2 (never anything future)
    eval_mon3 = next((e for e in data["evaluations"] if e["date"] == mon3), None)
    assert eval_mon3 is not None
    assert eval_mon3["eligible"] is True


def test_zero_actual_day_mape_handling(client):
    """
    Zero-actual days must be excluded from the MAPE denominator and reported.
    """
    # Seed history first
    client.post("/api/history/seed?days=21")

    # Force a zero-actual day on an eligible date
    zero_date = (date.today() - timedelta(days=3)).isoformat()
    client.post(
        "/api/consumption",
        json={"date": zero_date, "actual_consumption": 0},
    )

    res = client.get("/api/accuracy?days=14")
    assert res.status_code == 200
    data = res.json()
    assert data["zero_actual_days_excluded"] >= 1

    zero_eval = next((e for e in data["evaluations"] if e["date"] == zero_date), None)
    assert zero_eval is not None
    assert zero_eval["eligible"] is False
    assert zero_eval["absolute_percentage_error"] is None
    assert "excluded from MAPE denominator" in zero_eval["ineligibility_reason"]


def test_per_dish_waste_calculations_and_units(client):
    """
    Verify dish waste percentages, units (pieces, kg, litres), and
    clear separation of recorded waste vs simulated outcomes.
    """
    client.post("/api/history/seed?days=14")

    res = client.get("/api/waste/analysis")
    assert res.status_code == 200
    data = res.json()
    assert data["notice"] == "SYNTHETIC DEMO DATA — NOT REAL HOTEL DATA"

    summaries = {d["dish"].lower(): d for d in data["dish_summaries"]}
    for dish in SUPPORTED_DISHES:
        assert dish in summaries
        s = summaries[dish]
        assert s["unit"] == DISH_UNITS[dish]
        assert s["total_prepared"] >= s["total_consumed"]
        if s["total_prepared"] > 0:
            expected_pct = round((s["total_discarded"] / s["total_prepared"]) * 100, 1)
            assert s["waste_percentage"] == expected_pct
        assert s["simulation_status"] in ["simulated", "insufficient_inputs"]


def test_empty_and_insufficient_historical_data(client):
    """Verify empty database returns clean explanations rather than fabricating metrics."""
    client.post("/api/history/clear")

    acc_res = client.get("/api/accuracy")
    assert acc_res.status_code == 200
    acc_data = acc_res.json()
    assert acc_data["evaluation_days_count"] == 0
    assert acc_data["eligible_days_count"] == 0
    assert acc_data["mape"] is None
    assert "Insufficient eligible historical service days" in acc_data["status_message"]

    waste_res = client.get("/api/waste/analysis")
    assert waste_res.status_code == 200
    waste_data = waste_res.json()
    for s in waste_data["dish_summaries"]:
        assert s["days_recorded"] == 0
        assert s["waste_percentage"] is None
        assert s["simulated_waste"] is None
        assert s["simulation_status"] == "insufficient_inputs"


def test_delete_dish_record(client):
    """Test deleting a dish record."""
    target_date = (date.today() - timedelta(days=1)).isoformat()
    client.post(
        "/api/dishes/records",
        json={
            "date": target_date,
            "dish": "poori",
            "quantity_prepared": 60.0,
            "quantity_consumed": 55.0,
            "quantity_discarded": 5.0,
        },
    )

    del_res = client.delete(f"/api/dishes/records/{target_date}/poori")
    assert del_res.status_code == 200

    get_res = client.get(f"/api/dishes/records/{target_date}/poori")
    assert get_res.status_code == 404
