"""JWT token management and password hashing utilities"""

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from brainrot_backend.core.config import get_settings

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*"""
    return _pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Check *plain* text against a bcrypt *hashed* value"""
    return _pwd_ctx.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    """Issue a signed JWT carrying the user id as subject claim"""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes,
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> int | None:
    """Return the user id embedded in *token*, or ``None`` on any error"""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
