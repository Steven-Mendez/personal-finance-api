from typing import Any, cast

import httpx
from jose import jwk, jwt
from jose.utils import base64url_decode
from structlog.stdlib import BoundLogger

from app.core.config import Settings

from ...exceptions import InvalidTokenError
from ...logic import TokenVerifier


class CognitoTokenVerifier(TokenVerifier):
    """
    Cognito implementation for token verification.
    Focuses solely on verifying JWT tokens against Cognito JWKS.
    """

    def __init__(
        self,
        settings: Settings,
        logger: BoundLogger,
        http_client: httpx.AsyncClient,
    ) -> None:
        self.settings = settings
        self.logger = logger
        self.http_client = http_client
        self._jwks: dict[str, Any] | None = None

    async def _get_jwks(self) -> dict[str, Any]:
        """Fetch and cache JWKS keys from Cognito."""
        if self._jwks is None:
            self.logger.info(
                "Fetching Cognito JWKS keys",
                jwks_url=self.settings.cognito_jwks_url,
            )
            response = await self.http_client.get(self.settings.cognito_jwks_url)
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
            self.logger.error("Token verification failed", error=str(e))
            raise InvalidTokenError(f"Invalid token: {str(e)}") from e
