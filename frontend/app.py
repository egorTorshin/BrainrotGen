import re
import os

import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

from api import login, register, create_job, get_status, get_quota
from state import (
    init_state,
    go,
    is_authenticated,
    set_token,
    logout,
    set_job,
    clear_job,
    current_page,
)

init_state()
st.set_page_config(page_title="BrainrotGen", layout="centered")

API_BASE_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")


def validate_username(username):
    """Validate username format"""
    if not username:
        return False, "Username is required"
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 20:
        return False, "Username must be less than 20 characters"
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Only letters, numbers, and underscores allowed"
    return True, ""


def validate_password(password, confirm_password=None):
    """Validate password strength"""
    if not password:
        return False, "Password is required"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if len(password) > 50:
        return False, "Password must be less than 50 characters"
    if confirm_password is not None and password != confirm_password:
        return False, "Passwords do not match"
    return True, ""


# =========================
# LOGIN
# =========================
def login_page():
    st.title("Login")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input(
            "Username",
            key="login_user",
            placeholder="Enter your username",
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_pass",
            placeholder="Enter your password",
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button(
                "Login", use_container_width=True
            )
        with col2:
            if st.form_submit_button("Register", use_container_width=True):
                go("register")

        if submitted:
            if not username:
                st.error("Please enter your username")
                return
            if not password:
                st.error("Please enter your password")
                return

            try:
                with st.spinner("Logging in..."):
                    data = login(username, password)
                    set_token(data["access_token"])
                    go("generate")
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "Unauthorized" in error_msg:
                    st.error("Invalid username or password")
                elif "Connection" in error_msg:
                    st.error(
                        "Cannot connect to server. Please try again later."
                    )
                else:
                    st.error(f"Login failed: {error_msg}")


# =========================
# REGISTER
# =========================
def register_page():
    st.title("Register")

    with st.form("register_form", clear_on_submit=False):
        username = st.text_input(
            "Username",
            key="reg_user",
            placeholder="Enter username (min 3 characters)",
            help="Only letters, numbers, and underscores allowed",
        )

        password = st.text_input(
            "Password",
            type="password",
            key="reg_pass",
            placeholder="Enter password (min 6 characters)",
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="reg_confirm",
            placeholder="Confirm your password",
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button(
                "Register", use_container_width=True
            )
        with col2:
            if st.form_submit_button(
                "Back to Login", use_container_width=True
            ):
                go("login")

        if submitted:
            is_valid, error_msg = validate_username(username)
            if not is_valid:
                st.error(error_msg)
                return

            is_valid, error_msg = validate_password(
                password, confirm_password
            )
            if not is_valid:
                st.error(error_msg)
                return

            try:
                with st.spinner("Creating account..."):
                    data = register(username, password)
                    set_token(data["access_token"])
                    go("generate")
            except Exception as e:
                error_msg = str(e)
                if (
                    "username already exists" in error_msg.lower()
                    or "unique" in error_msg.lower()
                ):
                    st.error(
                        "Username already taken. Please choose another one."
                    )
                elif "422" in error_msg:
                    st.error(
                        "Invalid input. "
                        "Please check your username and password."
                    )
                else:
                    st.error(f"Registration failed: {error_msg}")


# =========================
# GENERATE
# =========================
def generate_page():
    st.title("BrainrotGen")

    quota = None
    if st.session_state.get("token"):
        try:
            quota = get_quota(st.session_state.token)

            if quota:
                daily_limit = int(quota["daily_limit_seconds"])
                used_seconds = int(quota["used_seconds"])
                remaining = int(quota["remaining_seconds"])
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Daily Limit",
                        f"{daily_limit // 60}:{daily_limit % 60:02d}",
                    )

                with col2:
                    st.metric(
                        "Used Today",
                        f"{used_seconds // 60}:{used_seconds % 60:02d}",
                    )

                with col3:
                    if remaining <= 0:
                        st.metric(
                            "Remaining", "0:00", delta="QUOTA EXCEEDED"
                        )
                    elif remaining < 60:
                        st.metric(
                            "Remaining",
                            f"{remaining // 60}:{remaining % 60:02d}",
                            delta="Low!",
                        )
                    else:
                        st.metric(
                            "Remaining",
                            f"{remaining // 60}:{remaining % 60:02d}",
                        )

                with col4:
                    percent_used = (
                        (used_seconds / daily_limit) * 100
                        if daily_limit > 0
                        else 0
                    )
                    st.metric("Usage", f"{percent_used:.0f}%")

                progress = (
                    min(used_seconds / daily_limit, 1.0)
                    if daily_limit > 0
                    else 0
                )
                st.progress(progress)

                if remaining <= 0:
                    st.error(
                        "**Daily quota exceeded!** "
                        "You've used all 5 minutes for today. "
                        "Please come back tomorrow."
                    )
                    st.stop()
                elif remaining < 60:
                    st.warning(
                        f"**Low quota!** Only "
                        f"{remaining // 60}:{remaining % 60:02d} remaining."
                    )

                st.markdown("---")

        except Exception as e:
            st.warning(f"Could not load quota information: {e}")

    with st.form("generate_form"):
        text = st.text_area(
            "**Text to Convert**",
            key="text",
            height=150,
            placeholder="Enter your text here...",
            help="The text will be converted to speech and used in the video",
        )

        col1, col2 = st.columns(2)
        with col1:
            voice = st.selectbox(
                "**Voice**",
                ["male", "female"],
                key="voice",
                help="Choose male or female voice for the narration",
            )
        with col2:
            background = st.selectbox(
                "**Background**",
                ["minecraft parkour", "subway surfers"],
                key="bg",
                help="Choose video background style",
            )

        if text:
            words = len(text.split())
            estimated_seconds = max(5, words // 3)
            est_min = estimated_seconds // 60
            est_sec = estimated_seconds % 60

            st.caption(
                f"Estimated duration: ~{est_min}:{est_sec:02d} minutes"
            )

            if quota:
                remaining = int(quota["remaining_seconds"])
                if estimated_seconds > remaining:
                    st.warning(
                        f"This video (~{est_min}:{est_sec:02d}) "
                        "may exceed your remaining quota"
                    )

        st.markdown("---")

        submitted = st.form_submit_button(
            "Generate Video", use_container_width=True, type="primary"
        )

        if submitted:
            if not text or not text.strip():
                st.error("Please enter some text to convert")
                return

            if len(text) > 500:
                st.warning(
                    "Text is quite long (>500 characters). "
                    "Generation may take longer."
                )

            if quota:
                remaining = int(quota["remaining_seconds"])
                if remaining <= 0:
                    st.error(
                        "Cannot generate: Daily quota exceeded. "
                        "Please come back tomorrow."
                    )
                    return

            try:
                with st.spinner("Creating your video job..."):
                    job = create_job(
                        st.session_state.token, text, voice, background
                    )
                    set_job(job["job_id"])
                    st.balloons()
                    go("preview")

            except Exception as e:
                error_msg = str(e)
                if "QUOTA_EXCEEDED" in error_msg:
                    st.error(
                        "**Daily quota exceeded!** "
                        "You've reached your 5-minute limit for today."
                    )
                    st.info(
                        "Quota resets at midnight UTC. "
                        "Check back tomorrow to generate more videos."
                    )
                else:
                    st.error(f"Failed to create job: {error_msg}")

    if st.button("Logout", use_container_width=True):
        logout()
        go("login")


# =========================
# PREVIEW
# =========================
def preview_page():
    st.title("Preview")

    job_id = st.session_state.job_id

    if not job_id:
        st.error("No job selected.")
        if st.button("Back to Generate"):
            clear_job()
            go("generate")
        return

    try:
        job = get_status(st.session_state.token, job_id)
    except Exception as e:
        st.error(f"Could not fetch job status: {e}")
        if st.button("Back to Generate"):
            clear_job()
            go("generate")
        return

    st.write("Status:", job["status"])

    if job["status"] == "done":
        try:
            res = requests.get(
                f"{API_BASE_URL}/jobs/{job_id}/result",
                headers={
                    "Authorization": f"Bearer {st.session_state.token}"
                },
                timeout=30,
            )
            if res.status_code == 200:
                st.video(res.content)
            else:
                st.error(f"Failed to load video (HTTP {res.status_code})")
        except Exception as e:
            st.error(f"Could not download video: {e}")

        if st.button("Back to Generate"):
            clear_job()
            go("generate")

    elif job["status"] == "failed":
        st.error(job.get("error", "Generation failed"))

        if st.button("Back to Generate"):
            clear_job()
            go("generate")

    else:
        st.info("Generating your video...")
        if st.button("Cancel and go back"):
            clear_job()
            go("generate")
        st_autorefresh(interval=2000, key="poll")


# =========================
# ROUTER
# =========================
if not is_authenticated():
    if current_page() == "register":
        register_page()
    else:
        login_page()
else:
    if current_page() == "preview":
        preview_page()
    else:
        generate_page()