"""
Avatar personnel pour Mon compte.

Cette route ne donne pas la permission générale DOCUMENTS.DEPOSER :
chaque utilisateur authentifié ne peut agir que sur son propre avatar.

Aucune migration supplémentaire :
preferences_utilisateur.avatar_document_id existe déjà.
"""

from __future__ import annotations

from datetime import date
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.document import Document
from app.models.preference_utilisateur import PreferenceUtilisateur
from app.permissions.auth import get_current_auth
from app.services.auth_service import AuthContext


avatar_router = APIRouter(
    prefix="/me",
    tags=["Mon compte"],
)

account_avatar_router = APIRouter(
    prefix="/auth",
    tags=["Authentification - compte"],
)

MAX_AVATAR_BYTES = 3 * 1024 * 1024

ALLOWED_MIME_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
}


def avatar_storage_dir() -> Path:
    """
    Stockage privé sous app/uploads/avatars.

    Ce dossier ne doit pas être monté publiquement.
    Le téléchargement passe par GET /api/v1/me/avatar.
    """

    app_dir = Path(__file__).resolve().parents[3]
    target = app_dir / "uploads" / "avatars"
    target.mkdir(parents=True, exist_ok=True)
    return target


async def get_or_create_preferences(
    db: AsyncSession,
    *,
    user_id,
) -> PreferenceUtilisateur:

    result = await db.execute(
        select(PreferenceUtilisateur).where(
            PreferenceUtilisateur.utilisateur_id == user_id
        )
    )

    preferences = result.scalar_one_or_none()

    if preferences is None:
        preferences = PreferenceUtilisateur(
            utilisateur_id=user_id,
        )
        db.add(preferences)
        await db.flush()

    return preferences


async def get_avatar_document(
    db: AsyncSession,
    *,
    preferences: PreferenceUtilisateur,
) -> Document | None:

    if preferences.avatar_document_id is None:
        return None

    result = await db.execute(
        select(Document).where(
            Document.id == preferences.avatar_document_id
        )
    )

    return result.scalar_one_or_none()


@avatar_router.post("/avatar")
async def upload_my_avatar(
    file: UploadFile = File(...),
    context: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Remplace l'avatar de l'utilisateur courant.

    - PNG / JPEG uniquement ;
    - 3 Mo maximum ;
    - document privé ;
    - ancien avatar conservé mais marqué INACTIF ;
    - aucun accès à l'avatar d'un autre utilisateur.
    """

    mime_type = (file.content_type or "").lower().strip()

    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Format accepté : PNG, JPG ou JPEG.",
        )

    content = await file.read(MAX_AVATAR_BYTES + 1)

    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="La photo de profil ne doit pas dépasser 3 Mo.",
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le fichier est vide.",
        )

    preferences = await get_or_create_preferences(
        db,
        user_id=context.user.id,
    )

    previous = await get_avatar_document(
        db,
        preferences=preferences,
    )

    extension = ALLOWED_MIME_TYPES[mime_type]
    storage_name = f"{context.user.id}_{uuid4().hex}{extension}"
    storage_path = avatar_storage_dir() / storage_name
    storage_path.write_bytes(content)

    document = Document(
        type_document="AVATAR_UTILISATEUR",
        nom_original=file.filename or storage_name,
        nom_stockage=storage_name,
        chemin_stockage=str(storage_path),
        format="PNG" if mime_type == "image/png" else "JPEG",
        taille_octets=len(content),
        checksum=sha256(content).hexdigest(),
        version="1",
        ressource_type="UTILISATEUR",
        ressource_id=context.user.id,
        confidentialite="PRIVE",
        source="MON_COMPTE",
        date_document=date.today(),
        depose_par_id=context.user.id,
        date_depot=date.today(),
        statut_verification="NON_REQUIS",
        statut="ACTIF",
    )

    db.add(document)
    await db.flush()

    preferences.avatar_document_id = document.id

    if previous is not None:
        previous.statut = "INACTIF"

    await db.commit()

    return {
        "avatar_document_id": str(document.id),
        "content_type": mime_type,
    }


@avatar_router.get("/avatar")
async def download_my_avatar(
    context: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Retourne uniquement l'avatar du compte authentifié.
    """

    preferences = await get_or_create_preferences(
        db,
        user_id=context.user.id,
    )

    document = await get_avatar_document(
        db,
        preferences=preferences,
    )

    if document is None or str(document.statut or "").upper() != "ACTIF":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun avatar configuré.",
        )

    path = Path(document.chemin_stockage)

    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Le fichier avatar est introuvable.",
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


@avatar_router.delete(
    "/avatar",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_my_avatar(
    context: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Retire l'avatar courant sans suppression physique définitive.
    """

    preferences = await get_or_create_preferences(
        db,
        user_id=context.user.id,
    )

    document = await get_avatar_document(
        db,
        preferences=preferences,
    )

    if document is not None:
        document.statut = "INACTIF"

    preferences.avatar_document_id = None

    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
