"""
Service métier de gestion rôle → permissions.

Responsabilités :
- contrôler l'existence du rôle ;
- contrôler l'existence de la permission ;
- empêcher les doublons ;
- empêcher la perte des droits critiques de ADMIN_HAUQE ;
- attribuer ou retirer une permission ;
- journaliser toute modification du RBAC.

IMPORTANT
---------
La table role_permission ne possède pas de champ "statut".

Le retrait d'une permission doit donc supprimer physiquement
l'association role_permission.

La traçabilité de cette suppression reste conservée dans :
    evenements_audit
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.role_permission import RolePermission
from app.repositories.role_repository import RoleRepository
from app.schemas.role import (
    PermissionResponse,
    RolePermissionsResponse,
)
from app.services.auth_service import AuthContext


# ============================================================
# IP CLIENT
# ============================================================

def client_ip(
    request: Request,
) -> str | None:
    """
    Adresse IP vue actuellement par FastAPI.

    La gestion avancée des proxies de confiance sera traitée
    plus tard avec Nginx / X-Forwarded-For.
    """

    if request.client is None:
        return None

    return request.client.host


# ============================================================
# SERIALISATION D'UNE MATRICE
# ============================================================

async def build_role_permissions_response(
    db: AsyncSession,
    role,
) -> RolePermissionsResponse:
    """
    Construit la réponse API complète du rôle.
    """

    permissions = (
        await RoleRepository
        .get_permissions_for_role(
            db,
            role.id,
        )
    )

    return RolePermissionsResponse(
        role_id=role.id,
        role_code=role.code,
        role_libelle=role.libelle,
        permissions=[
            PermissionResponse(
                id=permission.id,
                code=permission.code,
                domaine=permission.domaine,
                action=permission.action,
                description=permission.description,
            )
            for permission in permissions
        ],
    )


# ============================================================
# SERVICE
# ============================================================

class RolePermissionService:

    # ========================================================
    # CONSULTATION
    # ========================================================

    @staticmethod
    async def get_role_permissions(
        db: AsyncSession,
        *,
        role_id: UUID,
    ) -> RolePermissionsResponse:
        """
        Retourne la matrice d'un rôle.
        """

        role = await RoleRepository.get_role_by_id(
            db,
            role_id,
        )

        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rôle introuvable.",
            )

        return await build_role_permissions_response(
            db,
            role,
        )


    # ========================================================
    # ATTRIBUTION
    # ========================================================

    @staticmethod
    async def assign_permission(
        db: AsyncSession,
        *,
        role_id: UUID,
        permission_id: UUID,
        actor: AuthContext,
        request: Request,
    ) -> RolePermissionsResponse:
        """
        Attribue une permission existante à un rôle existant.

        La modification prend effet dès la prochaine requête
        authentifiée des utilisateurs possédant ce rôle.
        """

        # ----------------------------------------------------
        # Vérification du rôle
        # ----------------------------------------------------

        role = await RoleRepository.get_role_by_id(
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
        ).strip().upper() != "ACTIF":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Le rôle n'est pas actif.",
            )

        # ----------------------------------------------------
        # Vérification de la permission
        # ----------------------------------------------------

        permission = (
            await RoleRepository.get_permission_by_id(
                db,
                permission_id,
            )
        )

        if permission is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission introuvable.",
            )

        # ----------------------------------------------------
        # Protection contre les doublons
        # ----------------------------------------------------

        existing = (
            await RoleRepository
            .get_role_permission(
                db,
                role_id=role.id,
                permission_id=permission.id,
            )
        )

        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cette permission est déjà attribuée "
                    "à ce rôle."
                ),
            )

        # ----------------------------------------------------
        # Création du lien
        # ----------------------------------------------------

        link = RolePermission(
            role_id=role.id,
            permission_id=permission.id,
        )

        db.add(link)

        await db.flush()

        # ----------------------------------------------------
        # Audit
        #
        # L'acteur est l'administrateur ayant effectué
        # la modification.
        # ----------------------------------------------------

        await write_audit_event(
            db,
            action="ROLE_PERMISSION_ASSIGN",
            categorie="HABILITATION",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="role_permission",
            ressource_id=link.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "role_id": str(role.id),
                "role_code": role.code,
                "permission_id": str(
                    permission.id
                ),
                "permission_code":
                    permission.code,
            },
        )

        await db.commit()

        return await build_role_permissions_response(
            db,
            role,
        )


    # ========================================================
    # RETRAIT
    # ========================================================

    @staticmethod
    async def remove_permission(
        db: AsyncSession,
        *,
        role_id: UUID,
        permission_id: UUID,
        actor: AuthContext,
        request: Request,
    ) -> RolePermissionsResponse:
        """
        Retire une permission d'un rôle.

        ADMIN_HAUQE constitue notre compte de récupération
        administrative et doit toujours conserver toutes les
        permissions du système.
        """

        role = await RoleRepository.get_role_by_id(
            db,
            role_id,
        )

        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rôle introuvable.",
            )

        # ----------------------------------------------------
        # Protection critique ADMIN_HAUQE
        # ----------------------------------------------------

        if role.code == "ADMIN_HAUQE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Les permissions de ADMIN_HAUQE "
                    "ne peuvent pas être retirées."
                ),
            )

        permission = (
            await RoleRepository.get_permission_by_id(
                db,
                permission_id,
            )
        )

        if permission is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission introuvable.",
            )

        link = (
            await RoleRepository
            .get_role_permission(
                db,
                role_id=role.id,
                permission_id=permission.id,
            )
        )

        if link is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Cette permission n'est pas "
                    "attribuée à ce rôle."
                ),
            )

        # ----------------------------------------------------
        # Conserver les informations AVANT suppression.
        # ----------------------------------------------------

        link_id = link.id

        before = {
            "role_id": str(role.id),
            "role_code": role.code,
            "permission_id": str(permission.id),
            "permission_code": permission.code,
        }

        # ----------------------------------------------------
        # Le MPD ne prévoit pas de statut sur role_permission.
        # La suppression physique du lien est donc normale.
        # L'historique métier reste dans evenements_audit.
        # ----------------------------------------------------

        await db.delete(link)

        await write_audit_event(
            db,
            action="ROLE_PERMISSION_REMOVE",
            categorie="HABILITATION",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="role_permission",
            ressource_id=link_id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
        )

        await db.commit()

        return await build_role_permissions_response(
            db,
            role,
        )