import asyncio


def build_liveness_payload() -> dict[str, str]:
    return {"status": "alive"}


def build_readiness_payload(dependencies: dict[str, str]) -> dict[str, object]:
    overall_status = "ready" if all(state == "healthy" for state in dependencies.values()) else "unready"
    return {
        "status": overall_status,
        "dependencies": dependencies,
    }


async def check_api() -> bool:
    return True


async def check_dependencies() -> dict[str, str]:
    try:
        api_result, = await asyncio.wait_for(
            asyncio.gather(check_api(), return_exceptions=True),
            timeout=2.0,
        )
    except asyncio.TimeoutError:
        return {"api": "unhealthy"}

    if isinstance(api_result, Exception) or not api_result:
        return {"api": "unhealthy"}
    return {"api": "healthy"}
