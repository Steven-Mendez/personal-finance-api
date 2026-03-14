from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.core.config import Settings
from app.core.dependencies.settings import get_app_settings

from .dependencies import get_health_service
from .logic import HealthServiceInterface
from .schemas import HealthStatus, ReadinessResponse

router = APIRouter()


@router.get("/")
def read_root(
    settings: Annotated[Settings, Depends(get_app_settings)],
    health_service: Annotated[HealthServiceInterface, Depends(get_health_service)],
) -> dict[str, str]:
    return {
        "message": settings.app_name,
        "environment": settings.environment,
        "status": health_service.build_liveness_payload().status,
    }


@router.get("/health/live", status_code=status.HTTP_200_OK, response_model=HealthStatus)
def read_liveness_health(
    health_service: Annotated[HealthServiceInterface, Depends(get_health_service)],
) -> HealthStatus:
    return health_service.build_liveness_payload()


@router.get("/health/ready", response_model=ReadinessResponse)
async def read_readiness_health(
    response: Response,
    health_service: Annotated[HealthServiceInterface, Depends(get_health_service)],
) -> ReadinessResponse:
    dependencies = await health_service.check_dependencies()
    payload = health_service.build_readiness_payload(dependencies)
    if payload.status == "unready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload
