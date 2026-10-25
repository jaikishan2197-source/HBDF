import sqlite3
from fastapi import APIRouter, HTTPException, status
from app.database import get_db
from app.models import UserRegisterRequest, UserResponse
from app.auth_utils import hash_password
from app import crud

router = APIRouter(prefix="/api/auth", tags=["User Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest):
    """
    Register a new user account.
    - Validates full name, username, email format, and password length (min 8 chars).
    - Checks for duplicate username and email (case-insensitive).
    - Hashes password using salted PBKDF2-HMAC-SHA256 with >= 600,000 iterations.
    - Persists non-destructively in SQLite users table.
    """
    with get_db() as conn:
        # Check for existing username (case-insensitive)
        existing_username = crud.get_user_by_username(conn, payload.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{payload.username}' is already registered. Please choose another username.",
            )

        # Check for existing email (case-insensitive)
        existing_email = crud.get_user_by_email(conn, payload.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{payload.email}' is already registered. Please use a different email or log in.",
            )

        # Hash password securely with >= 600,000 iterations PBKDF2-HMAC-SHA256
        password_hash = hash_password(payload.password, iterations=600_000)

        try:
            user = crud.create_user(
                conn,
                full_name=payload.full_name,
                username=payload.username,
                email=payload.email,
                password_hash=password_hash,
            )
            return UserResponse(**user)
        except sqlite3.IntegrityError as e:
            # Safe constraint violation fallback
            err_msg = str(e).lower()
            if "username" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username is already in use.",
                )
            elif "email" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email is already in use.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with these details already exists.",
                )
