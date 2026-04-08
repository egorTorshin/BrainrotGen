"""Job-related request/response schemas"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateJobRequest(BaseModel):
    """Payload for submitting a new video generation job"""

    text: str = Field(min_length=1, max_length=5000)
    voice: str = Field(default="male")
    background: str = Field(default="minecraft")


class CreateJobResponse(BaseModel):
    """Returned immediately after a job is enqueued"""

    job_id: str
    estimated_duration: float


class JobStatusResponse(BaseModel):
    """Current state of a generation job"""

    job_id: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result_path: str | None = None
    error: str | None = None


class QuotaResponse(BaseModel):
    """Remaining daily generation quota for the authenticated user"""

    daily_limit_seconds: int
    used_seconds: float
    remaining_seconds: float
