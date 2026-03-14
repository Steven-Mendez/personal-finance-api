from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import get_readiness_dependencies
from app.schemas.health import HealthStatus, ReadinessResponse, StatusLiteral
from app.services.health import build_liveness_payload, build_readiness_payload

router = APIRouter()


@router.get("/health/live", status_code=status.HTTP_200_OK, response_model=HealthStatus)
def read_liveness_health() -> HealthStatus:
    return build_liveness_payload()


@router.get("/health/ready", response_model=ReadinessResponse)
async def read_readiness_health(
    response: Response,
    dependencies: Annotated[
        dict[str, StatusLiteral], Depends(get_readiness_dependencies)
    ],
) -> ReadinessResponse:
    payload = build_readiness_payload(dependencies)
    if payload.status == "unready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload
