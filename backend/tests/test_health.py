"""Health endpoint smoke tests."""

from fastapi.testclient import TestClient


def test_health_endpoint_returns_expected_payload(client: TestClient) -> None:
    """Health endpoint must stay stable for external checks."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "BrainrotGen Backend",
        "version": "0.1.0",
    }


def test_openapi_contains_health_route(client: TestClient) -> None:
    """Ensure the versioned health route stays part of API contract."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/health" in paths
