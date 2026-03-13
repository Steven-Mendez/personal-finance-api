from app.core.config import Settings, get_settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "Personal Finance API"
    assert settings.environment == "development"


def test_settings_reads_environment_variables(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "Test API")
    monkeypatch.setenv("ENVIRONMENT", "test")

    settings = Settings()

    assert settings.app_name == "Test API"
    assert settings.environment == "test"


def test_get_settings_returns_cached_instance() -> None:
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second
