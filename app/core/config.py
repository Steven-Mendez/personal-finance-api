from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Personal Finance API"
    environment: Literal["development", "production", "test"] = "development"

    # Database configuration
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/finance"

    # Cognito configuration
    cognito_region: str = "us-east-1"
    cognito_user_pool_id: str = "us-east-1_example"
    cognito_app_client_id: str = "example_client_id"

    @property
    def cognito_jwks_url(self) -> str:
        return f"https://cognito-idp.{self.cognito_region}.amazonaws.com/{self.cognito_user_pool_id}/.well-known/jwks.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
