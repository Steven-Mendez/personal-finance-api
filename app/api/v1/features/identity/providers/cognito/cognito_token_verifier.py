from typing import Any, cast

import httpx
from cachetools import TTLCache
from jose import jwk, jwt
from jose.utils import base64url_decode
from structlog.stdlib import BoundLogger

from app.core.config import Settings

from ...exceptions import InvalidTokenError
from ...logic import TokenVerifier
from ...schemas import BaseJWTPayload

# Shared JWKS cache: keyed by JWKS URL, 1-hour TTL, supports multiple Cognito pools
JWKS_CACHE: TTLCache[str, dict[str, Any]] = TTLCache(maxsize=10, ttl=3600)


class CognitoTokenVerifier(TokenVerifier):
    """
    Cognito implementation for token verification.
    Focuses solely on verifying JWT tokens against Cognito JWKS.
    Uses a shared TTL cache to avoid refetching JWKS on every request.
    """

    def __init__(
        self,
        settings: Settings,
        logger: BoundLogger,
        http_client: httpx.AsyncClient,
        jwks_cache: TTLCache[str, dict[str, Any]] | None = None,
    ) -> None:
        self.settings = settings
        self.logger = logger
        self.http_client = http_client
        self._jwks_cache = jwks_cache or JWKS_CACHE

    async def _get_jwks(self) -> dict[str, Any]:
        """Fetch JWKS from Cognito, using cache on hit."""
        jwks_url = self.settings.cognito_jwks_url
        cached = self._jwks_cache.get(jwks_url)
        if cached is not None:
            return cached

        self.logger.info(
            "Fetching Cognito JWKS keys",
            jwks_url=jwks_url,
        )
        response = await self.http_client.get(jwks_url)
        response.raise_for_status()
        jwks = cast(dict[str, Any], response.json())
        self._jwks_cache[jwks_url] = jwks
        return jwks

    async def verify_token(self, token: str) -> BaseJWTPayload:
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

            return BaseJWTPayload(**claims)

        except Exception as e:
            self.logger.error("Token verification failed", error=str(e))
            raise InvalidTokenError(f"Invalid token: {str(e)}") from e
