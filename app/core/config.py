from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings managed via environment variables.
    Defaults are provided for development.
    """

    # General
    app_name: str = "Personal Finance API"
    environment: Literal["development", "production", "test"] = "development"
    debug: bool = False

    # Database
    # Use SecretStr for the database URL to prevent accidental logging of credentials
    database_url: SecretStr = Field(
        default=SecretStr(
            "postgresql+asyncpg://postgres:postgres@localhost:5432/finance"
        ),
        description="The full SQLAlchemy database URL.",
    )

    # AWS Cognito
    cognito_region: str = Field(default="us-east-1")
    cognito_user_pool_id: str = Field(default="us-east-1_example")
    cognito_app_client_id: str = Field(default="example_client_id")

    # Versioning
    commit_sha: str = Field(
        default="development", description="Current git commit SHA."
    )

    # Observability
    enable_metrics: bool = True
    sentry_dsn: SecretStr | None = None

    @property
    def cognito_jwks_url(self) -> str:
        """Derive the JWKS URL from Cognito settings."""
        return (
            f"https://cognito-idp.{self.cognito_region}.amazonaws.com/"
            f"{self.cognito_user_pool_id}/.well-known/jwks.json"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Dependency to provide cached application settings."""
    return Settings()
