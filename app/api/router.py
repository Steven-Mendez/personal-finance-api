from fastapi import APIRouter

from app.features.health.routes import router as health_router
from app.features.identity.routes import router as auth_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, tags=["auth"])
