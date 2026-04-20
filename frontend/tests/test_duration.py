"""Unit tests for the quota / duration helpers shared with the backend."""

from __future__ import annotations

import math

import pytest

from duration import WORDS_PER_MINUTE, estimate_duration_seconds, format_mm_ss


class TestEstimateDurationSeconds:
    def test_empty_text_returns_minimum_one_second(self):
        assert estimate_duration_seconds("") == 1.0

    def test_whitespace_only_text_returns_minimum(self):
        assert estimate_duration_seconds("   \n\t  ") == 1.0

    def test_short_text_never_below_one_second(self):
        assert estimate_duration_seconds("hello world") == 1.0

    def test_long_text_scales_linearly(self):
        text = " ".join(["word"] * WORDS_PER_MINUTE)
        assert math.isclose(estimate_duration_seconds(text), 60.0)

    def test_very_long_text(self):
        text = " ".join(["word"] * (WORDS_PER_MINUTE * 3))
        assert math.isclose(estimate_duration_seconds(text), 180.0)

    @pytest.mark.parametrize(
        ("word_count", "expected_seconds"),
        [
            (WORDS_PER_MINUTE // 2, 30.0),
            (WORDS_PER_MINUTE, 60.0),
            (WORDS_PER_MINUTE * 2, 120.0),
        ],
    )
    def test_parametrized_scaling(self, word_count, expected_seconds):
        text = " ".join(["x"] * word_count)
        assert math.isclose(
            estimate_duration_seconds(text),
            expected_seconds,
        )


class TestFormatMmSs:
    @pytest.mark.parametrize(
        ("seconds", "expected"),
        [
            (0, "0:00"),
            (1, "0:01"),
            (59, "0:59"),
            (60, "1:00"),
            (75, "1:15"),
            (119, "1:59"),
            (600, "10:00"),
        ],
    )
    def test_integer_seconds(self, seconds, expected):
        assert format_mm_ss(seconds) == expected

    def test_rounds_fractional_seconds(self):
        assert format_mm_ss(65.4) == "1:05"
        assert format_mm_ss(65.6) == "1:06"

    def test_preserves_leading_zeros(self):
        assert format_mm_ss(5) == "0:05"
