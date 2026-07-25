
from __future__ import annotations
import sys
import asyncio
import getpass

from argon2 import PasswordHasher
from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.utilisateur import Utilisateur
from app.models.utilisateur_role import UtilisateurRole


# ============================================================
# CONFIGURATION
# ============================================================

ph = PasswordHasher()


BOOTSTRAP_ROLE = {
    "code": "ADMIN_HAUQE",
    "libelle": "Administrateur HAUQE",
    "description": (
        "Administrateur fonctionnel initial disposant de "
        "l'ensemble des permissions du système."
    ),
    "niveau": 100,
    "statut": "ACTIF",
}


# ============================================================
# PERMISSIONS TECHNIQUES INITIALES
# ============================================================
#
# Il ne s'agit pas encore de la matrice métier définitive.
#
# Elles constituent le catalogue technique que les rôles
# pourront recevoir.
#
# La matrice officielle rôles -> permissions sera ensuite
# configurable dans l'administration.
# ============================================================

DOMAINS = {
    "utilisateurs": [
        "lire",
        "creer",
        "modifier",
        "desactiver",
        "gerer_roles",
    ],

    "roles": [
        "lire",
        "creer",
        "modifier",
        "attribuer",
    ],

    "permissions": [
        "lire",
        "attribuer",
    ],

    "referentiels": [
        "lire",
        "creer",
        "modifier",
        "desactiver",
        "publier",
    ],

    "entreprises": [
        "lire",
        "creer",
        "modifier",
        "archiver",
        "exporter",
    ],

    "organismes": [
        "lire",
        "creer",
        "modifier",
        "archiver",
    ],

    "certifications": [
        "lire",
        "creer",
        "modifier",
        "verifier",
        "archiver",
    ],

    "collecte": [
        "lire",
        "creer",
        "modifier",
        "soumettre",
        "affecter",
    ],

    "verification": [
        "lire",
        "affecter",
        "verifier",
        "signaler_anomalie",
        "confirmer",
        "cloturer",
    ],

    "controle": [
        "lire",
        "demarrer",
        "noter",
        "modifier",
        "terminer",
    ],

    "validation": [
        "lire",
        "valider",
        "valider_sous_reserve",
        "ajourner",
        "rejeter",
    ],

    "integration_bnec": [
        "lire",
        "precontroler",
        "integrer",
        "postcontroler",
    ],

    "scoring": [
        "lire",
        "calculer",
        "valider",
    ],

    "infc": [
        "lire",
        "calculer",
        "valider",
    ],

    "classement": [
        "lire",
        "calculer",
        "valider",
    ],

    "echeances": [
        "lire",
        "creer",
        "modifier",
        "cloturer",
    ],

    "alertes": [
        "lire",
        "affecter",
        "traiter",
        "cloturer",
    ],

    "veille": [
        "lire",
        "creer",
        "relancer",
        "cloturer",
    ],

    "documents": [
        "lire",
        "deposer",
        "modifier",
        "archiver",
        "telecharger",
    ],

    "rapports": [
        "lire",
        "generer",
        "exporter",
        "valider",
    ],

    "regles_metier": [
        "lire",
        "creer",
        "modifier",
        "publier",
        "desactiver",
    ],

    "grilles": [
        "lire",
        "creer",
        "modifier",
        "publier",
        "desactiver",
    ],

    "audit": [
        "lire",
        "exporter",
    ],

    "publications": [
        "lire",
        "demander",
        "approuver",
        "publier",
    ],

    "qualite": [
        "lire",
        "creer",
        "modifier",
        "valider",
    ],

    "incidents": [
        "lire",
        "declarer",
        "affecter",
        "traiter",
        "cloturer",
    ],

    "sauvegardes": [
        "lire",
        "executer",
        "verifier",
    ],

    "administration": [
        "parametrer",
        "superviser",
    ],
}


# ============================================================
# GENERATION DU CATALOGUE
# ============================================================

def build_permission_catalog() -> list[dict]:
    permissions = []

    for domain, actions in DOMAINS.items():
        for action in actions:

            code = (
                f"{domain}.{action}"
                .upper()
                .replace("-", "_")
            )

            permissions.append(
                {
                    "code": code,
                    "domaine": domain,
                    "action": action,
                    "description": (
                        f"Autorise l'action '{action}' "
                        f"sur le domaine '{domain}'."
                    ),
                }
            )

    return permissions


# ============================================================
# ROLE
# ============================================================

async def get_or_create_admin_role(session) -> Role:

    result = await session.execute(
        select(Role).where(
            Role.code == BOOTSTRAP_ROLE["code"]
        )
    )

    role = result.scalar_one_or_none()

    if role:
        print(
            "[EXISTE] Rôle ADMIN_HAUQE"
        )
        return role

    role = Role(
        **BOOTSTRAP_ROLE,
    )

    session.add(role)

    await session.flush()

    print(
        "[CREE]   Rôle ADMIN_HAUQE"
    )

    return role


# ============================================================
# PERMISSIONS
# ============================================================

