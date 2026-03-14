from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.health import get_health_service
from app.schemas import ReadinessResponse


@pytest.mark.e2e
def test_liveness_endpoint_returns_alive(client: TestClient) -> None:
    # Given: a running application

    # When
    response = client.get("/health/live")

    # Then
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.e2e
def test_readiness_endpoint_returns_ready_when_dependencies_healthy(
    client: TestClient,
) -> None:
    # Given: all dependencies are healthy
    mock_service = MagicMock()
    mock_service.check_dependencies = AsyncMock(
        return_value={"api": "healthy", "cognito": "healthy"}
    )
    mock_service.build_readiness_payload.return_value = ReadinessResponse(
        status="ready",
        dependencies={"api": "healthy", "cognito": "healthy"},
    )

    client.app.dependency_overrides[get_health_service] = lambda: mock_service

    try:
        # When
        response = client.get("/health/ready")

        # Then
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ready"
        assert payload["dependencies"] == {"api": "healthy", "cognito": "healthy"}
    finally:
        client.app.dependency_overrides.clear()


@pytest.mark.e2e
def test_readiness_endpoint_returns_503_when_dependencies_unhealthy(
    unhealthy_client: TestClient,
) -> None:
    # Given: the readiness dependency check is overridden to report unhealthy

    # When
    response = unhealthy_client.get("/health/ready")

    # Then
    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "unready"
    assert payload["dependencies"] == {"api": "unhealthy", "cognito": "unhealthy"}


@pytest.mark.e2e
def test_root_endpoint_returns_service_metadata(client: TestClient) -> None:
    # Given: the app is configured with environment="test"

    # When
    response = client.get("/")

    # Then
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Personal Finance API"
    assert payload["environment"] == "test"
    assert "status" in payload


@pytest.mark.e2e
def test_unknown_route_returns_not_found(client: TestClient) -> None:
    # Given: a running application

    # When: a request is made to a route that does not exist
    response = client.get("/does-not-exist")

    # Then
    assert response.status_code == 404
