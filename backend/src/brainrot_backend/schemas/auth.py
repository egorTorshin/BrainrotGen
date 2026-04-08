"""Authentication request/response schemas"""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """Payload for creating a new user account"""

    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    """Payload for obtaining an access token"""

    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT bearer token returned after login or registration"""

    access_token: str
    token_type: str = "bearer"
