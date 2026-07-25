from fastapi import APIRouter, Depends

from app.permissions.auth import (
    get_current_auth,
)
from app.schemas.auth import (
    CurrentUserResponse,
)
from app.services.auth_service import (
    AuthContext,
)


router = APIRouter(
    tags=["Utilisateur courant"],
)


@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
async def me(
    context: AuthContext = Depends(
        get_current_auth
    ),
):
    user = context.user

    return CurrentUserResponse(
        id=user.id,
        email=user.email,
        nom=user.nom,
        prenoms=user.prenoms,
        fonction=user.fonction,
        statut=user.statut,
        mfa_active=user.mfa_active,
        roles=context.roles,
        permissions=context.permissions,
    )