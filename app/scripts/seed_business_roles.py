"""
Initialisation des rôles métier HAUQE Certif.

OBJECTIF
-------
Créer dans PostgreSQL les rôles métier nécessaires au fonctionnement
du workflow BNEC.

Ce script :
- NE modifie pas le schéma PostgreSQL ;
- NE crée aucune migration Alembic ;
- NE supprime aucun rôle existant ;
- NE modifie pas ADMIN_HAUQE ;
- peut être exécuté plusieurs fois sans créer de doublons.

IMPORTANT
---------
Les rôles sont créés ici comme référentiel fonctionnel.

La matrice détaillée :
    ROLE -> PERMISSIONS

sera gérée séparément, car les habilitations définitives doivent rester
validables et administrables.

Source fonctionnelle principale :
- Procédure de vérification et validation BNEC HAUQE
- Matrice RACI
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.role import Role


# ============================================================
# CATALOGUE INITIAL DES ROLES METIER
# ============================================================
#
# "niveau" sert ici uniquement à faciliter l'ordre d'affichage
# et certaines règles futures de délégation.
#
# Il ne remplace PAS le contrôle réel par permissions.
#
# Le système de sécurité doit toujours vérifier :
#
#       permission requise
#              ↓
#       rôle utilisateur
#              ↓
#       role_permission
#
# et jamais simplement :
#
#       niveau >= X
#
# ============================================================

BUSINESS_ROLES = [

    # --------------------------------------------------------
    # Direction / autorité de validation
    # --------------------------------------------------------
    {
        "code": "DIRECTION_TECHNIQUE",
        "libelle": "Direction Technique",
        "description": (
            "Autorité métier chargée notamment de la validation "
            "définitive, des arbitrages et des décisions sensibles."
        ),
        "niveau": 90,
        "statut": "ACTIF",
    },

    # --------------------------------------------------------
    # Supervision du processus BNEC
    # --------------------------------------------------------
    {
        "code": "POINT_FOCAL_BNEC",
        "libelle": "Point focal BNEC / Superviseur",
        "description": (
            "Supervise les dossiers, organise les affectations, "
            "contrôle la recevabilité et réalise la revue technique."
        ),
        "niveau": 80,
        "statut": "ACTIF",
    },

    # --------------------------------------------------------
    # Vérification documentaire
    # --------------------------------------------------------
    {
        "code": "VERIFICATEUR",
        "libelle": "Agent vérificateur",
        "description": (
            "Réalise les vérifications documentaires, contrôle la "
            "cohérence des données, les anomalies, les doublons "
            "et les confirmations externes."
        ),
        "niveau": 60,
        "statut": "ACTIF",
    },

    # --------------------------------------------------------
    # Evaluation selon la grille FUCCS
    # --------------------------------------------------------
    {
        "code": "CONTROLEUR_FUCCS",
        "libelle": "Contrôleur / Évaluateur FUCCS",
        "description": (
            "Applique la grille FUCCS publiée, enregistre les notes, "
            "preuves, commentaires et constats du contrôle."
        ),
        "niveau": 60,
        "statut": "ACTIF",
    },

    # --------------------------------------------------------
    # Intégration des dossiers validés dans la BNEC
    # --------------------------------------------------------
    {
        "code": "ADMIN_BNEC",
        "libelle": "Administrateur fonctionnel BNEC",
        "description": (
            "Prépare et réalise l'intégration des dossiers validés "
            "dans la BNEC ainsi que le contrôle post-intégration."
        ),
        "niveau": 70,
        "statut": "ACTIF",
    },

    # --------------------------------------------------------
    # Collecte des données
    # --------------------------------------------------------
    {
        "code": "AGENT_COLLECTE",
        "libelle": "Agent de collecte",
        "description": (
            "Collecte, saisit et corrige les informations et pièces "
            "nécessaires à la constitution des dossiers."
        ),
        "niveau": 40,
        "statut": "ACTIF",
    },

    # --------------------------------------------------------
    # Veille sur les certifications
    # --------------------------------------------------------
    {
        "code": "CELLULE_VEILLE",
        "libelle": "Cellule de Veille des Certifications",
        "description": (
            "Suit les échéances, renouvellements, risques, alertes "
            "et changements affectant les certifications."
        ),
        "niveau": 50,
        "statut": "ACTIF",
    },

    # --------------------------------------------------------
    # Consultation externe ou institutionnelle restreinte
    # --------------------------------------------------------
    {
        "code": "LECTEUR",
        "libelle": "Consultation en lecture seule",
        "description": (
            "Profil destiné aux utilisateurs autorisés à consulter "
            "certaines données sans pouvoir les modifier."
        ),
        "niveau": 10,
        "statut": "ACTIF",
    },
]


# ============================================================
# CREATION / MISE A JOUR
# ============================================================

async def seed_roles() -> None:
    """
    Insère les rôles absents.

    Si un rôle existe déjà :
    - il n'est pas dupliqué ;
    - son identité technique reste inchangée ;
    - ses libellés/descriptions peuvent être synchronisés.
    """

    print("=" * 72)
    print("HAUQE CERTIF — INITIALISATION DES ROLES METIER")
    print("=" * 72)

    async with AsyncSessionLocal() as db:

        try:

            created = 0
            updated = 0
            unchanged = 0

            for data in BUSINESS_ROLES:

                # ------------------------------------------------
                # Recherche par code unique
                # ------------------------------------------------

                result = await db.execute(
                    select(Role).where(
                        Role.code == data["code"]
                    )
                )

                role = result.scalar_one_or_none()

                # ------------------------------------------------
                # Nouveau rôle
                # ------------------------------------------------

                if role is None:

                    role = Role(
                        code=data["code"],
                        libelle=data["libelle"],
                        description=data["description"],
                        niveau=data["niveau"],
                        statut=data["statut"],
                    )

                    db.add(role)

                    created += 1

                    print(
                        f"[CREE]      {data['code']}"
                    )

                    continue

                # ------------------------------------------------
                # Synchronisation contrôlée
                # ------------------------------------------------

                changed = False

                for field in (
                    "libelle",
                    "description",
                    "niveau",
                    "statut",
                ):

                    expected = data[field]

                    if getattr(role, field) != expected:

                        setattr(
                            role,
                            field,
                            expected,
                        )

                        changed = True

                if changed:

                    updated += 1

                    print(
                        f"[MIS A JOUR] {data['code']}"
                    )

                else:

                    unchanged += 1

                    print(
                        f"[EXISTE]     {data['code']}"
                    )

            # ----------------------------------------------------
            # Une seule transaction :
            #
            # soit tous les rôles sont correctement enregistrés,
            # soit aucune modification partielle n'est conservée.
            # ----------------------------------------------------

            await db.commit()

            print()
            print("=" * 72)
            print("RESULTAT")
            print("=" * 72)

            print(f"Créés       : {created}")
            print(f"Mis à jour  : {updated}")
            print(f"Inchangés   : {unchanged}")

            print()
            print(
                "ADMIN_HAUQE n'est volontairement pas géré "
                "par ce script."
            )

        except Exception:

            await db.rollback()
            raise


# ============================================================
# EXECUTION WINDOWS / LINUX
# ============================================================
#
# Psycopg async nécessite SelectorEventLoop sous Windows.
# Nous conservons donc la même protection que pour le
# bootstrap de sécurité.
# ============================================================

if __name__ == "__main__":

    if sys.platform == "win32":

        asyncio.run(
            seed_roles(),
            loop_factory=asyncio.SelectorEventLoop,
        )

    else:

        asyncio.run(
            seed_roles()
        )