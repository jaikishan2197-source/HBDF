from fastapi import APIRouter, HTTPException, Query, status, Response
from typing import List, Optional
from app.database import get_db
from app.models import DishRecordCreate, DishRecordUpdate, DishRecordResponse, SUPPORTED_DISHES
from app import crud

router = APIRouter(prefix="/api/dishes", tags=["Epic 3 - Dish-wise Daily Records"])


@router.post("/records", response_model=DishRecordResponse)
def record_daily_dish_consumption(payload: DishRecordCreate, response: Response):
    """
    Record or update a daily dish service log (prepared, consumed, discarded, stock-out).
    Validates non-negative quantities and sensible relationships (consumed + discarded <= prepared).
    """
    with get_db() as conn:
        record, is_created = crud.upsert_dish_record(conn, payload)
        response.status_code = status.HTTP_201_CREATED if is_created else status.HTTP_200_OK
        return DishRecordResponse(**record)


@router.get("/records", response_model=List[DishRecordResponse])
def list_dish_records(
    dish: Optional[str] = Query(None, description="Filter by dish (idli, dosa, poori, pongal, sambar)"),
    date: Optional[str] = Query(None, description="Filter by exact service date (YYYY-MM-DD)"),
    start_date: Optional[str] = Query(None, description="Filter from start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter to end date (YYYY-MM-DD)")
):
    """Retrieve dish-wise service records with optional date and dish filters."""
    with get_db() as conn:
        records = crud.get_dish_records(
            conn,
            dish=dish,
            target_date=date,
            start_date=start_date,
            end_date=end_date
        )
        return [DishRecordResponse(**r) for r in records]


@router.get("/records/{target_date}/{dish}", response_model=DishRecordResponse)
def get_single_dish_record(target_date: str, dish: str):
    """Retrieve a specific daily dish record by date and dish name."""
    with get_db() as conn:
        record = crud.get_dish_record_single(conn, target_date, dish)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dish record for '{dish}' on '{target_date}' not found."
            )
        return DishRecordResponse(**record)


@router.put("/records/{target_date}/{dish}", response_model=DishRecordResponse)
def update_daily_dish_record(target_date: str, dish: str, payload: DishRecordUpdate):
    """
    Update an existing dish record safely.
    Validates that consumed + discarded does not exceed prepared quantity.
    """
    with get_db() as conn:
        record = crud.update_dish_record(conn, target_date, dish, payload)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dish record for '{dish}' on '{target_date}' not found."
            )
        return DishRecordResponse(**record)


@router.delete("/records/{target_date}/{dish}")
def delete_daily_dish_record(target_date: str, dish: str):
    """Delete a daily dish record."""
    with get_db() as conn:
        deleted = crud.delete_dish_record(conn, target_date, dish)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dish record for '{dish}' on '{target_date}' not found."
            )
        return {"success": True, "message": f"Dish record for '{dish}' on '{target_date}' deleted successfully."}
