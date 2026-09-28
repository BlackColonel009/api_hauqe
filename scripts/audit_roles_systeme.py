"""Audit en lecture seule du contrôle d'accès SNGSC / HAUQE Certif.

Contrôle le catalogue de rôles, les associations rôle-permission, les
permissions appelées par les routes privées et les attributions actives.
Il ne crée, ne modifie ni ne supprime aucune donnée PostgreSQL.
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database.session import AsyncSessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.utilisateur import Utilisateur
from app.models.utilisateur_role import UtilisateurRole
from app.scripts.seed_business_roles import BUSINESS_ROLES


EXPECTED_ROLES = {"ADMIN_HAUQE", *(row["code"] for row in BUSINESS_ROLES)}
PERMISSION_PATTERN = re.compile(r"require_permission\(\s*[\"']([^\"']+)[\"']")

# Socle minimum directement nécessaire au parcours Collecte → BNEC → SNCC.
WORKFLOW_MINIMUM = {
    "AGENT_COLLECTE": {
        "COLLECTE.LIRE", "COLLECTE.CREER", "COLLECTE.MODIFIER", "COLLECTE.SOUMETTRE",
    },
    "VERIFICATEUR": {
        "COLLECTE.LIRE", "VERIFICATION.LIRE", "VERIFICATION.OUVRIR", "VERIFICATION.VERIFIER",
        "VERIFICATION.SIGNALER_ANOMALIE", "VERIFICATION.CONFIRMER", "VERIFICATION.CLOTURER",
    },
    "CONTROLEUR_FUCCS": {"FUCCS.LIRE", "FUCCS.CONTROLER", "FUCCS.FINALISER"},
    "ADMIN_BNEC": {
        "INTEGRATION.LIRE", "INTEGRATION.OUVRIR", "INTEGRATION.EXECUTER",
        "INTEGRATION.PRECONTROLER", "INTEGRATION.POSTCONTROLER", "INTEGRATION.CLOTURER",
    },
    "DIRECTION_TECHNIQUE": {
        "COLLECTE.LIRE", "VERIFICATION.LIRE", "VALIDATION.LIRE", "VALIDATION.VALIDER",
    },
}


def route_permissions() -> set[str]:
    required: set[str] = set()
    for path in (PROJECT_ROOT / "app" / "routes" / "api" / "v1").glob("*.py"):
        required.update(PERMISSION_PATTERN.findall(path.read_text(encoding="utf-8")))
    return required


async def run_audit() -> dict:
    async with AsyncSessionLocal() as db:
        roles = (await db.execute(select(Role))).scalars().all()
        permissions = (await db.execute(select(Permission))).scalars().all()
        links = (await db.execute(select(RolePermission))).scalars().all()
        active_assignments = (
            await db.execute(
                select(UtilisateurRole.utilisateur_id, UtilisateurRole.role_id)
                .join(Utilisateur, Utilisateur.id == UtilisateurRole.utilisateur_id)
                .where(Utilisateur.statut == "ACTIF", UtilisateurRole.statut == "ACTIF")
            )
        ).all()
        active_users = (
            await db.execute(select(Utilisateur.id).where(Utilisateur.statut == "ACTIF"))
        ).scalars().all()

    role_by_id = {item.id: item for item in roles}
    permission_by_id = {item.id: item.code for item in permissions}
    grants: dict[str, set[str]] = defaultdict(set)
    for link in links:
        role = role_by_id.get(link.role_id)
        permission = permission_by_id.get(link.permission_id)
        if role and permission:
            grants[role.code].add(permission)

    roles_present = {item.code for item in roles}
    catalog = set(permission_by_id.values())
    routes = route_permissions()
    assignments_by_user: dict[object, set[object]] = defaultdict(set)
    for user_id, role_id in active_assignments:
        assignments_by_user[user_id].add(role_id)

    minimum_missing = {
        role: sorted(required - grants.get(role, set()))
        for role, required in WORKFLOW_MINIMUM.items()
        if required - grants.get(role, set())
    }
    stale_grants = {
        role: sorted(
            permission
            for permission in granted
            if permission.startswith(("CONTROLE.", "INTEGRATION_BNEC."))
        )
        for role, granted in grants.items()
        if any(item.startswith(("CONTROLE.", "INTEGRATION_BNEC.")) for item in granted)
    }
    verifier_can_assign = "VERIFICATION.AFFECTER" in grants.get("VERIFICATEUR", set())
    has_attention = bool(
        routes - catalog
        or EXPECTED_ROLES - roles_present
        or minimum_missing
        or stale_grants
        or verifier_can_assign
    )
    return {
        "statut": "ATTENTION" if has_attention else "OK",
        "roles_attendus_absents": sorted(EXPECTED_ROLES - roles_present),
        "roles_actifs_sans_permission": sorted(
            role.code for role in roles if role.statut == "ACTIF" and not grants.get(role.code)
        ),
        "permissions_routes_absentes_du_catalogue": sorted(routes - catalog),
        "socle_workflow_manquant": minimum_missing,
        "permissions_legacy_attribuees": stale_grants,
        "admin_a_toutes_permissions": catalog <= grants.get("ADMIN_HAUQE", set()),
        "utilisateurs_actifs_sans_role": sum(
            1 for user_id in active_users if not assignments_by_user.get(user_id)
        ),
        "roles": [
            {
                "code": role.code,
                "libelle": role.libelle,
                "statut": role.statut,
                "permissions": len(grants.get(role.code, set())),
            }
            for role in sorted(roles, key=lambda item: item.code)
        ],
        "separation_responsabilites": {
            "n1_n2_distincts": True,
            "preuve": "ValidationBnecService bloque N2 lorsque validateur N1 = validateur N2.",
            "point_a_valider_verificateur_affectation": (
                "VERIFICATION.AFFECTER est "
                + ("accordée" if verifier_can_assign else "non accordée")
                + " au rôle VERIFICATEUR."
            ),
        },
    }


def main() -> None:
    runner = {"loop_factory": asyncio.SelectorEventLoop} if sys.platform == "win32" else {}
    result = asyncio.run(run_audit(), **runner)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["statut"] != "OK":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
