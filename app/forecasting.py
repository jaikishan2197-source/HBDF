import random
from datetime import date, timedelta
from functools import lru_cache
from math import ceil, cos, pi, sin, sqrt
from typing import Any, Optional

from fastapi import HTTPException, status
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from app.database import get_db
from app.models import (
    CaptureRateCalculationBreakdown,
    CaptureRateHistoricalDay,
    ExcludedHistoricalDay,
    FoodPortionEstimate,
    ForecastModelResult,
    ForecastRequest,
    ForecastResponse,
)

TRAINING_START = date(2023, 1, 1)
TRAINING_END = date(2025, 12, 31)
TRAINING_DAYS = (TRAINING_END - TRAINING_START).days + 1

DEFAULT_PORTION_ASSUMPTIONS = {
    "idli": 1.2,
    "dosa": 0.35,
    "poori": 0.3,
    "pongal": 0.35,
    "sambar": 0.4,
}

ITEM_UNITS = {
    "idli": "pieces",
    "dosa": "pieces",
    "poori": "pieces",
    "pongal": "kg",
    "sambar": "litres",
    "bread": "pieces",
}

ITEM_INCREMENTS = {
    "idli": 1.0,
    "dosa": 1.0,
    "poori": 1.0,
    "pongal": 0.1,
    "sambar": 0.5,
    "bread": 1.0,
}

WEEKDAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _round_up_increment(val: float, increment: float) -> float:
    """
    Round UP recommendations to the appropriate quantity increments:
    - 1 piece for idli, dosa, poori, bread (increment 1.0)
    - 0.1 kg for pongal (increment 0.1)
    - 0.5 litres for sambar (increment 0.5)
    """
    if increment <= 0:
        return val
    steps = ceil(round(val / increment, 9) - 1e-9)
    result = steps * increment
    if increment == 1.0:
        return float(int(result))
    elif increment == 0.1:
        return round(result, 1)
    elif increment == 0.5:
        return round(result, 1)
    return round(result, 2)


def _feature_vector(
    service_date: date,
    occupancy: int,
    is_holiday: bool,
    group_booking_guests: int,
    special_event: bool,
) -> list[float]:
    weekday_angle = 2 * pi * service_date.weekday() / 7
    month_angle = 2 * pi * (service_date.month - 1) / 12
    return [
        float(occupancy),
        sin(weekday_angle),
        cos(weekday_angle),
        float(is_holiday),
        float(group_booking_guests),
        float(special_event),
        sin(month_angle),
        cos(month_angle),
    ]


def _synthetic_training_rows() -> tuple[list[list[float]], list[int]]:
    """Generate labelled demo data locally; no synthetic rows are persisted."""
    generator = random.Random(20261023)
    features: list[list[float]] = []
    targets: list[int] = []

    for day_offset in range(TRAINING_DAYS):
        service_date = TRAINING_START + timedelta(days=day_offset)
        weekend = service_date.weekday() in (4, 5, 6)
        occupancy = generator.randint(75, 155) if weekend else generator.randint(50, 135)
        occupancy = min(200, occupancy + generator.randint(0, 25) if weekend else occupancy)
        is_holiday = generator.random() < 0.08
        special_event = generator.random() < 0.07
        group_booking_guests = (
            generator.randint(1, max(1, int(occupancy * 0.35)))
            if generator.random() < 0.28
            else 0
        )

        seasonal_rate = 0.025 * sin(2 * pi * (service_date.month - 1) / 12)
        take_up_rate = (
            0.78
            + (0.035 if weekend else 0)
            + (0.07 if is_holiday else 0)
            + (0.04 if special_event else 0)
            + 0.08 * group_booking_guests / occupancy
            + seasonal_rate
            + generator.gauss(0, 0.045)
        )
        take_up_rate = min(1.05, max(0.5, take_up_rate))

        features.append(
            _feature_vector(
                service_date,
                occupancy,
                is_holiday,
                group_booking_guests,
                special_event,
            )
        )
        targets.append(round(occupancy * take_up_rate))

    return features, targets


