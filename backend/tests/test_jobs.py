"""Tests for jobs, quota, and result download."""

from __future__ import annotations

import os
import sqlite3
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from brainrot_backend.core.config import get_settings
from brainrot_backend.models.job import estimate_duration
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


def test_quota_exceeded_returns_429(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    detail = blocked.json()["detail"]
    assert isinstance(detail, dict)
    assert detail.get("code") == "QUOTA_EXCEEDED"
    assert "quota" in detail.get("message", "").lower()


def test_quota_processing_reserves_same_estimate_as_queued(
    client: TestClient,
) -> None:
    """Queued and processing both bill estimated_duration (parallel-safe reservation)."""
    _, _, token = register_user(client)
    headers = auth_headers(token)
    text_60 = " ".join(["w"] * 150)
    assert estimate_duration(text_60) == 60.0

    created = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"text": text_60, "voice": "male", "background": "minecraft"},
    )
    assert created.status_code == 201
    job_id = created.json()["job_id"]

    q_queued = client.get("/api/v1/jobs/quota", headers=headers).json()
    assert q_queued["used_seconds"] == 60.0

    conn = sqlite3.connect(os.environ["SQLITE_FILE"])
    conn.execute(
        "UPDATE jobs SET status = ?, started_at = CURRENT_TIMESTAMP WHERE id = ?",
        ("processing", job_id),
    )
    conn.commit()
    conn.close()

    q_processing = client.get("/api/v1/jobs/quota", headers=headers).json()
    assert q_processing["used_seconds"] == 60.0


def test_parallel_jobs_sum_estimates_before_completion(client: TestClient) -> None:
    """Two in-flight jobs both reserve quota; a third cannot exceed the daily cap."""
    _, _, token = register_user(client)
    headers = auth_headers(token)
    # 375 words -> 150.0 s each (see estimate_duration formula)
    text_150 = " ".join(["w"] * 375)
    assert estimate_duration(text_150) == 150.0

    j1 = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"text": text_150, "voice": "male", "background": "minecraft"},
    )
    j2 = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"text": text_150, "voice": "male", "background": "subway"},
    )
    assert j1.status_code == 201
    assert j2.status_code == 201

    q = client.get("/api/v1/jobs/quota", headers=headers).json()
    assert q["used_seconds"] == 300.0
    assert q["remaining_seconds"] == 0.0

    blocked = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"text": "hello", "voice": "male", "background": "minecraft"},
    )
    assert blocked.status_code == 429


def test_done_job_caps_actual_above_estimate_to_reserve(client: TestClient) -> None:
    """Strict reserve: if actual > estimate, quota bills at most the estimate."""
    _, _, token = register_user(client)
    headers = auth_headers(token)
    text_60 = " ".join(["w"] * 150)
    assert estimate_duration(text_60) == 60.0

    created = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"text": text_60, "voice": "male", "background": "minecraft"},
    )
    job_id = created.json()["job_id"]
    assert (
        client.get("/api/v1/jobs/quota", headers=headers).json()["used_seconds"] == 60.0
    )

    media = Path(os.environ["MEDIA_ROOT"])
    path = media / "long.mp4"
    path.write_bytes(b"x")
    conn = sqlite3.connect(os.environ["SQLITE_FILE"])
    conn.execute(
        """
        UPDATE jobs SET status = ?, result_path = ?, actual_duration_seconds = ?
        WHERE id = ?
        """,
        ("done", str(path), 90.0, job_id),
    )
    conn.commit()
    conn.close()

    assert (
        client.get("/api/v1/jobs/quota", headers=headers).json()["used_seconds"] == 60.0
    )


def test_done_job_replaces_estimate_with_lower_actual(client: TestClient) -> None:
    """When actual < estimate, quota frees the difference after completion."""
    _, _, token = register_user(client)
    headers = auth_headers(token)
    text_60 = " ".join(["w"] * 150)
    assert estimate_duration(text_60) == 60.0

    created = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"text": text_60, "voice": "male", "background": "minecraft"},
    )
    job_id = created.json()["job_id"]
    assert (
        client.get("/api/v1/jobs/quota", headers=headers).json()["used_seconds"] == 60.0
    )

    media = Path(os.environ["MEDIA_ROOT"])
    path = media / "done.mp4"
    path.write_bytes(b"x")
    conn = sqlite3.connect(os.environ["SQLITE_FILE"])
    conn.execute(
        """
        UPDATE jobs SET status = ?, result_path = ?, actual_duration_seconds = ?
        WHERE id = ?
        """,
        ("done", str(path), 30.0, job_id),
    )
    conn.commit()
    conn.close()

    assert (
        client.get("/api/v1/jobs/quota", headers=headers).json()["used_seconds"] == 30.0
    )


def test_quota_excludes_failed_jobs(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DAILY_QUOTA_SECONDS", "100")
    get_settings.cache_clear()

    _, _, token = register_user(client)
    headers = auth_headers(token)
    text_60 = " ".join(["w"] * 150)
    assert estimate_duration(text_60) == 60.0

    created = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"text": text_60, "voice": "male", "background": "subway"},
    )
    assert created.status_code == 201
    job_id = created.json()["job_id"]

    q1 = client.get("/api/v1/jobs/quota", headers=headers).json()
    assert q1["used_seconds"] == 60.0

    conn = sqlite3.connect(os.environ["SQLITE_FILE"])
    conn.execute("UPDATE jobs SET status = ? WHERE id = ?", ("failed", job_id))
    conn.commit()
    conn.close()

    q2 = client.get("/api/v1/jobs/quota", headers=headers).json()
    assert q2["used_seconds"] == 0.0

    text_90 = " ".join(["w"] * 225)
    assert estimate_duration(text_90) == 90.0
    ok = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={"text": text_90, "voice": "female", "background": "subway"},
    )
    assert ok.status_code == 201, ok.text


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
    assert "inline" in response.headers.get("content-disposition", "").lower()

    dl = client.get(
        f"/api/v1/jobs/{job_id}/result?attachment=true",
        headers=headers,
    )
    assert dl.status_code == 200
    assert "attachment" in dl.headers.get("content-disposition", "").lower()


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
