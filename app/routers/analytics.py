from fastapi import APIRouter, Query
from app.database import get_db
from app.models import ForecastAccuracyResponse, WasteAnalysisResponse
from app import crud

router = APIRouter(prefix="/api", tags=["Epic 3 - Forecast Accuracy & Waste Analysis"])


@router.get("/accuracy", response_model=ForecastAccuracyResponse)
def get_forecast_accuracy(
    days: int = Query(14, ge=1, le=60, description="Number of latest service days to evaluate (up to 14 recommended)")
):
    """
    Historical forecast accuracy evaluation for the latest eligible service days.
    - Evaluates each day using strictly information available by 9 PM on previous day (leakage-free).
    - Excludes stock-out days from true-demand evaluation when actual demand was censored.
    - Calculates MAPE, excluding zero-actual days from denominator.
    - Displays notice: SYNTHETIC DEMO DATA — NOT REAL HOTEL DATA.
    """
    with get_db() as conn:
        return crud.get_forecast_accuracy_evaluation(conn, days=days)


@router.get("/waste/analysis", response_model=WasteAnalysisResponse)
def get_waste_and_shortage_analysis():
    """
    Dish-wise waste and shortage analysis.
    - Reports recorded waste quantity, waste percentage, and stock-out days per dish.
    - Reports simulated waste and shortage where enough valid simulation inputs exist.
    - Keeps dish units separate (pieces, kg, litres) and clearly labels simulated metrics.
    """
    with get_db() as conn:
        return crud.get_waste_and_shortage_analysis(conn)
