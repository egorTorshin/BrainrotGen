"""API v1 router composition."""

from fastapi import APIRouter

from brainrot_backend.api.v1.endpoints import health

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["health"])
