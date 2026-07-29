"""
Logique métier d'administration des utilisateurs.

Ce service protège les invariants fonctionnels :

- unicité de l'email ;
- hash Argon2 avant stockage ;
- statut utilisateur contrôlé ;
- attribution de rôle sans doublon ;
- désactivation = révocation immédiate des sessions ;
- journalisation des actions sensibles.

Les routes FastAPI restent volontairement fines.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.utilisateur import Utilisateur
from app.models.utilisateur_role import UtilisateurRole
from app.repositories.user_repository import (
    UserRepository,
)
from app.schemas.user import (
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.utils.security import hash_password


# ============================================================
# HORLOGE UTC
# ============================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# ADRESSE IP
# ============================================================

def client_ip(
    request: Request,
) -> str | None:

    if request.client is None:
        return None

    return request.client.host


# ============================================================
# SERIALISATION
# ============================================================

async def build_user_response(
    db: AsyncSession,
    user: Utilisateur,
) -> UserResponse:
    """
    Construit une réponse API sans jamais exposer
    mot_de_passe_hash.
    """

    roles = (
        await UserRepository
        .get_role_codes_for_user(
            db,
            user.id,
        )
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        nom=user.nom,
        prenoms=user.prenoms,
        telephone=user.telephone,
        fonction=user.fonction,
        statut=user.statut,
        mfa_active=user.mfa_active,
        derniere_connexion_at=(
            user.derniere_connexion_at
        ),
        roles=roles,
    )


# ============================================================
# SERVICE
# ============================================================

class UserService:

    # ========================================================
    # LISTE
    # ========================================================

    @staticmethod
    async def list_users(
        db: AsyncSession,
    ) -> list[UserResponse]:

        users = await UserRepository.list_users(
            db
        )

        responses = []

        for user in users:
            responses.append(
                await build_user_response(
                    db,
                    user,
                )
            )

        return responses


    # ========================================================
    # DETAIL
    # ========================================================

    @staticmethod
    async def get_user(
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> UserResponse:

        user = await UserRepository.get_user_by_id(
            db,
            user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur introuvable.",
            )

        return await build_user_response(
            db,
            user,
        )


    # ========================================================
    # CREATION
    # ========================================================

    @staticmethod
    async def create_user(
        db: AsyncSession,
        *,
        payload: UserCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> UserResponse:
        """
        Crée un compte utilisateur.

        Le mot de passe est transformé en Argon2 avant
        toute insertion en base.
        """

        email = (
            payload.email
            .strip()
            .lower()
        )

        existing = (
            await UserRepository
            .get_user_by_email(
                db,
                email,
            )
        )

        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Un utilisateur avec cet email "
                    "existe déjà."
                ),
            )

        normalized_status = (
            payload.statut
            .strip()
            .upper()
        )

        if normalized_status not in {
            "ACTIF",
            "INACTIF",
        }:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail="Statut utilisateur invalide.",
            )

        user = Utilisateur(
            email=email,

            # Le mot de passe en clair disparaît ici.
            mot_de_passe_hash=hash_password(
                payload.password
            ),

            nom=payload.nom,
            prenoms=payload.prenoms,
            telephone=payload.telephone,
            fonction=payload.fonction,

            statut=normalized_status,

            # MFA sera implémenté dans un bloc dédié.
            mfa_active=False,
        )

        db.add(user)

        await db.flush()

        # ----------------------------------------------------
        # Journalisation
        #
        # IMPORTANT :
        # le mot de passe et son hash ne sont jamais
        # enregistrés dans l'audit.
        # ----------------------------------------------------

        await write_audit_event(
            db,
            action="USER_CREATE",
            categorie="ADMINISTRATION",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="utilisateur",
            ressource_id=user.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "email": user.email,
                "nom": user.nom,
                "prenoms": user.prenoms,
                "fonction": user.fonction,
                "statut": user.statut,
            },
        )

        await db.commit()

        return await build_user_response(
            db,
            user,
        )


    # ========================================================
    # MODIFICATION
    # ========================================================

    @staticmethod
    async def update_user(
        db: AsyncSession,
        *,
        user_id: UUID,
        payload: UserUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> UserResponse:

        user = await UserRepository.get_user_by_id(
            db,
            user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur introuvable.",
            )

        before = {
            "nom": user.nom,
            "prenoms": user.prenoms,
            "telephone": user.telephone,
            "fonction": user.fonction,
        }

        changes = payload.model_dump(
            exclude_unset=True
        )

        for field, value in changes.items():
            setattr(
                user,
                field,
                value,
            )

        await write_audit_event(
            db,
            action="USER_UPDATE",
            categorie="ADMINISTRATION",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="utilisateur",
            ressource_id=user.id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
            valeurs_apres={
                "nom": user.nom,
                "prenoms": user.prenoms,
                "telephone": user.telephone,
                "fonction": user.fonction,
            },
        )

        await db.commit()

        return await build_user_response(
            db,
            user,
        )


    # ========================================================
    # ACTIVATION / DESACTIVATION
    # ========================================================

    @staticmethod
    async def change_status(
        db: AsyncSession,
        *,
        user_id: UUID,
        new_status: str,
        motif: str | None,
        actor: AuthContext,
        request: Request,
    ) -> UserResponse:
        """
        Une désactivation doit prendre effet immédiatement.

        Toutes les sessions actives du compte sont donc
        révoquées dans la même transaction.
        """

        user = await UserRepository.get_user_by_id(
            db,
            user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur introuvable.",
            )

        normalized = (
            new_status
            .strip()
            .upper()
        )

        if normalized not in {
            "ACTIF",
            "INACTIF",
        }:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail="Statut utilisateur invalide.",
            )

        # Protection contre une auto-désactivation accidentelle.
        if (
            user.id == actor.user.id
            and normalized == "INACTIF"
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Vous ne pouvez pas désactiver "
                    "votre propre compte."
                ),
            )

        old_status = user.statut

        user.statut = normalized

        revoked_sessions = 0

        if normalized == "INACTIF":

            revoked_sessions = (
                await UserRepository
                .revoke_active_sessions(
                    db,
                    user_id=user.id,
                    revoked_at=utc_now(),
                )
            )

        await write_audit_event(
            db,
            action="USER_STATUS_CHANGE",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="utilisateur",
            ressource_id=user.id,
            adresse_ip=client_ip(request),
            valeurs_avant={
                "statut": old_status,
            },
            valeurs_apres={
                "statut": normalized,
                "sessions_revoquees":
                    revoked_sessions,
            },
            contexte={
                "motif": motif,
            },
        )

        await db.commit()

        return await build_user_response(
            db,
            user,
        )


    # ========================================================
    # ATTRIBUTION DE ROLE
    # ========================================================

    @staticmethod
    async def assign_role(
        db: AsyncSession,
        *,
        user_id: UUID,
        role_id: UUID,
        motif: str | None,
        actor: AuthContext,
        request: Request,
    ) -> UserResponse:

        user = await UserRepository.get_user_by_id(
            db,
            user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur introuvable.",
            )

        role = await UserRepository.get_role_by_id(
            db,
            role_id,
        )

        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rôle introuvable.",
            )

        if (
            role.statut or ""
        ).upper() != "ACTIF":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ce rôle n'est pas actif.",
            )

        existing = (
            await UserRepository
            .get_role_assignment(
                db,
                user_id=user.id,
                role_id=role.id,
            )
        )

        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Ce rôle est déjà attribué "
                    "à cet utilisateur."
                ),
            )

        assignment = UtilisateurRole(
            utilisateur_id=user.id,
            role_id=role.id,
            attribue_par_id=actor.user.id,
            motif=motif,
            statut="ACTIF",
        )

        db.add(assignment)

        await db.flush()

        await write_audit_event(
            db,
            action="USER_ROLE_ASSIGN",
            categorie="HABILITATION",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="utilisateur_role",
            ressource_id=assignment.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "utilisateur_id": str(user.id),
                "role_id": str(role.id),
                "role_code": role.code,
            },
            contexte={
                "motif": motif,
            },
        )

        await db.commit()

        return await build_user_response(
            db,
            user,
        )


    # ========================================================
    # RETRAIT DE ROLE
    # ========================================================

    @staticmethod
    async def remove_role(
        db: AsyncSession,
        *,
        user_id: UUID,
        role_id: UUID,
        actor: AuthContext,
        request: Request,
    ) -> UserResponse:
        """
        Le lien n'est pas supprimé physiquement.

        On le désactive afin de conserver la traçabilité
        de l'habilitation.
        """

        user = await UserRepository.get_user_by_id(
            db,
            user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur introuvable.",
            )

        assignment = (
            await UserRepository
            .get_role_assignment(
                db,
                user_id=user_id,
                role_id=role_id,
            )
        )

        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Cette attribution de rôle "
                    "n'existe pas."
                ),
            )

        role = await UserRepository.get_role_by_id(
            db,
            role_id,
        )

        # Le compte de récupération administrative ne doit pas
        # pouvoir retirer son propre rôle ADMIN_HAUQE.
        if (
            user.id == actor.user.id
            and role is not None
            and role.code == "ADMIN_HAUQE"
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Vous ne pouvez pas retirer ADMIN_HAUQE "
                    "de votre propre compte."
                ),
            )

        assignment.statut = "INACTIF"
        assignment.date_fin = utc_now().date()

        await write_audit_event(
            db,
            action="USER_ROLE_REMOVE",
            categorie="HABILITATION",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="utilisateur_role",
            ressource_id=assignment.id,
            adresse_ip=client_ip(request),
            valeurs_avant={
                "statut": "ACTIF",
                "role_code": (
                    role.code if role else None
                ),
            },
            valeurs_apres={
                "statut": "INACTIF",
            },
        )

        await db.commit()

        return await build_user_response(
            db,
            user,
        )