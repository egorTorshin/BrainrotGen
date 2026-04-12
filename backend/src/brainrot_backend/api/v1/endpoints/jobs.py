"""Job creation, status polling, and quota endpoints"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from brainrot_backend.api.deps import get_current_user
from brainrot_backend.core.config import get_settings
from brainrot_backend.core.media_paths import resolve_media_file
from brainrot_backend.db.session import get_db_session
from brainrot_backend.models.job import Job, estimate_duration
from brainrot_backend.models.user import User
from brainrot_backend.schemas.job import (
    CreateJobRequest,
    CreateJobResponse,
    JobStatusResponse,
    QuotaResponse,
)

router = APIRouter()


async def _used_today(user_id: int, session: AsyncSession) -> float:
    """Sum estimated_duration for all jobs the user created today"""
    today_start = datetime.now(timezone.utc).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    result = await session.execute(
        select(func.coalesce(func.sum(Job.estimated_duration), 0.0))
        .where(Job.user_id == user_id)
        .where(Job.created_at >= today_start),
    )
    return float(result.scalar_one())


@router.get(
    "/quota",
    response_model=QuotaResponse,
    summary="Get remaining daily quota",
)
async def get_quota(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> QuotaResponse:
    """Return how many seconds of generation the user has left today"""
    settings = get_settings()
    used = await _used_today(user.id, session)
    return QuotaResponse(
        daily_limit_seconds=settings.daily_quota_seconds,
        used_seconds=round(used, 1),
        remaining_seconds=round(max(settings.daily_quota_seconds - used, 0), 1),
    )


@router.post(
    "",
    response_model=CreateJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new video generation job",
)
async def create_job(
    body: CreateJobRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CreateJobResponse:
    """Enqueue a generation job after checking the daily quota"""
    settings = get_settings()
    duration = estimate_duration(body.text)
    used = await _used_today(user.id, session)

    if used + duration > settings.daily_quota_seconds:
        remaining = max(settings.daily_quota_seconds - used, 0)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Daily quota exceeded — "
                f"{remaining:.0f}s remaining, "
                f"but this job needs ~{duration:.0f}s"
            ),
        )

    job = Job(
        user_id=user.id,
        text=body.text,
        voice=body.voice,
        background=body.background,
        status="queued",
        estimated_duration=duration,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)

    return CreateJobResponse(
        job_id=job.id,
        estimated_duration=round(duration, 1),
    )


@router.get(
    "/{job_id}/result",
    response_class=FileResponse,
    summary="Download or stream the generated video file",
)
async def download_job_result(
    job_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> FileResponse:
    """Return the completed video file for this job (only when status is ``done``)."""
    settings = get_settings()
    result = await session.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    if job.status != "done":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job is not finished yet (status: {job.status})",
        )

    if not job.result_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result file not available",
        )

    try:
        path = resolve_media_file(job.result_path, settings.media_root)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result file missing on disk",
        ) from None

    download_name = f"brainrot-{job_id[:8]}.mp4"
    return FileResponse(
        path=str(path),
        media_type="video/mp4",
        filename=download_name,
        content_disposition_type="inline",
    )


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
)
async def get_job_status(
    job_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> JobStatusResponse:
    """Return the current state of a generation job owned by the caller"""
    result = await session.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        result_path=job.result_path,
        error=job.error,
    )
