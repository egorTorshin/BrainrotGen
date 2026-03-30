"""Health/status endpoint."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from brainrot_backend.core.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Response payload for service health checks."""

    status: Literal["ok"] = "ok"
    service: str
    version: str


@router.get(
    "",
    response_model=HealthResponse,
    summary="Get service health status",
)
async def health_check() -> HealthResponse:
    """Expose lightweight health information for monitors and smoke tests."""
    settings = get_settings()
    return HealthResponse(
        service=settings.app_name,
        version=settings.app_version,
    )
