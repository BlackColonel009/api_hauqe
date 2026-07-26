"""
Ajoute uniquement les permissions manquantes nécessaires au domaine
Organismes / Certifications / Documents.

Le script ne modifie pas le schéma et n'impose pas arbitrairement une matrice
métier aux rôles. Les nouvelles permissions sont simplement garanties pour
ADMIN_HAUQE afin de permettre les tests, puis peuvent être distribuées via
l'API RBAC déjà existante.
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
    ("ORGANISMES.CREER", "ORGANISMES", "CREER", "Créer un organisme certificateur."),
    ("ORGANISMES.MODIFIER", "ORGANISMES", "MODIFIER", "Modifier un organisme et ses accréditations."),
    ("CERTIFICATIONS.CREER", "CERTIFICATIONS", "CREER", "Créer une certification officielle."),
    ("CERTIFICATIONS.MODIFIER", "CERTIFICATIONS", "MODIFIER", "Modifier une certification et ses sous-modules."),
    ("DOCUMENTS.VERIFIER", "DOCUMENTS", "VERIFIER", "Vérifier, désactiver ou restaurer un document."),
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Permission))
            permissions = {p.code: p for p in result.scalars().all()}
            created = []

            for code, domaine, action, description in PERMISSIONS:
                if code in permissions:
                    continue

                permission = Permission(
                    code=code,
                    domaine=domaine,
                    action=action,
                    description=description,
                )
                db.add(permission)
                await db.flush()
                permissions[code] = permission
                created.append(code)

            admin_result = await db.execute(
                select(Role).where(Role.code == "ADMIN_HAUQE")
            )
            admin = admin_result.scalar_one_or_none()
            if admin is None:
                raise RuntimeError("Le rôle ADMIN_HAUQE est absent.")

            # ADMIN_HAUQE reste le filet de récupération : il possède tout le catalogue.
            for permission in permissions.values():
                link_result = await db.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == admin.id,
                        RolePermission.permission_id == permission.id,
                    )
                )
                if link_result.scalar_one_or_none() is None:
                    db.add(
                        RolePermission(
                            role_id=admin.id,
                            permission_id=permission.id,
                        )
                    )

            await db.commit()

            print(f"Permissions créées : {len(created)}")
            for code in created:
                print(f" - {code}")
            print("ADMIN_HAUQE possède toutes les permissions.")

        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(seed(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(seed())
