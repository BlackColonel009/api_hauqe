"""Accorde ORGANISMES.CREER au rôle AGENT_COLLECTE.

Cette synchronisation est idempotente : elle ajoute uniquement le droit
manquant et ne retire aucune permission configurée par la HAUQE.

Usage : python -m app.scripts.sync_agent_collecte_organismes_create
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


ROLE_CODE = "AGENT_COLLECTE"
PERMISSION_CODE = "ORGANISMES.CREER"


async def run() -> None:
    async with AsyncSessionLocal() as db:
        try:
            role = await db.scalar(select(Role).where(Role.code == ROLE_CODE))
            permission = await db.scalar(
                select(Permission).where(Permission.code == PERMISSION_CODE)
            )
            if role is None:
                raise RuntimeError(f"Rôle absent : {ROLE_CODE}")
            if permission is None:
                raise RuntimeError(f"Permission absente : {PERMISSION_CODE}")

            exists = await db.scalar(
                select(RolePermission.id).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id,
                )
            )
            if exists is None:
                db.add(RolePermission(role_id=role.id, permission_id=permission.id))
                await db.commit()
                print("Droit ajouté : AGENT_COLLECTE -> ORGANISMES.CREER")
            else:
                print("Droit déjà présent : AGENT_COLLECTE -> ORGANISMES.CREER")
        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    options = {"loop_factory": asyncio.SelectorEventLoop} if sys.platform == "win32" else {}
    asyncio.run(run(), **options)
