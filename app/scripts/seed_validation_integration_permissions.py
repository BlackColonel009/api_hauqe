"""
Seed idempotent des permissions Validation + Intégration BNEC.

La séparation des fonctions est portée par les permissions :
- Point focal / superviseur : revue N1 ;
- Direction Technique : décision N2 ;
- Administrateur BNEC : intégration technique ;
- Agent de collecte : resoumission des corrections.

La matrice reste ensuite administrable via le module RBAC.
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


PERMISSIONS = [
    ("VALIDATION.LIRE", "VALIDATION", "LIRE", "Consulter validations et corrections."),
    ("VALIDATION.REVUE_N1", "VALIDATION", "REVUE_N1", "Prononcer la revue technique de premier niveau."),
    ("VALIDATION.DECIDER_N2", "VALIDATION", "DECIDER_N2", "Prononcer la validation définitive de second niveau."),
    ("VALIDATION.DEMANDER_CORRECTION", "VALIDATION", "DEMANDER_CORRECTION", "Créer et gérer une demande de correction."),
    ("VALIDATION.RESOUMETTRE_CORRECTION", "VALIDATION", "RESOUMETTRE_CORRECTION", "Répondre et resoumettre une correction."),

    ("INTEGRATION.LIRE", "INTEGRATION", "LIRE", "Consulter la file et les intégrations BNEC."),
    ("INTEGRATION.OUVRIR", "INTEGRATION", "OUVRIR", "Ouvrir une intégration depuis une validation finale favorable."),
    ("INTEGRATION.PRECONTROLER", "INTEGRATION", "PRECONTROLER", "Effectuer le précontrôle d'intégration."),
    ("INTEGRATION.EXECUTER", "INTEGRATION", "EXECUTER", "Préparer et traiter les éléments d'intégration."),
    ("INTEGRATION.POSTCONTROLER", "INTEGRATION", "POSTCONTROLER", "Effectuer le contrôle post-intégration."),
    ("INTEGRATION.CLOTURER", "INTEGRATION", "CLOTURER", "Clôturer une intégration BNEC réussie."),
]


ROLE_MATRIX = {
    "DIRECTION_TECHNIQUE": {
        "VALIDATION.LIRE",
        "VALIDATION.REVUE_N1",
        "VALIDATION.DECIDER_N2",
        "VALIDATION.DEMANDER_CORRECTION",
        "INTEGRATION.LIRE",
    },
    "POINT_FOCAL_BNEC": {
        "VALIDATION.LIRE",
        "VALIDATION.REVUE_N1",
        "VALIDATION.DEMANDER_CORRECTION",
        "INTEGRATION.LIRE",
    },
    "ADMIN_BNEC": {
        "VALIDATION.LIRE",
        "INTEGRATION.LIRE",
        "INTEGRATION.OUVRIR",
        "INTEGRATION.PRECONTROLER",
        "INTEGRATION.EXECUTER",
        "INTEGRATION.POSTCONTROLER",
        "INTEGRATION.CLOTURER",
    },
    "AGENT_COLLECTE": {
        "VALIDATION.LIRE",
        "VALIDATION.RESOUMETTRE_CORRECTION",
    },
    "LECTEUR": {
        "VALIDATION.LIRE",
        "INTEGRATION.LIRE",
    },
}


async def ensure_link(db, role_id, permission_id):
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
    )
    if result.scalar_one_or_none() is None:
        db.add(
            RolePermission(
                role_id=role_id,
                permission_id=permission_id,
            )
        )


async def seed():
    async with AsyncSessionLocal() as db:
        try:
            by_code = {}

            for code, domaine, action, description in PERMISSIONS:
                result = await db.execute(
                    select(Permission).where(Permission.code == code)
                )
                permission = result.scalar_one_or_none()

                if permission is None:
                    permission = Permission(
                        code=code,
                        domaine=domaine,
                        action=action,
                        description=description,
                    )
                    db.add(permission)
                    await db.flush()

                by_code[code] = permission

            admin_result = await db.execute(
                select(Role).where(Role.code == "ADMIN_HAUQE")
            )
            admin = admin_result.scalar_one_or_none()
            if admin is None:
                raise RuntimeError("Le rôle ADMIN_HAUQE est absent.")

            all_permissions = await db.execute(select(Permission))
            for permission in all_permissions.scalars().all():
                await ensure_link(db, admin.id, permission.id)

            for role_code, codes in ROLE_MATRIX.items():
                role_result = await db.execute(
                    select(Role).where(Role.code == role_code)
                )
                role = role_result.scalar_one_or_none()

                if role is None:
                    print(f"Rôle absent, ignoré : {role_code}")
                    continue

                for code in codes:
                    await ensure_link(db, role.id, by_code[code].id)

            await db.commit()
            print("Permissions Validation / Intégration BNEC synchronisées.")

        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(seed(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(seed())
