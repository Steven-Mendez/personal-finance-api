import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_auth_service, get_current_user
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
    app.dependency_overrides[get_current_user] = lambda: {"sub": "test_user_id"}

    try:
        response = client.get(
            "/auth/me", headers={"Authorization": "Bearer some_token"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"user": {"sub": "test_user_id"}}
    finally:
        app.dependency_overrides.clear()


def test_get_me_invalid_token(client: TestClient) -> None:
    # We don't need to override dependency here if we want to test the actual flow
    # but that would require a real JWT and mocking JWKS.
    # For a simple E2E that tests the wiring:
    def mock_get_current_user():
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Invalid token")

    app.dependency_overrides[get_current_user] = mock_get_current_user

    try:
        response = client.get(
            "/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid token"
    finally:
        app.dependency_overrides.clear()


def test_login_success(client: TestClient) -> None:
    mock_tokens = {"AccessToken": "access", "IdToken": "id", "RefreshToken": "refresh"}

    class MockCognitoService:
        async def login(self, email, password):
            return mock_tokens

    app.dependency_overrides[get_auth_service] = MockCognitoService

    try:
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "Password123!"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_tokens
    finally:
        app.dependency_overrides.clear()


def test_create_user_success(client: TestClient) -> None:
    mock_user = {"Username": "test@example.com"}

    class MockCognitoService:
        async def create_user(self, email, password):
            return mock_user

    app.dependency_overrides[get_auth_service] = MockCognitoService

    try:
        response = client.post(
            "/auth/users",
            json={"email": "test@example.com", "password": "Password123!"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {"user": mock_user}
    finally:
        app.dependency_overrides.clear()


def test_list_users_success(client: TestClient) -> None:
    mock_users = [{"Username": "user1"}]

    class MockCognitoService:
        async def list_users(self):
            return mock_users

    app.dependency_overrides[get_auth_service] = MockCognitoService
    app.dependency_overrides[get_current_user] = lambda: {"sub": "admin"}

    try:
        response = client.get(
            "/auth/users", headers={"Authorization": "Bearer some_token"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"users": mock_users}
    finally:
        app.dependency_overrides.clear()
