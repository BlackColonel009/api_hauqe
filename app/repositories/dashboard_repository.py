"""
Repository PostgreSQL — Pilotage / Tableaux de bord.

RÔLE
----
Centraliser les agrégations SQL utilisées par les six niveaux de pilotage.

CHOIX D'ARCHITECTURE
--------------------
- aucune table de cache ou de matérialisation n'est ajoutée ;
- aucune migration n'est nécessaire ;
- les agrégats sont calculés depuis les tables métier existantes ;
- les "derniers" résultats INFC et SNCC utilisent des sous-requêtes
  `row_number()` afin d'éviter les doubles comptes historiques ;
- les filtres région/secteur/norme/organisme sont appliqués au niveau
  Certification/Entreprise quand ils sont pertinents.

Pour des volumes futurs élevés, les mêmes contrats API pourront être conservés
et les agrégations déplacées vers des vues matérialisées sans modifier le
frontend.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Numeric,
    and_,
    case,
    cast,
    distinct,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alerte import Alerte
from app.models.certification import Certification
from app.models.classement_sncc import ClassementSncc
from app.models.controle_fuccs import ControleFuccs
from app.models.dossier_verification import DossierVerification
from app.models.echeance import Echeance
from app.models.entreprise import Entreprise
from app.models.fiche_collecte import FicheCollecte
from app.models.incident import Incident
from app.models.integration_bnec import IntegrationBnec
from app.models.norme import Norme
from app.models.organisme import Organisme
from app.models.plan_action import PlanAction
from app.models.publication import Publication
from app.models.regle_metier import RegleMetier
from app.models.renouvellement_certification import RenouvellementCertification
from app.models.resultat_infc import ResultatInfc
from app.models.revue_qualite import RevueQualite
from app.models.sauvegarde import Sauvegarde
from app.models.validation import Validation
from app.models.zone_administrative import ZoneAdministrative


ACTIVE_CERT_STATUSES = {
    "ACTIVE",
    "ACTIF",
    "VALIDE",
    "VALIDE_ACTIVE",
}

FINAL_FUCCS_STATUSES = {"FINALISE", "FINALISEE"}
FINAL_INTEGRATION_STATUSES = {"INTEGREE", "INTEGRE"}
ACTIVE_ALERT_STATUSES = {"NOUVELLE", "AFFECTEE", "EN_COURS"}
ACTIVE_DEADLINE_STATUSES = {"PLANIFIEE", "EN_COURS"}


class DashboardRepository:

    # ========================================================
    # FILTRES PARTAGÉS
    # ========================================================

    @staticmethod
    def certification_filters(
        *,
        zone_id: UUID | None,
        sector: str | None,
        norm_id: UUID | None,
        organisme_id: UUID | None,
    ):
        filters = []
        if norm_id:
            filters.append(Certification.norme_id == norm_id)
        if organisme_id:
            filters.append(Certification.organisme_id == organisme_id)
        if zone_id:
            filters.append(Entreprise.zone_siege_id == zone_id)
        if sector:
            filters.append(
                func.upper(Entreprise.activite_principale)
                == sector.strip().upper()
            )
        return filters

    @staticmethod
    async def filter_catalog(db: AsyncSession):
        zones_result = await db.execute(
            select(
                ZoneAdministrative.id,
                ZoneAdministrative.code,
                ZoneAdministrative.nom,
                ZoneAdministrative.type_zone,
            )
            .where(
                or_(
                    ZoneAdministrative.statut.is_(None),
                    ZoneAdministrative.statut == "ACTIF",
                )
            )
            .order_by(
                ZoneAdministrative.type_zone,
                ZoneAdministrative.nom,
            )
        )
        zones = [
            {
                "id": str(row.id),
                "code": row.code,
                "name": row.nom,
                "type": row.type_zone,
            }
            for row in zones_result.all()
        ]

        sectors_result = await db.execute(
            select(distinct(Entreprise.activite_principale))
            .where(
                Entreprise.activite_principale.is_not(None),
                Entreprise.activite_principale != "",
            )
            .order_by(Entreprise.activite_principale)
        )
        sectors = [
            row[0]
            for row in sectors_result.all()
            if row[0]
        ]

        norms_result = await db.execute(
            select(
                Norme.id,
                Norme.code,
                Norme.nom,
                Norme.version,
            )
            .order_by(Norme.code, Norme.version)
        )
        norms = [
            {
                "id": str(row.id),
                "code": row.code,
                "name": row.nom,
                "version": row.version,
            }
            for row in norms_result.all()
        ]

        bodies_result = await db.execute(
            select(
                Organisme.id,
                Organisme.identifiant_national,
                Organisme.nom_officiel,
                Organisme.sigle,
            )
            .order_by(Organisme.nom_officiel)
        )
        bodies = [
            {
                "id": str(row.id),
                "code": row.identifiant_national,
                "name": row.nom_officiel,
                "sigle": row.sigle,
            }
            for row in bodies_result.all()
        ]

        return zones, sectors, norms, bodies

    # ========================================================
    # AGRÉGATS DE BASE
    # ========================================================

    @staticmethod
    async def count_enterprises(
        db: AsyncSession,
        *,
        zone_id: UUID | None = None,
        sector: str | None = None,
    ) -> int:
        filters = []
        if zone_id:
            filters.append(Entreprise.zone_siege_id == zone_id)
        if sector:
            filters.append(
                func.upper(Entreprise.activite_principale)
                == sector.strip().upper()
            )

        result = await db.execute(
            select(func.count(Entreprise.id)).where(*filters)
        )
        return int(result.scalar_one())

    @staticmethod
    async def count_certifications(
        db: AsyncSession,
        *,
        zone_id: UUID | None = None,
        sector: str | None = None,
        norm_id: UUID | None = None,
        organisme_id: UUID | None = None,
        active_only: bool = False,
        created_start: date | None = None,
        created_end: date | None = None,
    ) -> int:
        filters = DashboardRepository.certification_filters(
            zone_id=zone_id,
            sector=sector,
            norm_id=norm_id,
            organisme_id=organisme_id,
        )
        if active_only:
            filters.append(
                func.upper(Certification.statut).in_(
                    list(ACTIVE_CERT_STATUSES)
                )
            )
        if created_start:
            filters.append(func.date(Certification.created_at) >= created_start)
        if created_end:
            filters.append(func.date(Certification.created_at) <= created_end)

        stmt = (
            select(func.count(distinct(Certification.id)))
            .select_from(Certification)
            .join(
                Entreprise,
                Entreprise.id == Certification.entreprise_id,
            )
            .where(*filters)
        )
        result = await db.execute(stmt)
        return int(result.scalar_one())

    @staticmethod
    async def controls_to_plan_count(
        db: AsyncSession,
        *,
        zone_id: UUID | None = None,
        sector: str | None = None,
    ) -> int:
        """
        Dossiers de vérification ouverts qui ne possèdent encore aucun contrôle
        FUCCS. Région et secteur sont appliqués via la fiche de collecte.
        """
        control_exists = (
            select(ControleFuccs.id)
            .where(
                ControleFuccs.dossier_verification_id
                == DossierVerification.id
            )
            .exists()
        )

        filters = [
            DossierVerification.date_fin.is_(None),
            ~control_exists,
        ]

        if zone_id:
            filters.append(
                Entreprise.zone_siege_id == zone_id
            )
        if sector:
            filters.append(
                func.upper(Entreprise.activite_principale)
                == sector.strip().upper()
            )

        stmt = (
            select(func.count(DossierVerification.id))
            .select_from(DossierVerification)
            .join(
                FicheCollecte,
                FicheCollecte.id
                == DossierVerification.fiche_collecte_id,
            )
            .outerjoin(
                Entreprise,
                Entreprise.id == FicheCollecte.entreprise_id,
            )
            .where(*filters)
        )

        result = await db.execute(stmt)
        return int(result.scalar_one())

    @staticmethod
    async def count_strategic_certifications_expiring(
        db: AsyncSession,
        *,
        start_date: date,
        end_date: date,
        zone_id: UUID | None = None,
        sector: str | None = None,
        norm_id: UUID | None = None,
        organisme_id: UUID | None = None,
    ) -> int:
        filters = DashboardRepository.certification_filters(
            zone_id=zone_id,
            sector=sector,
            norm_id=norm_id,
            organisme_id=organisme_id,
        )
        filters.extend(
            [
                Certification.certification_strategique.is_(True),
                Certification.date_expiration >= start_date,
                Certification.date_expiration <= end_date,
                func.upper(Certification.statut).in_(
                    list(ACTIVE_CERT_STATUSES)
                ),
            ]
        )

        result = await db.execute(
            select(
                func.count(
                    distinct(Certification.entreprise_id)
                )
            )
            .select_from(Certification)
            .join(
                Entreprise,
                Entreprise.id == Certification.entreprise_id,
            )
            .where(*filters)
        )
        return int(result.scalar_one())

    @staticmethod
    async def certification_status_distribution(
        db: AsyncSession,
        *,
        zone_id: UUID | None = None,
        sector: str | None = None,
        norm_id: UUID | None = None,
        organisme_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        filters = DashboardRepository.certification_filters(
            zone_id=zone_id,
            sector=sector,
            norm_id=norm_id,
            organisme_id=organisme_id,
        )
        if start_date:
            filters.append(func.date(Certification.created_at) >= start_date)
        if end_date:
            filters.append(func.date(Certification.created_at) <= end_date)

        result = await db.execute(
            select(
                func.coalesce(Certification.statut, "NON_RENSEIGNE").label("key"),
                func.count(distinct(Certification.id)).label("value"),
            )
            .select_from(Certification)
            .join(
                Entreprise,
                Entreprise.id == Certification.entreprise_id,
            )
            .where(*filters)
            .group_by(Certification.statut)
            .order_by(func.count(distinct(Certification.id)).desc())
        )
        return result.all()

    @staticmethod
    async def recent_certifications(
        db: AsyncSession,
        *,
        limit: int = 10,
        zone_id: UUID | None = None,
        sector: str | None = None,
        norm_id: UUID | None = None,
        organisme_id: UUID | None = None,
    ):
        filters = DashboardRepository.certification_filters(
            zone_id=zone_id,
            sector=sector,
            norm_id=norm_id,
            organisme_id=organisme_id,
        )

        result = await db.execute(
            select(
                Certification.id,
                Certification.identifiant_national,
                Certification.numero_certificat,
                Certification.statut,
                Certification.date_expiration,
                Certification.updated_at,
                Entreprise.id.label("enterprise_id"),
                Entreprise.raison_sociale,
                Norme.code.label("norm_code"),
                Organisme.nom_officiel.label("organisme_name"),
            )
            .join(
                Entreprise,
                Entreprise.id == Certification.entreprise_id,
            )
            .join(
                Norme,
                Norme.id == Certification.norme_id,
            )
            .join(
                Organisme,
                Organisme.id == Certification.organisme_id,
            )
            .where(*filters)
            .order_by(Certification.updated_at.desc())
            .limit(limit)
        )
        return result.all()

    # ========================================================
    # EXPIRATIONS DE CERTIFICATIONS — DASHBOARD
    # ========================================================

    @staticmethod
    async def certification_expiration_buckets(
        db: AsyncSession,
        *,
        zone_id: UUID | None = None,
        sector: str | None = None,
        norm_id: UUID | None = None,
        organisme_id: UUID | None = None,
    ):
        today = date.today()

        filters = DashboardRepository.certification_filters(
            zone_id=zone_id,
            sector=sector,
            norm_id=norm_id,
            organisme_id=organisme_id,
        )
        filters.extend(
            [
                Certification.date_expiration.is_not(None),
                func.upper(Certification.statut).in_(
                    list(ACTIVE_CERT_STATUSES)
                ),
            ]
        )

        result = await db.execute(
            select(
                func.sum(
                    case(
                        (
                            Certification.date_expiration < today,
                            1,
                        ),
                        else_=0,
                    )
                ).label("expired"),
                func.sum(
                    case(
                        (
                            and_(
                                Certification.date_expiration >= today,
                                Certification.date_expiration
                                <= today
                                + __import__("datetime").timedelta(days=30),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("d30"),
                func.sum(
                    case(
                        (
                            and_(
                                Certification.date_expiration
                                > today
                                + __import__("datetime").timedelta(days=30),
                                Certification.date_expiration
                                <= today
                                + __import__("datetime").timedelta(days=90),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("d90"),
                func.sum(
                    case(
                        (
                            and_(
                                Certification.date_expiration
                                > today
                                + __import__("datetime").timedelta(days=90),
                                Certification.date_expiration
                                <= today
                                + __import__("datetime").timedelta(days=180),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("d180"),
            )
            .select_from(Certification)
            .join(
                Entreprise,
                Entreprise.id == Certification.entreprise_id,
            )
            .where(*filters)
        )

        row = result.one()

        return {
            "expired": int(row.expired or 0),
            "d30": int(row.d30 or 0),
            "d90": int(row.d90 or 0),
            "d180": int(row.d180 or 0),
        }

    @staticmethod
    async def expiring_certifications(
        db: AsyncSession,
        *,
        days: int = 180,
        limit: int = 10,
        zone_id: UUID | None = None,
        sector: str | None = None,
        norm_id: UUID | None = None,
        organisme_id: UUID | None = None,
    ):
        today = date.today()
        end_date = today + __import__("datetime").timedelta(days=days)

        filters = DashboardRepository.certification_filters(
            zone_id=zone_id,
            sector=sector,
            norm_id=norm_id,
            organisme_id=organisme_id,
        )
        filters.extend(
            [
                Certification.date_expiration.is_not(None),
                Certification.date_expiration >= today,
                Certification.date_expiration <= end_date,
                func.upper(Certification.statut).in_(
                    list(ACTIVE_CERT_STATUSES)
                ),
            ]
        )

        result = await db.execute(
            select(
                Certification.id,
                Certification.identifiant_national,
                Certification.numero_certificat,
                Certification.date_expiration,
                Entreprise.id.label("enterprise_id"),
                Entreprise.raison_sociale,
                Norme.code.label("norm_code"),
                Organisme.nom_officiel.label("organisme_name"),
            )
            .select_from(Certification)
            .join(
                Entreprise,
                Entreprise.id == Certification.entreprise_id,
            )
            .join(
                Norme,
                Norme.id == Certification.norme_id,
            )
            .join(
                Organisme,
                Organisme.id == Certification.organisme_id,
            )
            .where(*filters)
            .order_by(Certification.date_expiration.asc())
            .limit(limit)
        )

        return result.all()

    # ========================================================
    # ÉCHÉANCES / ALERTES
    # ========================================================

    @staticmethod
    async def deadline_bucket_counts(db: AsyncSession):
        today = date.today()
        result = await db.execute(
            select(
                func.sum(
                    case(
                        (
                            and_(
                                Echeance.date_echeance < today,
                                Echeance.statut.in_(
                                    list(ACTIVE_DEADLINE_STATUSES)
                                ),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("expired"),
                func.sum(
                    case(
                        (
                            and_(
                                Echeance.date_echeance >= today,
                                Echeance.date_echeance <= today.replace(
                                    year=today.year
                                ) + __import__("datetime").timedelta(days=30),
                                Echeance.statut.in_(
                                    list(ACTIVE_DEADLINE_STATUSES)
                                ),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("d30"),
                func.sum(
                    case(
                        (
                            and_(
                                Echeance.date_echeance >
                                today + __import__("datetime").timedelta(days=30),
                                Echeance.date_echeance <=
                                today + __import__("datetime").timedelta(days=90),
                                Echeance.statut.in_(
                                    list(ACTIVE_DEADLINE_STATUSES)
                                ),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("d90"),
                func.sum(
                    case(
                        (
                            and_(
                                Echeance.date_echeance >
                                today + __import__("datetime").timedelta(days=90),
                                Echeance.date_echeance <=
                                today + __import__("datetime").timedelta(days=180),
                                Echeance.statut.in_(
                                    list(ACTIVE_DEADLINE_STATUSES)
                                ),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("d180"),
            )
        )
        row = result.one()
        return {
            "expired": int(row.expired or 0),
            "d30": int(row.d30 or 0),
            "d90": int(row.d90 or 0),
            "d180": int(row.d180 or 0),
        }

    @staticmethod
    def resource_scope_filters(
        resource_type_column,
        resource_id_column,
        *,
        zone_id: UUID | None = None,
        sector: str | None = None,
        norm_id: UUID | None = None,
        organisme_id: UUID | None = None,
    ):
        if not any(
            [zone_id, sector, norm_id, organisme_id]
        ):
            return []

        cert_filters = DashboardRepository.certification_filters(
            zone_id=zone_id,
            sector=sector,
            norm_id=norm_id,
            organisme_id=organisme_id,
        )

        cert_ids = (
            select(Certification.id)
            .select_from(Certification)
            .join(
                Entreprise,
                Entreprise.id == Certification.entreprise_id,
            )
            .where(*cert_filters)
        )

        enterprise_ids = (
            select(distinct(Certification.entreprise_id))
            .select_from(Certification)
            .join(
                Entreprise,
                Entreprise.id == Certification.entreprise_id,
            )
            .where(*cert_filters)
        )

        normalized_type = func.upper(
            func.coalesce(resource_type_column, "")
        )

        return [
            or_(
                and_(
                    normalized_type.in_(
                        ["CERTIFICATION", "CERTIFICATIONS"]
                    ),
                    resource_id_column.in_(cert_ids),
                ),
                and_(
                    normalized_type.in_(
                        ["ENTREPRISE", "ENTREPRISES"]
                    ),
                    resource_id_column.in_(enterprise_ids),
                ),
            )
        ]

    @staticmethod
    async def active_alert_count(
        db: AsyncSession,
        *,
        level: int | None = None,
        zone_id: UUID | None = None,
        sector: str | None = None,
        norm_id: UUID | None = None,
        organisme_id: UUID | None = None,
    ) -> int:
        filters = [
            Alerte.statut.in_(list(ACTIVE_ALERT_STATUSES))
        ]
        filters.extend(
            DashboardRepository.resource_scope_filters(
                Alerte.ressource_type,
                Alerte.ressource_id,
                zone_id=zone_id,
                sector=sector,
                norm_id=norm_id,
                organisme_id=organisme_id,
            )
        )

        if level:
            filters.append(Alerte.niveau == level)

        result = await db.execute(
            select(func.count(Alerte.id)).where(*filters)
        )
        return int(result.scalar_one())

    @staticmethod
    async def overdue_deadline_count(
        db: AsyncSession,
        *,
        zone_id: UUID | None = None,
        sector: str | None = None,
        norm_id: UUID | None = None,
        organisme_id: UUID | None = None,
    ) -> int:
        filters = [
            Echeance.date_echeance < date.today(),
            Echeance.statut.in_(list(ACTIVE_DEADLINE_STATUSES)),
        ]
        filters.extend(
            DashboardRepository.resource_scope_filters(
                Echeance.ressource_type,
                Echeance.ressource_id,
                zone_id=zone_id,
                sector=sector,
                norm_id=norm_id,
                organisme_id=organisme_id,
            )
        )

        result = await db.execute(
            select(func.count(Echeance.id)).where(*filters)
        )
        return int(result.scalar_one())

    @staticmethod
    async def priority_actions(
        db: AsyncSession,
        *,
        limit: int = 10,
        zone_id: UUID | None = None,
        sector: str | None = None,
        norm_id: UUID | None = None,
        organisme_id: UUID | None = None,
    ):
        alert_filters = [
            Alerte.statut.in_(list(ACTIVE_ALERT_STATUSES))
        ]
        alert_filters.extend(
            DashboardRepository.resource_scope_filters(
                Alerte.ressource_type,
                Alerte.ressource_id,
                zone_id=zone_id,
                sector=sector,
                norm_id=norm_id,
                organisme_id=organisme_id,
            )
        )

        deadline_filters = [
            Echeance.statut.in_(list(ACTIVE_DEADLINE_STATUSES)),
            Echeance.date_echeance <= date.today(),
        ]
        deadline_filters.extend(
            DashboardRepository.resource_scope_filters(
                Echeance.ressource_type,
                Echeance.ressource_id,
                zone_id=zone_id,
                sector=sector,
                norm_id=norm_id,
                organisme_id=organisme_id,
            )
        )

        alerts = await db.execute(
            select(
                Alerte.id,
                Alerte.niveau,
                Alerte.titre,
                Alerte.ressource_type,
                Alerte.ressource_id,
                Alerte.date_detection,
            )
            .where(*alert_filters)
            .order_by(
                Alerte.niveau.desc().nullslast(),
                Alerte.date_detection.asc().nullslast(),
            )
            .limit(limit)
        )

        deadlines = await db.execute(
            select(
                Echeance.id,
                Echeance.titre,
                Echeance.ressource_type,
                Echeance.ressource_id,
                Echeance.date_echeance,
            )
            .where(*deadline_filters)
            .order_by(Echeance.date_echeance.asc())
            .limit(limit)
        )

        return list(alerts.all()), list(deadlines.all())

    # ========================================================
    # INFC — DERNIER RÉSULTAT VALIDÉ PAR CERTIFICATION
    # ========================================================

    @staticmethod
    def latest_validated_infc_subquery():
        return (
            select(
                ResultatInfc.id.label("id"),
                ResultatInfc.certification_id.label("certification_id"),
                ResultatInfc.score_global.label("score_global"),
                ResultatInfc.niveau.label("niveau"),
                ResultatInfc.date_validation.label("date_validation"),
                func.row_number()
                .over(
                    partition_by=ResultatInfc.certification_id,
                    order_by=(
                        ResultatInfc.date_validation.desc().nullslast(),
                        ResultatInfc.created_at.desc(),
                    ),
                )
                .label("rn"),
            )
            .where(
                ResultatInfc.statut == "VALIDE",
                ResultatInfc.date_validation.is_not(None),
            )
            .subquery()
        )

    @staticmethod
    async def latest_infc_average(
        db: AsyncSession,
        *,
        zone_id: UUID | None = None,
        sector: str | None = None,
        norm_id: UUID | None = None,
        organisme_id: UUID | None = None,
    ) -> tuple[Decimal | None, int]:
        latest = DashboardRepository.latest_validated_infc_subquery()

        filters = DashboardRepository.certification_filters(
            zone_id=zone_id,
            sector=sector,
            norm_id=norm_id,
            organisme_id=organisme_id,
        )
        filters.append(latest.c.rn == 1)

        result = await db.execute(
            select(
                func.avg(latest.c.score_global),
                func.count(latest.c.id),
            )
            .select_from(latest)
            .join(
                Certification,
                Certification.id == latest.c.certification_id,
            )
            .join(
                Entreprise,
                Entreprise.id == Certification.entreprise_id,
            )
            .where(*filters)
        )
        avg_value, count_value = result.one()
        return (
            Decimal(str(avg_value)).quantize(Decimal("0.01"))
            if avg_value is not None else None,
            int(count_value or 0),
        )

    @staticmethod
    async def infc_average_in_period(
        db: AsyncSession,
        *,
        start_date: date,
        end_date: date,
    ) -> Decimal | None:
        result = await db.execute(
            select(func.avg(ResultatInfc.score_global)).where(
                ResultatInfc.statut == "VALIDE",
                ResultatInfc.date_validation >= start_date,
                ResultatInfc.date_validation <= end_date,
            )
        )
        value = result.scalar_one_or_none()
        return (
            Decimal(str(value)).quantize(Decimal("0.01"))
            if value is not None else None
        )

    # ========================================================
    # SNCC — CLASSEMENT COURANT
    # ========================================================

    @staticmethod
    def current_sncc_subquery():
        return (
            select(
                ClassementSncc.id.label("id"),
                ClassementSncc.certification_id.label("certification_id"),
                ClassementSncc.classe.label("classe"),
                ClassementSncc.statut_administratif.label(
                    "statut_administratif"
                ),
                ClassementSncc.niveau_risque.label("niveau_risque"),
                ClassementSncc.date_effet.label("date_effet"),
                func.row_number()
                .over(
                    partition_by=ClassementSncc.certification_id,
                    order_by=(
                        case(
                            (ClassementSncc.date_fin.is_(None), 0),
                            else_=1,
                        ),
                        ClassementSncc.date_effet.desc().nullslast(),
                        ClassementSncc.created_at.desc(),
                    ),
                )
                .label("rn"),
            )
            .subquery()
        )

    @staticmethod
    async def sncc_distribution(
        db: AsyncSession,
        *,
        field: str,
    ):
        current = DashboardRepository.current_sncc_subquery()
        column = (
            current.c.classe
            if field == "classe"
            else current.c.niveau_risque
        )
        result = await db.execute(
            select(
                func.coalesce(column, "NON_RENSEIGNE").label("key"),
                func.count(current.c.id).label("value"),
            )
            .where(current.c.rn == 1)
            .group_by(column)
            .order_by(func.count(current.c.id).desc())
        )
        return result.all()

    # ========================================================
    # AGRÉGATS GÉOGRAPHIQUES / SECTORIELS / NORMES / OC
    # ========================================================

    @staticmethod
    async def by_region(db: AsyncSession):
        latest = DashboardRepository.latest_validated_infc_subquery()

        result = await db.execute(
            select(
                ZoneAdministrative.id.label("zone_id"),
                ZoneAdministrative.code.label("zone_code"),
                ZoneAdministrative.nom.label("zone_name"),
                ZoneAdministrative.type_zone.label("zone_type"),
                ZoneAdministrative.latitude,
                ZoneAdministrative.longitude,
                func.count(
                    distinct(Entreprise.id)
                ).label("enterprises"),
                func.count(
                    distinct(Certification.id)
                ).label("certifications"),
                func.count(
                    distinct(
                        case(
                            (
                                func.upper(Certification.statut).in_(
                                    list(ACTIVE_CERT_STATUSES)
                                ),
                                Certification.id,
                            )
                        )
                    )
                ).label("active_certifications"),
                func.avg(
                    case(
                        (
                            latest.c.rn == 1,
                            latest.c.score_global,
                        )
                    )
                ).label("average_infc"),
            )
            .select_from(Entreprise)
            .join(
                ZoneAdministrative,
                ZoneAdministrative.id == Entreprise.zone_siege_id,
                isouter=True,
            )
            .join(
                Certification,
                Certification.entreprise_id == Entreprise.id,
                isouter=True,
            )
            .join(
                latest,
                latest.c.certification_id == Certification.id,
                isouter=True,
            )
            .group_by(
                ZoneAdministrative.id,
                ZoneAdministrative.code,
                ZoneAdministrative.nom,
                ZoneAdministrative.type_zone,
                ZoneAdministrative.latitude,
                ZoneAdministrative.longitude,
            )
            .order_by(
                func.count(distinct(Certification.id)).desc()
            )
        )
        return result.all()

    @staticmethod
    async def distribution_by_sector(db: AsyncSession):
        result = await db.execute(
            select(
                func.coalesce(
                    Entreprise.activite_principale,
                    "NON_RENSEIGNE",
                ).label("key"),
                func.count(
                    distinct(Certification.id)
                ).label("value"),
            )
            .select_from(Entreprise)
            .join(
                Certification,
                Certification.entreprise_id == Entreprise.id,
            )
            .group_by(
                Entreprise.activite_principale
            )
            .order_by(func.count(distinct(Certification.id)).desc())
        )
        return result.all()

    @staticmethod
    async def distribution_by_norm(db: AsyncSession):
        result = await db.execute(
            select(
                Norme.code.label("key"),
                func.count(Certification.id).label("value"),
            )
            .select_from(Certification)
            .join(Norme, Norme.id == Certification.norme_id)
            .group_by(Norme.code)
            .order_by(func.count(Certification.id).desc())
        )
        return result.all()

    @staticmethod
    async def distribution_by_body(db: AsyncSession):
        result = await db.execute(
            select(
                Organisme.nom_officiel.label("key"),
                func.count(Certification.id).label("value"),
            )
            .select_from(Certification)
            .join(
                Organisme,
                Organisme.id == Certification.organisme_id,
            )
            .group_by(Organisme.nom_officiel)
            .order_by(func.count(Certification.id).desc())
        )
        return result.all()

    # ========================================================
    # ACTIVITÉ / PÉRIODES
    # ========================================================

    @staticmethod
    async def monthly_certification_series(
        db: AsyncSession,
        *,
        start_date: date,
        end_date: date,
        zone_id: UUID | None = None,
        sector: str | None = None,
        norm_id: UUID | None = None,
        organisme_id: UUID | None = None,
    ):
        period = func.to_char(
            Certification.created_at,
            "YYYY-MM",
        ).label("period")

        filters = DashboardRepository.certification_filters(
            zone_id=zone_id,
            sector=sector,
            norm_id=norm_id,
            organisme_id=organisme_id,
        )
        filters.extend(
            [
                func.date(Certification.created_at) >= start_date,
                func.date(Certification.created_at) <= end_date,
            ]
        )

        result = await db.execute(
            select(
                period,
                func.count(Certification.id).label("value"),
            )
            .select_from(Certification)
            .join(
                Entreprise,
                Entreprise.id == Certification.entreprise_id,
            )
            .where(*filters)
            .group_by(period)
            .order_by(period)
        )
        return result.all()

    @staticmethod
    async def period_counts(
        db: AsyncSession,
        *,
        start_date: date,
        end_date: date,
    ) -> dict:
        fiches = await db.execute(
            select(func.count(FicheCollecte.id)).where(
                FicheCollecte.soumise_at.is_not(None),
                func.date(FicheCollecte.soumise_at) >= start_date,
                func.date(FicheCollecte.soumise_at) <= end_date,
            )
        )

        verifications_opened = await db.execute(
            select(func.count(DossierVerification.id)).where(
                DossierVerification.date_ouverture >= start_date,
                DossierVerification.date_ouverture <= end_date,
            )
        )
        verifications_closed = await db.execute(
            select(func.count(DossierVerification.id)).where(
                DossierVerification.date_fin >= start_date,
                DossierVerification.date_fin <= end_date,
            )
        )

        fuccs_count = await db.execute(
            select(func.count(ControleFuccs.id)).where(
                ControleFuccs.date_fin >= start_date,
                ControleFuccs.date_fin <= end_date,
                ControleFuccs.statut.in_(list(FINAL_FUCCS_STATUSES)),
            )
        )
        numeric_fuccs_rate = case(
            (
                ControleFuccs.taux.op("~")(
                    r"^\s*[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)\s*$"
                ),
                cast(
                    func.replace(ControleFuccs.taux, ",", "."),
                    Numeric(10, 4),
                ),
            ),
            else_=None,
        )
        fuccs_avg_result = await db.execute(
            select(func.avg(numeric_fuccs_rate)).where(
                ControleFuccs.date_fin >= start_date,
                ControleFuccs.date_fin <= end_date,
                ControleFuccs.statut.in_(list(FINAL_FUCCS_STATUSES)),
            )
        )
        fuccs_avg_value = fuccs_avg_result.scalar_one_or_none()

        validations = await db.execute(
            select(
                func.coalesce(
                    Validation.decision,
                    "NON_RENSEIGNE",
                ).label("decision"),
                func.count(Validation.id).label("value"),
            )
            .where(
                Validation.date_validation >= start_date,
                Validation.date_validation <= end_date,
            )
            .group_by(
                Validation.decision
            )
        )

        integrations = await db.execute(
            select(func.count(IntegrationBnec.id)).where(
                IntegrationBnec.date_fin >= start_date,
                IntegrationBnec.date_fin <= end_date,
                IntegrationBnec.statut.in_(
                    list(FINAL_INTEGRATION_STATUSES)
                ),
            )
        )

        alerts_created = await db.execute(
            select(func.count(Alerte.id)).where(
                Alerte.date_detection >= start_date,
                Alerte.date_detection <= end_date,
            )
        )
        alerts_resolved = await db.execute(
            select(func.count(Alerte.id)).where(
                Alerte.date_resolution >= start_date,
                Alerte.date_resolution <= end_date,
            )
        )

        renewals = await db.execute(
            select(func.count(RenouvellementCertification.id)).where(
                RenouvellementCertification.date_decision >= start_date,
                RenouvellementCertification.date_decision <= end_date,
            )
        )

        quality_reviews = await db.execute(
            select(func.count(RevueQualite.id)).where(
                RevueQualite.date_validation >= start_date,
                RevueQualite.date_validation <= end_date,
            )
        )
        action_plans_open = await db.execute(
            select(func.count(PlanAction.id)).where(
                PlanAction.date_cloture.is_(None)
            )
        )

        return {
            "fiches_submitted": int(fiches.scalar_one()),
            "verifications_opened": int(verifications_opened.scalar_one()),
            "verifications_closed": int(verifications_closed.scalar_one()),
            "fuccs_finalized": int(fuccs_count.scalar_one()),
            "fuccs_average_rate": (
                Decimal(str(fuccs_avg_value)).quantize(
                    Decimal("0.01")
                )
                if fuccs_avg_value is not None
                else None
            ),
            "validation_decisions": {
                row.decision: int(row.value)
                for row in validations.all()
            },
            "integrations_completed": int(integrations.scalar_one()),
            "alerts_created": int(alerts_created.scalar_one()),
            "alerts_resolved": int(alerts_resolved.scalar_one()),
            "renewal_decisions": int(renewals.scalar_one()),
            "quality_reviews_validated": int(quality_reviews.scalar_one()),
            "open_action_plans": int(action_plans_open.scalar_one()),
        }

    @staticmethod
    async def annual_governance_counts(
        db: AsyncSession,
        *,
        start_date: date,
        end_date: date,
    ) -> dict:
        incidents = await db.execute(
            select(func.count(Incident.id)).where(
                Incident.date_declaration >= start_date,
                Incident.date_declaration <= end_date,
            )
        )
        reviews = await db.execute(
            select(func.count(RevueQualite.id)).where(
                func.date(RevueQualite.created_at) >= start_date,
                func.date(RevueQualite.created_at) <= end_date,
            )
        )
        backups_failed = await db.execute(
            select(func.count(Sauvegarde.id)).where(
                func.date(Sauvegarde.created_at) >= start_date,
                func.date(Sauvegarde.created_at) <= end_date,
                Sauvegarde.statut.in_(["ECHEC", "ECHEC_INTEGRITE"]),
            )
        )
        return {
            "incidents_declared": int(incidents.scalar_one()),
            "quality_reviews_created": int(reviews.scalar_one()),
            "backup_failures": int(backups_failed.scalar_one()),
        }

    # ========================================================
    # PUBLICATION DU TABLEAU PUBLIC
    # ========================================================

    @staticmethod
    async def public_dashboard_rule(db: AsyncSession):
        """
        Recherche une règle publiée dont `_logical_code` vaut
        PUBLIC_DASHBOARD_INDICATORS.

        Cette méthode évite de dépendre de `code == ...` car le domaine
        Gouvernance versionne les règles avec un code physique unique.
        """
        result = await db.execute(
            select(RegleMetier)
            .where(RegleMetier.statut == "PUBLIE")
            .order_by(
                RegleMetier.date_debut_effet.desc().nullslast(),
                RegleMetier.created_at.desc(),
            )
        )
        today = date.today()
        for rule in result.scalars().all():
            params = rule.parametres if isinstance(rule.parametres, dict) else {}
            logical = str(params.get("_logical_code", rule.code or "")).upper()
            if logical != "PUBLIC_DASHBOARD_INDICATORS":
                continue
            if rule.date_debut_effet and rule.date_debut_effet > today:
                continue
            if rule.date_fin_effet and rule.date_fin_effet < today:
                continue
            return rule
        return None

    @staticmethod
    async def published_public_dashboard_approval(
        db: AsyncSession,
        *,
        rule_id: UUID,
    ) -> Publication | None:
        result = await db.execute(
            select(Publication)
            .where(
                Publication.ressource_type == "PUBLIC_DASHBOARD_RULE",
                Publication.ressource_id == rule_id,
                Publication.statut == "PUBLIEE",
                Publication.date_publication.is_not(None),
            )
            .order_by(
                Publication.date_publication.desc(),
                Publication.created_at.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()
