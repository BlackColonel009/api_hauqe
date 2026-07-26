"""
Seed idempotent des permissions Pilotage / Tableaux de bord.

IMPORTANT
---------
Exécuter après intégration du lot :

    python -m app.scripts.seed_dashboard_permissions

Sinon les routes internes retourneront 403 même si le code est correct.
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
    (
        "DASHBOARDS.LIRE_REFERENTIELS",
        "DASHBOARDS",
        "LIRE_REFERENTIELS",
        "Lire les filtres et définitions des indicateurs.",
    ),
    (
        "DASHBOARDS.OPERATIONNEL",
        "DASHBOARDS",
        "OPERATIONNEL",
        "Accéder au tableau de bord opérationnel.",
    ),
    (
        "DASHBOARDS.TACTIQUE",
        "DASHBOARDS",
        "TACTIQUE",
        "Accéder au tableau de bord tactique mensuel.",
    ),
    (
        "DASHBOARDS.STRATEGIQUE",
        "DASHBOARDS",
        "STRATEGIQUE",
        "Accéder au tableau de bord stratégique trimestriel.",
    ),
    (
        "DASHBOARDS.ANNUEL",
        "DASHBOARDS",
        "ANNUEL",
        "Accéder au bilan annuel institutionnel.",
    ),
    (
        "BAROMETRE.LIRE",
        "BAROMETRE",
        "LIRE",
        "Consulter le baromètre national des certifications.",
    ),
]


ROLE_MATRIX = {
    "DIRECTION_TECHNIQUE": {
        "DASHBOARDS.LIRE_REFERENTIELS",
        "DASHBOARDS.OPERATIONNEL",
        "DASHBOARDS.TACTIQUE",
        "DASHBOARDS.STRATEGIQUE",
        "DASHBOARDS.ANNUEL",
        "BAROMETRE.LIRE",
    },
    "POINT_FOCAL_BNEC": {
        "DASHBOARDS.LIRE_REFERENTIELS",
        "DASHBOARDS.OPERATIONNEL",
        "DASHBOARDS.TACTIQUE",
        "BAROMETRE.LIRE",
    },
    "ADMIN_BNEC": {
        "DASHBOARDS.LIRE_REFERENTIELS",
        "DASHBOARDS.OPERATIONNEL",
        "DASHBOARDS.TACTIQUE",
        "BAROMETRE.LIRE",
    },
    "CELLULE_VEILLE": {
        "DASHBOARDS.LIRE_REFERENTIELS",
        "DASHBOARDS.OPERATIONNEL",
        "DASHBOARDS.TACTIQUE",
        "BAROMETRE.LIRE",
    },
    "VERIFICATEUR": {
        "DASHBOARDS.LIRE_REFERENTIELS",
        "DASHBOARDS.OPERATIONNEL",
    },
    "CONTROLEUR_FUCCS": {
        "DASHBOARDS.LIRE_REFERENTIELS",
        "DASHBOARDS.OPERATIONNEL",
    },
    "AGENT_COLLECTE": {
        "DASHBOARDS.LIRE_REFERENTIELS",
        "DASHBOARDS.OPERATIONNEL",
    },
    "LECTEUR": {
        "DASHBOARDS.LIRE_REFERENTIELS",
        "DASHBOARDS.OPERATIONNEL",
        "BAROMETRE.LIRE",
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
                    print(f"Rôle absent, attribution ignorée : {role_code}")
                    continue

                for code in codes:
                    await ensure_link(
                        db,
                        role.id,
                        by_code[code].id,
                    )

            await db.commit()
            print("Permissions Pilotage / Tableaux de bord synchronisées.")

        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(seed(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(seed())
