"""
Repository des fiches de collecte, déclarations et historique.

La notion de "révision courante" n'a pas de booléen dédié dans le MPD.
Le backend considère donc comme courante la fiche ayant le plus grand
`numero_revision` pour une mission.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certification_declaree import CertificationDeclaree
from app.models.entreprise import Entreprise
from app.models.evenement_collecte import EvenementCollecte
from app.models.fiche_collecte import FicheCollecte
from app.models.offre_declaree import OffreDeclaree
from app.models.organisme import Organisme
from app.models.regle_metier import RegleMetier
from app.rules.business_rule_resolver import resolve_business_rule


class FicheCollecteRepository:

    @staticmethod
    async def get_entreprise(
        db: AsyncSession,
        entreprise_id: UUID,
    ) -> Entreprise | None:
        result = await db.execute(
            select(Entreprise).where(Entreprise.id == entreprise_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_organisme(db: AsyncSession, organisme_id: UUID) -> Organisme | None:
        result = await db.execute(select(Organisme).where(Organisme.id == organisme_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def find_organisme_by_label(
        db: AsyncSession,
        label: str,
    ) -> Organisme | None:
        """Retrouve un organisme par nom officiel ou sigle, sans approximation."""
        normalized = label.strip().lower()
        result = await db.execute(
            select(Organisme)
            .where(
                or_(
                    func.lower(func.trim(Organisme.nom_officiel)) == normalized,
                    func.lower(func.trim(Organisme.sigle)) == normalized,
                )
            )
            .order_by(Organisme.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_for_mission(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
    ) -> FicheCollecte | None:
        result = await db.execute(
            select(FicheCollecte).where(
                FicheCollecte.id == fiche_id,
                FicheCollecte.mission_id == mission_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_revisions(
        db: AsyncSession,
        mission_id: UUID,
    ) -> list[FicheCollecte]:
        result = await db.execute(
            select(FicheCollecte)
            .where(FicheCollecte.mission_id == mission_id)
            .order_by(
                FicheCollecte.numero_revision.desc().nullslast(),
                FicheCollecte.created_at.desc(),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_current(
        db: AsyncSession,
        mission_id: UUID,
        *,
        dossier_id: UUID | None = None,
        entreprise_id: UUID | None = None,
    ) -> FicheCollecte | None:
        filters = [FicheCollecte.mission_id == mission_id]
        if dossier_id is not None:
            filters.append(FicheCollecte.dossier_id == dossier_id)
        elif entreprise_id is not None:
            filters.append(FicheCollecte.entreprise_id == entreprise_id)
        result = await db.execute(
            select(FicheCollecte)
            .where(*filters)
            .order_by(
                FicheCollecte.numero_revision.desc().nullslast(),
                FicheCollecte.created_at.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_completeness_rule(
        db: AsyncSession,
    ) -> RegleMetier | None:
        """
        Résout la version publiée applicable du code logique
        COLLECTE_COMPLETUDE.

        `regles_metier.code` est un identifiant physique versionné,
        par exemple COLLECTE_COMPLETUDE__V1_0.
        """
        return await resolve_business_rule(
            db,
            "COLLECTE_COMPLETUDE",
        )

    @staticmethod
    async def list_offres(
        db: AsyncSession,
        fiche_id: UUID,
    ) -> list[OffreDeclaree]:
        result = await db.execute(
            select(OffreDeclaree)
            .where(
                OffreDeclaree.fiche_collecte_id == fiche_id,
                or_(
                    OffreDeclaree.statut.is_(None),
                    OffreDeclaree.statut != "DOUBLON_ANNULE",
                ),
            )
            .order_by(OffreDeclaree.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def find_equivalent_offre(
        db: AsyncSession,
        *,
        fiche_id: UUID,
        type_offre: str | None,
        nom: str,
        categorie: str | None,
        exclude_offre_id: UUID | None = None,
    ) -> OffreDeclaree | None:
        """Retrouve une offre active avec la même clé métier dans une fiche."""
        filters = [
            OffreDeclaree.fiche_collecte_id == fiche_id,
            func.upper(func.trim(func.coalesce(OffreDeclaree.type_offre, "")))
            == (type_offre or "").upper(),
            func.upper(func.trim(OffreDeclaree.nom)) == nom.upper(),
            func.upper(func.trim(func.coalesce(OffreDeclaree.categorie, "")))
            == (categorie or "").upper(),
            or_(
                OffreDeclaree.statut.is_(None),
                OffreDeclaree.statut != "DOUBLON_ANNULE",
            ),
        ]
        if exclude_offre_id is not None:
            filters.append(OffreDeclaree.id != exclude_offre_id)
        result = await db.execute(
            select(OffreDeclaree)
            .where(*filters)
            .order_by(OffreDeclaree.created_at)
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_offre(
        db: AsyncSession,
        *,
        fiche_id: UUID,
        offre_id: UUID,
    ) -> OffreDeclaree | None:
        result = await db.execute(
            select(OffreDeclaree).where(
                OffreDeclaree.id == offre_id,
                OffreDeclaree.fiche_collecte_id == fiche_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_certifications(
        db: AsyncSession,
        fiche_id: UUID,
    ) -> list[CertificationDeclaree]:
        result = await db.execute(
            select(CertificationDeclaree)
            .where(
                CertificationDeclaree.fiche_collecte_id == fiche_id
            )
            .order_by(CertificationDeclaree.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_certification(
        db: AsyncSession,
        *,
        fiche_id: UUID,
        certification_declaree_id: UUID,
    ) -> CertificationDeclaree | None:
        result = await db.execute(
            select(CertificationDeclaree).where(
                CertificationDeclaree.id
                == certification_declaree_id,
                CertificationDeclaree.fiche_collecte_id == fiche_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_events(
        db: AsyncSession,
        fiche_id: UUID,
    ) -> list[EvenementCollecte]:
        result = await db.execute(
            select(EvenementCollecte)
            .where(
                EvenementCollecte.fiche_collecte_id == fiche_id
            )
            .order_by(
                EvenementCollecte.date_evenement.desc(),
                EvenementCollecte.created_at.desc(),
            )
        )
        return list(result.scalars().all())
