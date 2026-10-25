from datetime import date, datetime
from math import isfinite
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
    expected_occupancy: Optional[int] = Field(None, ge=0, description="Number of expected resident guests (must be >= 0)", json_schema_extra={"example": 120})
    guests_included: Optional[int] = Field(None, ge=0, description="Guests with breakfast included in room rate")
    guests_other: Optional[int] = Field(None, ge=0, description="Guests without breakfast included (room only/walk-in)")
    event_expected_covers: Optional[int] = Field(0, ge=0, description="Event expected covers (non-resident diners)")
    total_rooms: Optional[int] = Field(None, ge=0, description="Optional total rooms booked/available", json_schema_extra={"example": 75})
    notes: Optional[str] = Field("", description="Optional notes or context (e.g. tour group, conference)", json_schema_extra={"example": "Corporate group checking in"})

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        return DateValidatorMixin.validate_iso_date(v)

    @field_validator("expected_occupancy")
    @classmethod
    def validate_occupancy(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Expected occupancy cannot be negative.")
        return v

    @field_validator("guests_included", "guests_other", "event_expected_covers")
    @classmethod
    def validate_non_negative_guest_counts(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Guest counts and event covers cannot be negative.")
        return v

    @field_validator("total_rooms")
    @classmethod
    def validate_total_rooms(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Total rooms cannot be negative.")
        return v

    @model_validator(mode="after")
    def resolve_occupancy_fields(self):
        if self.guests_included is not None and self.guests_other is not None:
            total = self.guests_included + self.guests_other
            if self.expected_occupancy is None:
                self.expected_occupancy = total
        elif self.expected_occupancy is not None:
            self.guests_included = int(round(self.expected_occupancy * 0.75))
            self.guests_other = self.expected_occupancy - self.guests_included
        else:
            raise ValueError("Either expected_occupancy or both guests_included and guests_other must be provided.")
        return self

class OccupancyUpdate(BaseModel):
    expected_occupancy: Optional[int] = Field(None, ge=0, description="Updated number of expected guests")
    guests_included: Optional[int] = Field(None, ge=0, description="Updated guests with breakfast included")
    guests_other: Optional[int] = Field(None, ge=0, description="Updated guests without breakfast included")
    event_expected_covers: Optional[int] = Field(None, ge=0, description="Updated event expected covers")
    total_rooms: Optional[int] = Field(None, ge=0, description="Updated total rooms")
    notes: Optional[str] = Field(None, description="Updated notes")

    @field_validator("expected_occupancy", "guests_included", "guests_other", "event_expected_covers")
    @classmethod
    def validate_occupancy(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Guest counts cannot be negative.")
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
    guests_included: Optional[int] = None
    guests_other: Optional[int] = None
    event_expected_covers: Optional[int] = 0
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
    requires_verification: bool = False
    verification_reason: Optional[str] = None

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

# ==========================================
# Epic 2 - Breakfast Demand Forecasting
# ==========================================
class CaptureRateHistoricalDay(BaseModel):
    date: str
    weekday_name: str
    guests_included: int
    covers_included: int
    capture_rate_included: float
    guests_other: int
    covers_other: int
    capture_rate_other: float
    event_covers: int = 0
    is_anomalous: bool = False
    anomaly_reason: Optional[str] = None


class ExcludedHistoricalDay(BaseModel):
    date: str
    weekday_name: str
    guests_included: Optional[int] = None
    covers_included: Optional[int] = None
    guests_other: Optional[int] = None
    covers_other: Optional[int] = None
    event_covers: Optional[int] = 0
    reason: str
    status: str = "Requires Verification"


class CaptureRateCalculationBreakdown(BaseModel):
    historical_dates_used: List[str]
    matching_weekdays_count: int
    matching_weekday_name: str
    warning: Optional[str] = None
    has_anomalous_rates: bool = False
    rate_warnings: List[str] = Field(default_factory=list)
    excluded_dates: List[str] = Field(default_factory=list)
    excluded_days_detail: List[ExcludedHistoricalDay] = Field(default_factory=list)
    historical_days_detail: List[CaptureRateHistoricalDay] = Field(default_factory=list)
    sum_guests_included: int
    sum_covers_included: int
    sum_guests_other: int
    sum_covers_other: int
    capture_rate_included: float
    capture_rate_included_percent: float
    capture_rate_other: float
    capture_rate_other_percent: float
    resident_covers: float
    total_resident_guests: int
    event_expected_covers: int
    final_forecast_covers: int


class ForecastRequest(BaseModel):
    forecast_date: str = Field(..., description="Breakfast service date in YYYY-MM-DD format")
    guests_included: Optional[int] = Field(None, ge=0, le=200, description="Guests with breakfast included in room rate")
    guests_other: Optional[int] = Field(None, ge=0, le=200, description="Guests without breakfast included (other)")
    event_expected_covers: int = Field(0, ge=0, le=200, description="Event-cover estimate (uplift added exactly once)")
    expected_occupancy: Optional[int] = Field(None, ge=50, le=200, description="Total expected resident guests (50 to 200)")
    total_resident_guests: Optional[int] = Field(None, ge=50, le=200, description="Total resident guests (Included + Without Breakfast)")
    group_event: bool = Field(False, description="Whether a group event is scheduled")
    is_holiday: bool = Field(False, description="Whether the service date is a holiday")
    group_booking_guests: int = Field(0, ge=0, description="Guests included in group bookings")
    special_event: bool = Field(False, description="Whether a special event may affect breakfast demand")
    portion_assumptions: dict[str, float] = Field(
        default_factory=dict,
        description="Optional servings per forecast cover for idli, dosa, pongal, poori, sambar, and bread",
    )
    buffer_percent: float = Field(10.0, ge=0.0, le=25.0, description="Preparation buffer percentage (0% to 25%)")

    @field_validator("forecast_date")
    @classmethod
    def validate_forecast_date(cls, value: str) -> str:
        valid_date = DateValidatorMixin.validate_iso_date(value)
        parsed_date = date.fromisoformat(valid_date)
        if parsed_date.isoformat() != valid_date:
            raise ValueError("Forecast date must use YYYY-MM-DD format.")
        if parsed_date <= date.today():
            raise ValueError("Forecast date must be in the future.")
        return valid_date

    @field_validator("guests_included", "guests_other", "event_expected_covers")
    @classmethod
    def validate_counts_non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Guest counts and event covers must be non-negative integers.")
        return v

    @field_validator("portion_assumptions")
    @classmethod
    def validate_portion_assumptions(cls, value: dict[str, float]) -> dict[str, float]:
        allowed_items = {"idli", "dosa", "pongal", "poori", "sambar", "bread"}
        for item, servings in value.items():
            if item not in allowed_items:
                raise ValueError(f"Unsupported food item '{item}'.")
            if not isfinite(servings) or servings < 0 or servings > 3:
                raise ValueError("Portion assumptions must be finite values between 0 and 3 servings per guest.")
        return value

    @model_validator(mode="after")
    def validate_guest_groups(self):
        # Resolve total resident guests from separate guest categories
        if self.guests_included is not None and self.guests_other is not None:
            self.total_resident_guests = self.guests_included + self.guests_other
            self.expected_occupancy = self.total_resident_guests
        elif self.expected_occupancy is not None:
            self.total_resident_guests = self.expected_occupancy
            self.guests_included = int(round(self.expected_occupancy * 0.75))
            self.guests_other = self.expected_occupancy - self.guests_included
        else:
            raise ValueError("Both guests_included and guests_other must be provided.")

        if self.guests_included < 0 or self.guests_other < 0:
            raise ValueError("Guest counts must be non-negative integers.")

        if self.event_expected_covers < 0:
            raise ValueError("Event expected covers must be a non-negative integer.")

        # Total resident guests hotel capacity validation: 50 to 200 guests
        if self.total_resident_guests < 50 or self.total_resident_guests > 200:
            raise ValueError("Total resident guests (Included + Without Breakfast) must be between 50 and 200.")

        # Group booking guests must not exceed total resident guests, and are not a substitute for guest categories
        if self.group_booking_guests < 0:
            raise ValueError("Group booking guests must be a non-negative integer.")
        if self.group_booking_guests > self.total_resident_guests:
            raise ValueError("Group booking guests cannot exceed total resident guests.")

        return self


class ForecastModelResult(BaseModel):
    model: str
    predicted_guests: int
    mae: float
    rmse: float
    data_source: str = "Synthetic demonstration dataset (not verified hotel history)"


class FoodPortionEstimate(BaseModel):
    servings_per_guest: float
    estimated_portions: float
    base_portions: float
    buffer_percent: float
    buffer_amount: Optional[float] = None
    unit: str
    increment: Optional[float] = None


class ForecastResponse(BaseModel):
    forecast_date: str
    expected_occupancy: int
    total_resident_guests: int
    guests_included: int
    guests_other: int
    event_expected_covers: int
    forecasted_breakfast_guests: int
    selected_model: str
    synthetic_training_data: bool
    training_days: int
    evaluation_days: int
    evaluation_start_date: str
    evaluation_end_date: str
    model_comparison: List[ForecastModelResult]
    food_portions: dict[str, FoodPortionEstimate]
    calculation_breakdown: Optional[CaptureRateCalculationBreakdown] = None
    warning: Optional[str] = None


# ==========================================
# User Account & Registration Models
# ==========================================
import re

class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    username: str = Field(..., min_length=3, max_length=30, description="Unique username")
    email: str = Field(..., max_length=150, description="Unique email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (at least 8 characters)")
    confirm_password: str = Field(..., description="Confirmation matching the password")

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Full name must be at least 2 characters.")
        return cleaned

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        cleaned = v.strip()
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", cleaned):
            raise ValueError("Username must be 3-30 characters long and contain only letters, numbers, and underscores.")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        # Standard email regex pattern
        email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_pattern, cleaned):
            raise ValueError(f"'{v}' is not a valid email address.")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class UserResponse(BaseModel):
    id: int
    full_name: str
    username: str
    email: str
    created_at: str


# ==========================================
# Epic 3 - Dish-wise Records, Waste & Accuracy
# ==========================================
SUPPORTED_DISHES = ["idli", "dosa", "poori", "pongal", "sambar"]
DISH_UNITS = {
    "idli": "pieces",
    "dosa": "pieces",
    "poori": "pieces",
    "pongal": "kg",
    "sambar": "litres",
}
DISH_DISPLAY_NAMES = {
    "idli": "Idli",
    "dosa": "Dosa",
    "poori": "Poori",
    "pongal": "Pongal",
    "sambar": "Sambar",
}


class DishRecordCreate(BaseModel):
    date: str = Field(..., description="Service date in YYYY-MM-DD format")
    dish: str = Field(..., description="Dish name (idli, dosa, poori, pongal, or sambar)")
    quantity_prepared: float = Field(..., ge=0, description="Quantity prepared (>= 0)")
    quantity_consumed: float = Field(..., ge=0, description="Quantity consumed (>= 0)")
    quantity_discarded: float = Field(..., ge=0, description="Quantity discarded as waste (>= 0)")
    stock_out: bool = Field(False, description="Whether the dish ran out of stock during service")
    notes: Optional[str] = Field("", description="Optional notes or remarks")

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        valid_iso = DateValidatorMixin.validate_iso_date(v)
        parsed_date = date.fromisoformat(valid_iso)
        if parsed_date > date.today():
            raise ValueError(
                f"Dish service record cannot be entered for a future date (maximum allowed date: {date.today().isoformat()})."
            )
        return valid_iso

    @field_validator("dish")
    @classmethod
    def validate_dish(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if v_clean not in SUPPORTED_DISHES:
            raise ValueError(f"Unsupported dish '{v}'. Supported dishes are: {', '.join(SUPPORTED_DISHES)}.")
        return v_clean

    @field_validator("quantity_prepared", "quantity_consumed", "quantity_discarded")
    @classmethod
    def validate_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Quantities cannot be negative.")
        return v

    @model_validator(mode="after")
    def validate_sensible_quantities(self):
        if (self.quantity_consumed + self.quantity_discarded) > (self.quantity_prepared + 1e-4):
            raise ValueError(
                f"Sum of consumed ({self.quantity_consumed}) and discarded ({self.quantity_discarded}) "
                f"cannot exceed prepared quantity ({self.quantity_prepared})."
            )
        return self


class DishRecordUpdate(BaseModel):
    quantity_prepared: Optional[float] = Field(None, ge=0)
    quantity_consumed: Optional[float] = Field(None, ge=0)
    quantity_discarded: Optional[float] = Field(None, ge=0)
    stock_out: Optional[bool] = None
    notes: Optional[str] = None

    @field_validator("quantity_prepared", "quantity_consumed", "quantity_discarded")
    @classmethod
    def validate_non_negative(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Quantities cannot be negative.")
        return v


class DishRecordResponse(BaseModel):
    id: int
    date: str
    dish: str
    unit: str
    quantity_prepared: float
    quantity_consumed: float
    quantity_discarded: float
    stock_out: bool
    notes: Optional[str] = ""
    created_at: str
    updated_at: str
    data_provenance: str = "Synthetic Demonstration Entry (Unverified — Demo Data Only)"
    is_synthetic: bool = True


class DayAccuracyEvaluation(BaseModel):
    date: str
    weekday: str
    actual_covers: Optional[int] = None
    predicted_covers: Optional[int] = None
    absolute_error: Optional[int] = None
    absolute_percentage_error: Optional[float] = None
    eligible: bool
    ineligibility_reason: Optional[str] = None
    stock_out_occurred: bool = False


class ForecastAccuracyResponse(BaseModel):
    evaluation_days_count: int
    eligible_days_count: int
    excluded_stockout_days: int
    zero_actual_days_excluded: int
    mape: Optional[float] = None
    evaluations: List[DayAccuracyEvaluation]
    status_message: str
    notice: str = "SYNTHETIC DEMO DATA — NOT REAL HOTEL DATA"


class DishWasteSummary(BaseModel):
    dish: str
    unit: str
    days_recorded: int
    total_prepared: float
    total_consumed: float
    total_discarded: float
    waste_percentage: Optional[float] = None
    stock_out_days: int
    simulated_waste: Optional[float] = None
    simulated_shortage: Optional[float] = None
    simulation_status: str
    data_provenance: str = "Synthetic Demonstration Dataset (Unverified — Not Real Hotel Data)"
    is_synthetic: bool = True


class WasteAnalysisResponse(BaseModel):
    dish_summaries: List[DishWasteSummary]
    notice: str = "SYNTHETIC DEMO DATA — NOT REAL HOTEL DATA"
    notes: str = (
        "Recorded waste metrics reflect synthetic demonstration entries and are unverified; "
        "they must not be used to claim real-world hotel waste reduction or operational benchmarks. "
        "Simulated metrics model performance under a 10% buffered demand forecast. Dish units are kept strictly separate."
    )


