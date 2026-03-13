import pytest
from fastapi.testclient import TestClient


@pytest.mark.e2e
def test_liveness_endpoint_returns_alive(client: TestClient) -> None:
    # Given: a running application

    # When
    response = client.get("/health/live")

    # Then
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.e2e
def test_readiness_endpoint_returns_ready_when_dependencies_healthy(client: TestClient) -> None:
    # Given: all dependencies are healthy (default in the test environment)

    # When
    response = client.get("/health/ready")

    # Then
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["dependencies"] == {"api": "healthy"}


@pytest.mark.e2e
def test_readiness_endpoint_returns_503_when_dependencies_unhealthy(unhealthy_client: TestClient) -> None:
    # Given: the readiness dependency check is overridden to report unhealthy

    # When
    response = unhealthy_client.get("/health/ready")

    # Then
    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "unready"
    assert payload["dependencies"] == {"api": "unhealthy"}


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


@pytest.mark.e2e
def test_unknown_route_returns_not_found(client: TestClient) -> None:
    # Given: a running application

    # When: a request is made to a route that does not exist
    response = client.get("/does-not-exist")

    # Then
    assert response.status_code == 404
