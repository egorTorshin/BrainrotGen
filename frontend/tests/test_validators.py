"""Unit tests for the pure helpers in ``validators.py``."""

from __future__ import annotations

import pytest

from validators import fmt_mmss, validate_password, validate_username


class TestValidateUsername:
    def test_valid_username(self):
        ok, msg = validate_username("alice_123")
        assert ok is True
        assert msg == ""

    def test_empty_username(self):
        ok, msg = validate_username("")
        assert ok is False
        assert "required" in msg.lower()

    def test_too_short(self):
        ok, msg = validate_username("ab")
        assert ok is False
        assert "at least 3" in msg

    def test_too_long(self):
        ok, msg = validate_username("a" * 21)
        assert ok is False
        assert "less than 20" in msg

    def test_exactly_20_is_allowed(self):
        ok, _ = validate_username("a" * 20)
        assert ok is True

    def test_exactly_3_is_allowed(self):
        ok, _ = validate_username("abc")
        assert ok is True

    @pytest.mark.parametrize(
        "bad",
        [
            "user name",
            "user-name",
            "user.name",
            "user!",
            "кириллица",
            "🙂smile",
        ],
    )
    def test_rejects_special_characters(self, bad):
        ok, msg = validate_username(bad)
        assert ok is False
        assert "letters" in msg.lower() or "allowed" in msg.lower()


class TestValidatePassword:
    def test_valid(self):
        ok, msg = validate_password("secret123")
        assert ok is True
        assert msg == ""

    def test_empty(self):
        ok, msg = validate_password("")
        assert ok is False
        assert "required" in msg.lower()

    def test_too_short(self):
        ok, msg = validate_password("abc")
        assert ok is False
        assert "at least 6" in msg

    def test_too_long(self):
        ok, msg = validate_password("a" * 51)
        assert ok is False
        assert "less than 50" in msg

    def test_boundary_6_chars_ok(self):
        ok, _ = validate_password("abcdef")
        assert ok is True

    def test_boundary_50_chars_ok(self):
        ok, _ = validate_password("a" * 50)
        assert ok is True

    def test_mismatch(self):
        ok, msg = validate_password("password1", "password2")
        assert ok is False
        assert "do not match" in msg.lower()

    def test_match(self):
        ok, _ = validate_password("password1", "password1")
        assert ok is True

    def test_confirm_none_skips_comparison(self):
        ok, _ = validate_password("password1", None)
        assert ok is True


class TestFmtMmss:
    @pytest.mark.parametrize(
        ("total_seconds", "expected"),
        [
            (0, "0:00"),
            (9, "0:09"),
            (60, "1:00"),
            (61, "1:01"),
            (599, "9:59"),
            (3600, "60:00"),
        ],
    )
    def test_formats(self, total_seconds, expected):
        assert fmt_mmss(total_seconds) == expected
