import pytest
from app.auth_utils import hash_password, verify_password, DEFAULT_ITERATIONS
from app.database import get_db


def valid_user_payload(**overrides):
    payload = {
        "full_name": "Chef Senthil Kumar",
        "username": "chef_senthil",
        "email": "senthil@grandhotel.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
    }
    payload.update(overrides)
    return payload


def test_register_user_success(client):
    """Test successful user registration returns 201 Created and excludes password hashes."""
    payload = valid_user_payload()
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Chef Senthil Kumar"
    assert data["username"] == "chef_senthil"
    assert data["email"] == "senthil@grandhotel.com"
    assert "id" in data
    assert "created_at" in data
    # Ensure no password or hash is exposed in API response
    assert "password" not in data
    assert "password_hash" not in data


def test_register_missing_required_fields(client):
    """Test that missing required fields trigger 422 Unprocessable Entity."""
    required_fields = ["full_name", "username", "email", "password", "confirm_password"]
    for field in required_fields:
        payload = valid_user_payload()
        del payload[field]
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 422, f"Expected 422 when '{field}' is missing"


def test_register_invalid_email_format(client):
    """Test rejection of malformed email addresses."""
    invalid_emails = ["notanemail", "user@", "@domain.com", "user@domain", "user space@domain.com"]
    for bad_email in invalid_emails:
        payload = valid_user_payload(email=bad_email)
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 422, f"Expected 422 for invalid email: '{bad_email}'"


def test_register_mismatched_passwords(client):
    """Test rejection when confirm_password does not match password."""
    payload = valid_user_payload(
        password="SuperSecretPassword1",
        confirm_password="SuperSecretPassword2",
    )
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422
    assert "passwords do not match" in str(response.json()["detail"]).lower()


def test_register_password_too_short(client):
    """Test rejection of passwords shorter than 8 characters."""
    payload = valid_user_payload(
        password="short",
        confirm_password="short",
    )
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422
    assert "at least 8 characters" in str(response.json()["detail"]).lower()


def test_register_duplicate_username_case_insensitive(client):
    """Test rejection of duplicate usernames, including case variations."""
    payload1 = valid_user_payload(username="ChefMurugan", email="murugan1@hotel.com")
    res1 = client.post("/api/auth/register", json=payload1)
    assert res1.status_code == 201

    # Attempt to register with lowercase version of same username
    payload2 = valid_user_payload(username="chefmurugan", email="murugan2@hotel.com")
    res2 = client.post("/api/auth/register", json=payload2)
    assert res2.status_code == 409
    assert "already registered" in str(res2.json()["detail"]).lower()


def test_register_duplicate_email_case_insensitive(client):
    """Test rejection of duplicate emails, including case variations."""
    payload1 = valid_user_payload(username="chef1", email="Admin@Hotel.com")
    res1 = client.post("/api/auth/register", json=payload1)
    assert res1.status_code == 201

    # Attempt to register with lowercase version of same email
    payload2 = valid_user_payload(username="chef2", email="admin@hotel.com")
    res2 = client.post("/api/auth/register", json=payload2)
    assert res2.status_code == 409
    assert "already registered" in str(res2.json()["detail"]).lower()


def test_password_hashing_security():
    """Verify PBKDF2-HMAC-SHA256 implementation with >= 600,000 iterations and salt uniqueness."""
    raw_pwd = "CorrectHorseBatteryStaple99!"
    hash1 = hash_password(raw_pwd, iterations=600_000)
    hash2 = hash_password(raw_pwd, iterations=600_000)

    # Must produce different hashes due to unique random salts
    assert hash1 != hash2

    parts = hash1.split("$")
    assert len(parts) == 4
    assert parts[0] == "pbkdf2_sha256"
    assert int(parts[1]) >= 600_000
    assert len(parts[2]) == 32  # 16-byte hex salt

    # Verification must succeed for correct password
    assert verify_password(raw_pwd, hash1) is True
    # Verification must fail for incorrect password
    assert verify_password("WrongPassword123!", hash1) is False
    # Verification must fail gracefully for malformed hash
    assert verify_password(raw_pwd, "invalid$hash$string") is False


def test_registration_page_accessible(client):
    """Test that GET /register serves the registration page."""
    response = client.get("/register")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Create Your Account" in response.text
    assert "BreakfastWise" in response.text
    assert "full_name" in response.text
    assert "confirm_password" in response.text


def test_login_page_accessible(client):
    """Test that GET /login serves the login status notice page."""
    response = client.get("/login")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Welcome Back!" in response.text
