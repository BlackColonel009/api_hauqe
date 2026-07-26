"""
Seed idempotent des permissions Scoring / Classification / INFC / SNCC.

La matrice initiale est volontairement prudente.
Elle reste modifiable ensuite avec l'API RBAC déjà développée.
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
    ("SCORING.LIRE", "SCORING", "LIRE", "Consulter modèles et pondérations de scoring."),
    ("SCORING.ADMINISTRER_MODELE", "SCORING", "ADMINISTRER_MODELE", "Créer, versionner, publier et retirer les modèles de scoring."),

    ("CLASSIFICATION.LIRE", "CLASSIFICATION", "LIRE", "Consulter l'historique des classifications entreprise."),
    ("CLASSIFICATION.CALCULER_VALIDER", "CLASSIFICATION", "CALCULER_VALIDER", "Calculer et enregistrer une classification entreprise validée."),

    ("INFC.LIRE", "INFC", "LIRE", "Consulter les résultats INFC."),
    ("INFC.CALCULER", "INFC", "CALCULER", "Calculer un résultat INFC depuis un modèle publié."),
    ("INFC.VALIDER", "INFC", "VALIDER", "Valider un résultat INFC calculé."),

    ("SNCC.LIRE", "SNCC", "LIRE", "Consulter les classements SNCC."),
    ("SNCC.CLASSER", "SNCC", "CLASSER", "Créer le premier classement SNCC d'une certification."),
    ("SNCC.RECLASSER", "SNCC", "RECLASSER", "Reclasser ou clôturer un classement SNCC."),
]


ROLE_MATRIX = {
    "DIRECTION_TECHNIQUE": {
        "SCORING.LIRE",
        "SCORING.ADMINISTRER_MODELE",
        "CLASSIFICATION.LIRE",
        "CLASSIFICATION.CALCULER_VALIDER",
        "INFC.LIRE",
        "INFC.VALIDER",
        "SNCC.LIRE",
        "SNCC.CLASSER",
        "SNCC.RECLASSER",
    },
    "POINT_FOCAL_BNEC": {
        "SCORING.LIRE",
        "CLASSIFICATION.LIRE",
        "INFC.LIRE",
        "INFC.CALCULER",
        "SNCC.LIRE",
    },
    "ADMIN_BNEC": {
        "SCORING.LIRE",
        "CLASSIFICATION.LIRE",
        "INFC.LIRE",
        "SNCC.LIRE",
    },
    "VERIFICATEUR": {
        "CLASSIFICATION.LIRE",
        "INFC.LIRE",
        "SNCC.LIRE",
    },
    "CONTROLEUR_FUCCS": {
        "CLASSIFICATION.LIRE",
        "INFC.LIRE",
        "SNCC.LIRE",
    },
    "LECTEUR": {
        "CLASSIFICATION.LIRE",
        "INFC.LIRE",
        "SNCC.LIRE",
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

            all_permissions_result = await db.execute(select(Permission))
            for permission in all_permissions_result.scalars().all():
                await ensure_link(db, admin.id, permission.id)

            for role_code, codes in ROLE_MATRIX.items():
                role_result = await db.execute(
                    select(Role).where(Role.code == role_code)
                )
                role = role_result.scalar_one_or_none()

                if role is None:
                    print(f"Rôle absent, attribution ignorée : {role_code}")
                    continue

                for code in codes:
                    await ensure_link(
                        db,
                        role.id,
                        by_code[code].id,
                    )

            await db.commit()
            print("Permissions Scoring / Classification / INFC / SNCC synchronisées.")

        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(seed(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(seed())
