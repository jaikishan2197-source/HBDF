from fastapi import APIRouter, HTTPException, Query, status, Response
from typing import List, Optional
from app.database import get_db
from app.models import OccupancyCreate, OccupancyUpdate, OccupancyResponse
from app import crud

router = APIRouter(prefix="/api/occupancy", tags=["Epic 1 - Story 1: Expected Occupancy"])

@router.post("", response_model=OccupancyResponse)
def record_expected_occupancy(payload: OccupancyCreate, response: Response):
    """
    Story 1: Enter expected occupancy for a selected date.
    - Validates date format and non-negative guest count.
    - Creates (201 Created) or updates (200 OK) the expected occupancy record.
    """
    with get_db() as conn:
        record, is_created = crud.upsert_occupancy(conn, payload)
        response.status_code = status.HTTP_201_CREATED if is_created else status.HTTP_200_OK
        return OccupancyResponse(**record)

@router.put("/{target_identifier}", response_model=OccupancyResponse)
def update_expected_occupancy(target_identifier: str, payload: OccupancyUpdate):
    """
    Story 1: Update specific fields of an occupancy record by ID or Date.
    - Preserves unmentioned fields (e.g. total_rooms or notes).
    """
    with get_db() as conn:
        record = crud.update_occupancy_partial(conn, target_identifier, payload)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Occupancy record '{target_identifier}' not found."
            )
        return OccupancyResponse(**record)

@router.get("", response_model=List[OccupancyResponse])
def list_occupancy_records(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Retrieve all expected occupancy records."""
    with get_db() as conn:
        records = crud.get_all_occupancy(conn, limit=limit, offset=offset)
        return [OccupancyResponse(**r) for r in records]

@router.get("/{target_date}", response_model=OccupancyResponse)
def get_occupancy_by_date(target_date: str):
    """Retrieve expected occupancy record for a specific date (YYYY-MM-DD)."""
    with get_db() as conn:
        record = crud.get_occupancy_by_date(conn, target_date)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No occupancy record found for date '{target_date}'."
            )
        return OccupancyResponse(**record)

@router.delete("/{target_identifier}")
def delete_occupancy_record(target_identifier: str):
    """Delete an occupancy record by ID or Date."""
    with get_db() as conn:
        deleted = crud.delete_occupancy(conn, target_identifier)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Occupancy record '{target_identifier}' not found."
            )
        return {"success": True, "message": f"Occupancy record '{target_identifier}' deleted successfully."}
