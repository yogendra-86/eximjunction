"""Security primitives: password hashing, JWT, API key generation."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import settings


# --- Passwords ---

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plaintext: str) -> str:
    return _pwd_context.hash(plaintext)


def verify_password(plaintext: str, hashed: str) -> bool:
    try:
        return _pwd_context.verify(plaintext, hashed)
    except Exception:
        return False


# --- JWT ---

def create_access_token(subject: str, token_type: str = "customer", extra_claims: dict | None = None) -> str:
    """Issue a JWT. token_type is 'admin' or 'customer'."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)).timestamp()),
        "type": token_type,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Return payload or None on any failure (expired, bad signature, malformed)."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


# --- API keys ---

API_KEY_PREFIX = "tdk_"  # "trade data key"
API_KEY_BYTES = 32


def generate_api_key() -> tuple[str, str, str]:
    """Returns (plaintext, prefix, sha256_hash). Plaintext shown ONCE."""
    raw = secrets.token_urlsafe(API_KEY_BYTES)
    plaintext = f"{API_KEY_PREFIX}{raw}"
    prefix = plaintext[:12]
    return plaintext, prefix, _sha256(plaintext)


def hash_api_key(plaintext: str) -> str:
    return _sha256(plaintext)


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
