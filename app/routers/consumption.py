from fastapi import APIRouter, HTTPException, Query, status, Response
from typing import List
from app.database import get_db
from app.models import ConsumptionCreate, ConsumptionUpdate, ConsumptionResponse
from app import crud

router = APIRouter(prefix="/api/consumption", tags=["Epic 1 - Story 2: Breakfast Consumption"])

@router.post("", response_model=ConsumptionResponse)
def record_breakfast_consumption(payload: ConsumptionCreate, response: Response):
    """
    Story 2: Record previous breakfast consumption.
    - Validates date format and non-negative meal consumption.
    - Creates (201 Created) or updates (200 OK) the consumption record.
    """
    with get_db() as conn:
        record, is_created = crud.upsert_consumption(conn, payload)
        response.status_code = status.HTTP_201_CREATED if is_created else status.HTTP_200_OK
        return ConsumptionResponse(**record)

@router.put("/{target_identifier}", response_model=ConsumptionResponse)
def update_breakfast_consumption(target_identifier: str, payload: ConsumptionUpdate):
    """
    Story 2: Update specific fields of a breakfast consumption record by ID or Date.
    - Preserves unmentioned fields (e.g. actual_occupancy or notes).
    """
    with get_db() as conn:
        record = crud.update_consumption_partial(conn, target_identifier, payload)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Consumption record '{target_identifier}' not found."
            )
        return ConsumptionResponse(**record)

@router.get("", response_model=List[ConsumptionResponse])
def list_consumption_records(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Retrieve all recorded breakfast consumption entries."""
    with get_db() as conn:
        records = crud.get_all_consumption(conn, limit=limit, offset=offset)
        return [ConsumptionResponse(**r) for r in records]

@router.get("/{target_date}", response_model=ConsumptionResponse)
def get_consumption_by_date(target_date: str):
    """Retrieve breakfast consumption record for a specific date (YYYY-MM-DD)."""
    with get_db() as conn:
        record = crud.get_consumption_by_date(conn, target_date)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No breakfast consumption record found for date '{target_date}'."
            )
        return ConsumptionResponse(**record)

@router.delete("/{target_identifier}")
def delete_consumption_record(target_identifier: str):
    """Delete a breakfast consumption record by ID or Date."""
    with get_db() as conn:
        deleted = crud.delete_consumption(conn, target_identifier)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Consumption record '{target_identifier}' not found."
            )
        return {"success": True, "message": f"Consumption record '{target_identifier}' deleted successfully."}
