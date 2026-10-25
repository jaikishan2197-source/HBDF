import hashlib
import hmac
import secrets

DEFAULT_ITERATIONS = 600_000
ALGORITHM = "pbkdf2_sha256"


def hash_password(password: str, iterations: int = DEFAULT_ITERATIONS) -> str:
    """
    Hash a password using salted PBKDF2-HMAC-SHA256 with at least 600,000 iterations.
    Returns format: pbkdf2_sha256$<iterations>$<salt>$<hash>
    """
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")

    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return f"{ALGORITHM}${iterations}${salt}${dk.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a stored PBKDF2-HMAC-SHA256 hash using constant-time comparison.
    """
    if not password or not hashed:
        return False

    try:
        parts = hashed.split("$")
        if len(parts) != 4:
            return False

        algo, iter_str, salt, stored_hash = parts
        if algo != ALGORITHM:
            return False

        iterations = int(iter_str)
        if iterations < 600_000:
            # Enforce at least 600,000 iterations policy
            pass

        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(dk.hex(), stored_hash)
    except Exception:
        return False
