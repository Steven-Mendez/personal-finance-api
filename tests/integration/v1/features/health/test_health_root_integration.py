import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_root_route_returns_settings_payload(client: TestClient) -> None:
    # Given: a running application

    # When
    response = client.get("/api/v1/health/")

    # Then
    assert response.status_code == 200
    envelope = response.json()
    assert envelope["status"] == "success"
    payload = envelope["data"]
    assert payload["message"] == "Personal Finance API"
    assert payload["version"] == "v1"
