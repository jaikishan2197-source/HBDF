import os
import tempfile
import warnings
import pytest

# Suppress harmless StarletteDeprecationWarning about httpx with testclient
warnings.filterwarnings("ignore", message=".*Using `httpx` with `starlette.testclient`.*")

from starlette.testclient import TestClient

# Create a temporary database path before importing app modules
temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
os.close(temp_db_fd)
os.environ["DATABASE_PATH"] = temp_db_path

from app.database import init_db
from app.main import app

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db(temp_db_path)
    yield
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except OSError:
            pass

@pytest.fixture
def client():
    # Clear tables before each test to ensure test isolation
    from app.database import get_db
    with get_db(temp_db_path) as conn:
        conn.execute("DELETE FROM occupancy_records;")
        conn.execute("DELETE FROM consumption_records;")
    
    with TestClient(app) as test_client:
        yield test_client
