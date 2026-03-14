import asyncio
from abc import ABC, abstractmethod
from typing import Literal

import httpx
from structlog.stdlib import BoundLogger

from app.core.config import Settings

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

    async def check(self) -> tuple[str, StatusLiteral]:
        return "api", "healthy"


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

    def __init__(self, checks: list[HealthCheck]) -> None:
        self.checks = checks

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
        if not self.checks:
            return {}

        results = await asyncio.gather(
            *[check.check() for check in self.checks], return_exceptions=True
        )

        dependencies: dict[str, StatusLiteral] = {}
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                name, status = result
                dependencies[name] = status

        return dependencies
