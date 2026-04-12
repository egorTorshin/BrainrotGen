import os

import requests

API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/v1")
_DEFAULT_TIMEOUT = 30
_CREATE_JOB_TIMEOUT = 120


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"} if token else {}


def _detail_message(res: requests.Response) -> str:
    try:
        payload = res.json()
    except Exception:
        return res.text or res.reason
    detail = payload.get("detail")
    if isinstance(detail, dict):
        return str(detail.get("message", detail.get("detail", res.reason)))
    if isinstance(detail, list) and detail:
        return str(detail[0].get("msg", detail))
    return str(detail) if detail is not None else res.reason


def register(username: str, password: str):
    res = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"username": username, "password": password},
        timeout=_DEFAULT_TIMEOUT,
    )
    if not res.ok:
        raise Exception(res.text)
    return res.json()


def login(username: str, password: str):
    res = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": username, "password": password},
        timeout=_DEFAULT_TIMEOUT,
    )
    if not res.ok:
        raise Exception(res.text)
    return res.json()


def get_quota(token: str):
    """Get user's remaining daily quota"""
    try:
        res = requests.get(
            f"{API_BASE_URL}/jobs/quota",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )

        if res.status_code == 200:
            return res.json()
        else:
            return None
    except Exception as e:
        print(f"Error fetching quota: {e}")
        return None


def create_job(token: str, text: str, voice: str, background: str):
    res = requests.post(
        f"{API_BASE_URL}/jobs",
        json={"text": text, "voice": voice, "background": background},
        headers=auth_header(token),
        timeout=_CREATE_JOB_TIMEOUT,
    )

    if res.status_code == 201:
        return res.json()

    if res.status_code == 429:
        msg = _detail_message(res)
        try:
            code = res.json().get("detail", {}).get("code", "QUOTA_EXCEEDED")
        except Exception:
            code = "QUOTA_EXCEEDED"
        raise Exception(f"{code}: {msg}")

    res.raise_for_status()
    return res.json()


def get_status(token: str, job_id: str):
    res = requests.get(
        f"{API_BASE_URL}/jobs/{job_id}",
        headers=auth_header(token),
        timeout=_DEFAULT_TIMEOUT,
    )

    try:
        data = res.json()
    except Exception:
        raise Exception(f"Invalid JSON: {res.text}")

    if not res.ok:
        raise Exception(data)

    if "status" not in data:
        raise Exception(f"Unexpected response: {data}")

    return data


def fetch_job_video_bytes(token: str, job_id: str) -> bytes:
    """Download completed job video (same bytes as preview/stream)."""
    res = requests.get(
        f"{API_BASE_URL}/jobs/{job_id}/result",
        headers=auth_header(token),
        timeout=120,
    )
    res.raise_for_status()
    return res.content
