"""
Daily generation quota accounting (seconds per user, UTC calendar day).

Business rules
--------------
* **Failed** jobs contribute ``0`` — no charge for unsuccessful runs.
* **Queued** and **processing** jobs each count ``estimated_duration`` toward the
  daily sum. That reserves quota so parallel jobs and multi-worker setups cannot
  over-commit: every accepted job is paid for up-front using the same estimate
  the API used at creation time.
* **Done** jobs bill ``min(actual, estimated)`` (strict reserve): the enqueue
  check used ``estimated_duration``, so quota must never charge more than that
  for a completed job. If the render runs longer than estimated, the user still
  gets the file, but only the reserved seconds count toward the daily total.
  If actual is shorter than estimated, the measured length is billed (freeing
  the remainder vs. the reservation).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import case, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from brainrot_backend.models.job import Job


def utc_midnight_today() -> datetime:
    """Start of the current UTC calendar day (timezone-aware)."""
    return datetime.now(timezone.utc).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def charged_seconds_expression():
    """
    SQL expression: seconds charged against quota for one job row.

    See module docstring for semantics by ``status``.
    """
    est = func.coalesce(Job.estimated_duration, 0.0)
    actual_or_est = func.coalesce(
        Job.actual_duration_seconds,
        Job.estimated_duration,
        0.0,
    )
    # min(actual_or_est, est) — portable for SQLite (no LEAST()/least built-in).
    done_charge = case((actual_or_est <= est, actual_or_est), else_=est)
    return case(
        (Job.status == "failed", literal(0.0)),
        (Job.status == "done", done_charge),
        else_=est,
    )


async def sum_charged_seconds_today(
    session: AsyncSession,
    user_id: int,
) -> float:
    """Total charged seconds for *user_id* for jobs created today (UTC)."""
    today_start = utc_midnight_today()
    expr = charged_seconds_expression()
    result = await session.execute(
        select(func.coalesce(func.sum(expr), 0.0))
        .where(Job.user_id == user_id)
        .where(Job.created_at >= today_start),
    )
    return float(result.scalar_one())
