"""Reprend les offres de collectes déjà soumises dans une entreprise.

Usage local / serveur :
    python -m app.scripts.synchronize_collection_offers_to_enterprise \
        --enterprise-name "AgroNoura SARL" --apply

    python -m app.scripts.synchronize_collection_offers_to_enterprise \
        --all --apply

Sans ``--apply``, le script vérifie seulement l'entreprise et les fiches qui
seraient traitées. Il ne modifie jamais les brouillons.
"""

from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import func, select

from app.database.session import AsyncSessionLocal
from app.models.entreprise import Entreprise
from app.models.fiche_collecte import FicheCollecte
from app.models.offre_declaree import OffreDeclaree
from app.services.fiche_collecte_service import FicheCollecteService


async def run(
    enterprise_name: str | None,
    *,
    all_enterprises: bool,
    apply: bool,
) -> None:
    async with AsyncSessionLocal() as db:
        if all_enterprises:
            enterprises = list(
                (
                    await db.execute(
                        select(Entreprise)
                        .join(
                            FicheCollecte,
                            FicheCollecte.entreprise_id == Entreprise.id,
                        )
                        .where(FicheCollecte.statut != "BROUILLON")
                        .distinct()
                        .order_by(Entreprise.raison_sociale)
                    )
                ).scalars().all()
            )
        else:
            enterprise = (
                await db.execute(
                    select(Entreprise).where(
                        Entreprise.raison_sociale.ilike(
                            enterprise_name.strip()
                        )
                    )
                )
            ).scalar_one_or_none()
            if enterprise is None:
                raise SystemExit("Entreprise introuvable ou nom ambigu.")
            enterprises = [enterprise]

        source_count = await db.scalar(
            select(func.count(OffreDeclaree.id))
            .join(
                FicheCollecte,
                OffreDeclaree.fiche_collecte_id == FicheCollecte.id,
            )
            .where(
                FicheCollecte.entreprise_id.in_([item.id for item in enterprises]),
                FicheCollecte.statut != "BROUILLON",
            )
        )
        print(
            f"{len(enterprises)} entreprise(s), {source_count or 0} offre(s) "
            "déclarée(s) à reprendre."
        )
        if not apply:
            print("Mode contrôle : aucune donnée n'a été modifiée.")
            return

        totals = {"created": 0, "updated": 0, "skipped": 0}
        for enterprise in enterprises:
            fiches = list(
                (
                    await db.execute(
                        select(FicheCollecte)
                        .where(
                            FicheCollecte.entreprise_id == enterprise.id,
                            FicheCollecte.statut != "BROUILLON",
                        )
                        .order_by(
                            FicheCollecte.soumise_at.asc().nullsfirst(),
                            FicheCollecte.created_at.asc(),
                        )
                    )
                ).scalars().all()
            )
            for fiche in fiches:
                result = await FicheCollecteService.synchronize_enterprise_offers(
                    db,
                    fiche=fiche,
                    actor=None,
                    request=None,
                )
                for key, value in result.items():
                    totals[key] += value

        await db.commit()
        print(
            "Migration terminée : "
            f"{totals['created']} créée(s), {totals['updated']} rapprochée(s), "
            f"{totals['skipped']} ignorée(s)."
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--enterprise-name")
    scope.add_argument("--all", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(
        run(
            args.enterprise_name,
            all_enterprises=args.all,
            apply=args.apply,
        )
    )


if __name__ == "__main__":
    main()
