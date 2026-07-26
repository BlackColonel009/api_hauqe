"""
Seed idempotent des permissions Gouvernance / Qualité / Continuité.

IMPORTANT
---------
Exécuter ce seed immédiatement après intégration du lot, avant de tester
les endpoints, sinon les routes retourneront correctement 403.

Commande :
    python -m app.scripts.seed_governance_permissions
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
    ("GOUVERNANCE.LIRE", "GOUVERNANCE", "LIRE", "Consulter le tableau de gouvernance et les règles métier."),
    ("GOUVERNANCE.ADMINISTRER_REGLES", "GOUVERNANCE", "ADMINISTRER_REGLES", "Créer, versionner, publier et retirer les règles métier."),

    ("QUALITE.LIRE", "QUALITE", "LIRE", "Consulter les revues qualité et plans d'action."),
    ("QUALITE.GERER", "QUALITE", "GERER", "Préparer les revues qualité et gérer les plans d'action."),
    ("QUALITE.VALIDER", "QUALITE", "VALIDER", "Valider une revue qualité et clôturer un plan d'action."),

    ("DECISIONS.LIRE", "DECISIONS", "LIRE", "Consulter les décisions institutionnelles."),
    ("DECISIONS.PREPARER", "DECISIONS", "PREPARER", "Préparer et soumettre une note de décision."),
    ("DECISIONS.PRONONCER", "DECISIONS", "PRONONCER", "Prononcer une décision institutionnelle."),

    ("PUBLICATIONS.LIRE", "PUBLICATIONS", "LIRE", "Consulter les demandes et publications."),
    ("PUBLICATIONS.DEMANDER", "PUBLICATIONS", "DEMANDER", "Préparer et soumettre une demande de publication."),
    ("PUBLICATIONS.APPROUVER", "PUBLICATIONS", "APPROUVER", "Approuver ou rejeter une publication."),
    ("PUBLICATIONS.PUBLIER", "PUBLICATIONS", "PUBLIER", "Publier ou retirer une ressource approuvée."),

    ("RAPPORTS.LIRE", "RAPPORTS", "LIRE", "Consulter les rapports demandés et générés."),
    ("RAPPORTS.DEMANDER", "RAPPORTS", "DEMANDER", "Demander la génération d'un rapport."),
    ("RAPPORTS.GENERER", "RAPPORTS", "GENERER", "Piloter/finaliser une tâche de génération de rapport."),

    ("AUDIT.LIRE", "AUDIT", "LIRE", "Consulter le journal d'audit immuable."),

    ("ARCHIVES.LIRE", "ARCHIVES", "LIRE", "Consulter le registre des archives."),
    ("ARCHIVES.CREER", "ARCHIVES", "CREER", "Créer une inscription d'archivage motivée."),

    ("SAUVEGARDES.LIRE", "SAUVEGARDES", "LIRE", "Consulter politiques, exécutions et tests de restauration."),
    ("SAUVEGARDES.GERER", "SAUVEGARDES", "GERER", "Administrer le registre des sauvegardes et tests de restauration."),

    ("INCIDENTS.LIRE", "INCIDENTS", "LIRE", "Consulter les incidents."),
    ("INCIDENTS.DECLARER", "INCIDENTS", "DECLARER", "Déclarer un incident."),
    ("INCIDENTS.GERER", "INCIDENTS", "GERER", "Affecter, modifier et résoudre un incident."),
    ("INCIDENTS.CLOTURER", "INCIDENTS", "CLOTURER", "Clôturer un incident résolu."),
]


ROLE_MATRIX = {
    "DIRECTION_TECHNIQUE": {
        "GOUVERNANCE.LIRE",
        "GOUVERNANCE.ADMINISTRER_REGLES",
        "QUALITE.LIRE",
        "QUALITE.GERER",
        "QUALITE.VALIDER",
        "DECISIONS.LIRE",
        "DECISIONS.PREPARER",
        "DECISIONS.PRONONCER",
        "PUBLICATIONS.LIRE",
        "PUBLICATIONS.DEMANDER",
        "PUBLICATIONS.APPROUVER",
        "PUBLICATIONS.PUBLIER",
        "RAPPORTS.LIRE",
        "RAPPORTS.DEMANDER",
        "AUDIT.LIRE",
        "ARCHIVES.LIRE",
        "ARCHIVES.CREER",
        "SAUVEGARDES.LIRE",
        "INCIDENTS.LIRE",
        "INCIDENTS.DECLARER",
        "INCIDENTS.GERER",
        "INCIDENTS.CLOTURER",
    },
    "POINT_FOCAL_BNEC": {
        "GOUVERNANCE.LIRE",
        "QUALITE.LIRE",
        "QUALITE.GERER",
        "DECISIONS.LIRE",
        "DECISIONS.PREPARER",
        "PUBLICATIONS.LIRE",
        "PUBLICATIONS.DEMANDER",
        "RAPPORTS.LIRE",
        "RAPPORTS.DEMANDER",
        "ARCHIVES.LIRE",
        "INCIDENTS.LIRE",
        "INCIDENTS.DECLARER",
        "INCIDENTS.GERER",
    },
    "ADMIN_BNEC": {
        "GOUVERNANCE.LIRE",
        "QUALITE.LIRE",
        "DECISIONS.LIRE",
        "PUBLICATIONS.LIRE",
        "RAPPORTS.LIRE",
        "RAPPORTS.DEMANDER",
        "RAPPORTS.GENERER",
        "ARCHIVES.LIRE",
        "SAUVEGARDES.LIRE",
        "SAUVEGARDES.GERER",
        "INCIDENTS.LIRE",
        "INCIDENTS.DECLARER",
        "INCIDENTS.GERER",
    },
    "CELLULE_VEILLE": {
        "GOUVERNANCE.LIRE",
        "QUALITE.LIRE",
        "QUALITE.GERER",
        "DECISIONS.LIRE",
        "PUBLICATIONS.LIRE",
        "RAPPORTS.LIRE",
        "RAPPORTS.DEMANDER",
        "ARCHIVES.LIRE",
        "INCIDENTS.LIRE",
        "INCIDENTS.DECLARER",
        "INCIDENTS.GERER",
    },
    "VERIFICATEUR": {
        "QUALITE.LIRE",
        "DECISIONS.LIRE",
        "RAPPORTS.LIRE",
        "INCIDENTS.LIRE",
        "INCIDENTS.DECLARER",
    },
    "CONTROLEUR_FUCCS": {
        "QUALITE.LIRE",
        "DECISIONS.LIRE",
        "RAPPORTS.LIRE",
        "INCIDENTS.LIRE",
        "INCIDENTS.DECLARER",
    },
    "AGENT_COLLECTE": {
        "INCIDENTS.LIRE",
        "INCIDENTS.DECLARER",
    },
    "LECTEUR": {
        "GOUVERNANCE.LIRE",
        "QUALITE.LIRE",
        "DECISIONS.LIRE",
        "PUBLICATIONS.LIRE",
        "RAPPORTS.LIRE",
        "ARCHIVES.LIRE",
        "INCIDENTS.LIRE",
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
        db.add(RolePermission(role_id=role_id, permission_id=permission_id))


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
            print("Permissions Gouvernance / Qualité / Continuité synchronisées.")

        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(seed(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(seed())
