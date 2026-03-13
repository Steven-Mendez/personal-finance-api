import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_root_route_returns_settings_payload(client: TestClient) -> None:
    # Given: the app is wired with its real settings (no dependency overrides)

    # When
    response = client.get("/")

    # Then
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Personal Finance API"
    assert payload["environment"] == "development"
