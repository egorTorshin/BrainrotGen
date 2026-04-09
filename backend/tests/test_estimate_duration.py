"""Unit tests for job duration estimation (quota input)."""

from brainrot_backend.models.job import WORDS_PER_MINUTE, estimate_duration


def test_estimate_duration_single_word_is_at_least_one_second() -> None:
    assert estimate_duration("hello") == 1.0


def test_estimate_duration_empty_words_still_minimum() -> None:
    assert estimate_duration("") == 1.0


def test_estimate_duration_scales_with_word_count() -> None:
    words = " ".join(["word"] * WORDS_PER_MINUTE)
    expected = max((WORDS_PER_MINUTE / WORDS_PER_MINUTE) * 60, 1.0)
    assert estimate_duration(words) == expected
