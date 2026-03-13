from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.health import get_readiness_dependencies
from app.api.dependencies.settings import get_app_settings
from app.core.config import Settings
from app.main import create_app


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
    async def override_unhealthy_dependencies() -> dict[str, str]:
        return {"api": "unhealthy"}

    app.dependency_overrides[get_readiness_dependencies] = override_unhealthy_dependencies

    with TestClient(app) as test_client:
        yield test_client
