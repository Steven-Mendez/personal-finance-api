from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.cognito.cognito import CognitoAuthService


@pytest.fixture
def cognito_service() -> CognitoAuthService:
    with patch("boto3.client") as mock_boto:
        # We need to return a mock client that has the methods we use
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        return CognitoAuthService()


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


@pytest.mark.asyncio
async def test_get_jwks(cognito_service: CognitoAuthService, mock_jwks: dict) -> None:
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_jwks
        mock_get.return_value = mock_response

        jwks = await cognito_service._get_jwks()

        assert jwks == mock_jwks
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_verify_token_success(
    cognito_service: CognitoAuthService, mock_jwks: dict
) -> None:
    token = "header.payload.signature"
    claims = {
        "sub": "user_id",
        "aud": "example_client_id",
        "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_example",
    }

    with (
        patch.object(cognito_service, "_get_jwks", return_value=mock_jwks),
        patch("jose.jwt.get_unverified_headers", return_value={"kid": "test_kid"}),
        patch("jose.jwk.construct") as mock_construct,
        patch(
            "app.services.cognito.cognito.base64url_decode", return_value=b"decoded_sig"
        ),
        patch("jose.jwt.get_unverified_claims", return_value=claims),
    ):
        from unittest.mock import MagicMock

        mock_key = MagicMock()
        mock_key.verify.return_value = True
        mock_construct.return_value = mock_key

        result = await cognito_service.verify_token(token)

        assert result == claims


@pytest.mark.asyncio
async def test_verify_token_invalid_kid(
    cognito_service: CognitoAuthService, mock_jwks: dict
) -> None:
    token = "header.payload.signature"

    with (
        patch.object(cognito_service, "_get_jwks", return_value=mock_jwks),
        patch("jose.jwt.get_unverified_headers", return_value={"kid": "wrong_kid"}),
    ):
        with pytest.raises(ValueError, match="Public key for kid wrong_kid not found"):
            await cognito_service.verify_token(token)


@pytest.mark.asyncio
async def test_login_success(cognito_service: CognitoAuthService) -> None:
    email = "test@example.com"
    password = "Password123!"
    mock_tokens = {
        "AccessToken": "access",
        "IdToken": "id",
        "RefreshToken": "refresh",
    }

    cognito_service._client.initiate_auth.return_value = {
        "AuthenticationResult": mock_tokens
    }

    result = await cognito_service.login(email, password)

    assert result == mock_tokens
    cognito_service._client.initiate_auth.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_success(cognito_service: CognitoAuthService) -> None:
    email = "test@example.com"
    password = "Password123!"
    mock_user = {"Username": email, "UserStatus": "FORCE_CHANGE_PASSWORD"}

    cognito_service._client.admin_create_user.return_value = {"User": mock_user}

    result = await cognito_service.create_user(email, password)

    assert result == mock_user
    cognito_service._client.admin_create_user.assert_called_once()


@pytest.mark.asyncio
async def test_list_users_success(cognito_service: CognitoAuthService) -> None:
    mock_users = [{"Username": "user1"}, {"Username": "user2"}]

    cognito_service._client.list_users.return_value = {"Users": mock_users}

    result = await cognito_service.list_users()

    assert result == mock_users
    cognito_service._client.list_users.assert_called_once()
