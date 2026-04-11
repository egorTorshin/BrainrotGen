import streamlit as st
import time
import os
from streamlit_autorefresh import st_autorefresh

from api import login, register, create_job, get_status
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

API_BASE_URL = os.getenv('API_URL', "http://localhost:8000/api/v1")




def validate_username(username):
    """Validate username format"""
    if not username:
        return False, "Username is required"
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 20:
        return False, "Username must be less than 20 characters"
    return True, ""

def validate_password(password, confirm_password=None):
    """Validate password strength"""
    if not password:
        return False, "Password is required"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if len(password) > 50:
        return False, "Password must be less than 50 characters"
    
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
            placeholder="Enter your username"
        )
        
        password = st.text_input(
            "Password", 
            type="password", 
            key="login_pass",
            placeholder="Enter your password"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("Login", use_container_width=True)
        with col2:
            if st.form_submit_button("Register", use_container_width=True):
                go("register")
                st.rerun()
        
        if submitted:
            # Validate inputs
            if not username:
                st.error("Please enter your username")
                return
            if not password:
                st.error("Please enter your password")
                return
            
            # Attempt login
            try:
                with st.spinner("Logging in..."):
                    data = login(username, password)
                    set_token(data["access_token"])
                    go("generate")
                    st.rerun()
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "Unauthorized" in error_msg:
                    st.error("Invalid username or password")
                elif "Connection error" in error_msg:
                    st.error("Cannot connect to server. Please try again later.")
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
            help="Only letters, numbers, and underscores allowed"
        )
        
        password = st.text_input(
            "Password", 
            type="password", 
            key="reg_pass",
            placeholder="Enter password (min 6 characters)"
        )
        
        confirm_password = st.text_input(
            "Confirm Password", 
            type="password", 
            key="reg_confirm",
            placeholder="Confirm your password"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("Register", use_container_width=True)
        with col2:
            if st.form_submit_button("⬅ Back to Login", use_container_width=True):
                go("login")
                st.rerun()
        
        if submitted:
            # Validate username
            is_valid, error_msg = validate_username(username)
            if not is_valid:
                st.error(error_msg)
                return
            
            # Validate password
            is_valid, error_msg = validate_password(password, confirm_password)
            if not is_valid:
                st.error(error_msg)
                return
            
            # Attempt registration
            try:
                with st.spinner("Creating account..."):
                    data = register(username, password)
                    set_token(data["access_token"])
                    go("generate")
                    st.rerun()
            except Exception as e:
                error_msg = str(e)
                if "username already exists" in error_msg.lower() or "unique" in error_msg.lower():
                    st.error("Username already taken. Please choose another one.")
                elif "422" in error_msg:
                    st.error("Invalid input. Please check your username and password.")
                else:
                    st.error(f"Registration failed: {error_msg}")



# =========================
# GENERATE
# =========================
def generate_page():
    st.title("🧠 BrainrotGen")

    text = st.text_area("Text", key="text")
    voice = st.selectbox("Voice", ["male", "female"], key="voice")
    background = st.selectbox("Background", ["minecraft parkour", "subway surfers"], key="bg")

    if st.button("Generate"):
        try:
            job = create_job(st.session_state.token, text, voice, background)
            set_job(job["job_id"])
            go("preview")
        except Exception as e:
            st.error(str(e))

    if st.button("Logout"):
        logout()
        go("login")


# =========================
# PREVIEW
# =========================
def preview_page():
    st.title("🎬 Preview")

    job_id = st.session_state.job_id

    if not job_id:
        st.error("No job_id")
        return

    job = get_status(st.session_state.token, job_id)
    st.write("Status:", job["status"])

    if job["status"] == "done":

        import requests

        res = requests.get(
            f"{API_BASE_URL}/jobs/{job_id}/result",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )

        if res.status_code == 200:
            st.video(res.content)
        else:
            st.error(f"Failed to load video: {res.text}")

        if st.button("⬅ Back"):
            clear_job()
            go("generate")
            st.rerun()

    elif job["status"] == "failed":
        st.error(job.get("error", "Failed"))

        if st.button("⬅ Back"):
            st.session_state.job_id = None
            st.session_state.page = "generate"
            st.rerun()

    else:
        st.info("Generating...")
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