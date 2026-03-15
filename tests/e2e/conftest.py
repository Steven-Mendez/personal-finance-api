from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.features.health.dependencies import get_health_service
from app.api.v1.features.health.schemas import ReadinessResponse
from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.fixture(scope="function")
def app() -> Generator[FastAPI, None, None]:
    _app = create_app()
    _app.dependency_overrides[get_settings] = lambda: Settings(
        environment="test",
        cognito_user_pool_id="us-east-1_test",
        cognito_app_client_id="test-client-id",
    )

    # In E2E tests, we want to mock the state clients before lifespan starts
    # so that Boto3 doesn't try to load real credentials.
    _app.state.cognito_client = MagicMock()
    _app.state.http_client = AsyncMock()

    yield _app

    _app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    # Use TestClient as a context manager to trigger lifespan events
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def unhealthy_client(app: FastAPI) -> Generator[TestClient, None, None]:
    def override_unhealthy_health_service() -> MagicMock:
        mock_service = MagicMock()
        mock_service.check_dependencies = AsyncMock(
            return_value={"api": "unhealthy", "cognito": "unhealthy"}
        )
        mock_service.build_readiness_payload.return_value = ReadinessResponse(
            status="unready",
            dependencies={"api": "unhealthy", "cognito": "unhealthy"},
        )
        return mock_service

    app.dependency_overrides[get_health_service] = override_unhealthy_health_service

    with TestClient(app) as test_client:
        yield test_client
