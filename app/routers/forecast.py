from fastapi import APIRouter

from app.forecasting import create_forecast
from app.models import ForecastRequest, ForecastResponse

router = APIRouter(prefix="/api/forecast", tags=["Epic 2 - Breakfast Demand Forecasting"])


@router.post("", response_model=ForecastResponse)
def forecast_breakfast_demand(payload: ForecastRequest):
    """Forecast breakfast covers and portions using labelled synthetic training data."""
    return create_forecast(payload)