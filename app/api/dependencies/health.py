from app.services.health import check_dependencies


async def get_readiness_dependencies() -> dict[str, str]:
    return await check_dependencies()
