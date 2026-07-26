"""
Dépendances d'authentification et d'autorisation FastAPI.

Ce fichier est le point de contrôle central des routes privées.

Chaîne de contrôle :

Bearer token
    ↓
hash SHA-256
    ↓
session PostgreSQL
    ↓
révocation ?
    ↓
expiration absolue ?
    ↓
expiration par inactivité ?
    ↓
utilisateur actif ?
    ↓
rôles
    ↓
permissions
    ↓
accès autorisé
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from fastapi import (
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.repositories.auth_repository import (
    AuthRepository,
)
from app.services.auth_service import (
    AuthContext,
)
from app.services.session_security_service import (
    SessionSecurityService,
)
from app.utils.security import (
    hash_access_token,
)

from app.services.account_session_lock_guard import (
    ensure_session_not_screen_locked,
)


# ============================================================
# SCHEMA BEARER POUR FASTAPI / SWAGGER
# ============================================================

bearer_scheme = HTTPBearer(
    auto_error=False
)



def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# UTILITAIRE 401
# ============================================================

def unauthorized(
    message: str,
) -> HTTPException:
    """
    Uniformise les réponses d'authentification refusée.
    """

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )


# ============================================================
# UTILISATEUR AUTHENTIFIE
# ============================================================

async def get_current_auth(
    request: Request,

    credentials: (
        HTTPAuthorizationCredentials | None
    ) = Depends(bearer_scheme),

    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    """
    Valide complètement une session utilisateur.

    Cette dépendance doit protéger toutes les routes
    nécessitant une authentification.
    """

    # --------------------------------------------------------
    # 1. Présence du Bearer token
    # --------------------------------------------------------

    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not credentials.credentials
    ):
        raise unauthorized(
            "Authentification requise."
        )

    # --------------------------------------------------------
    # 2. Le token brut n'est jamais recherché en base.
    #
    # Seul son hash SHA-256 est stocké dans
    # sessions_utilisateur.jeton_hash.
    # --------------------------------------------------------

    token_hash = hash_access_token(
        credentials.credentials
    )

    db_session = (
        await AuthRepository
        .get_session_by_token_hash(
            db,
            token_hash,
        )
    )

    if db_session is None:
        raise unauthorized(
            "Session invalide."
        )

    # --------------------------------------------------------
    # 3. Session déjà révoquée
    # --------------------------------------------------------

    if db_session.revoquee_at is not None:
        raise unauthorized(
            "Session révoquée."
        )

    now = utc_now()

    # --------------------------------------------------------
    # 4. Expiration absolue
    #
    # Exemple :
    # AUTH_SESSION_MINUTES=480
    #
    # Même si l'utilisateur reste actif, la session ne peut
    # pas dépasser cette échéance.
    # --------------------------------------------------------

    if (
        SessionSecurityService
        .is_absolute_expired(
            db_session,
            now=now,
        )
    ):

        await SessionSecurityService.revoke_session(
            db,
            session=db_session,
            request=request,
            reason="EXPIRATION_ABSOLUE",
            audit_action="AUTH_SESSION_EXPIRED",
        )

        raise unauthorized(
            "Session expirée."
        )

    # --------------------------------------------------------
    # 5. Verrouillage automatique pour inactivité
    #
    # Exemple :
    # AUTH_IDLE_TIMEOUT_MINUTES=30
    #
    # Après 30 minutes sans appel authentifié,
    # la session devient inutilisable.
    # --------------------------------------------------------

    if (
        SessionSecurityService
        .is_idle_expired(
            db_session,
            now=now,
        )
    ):

        await SessionSecurityService.revoke_session(
            db,
            session=db_session,
            request=request,
            reason="INACTIVITE_PROLONGEE",
            audit_action=(
                "AUTH_SESSION_IDLE_TIMEOUT"
            ),
        )

        raise unauthorized(
            "Session verrouillée pour inactivité."
        )

    # --------------------------------------------------------
    # 6. Utilisateur associé à la session
    # --------------------------------------------------------

    user = await AuthRepository.get_user_by_id(
        db,
        db_session.utilisateur_id,
    )

    if user is None:
        raise unauthorized(
            "Utilisateur introuvable."
        )

    # --------------------------------------------------------
    # 7. Le compte doit rester actif
    # --------------------------------------------------------

    if (
        user.statut or ""
    ).strip().upper() != "ACTIF":

        await SessionSecurityService.revoke_session(
            db,
            session=db_session,
            request=request,
            reason="COMPTE_NON_ACTIF",
            audit_action=(
                "AUTH_SESSION_ACCOUNT_DISABLED"
            ),
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte utilisateur non actif.",
        )

    # --------------------------------------------------------
    # 8. Verrouillage de reprise de session
    #
    # IMPORTANT :
    # Ce verrouillage n'est pas une expiration de session.
    # Le Bearer token reste valide mais les routes privées
    # sont bloquées jusqu'à saisie correcte du code privé.
    # --------------------------------------------------------

    await ensure_session_not_screen_locked(
        db,
        session=db_session,
        request=request,
    )

    # --------------------------------------------------------
    # 9. Rechargement des rôles et permissions
    # --------------------------------------------------------

    roles = await AuthRepository.get_roles(
        db,
        user.id,
    )

    permissions = (
        await AuthRepository.get_permissions(
            db,
            user.id,
        )
    )

    # --------------------------------------------------------
    # 10. Actualisation de l'activité
    # --------------------------------------------------------

    await SessionSecurityService.touch(
        db,
        session=db_session,
    )

    # --------------------------------------------------------
    # 11. Contexte transmis aux routes protégées
    # --------------------------------------------------------

    return AuthContext(
        user=user,
        db_session=db_session,
        roles=roles,
        permissions=permissions,
    )


# ============================================================
# CONTROLE D'UNE PERMISSION
# ============================================================

def require_permission(
    permission_code: str,
) -> Callable:
    """
    Génère une dépendance FastAPI imposant une permission.

    Exemple :

        Depends(
            require_permission(
                "ENTREPRISES.CREER"
            )
        )
    """

    async def dependency(
        context: AuthContext = Depends(
            get_current_auth
        ),
    ) -> AuthContext:

        if (
            permission_code
            not in context.permissions
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Permission insuffisante."
                ),
            )

        return context

    return dependency