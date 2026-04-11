import requests
import os

API_BASE_URL = os.getenv('API_URL', "http://127.0.0.1:8000/api/v1")


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"} if token else {}


def register(username: str, password: str):
    res = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"username": username, "password": password},
    )
    if not res.ok:
        raise Exception(res.text)
    return res.json()


def login(username: str, password: str):
    res = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": username, "password": password},
    )
    if not res.ok:
        raise Exception(res.text)
    return res.json()


def create_job(token: str, text: str, voice: str, background: str):
    res = requests.post(
        f"{API_BASE_URL}/jobs",
        json={"text": text, "voice": voice, "background": background},
        headers=auth_header(token),
    )

    try:
        data = res.json()
    except:
        raise Exception(res.text)

    if not res.ok:
        raise Exception(data)

    if "job_id" not in data:
        raise Exception(f"Invalid response: {data}")

    return data


def get_status(token: str, job_id: str):
    res = requests.get(
        f"{API_BASE_URL}/jobs/{job_id}",
        headers=auth_header(token),
    )

    try:
        data = res.json()
    except:
        raise Exception(f"Invalid JSON: {res.text}")

    if not res.ok:
        raise Exception(data)

    if "status" not in data:
        raise Exception(f"Unexpected response: {data}")

    return data