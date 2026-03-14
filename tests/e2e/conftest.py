from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_app_settings, get_health_service
from app.core.config import Settings
from app.main import create_app
from app.schemas import ReadinessResponse


@pytest.fixture(scope="function")
def app() -> Generator[FastAPI, None, None]:
    _app = create_app()
    _app.dependency_overrides[get_app_settings] = lambda: Settings(environment="test")

    yield _app

    _app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(app: FastAPI) -> Generator[TestClient, None, None]:
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
