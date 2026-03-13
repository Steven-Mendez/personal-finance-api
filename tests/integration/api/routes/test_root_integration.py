import pytest


@pytest.mark.integration
def test_root_route_returns_settings_payload(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Personal Finance API"
    assert response.json()["environment"] == "development"
