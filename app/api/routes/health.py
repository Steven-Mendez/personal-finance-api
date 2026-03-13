from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies.health import get_readiness_dependencies
from app.services.health import build_liveness_payload, build_readiness_payload

router = APIRouter()


@router.get("/health/live", status_code=status.HTTP_200_OK)
def read_liveness_health() -> dict[str, str]:
    return build_liveness_payload()


@router.get("/health/ready")
async def read_readiness_health(
    response: Response,
    dependencies: Annotated[dict[str, str], Depends(get_readiness_dependencies)],
) -> dict[str, object]:
    payload = build_readiness_payload(dependencies)
    if payload["status"] == "unready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload
