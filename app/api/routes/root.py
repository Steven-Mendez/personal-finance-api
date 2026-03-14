from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_app_settings, get_health_service
from app.core.config import Settings
from app.services.health.health_service_interface import HealthServiceInterface

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
