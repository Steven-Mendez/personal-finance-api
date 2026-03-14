import httpx
from structlog.stdlib import BoundLogger

from app.core.config import Settings
from app.schemas import StatusLiteral
from app.services.health.health_check import HealthCheck

# Keeps the /health/ready probe response time well within the default timeout
# window of most load balancers and container orchestrators (typically 5–10 s),
# while still failing fast enough to prevent dependency-stall cascades.
_DEPENDENCY_CHECK_TIMEOUT_SECONDS = 2.0


class CognitoHealthCheck(HealthCheck):
    """Check to confirm AWS Cognito (JWKS endpoint) is reachable."""

    def __init__(
        self,
        settings: Settings,
        logger: BoundLogger,
        http_client: httpx.AsyncClient,
    ) -> None:
        self.settings = settings
        self.logger = logger
        self.http_client = http_client

    async def check(self) -> tuple[str, StatusLiteral]:
        try:
            response = await self.http_client.get(
                self.settings.cognito_jwks_url,
                timeout=_DEPENDENCY_CHECK_TIMEOUT_SECONDS,
            )
            status: StatusLiteral = (
                "healthy" if response.status_code == 200 else "unhealthy"
            )
            return "cognito", status
        except Exception as e:
            self.logger.error(
                "Cognito health check failed",
                jwks_url=self.settings.cognito_jwks_url,
                error=str(e),
            )
            return "cognito", "unhealthy"
