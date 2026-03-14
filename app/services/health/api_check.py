from app.schemas import StatusLiteral
from app.services.health.health_check import HealthCheck


class ApiHealthCheck(HealthCheck):
    """Simple check to confirm the API service is reachable."""

    async def check(self) -> tuple[str, StatusLiteral]:
        return "api", "healthy"
