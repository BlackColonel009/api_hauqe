"""
Seed idempotent — présence utilisateurs.

Exécuter après intégration :

    python -m app.scripts.seed_presence_permission

Le menu reste invisible côté frontend si l'API retourne 403.
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


PERMISSION = (
    "PRESENCE.LIRE",
    "PRESENCE",
    "LIRE",
    "Consulter les utilisateurs actuellement ou récemment actifs.",
)

ROLE_CODES = {
    "ADMIN_HAUQE",
    "DIRECTION_TECHNIQUE",
    "POINT_FOCAL_BNEC",
    "VERIFICATEUR",
    "CONTROLEUR_FUCCS",
    "ADMIN_BNEC",
    "AGENT_COLLECTE",
    "CELLULE_VEILLE",
    "LECTEUR",
}


async def ensure_link(
    db,
    *,
    role_id,
    permission_id,
):
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id
            == permission_id,
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
            code, domaine, action, description = PERMISSION

            result = await db.execute(
                select(Permission).where(
                    Permission.code == code
                )
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

            for role_code in ROLE_CODES:
                result = await db.execute(
                    select(Role).where(
                        Role.code == role_code
                    )
                )

                role = result.scalar_one_or_none()

                if role is None:
                    print(
                        "Rôle absent, attribution ignorée : "
                        f"{role_code}"
                    )
                    continue

                await ensure_link(
                    db,
                    role_id=role.id,
                    permission_id=permission.id,
                )

            await db.commit()

            print(
                "Permission PRESENCE.LIRE synchronisée."
            )

        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(
            seed(),
            loop_factory=asyncio.SelectorEventLoop,
        )
    else:
        asyncio.run(seed())