async def create_permissions(
    session,
) -> list[Permission]:

    permissions = []

    for item in build_permission_catalog():

        result = await session.execute(
            select(Permission).where(
                Permission.code == item["code"]
            )
        )

        permission = (
            result.scalar_one_or_none()
        )

        if permission is None:

            permission = Permission(
                **item
            )

            session.add(
                permission
            )

            await session.flush()

            print(
                f"[CREE]   Permission "
                f"{permission.code}"
            )

        else:

            print(
                f"[EXISTE] Permission "
                f"{permission.code}"
            )

        permissions.append(
            permission
        )

    return permissions


# ============================================================
# ADMINISTRATEUR
# ============================================================

async def create_admin(
    session,
    *,
    email: str,
    password: str,
    nom: str,
    prenoms: str,
) -> Utilisateur:

    email = email.strip().lower()

    result = await session.execute(
        select(Utilisateur).where(
            Utilisateur.email == email
        )
    )

    user = result.scalar_one_or_none()

    if user:

        print(
            f"[EXISTE] Utilisateur {email}"
        )

        return user

    password_hash = ph.hash(
        password
    )

    user = Utilisateur(
        email=email,
        mot_de_passe_hash=password_hash,
        nom=nom.strip() or None,
        prenoms=prenoms.strip() or None,
        fonction="Administrateur HAUQE",
        statut="ACTIF",
        mfa_active=False,
    )

    session.add(user)

    await session.flush()

    print(
        f"[CREE]   Utilisateur {email}"
    )

    return user


# ============================================================
# ATTRIBUTION ROLE
# ============================================================

async def assign_admin_role(
    session,
    *,
    user: Utilisateur,
    role: Role,
) -> None:

    result = await session.execute(
        select(UtilisateurRole).where(
            UtilisateurRole.utilisateur_id
            == user.id,
            UtilisateurRole.role_id
            == role.id,
        )
    )

    existing = result.scalar_one_or_none()

    if existing:

        print(
            "[EXISTE] Attribution ADMIN_HAUQE"
        )

        return

    attribution = UtilisateurRole(
        utilisateur_id=user.id,
        role_id=role.id,

        # Pour le bootstrap uniquement :
        # le premier administrateur s'attribue
        # son propre rôle initial.
        attribue_par_id=user.id,

        motif=(
            "Initialisation sécurisée "
            "de la plateforme HAUQE Certif."
        ),

        statut="ACTIF",
    )

    session.add(
        attribution
    )

    print(
        "[CREE]   Attribution ADMIN_HAUQE"
    )


# ============================================================
# ADMIN = TOUTES LES PERMISSIONS
# ============================================================

async def assign_all_permissions(
    session,
    *,
    role: Role,
    permissions: list[Permission],
) -> None:

    result = await session.execute(
        select(
            RolePermission.permission_id
        ).where(
            RolePermission.role_id
            == role.id
        )
    )

    existing_ids = set(
        result.scalars().all()
    )

    created = 0

    for permission in permissions:

        if permission.id in existing_ids:
            continue

        session.add(
            RolePermission(
                role_id=role.id,
                permission_id=permission.id,
            )
        )

        created += 1

    print(
        f"[OK]     {created} nouvelle(s) "
        "permission(s) affectée(s) "
        "à ADMIN_HAUQE"
    )


# ============================================================
# EXECUTION
# ============================================================

async def bootstrap() -> None:

    print("=" * 72)
    print("HAUQE CERTIF — INITIALISATION SECURITE")
    print("=" * 72)

    print()
    print(
        "Création du premier administrateur."
    )

    email = input(
        "Email administrateur : "
    ).strip()

    nom = input(
        "Nom : "
    ).strip()

    prenoms = input(
        "Prénoms : "
    ).strip()

    password = getpass.getpass(
        "Mot de passe : "
    )

    confirmation = getpass.getpass(
        "Confirmer le mot de passe : "
    )

    if password != confirmation:
        raise SystemExit(
            "ERREUR : les mots de passe "
            "ne correspondent pas."
        )

    if len(password) < 12:
        raise SystemExit(
            "ERREUR : utilise un mot de passe "
            "d'au moins 12 caractères pour "
            "le compte initial."
        )

    async with AsyncSessionLocal() as session:

        try:

            role = await get_or_create_admin_role(
                session
            )

            permissions = await create_permissions(
                session
            )

            user = await create_admin(
                session,
                email=email,
                password=password,
                nom=nom,
                prenoms=prenoms,
            )

            await assign_admin_role(
                session,
                user=user,
                role=role,
            )

            await assign_all_permissions(
                session,
                role=role,
                permissions=permissions,
            )

            await session.commit()

        except Exception:
            await session.rollback()
            raise

    print()
    print("=" * 72)
    print("INITIALISATION TERMINEE")
    print("=" * 72)

    print(
        """
Le système possède maintenant :

- un compte administrateur initial ;
- le rôle ADMIN_HAUQE ;
- le catalogue initial de permissions ;
- toutes les permissions affectées à ADMIN_HAUQE.

Aucun mot de passe en clair n'est stocké.
"""
    )


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(
            bootstrap(),
            loop_factory=asyncio.SelectorEventLoop,
        )
    else:
        asyncio.run(
            bootstrap()
        )