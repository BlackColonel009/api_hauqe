from fastapi import APIRouter

from app.routes.api.v1 import health

from app.routes.api.v1.auth import (
    router as auth_router,
)
from app.routes.api.v1.me import (
    router as me_router,
)

api_router = APIRouter()


api_router.include_router(
    health.router,
    prefix="/health",
    tags=["System"],
)

api_router.include_router(
    auth_router
)

api_router.include_router(
    me_router
)