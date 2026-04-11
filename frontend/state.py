import streamlit as st


def init_state():
    defaults = {
        "token": None,
        "job_id": None,
        "page": "login",
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def set_token(token: str):
    st.session_state.token = token


def logout():
    st.session_state.token = None
    st.session_state.job_id = None
    st.session_state.page = "login"


def set_job(job_id: str):
    st.session_state.job_id = job_id


def clear_job():
    st.session_state.job_id = None


def go(page: str):
    st.session_state.page = page
    st.rerun()


def is_authenticated():
    return st.session_state.token is not None


def current_page():
    return st.session_state.page