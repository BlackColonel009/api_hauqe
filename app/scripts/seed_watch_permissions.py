"""
Seed idempotent des permissions Échéances / Alertes / Notifications / Veille.

La Cellule de Veille reçoit les droits opérationnels de suivi.
La Direction Technique supervise et valide les rapports.
L'administrateur HAUQE conserve l'ensemble des permissions.
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
    ("ECHEANCES.LIRE", "ECHEANCES", "LIRE", "Consulter les échéances."),
    ("ECHEANCES.GERER", "ECHEANCES", "GERER", "Planifier, modifier et clôturer les échéances."),

    ("ALERTES.LIRE", "ALERTES", "LIRE", "Consulter les alertes."),
    ("ALERTES.CREER", "ALERTES", "CREER", "Créer une alerte spéciale/manuelle."),
    ("ALERTES.GERER", "ALERTES", "GERER", "Modifier une alerte active."),
    ("ALERTES.AFFECTER", "ALERTES", "AFFECTER", "Affecter une alerte à un responsable."),
    ("ALERTES.RESOUDRE", "ALERTES", "RESOUDRE", "Résoudre ou clôturer une alerte."),

    ("NOTIFICATIONS.LIRE", "NOTIFICATIONS", "LIRE", "Consulter et marquer ses notifications."),
    ("NOTIFICATIONS.CREER", "NOTIFICATIONS", "CREER", "Créer des notifications liées à une alerte."),
    ("NOTIFICATIONS.TRANSPORT", "NOTIFICATIONS", "TRANSPORT", "Retenter et enregistrer le résultat d'un transport externe."),

    ("VEILLE.LIRE", "VEILLE", "LIRE", "Consulter l'espace CVC."),
    ("VEILLE.SCANNER", "VEILLE", "SCANNER", "Déclencher manuellement le scan quotidien."),
    ("VEILLE.GERER", "VEILLE", "GERER", "Créer et mettre à jour les dossiers de veille."),
    ("VEILLE.RELANCER", "VEILLE", "RELANCER", "Gérer les relances de veille."),
    ("VEILLE.CLOTURER", "VEILLE", "CLOTURER", "Clôturer un dossier de veille."),
    ("VEILLE.RAPPORTER", "VEILLE", "RAPPORTER", "Générer une note ou un rapport de veille."),
    ("VEILLE.VALIDER_RAPPORT", "VEILLE", "VALIDER_RAPPORT", "Valider un rapport de veille."),
]


ROLE_MATRIX = {
    "CELLULE_VEILLE": {
        "ECHEANCES.LIRE",
        "ECHEANCES.GERER",
        "ALERTES.LIRE",
        "ALERTES.CREER",
        "ALERTES.GERER",
        "ALERTES.AFFECTER",
        "ALERTES.RESOUDRE",
        "NOTIFICATIONS.LIRE",
        "NOTIFICATIONS.CREER",
        "VEILLE.LIRE",
        "VEILLE.SCANNER",
        "VEILLE.GERER",
        "VEILLE.RELANCER",
        "VEILLE.CLOTURER",
        "VEILLE.RAPPORTER",
    },
    "DIRECTION_TECHNIQUE": {
        "ECHEANCES.LIRE",
        "ALERTES.LIRE",
        "ALERTES.AFFECTER",
        "ALERTES.RESOUDRE",
        "NOTIFICATIONS.LIRE",
        "NOTIFICATIONS.CREER",
        "VEILLE.LIRE",
        "VEILLE.RAPPORTER",
        "VEILLE.VALIDER_RAPPORT",
    },
    "POINT_FOCAL_BNEC": {
        "ECHEANCES.LIRE",
        "ECHEANCES.GERER",
        "ALERTES.LIRE",
        "ALERTES.AFFECTER",
        "NOTIFICATIONS.LIRE",
        "VEILLE.LIRE",
    },
    "ADMIN_BNEC": {
        "ECHEANCES.LIRE",
        "ALERTES.LIRE",
        "NOTIFICATIONS.LIRE",
        "VEILLE.LIRE",
    },
    "VERIFICATEUR": {
        "NOTIFICATIONS.LIRE",
    },
    "CONTROLEUR_FUCCS": {
        "NOTIFICATIONS.LIRE",
    },
    "AGENT_COLLECTE": {
        "NOTIFICATIONS.LIRE",
    },
    "LECTEUR": {
        "ECHEANCES.LIRE",
        "ALERTES.LIRE",
        "NOTIFICATIONS.LIRE",
        "VEILLE.LIRE",
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
            print("Permissions Veille synchronisées.")

        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(seed(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(seed())
