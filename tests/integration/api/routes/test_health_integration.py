from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_liveness_route_returns_alive(client: TestClient) -> None:
    # Given: a running application

    # When
    response = client.get("/health/live")

    # Then
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.integration
def test_readiness_route_returns_ready_when_health_check_passes(
    client: TestClient,
) -> None:
    # Given: all internal health checks pass (default behaviour)
    with patch("app.services.health.check_cognito", return_value=True):
        # When
        response = client.get("/health/ready")

        # Then
        assert response.status_code == 200
        assert response.json() == {
            "status": "ready",
            "dependencies": {"api": "healthy", "cognito": "healthy"},
        }


@pytest.mark.integration
def test_readiness_route_returns_503_when_health_check_raises(
    client: TestClient,
) -> None:
    # Given: the low-level check_api call raises an unexpected error
    async def failing_check_api() -> bool:
        raise RuntimeError("connection refused")

    with (
        patch("app.services.health.check_api", failing_check_api),
        patch("app.services.health.check_cognito", return_value=True),
    ):
        # When
        response = client.get("/health/ready")

    # Then
    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "unready"
    assert payload["dependencies"] == {"api": "unhealthy", "cognito": "healthy"}


@pytest.mark.integration
def test_readiness_route_returns_503_when_health_check_returns_false(
    client: TestClient,
) -> None:
    # Given: the low-level check_api call returns False
    async def degraded_check_api() -> bool:
        return False

    with (
        patch("app.services.health.check_api", degraded_check_api),
        patch("app.services.health.check_cognito", return_value=True),
    ):
        # When
        response = client.get("/health/ready")

    # Then
    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "unready"
    assert payload["dependencies"] == {"api": "unhealthy", "cognito": "healthy"}
