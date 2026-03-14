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
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)
    db_user: str = Field(default="postgres")
    db_password: SecretStr = Field(default=SecretStr("postgres"))
    db_name: str = Field(default="finance")
    db_pool_size: int = Field(
        default=5, description="Number of permanent connections to keep."
    )
    db_max_overflow: int = Field(
        default=10, description="Number of extra connections to allow during spikes."
    )

    @property
    def database_url(self) -> SecretStr:
        """Construct the full SQLAlchemy database URL from components."""
        return SecretStr(
            f"postgresql+asyncpg://{self.db_user}:"
            f"{self.db_password.get_secret_value()}@{self.db_host}:"
            f"{self.db_port}/{self.db_name}"
        )

    # AWS Cognito
    cognito_region: str = Field(default="us-east-1")
    cognito_user_pool_id: str = Field(default="us-east-1_example")
    cognito_app_client_id: str = Field(default="example_client_id")
    cognito_domain: str | None = Field(
        default=None, description="Cognito custom or prefix domain."
    )

    @property
    def cognito_oauth_authorize_url(self) -> str:
        """Derive the Cognito authorize URL."""
        domain = self.cognito_domain or "your-domain"
        return (
            f"https://{domain}.auth.{self.cognito_region}"
            ".amazoncognito.com/oauth2/authorize"
        )

    @property
    def cognito_oauth_token_url(self) -> str:
        """Derive the Cognito token URL."""
        domain = self.cognito_domain or "your-domain"
        return (
            f"https://{domain}.auth.{self.cognito_region}"
            ".amazoncognito.com/oauth2/token"
        )

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
        extra="forbid",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Dependency to provide cached application settings."""
    return Settings()
