"""Pytest configuration: isolated env and DB before any test module imports the app."""

from __future__ import annotations

import os
import tempfile
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_settings_cache_after_each_test() -> Generator[None, None, None]:
    """So monkeypatched env vars take effect on the next request."""
    yield
    from brainrot_backend.core.config import get_settings

    get_settings.cache_clear()


def pytest_configure(_config: pytest.Config | None = None) -> None:
    """Use a temp SQLite file and media dir for the whole test session."""
    root = Path(tempfile.mkdtemp(prefix="brainrot_pytest_"))
    (root / "media").mkdir(parents=True, exist_ok=True)
    os.environ["BRAINROT_PYTEST_ROOT"] = str(root)
    os.environ["SQLITE_FILE"] = str(root / "db.sqlite")
    os.environ["MEDIA_ROOT"] = str(root / "media")
    os.environ["JWT_SECRET"] = "pytest-jwt-secret-key-32bytes-min!!"
    os.environ["DAILY_QUOTA_SECONDS"] = "300"
    os.environ["ENVIRONMENT"] = "test"

    from brainrot_backend.core.config import get_settings

    get_settings.cache_clear()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """HTTP client against the FastAPI app (DB initialized on first request)."""
    from brainrot_backend.main import app

    with TestClient(app) as test_client:
        yield test_client


def register_user(
    client: TestClient,
    *,
    username: str | None = None,
    password: str = "secretpass12",
) -> tuple[str, str, str]:
    """Register a user; return (username, password, access_token)."""
    name = username or f"user_{uuid.uuid4().hex[:10]}"
    response = client.post(
        "/api/v1/auth/register",
        json={"username": name, "password": password},
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return name, password, token


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def login_user(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]
