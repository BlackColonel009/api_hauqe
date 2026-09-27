"""Synchronise le rôle VERIFICATEUR avec la décision RACI en vigueur.

Le vérificateur consulte les collectes, sans pouvoir les modifier, les
soumettre ou organiser l'affectation des vérificateurs.

Usage : python -m app.scripts.sync_verificateur_collecte_read
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import delete, select

from app.database.session import AsyncSessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


ROLE_CODE = "VERIFICATEUR"
READ_PERMISSION = "COLLECTE.LIRE"
REVOKED_PERMISSION = "VERIFICATION.AFFECTER"


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
                        select(Permission).where(
                            Permission.code.in_([READ_PERMISSION, REVOKED_PERMISSION])
                        )
                    )
                ).scalars()
            }
            if READ_PERMISSION not in permissions:
                raise RuntimeError(f"Permission absente : {READ_PERMISSION}")

            read_link = await db.scalar(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permissions[READ_PERMISSION].id,
                )
            )
            added = read_link is None
            if added:
                db.add(RolePermission(role_id=role.id, permission_id=permissions[READ_PERMISSION].id))

            removed = 0
            if REVOKED_PERMISSION in permissions:
                result = await db.execute(
                    delete(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == permissions[REVOKED_PERMISSION].id,
                    )
                )
                removed = result.rowcount or 0

            await db.commit()
            print(
                "Synchronisation VERIFICATEUR terminée : "
                f"COLLECTE.LIRE {'ajoutée' if added else 'déjà présente'} ; "
                f"VERIFICATION.AFFECTER retirée : {removed}."
            )
        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    options = {"loop_factory": asyncio.SelectorEventLoop} if sys.platform == "win32" else {}
    asyncio.run(run(), **options)
