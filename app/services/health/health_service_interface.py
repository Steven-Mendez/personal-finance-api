from abc import ABC, abstractmethod

from app.schemas import HealthStatus, ReadinessResponse, StatusLiteral


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
