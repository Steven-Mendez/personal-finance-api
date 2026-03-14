from typing import Any, cast

import boto3
import httpx
from botocore.exceptions import ClientError
from jose import jwk, jwt
from jose.utils import base64url_decode
from structlog import get_logger

from app.core.config import get_settings
from app.services.auth.base import Authenticator, TokenVerifier, UserManager

logger = get_logger()


class CognitoAuthService(Authenticator, TokenVerifier, UserManager):
    """
    Cognito implementation for authentication and user management.
    Follows SRP by separating logic from AWS client lifecycle management.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._jwks: dict[str, Any] | None = None
        self._client = boto3.client(
            "cognito-idp",
            region_name=self.settings.cognito_region,
        )

    async def _get_jwks(self) -> dict[str, Any]:
        """Fetch and cache JWKS keys from Cognito."""
        if self._jwks is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.settings.cognito_jwks_url)
                response.raise_for_status()
                self._jwks = cast(dict[str, Any], response.json())
        return self._jwks

    async def verify_token(self, token: str) -> dict[str, Any]:
        """Verify token signature and claims against Cognito."""
        try:
            headers = cast(dict[str, Any], jwt.get_unverified_headers(token))
            kid = headers.get("kid")
            if not kid:
                raise ValueError("Public key ID (kid) not found in token headers")

            jwks = await self._get_jwks()
            key_data = next((k for k in jwks["keys"] if k["kid"] == kid), None)
            if not key_data:
                raise ValueError(f"Public key for kid {kid} not found")

            public_key = jwk.construct(key_data)
            message, encoded_signature = token.rsplit(".", 1)
            decoded_signature = base64url_decode(encoded_signature.encode("utf-8"))

            if not public_key.verify(message.encode("utf-8"), decoded_signature):
                raise ValueError("Token signature verification failed")

            claims = cast(dict[str, Any], jwt.get_unverified_claims(token))

            # Basic validations
            if claims.get("aud") != self.settings.cognito_app_client_id:
                if claims.get("client_id") != self.settings.cognito_app_client_id:
                    raise ValueError("Token audience/client_id mismatch")

            expected_iss = (
                f"https://cognito-idp.{self.settings.cognito_region}.amazonaws.com/"
                f"{self.settings.cognito_user_pool_id}"
            )
            if claims.get("iss") != expected_iss:
                raise ValueError("Token issuer mismatch")

            return claims

        except Exception as e:
            logger.error("Token verification failed", error=str(e))
            raise ValueError(f"Invalid token: {str(e)}") from e

    async def login(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate a user and return tokens."""
        try:
            response = self._client.initiate_auth(
                ClientId=self.settings.cognito_app_client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": email,
                    "PASSWORD": password,
                },
            )
            return cast(dict[str, Any], response["AuthenticationResult"])
        except ClientError as e:
            logger.error("Failed to authenticate user in Cognito", error=str(e))
            msg = e.response["Error"]["Message"]
            raise ValueError(f"Authentication failed: {msg}") from e

    async def create_user(self, email: str, password: str) -> dict[str, Any]:
        """Create a user in Cognito User Pool."""
        try:
            response = self._client.admin_create_user(
                UserPoolId=self.settings.cognito_user_pool_id,
                Username=email,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "email_verified", "Value": "true"},
                ],
                TemporaryPassword=password,
                MessageAction="SUPPRESS",
            )
            return cast(dict[str, Any], response["User"])
        except ClientError as e:
            logger.error("Failed to create user in Cognito", error=str(e))
            msg = e.response["Error"]["Message"]
            raise ValueError(f"User creation failed: {msg}") from e

    async def list_users(self) -> list[dict[str, Any]]:
        """List all users in the configured Cognito User Pool."""
        try:
            response = self._client.list_users(
                UserPoolId=self.settings.cognito_user_pool_id,
            )
            return cast(list[dict[str, Any]], response.get("Users", []))
        except ClientError as e:
            logger.error("Failed to list users from Cognito", error=str(e))
            msg = e.response["Error"]["Message"]
            raise ValueError(f"Listing users failed: {msg}") from e
