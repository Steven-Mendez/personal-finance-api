from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.features.health.dependencies import get_health_service
from app.api.v1.features.health.schemas import ReadinessResponse


@pytest.mark.integration
def test_liveness_route_returns_alive(client: TestClient) -> None:
    # Given: a running application

    # When
    response = client.get("/api/v1/health/live")

    # Then
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.integration
def test_readiness_route_returns_ready_when_health_check_passes(
    client: TestClient,
) -> None:
    # Given: all internal health checks pass (default behaviour)
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
        response = client.get("/api/v1/health/ready")

        # Then
        assert response.status_code == 200
        assert response.json() == {
            "status": "ready",
            "dependencies": {"api": "healthy", "cognito": "healthy"},
        }
    finally:
        client.app.dependency_overrides.clear()


@pytest.mark.integration
def test_readiness_route_returns_503_when_health_check_fails(
    client: TestClient,
) -> None:
    # Given: the readiness check fails
    mock_service = MagicMock()
    mock_service.check_dependencies = AsyncMock(
        return_value={"api": "unhealthy", "cognito": "healthy"}
    )
    mock_service.build_readiness_payload.return_value = ReadinessResponse(
        status="unready",
        dependencies={"api": "unhealthy", "cognito": "healthy"},
    )

    client.app.dependency_overrides[get_health_service] = lambda: mock_service

    try:
        # When
        response = client.get("/api/v1/health/ready")

        # Then
        assert response.status_code == 503
        payload = response.json()
        assert payload["status"] == "unready"
        assert payload["dependencies"] == {"api": "unhealthy", "cognito": "healthy"}
    finally:
        client.app.dependency_overrides.clear()
