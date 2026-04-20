"""Shared fixtures for the frontend test suite.

The frontend is a Streamlit app, so we rely on two testing techniques:

* Pure-Python unit tests for modules that can be imported directly
  (``duration``, ``api``, and the helper functions from ``app``).
* End-to-end tests driven by ``streamlit.testing.v1.AppTest`` — it runs the
  real Streamlit script in-process without a browser, which is the officially
  recommended way to test Streamlit apps.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

FRONTEND_ROOT = Path(__file__).resolve().parent.parent
if str(FRONTEND_ROOT) not in sys.path:
    sys.path.insert(0, str(FRONTEND_ROOT))

os.environ.setdefault("API_URL", "http://testserver/api/v1")


@pytest.fixture
def api_base_url() -> str:
    return os.environ["API_URL"]


@pytest.fixture
def fake_api(monkeypatch):
    """Replace every function in ``api`` with a deterministic fake.

    The returned ``SimpleNamespace`` captures the arguments of the last call
    per endpoint so tests can make assertions about the UI→API interaction.
    """
    import types

    import api  # type: ignore  # noqa: WPS433 — local import is intentional

    state: dict = {
        "calls": [],
        "quota": {
            "daily_limit_seconds": 300,
            "used_seconds": 60,
            "remaining_seconds": 240,
        },
        "job_status": {"status": "done", "job_id": "job-123"},
        "create_job_exc": None,
        "login_exc": None,
        "register_exc": None,
        "video_bytes": b"FAKEVIDEOBYTES",
    }

    def _record(name: str, *args, **kwargs):
        state["calls"].append((name, args, kwargs))

    def fake_login(username, password):
        _record("login", username, password)
        if state["login_exc"]:
            raise state["login_exc"]
        return {"access_token": "tok-login"}

    def fake_register(username, password):
        _record("register", username, password)
        if state["register_exc"]:
            raise state["register_exc"]
        return {"access_token": "tok-register"}

    def fake_get_quota(token):
        _record("get_quota", token)
        return state["quota"]

    def fake_create_job(token, text, voice, background):
        _record("create_job", token, text, voice, background)
        if state["create_job_exc"]:
            raise state["create_job_exc"]
        return {"job_id": "job-123"}

    def fake_get_status(token, job_id):
        _record("get_status", token, job_id)
        return state["job_status"]

    def fake_fetch_job_video_bytes(token, job_id):
        _record("fetch_job_video_bytes", token, job_id)
        return state["video_bytes"]

    monkeypatch.setattr(api, "login", fake_login)
    monkeypatch.setattr(api, "register", fake_register)
    monkeypatch.setattr(api, "get_quota", fake_get_quota)
    monkeypatch.setattr(api, "create_job", fake_create_job)
    monkeypatch.setattr(api, "get_status", fake_get_status)
    monkeypatch.setattr(api, "fetch_job_video_bytes", fake_fetch_job_video_bytes)

    return types.SimpleNamespace(
        state=state,
        calls=state["calls"],
    )
