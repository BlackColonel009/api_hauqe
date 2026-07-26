"""
Initialisation de la matrice rôle → permissions HAUQE.

IMPORTANT
---------
Cette matrice constitue une BASE TECHNIQUE INITIALE.

Elle reste :
- administrable via l'API ;
- modifiable après validation institutionnelle ;
- indépendante du code des routes.

Le script est idempotent :
- il ajoute uniquement les associations absentes ;
- il ne supprime jamais une permission existante ;
- il ne détruit donc pas une modification manuelle déjà faite.

ADMIN_HAUQE reçoit systématiquement toutes les permissions.
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from app.audit.service import write_audit_event
from app.database.session import AsyncSessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


# ============================================================
# MATRICE INITIALE
# ============================================================

ROLE_PERMISSION_MATRIX = {

    # --------------------------------------------------------
    # DIRECTION TECHNIQUE
    # --------------------------------------------------------
    "DIRECTION_TECHNIQUE": {
        "UTILISATEURS.LIRE",
        "ROLES.LIRE",
        "PERMISSIONS.LIRE",
        "REFERENTIELS.LIRE",
        "ENTREPRISES.LIRE",
        "ENTREPRISES.EXPORTER",
        "ORGANISMES.LIRE",
        "CERTIFICATIONS.LIRE",
        "VALIDATION.LIRE",
        "VALIDATION.VALIDER",
        "VALIDATION.VALIDER_SOUS_RESERVE",
        "VALIDATION.AJOURNER",
        "VALIDATION.REJETER",
        "SCORING.LIRE",
        "SCORING.VALIDER",
        "INFC.LIRE",
        "INFC.VALIDER",
        "CLASSEMENT.LIRE",
        "CLASSEMENT.VALIDER",
        "DOCUMENTS.LIRE",
        "DOCUMENTS.TELECHARGER",
        "RAPPORTS.LIRE",
        "RAPPORTS.GENERER",
        "RAPPORTS.EXPORTER",
        "RAPPORTS.VALIDER",
        "AUDIT.LIRE",
        "AUDIT.EXPORTER",
        "PUBLICATIONS.LIRE",
        "PUBLICATIONS.APPROUVER",
        "PUBLICATIONS.PUBLIER",
        "QUALITE.LIRE",
        "QUALITE.VALIDER",
        "INCIDENTS.LIRE",
        "REGLES_METIER.LIRE",
        "GRILLES.LIRE",
        "ADMINISTRATION.SUPERVISER",
    },

    # --------------------------------------------------------
    # POINT FOCAL / SUPERVISEUR
    # --------------------------------------------------------
    "POINT_FOCAL_BNEC": {
        "UTILISATEURS.LIRE",
        "REFERENTIELS.LIRE",
        "ENTREPRISES.LIRE",
        "ORGANISMES.LIRE",
        "CERTIFICATIONS.LIRE",
        "COLLECTE.LIRE",
        "COLLECTE.AFFECTER",
        "VERIFICATION.LIRE",
        "VERIFICATION.AFFECTER",
        "VERIFICATION.CLOTURER",
        "CONTROLE.LIRE",
        "VALIDATION.LIRE",
        "DOCUMENTS.LIRE",
        "DOCUMENTS.TELECHARGER",
        "RAPPORTS.LIRE",
        "RAPPORTS.GENERER",
        "RAPPORTS.EXPORTER",
        "AUDIT.LIRE",
        "ALERTES.LIRE",
        "ALERTES.AFFECTER",
        "INCIDENTS.LIRE",
    },

    # --------------------------------------------------------
    # VERIFICATEUR
    # --------------------------------------------------------
    "VERIFICATEUR": {
        "REFERENTIELS.LIRE",
        "ENTREPRISES.LIRE",
        "ORGANISMES.LIRE",
        "CERTIFICATIONS.LIRE",
        "CERTIFICATIONS.VERIFIER",
        "VERIFICATION.LIRE",
        "VERIFICATION.VERIFIER",
        "VERIFICATION.SIGNALER_ANOMALIE",
        "VERIFICATION.CONFIRMER",
        "DOCUMENTS.LIRE",
        "DOCUMENTS.DEPOSER",
        "DOCUMENTS.TELECHARGER",
        "INCIDENTS.DECLARER",
    },

    # --------------------------------------------------------
    # CONTROLEUR FUCCS
    # --------------------------------------------------------
    "CONTROLEUR_FUCCS": {
        "REFERENTIELS.LIRE",
        "ENTREPRISES.LIRE",
        "CERTIFICATIONS.LIRE",
        "VERIFICATION.LIRE",
        "GRILLES.LIRE",
        "CONTROLE.LIRE",
        "CONTROLE.DEMARRER",
        "CONTROLE.NOTER",
        "CONTROLE.MODIFIER",
        "CONTROLE.TERMINER",
        "DOCUMENTS.LIRE",
        "DOCUMENTS.DEPOSER",
        "DOCUMENTS.TELECHARGER",
    },

    # --------------------------------------------------------
    # ADMINISTRATEUR FONCTIONNEL BNEC
    # --------------------------------------------------------
    "ADMIN_BNEC": {
        "ENTREPRISES.LIRE",
        "ORGANISMES.LIRE",
        "CERTIFICATIONS.LIRE",
        "VALIDATION.LIRE",
        "INTEGRATION_BNEC.LIRE",
        "INTEGRATION_BNEC.PRECONTROLER",
        "INTEGRATION_BNEC.INTEGRER",
        "INTEGRATION_BNEC.POSTCONTROLER",
        "DOCUMENTS.LIRE",
        "DOCUMENTS.TELECHARGER",
        "AUDIT.LIRE",
        "RAPPORTS.LIRE",
        "RAPPORTS.GENERER",
    },

    # --------------------------------------------------------
    # AGENT DE COLLECTE
    # --------------------------------------------------------
    "AGENT_COLLECTE": {
        "REFERENTIELS.LIRE",
        "ENTREPRISES.LIRE",
        "ENTREPRISES.CREER",
        "ENTREPRISES.MODIFIER",
        "ORGANISMES.LIRE",
        "CERTIFICATIONS.LIRE",
        "COLLECTE.LIRE",
        "COLLECTE.CREER",
        "COLLECTE.MODIFIER",
        "COLLECTE.SOUMETTRE",
        "DOCUMENTS.LIRE",
        "DOCUMENTS.DEPOSER",
        "DOCUMENTS.TELECHARGER",
    },

    # --------------------------------------------------------
    # CELLULE DE VEILLE
    # --------------------------------------------------------
    "CELLULE_VEILLE": {
        "ENTREPRISES.LIRE",
        "ORGANISMES.LIRE",
        "CERTIFICATIONS.LIRE",
        "ECHEANCES.LIRE",
        "ECHEANCES.CREER",
        "ECHEANCES.MODIFIER",
        "ECHEANCES.CLOTURER",
        "ALERTES.LIRE",
        "ALERTES.AFFECTER",
        "ALERTES.TRAITER",
        "ALERTES.CLOTURER",
        "VEILLE.LIRE",
        "VEILLE.CREER",
        "VEILLE.RELANCER",
        "VEILLE.CLOTURER",
        "DOCUMENTS.LIRE",
        "DOCUMENTS.DEPOSER",
        "DOCUMENTS.TELECHARGER",
        "RAPPORTS.LIRE",
        "RAPPORTS.GENERER",
        "RAPPORTS.EXPORTER",
        "INCIDENTS.LIRE",
        "INCIDENTS.DECLARER",
    },

    # --------------------------------------------------------
    # LECTEUR
    # --------------------------------------------------------
    "LECTEUR": {
        "REFERENTIELS.LIRE",
        "ENTREPRISES.LIRE",
        "ORGANISMES.LIRE",
        "CERTIFICATIONS.LIRE",
        "GRILLES.LIRE",
        "VALIDATION.LIRE",
        "SCORING.LIRE",
        "INFC.LIRE",
        "CLASSEMENT.LIRE",
        "ECHEANCES.LIRE",
        "ALERTES.LIRE",
        "VEILLE.LIRE",
        "DOCUMENTS.LIRE",
        "DOCUMENTS.TELECHARGER",
        "RAPPORTS.LIRE",
    },
}


# ============================================================
# EXECUTION
# ============================================================

async def seed_matrix() -> None:

    print("=" * 72)
    print("HAUQE CERTIF — INITIALISATION MATRICE RBAC")
    print("=" * 72)

    async with AsyncSessionLocal() as db:

        try:

            # ------------------------------------------------
            # Chargement de tous les rôles
            # ------------------------------------------------

            role_result = await db.execute(
                select(Role)
            )

            roles = {
                role.code: role
                for role in role_result.scalars().all()
            }

            # ------------------------------------------------
            # Chargement du catalogue complet des permissions
            # ------------------------------------------------

            permission_result = await db.execute(
                select(Permission)
            )

            permissions = {
                permission.code: permission
                for permission
                in permission_result.scalars().all()
            }

            # ------------------------------------------------
            # ADMIN_HAUQE doit posséder TOUTES les permissions.
            # ------------------------------------------------

            matrix = dict(
                ROLE_PERMISSION_MATRIX
            )

            matrix["ADMIN_HAUQE"] = set(
                permissions.keys()
            )

            total_created = 0

            # ------------------------------------------------
            # Traitement rôle par rôle
            # ------------------------------------------------

            for role_code, permission_codes in matrix.items():

                role = roles.get(
                    role_code
                )

                if role is None:
                    raise RuntimeError(
                        f"Rôle absent : {role_code}"
                    )

                added_codes = []

                for permission_code in sorted(
                    permission_codes
                ):

                    permission = permissions.get(
                        permission_code
                    )

                    # ----------------------------------------
                    # Une faute dans la matrice doit être
                    # détectée immédiatement.
                    # ----------------------------------------

                    if permission is None:
                        raise RuntimeError(
                            "Permission absente du catalogue : "
                            f"{permission_code}"
                        )

                    existing_result = await db.execute(
                        select(RolePermission).where(
                            RolePermission.role_id
                            == role.id,

                            RolePermission.permission_id
                            == permission.id,
                        )
                    )

                    existing = (
                        existing_result
                        .scalar_one_or_none()
                    )

                    if existing is not None:
                        continue

                    link = RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                    )

                    db.add(link)

                    added_codes.append(
                        permission.code
                    )

                    total_created += 1

                # --------------------------------------------
                # Un seul événement d'audit par rôle,
                # plutôt qu'un événement par permission.
                # --------------------------------------------

                if added_codes:

                    await write_audit_event(
                        db,
                        action="RBAC_MATRIX_SEED",
                        categorie="HABILITATION",
                        resultat="SUCCES",

                        # Exécution système :
                        # aucun utilisateur humain n'est
                        # considéré comme auteur.
                        utilisateur_id=None,

                        ressource_type="role",
                        ressource_id=role.id,

                        contexte={
                            "source":
                                "SEED_INITIAL_RBAC_MATRIX",
                            "role_code":
                                role.code,
                            "permissions_ajoutees":
                                added_codes,
                            "nombre":
                                len(added_codes),
                        },
                    )

                    print(
                        f"[OK] {role.code:<25} "
                        f"+{len(added_codes)} permission(s)"
                    )

                else:

                    print(
                        f"[EXISTE] {role.code}"
                    )

            await db.commit()

            print()
            print("=" * 72)
            print(
                f"Associations ajoutées : {total_created}"
            )
            print("=" * 72)

        except Exception:

            await db.rollback()
            raise


# ============================================================
# COMPATIBILITE WINDOWS / PSYCOPG ASYNC
# ============================================================

if __name__ == "__main__":

    if sys.platform == "win32":

        asyncio.run(
            seed_matrix(),
            loop_factory=asyncio.SelectorEventLoop,
        )

    else:

        asyncio.run(
            seed_matrix()
        )