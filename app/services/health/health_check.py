from abc import ABC, abstractmethod

from app.schemas import StatusLiteral


class HealthCheck(ABC):
    """Abstract interface for individual health checks."""

    @abstractmethod
    async def check(self) -> tuple[str, StatusLiteral]:
        """
        Perform a health check.
        Returns a tuple of (dependency_name, status).
        """
        pass