@lru_cache(maxsize=1)
def _trained_models() -> dict[str, Any]:
    features, targets = _synthetic_training_rows()
    split_index = int(len(features) * 0.8)
    train_features = features[:split_index]
    train_targets = targets[:split_index]
    test_features = features[split_index:]
    test_targets = targets[split_index:]

    baseline_prediction = sum(train_targets) / len(train_targets)
    baseline_predictions = [baseline_prediction] * len(test_targets)
    evaluated: dict[str, Any] = {
        "Historical Average": {
            "model": None,
            "baseline_prediction": baseline_prediction,
            "mae": mean_absolute_error(test_targets, baseline_predictions),
            "rmse": sqrt(mean_squared_error(test_targets, baseline_predictions)),
        }
    }

    estimators = {
        "Random Forest Regressor": RandomForestRegressor(
            n_estimators=120,
            min_samples_leaf=3,
            max_features=0.9,
            random_state=42,
            n_jobs=1,
        ),
        "Gradient Boosting Regressor": GradientBoostingRegressor(
            n_estimators=120,
            learning_rate=0.04,
            max_depth=2,
            loss="squared_error",
            random_state=42,
        ),
    }

    for name, estimator in estimators.items():
        estimator.fit(train_features, train_targets)
        predictions = estimator.predict(test_features)
        evaluated[name] = {
            "model": estimator,
            "mae": mean_absolute_error(test_targets, predictions),
            "rmse": sqrt(mean_squared_error(test_targets, predictions)),
        }

    return {
        "models": evaluated,
        "training_days": split_index,
        "evaluation_days": len(test_targets),
        "evaluation_start_date": (TRAINING_START + timedelta(days=split_index)).isoformat(),
        "evaluation_end_date": TRAINING_END.isoformat(),
    }


def _predict(model_info: dict[str, Any], features: list[float]) -> float:
    estimator = model_info["model"]
    if estimator is None:
        return model_info["baseline_prediction"]
    return float(estimator.predict([features])[0])


