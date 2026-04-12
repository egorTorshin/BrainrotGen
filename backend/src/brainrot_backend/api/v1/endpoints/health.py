"""Health/status endpoint."""

from typing import Literal

from fastapi import APIRouter, status
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
    description="Returns the current state, service name, and version of the backend API. Used for monitoring and automated health checks.",
    responses={
        status.HTTP_200_OK: {
            "description": "Service is healthy.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "service": "BrainrotGen-API",
                        "version": "0.1.0",
                    }
                }
            },
        }
    },
)
async def health_check() -> HealthResponse:
    """Expose lightweight health information for monitors and smoke tests."""
    settings = get_settings()
    return HealthResponse(
        service=settings.app_name,
        version=settings.app_version,
    )
