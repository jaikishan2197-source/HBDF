from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional
from app.database import get_db
from app.models import HistoryListResponse, HistorySummaryStats, ApiResponse
from app import crud

router = APIRouter(prefix="/api/history", tags=["Epic 1 - Story 3: Historical Records & KPIs"])

@router.get("", response_model=HistoryListResponse)
def get_historical_data(
    start_date: Optional[str] = Query(None, description="Filter from start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter to end date (YYYY-MM-DD)"),
    sort_asc: bool = Query(False, description="Sort ascending by date (default false = newest first)")
):
    """
    Story 3: View historical occupancy and consumption records.
    - Merges occupancy and breakfast consumption by date.
    - Calculates breakfast take-up rate (%) and variance.
    - Provides aggregate summary statistics.
    """
    with get_db() as conn:
        records, summary = crud.get_historical_records(
            conn,
            start_date=start_date,
            end_date=end_date,
            sort_asc=sort_asc
        )
        return HistoryListResponse(
            records=records,
            summary=summary,
            total_count=len(records)
        )

@router.get("/stats", response_model=HistorySummaryStats)
def get_historical_summary_stats():
    """Retrieve high-level summary KPIs across all historical records."""
    with get_db() as conn:
        _, summary = crud.get_historical_records(conn)
        return summary

@router.delete("/{target_date}")
def delete_historical_entry_by_date(target_date: str):
    """Delete all records (occupancy and consumption) for a given date."""
    with get_db() as conn:
        deleted = crud.delete_history_date(conn, target_date)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No records found for date '{target_date}'."
            )
        return {"success": True, "message": f"Historical entries for '{target_date}' removed."}

@router.post("/seed", response_model=ApiResponse)
def seed_sample_records(days: int = Query(14, ge=1, le=60)):
    """Seed sample hotel occupancy & consumption data for testing and evaluation."""
    with get_db() as conn:
        seeded = crud.seed_sample_hotel_data(conn, days=days)
        return ApiResponse(
            success=True,
            message=f"Successfully seeded {seeded} days of realistic hotel breakfast and occupancy data."
        )

@router.post("/clear", response_model=ApiResponse)
def clear_records():
    """Clear all records from database (useful for testing empty state)."""
    with get_db() as conn:
        crud.clear_all_history(conn)
        return ApiResponse(
            success=True,
            message="All historical records cleared. Database is now in empty state."
        )
