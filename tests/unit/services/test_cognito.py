from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.features.identity.exceptions import (
    InvalidTokenError,
)
from app.api.v1.features.identity.providers.cognito.cognito_authenticator import (
    CognitoAuthenticator,
)
from app.api.v1.features.identity.providers.cognito.cognito_token_verifier import (
    CognitoTokenVerifier,
)
from app.api.v1.features.identity.providers.cognito.cognito_user_manager import (
    CognitoUserManager,
)
from app.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def logger() -> MagicMock:
    return MagicMock()


@pytest.fixture
def http_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def cognito_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_jwks() -> dict:
    return {
        "keys": [
            {
                "kid": "test_kid",
                "kty": "RSA",
                "alg": "RS256",
                "use": "sig",
                "n": "test_n",
                "e": "AQAB",
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
        verifier = CognitoTokenVerifier(settings, logger, http_client)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_jwks
        http_client.get.return_value = mock_response

        jwks = await verifier._get_jwks()

        assert jwks == mock_jwks
        http_client.get.assert_called_once_with(settings.cognito_jwks_url)

    @pytest.mark.asyncio
    async def test_verify_token_success(
        self,
        settings: Settings,
        logger: MagicMock,
        http_client: AsyncMock,
        mock_jwks: dict,
    ) -> None:
        verifier = CognitoTokenVerifier(settings, logger, http_client)
        token = "header.payload.signature"
        claims = {
            "sub": "user_id",
            "aud": "example_client_id",
            "iss": f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/{settings.cognito_user_pool_id}",
        }

        with (
            patch.object(verifier, "_get_jwks", return_value=mock_jwks),
            patch("jose.jwt.get_unverified_headers", return_value={"kid": "test_kid"}),
            patch("jose.jwk.construct") as mock_construct,
            patch(
                "app.api.v1.features.identity.providers.cognito.cognito_token_verifier.base64url_decode",
                return_value=b"decoded_sig",
            ),
            patch("jose.jwt.get_unverified_claims", return_value=claims),
        ):
            mock_key = MagicMock()
            mock_key.verify.return_value = True
            mock_construct.return_value = mock_key

            result = await verifier.verify_token(token)

            assert result == claims

    @pytest.mark.asyncio
    async def test_verify_token_invalid_kid(
        self,
        settings: Settings,
        logger: MagicMock,
        http_client: AsyncMock,
        mock_jwks: dict,
    ) -> None:
        verifier = CognitoTokenVerifier(settings, logger, http_client)
        token = "header.payload.signature"

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
        mock_tokens = {
            "AccessToken": "access",
            "IdToken": "id",
            "RefreshToken": "refresh",
        }

        cognito_client.initiate_auth.return_value = {
            "AuthenticationResult": mock_tokens
        }

        result = await authenticator.login(email, password)

        assert result == mock_tokens
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
        mock_user = {"Username": email, "UserStatus": "FORCE_CHANGE_PASSWORD"}

        cognito_client.admin_create_user.return_value = {"User": mock_user}

        result = await manager.create_user(email, password)

        assert result == mock_user
        cognito_client.admin_create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_users_success(
        self,
        settings: Settings,
        logger: MagicMock,
        cognito_client: MagicMock,
    ) -> None:
        manager = CognitoUserManager(settings, logger, cognito_client)
        mock_users = [{"Username": "user1"}, {"Username": "user2"}]

        cognito_client.list_users.return_value = {"Users": mock_users}

        result = await manager.list_users()

        assert result == mock_users
        cognito_client.list_users.assert_called_once()
