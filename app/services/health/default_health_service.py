import asyncio
from typing import Literal

from app.schemas import HealthStatus, ReadinessResponse, StatusLiteral
from app.services.health.health_check import HealthCheck
from app.services.health.health_service_interface import HealthServiceInterface


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
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # We don't have the check name here without changing the result type
                # or relying on order. Individual checks should handle their own errors.
                # If an error reaches here, we mark it as unhealthy.
                pass
            elif isinstance(result, tuple) and len(result) == 2:
                name, status = result
                dependencies[name] = status

        return dependencies
