"""HTTP-level tests for ``api.py`` using the ``responses`` library."""

from __future__ import annotations

import importlib

import pytest
import responses

import api


@pytest.fixture(autouse=True)
def _reload_api_module(monkeypatch, api_base_url):
    """Make sure ``api.API_BASE_URL`` uses our test base for every test."""
    monkeypatch.setenv("API_URL", api_base_url)
    importlib.reload(api)
    yield
    importlib.reload(api)


class TestAuthHeader:
    def test_with_token(self):
        assert api.auth_header("abc") == {"Authorization": "Bearer abc"}

    def test_without_token(self):
        assert api.auth_header("") == {}
        assert api.auth_header(None) == {}  # type: ignore[arg-type]


class TestRegister:
    @responses.activate
    def test_success(self, api_base_url):
        responses.add(
            responses.POST,
            f"{api_base_url}/auth/register",
            json={"access_token": "T"},
            status=201,
        )
        data = api.register("alice", "secret123")
        assert data == {"access_token": "T"}
        sent = responses.calls[0].request
        assert b'"username": "alice"' in sent.body

    @responses.activate
    def test_failure_raises(self, api_base_url):
        responses.add(
            responses.POST,
            f"{api_base_url}/auth/register",
            json={"detail": "username already exists"},
            status=400,
        )
        with pytest.raises(Exception, match="already exists"):
            api.register("alice", "secret123")


class TestLogin:
    @responses.activate
    def test_success(self, api_base_url):
        responses.add(
            responses.POST,
            f"{api_base_url}/auth/login",
            json={"access_token": "TOK"},
            status=200,
        )
        assert api.login("alice", "secret123") == {"access_token": "TOK"}

    @responses.activate
    def test_unauthorized(self, api_base_url):
        responses.add(
            responses.POST,
            f"{api_base_url}/auth/login",
            json={"detail": "Unauthorized"},
            status=401,
        )
        with pytest.raises(Exception, match="Unauthorized"):
            api.login("alice", "wrong")


class TestGetQuota:
    @responses.activate
    def test_returns_payload_on_200(self, api_base_url):
        payload = {
            "daily_limit_seconds": 300,
            "used_seconds": 60,
            "remaining_seconds": 240,
        }
        responses.add(
            responses.GET,
            f"{api_base_url}/jobs/quota",
            json=payload,
            status=200,
        )
        assert api.get_quota("tok") == payload

    @responses.activate
    def test_returns_none_on_non_200(self, api_base_url):
        responses.add(
            responses.GET,
            f"{api_base_url}/jobs/quota",
            json={"detail": "nope"},
            status=401,
        )
        assert api.get_quota("tok") is None

    @responses.activate
    def test_returns_none_on_network_error(self, api_base_url):
        assert api.get_quota("tok") is None


class TestCreateJob:
    @responses.activate
    def test_success(self, api_base_url):
        responses.add(
            responses.POST,
            f"{api_base_url}/jobs",
            json={"job_id": "J-1"},
            status=201,
        )
        assert api.create_job("tok", "hi", "male", "minecraft") == {"job_id": "J-1"}
        body = responses.calls[0].request.body or b""
        assert b'"voice": "male"' in body
        assert b'"background": "minecraft"' in body

    @responses.activate
    def test_quota_exceeded_raises_with_code(self, api_base_url):
        responses.add(
            responses.POST,
            f"{api_base_url}/jobs",
            json={
                "detail": {
                    "code": "QUOTA_EXCEEDED",
                    "message": "Daily limit reached",
                },
            },
            status=429,
        )
        with pytest.raises(Exception) as exc_info:
            api.create_job("tok", "hi", "male", "minecraft")
        assert "QUOTA_EXCEEDED" in str(exc_info.value)
        assert "Daily limit" in str(exc_info.value)

    @responses.activate
    def test_server_error_raises(self, api_base_url):
        responses.add(
            responses.POST,
            f"{api_base_url}/jobs",
            json={"detail": "boom"},
            status=500,
        )
        with pytest.raises(Exception):
            api.create_job("tok", "hi", "male", "minecraft")


class TestGetStatus:
    @responses.activate
    def test_success(self, api_base_url):
        responses.add(
            responses.GET,
            f"{api_base_url}/jobs/JOB",
            json={"job_id": "JOB", "status": "done"},
            status=200,
        )
        assert api.get_status("tok", "JOB") == {"job_id": "JOB", "status": "done"}

    @responses.activate
    def test_invalid_json_raises(self, api_base_url):
        responses.add(
            responses.GET,
            f"{api_base_url}/jobs/JOB",
            body="not json",
            status=200,
        )
        with pytest.raises(Exception, match="Invalid JSON"):
            api.get_status("tok", "JOB")

    @responses.activate
    def test_missing_status_field_raises(self, api_base_url):
        responses.add(
            responses.GET,
            f"{api_base_url}/jobs/JOB",
            json={"job_id": "JOB"},
            status=200,
        )
        with pytest.raises(Exception, match="Unexpected response"):
            api.get_status("tok", "JOB")

    @responses.activate
    def test_error_response_raises(self, api_base_url):
        responses.add(
            responses.GET,
            f"{api_base_url}/jobs/JOB",
            json={"detail": "not found"},
            status=404,
        )
        with pytest.raises(Exception):
            api.get_status("tok", "JOB")


class TestFetchJobVideoBytes:
    @responses.activate
    def test_returns_raw_bytes(self, api_base_url):
        responses.add(
            responses.GET,
            f"{api_base_url}/jobs/JOB/result",
            body=b"\x00\x01VIDEO",
            status=200,
            content_type="video/mp4",
        )
        assert api.fetch_job_video_bytes("tok", "JOB") == b"\x00\x01VIDEO"

    @responses.activate
    def test_raises_on_http_error(self, api_base_url):
        responses.add(
            responses.GET,
            f"{api_base_url}/jobs/JOB/result",
            status=404,
        )
        with pytest.raises(Exception):
            api.fetch_job_video_bytes("tok", "JOB")
