"""Tests for /api/v1/auth register and login."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from tests.conftest import login_user, register_user


def test_register_returns_bearer_token(client: TestClient) -> None:
    username, _, token = register_user(client)
    assert username
    assert len(token) > 20


def test_register_duplicate_username_conflict(client: TestClient) -> None:
    name = f"dup_{uuid.uuid4().hex[:8]}"
    register_user(client, username=name)
    response = client.post(
        "/api/v1/auth/register",
        json={"username": name, "password": "secretpass12"},
    )
    assert response.status_code == 409
    assert "taken" in response.json()["detail"].lower()


def test_login_success(client: TestClient) -> None:
    password = "mysecurepass99"
    name, _, _ = register_user(client, password=password)
    token = login_user(client, name, password)
    assert token


def test_login_invalid_password(client: TestClient) -> None:
    name, _, _ = register_user(client, password="rightpass11")
    response = client.post(
        "/api/v1/auth/login",
        json={"username": name, "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_unknown_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent_user_xyz", "password": "secretpass12"},
    )
    assert response.status_code == 401


def test_protected_route_without_token(client: TestClient) -> None:
    response = client.get("/api/v1/jobs/quota")
    assert response.status_code == 401
