import asyncio
from typing import Literal, cast

import httpx

from app.core.config import get_settings
from app.schemas.health import HealthStatus, ReadinessResponse, StatusLiteral

# Keeps the /health/ready probe response time well within the default timeout
# window of most load balancers and container orchestrators (typically 5–10 s),
# while still failing fast enough to prevent dependency-stall cascades.
_DEPENDENCY_CHECK_TIMEOUT_SECONDS = 2.0


def build_liveness_payload() -> HealthStatus:
    return HealthStatus(status="alive")


def build_readiness_payload(
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


async def check_api() -> bool:
    return True


async def check_cognito() -> bool:
    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.cognito_jwks_url, timeout=_DEPENDENCY_CHECK_TIMEOUT_SECONDS
            )
            return cast(bool, response.status_code == 200)
    except Exception:
        return False


async def check_dependencies() -> dict[str, StatusLiteral]:
    try:
        results = await asyncio.wait_for(
            asyncio.gather(check_api(), check_cognito(), return_exceptions=True),
            timeout=_DEPENDENCY_CHECK_TIMEOUT_SECONDS,
        )
        api_result, cognito_result = results
    except asyncio.TimeoutError:
        return {"api": "unhealthy", "cognito": "unhealthy"}

    return {
        "api": "healthy" if api_result is True else "unhealthy",
        "cognito": "healthy" if cognito_result is True else "unhealthy",
    }
