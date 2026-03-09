import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 390000


def get_password_hash(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return (
        f"pbkdf2_{PBKDF2_ALGORITHM}$"
        f"{PBKDF2_ITERATIONS}$"
        f"{base64.b64encode(salt).decode('utf-8')}$"
        f"{base64.b64encode(key).decode('utf-8')}"
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        algo_part, iter_part, salt_part, key_part = hashed_password.split("$")
        if algo_part != f"pbkdf2_{PBKDF2_ALGORITHM}":
            return False
        iterations = int(iter_part)
        salt = base64.b64decode(salt_part.encode("utf-8"))
        expected_key = base64.b64decode(key_part.encode("utf-8"))
    except (ValueError, TypeError):
        return False

    actual_key = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        plain_password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual_key, expected_key)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
