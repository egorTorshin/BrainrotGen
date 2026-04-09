"""Tests for jobs, quota, and result download."""

from __future__ import annotations

import os
import sqlite3
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from brainrot_backend.core.config import get_settings
from tests.conftest import auth_headers, register_user


def _mark_job_done(job_id: str, filename: str = "out.mp4") -> Path:
    """Write a dummy file and set job to done in the shared test SQLite."""
    media = Path(os.environ["MEDIA_ROOT"])
    path = media / filename
    path.write_bytes(b"fake-mp4-bytes")
    conn = sqlite3.connect(os.environ["SQLITE_FILE"])
    conn.execute(
        "UPDATE jobs SET status = ?, result_path = ? WHERE id = ?",
        ("done", str(path), job_id),
    )
    conn.commit()
    conn.close()
    return path


def test_quota_full_cycle(client: TestClient) -> None:
    _, _, token = register_user(client)
    headers = auth_headers(token)
    response = client.get("/api/v1/jobs/quota", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["daily_limit_seconds"] == 300
    assert data["used_seconds"] == 0.0
    assert data["remaining_seconds"] == 300.0


def test_create_job_and_get_status(client: TestClient) -> None:
    _, _, token = register_user(client)
    headers = auth_headers(token)
    body = {
        "text": "hello brainrot world",
        "voice": "male",
        "background": "minecraft",
    }
    created = client.post("/api/v1/jobs", headers=headers, json=body)
    assert created.status_code == 201
    job_id = created.json()["job_id"]

    status_response = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert status_response.status_code == 200
    st = status_response.json()
    assert st["job_id"] == job_id
    assert st["status"] == "queued"
    assert st["result_path"] is None


def test_get_foreign_job_forbidden(client: TestClient) -> None:
    _, _, token_a = register_user(client)
    _, _, token_b = register_user(client)
    headers_a = auth_headers(token_a)
    created = client.post(
        "/api/v1/jobs",
        headers=headers_a,
        json={"text": "secret job", "voice": "male", "background": "minecraft"},
    )
    job_id = created.json()["job_id"]

    response = client.get(
        f"/api/v1/jobs/{job_id}",
        headers=auth_headers(token_b),
    )
    assert response.status_code == 403


def test_get_job_not_found(client: TestClient) -> None:
    _, _, token = register_user(client)
    fake_id = str(uuid.uuid4())
    response = client.get(
        f"/api/v1/jobs/{fake_id}",
        headers=auth_headers(token),
    )
    assert response.status_code == 404


def test_quota_exceeded_returns_429(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DAILY_QUOTA_SECONDS", "5")
    get_settings.cache_clear()

    _, _, token = register_user(client)
    headers = auth_headers(token)
    payload = {"text": "hello", "voice": "male", "background": "minecraft"}
    for _ in range(5):
        response = client.post("/api/v1/jobs", headers=headers, json=payload)
        assert response.status_code == 201, response.text

    blocked = client.post("/api/v1/jobs", headers=headers, json=payload)
    assert blocked.status_code == 429
    assert "quota" in blocked.json()["detail"].lower()


def test_download_result_success(client: TestClient) -> None:
    _, _, token = register_user(client)
    headers = auth_headers(token)
    created = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"text": "done test", "voice": "male", "background": "minecraft"},
    )
    job_id = created.json()["job_id"]
    _mark_job_done(job_id)

    response = client.get(f"/api/v1/jobs/{job_id}/result", headers=headers)
    assert response.status_code == 200
    assert response.content == b"fake-mp4-bytes"
    assert "video/mp4" in response.headers.get("content-type", "")


def test_download_not_ready_returns_409(client: TestClient) -> None:
    _, _, token = register_user(client)
    headers = auth_headers(token)
    created = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"text": "queued only", "voice": "male", "background": "minecraft"},
    )
    job_id = created.json()["job_id"]

    response = client.get(f"/api/v1/jobs/{job_id}/result", headers=headers)
    assert response.status_code == 409


def test_openapi_lists_job_routes(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/jobs/quota" in paths
    assert "/api/v1/jobs/{job_id}/result" in paths


def test_download_result_forbidden_for_other_user(client: TestClient) -> None:
    _, _, token_a = register_user(client)
    _, _, token_b = register_user(client)
    created = client.post(
        "/api/v1/jobs",
        headers=auth_headers(token_a),
        json={"text": "mine", "voice": "male", "background": "minecraft"},
    )
    job_id = created.json()["job_id"]
    _mark_job_done(job_id)

    response = client.get(
        f"/api/v1/jobs/{job_id}/result",
        headers=auth_headers(token_b),
    )
    assert response.status_code == 403


def test_download_missing_file_returns_404(client: TestClient) -> None:
    _, _, token = register_user(client)
    headers = auth_headers(token)
    created = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"text": "orphan path", "voice": "male", "background": "minecraft"},
    )
    job_id = created.json()["job_id"]
    conn = sqlite3.connect(os.environ["SQLITE_FILE"])
    conn.execute(
        "UPDATE jobs SET status = ?, result_path = ? WHERE id = ?",
        ("done", "nonexistent-file-xyz.mp4", job_id),
    )
    conn.commit()
    conn.close()

    response = client.get(f"/api/v1/jobs/{job_id}/result", headers=headers)
    assert response.status_code == 404
    assert "missing" in response.json()["detail"].lower()
