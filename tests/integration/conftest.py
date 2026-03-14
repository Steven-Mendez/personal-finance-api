from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine
from app.main import create_app


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Creates a new database session wrapped in a transaction.
    Rolls back the transaction after the test to ensure isolation.
    """
    connection = await engine.connect()
    transaction = await connection.begin()

    # Bind the session to the connection that has the active transaction
    session = AsyncSessionLocal(bind=connection)

    # We must yield the session to the test / app
    yield session

    await session.close()
    # Rollback the top-level transaction to erase all changes made during the test
    await transaction.rollback()
    await connection.close()


@pytest.fixture(scope="function")
def app_instance() -> Generator[FastAPI, None, None]:
    """Provides a FastAPI application with dependencies mocked/overridden."""
    app = create_app()

    # Mock the state clients before lifespan starts
    app.state.cognito_client = MagicMock()
    app.state.http_client = AsyncMock()

    yield app
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(app_instance: FastAPI) -> Generator[TestClient, None, None]:
    """Provides a TestClient connected to the overridden app."""
    with TestClient(app_instance) as test_client:
        yield test_client
