"""Ajoute les droits de consultation de dossier à DIRECTION_TECHNIQUE.

La Direction technique suit les collectes et vérifications sans exécuter les
actions opérationnelles de ces deux modules.

Usage : python -m app.scripts.sync_direction_consultation_dossiers
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


ROLE_CODE = "DIRECTION_TECHNIQUE"
PERMISSION_CODES = ("COLLECTE.LIRE", "VERIFICATION.LIRE")


async def run() -> None:
    async with AsyncSessionLocal() as db:
        try:
            role = await db.scalar(select(Role).where(Role.code == ROLE_CODE))
            if role is None:
                raise RuntimeError(f"Rôle absent : {ROLE_CODE}")
            permissions = {
                item.code: item
                for item in (
                    await db.execute(
                        select(Permission).where(Permission.code.in_(PERMISSION_CODES))
                    )
                ).scalars()
            }
            missing_catalog = set(PERMISSION_CODES) - set(permissions)
            if missing_catalog:
                raise RuntimeError(
                    "Permissions absentes du catalogue : "
                    + ", ".join(sorted(missing_catalog))
                )

            current = set(
                (
                    await db.execute(
                        select(Permission.code)
                        .join(RolePermission, RolePermission.permission_id == Permission.id)
                        .where(RolePermission.role_id == role.id)
                    )
                ).scalars()
            )
            added = []
            for code in PERMISSION_CODES:
                if code not in current:
                    db.add(RolePermission(role_id=role.id, permission_id=permissions[code].id))
                    added.append(code)
            await db.commit()
            print(
                "Synchronisation DIRECTION_TECHNIQUE terminée : "
                + (", ".join(added) if added else "droits déjà présents")
            )
        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    options = {"loop_factory": asyncio.SelectorEventLoop} if sys.platform == "win32" else {}
    asyncio.run(run(), **options)
