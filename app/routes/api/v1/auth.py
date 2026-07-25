from fastapi import (
    APIRouter,
    Depends,
    Request,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import get_current_auth
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
)
from app.services.auth_service import (
    AuthContext,
    AuthService,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentification"],
)


@router.post(
    "/login",
    response_model=LoginResponse,
)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService.login(
        db,
        email=payload.email,
        password=payload.password,
        request=request,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
)
async def logout(
    request: Request,
    context: AuthContext = Depends(
        get_current_auth
    ),
    db: AsyncSession = Depends(get_db),
):
    await AuthService.logout(
        db,
        context=context,
        request=request,
    )

    return LogoutResponse()