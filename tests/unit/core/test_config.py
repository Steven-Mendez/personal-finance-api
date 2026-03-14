import pytest

from app.core.config import Settings, get_settings


def test_settings_defaults() -> None:
    # Given / When
    settings = Settings()

    # Then
    assert settings.app_name == "Personal Finance API"
    assert settings.environment == "development"


def test_settings_reads_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given
    monkeypatch.setenv("APP_NAME", "Test API")
    monkeypatch.setenv("ENVIRONMENT", "test")

    # When
    settings = Settings()

    # Then
    assert settings.app_name == "Test API"
    assert settings.environment == "test"


def test_settings_database_url_property() -> None:
    # Given
    settings = Settings(
        db_host="test-host",
        db_port=1234,
        db_user="test-user",
        db_password="test-password",
        db_name="test-db",
    )

    # When
    url = settings.database_url.get_secret_value()

    # Then
    assert url == "postgresql+asyncpg://test-user:test-password@test-host:1234/test-db"


def test_get_settings_returns_cached_instance() -> None:
    # Given
    get_settings.cache_clear()

    # When
    first = get_settings()
    second = get_settings()

    # Then
    assert first is second
