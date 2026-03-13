import pytest


@pytest.mark.integration
def test_liveness_route_returns_alive(client) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.integration
def test_readiness_route_returns_ready(client) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "dependencies": {"api": "healthy"}}
