"""Authentication request/response schemas"""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """Payload for creating a new user account"""

    username: str = Field(
        min_length=3,
        max_length=64,
        description="Unique username for the account",
        json_schema_extra={"example": "jdoe_brainrot"},
    )
    password: str = Field(
        min_length=6,
        max_length=128,
        description="Password must be at least 6 characters",
        json_schema_extra={"example": "strongpass123"},
    )


class LoginRequest(BaseModel):
    """Payload for obtaining an access token"""

    username: str = Field(
        description="Account username", json_schema_extra={"example": "jdoe_brainrot"}
    )
    password: str = Field(
        description="Account password", json_schema_extra={"example": "strongpass123"}
    )


class TokenResponse(BaseModel):
    """JWT bearer token returned after login or registration"""

    access_token: str = Field(
        description="JWT access token used for subsequent requests",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
    )
    token_type: str = Field(
        default="bearer",
        description="Type of the token (always 'bearer')",
        json_schema_extra={"example": "bearer"},
    )
