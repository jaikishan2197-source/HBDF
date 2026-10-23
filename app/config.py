import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "breakfastwise.db"

DATABASE_PATH = os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH))

def get_database_path() -> str:
    db_path = Path(DATABASE_PATH)
    if not db_path.parent.exists() and db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path)
