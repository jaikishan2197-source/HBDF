from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import occupancy, consumption, history

STATIC_DIR = Path(__file__).resolve().parent / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield

app = FastAPI(
    title="BreakfastWise - Hotel Breakfast Demand Forecasting",
    description="Hotel Breakfast Demand Forecasting application. Epic 1: Hotel Data Management.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom validation exception handler for clear error messages
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_messages = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        # Clean up pydantic internal prefixes
        if msg.startswith("Value error, "):
            msg = msg.replace("Value error, ", "")
        error_messages.append(f"{loc}: {msg}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": error_messages[0] if len(error_messages) == 1 else error_messages,
            "all_errors": error_messages
        }
    )

# Include Routers
app.include_router(occupancy.router)
app.include_router(consumption.router)
app.include_router(history.router)

# Mount Static Files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "BreakfastWise",
        "epic": "Epic 1: Hotel Data Management",
        "version": "1.0.0"
    }

@app.get("/", include_in_schema=False)
def index_page():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "BreakfastWise API is running. Static files are not yet created."}
