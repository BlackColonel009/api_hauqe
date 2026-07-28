from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campagne import Campagne
from app.models.constat_controle import ConstatControle
from app.models.controle_fuccs import ControleFuccs
from app.models.critere_fuccs import CritereFuccs
from app.models.document import Document
from app.models.dossier_verification import DossierVerification
from app.models.entreprise import Entreprise
from app.models.fiche_collecte import FicheCollecte
from app.models.grille_fuccs import GrilleFuccs
from app.models.mission_collecte import MissionCollecte
from app.models.note_critere import NoteCritere
from app.models.rubrique_fuccs import RubriqueFuccs
from app.models.utilisateur import Utilisateur
from app.models.zone_administrative import ZoneAdministrative


ADMISSIBLE_OPINIONS = (
    "verified_compliant",
    "verified_with_reservation",
)


class FuccsWorkspaceRepository:
    @staticmethod
    async def statuses(
        db: AsyncSession,
    ) -> list[str]:
        result = await db.execute(
            select(ControleFuccs.statut)
            .where(
                ControleFuccs.statut.is_not(None),
                func.trim(ControleFuccs.statut) != "",
            )
            .distinct()
            .order_by(ControleFuccs.statut)
        )

        return [
            str(value).strip()
            for value in result.scalars().all()
            if value
        ]

    @staticmethod
    async def active_grid(
        db: AsyncSession,
    ):
        result = await db.execute(
            select(GrilleFuccs)
            .where(
                func.upper(
                    func.coalesce(
                        GrilleFuccs.statut_publication,
                        "",
                    )
                ) == "PUBLIE"
            )
            .order_by(
                GrilleFuccs.date_effet.desc().nullslast(),
                GrilleFuccs.created_at.desc(),
            )
            .limit(1)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def grid_counts(
        db: AsyncSession,
        grid_id: UUID,
    ):
        rubric_result = await db.execute(
            select(func.count(RubriqueFuccs.id))
            .where(
                RubriqueFuccs.grille_fuccs_id == grid_id
            )
        )

        criteria_result = await db.execute(
            select(
                func.count(CritereFuccs.id),
                func.coalesce(
                    func.sum(CritereFuccs.score_maximal),
                    0,
                ),
            )
            .select_from(CritereFuccs)
            .join(
                RubriqueFuccs,
                RubriqueFuccs.id
                == CritereFuccs.rubrique_fuccs_id,
            )
            .where(
                RubriqueFuccs.grille_fuccs_id == grid_id
            )
        )

        criteria_count, maximum_score = (
            criteria_result.one()
        )

        return (
            int(rubric_result.scalar_one() or 0),
            int(criteria_count or 0),
            maximum_score,
        )

    @staticmethod
    def registry_filters(
        *,
        search: str | None,
        statut: str | None,
    ):
        filters = []

        if statut:
            filters.append(
                func.upper(ControleFuccs.statut)
                == statut.strip().upper()
            )

        if search and search.strip():
            pattern = f"%{search.strip()}%"

            filters.append(
                or_(
                    MissionCollecte.code.ilike(pattern),
                    Campagne.code.ilike(pattern),
                    Campagne.nom.ilike(pattern),
                    ZoneAdministrative.nom.ilike(pattern),
                    Entreprise.identifiant_national.ilike(pattern),
                    Entreprise.raison_sociale.ilike(pattern),
                    Entreprise.nom_commercial.ilike(pattern),
                    GrilleFuccs.code.ilike(pattern),
                    GrilleFuccs.libelle.ilike(pattern),
                    GrilleFuccs.version.ilike(pattern),
                    ControleFuccs.synthese.ilike(pattern),
                )
            )

        return filters

    @staticmethod
    def base_control_query():
        notes_count = (
            select(func.count(NoteCritere.id))
            .where(
                NoteCritere.controle_fuccs_id
                == ControleFuccs.id
            )
            .correlate(ControleFuccs)
            .scalar_subquery()
        )

        criteria_count = (
            select(func.count(CritereFuccs.id))
            .select_from(CritereFuccs)
            .join(
                RubriqueFuccs,
                RubriqueFuccs.id
                == CritereFuccs.rubrique_fuccs_id,
            )
            .where(
                RubriqueFuccs.grille_fuccs_id
                == ControleFuccs.grille_fuccs_id
            )
            .correlate(ControleFuccs)
            .scalar_subquery()
        )

        findings_count = (
            select(func.count(ConstatControle.id))
            .where(
                ConstatControle.controle_fuccs_id
                == ControleFuccs.id
            )
            .correlate(ControleFuccs)
            .scalar_subquery()
        )

        documents_count = (
            select(func.count(Document.id))
            .where(
                Document.ressource_type
                == "FICHE_COLLECTE",
                Document.ressource_id
                == FicheCollecte.id,
                or_(
                    Document.statut.is_(None),
                    func.upper(Document.statut)
                    == "ACTIF",
                ),
            )
            .correlate(FicheCollecte)
            .scalar_subquery()
        )

        return (
            select(
                ControleFuccs,
                GrilleFuccs.code.label("grid_code"),
                GrilleFuccs.libelle.label("grid_label"),
                GrilleFuccs.version.label("grid_version"),
                criteria_count.label("criteria_count"),
                DossierVerification.avis.label(
                    "verification_opinion"
                ),
                DossierVerification.niveau_risque.label(
                    "verification_risk"
                ),
                DossierVerification.date_fin.label(
                    "verification_closed_on"
                ),
                FicheCollecte.id.label("fiche_id"),
                FicheCollecte.numero_revision.label(
                    "fiche_revision"
                ),
                FicheCollecte.mission_id.label("mission_id"),
                MissionCollecte.code.label("mission_code"),
                Campagne.code.label("campaign_code"),
                Campagne.nom.label("campaign_name"),
                ZoneAdministrative.nom.label("zone_name"),
                Entreprise.id.label("entreprise_id"),
                Entreprise.identifiant_national.label(
                    "entreprise_identifiant"
                ),
                Entreprise.raison_sociale.label(
                    "entreprise_name"
                ),
                Entreprise.nom_commercial.label(
                    "entreprise_trade_name"
                ),
                Utilisateur.prenoms.label(
                    "controller_first_names"
                ),
                Utilisateur.nom.label(
                    "controller_last_name"
                ),
                Utilisateur.email.label(
                    "controller_email"
                ),
                notes_count.label("notes_count"),
                findings_count.label("findings_count"),
                documents_count.label("documents_count"),
            )
            .select_from(ControleFuccs)
            .join(
                GrilleFuccs,
                GrilleFuccs.id
                == ControleFuccs.grille_fuccs_id,
            )
            .join(
                DossierVerification,
                DossierVerification.id
                == ControleFuccs.dossier_verification_id,
            )
            .join(
                FicheCollecte,
                FicheCollecte.id
                == DossierVerification.fiche_collecte_id,
            )
            .join(
                MissionCollecte,
                MissionCollecte.id
                == FicheCollecte.mission_id,
            )
            .join(
                Campagne,
                Campagne.id
                == MissionCollecte.campagne_id,
            )
            .join(
                ZoneAdministrative,
                ZoneAdministrative.id
                == MissionCollecte.zone_id,
            )
            .outerjoin(
                Entreprise,
                Entreprise.id
                == FicheCollecte.entreprise_id,
            )
            .join(
                Utilisateur,
                Utilisateur.id
                == ControleFuccs.controleur_id,
            )
        )

    @staticmethod
    async def registry(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
        sort: str,
        limit: int,
        offset: int,
    ):
        filters = (
            FuccsWorkspaceRepository
            .registry_filters(
                search=search,
                statut=statut,
            )
        )

        order_by = {
            "recent": ControleFuccs.created_at.desc(),
            "company": Entreprise.raison_sociale.asc().nullslast(),
            "score": ControleFuccs.score_brut.desc().nullslast(),
            "status": ControleFuccs.statut.asc().nullslast(),
        }.get(
            sort,
            ControleFuccs.date_debut.desc().nullslast(),
        )

        result = await db.execute(
            FuccsWorkspaceRepository
            .base_control_query()
            .where(*filters)
            .order_by(
                order_by,
                ControleFuccs.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        count_result = await db.execute(
            select(func.count(ControleFuccs.id))
            .select_from(ControleFuccs)
            .join(
                GrilleFuccs,
                GrilleFuccs.id
                == ControleFuccs.grille_fuccs_id,
            )
            .join(
                DossierVerification,
                DossierVerification.id
                == ControleFuccs.dossier_verification_id,
            )
            .join(
                FicheCollecte,
                FicheCollecte.id
                == DossierVerification.fiche_collecte_id,
            )
            .join(
                MissionCollecte,
                MissionCollecte.id
                == FicheCollecte.mission_id,
            )
            .join(
                Campagne,
                Campagne.id
                == MissionCollecte.campagne_id,
            )
            .join(
                ZoneAdministrative,
                ZoneAdministrative.id
                == MissionCollecte.zone_id,
            )
            .outerjoin(
                Entreprise,
                Entreprise.id
                == FicheCollecte.entreprise_id,
            )
            .where(*filters)
        )

        return (
            result.all(),
            int(count_result.scalar_one() or 0),
        )

    @staticmethod
    async def summary(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
    ) -> dict:
        filters = (
            FuccsWorkspaceRepository
            .registry_filters(
                search=search,
                statut=statut,
            )
        )

        base = (
            FuccsWorkspaceRepository
            .base_control_query()
            .with_only_columns(
                ControleFuccs.id,
                ControleFuccs.statut,
            )
            .order_by(None)
            .where(*filters)
            .subquery()
        )

        total_result = await db.execute(
            select(func.count(base.c.id))
        )

        draft_result = await db.execute(
            select(func.count(base.c.id))
            .where(
                func.upper(
                    func.coalesce(
                        base.c.statut,
                        "",
                    )
                ) == "BROUILLON"
            )
        )

        finalized_result = await db.execute(
            select(func.count(base.c.id))
            .where(
                func.upper(
                    func.coalesce(
                        base.c.statut,
                        "",
                    )
                ) == "FINALISE"
            )
        )

        complete_result = await db.execute(
            select(func.count(ControleFuccs.id))
            .select_from(ControleFuccs)
            .join(
                DossierVerification,
                DossierVerification.id
                == ControleFuccs.dossier_verification_id,
            )
            .join(
                FicheCollecte,
                FicheCollecte.id
                == DossierVerification.fiche_collecte_id,
            )
            .join(
                MissionCollecte,
                MissionCollecte.id
                == FicheCollecte.mission_id,
            )
            .join(
                Campagne,
                Campagne.id
                == MissionCollecte.campagne_id,
            )
            .join(
                ZoneAdministrative,
                ZoneAdministrative.id
                == MissionCollecte.zone_id,
            )
            .outerjoin(
                Entreprise,
                Entreprise.id
                == FicheCollecte.entreprise_id,
            )
            .join(
                GrilleFuccs,
                GrilleFuccs.id
                == ControleFuccs.grille_fuccs_id,
            )
            .where(
                *filters,
                (
                    select(func.count(NoteCritere.id))
                    .where(
                        NoteCritere.controle_fuccs_id
                        == ControleFuccs.id
                    )
                    .correlate(ControleFuccs)
                    .scalar_subquery()
                )
                ==
                (
                    select(func.count(CritereFuccs.id))
                    .select_from(CritereFuccs)
                    .join(
                        RubriqueFuccs,
                        RubriqueFuccs.id
                        == CritereFuccs.rubrique_fuccs_id,
                    )
                    .where(
                        RubriqueFuccs.grille_fuccs_id
                        == ControleFuccs.grille_fuccs_id
                    )
                    .correlate(ControleFuccs)
                    .scalar_subquery()
                ),
            )
        )

        total = int(total_result.scalar_one() or 0)
        drafts = int(draft_result.scalar_one() or 0)
        finalized = int(
            finalized_result.scalar_one() or 0
        )
        complete_notes = int(
            complete_result.scalar_one() or 0
        )

        return {
            "total": total,
            "drafts": drafts,
            "finalized": finalized,
            "complete_notes": complete_notes,
            "incomplete_notes": max(
                total - complete_notes,
                0,
            ),
        }

    @staticmethod
    async def control_context(
        db: AsyncSession,
        control_id: UUID,
    ):
        result = await db.execute(
            FuccsWorkspaceRepository
            .base_control_query()
            .where(
                ControleFuccs.id == control_id
            )
        )

        return result.one_or_none()

    @staticmethod
    async def eligible_verifications(
        db: AsyncSession,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ):
        controls_count = (
            select(func.count(ControleFuccs.id))
            .where(
                ControleFuccs.dossier_verification_id
                == DossierVerification.id
            )
            .correlate(DossierVerification)
            .scalar_subquery()
        )

        latest_control_id = (
            select(ControleFuccs.id)
            .where(
                ControleFuccs.dossier_verification_id
                == DossierVerification.id
            )
            .order_by(
                ControleFuccs.created_at.desc()
            )
            .limit(1)
            .correlate(DossierVerification)
            .scalar_subquery()
        )

        latest_control_status = (
            select(ControleFuccs.statut)
            .where(
                ControleFuccs.dossier_verification_id
                == DossierVerification.id
            )
            .order_by(
                ControleFuccs.created_at.desc()
            )
            .limit(1)
            .correlate(DossierVerification)
            .scalar_subquery()
        )

        filters = [
            DossierVerification.date_fin.is_not(None),
            DossierVerification.avis.in_(
                ADMISSIBLE_OPINIONS
            ),
        ]

        if search and search.strip():
            pattern = f"%{search.strip()}%"

            filters.append(
                or_(
                    MissionCollecte.code.ilike(pattern),
                    Campagne.code.ilike(pattern),
                    Campagne.nom.ilike(pattern),
                    ZoneAdministrative.nom.ilike(pattern),
                    Entreprise.identifiant_national.ilike(pattern),
                    Entreprise.raison_sociale.ilike(pattern),
                    Entreprise.nom_commercial.ilike(pattern),
                )
            )

        query = (
            select(
                DossierVerification.id.label("dossier_id"),
                DossierVerification.avis.label(
                    "verification_opinion"
                ),
                DossierVerification.niveau_risque.label(
                    "verification_risk"
                ),
                DossierVerification.date_fin.label(
                    "verification_closed_on"
                ),
                FicheCollecte.id.label("fiche_id"),
                FicheCollecte.numero_revision.label(
                    "fiche_revision"
                ),
                FicheCollecte.mission_id.label("mission_id"),
                MissionCollecte.code.label("mission_code"),
                Campagne.code.label("campaign_code"),
                Campagne.nom.label("campaign_name"),
                ZoneAdministrative.nom.label("zone_name"),
                Entreprise.id.label("entreprise_id"),
                Entreprise.identifiant_national.label(
                    "entreprise_identifiant"
                ),
                Entreprise.raison_sociale.label(
                    "entreprise_name"
                ),
                Entreprise.nom_commercial.label(
                    "entreprise_trade_name"
                ),
                controls_count.label("controls_count"),
                latest_control_id.label("latest_control_id"),
                latest_control_status.label(
                    "latest_control_status"
                ),
            )
            .select_from(DossierVerification)
            .join(
                FicheCollecte,
                FicheCollecte.id
                == DossierVerification.fiche_collecte_id,
            )
            .join(
                MissionCollecte,
                MissionCollecte.id
                == FicheCollecte.mission_id,
            )
            .join(
                Campagne,
                Campagne.id
                == MissionCollecte.campagne_id,
            )
            .join(
                ZoneAdministrative,
                ZoneAdministrative.id
                == MissionCollecte.zone_id,
            )
            .outerjoin(
                Entreprise,
                Entreprise.id
                == FicheCollecte.entreprise_id,
            )
            .where(*filters)
            .order_by(
                DossierVerification.date_fin.desc().nullslast(),
                DossierVerification.created_at.desc(),
            )
        )

        result = await db.execute(
            query.limit(limit).offset(offset)
        )

        count_result = await db.execute(
            select(func.count(DossierVerification.id))
            .select_from(DossierVerification)
            .join(
                FicheCollecte,
                FicheCollecte.id
                == DossierVerification.fiche_collecte_id,
            )
            .join(
                MissionCollecte,
                MissionCollecte.id
                == FicheCollecte.mission_id,
            )
            .join(
                Campagne,
                Campagne.id
                == MissionCollecte.campagne_id,
            )
            .join(
                ZoneAdministrative,
                ZoneAdministrative.id
                == MissionCollecte.zone_id,
            )
            .outerjoin(
                Entreprise,
                Entreprise.id
                == FicheCollecte.entreprise_id,
            )
            .where(*filters)
        )

        return (
            result.all(),
            int(count_result.scalar_one() or 0),
        )
