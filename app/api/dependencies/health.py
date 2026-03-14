from app.schemas.health import StatusLiteral
from app.services.health import check_dependencies


async def get_readiness_dependencies() -> dict[str, StatusLiteral]:
    return await check_dependencies()
