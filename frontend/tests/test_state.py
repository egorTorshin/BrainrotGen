"""Tests for ``state.py`` — exercised via Streamlit's AppTest harness.

``state`` relies on ``st.session_state`` which only works inside a real
Streamlit script run, so we drive it through a tiny embedded harness.
"""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

FRONTEND_ROOT = Path(__file__).resolve().parent.parent
HARNESS = FRONTEND_ROOT / "tests" / "_state_harness.py"


def _write_harness(body: str) -> None:
    HARNESS.write_text(body, encoding="utf-8")


def _run_harness() -> AppTest:
    at = AppTest.from_file(str(HARNESS))
    at.run()
    return at


def test_init_state_sets_defaults():
    _write_harness(
        "import streamlit as st\n"
        "from state import init_state\n"
        "init_state()\n"
        "st.write(repr(st.session_state['token']))\n"
        "st.write(repr(st.session_state['job_id']))\n"
        "st.write(st.session_state['page'])\n"
    )
    at = _run_harness()
    values = [m.value for m in at.markdown]
    assert "None" in values[0]
    assert "None" in values[1]
    assert values[2] == "login"


def test_init_state_does_not_overwrite_existing_values():
    _write_harness(
        "import streamlit as st\n"
        "from state import init_state\n"
        "st.session_state['token'] = 'keep-me'\n"
        "st.session_state['page'] = 'generate'\n"
        "init_state()\n"
        "st.write(st.session_state['token'])\n"
        "st.write(st.session_state['page'])\n"
    )
    at = _run_harness()
    values = [m.value for m in at.markdown]
    assert values[0] == "keep-me"
    assert values[1] == "generate"


def test_set_token_and_is_authenticated():
    _write_harness(
        "import streamlit as st\n"
        "from state import init_state, set_token, is_authenticated\n"
        "init_state()\n"
        "st.write(str(is_authenticated()))\n"
        "set_token('abc')\n"
        "st.write(str(is_authenticated()))\n"
        "st.write(st.session_state['token'])\n"
    )
    at = _run_harness()
    values = [m.value for m in at.markdown]
    assert values[0] == "False"
    assert values[1] == "True"
    assert values[2] == "abc"


def test_logout_clears_token_and_job_and_page():
    _write_harness(
        "import streamlit as st\n"
        "from state import init_state, set_token, set_job, logout\n"
        "init_state()\n"
        "set_token('tok')\n"
        "set_job('job-1')\n"
        "st.session_state['page'] = 'preview'\n"
        "logout()\n"
        "st.write(repr(st.session_state['token']))\n"
        "st.write(repr(st.session_state['job_id']))\n"
        "st.write(st.session_state['page'])\n"
    )
    at = _run_harness()
    values = [m.value for m in at.markdown]
    assert "None" in values[0]
    assert "None" in values[1]
    assert values[2] == "login"


def test_set_and_clear_job():
    _write_harness(
        "import streamlit as st\n"
        "from state import init_state, set_job, clear_job\n"
        "init_state()\n"
        "set_job('job-42')\n"
        "st.write(repr(st.session_state['job_id']))\n"
        "clear_job()\n"
        "st.write(repr(st.session_state['job_id']))\n"
    )
    at = _run_harness()
    values = [m.value for m in at.markdown]
    assert "job-42" in values[0]
    assert "None" in values[1]


def test_current_page_reflects_session_state():
    _write_harness(
        "import streamlit as st\n"
        "from state import init_state, current_page\n"
        "init_state()\n"
        "st.write(current_page())\n"
        "st.session_state['page'] = 'generate'\n"
        "st.write(current_page())\n"
    )
    at = _run_harness()
    values = [m.value for m in at.markdown]
    assert values[0] == "login"
    assert values[1] == "generate"