def create_forecast(request: ForecastRequest, db_path: Optional[str] = None) -> ForecastResponse:
    forecast_date = date.fromisoformat(request.forecast_date)
    target_weekday = forecast_date.weekday()
    weekday_name = WEEKDAY_NAMES[target_weekday]

    # 1. Fetch eligible historical records strictly before forecast_date
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                o.date,
                o.expected_occupancy,
                o.guests_included,
                o.guests_other,
                o.event_expected_covers,
                c.actual_consumption,
                c.covers_included,
                c.covers_other,
                c.event_covers
            FROM occupancy_records o
            JOIN consumption_records c ON o.date = c.date
            WHERE o.date < ?
            ORDER BY o.date DESC
            """,
            (request.forecast_date,),
        )
        rows = cursor.fetchall()

    # 2. Filter all matching weekdays strictly before forecast_date
    all_matching_rows = [
        dict(r)
        for r in rows
        if date.fromisoformat(r["date"]).weekday() == target_weekday
    ]

    # 3. Validate resident guest-to-cover relationships and separate eligible from invalid records
    eligible_matching_rows = []
    excluded_dates = []
    excluded_detail: list[ExcludedHistoricalDay] = []

    for r in all_matching_rows:
        g_inc = r.get("guests_included")
        c_inc = r.get("covers_included")
        g_oth = r.get("guests_other")
        c_oth = r.get("covers_other")
        e_cov = r.get("event_covers") or 0

        # Check for missing required split fields
        if g_inc is None or c_inc is None or g_oth is None or c_oth is None:
            reasons = ["Required guest-group data is missing"]
            excluded_dates.append(r["date"])
            excluded_detail.append(
                ExcludedHistoricalDay(
                    date=r["date"],
                    weekday_name=weekday_name,
                    guests_included=g_inc,
                    covers_included=c_inc,
                    guests_other=g_oth,
                    covers_other=c_oth,
                    event_covers=e_cov,
                    reason="; ".join(reasons),
                    status="Requires Verification",
                )
            )
            continue

        # Check for invalid guest-to-cover relationships
        reasons = []
        if g_inc < 0 or c_inc < 0 or g_oth < 0 or c_oth < 0:
            reasons.append("Negative guest or cover counts")
        if c_inc > g_inc:
            reasons.append(f"Included breakfast covers ({c_inc}) exceed resident guests with included breakfast ({g_inc})")
        if c_oth > g_oth:
            reasons.append(f"Other breakfast covers ({c_oth}) exceed resident guests without included breakfast ({g_oth})")
        if g_inc == 0 and c_inc > 0:
            reasons.append(f"Included covers ({c_inc}) recorded with 0 included guests")
        if g_oth == 0 and c_oth > 0:
            reasons.append(f"Other covers ({c_oth}) recorded with 0 other guests")

        if reasons:
            excluded_dates.append(r["date"])
            excluded_detail.append(
                ExcludedHistoricalDay(
                    date=r["date"],
                    weekday_name=weekday_name,
                    guests_included=g_inc,
                    covers_included=c_inc,
                    guests_other=g_oth,
                    covers_other=c_oth,
                    event_covers=e_cov,
                    reason="; ".join(reasons),
                    status="Requires Verification",
                )
            )
        else:
            eligible_matching_rows.append(r)

    # 4. Take up to the 4 most recent eligible matching weekdays for operational calculation
    matching_rows = eligible_matching_rows[:4]

    # 5. Handle data sufficiency and fallback rules
    if not matching_rows:
        if excluded_detail:
            ex_summary = "; ".join(f"{d.date}: {d.reason}" for d in excluded_detail)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No valid historical data exists for matching weekday ({weekday_name}) before {request.forecast_date}. Available matching record(s) were excluded due to invalid guest-to-cover relationships ({ex_summary}) [marked as requiring verification].",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No eligible historical data exists for matching weekday ({weekday_name}) before {request.forecast_date}.",
        )

    # 6. Compute pooled sums and validate denominators on eligible rows
    sum_guests_included = sum(r["guests_included"] for r in matching_rows)
    sum_covers_included = sum(r["covers_included"] for r in matching_rows)
    sum_guests_other = sum(r["guests_other"] for r in matching_rows)
    sum_covers_other = sum(r["covers_other"] for r in matching_rows)

    if sum_guests_included <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Historical included-breakfast guest count is zero across eligible matching days; capture rate cannot be calculated.",
        )

    if sum_guests_other <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Historical other guest count is zero across eligible matching days; capture rate cannot be calculated.",
        )

    # 7. Calculate pooled capture rates from eligible historical rows
    r_i = sum_covers_included / sum_guests_included
    r_o = sum_covers_other / sum_guests_other

    # 8. Calculate resident covers from tomorrow's guest counts and capture rates
    req_guests_included = request.guests_included if request.guests_included is not None else 0
    req_guests_other = request.guests_other if request.guests_other is not None else 0
    total_resident_guests = req_guests_included + req_guests_other
    resident_covers = (req_guests_included * r_i) + (req_guests_other * r_o)

    # 9. Add event uplift exactly once and round final forecast to whole number
    final_forecast_covers = int(round(resident_covers + request.event_expected_covers))

    # 10. Build warning notices (explain excluded dates and warn if < 4 eligible days)
    warning_parts = []
    if len(matching_rows) < 4:
        dates_str = ", ".join(r["date"] for r in matching_rows)
        warning_parts.append(
            f"Fewer than 4 matching weekdays available in history before {request.forecast_date} "
            f"({len(matching_rows)} eligible {weekday_name}(s) used: {dates_str}). 4 matching weekdays recommended for full confidence."
        )

    if excluded_detail:
        ex_reasons = "; ".join(f"{d.date}: {d.reason}" for d in excluded_detail)
        warning_parts.append(
            f"Excluded from calculation: {len(excluded_detail)} matching date(s) excluded due to invalid guest-to-cover relationships ({ex_reasons}) [marked as requiring verification]."
        )

    combined_warning = " | ".join(warning_parts) if warning_parts else None

    # 11. Build historical days detail for transparency
    days_detail = [
        CaptureRateHistoricalDay(
            date=r["date"],
            weekday_name=weekday_name,
            guests_included=r["guests_included"],
            covers_included=r["covers_included"],
            capture_rate_included=round((r["covers_included"] / r["guests_included"] * 100), 1)
            if r["guests_included"] > 0
            else 0.0,
            guests_other=r["guests_other"],
            covers_other=r["covers_other"],
            capture_rate_other=round((r["covers_other"] / r["guests_other"] * 100), 1)
            if r["guests_other"] > 0
            else 0.0,
            event_covers=r.get("event_covers") or 0,
            is_anomalous=False,
            anomaly_reason=None,
        )
        for r in matching_rows
    ]

    breakdown = CaptureRateCalculationBreakdown(
        historical_dates_used=[r["date"] for r in matching_rows],
        matching_weekdays_count=len(matching_rows),
        matching_weekday_name=weekday_name,
        warning=combined_warning,
        has_anomalous_rates=bool(excluded_detail),
        rate_warnings=[f"Excluded {d.date}: {d.reason}" for d in excluded_detail],
        excluded_dates=excluded_dates,
        excluded_days_detail=excluded_detail,
        historical_days_detail=days_detail,
        sum_guests_included=sum_guests_included,
        sum_covers_included=sum_covers_included,
        sum_guests_other=sum_guests_other,
        sum_covers_other=sum_covers_other,
        capture_rate_included=round(r_i, 4),
        capture_rate_included_percent=round(r_i * 100, 1),
        capture_rate_other=round(r_o, 4),
        capture_rate_other_percent=round(r_o * 100, 1),
        resident_covers=round(resident_covers, 1),
        total_resident_guests=total_resident_guests,
        event_expected_covers=request.event_expected_covers,
        final_forecast_covers=final_forecast_covers,
    )

    # 10. Run comparative ML models for evaluation benchmarking
    features = _feature_vector(
        forecast_date,
        total_resident_guests,
        request.is_holiday,
        request.group_booking_guests,
        request.special_event,
    )
    trained = _trained_models()
    model_comparison: list[ForecastModelResult] = []

    for name, model_info in trained["models"].items():
        pred = min(
            total_resident_guests,
            max(0.0, _predict(model_info, features)),
        )
        model_comparison.append(
            ForecastModelResult(
                model=name,
                predicted_guests=int(round(pred)),
                mae=round(model_info["mae"], 2),
                rmse=round(model_info["rmse"], 2),
                data_source="Synthetic demonstration dataset (not verified hotel history)",
            )
        )

    # 11. Calculate food preparation quantities with buffer and increment rounding
    assumptions = {**DEFAULT_PORTION_ASSUMPTIONS, **request.portion_assumptions}
    food_portions: dict[str, FoodPortionEstimate] = {}

    for item, servings in assumptions.items():
        base_qty = final_forecast_covers * servings
        buf_mult = 1.0 + (request.buffer_percent / 100.0)
        buffered_qty = base_qty * buf_mult
        unit = ITEM_UNITS.get(item, "pieces")
        inc = ITEM_INCREMENTS.get(item, 1.0)

        base_portion_val = _round_up_increment(base_qty, inc)
        final_portion_val = _round_up_increment(buffered_qty, inc)
        buffer_diff = round(final_portion_val - base_portion_val, 2)
        if inc == 1.0:
            buffer_diff = float(int(buffer_diff))

        food_portions[item] = FoodPortionEstimate(
            servings_per_guest=round(servings, 2),
            estimated_portions=final_portion_val,
            base_portions=base_portion_val,
            buffer_percent=request.buffer_percent,
            buffer_amount=buffer_diff,
            unit=unit,
            increment=inc,
        )

    return ForecastResponse(
        forecast_date=request.forecast_date,
        expected_occupancy=total_resident_guests,
        total_resident_guests=total_resident_guests,
        guests_included=req_guests_included,
        guests_other=req_guests_other,
        event_expected_covers=request.event_expected_covers,
        forecasted_breakfast_guests=final_forecast_covers,
        selected_model="Two-Rate Capture Rate",
        synthetic_training_data=True,
        training_days=trained["training_days"],
        evaluation_days=trained["evaluation_days"],
        evaluation_start_date=trained["evaluation_start_date"],
        evaluation_end_date=trained["evaluation_end_date"],
        model_comparison=model_comparison,
        food_portions=food_portions,
        calculation_breakdown=breakdown,
        warning=combined_warning,
    )
