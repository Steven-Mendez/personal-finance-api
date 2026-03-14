from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_app_settings
from app.core.config import Settings

router = APIRouter()


@router.get("/")
def read_root(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> dict[str, str]:
    return {"message": settings.app_name, "environment": settings.environment}
