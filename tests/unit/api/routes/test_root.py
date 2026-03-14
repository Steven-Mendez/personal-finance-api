from unittest.mock import MagicMock

from app.api.routes.root import read_root
from app.core.config import Settings
from app.schemas import HealthStatus


def test_read_root_returns_settings_values() -> None:
    # Given
    settings = Settings(app_name="Unit Test API", environment="test")
    health_service = MagicMock()
    health_service.build_liveness_payload.return_value = HealthStatus(status="alive")

    # When
    response = read_root(settings, health_service)

    # Then
    assert response == {
        "message": "Unit Test API",
        "environment": "test",
        "status": "alive",
    }
