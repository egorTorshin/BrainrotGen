"""End-to-end tests for the Streamlit UI driven by ``AppTest``.

We patch every function in ``api`` with deterministic fakes (see the
``fake_api`` fixture in ``conftest.py``) so the whole script — from
``login_page`` through ``generate_page`` to ``preview_page`` — can be
exercised without talking to the real backend.

AppTest re-executes ``app.py`` on each ``.run()``. Since the script does
``from api import login, register, ...`` at import time, patching the
attributes on the ``api`` module *before* the run is enough: the fresh
execution picks up the fakes.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

FRONTEND_ROOT = Path(__file__).resolve().parent.parent
APP_PATH = str(FRONTEND_ROOT / "app.py")


def _new_app() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=10)
    at.run()
    return at


# ---------------------------------------------------------------------------
# Routing / initial render
# ---------------------------------------------------------------------------


def test_initial_page_is_login(fake_api):
    at = _new_app()
    assert not at.exception
    titles = [h.value for h in at.title]
    assert "Login" in titles


def test_switch_to_register_via_button(fake_api):
    at = _new_app()

    register_btn = next(
        btn for btn in at.button if btn.label == "Register"
    )
    register_btn.click().run()

    titles = [h.value for h in at.title]
    assert "Register" in titles


def test_register_validation_shows_error_for_short_username(fake_api):
    at = _new_app()
    next(btn for btn in at.button if btn.label == "Register").click().run()

    at.text_input(key="reg_user").set_value("ab")
    at.text_input(key="reg_pass").set_value("secret12")
    at.text_input(key="reg_confirm").set_value("secret12")
    submit = next(
        btn
        for btn in at.button
        if btn.label == "Register" and btn.key != "FormSubmitter:login_form-Register"
    )
    submit.click().run()

    errors = [err.value for err in at.error]
    assert any("at least 3" in msg for msg in errors)
    assert fake_api.calls == []


def test_register_validation_shows_error_for_password_mismatch(fake_api):
    at = _new_app()
    next(btn for btn in at.button if btn.label == "Register").click().run()

    at.text_input(key="reg_user").set_value("alice")
    at.text_input(key="reg_pass").set_value("password1")
    at.text_input(key="reg_confirm").set_value("different2")
    submit = next(
        btn for btn in at.button if btn.label == "Register" and "reg" in (btn.key or "")
    ) if False else None
    # pick register submit inside the form
    submit_btn = [
        b for b in at.button if b.label == "Register"
    ][-1]
    submit_btn.click().run()

    errors = [err.value for err in at.error]
    assert any("do not match" in msg.lower() for msg in errors)


# ---------------------------------------------------------------------------
# Login flow
# ---------------------------------------------------------------------------


def test_login_empty_username_shows_error(fake_api):
    at = _new_app()
    login_btn = next(
        b for b in at.button if b.label == "Login"
    )
    login_btn.click().run()

    errors = [err.value for err in at.error]
    assert any("username" in msg.lower() for msg in errors)


def test_login_successful_navigates_to_generate(fake_api):
    at = _new_app()

    at.text_input(key="login_user").set_value("alice")
    at.text_input(key="login_pass").set_value("secret123")
    next(b for b in at.button if b.label == "Login").click().run()

    assert at.session_state["token"] == "tok-login"
    assert at.session_state["page"] == "generate"
    titles = [h.value for h in at.title]
    assert "BrainrotGen" in titles

    login_calls = [c for c in fake_api.calls if c[0] == "login"]
    assert login_calls == [("login", ("alice", "secret123"), {})]


def test_login_invalid_credentials_shows_friendly_error(fake_api):
    fake_api.state["login_exc"] = Exception("401 Unauthorized")

    at = _new_app()
    at.text_input(key="login_user").set_value("alice")
    at.text_input(key="login_pass").set_value("nope")
    next(b for b in at.button if b.label == "Login").click().run()

    errors = [e.value for e in at.error]
    assert any("Invalid username or password" in msg for msg in errors)
    assert at.session_state["token"] is None


# ---------------------------------------------------------------------------
# Generate flow
# ---------------------------------------------------------------------------


def test_generate_page_renders_quota_dashboard_when_logged_in(fake_api):
    at = AppTest.from_file(APP_PATH, default_timeout=10)
    at.session_state["token"] = "tok-login"
    at.session_state["page"] = "generate"
    at.run()

    metric_labels = [m.label for m in at.get("metric")]
    assert "Daily Limit" in metric_labels
    assert "Used Today" in metric_labels
    assert "Remaining" in metric_labels
    assert "Usage" in metric_labels


def test_generate_submit_creates_job_and_opens_preview(fake_api):
    at = AppTest.from_file(APP_PATH, default_timeout=10)
    at.session_state["token"] = "tok-login"
    at.session_state["page"] = "generate"
    at.run()

    at.text_area(key="text").set_value("Hello, world! This is a test.")
    at.selectbox(key="voice").set_value("female")
    at.selectbox(key="bg").set_value("Subway Surfers")

    submit = next(
        b for b in at.button if b.label == "Generate Video"
    )
    submit.click().run()

    create_calls = [c for c in fake_api.calls if c[0] == "create_job"]
    assert len(create_calls) == 1
    _, args, _ = create_calls[0]
    token, text, voice, background = args
    assert token == "tok-login"
    assert text == "Hello, world! This is a test."
    assert voice == "female"
    assert background == "subway"

    assert at.session_state["job_id"] == "job-123"
    assert at.session_state["page"] == "preview"


def test_generate_with_empty_text_shows_error(fake_api):
    at = AppTest.from_file(APP_PATH, default_timeout=10)
    at.session_state["token"] = "tok-login"
    at.session_state["page"] = "generate"
    at.run()

    next(b for b in at.button if b.label == "Generate Video").click().run()

    errors = [e.value for e in at.error]
    assert any("enter some text" in msg.lower() for msg in errors)
    assert [c for c in fake_api.calls if c[0] == "create_job"] == []


def test_generate_quota_exceeded_shows_friendly_error(fake_api):
    fake_api.state["create_job_exc"] = Exception(
        "QUOTA_EXCEEDED: Daily limit reached"
    )

    at = AppTest.from_file(APP_PATH, default_timeout=10)
    at.session_state["token"] = "tok-login"
    at.session_state["page"] = "generate"
    at.run()

    at.text_area(key="text").set_value("some text to convert")
    next(b for b in at.button if b.label == "Generate Video").click().run()

    errors = [e.value for e in at.error]
    assert any("quota exceeded" in msg.lower() for msg in errors)
    assert at.session_state["page"] == "generate"


def test_generate_quota_fully_consumed_stops_page(fake_api):
    fake_api.state["quota"] = {
        "daily_limit_seconds": 300,
        "used_seconds": 300,
        "remaining_seconds": 0,
    }

    at = AppTest.from_file(APP_PATH, default_timeout=10)
    at.session_state["token"] = "tok-login"
    at.session_state["page"] = "generate"
    at.run()

    errors = [e.value for e in at.error]
    assert any("quota exceeded" in msg.lower() for msg in errors)


def test_logout_button_resets_session(fake_api):
    at = AppTest.from_file(APP_PATH, default_timeout=10)
    at.session_state["token"] = "tok-login"
    at.session_state["page"] = "generate"
    at.run()

    next(b for b in at.button if b.label == "Logout").click().run()
    assert at.session_state["token"] is None
    assert at.session_state["page"] == "login"


# ---------------------------------------------------------------------------
# Preview flow
# ---------------------------------------------------------------------------


@pytest.fixture
def preview_app(fake_api):
    at = AppTest.from_file(APP_PATH, default_timeout=10)
    at.session_state["token"] = "tok-login"
    at.session_state["page"] = "preview"
    at.session_state["job_id"] = "job-123"
    return at


def test_preview_done_shows_video_and_download_button(preview_app, fake_api):
    fake_api.state["job_status"] = {"status": "done", "job_id": "job-123"}
    preview_app.run()

    assert not preview_app.exception
    labels = [b.label for b in preview_app.button]
    assert "Back to Generate" in labels
    fetch_calls = [
        c for c in fake_api.calls if c[0] == "fetch_job_video_bytes"
    ]
    assert len(fetch_calls) == 1


def test_preview_failed_shows_error_and_back_button(preview_app, fake_api):
    fake_api.state["job_status"] = {
        "status": "failed",
        "job_id": "job-123",
        "error": "TTS engine crashed",
    }
    preview_app.run()

    errors = [e.value for e in preview_app.error]
    assert any("TTS engine crashed" in msg for msg in errors)
    labels = [b.label for b in preview_app.button]
    assert "Back to Generate" in labels


def test_preview_pending_shows_info_and_cancel_button(preview_app, fake_api):
    fake_api.state["job_status"] = {"status": "pending", "job_id": "job-123"}
    preview_app.run()

    infos = [i.value for i in preview_app.info]
    assert any("Generating your video" in msg for msg in infos)
    labels = [b.label for b in preview_app.button]
    assert "Cancel and go back" in labels


def test_preview_cancel_returns_to_generate(preview_app, fake_api):
    fake_api.state["job_status"] = {"status": "pending", "job_id": "job-123"}
    preview_app.run()

    next(
        b for b in preview_app.button if b.label == "Cancel and go back"
    ).click().run()

    assert preview_app.session_state["job_id"] is None
    assert preview_app.session_state["page"] == "generate"


def test_preview_without_job_shows_error(fake_api):
    at = AppTest.from_file(APP_PATH, default_timeout=10)
    at.session_state["token"] = "tok-login"
    at.session_state["page"] = "preview"
    at.session_state["job_id"] = None
    at.run()

    errors = [e.value for e in at.error]
    assert any("No job selected" in msg for msg in errors)


# ---------------------------------------------------------------------------
# Full register → generate → preview journey
# ---------------------------------------------------------------------------


def test_full_user_journey(fake_api):
    """Go from login → register → generate → preview in one continuous run."""
    at = _new_app()

    next(b for b in at.button if b.label == "Register").click().run()
    assert "Register" in [t.value for t in at.title]

    at.text_input(key="reg_user").set_value("newuser")
    at.text_input(key="reg_pass").set_value("secretpw1")
    at.text_input(key="reg_confirm").set_value("secretpw1")
    [b for b in at.button if b.label == "Register"][-1].click().run()

    assert at.session_state["token"] == "tok-register"
    assert at.session_state["page"] == "generate"

    at.text_area(key="text").set_value("A short demo sentence.")
    next(b for b in at.button if b.label == "Generate Video").click().run()

    assert at.session_state["page"] == "preview"
    assert at.session_state["job_id"] == "job-123"
    assert any(c[0] == "register" for c in fake_api.calls)
    assert any(c[0] == "create_job" for c in fake_api.calls)
