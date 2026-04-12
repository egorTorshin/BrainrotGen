"""Video generation job model"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from brainrot_backend.db.base import Base

WORDS_PER_MINUTE = 150


def estimate_duration(text: str) -> float:
    """Estimate speech duration in seconds from *text* word count"""
    word_count = len(text.split())
    return max((word_count / WORDS_PER_MINUTE) * 60, 1.0)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    voice: Mapped[str] = mapped_column(String(32), default="male")
    background: Mapped[str] = mapped_column(String(32), default="minecraft")
    status: Mapped[str] = mapped_column(String(16), default="queued")
    estimated_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    result_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner: Mapped["User | None"] = relationship(back_populates="jobs")  # noqa: F821
