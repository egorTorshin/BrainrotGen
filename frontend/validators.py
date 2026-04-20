"""Pure helpers used by ``app.py``: input validation and UI formatters.

Extracted into a dedicated module so they can be unit-tested without pulling
in Streamlit at import time.
"""

from __future__ import annotations

import re

_USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")


def validate_username(username: str) -> tuple[bool, str]:
    """Validate username format.

    Returns ``(ok, error_message)`` — ``error_message`` is empty when valid.
    """
    if not username:
        return False, "Username is required"
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 20:
        return False, "Username must be less than 20 characters"
    if not _USERNAME_PATTERN.match(username):
        return False, "Only letters, numbers, and underscores allowed"
    return True, ""


def validate_password(
    password: str,
    confirm_password: str | None = None,
) -> tuple[bool, str]:
    """Validate password strength and optional confirmation match."""
    if not password:
        return False, "Password is required"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if len(password) > 50:
        return False, "Password must be less than 50 characters"
    if confirm_password is not None and password != confirm_password:
        return False, "Passwords do not match"
    return True, ""


def fmt_mmss(total_seconds: int) -> str:
    """Format a whole-second count as ``M:SS`` (no zero-padding for minutes)."""
    total_seconds = int(total_seconds)
    return f"{total_seconds // 60}:{total_seconds % 60:02d}"
