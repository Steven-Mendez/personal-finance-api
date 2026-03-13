from app.api.routes.root import read_root
from app.core.config import Settings


def test_read_root_returns_settings_values() -> None:
    settings = Settings(app_name="Unit Test API", environment="test")

    response = read_root(settings)

    assert response == {"message": "Unit Test API", "environment": "test"}
