from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator

class DateValidatorMixin:
    @staticmethod
    def validate_iso_date(value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Date must be a string in YYYY-MM-DD format.")
        value = value.strip()
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            raise ValueError(f"'{value}' is not a valid calendar date. Expected YYYY-MM-DD format.")
        # Sanity check year range (e.g. 2000 to 2100)
        if parsed.year < 2000 or parsed.year > 2100:
            raise ValueError("Date year must be between 2000 and 2100.")
        return value

# ==========================================
# Epic 1 - Story 1: Expected Occupancy Models
# ==========================================
class OccupancyCreate(BaseModel):
    date: str = Field(..., description="Date for expected occupancy in YYYY-MM-DD format", json_schema_extra={"example": "2026-10-24"})
    expected_occupancy: int = Field(..., ge=0, description="Number of expected guests (must be >= 0)", json_schema_extra={"example": 120})
    total_rooms: Optional[int] = Field(None, ge=0, description="Optional total rooms booked/available", json_schema_extra={"example": 75})
    notes: Optional[str] = Field("", description="Optional notes or context (e.g. tour group, conference)", json_schema_extra={"example": "Corporate group checking in"})

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        return DateValidatorMixin.validate_iso_date(v)

    @field_validator("expected_occupancy")
    @classmethod
    def validate_occupancy(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Expected occupancy cannot be negative.")
        return v

    @field_validator("total_rooms")
    @classmethod
    def validate_total_rooms(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Total rooms cannot be negative.")
        return v

class OccupancyUpdate(BaseModel):
    expected_occupancy: Optional[int] = Field(None, ge=0, description="Updated number of expected guests")
    total_rooms: Optional[int] = Field(None, ge=0, description="Updated total rooms")
    notes: Optional[str] = Field(None, description="Updated notes")

    @field_validator("expected_occupancy")
    @classmethod
    def validate_occupancy(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Expected occupancy cannot be negative.")
        return v

    @field_validator("total_rooms")
    @classmethod
    def validate_total_rooms(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Total rooms cannot be negative.")
        return v

class OccupancyResponse(BaseModel):
    id: int
    date: str
    expected_occupancy: int
    total_rooms: Optional[int] = None
    notes: Optional[str] = ""
    created_at: str
    updated_at: str

# ==========================================
# Epic 1 - Story 2: Breakfast Consumption Models
# ==========================================
class ConsumptionCreate(BaseModel):
    date: str = Field(..., description="Date of breakfast consumption in YYYY-MM-DD format", json_schema_extra={"example": "2026-10-23"})
    actual_consumption: int = Field(..., ge=0, description="Number of breakfast meals/guests served (must be >= 0)", json_schema_extra={"example": 105})
    actual_occupancy: Optional[int] = Field(None, ge=0, description="Optional verified guest occupancy", json_schema_extra={"example": 118})
    notes: Optional[str] = Field("", description="Optional operational notes (e.g. buffet wastage, early departures)", json_schema_extra={"example": "High continental breakfast demand"})

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        valid_iso = DateValidatorMixin.validate_iso_date(v)
        parsed_date = date.fromisoformat(valid_iso)
        current_service_date = date.today()
        if parsed_date > current_service_date:
            raise ValueError(
                f"Actual breakfast consumption cannot be recorded for a future date (maximum allowed date: {current_service_date.isoformat()})."
            )
        return valid_iso

    @field_validator("actual_consumption")
    @classmethod
    def validate_consumption(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Actual breakfast consumption cannot be negative.")
        return v

    @field_validator("actual_occupancy")
    @classmethod
    def validate_actual_occupancy(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Actual occupancy cannot be negative.")
        return v

class ConsumptionUpdate(BaseModel):
    actual_consumption: Optional[int] = Field(None, ge=0, description="Updated actual consumption count")
    actual_occupancy: Optional[int] = Field(None, ge=0, description="Updated actual occupancy")
    notes: Optional[str] = Field(None, description="Updated notes")

    @field_validator("actual_consumption")
    @classmethod
    def validate_consumption(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Actual breakfast consumption cannot be negative.")
        return v

    @field_validator("actual_occupancy")
    @classmethod
    def validate_actual_occupancy(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Actual occupancy cannot be negative.")
        return v

class ConsumptionResponse(BaseModel):
    id: int
    date: str
    actual_consumption: int
    actual_occupancy: Optional[int] = None
    notes: Optional[str] = ""
    created_at: str
    updated_at: str

# ==========================================
# Epic 1 - Story 3: Historical Records Models
# ==========================================
class HistoricalRecordItem(BaseModel):
    date: str
    expected_occupancy: Optional[int] = None
    actual_consumption: Optional[int] = None
    actual_occupancy: Optional[int] = None
    total_rooms: Optional[int] = None
    take_up_rate: Optional[float] = None
    variance: Optional[int] = None
    status: str
    occupancy_id: Optional[int] = None
    consumption_id: Optional[int] = None
    occupancy_notes: Optional[str] = None
    consumption_notes: Optional[str] = None

class HistorySummaryStats(BaseModel):
    total_records: int
    occupancy_logged_days: int
    consumption_logged_days: int
    matched_days: int
    avg_expected_occupancy: Optional[float] = None
    avg_actual_consumption: Optional[float] = None
    avg_take_up_rate: Optional[float] = Field(None, description="Aggregate take-up rate (%) across all matched dates: (total actual breakfast / total expected occupancy) * 100")
    min_date: Optional[str] = None
    max_date: Optional[str] = None

class HistoryListResponse(BaseModel):
    records: List[HistoricalRecordItem]
    summary: HistorySummaryStats
    total_count: int

# Generic Standard API Response wrapper
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
