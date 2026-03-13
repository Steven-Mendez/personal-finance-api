from app.api.routes.root import read_root
from app.core.config import Settings


def test_read_root_returns_settings_values() -> None:
    # Given
    settings = Settings(app_name="Unit Test API", environment="test")

    # When
    response = read_root(settings)

    # Then
    assert response == {"message": "Unit Test API", "environment": "test"}
