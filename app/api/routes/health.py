from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies.health import get_health_service
from app.schemas import HealthStatus, ReadinessResponse
from app.services.health.health_service_interface import HealthServiceInterface

router = APIRouter()


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
