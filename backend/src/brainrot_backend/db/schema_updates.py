"""SQLite schema adjustments after ORM create_all (additive columns)."""

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncConnection


async def ensure_jobs_quota_columns(connection: AsyncConnection) -> None:
    """Add columns introduced after initial deployments (idempotent)."""

    def _add_column_if_missing(sync_conn) -> None:
        insp = inspect(sync_conn)
        if not insp.has_table("jobs"):
            return
        cols = {c["name"] for c in insp.get_columns("jobs")}
        if "actual_duration_seconds" not in cols:
            sync_conn.execute(
                text("ALTER TABLE jobs ADD COLUMN actual_duration_seconds FLOAT"),
            )

    await connection.run_sync(_add_column_if_missing)
