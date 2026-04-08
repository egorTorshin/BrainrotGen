"""Shared FastAPI dependencies for the API layer"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from brainrot_backend.core.security import decode_access_token
from brainrot_backend.db.session import get_db_session
from brainrot_backend.models.user import User

_bearer = HTTPBearer()


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Extract and validate the authenticated user from the JWT bearer token"""
    user_id = decode_access_token(creds.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )
    return user
