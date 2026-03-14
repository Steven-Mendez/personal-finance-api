from fastapi import APIRouter

from app.api.v1.features.health.routes import router as health_router
from app.api.v1.features.identity.routes import router as identity_router

router = APIRouter()

router.include_router(health_router, tags=["health"])
router.include_router(identity_router, prefix="/auth", tags=["identity"])
