from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    app = create_app()
    # Mock the state clients before lifespan starts
    app.state.cognito_client = MagicMock()

    with TestClient(app) as test_client:
        yield test_client
