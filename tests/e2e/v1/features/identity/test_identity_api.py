from unittest.mock import AsyncMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.v1.features.identity.dependencies import (
    get_authenticator,
    get_current_user,
    get_user_manager,
)

pytestmark = pytest.mark.e2e


def test_get_me_unauthorized(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    # FastAPI's HTTPBearer returns 401 if header is missing
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_me_success(client: TestClient) -> None:
    # Override dependency to mock successful authentication
    mock_claims = {
        "sub": "test_user_id",
        "iss": "https://cognito-idp.us-east-1.amazonaws.com/pool",
        "aud": "client_id",
        "exp": 9999999999,
        "iat": 1111111111,
    }
    client.app.dependency_overrides[get_current_user] = lambda: mock_claims

    try:
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer some_token"}
        )
        assert response.status_code == status.HTTP_200_OK
        envelope = response.json()
        assert envelope["status"] == "success"
        assert envelope["data"]["sub"] == "test_user_id"
    finally:
        client.app.dependency_overrides.clear()


def test_get_me_invalid_token(client: TestClient) -> None:
    def mock_get_current_user():
        from app.api.v1.features.identity.exceptions import InvalidTokenError

        raise InvalidTokenError("Invalid token")

    client.app.dependency_overrides[get_current_user] = mock_get_current_user

    try:
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        envelope = response.json()
        assert envelope["status"] == "error"
        assert envelope["error"]["message"] == "Invalid token"
    finally:
        client.app.dependency_overrides.clear()


def test_login_success(client: TestClient) -> None:
    mock_tokens = {
        "AccessToken": "access",
        "IdToken": "id",
        "RefreshToken": "refresh",
        "ExpiresIn": 3600,
        "TokenType": "Bearer",
    }

    mock_authenticator = AsyncMock()
    mock_authenticator.login.return_value = mock_tokens

    client.app.dependency_overrides[get_authenticator] = lambda: mock_authenticator

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "Password123!"},
        )
        assert response.status_code == status.HTTP_200_OK
        envelope = response.json()
        assert envelope["status"] == "success"
        assert envelope["data"] == mock_tokens
    finally:
        client.app.dependency_overrides.clear()


def test_create_user_success(client: TestClient) -> None:
    mock_user = {"Username": "test@example.com"}

    mock_user_manager = AsyncMock()
    mock_user_manager.create_user.return_value = mock_user

    client.app.dependency_overrides[get_user_manager] = lambda: mock_user_manager

    try:
        response = client.post(
            "/api/v1/auth/users",
            json={"email": "test@example.com", "password": "Password123!"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        envelope = response.json()
        assert envelope["status"] == "success"
        assert envelope["data"]["Username"] == mock_user["Username"]
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
            "/api/v1/auth/users", headers={"Authorization": "Bearer some_token"}
        )
        assert response.status_code == status.HTTP_200_OK
        envelope = response.json()
        assert envelope["status"] == "success"
        assert envelope["data"]["users"][0]["Username"] == mock_users[0]["Username"]
    finally:
        client.app.dependency_overrides.clear()
