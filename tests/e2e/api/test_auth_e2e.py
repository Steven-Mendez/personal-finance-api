from unittest.mock import AsyncMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.features.identity.dependencies import (
    get_authenticator,
    get_current_user,
    get_user_manager,
)
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_get_me_unauthorized(client: TestClient) -> None:
    response = client.get("/auth/me")
    # FastAPI's HTTPBearer returns 401 if header is missing
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_me_success(client: TestClient) -> None:
    # Override dependency to mock successful authentication
    client.app.dependency_overrides[get_current_user] = lambda: {"sub": "test_user_id"}

    try:
        response = client.get(
            "/auth/me", headers={"Authorization": "Bearer some_token"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"user": {"sub": "test_user_id"}}
    finally:
        client.app.dependency_overrides.clear()


def test_get_me_invalid_token(client: TestClient) -> None:
    # We don't need to override dependency here if we want to test the actual flow
    # but that would require a real JWT and mocking JWKS.
    # For a simple E2E that tests the wiring:
    def mock_get_current_user():
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Invalid token")

    client.app.dependency_overrides[get_current_user] = mock_get_current_user

    try:
        response = client.get(
            "/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid token"
    finally:
        client.app.dependency_overrides.clear()


def test_login_success(client: TestClient) -> None:
    mock_tokens = {"AccessToken": "access", "IdToken": "id", "RefreshToken": "refresh"}

    mock_authenticator = AsyncMock()
    mock_authenticator.login.return_value = mock_tokens

    client.app.dependency_overrides[get_authenticator] = lambda: mock_authenticator

    try:
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "Password123!"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_tokens
    finally:
        client.app.dependency_overrides.clear()


def test_create_user_success(client: TestClient) -> None:
    mock_user = {"Username": "test@example.com"}

    mock_user_manager = AsyncMock()
    mock_user_manager.create_user.return_value = mock_user

    client.app.dependency_overrides[get_user_manager] = lambda: mock_user_manager

    try:
        response = client.post(
            "/auth/users",
            json={"email": "test@example.com", "password": "Password123!"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {"user": mock_user}
    finally:
        client.app.dependency_overrides.clear()


def test_list_users_success(client: TestClient) -> None:
    mock_users = [{"Username": "user1"}]

    mock_user_manager = AsyncMock()
    mock_user_manager.list_users.return_value = mock_users

    client.app.dependency_overrides[get_user_manager] = lambda: mock_user_manager
    client.app.dependency_overrides[get_current_user] = lambda: {"sub": "admin"}

    try:
        response = client.get(
            "/auth/users", headers={"Authorization": "Bearer some_token"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"users": mock_users}
    finally:
        client.app.dependency_overrides.clear()
