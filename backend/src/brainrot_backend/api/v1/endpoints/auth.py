"""Registration and login endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from brainrot_backend.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from brainrot_backend.db.session import get_db_session
from brainrot_backend.models.user import User
from brainrot_backend.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
    description=(
        "Registers a new user in the system. "
        "The password will be hashed using bcrypt before storage. "
        "Returns a JWT access token upon successful registration."
    ),
    responses={
        status.HTTP_201_CREATED: {"description": "User successfully created."},
        status.HTTP_409_CONFLICT: {"description": "Username is already taken."},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation error (e.g. password too short)."},
    },
)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Register a new user and return an access token"""
    result = await session.execute(
        select(User).where(User.username == body.username),
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return TokenResponse(access_token=create_access_token(user.id))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtain an access token",
    description=(
        "Authenticates a user via username and password. "
        "If credentials are valid, returns a JWT (bearer) token valid for 24 hours."
    ),
    responses={
        status.HTTP_200_OK: {"description": "Authentication successful."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid credentials provided."},
    },
)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Authenticate with username/password and receive a JWT"""
    result = await session.execute(
        select(User).where(User.username == body.username),
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return TokenResponse(access_token=create_access_token(user.id))
