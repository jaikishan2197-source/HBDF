# BreakfastWise 🍳
> **Hotel Breakfast-Demand Forecasting Web Application**  
> Built for hotel F&B leaders, kitchen managers, and front-desk staff to eliminate food waste and ensure optimal breakfast preparation.

---

## Current Status: Epic 1 — Hotel Data Management

BreakfastWise is structured around four epics:
1. **Epic 1: Hotel Data Management** (*Complete & Traceable*) — Stories 1–3
2. **Epic 2: Breakfast Demand Forecasting** — Stories 4–6 (*Next*)
3. **Epic 3: Forecast Dashboard** — Stories 7–9 (*Planned*)
4. **Epic 4: Food Preparation Planning** — Stories 10–12 (*Planned*)

---

## Epic 1 Feature Matrix & Traceability

| Story | User Need | Implementation Component | API Route | Validation & Edge Case Rules |
| :--- | :--- | :--- | :--- | :--- |
| **Story 1** | Enter expected occupancy for a selected date | Form 1 & Table (`app/static/index.html`, `app/routers/occupancy.py`, `app/crud.py`) | `POST /api/occupancy`<br>`GET /api/occupancy`<br>`GET /api/occupancy/{date}`<br>`DELETE /api/occupancy/{id}` | • Calendar date validation (`YYYY-MM-DD`). Rejects invalid dates (e.g. Feb 31).<br>• Expected occupancy must be non-negative integer ($\ge 0$).<br>• Total rooms booked/available $\ge 0$.<br>• Upsert: updates existing entry for date without duplicating. |
| **Story 2** | Record previous breakfast consumption | Form 2 & Table (`app/static/index.html`, `app/routers/consumption.py`, `app/crud.py`) | `POST /api/consumption`<br>`GET /api/consumption`<br>`GET /api/consumption/{date}`<br>`DELETE /api/consumption/{id}` | • Valid ISO calendar date.<br>• Actual consumption must be non-negative integer ($\ge 0$). Zero allowed (e.g. maintenance closure).<br>• Verified occupancy $\ge 0$.<br>• Upsert: updating actual count replaces record seamlessly. |
| **Story 3** | View historical data, take-up rates, & KPIs | Interactive Table, KPI Cards & Empty State (`app/routers/history.py`, `app/crud.py`, `app/static/js/app.js`) | `GET /api/history`<br>`GET /api/history/stats`<br>`POST /api/history/seed`<br>`POST /api/history/clear`<br>`DELETE /api/history/{date}` | • Merges occupancy & consumption chronologically.<br>• Computes **Take-up Rate (%)** $\frac{\text{Actual}}{\text{Expected}} \times 100$ and **Variance** ($\text{Expected} - \text{Actual}$).<br>• Status badges: `Complete`, `Occupancy Only`, `Consumption Only`.<br>• **Empty state handling**: Friendly empty container with 1-click sample data loader.<br>• Date filters: *All Time*, *Last 7 Days*, *Last 14 Days*, *Last 30 Days*, and Custom Range. |

---

## Tech Stack & Architecture

- **Backend**: Python 3.15, FastAPI, Pydantic v2 (strict request validation, clean schemas, OpenAPI docs at `/docs`).
- **Database**: SQLite3 persistent storage with WAL mode, foreign key constraints, and automatic schema initialization.
- **Frontend**: Clean single-page interface served directly by FastAPI (HTML5, responsive CSS design system, asynchronous vanilla JavaScript with toast notifications, empty states, and modals).
- **Testing**: `pytest` test suite with 25 test cases covering happy paths, negative boundaries, calendar edge cases, and empty states.

---

## Project Structure

```text
HBDF/
├── app/
│   ├── __init__.py
│   ├── config.py              # Database path and environment configuration
│   ├── database.py            # SQLite connection, WAL mode, schema DDL
│   ├── models.py              # Pydantic validation models for Stories 1, 2, and 3
│   ├── crud.py                # Database queries, upsert operations, and KPI aggregations
│   ├── main.py                # FastAPI app entrypoint, CORS, custom validation error handler
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── occupancy.py       # Story 1 API endpoints
│   │   ├── consumption.py     # Story 2 API endpoints
│   │   └── history.py         # Story 3 historical merging, filtering, & KPI endpoints
│   └── static/
│       ├── index.html         # Responsive web application UI
│       ├── css/
│       │   └── styles.css     # Clean CSS design system with toasts, badges, and empty states
│       └── js/
│           └── app.js         # Frontend controller, form handlers, and reactive table renderer
├── data/
│   └── breakfastwise.db       # Persistent SQLite database file
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Pytest test database fixture & TestClient setup
│   ├── test_occupancy.py      # Story 1 unit & API test cases
│   ├── test_consumption.py    # Story 2 unit & API test cases
│   └── test_history.py        # Story 3 unit & API test cases
├── requirements.txt           # Python package dependencies
├── LICENSE                    # MIT License
└── README.md                  # Documentation and user manual
```

---

## Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Web Application
```bash
python -m uvicorn app.main:app --reload --port 8000
```
Open your browser and navigate to:
- **Application UI**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Run Automated Tests
```bash
python -m pytest -v
```
All 25 automated tests will execute and validate:
- Valid occupancy and consumption logging
- Negative values rejection (`ge=0`)
- Invalid date rejection (e.g. `2026-02-31`)
- Data upserts on existing dates
- Historical records merging, take-up rate calculation, variance computation
- Empty state behavior and seed/clear operations
