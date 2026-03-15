from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cachetools import TTLCache

from app.api.v1.features.identity.exceptions import InvalidTokenError
from app.api.v1.features.identity.providers.cognito.cognito_authenticator import (
    CognitoAuthenticator,
)
from app.api.v1.features.identity.providers.cognito.cognito_token_verifier import (
    CognitoTokenVerifier,
)
from app.api.v1.features.identity.providers.cognito.cognito_user_manager import (
    CognitoUserManager,
)
from app.api.v1.features.identity.schemas import (
    BaseJWTPayload,
    TokenResponse,
    UserResponse,
)
from app.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        cognito_region="us-east-1",
        cognito_user_pool_id="us-east-1_example",
        cognito_app_client_id="example_client_id",
    )


@pytest.fixture
def logger() -> MagicMock:
    return MagicMock()


@pytest.fixture
def cognito_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def http_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_jwks() -> dict:
    return {
        "keys": [
            {
                "kid": "test_kid",
                "alg": "RS256",
                "kty": "RSA",
                "e": "AQAB",
                "n": "test_n",
                "use": "sig",
            }
        ]
    }


class TestCognitoTokenVerifier:
    @pytest.mark.asyncio
    async def test_get_jwks(
        self,
        settings: Settings,
        logger: MagicMock,
        http_client: AsyncMock,
        mock_jwks: dict,
    ) -> None:
        # Use fresh cache per test to avoid cross-test pollution
        verifier = CognitoTokenVerifier(
            settings, logger, http_client, jwks_cache=TTLCache(maxsize=10, ttl=3600)
        )
        mock_response = MagicMock()
        mock_response.json.return_value = mock_jwks
        http_client.get.return_value = mock_response

        jwks = await verifier._get_jwks()

        assert jwks == mock_jwks
        http_client.get.assert_called_once_with(settings.cognito_jwks_url)

        # Second call should use cache, no additional HTTP request
        jwks2 = await verifier._get_jwks()
        assert jwks2 == mock_jwks
        http_client.get.assert_called_once_with(settings.cognito_jwks_url)

    @pytest.mark.asyncio
    async def test_verify_token_success(
        self,
        settings: Settings,
        logger: MagicMock,
        http_client: AsyncMock,
        mock_jwks: dict,
    ) -> None:
        verifier = CognitoTokenVerifier(
            settings, logger, http_client, jwks_cache=TTLCache(maxsize=10, ttl=3600)
        )
        # Use a valid base64-url encoded string for the signature (e.g., 'sig')
        token = "header.payload.c2ln"
        claims = {
            "sub": "user_id",
            "email": "test@example.com",
            "aud": settings.cognito_app_client_id,
            "iss": (
                f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/"
                f"{settings.cognito_user_pool_id}"
            ),
            "exp": 1,
            "iat": 1,
        }

        with (
            patch.object(verifier, "_get_jwks", return_value=mock_jwks),
            patch("jose.jwt.get_unverified_headers", return_value={"kid": "test_kid"}),
            patch("jose.jwt.get_unverified_claims", return_value=claims),
            patch("jose.jwk.construct") as mock_construct,
        ):
            mock_key = MagicMock()
            mock_key.verify.return_value = True
            mock_construct.return_value = mock_key

            result = await verifier.verify_token(token)

            assert isinstance(result, BaseJWTPayload)
            assert result.sub == claims["sub"]
            assert result.email == claims["email"]

    @pytest.mark.asyncio
    async def test_verify_token_invalid_kid(
        self,
        settings: Settings,
        logger: MagicMock,
        http_client: AsyncMock,
        mock_jwks: dict,
    ) -> None:
        verifier = CognitoTokenVerifier(
            settings, logger, http_client, jwks_cache=TTLCache(maxsize=10, ttl=3600)
        )
        token = "header.payload.c2ln"

        with (
            patch.object(verifier, "_get_jwks", return_value=mock_jwks),
            patch("jose.jwt.get_unverified_headers", return_value={"kid": "wrong_kid"}),
        ):
            with pytest.raises(
                InvalidTokenError,
                match="Invalid token: Public key for kid wrong_kid not found",
            ):
                await verifier.verify_token(token)


class TestCognitoAuthenticator:
    @pytest.mark.asyncio
    async def test_login_success(
        self,
        settings: Settings,
        logger: MagicMock,
        cognito_client: MagicMock,
    ) -> None:
        authenticator = CognitoAuthenticator(settings, logger, cognito_client)
        email = "test@example.com"
        password = "Password123!"
        mock_tokens_raw = {
            "AccessToken": "access",
            "IdToken": "id",
            "RefreshToken": "refresh",
            "ExpiresIn": 3600,
            "TokenType": "Bearer",
        }

        cognito_client.initiate_auth.return_value = {
            "AuthenticationResult": mock_tokens_raw
        }

        result = await authenticator.login(email, password)

        assert isinstance(result, TokenResponse)
        assert result.AccessToken == "access"
        cognito_client.initiate_auth.assert_called_once()


class TestCognitoUserManager:
    @pytest.mark.asyncio
    async def test_create_user_success(
        self,
        settings: Settings,
        logger: MagicMock,
        cognito_client: MagicMock,
    ) -> None:
        manager = CognitoUserManager(settings, logger, cognito_client)
        email = "test@example.com"
        password = "Password123!"
        mock_user_raw = {"Username": email, "UserStatus": "FORCE_CHANGE_PASSWORD"}

        cognito_client.admin_create_user.return_value = {"User": mock_user_raw}

        result = await manager.create_user(email, password)

        assert isinstance(result, UserResponse)
        assert result.Username == email
        cognito_client.admin_create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_users_success(
        self,
        settings: Settings,
        logger: MagicMock,
        cognito_client: MagicMock,
    ) -> None:
        manager = CognitoUserManager(settings, logger, cognito_client)
        mock_users_raw = [{"Username": "user1"}, {"Username": "user2"}]

        cognito_client.list_users.return_value = {"Users": mock_users_raw}

        result = await manager.list_users()

        assert len(result) == 2
        assert all(isinstance(u, UserResponse) for u in result)
        assert result[0].Username == "user1"
        cognito_client.list_users.assert_called_once()
