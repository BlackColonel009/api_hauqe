"""Routes API — présence des utilisateurs HAUQE."""

from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import (
    get_current_auth,
    require_permission,
)
from app.schemas.presence import PresenceListResponse
from app.services.auth_service import AuthContext
from app.services.presence_service import PresenceService


router = APIRouter(
    prefix="/presence",
    tags=["Présence utilisateurs"],
)


@router.get(
    "/users",
    response_model=PresenceListResponse,
)
async def recent_users(
    minutes: int = Query(
        default=15,
        ge=5,
        le=60,
    ),
    limit: int = Query(
        default=6,
        ge=1,
        le=20,
    ),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("PRESENCE.LIRE")
    ),
):
    """
    Utilisateurs actifs ou récemment actifs.

    ONLINE = session vivante + activité <= 2 minutes.
    RECENT = activité dans la fenêtre `minutes`.
    """

    return await PresenceService.list_users(
        db,
        actor=actor,
        minutes=minutes,
        limit=limit,
    )


@router.post(
    "/heartbeat",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def presence_heartbeat(
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    """
    Met à jour la dernière activité de la session courante.

    Le frontend n'appelle cette route qu'après une vraie interaction
    utilisateur et la limite à un appel par minute.
    """

    await PresenceService.heartbeat(
        db,
        request=request,
        actor=actor,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.get("/users/{user_id}/avatar")
async def presence_avatar(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("PRESENCE.LIRE")
    ),
):
    """
    Avatar d'un utilisateur affichable uniquement par un compte
    autorisé à consulter la présence.
    """

    document, path = await PresenceService.avatar_path(
        db,
        user_id=user_id,
    )

    suffix = path.suffix.lower()

    media_type = (
        "image/png"
        if suffix == ".png"
        else "image/jpeg"
    )

    return FileResponse(
        path=path,
        media_type=media_type,
        filename=document.nom_original or path.name,
    )
