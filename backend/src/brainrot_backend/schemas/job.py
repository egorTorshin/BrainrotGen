"""Job-related request/response schemas"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

BackgroundKind = Literal["minecraft", "subway"]
VoiceKind = Literal["male", "female"]


class CreateJobRequest(BaseModel):
    """Payload for submitting a new video generation job"""

    text: str = Field(
        min_length=1,
        max_length=5000,
        description="Text content to be converted to speech and subtitles.",
        json_schema_extra={"example": "Hello world, this is a brainrot video generation test."},
    )
    voice: VoiceKind = Field(
        default="male",
        description="Voice model to use for TTS synthesis.",
        json_schema_extra={"example": "male"},
    )
    background: BackgroundKind = Field(
        default="minecraft",
        description="Gameplay asset set: minecraft (parkour) or subway (surfers).",
        json_schema_extra={"example": "minecraft"},
    )


class CreateJobResponse(BaseModel):
    """Returned immediately after a job is enqueued"""

    job_id: str = Field(
        description="Unique identifier (UUID) for the created job.",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )
    estimated_duration: float = Field(
        description="Predicted length of the generated video in seconds.",
        json_schema_extra={"example": 42.5},
    )


class JobStatusResponse(BaseModel):
    """Current state of a generation job"""

    job_id: str = Field(
        description="Unique job identifier.",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )
    status: str = Field(
        description="Current workflow state: queued, processing, done, or failed.",
        json_schema_extra={"example": "processing"},
    )
    created_at: datetime = Field(description="Timestamp when job was submitted.")
    started_at: datetime | None = Field(
        default=None,
        description="Timestamp when worker started processing (if applicable).",
    )
    finished_at: datetime | None = Field(
        default=None,
        description="Timestamp when processing finished (if applicable).",
    )
    result_path: str | None = Field(
        default=None,
        description="Relative path to the output video file (present if status is 'done').",
        json_schema_extra={"example": "jobs/550e8400-e29b-41d4-a716-446655440000.mp4"},
    )
    error: str | None = Field(
        default=None,
        description="Detailed error message if status is 'failed'.",
    )


class QuotaResponse(BaseModel):
    """Remaining daily generation quota for the authenticated user"""

    daily_limit_seconds: int = Field(
        description="Total duration allowed per 24h cycle (e.g. 300s).",
        json_schema_extra={"example": 300},
    )
    used_seconds: float = Field(
        description="Accumulated duration generated today.",
        json_schema_extra={"example": 120.5},
    )
    remaining_seconds: float = Field(
        description="Seconds remaining before quota exhaustion.",
        json_schema_extra={"example": 179.5},
    )
