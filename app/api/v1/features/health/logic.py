import asyncio
from abc import ABC, abstractmethod
from typing import Any, Literal

import httpx
from structlog.stdlib import BoundLogger

from .schemas import HealthStatus, ReadinessResponse, StatusLiteral

# Keeps the /health/ready probe response time well within the default timeout
# window of most load balancers and container orchestrators (typically 5–10 s),
# while still failing fast enough to prevent dependency-stall cascades.
_DEPENDENCY_CHECK_TIMEOUT_SECONDS = 2.0


class HealthCheck(ABC):
    """Abstract interface for individual health checks."""

    @abstractmethod
    async def check(self) -> tuple[str, StatusLiteral]:
        """
        Perform a health check.
        Returns a tuple of (dependency_name, status).
        """
        pass


class ApiHealthCheck(HealthCheck):
    """Simple check to confirm the API service is reachable."""

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self.http_client = http_client

    async def check(self) -> tuple[str, StatusLiteral]:
        # In a real app, this could check if the local server can make outbound calls
        # or ping a local resource. For now, it's a heartbeat.
        return "api", "healthy"


class CognitoHealthCheck(HealthCheck):
    """Check to confirm AWS Cognito (JWKS endpoint) is reachable."""

    def __init__(
        self,
        cognito_client: Any,
        user_pool_id: str,
    ) -> None:
        self.cognito_client = cognito_client
        self.user_pool_id = user_pool_id

    async def check(self) -> tuple[str, StatusLiteral]:
        try:
            # We use the Cognito client to describe the user pool as a health check
            self.cognito_client.describe_user_pool(UserPoolId=self.user_pool_id)
            return "cognito", "healthy"
        except Exception:
            return "cognito", "unhealthy"


class HealthServiceInterface(ABC):
    """Abstract interface for the main health service."""

    @abstractmethod
    def build_liveness_payload(self) -> HealthStatus:
        """Build the payload for a liveness check."""
        pass

    @abstractmethod
    def build_readiness_payload(
        self,
        dependencies: dict[str, StatusLiteral],
    ) -> ReadinessResponse:
        """Build the payload for a readiness check."""
        pass

    @abstractmethod
    async def check_dependencies(self) -> dict[str, StatusLiteral]:
        """Execute all configured health checks concurrently."""
        pass


class DefaultHealthService(HealthServiceInterface):
    """
    Default implementation of HealthServiceInterface.
    Executes multiple health checks concurrently.
    """

    def __init__(
        self,
        api_check: ApiHealthCheck,
        cognito_check: CognitoHealthCheck,
        logger: BoundLogger,
    ) -> None:
        self.api_check = api_check
        self.cognito_check = cognito_check
        self.logger = logger

    def build_liveness_payload(self) -> HealthStatus:
        return HealthStatus(status="alive")

    def build_readiness_payload(
        self,
        dependencies: dict[str, StatusLiteral],
    ) -> ReadinessResponse:
        overall_status: Literal["ready", "unready"] = (
            "ready"
            if all(state == "healthy" for state in dependencies.values())
            else "unready"
        )
        return ReadinessResponse(
            status=overall_status,
            dependencies=dependencies,
        )

    async def check_dependencies(self) -> dict[str, StatusLiteral]:
        # Run checks concurrently
        results = await asyncio.gather(
            self.api_check.check(),
            self.cognito_check.check(),
            return_exceptions=True,
        )

        dependencies: dict[str, StatusLiteral] = {}
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                name, status = result
                dependencies[name] = status
            elif isinstance(result, Exception):
                # This should be handled by individual checks
                self.logger.error("Health check error", error=str(result))

        return dependencies
