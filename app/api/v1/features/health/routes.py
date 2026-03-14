from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from app.core.schemas.responses import ResponseEnvelope

from .dependencies import get_health_service
from .logic import HealthServiceInterface
from .schemas import HealthStatus, ReadinessResponse

router = APIRouter()


@router.get("/", response_model=ResponseEnvelope[dict[str, str]])
async def read_root() -> ResponseEnvelope[dict[str, str]]:
    """Root endpoint providing basic service identification."""
    return ResponseEnvelope(data={"message": "Personal Finance API", "version": "v1"})


@router.get("/live", response_model=ResponseEnvelope[HealthStatus])
async def liveness_check(
    health_service: Annotated[HealthServiceInterface, Depends(get_health_service)],
) -> ResponseEnvelope[HealthStatus]:
    """Endpoint for load balancers to verify the service is running."""
    return ResponseEnvelope(data=health_service.build_liveness_payload())


@router.get("/ready", response_model=ResponseEnvelope[ReadinessResponse])
async def readiness_check(
    health_service: Annotated[HealthServiceInterface, Depends(get_health_service)],
) -> Any:
    """Endpoint to verify the service and its dependencies are ready."""
    dependencies = await health_service.check_dependencies()
    payload = health_service.build_readiness_payload(dependencies)

    status_code = (
        status.HTTP_200_OK
        if payload.status == "ready"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    # Note: ResponseEnvelope handles the wrapping, status_code is for the HTTP level
    # We need to return JSONResponse if we want custom status code WITH the model
    from fastapi.responses import JSONResponse

    envelope = ResponseEnvelope(data=payload)
    return JSONResponse(
        status_code=status_code,
        content=envelope.model_dump(mode="json"),
    )
