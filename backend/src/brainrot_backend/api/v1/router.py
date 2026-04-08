"""API v1 router composition"""

from fastapi import APIRouter

from brainrot_backend.api.v1.endpoints import auth, health, jobs

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
