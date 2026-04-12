"""Keep in sync with ``brainrot_backend.models.job`` (WORDS_PER_MINUTE / estimate)."""

WORDS_PER_MINUTE = 150


def estimate_duration_seconds(text: str) -> float:
    """Estimate speech duration in seconds (same formula as the API quota)."""
    word_count = len(text.split())
    return max((word_count / WORDS_PER_MINUTE) * 60, 1.0)


def format_mm_ss(total_seconds: float) -> str:
    """Format seconds as M:SS for captions."""
    s = int(round(total_seconds))
    m, sec = divmod(s, 60)
    return f"{m}:{sec:02d}"
