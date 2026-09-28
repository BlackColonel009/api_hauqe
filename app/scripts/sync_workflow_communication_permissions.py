"""Synchronisation ciblée et additive des droits de communication/CVC.

Aucune permission n'est retirée. À lancer une fois après le déploiement du code.
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


CVC_CODES = {
    "SCORING.LIRE",
    "CLASSIFICATION.LIRE",
    "CLASSIFICATION.CALCULER_VALIDER",
    "INFC.LIRE",
    "INFC.CALCULER",
    "INFC.VALIDER",
    "SNCC.LIRE",
    "SNCC.CLASSER",
    "SNCC.RECLASSER",
}


async def sync() -> None:
    async with AsyncSessionLocal() as db:
        roles = (await db.execute(select(Role))).scalars().all()
        permissions = {
            item.code: item for item in (
                await db.execute(select(Permission).where(
                    Permission.code.in_(CVC_CODES | {"NOTIFICATIONS.LIRE"})
                ))
            ).scalars().all()
        }
        missing = (CVC_CODES | {"NOTIFICATIONS.LIRE"}) - permissions.keys()
        for code in sorted(missing):
            domaine, action = code.split(".", 1)
            item = Permission(
                code=code, domaine=domaine, action=action,
                description="Permission utilisée par la communication du parcours SNGSC.",
            )
            db.add(item)
            permissions[code] = item
        if missing:
            await db.flush()
        if not any(role.code == "CELLULE_VEILLE" for role in roles):
            raise RuntimeError("Rôle CELLULE_VEILLE absent ; aucune attribution n'a été validée.")

        grants = 0
        for role in roles:
            codes = {"NOTIFICATIONS.LIRE"}
            if role.code == "CELLULE_VEILLE":
                codes |= CVC_CODES
            for code in codes:
                exists = await db.scalar(select(RolePermission.id).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permissions[code].id,
                ))
                if exists is None:
                    db.add(RolePermission(role_id=role.id, permission_id=permissions[code].id))
                    grants += 1
        await db.commit()
        print(f"Communication/CVC : {len(missing)} permission(s) créée(s), {grants} association(s) ajoutée(s), aucune retirée.")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(sync(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(sync())
