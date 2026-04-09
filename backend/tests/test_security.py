"""Unit tests for security helpers."""

from brainrot_backend.core.security import (
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_round_trip() -> None:
    hashed = hash_password("correct horse battery")
    assert verify_password("correct horse battery", hashed)
    assert not verify_password("wrong", hashed)


def test_verify_password_rejects_malformed_hash() -> None:
    assert not verify_password("x", "not-a-valid-bcrypt-string")


def test_decode_access_token_rejects_garbage() -> None:
    assert decode_access_token("not.a.jwt") is None
