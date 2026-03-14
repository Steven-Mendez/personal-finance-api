import asyncio

# Keeps the /health/ready probe response time well within the default timeout
# window of most load balancers and container orchestrators (typically 5–10 s),
# while still failing fast enough to prevent dependency-stall cascades.
_DEPENDENCY_CHECK_TIMEOUT_SECONDS = 2.0


def build_liveness_payload() -> dict[str, str]:
    return {"status": "alive"}


def build_readiness_payload(dependencies: dict[str, str]) -> dict[str, object]:
    overall_status = (
        "ready"
        if all(state == "healthy" for state in dependencies.values())
        else "unready"
    )
    return {
        "status": overall_status,
        "dependencies": dependencies,
    }


async def check_api() -> bool:
    return True


async def check_dependencies() -> dict[str, str]:
    try:
        (api_result,) = await asyncio.wait_for(
            asyncio.gather(check_api(), return_exceptions=True),
            timeout=_DEPENDENCY_CHECK_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        return {"api": "unhealthy"}

    if isinstance(api_result, Exception) or not api_result:
        return {"api": "unhealthy"}
    return {"api": "healthy"}
