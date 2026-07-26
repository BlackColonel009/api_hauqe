"""
Service métier — Pilotage / Tableaux de bord.

NIVEAUX
-------
- opérationnel : quotidien / hebdomadaire ;
- tactique : mensuel ;
- stratégique : trimestriel ;
- annuel : bilan de l'année ;
- baromètre : photographie nationale sur période ;
- public : agrégats explicitement autorisés.

SÉCURITÉ DU TABLEAU PUBLIC
--------------------------
Le endpoint `/api/v1/public/indicators` n'interroge jamais librement les
ressources détaillées à la demande du client.

Il exige :
1. une règle publiée `PUBLIC_DASHBOARD_INDICATORS` ;
2. `allowed_indicators` dans les paramètres de cette règle ;
3. une période explicitement publiée dans la règle ;
4. une `publication` au statut PUBLIEE liée à la règle.

Le résultat public ne contient :
- aucun identifiant d'entreprise/certification ;
- aucun numéro de certificat ;
- aucun contact ;
- aucun document ;
- aucune coordonnée individuelle.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import (
    AnnualDashboardResponse,
    BarometerResponse,
    DashboardFiltersResponse,
    DecisionSynthesis,
    DistributionItem,
    GeographicAggregate,
    IndicatorDefinition,
    IndicatorDefinitionsResponse,
    KpiValue,
    OperationalDashboardResponse,
    PeriodResponse,
    PriorityAction,
    PublicIndicatorItem,
    PublicIndicatorsResponse,
    StrategicDashboardResponse,
    TacticalDashboardResponse,
    TimeSeriesPoint,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def percent(part: int | Decimal, total: int | Decimal) -> Decimal | None:
    if not total:
        return None
    return (
        Decimal(str(part))
        * Decimal("100")
        / Decimal(str(total))
    ).quantize(Decimal("0.01"))


def delta(current, previous):
    if current is None or previous is None:
        return None
    return Decimal(str(current)) - Decimal(str(previous))


def distribution(rows) -> list[DistributionItem]:
    total = sum(int(row.value or 0) for row in rows)
    return [
        DistributionItem(
            key=str(row.key),
            label=str(row.key),
            value=int(row.value or 0),
            percentage=percent(int(row.value or 0), total),
        )
        for row in rows
    ]


def period_response(start: date, end: date, label: str) -> PeriodResponse:
    return PeriodResponse(start=start, end=end, label=label)


def month_bounds(year: int, month: int) -> tuple[date, date]:
    if month < 1 or month > 12:
        raise HTTPException(422, "month doit être compris entre 1 et 12.")
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def previous_month_bounds(year: int, month: int) -> tuple[date, date]:
    if month == 1:
        return month_bounds(year - 1, 12)
    return month_bounds(year, month - 1)


def quarter_bounds(year: int, quarter: int) -> tuple[date, date]:
    if quarter not in {1, 2, 3, 4}:
        raise HTTPException(422, "quarter doit être compris entre 1 et 4.")
    start_month = (quarter - 1) * 3 + 1
    end_month = start_month + 2
    end_day = calendar.monthrange(year, end_month)[1]
    return date(year, start_month, 1), date(year, end_month, end_day)


def previous_quarter_bounds(year: int, quarter: int) -> tuple[date, date]:
    if quarter == 1:
        return quarter_bounds(year - 1, 4)
    return quarter_bounds(year, quarter - 1)


def year_bounds(year: int) -> tuple[date, date]:
    return date(year, 1, 1), date(year, 12, 31)


def parse_rule_date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Paramètre public manquant : {field}.",
        )
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Paramètre public invalide : {field}.",
        ) from exc


class DashboardService:

    # ========================================================
    # DÉFINITIONS / FILTRES
    # ========================================================

    @staticmethod
    async def filters(db: AsyncSession) -> DashboardFiltersResponse:
        zones, sectors, norms, bodies = (
            await DashboardRepository.filter_catalog(db)
        )
        return DashboardFiltersResponse(
            zones=zones,
            sectors=sectors,
            norms=norms,
            certification_bodies=bodies,
        )

    @staticmethod
    def definitions() -> IndicatorDefinitionsResponse:
        return IndicatorDefinitionsResponse(
            items=[
                IndicatorDefinition(
                    key="enterprises_count",
                    label="Entreprises enregistrées",
                    description=(
                        "Nombre d'entreprises présentes dans le registre BNEC."
                    ),
                    source_tables=["entreprises"],
                    public_candidate=True,
                ),
                IndicatorDefinition(
                    key="certifications_count",
                    label="Certifications enregistrées",
                    description=(
                        "Nombre de certifications présentes dans le registre."
                    ),
                    source_tables=["certifications"],
                    public_candidate=True,
                ),
                IndicatorDefinition(
                    key="active_certifications_count",
                    label="Certifications actives",
                    description=(
                        "Certifications dont le statut courant appartient "
                        "au vocabulaire actif reconnu par le backend."
                    ),
                    source_tables=["certifications"],
                    public_candidate=True,
                ),
                IndicatorDefinition(
                    key="strategic_expiring_90d_enterprises",
                    label="Entreprises avec certification stratégique à échéance ≤ 90 jours",
                    description=(
                        "Entreprises distinctes portant au moins une certification "
                        "stratégique dont l'expiration intervient dans les 90 jours."
                    ),
                    source_tables=["certifications"],
                    public_candidate=False,
                ),
                IndicatorDefinition(
                    key="controls_to_plan",
                    label="Contrôles FUCCS à planifier",
                    description=(
                        "Dossiers de vérification ouverts sans contrôle FUCCS créé."
                    ),
                    source_tables=["dossiers_verification", "controles_fuccs"],
                    public_candidate=False,
                ),
                IndicatorDefinition(
                    key="national_infc_average",
                    label="INFC national moyen",
                    description=(
                        "Moyenne des derniers résultats INFC validés par certification. "
                        "Aucun dossier non validé n'est inclus."
                    ),
                    source_tables=["resultats_infc", "certifications"],
                    public_candidate=True,
                ),
                IndicatorDefinition(
                    key="certification_statuses",
                    label="Répartition des certifications par statut",
                    description="Comptage agrégé par statut courant.",
                    source_tables=["certifications"],
                    public_candidate=True,
                ),
                IndicatorDefinition(
                    key="sncc_classes",
                    label="Répartition SNCC par classe",
                    description=(
                        "Répartition fondée sur le classement SNCC courant "
                        "de chaque certification."
                    ),
                    source_tables=["classements_sncc"],
                    public_candidate=True,
                ),
                IndicatorDefinition(
                    key="sncc_risks",
                    label="Répartition SNCC par niveau de risque",
                    description=(
                        "Répartition fondée sur le classement SNCC courant."
                    ),
                    source_tables=["classements_sncc"],
                    public_candidate=False,
                ),
                IndicatorDefinition(
                    key="by_region",
                    label="Répartition géographique",
                    description=(
                        "Agrégats par zone administrative du siège de l'entreprise."
                    ),
                    source_tables=[
                        "entreprises",
                        "zones_administratives",
                        "certifications",
                    ],
                    public_candidate=True,
                ),
                IndicatorDefinition(
                    key="by_sector",
                    label="Répartition sectorielle",
                    description=(
                        "Certifications agrégées selon l'activité principale "
                        "de l'entreprise."
                    ),
                    source_tables=["entreprises", "certifications"],
                    public_candidate=True,
                ),
                IndicatorDefinition(
                    key="by_norm",
                    label="Répartition par référentiel/norme",
                    description="Certifications agrégées par code de norme.",
                    source_tables=["certifications", "normes"],
                    public_candidate=True,
                ),
                IndicatorDefinition(
                    key="by_certification_body",
                    label="Répartition par organisme certificateur",
                    description="Certifications agrégées par organisme.",
                    source_tables=["certifications", "organismes"],
                    public_candidate=True,
                ),
            ]
        )

    # ========================================================
    # COMPOSANTS COMMUNS
    # ========================================================

    @staticmethod
    async def geography(db: AsyncSession) -> list[GeographicAggregate]:
        rows = await DashboardRepository.by_region(db)
        items = []
        for row in rows:
            name = row.zone_name or "ZONE NON RENSEIGNÉE"
            avg = (
                Decimal(str(row.average_infc)).quantize(Decimal("0.01"))
                if row.average_infc is not None
                else None
            )
            items.append(
                GeographicAggregate(
                    zone_id=row.zone_id,
                    zone_code=row.zone_code,
                    zone_name=name,
                    zone_type=row.zone_type,
                    latitude=(
                        Decimal(str(row.latitude))
                        if row.latitude is not None else None
                    ),
                    longitude=(
                        Decimal(str(row.longitude))
                        if row.longitude is not None else None
                    ),
                    enterprises=int(row.enterprises or 0),
                    certifications=int(row.certifications or 0),
                    active_certifications=int(
                        row.active_certifications or 0
                    ),
                    average_infc=avg,
                )
            )
        return items

    @staticmethod
    async def base_distributions(db: AsyncSession):
        status_rows = (
            await DashboardRepository.certification_status_distribution(
                db
            )
        )
        sncc_class_rows = await DashboardRepository.sncc_distribution(
            db,
            field="classe",
        )
        sncc_risk_rows = await DashboardRepository.sncc_distribution(
            db,
            field="risque",
        )
        sector_rows = await DashboardRepository.distribution_by_sector(db)
        norm_rows = await DashboardRepository.distribution_by_norm(db)
        body_rows = await DashboardRepository.distribution_by_body(db)

        return {
            "certification_statuses": distribution(status_rows),
            "sncc_classes": distribution(sncc_class_rows),
            "sncc_risks": distribution(sncc_risk_rows),
            "by_sector": distribution(sector_rows),
            "by_norm": distribution(norm_rows),
            "by_certification_body": distribution(body_rows),
        }

    # ========================================================
    # OPÉRATIONNEL
    # ========================================================

    @staticmethod
    async def operational(
        db: AsyncSession,
        *,
        days: int,
        zone_id: UUID | None,
        sector: str | None,
        norm_id: UUID | None,
        organisme_id: UUID | None,
    ) -> OperationalDashboardResponse:
        if days < 1 or days > 90:
            raise HTTPException(422, "days doit être compris entre 1 et 90.")

        end = date.today()
        start = end - timedelta(days=days - 1)
        previous_end = start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=days - 1)

        enterprises = await DashboardRepository.count_enterprises(
            db,
            zone_id=zone_id,
            sector=sector,
        )
        certifications = await DashboardRepository.count_certifications(
            db,
            zone_id=zone_id,
            sector=sector,
            norm_id=norm_id,
            organisme_id=organisme_id,
        )
        active_certifications = (
            await DashboardRepository.count_certifications(
                db,
                zone_id=zone_id,
                sector=sector,
                norm_id=norm_id,
                organisme_id=organisme_id,
                active_only=True,
            )
        )
        current_new_certifications = (
            await DashboardRepository.count_certifications(
                db,
                zone_id=zone_id,
                sector=sector,
                norm_id=norm_id,
                organisme_id=organisme_id,
                created_start=start,
                created_end=end,
            )
        )
        previous_new_certifications = (
            await DashboardRepository.count_certifications(
                db,
                zone_id=zone_id,
                sector=sector,
                norm_id=norm_id,
                organisme_id=organisme_id,
                created_start=previous_start,
                created_end=previous_end,
            )
        )

        controls_to_plan = (
            await DashboardRepository.controls_to_plan_count(db)
        )
        expiring_risk = (
            await DashboardRepository.count_strategic_certifications_expiring(
                db,
                start_date=end,
                end_date=end + timedelta(days=90),
            )
        )
        active_alerts = await DashboardRepository.active_alert_count(db)
        critical_alerts = await DashboardRepository.active_alert_count(
            db,
            level=4,
        )
        overdue = await DashboardRepository.overdue_deadline_count(db)
        infc_avg, _ = await DashboardRepository.latest_infc_average(
            db,
            zone_id=zone_id,
            sector=sector,
            norm_id=norm_id,
            organisme_id=organisme_id,
        )

        status_rows = (
            await DashboardRepository.certification_status_distribution(
                db,
                zone_id=zone_id,
                sector=sector,
                norm_id=norm_id,
                organisme_id=organisme_id,
            )
        )

        deadline_buckets = await DashboardRepository.deadline_bucket_counts(
            db
        )
        alerts, deadlines = await DashboardRepository.priority_actions(
            db,
            limit=8,
        )

        actions: list[PriorityAction] = []
        for row in alerts:
            actions.append(
                PriorityAction(
                    type="ALERTE",
                    level=row.niveau,
                    title=row.titre or "Alerte",
                    due_date=None,
                    resource_type=row.ressource_type,
                    resource_id=row.ressource_id,
                )
            )
        for row in deadlines:
            actions.append(
                PriorityAction(
                    type="ECHEANCE",
                    level=4,
                    title=row.titre or "Échéance dépassée",
                    due_date=row.date_echeance,
                    resource_type=row.ressource_type,
                    resource_id=row.ressource_id,
                )
            )
        actions = actions[:10]

        recent_rows = await DashboardRepository.recent_certifications(
            db,
            limit=10,
        )
        recent = [
            {
                "certification_id": str(row.id),
                "enterprise_id": str(row.enterprise_id),
                "certification_code": (
                    row.identifiant_national or row.numero_certificat
                ),
                "enterprise_name": row.raison_sociale,
                "norm": row.norm_code,
                "certification_body": row.organisme_name,
                "status": row.statut,
                "expiration_date": (
                    row.date_expiration.isoformat()
                    if row.date_expiration else None
                ),
                "updated_at": (
                    row.updated_at.isoformat()
                    if row.updated_at else None
                ),
            }
            for row in recent_rows
        ]

        series_rows = await DashboardRepository.monthly_certification_series(
            db,
            start_date=end - timedelta(days=180),
            end_date=end,
        )

        return OperationalDashboardResponse(
            generated_at=utcnow(),
            period=period_response(
                start,
                end,
                f"{days} dernier(s) jour(s)",
            ),
            kpis=[
                KpiValue(
                    key="enterprises_count",
                    label="Entreprises enregistrées",
                    value=enterprises,
                    unit="entreprises",
                ),
                KpiValue(
                    key="certifications_count",
                    label="Certifications enregistrées",
                    value=certifications,
                    unit="certifications",
                ),
                KpiValue(
                    key="active_certifications_count",
                    label="Certifications actives",
                    value=active_certifications,
                    unit="certifications",
                    definition=(
                        "Statuts courants reconnus comme actifs par le backend."
                    ),
                ),
                KpiValue(
                    key="new_certifications",
                    label="Nouvelles certifications sur la période",
                    value=current_new_certifications,
                    previous_value=previous_new_certifications,
                    delta=delta(
                        current_new_certifications,
                        previous_new_certifications,
                    ),
                ),
                KpiValue(
                    key="strategic_expiring_90d_enterprises",
                    label="Entreprises à vigilance stratégique ≤ 90 jours",
                    value=expiring_risk,
                    unit="entreprises",
                ),
                KpiValue(
                    key="controls_to_plan",
                    label="Contrôles FUCCS à planifier",
                    value=controls_to_plan,
                    unit="dossiers",
                ),
                KpiValue(
                    key="active_alerts",
                    label="Alertes actives",
                    value=active_alerts,
                    unit="alertes",
                ),
                KpiValue(
                    key="critical_alerts",
                    label="Alertes critiques",
                    value=critical_alerts,
                    unit="alertes",
                ),
                KpiValue(
                    key="overdue_deadlines",
                    label="Échéances en retard",
                    value=overdue,
                    unit="échéances",
                ),
            ],
            certification_statuses=distribution(status_rows),
            deadline_buckets=[
                DistributionItem(
                    key="EXPIREE",
                    label="Dépassées / expiration",
                    value=deadline_buckets["expired"],
                ),
                DistributionItem(
                    key="J30",
                    label="≤ 30 jours",
                    value=deadline_buckets["d30"],
                ),
                DistributionItem(
                    key="J90",
                    label="31 à 90 jours",
                    value=deadline_buckets["d90"],
                ),
                DistributionItem(
                    key="J180",
                    label="91 à 180 jours",
                    value=deadline_buckets["d180"],
                ),
            ],
            infc_national_average=infc_avg,
            priority_actions=actions,
            recent_certifications=recent,
            activity_series=[
                TimeSeriesPoint(
                    period=row.period,
                    value=int(row.value or 0),
                )
                for row in series_rows
            ],
        )

    # ========================================================
    # TACTIQUE MENSUEL
    # ========================================================

    @staticmethod
    async def tactical(
        db: AsyncSession,
        *,
        year: int,
        month: int,
    ) -> TacticalDashboardResponse:
        start, end = month_bounds(year, month)
        previous_start, previous_end = previous_month_bounds(year, month)

        current = await DashboardRepository.period_counts(
            db,
            start_date=start,
            end_date=end,
        )
        previous = await DashboardRepository.period_counts(
            db,
            start_date=previous_start,
            end_date=previous_end,
        )

        new_certifications = await DashboardRepository.count_certifications(
            db,
            created_start=start,
            created_end=end,
        )
        previous_new_certifications = (
            await DashboardRepository.count_certifications(
                db,
                created_start=previous_start,
                created_end=previous_end,
            )
        )

        return TacticalDashboardResponse(
            generated_at=utcnow(),
            period=period_response(
                start,
                end,
                f"{year}-{month:02d}",
            ),
            kpis=[
                KpiValue(
                    key="submitted_collection_forms",
                    label="Fiches soumises",
                    value=current["fiches_submitted"],
                    previous_value=previous["fiches_submitted"],
                    delta=delta(
                        current["fiches_submitted"],
                        previous["fiches_submitted"],
                    ),
                ),
                KpiValue(
                    key="new_certifications",
                    label="Nouvelles certifications",
                    value=new_certifications,
                    previous_value=previous_new_certifications,
                    delta=delta(
                        new_certifications,
                        previous_new_certifications,
                    ),
                ),
                KpiValue(
                    key="fuccs_finalized",
                    label="Contrôles FUCCS finalisés",
                    value=current["fuccs_finalized"],
                    previous_value=previous["fuccs_finalized"],
                    delta=delta(
                        current["fuccs_finalized"],
                        previous["fuccs_finalized"],
                    ),
                ),
                KpiValue(
                    key="integrations_completed",
                    label="Intégrations BNEC terminées",
                    value=current["integrations_completed"],
                    previous_value=previous["integrations_completed"],
                    delta=delta(
                        current["integrations_completed"],
                        previous["integrations_completed"],
                    ),
                ),
                KpiValue(
                    key="alerts_created",
                    label="Alertes détectées",
                    value=current["alerts_created"],
                    previous_value=previous["alerts_created"],
                    delta=delta(
                        current["alerts_created"],
                        previous["alerts_created"],
                    ),
                ),
            ],
            collection={
                "submitted_forms": current["fiches_submitted"],
            },
            verification={
                "opened": current["verifications_opened"],
                "closed": current["verifications_closed"],
            },
            fuccs={
                "finalized": current["fuccs_finalized"],
                "average_rate": current["fuccs_average_rate"],
            },
            validation={
                "decisions": current["validation_decisions"],
            },
            integration={
                "completed": current["integrations_completed"],
                "new_certifications": new_certifications,
            },
            watch={
                "alerts_created": current["alerts_created"],
                "alerts_resolved": current["alerts_resolved"],
                "renewal_decisions": current["renewal_decisions"],
            },
            quality={
                "reviews_validated": current[
                    "quality_reviews_validated"
                ],
                "open_action_plans": current["open_action_plans"],
            },
        )

    # ========================================================
    # STRATÉGIQUE TRIMESTRIEL
    # ========================================================

    @staticmethod
    async def strategic(
        db: AsyncSession,
        *,
        year: int,
        quarter: int,
    ) -> StrategicDashboardResponse:
        start, end = quarter_bounds(year, quarter)
        previous_start, previous_end = previous_quarter_bounds(
            year,
            quarter,
        )

        enterprises = await DashboardRepository.count_enterprises(db)
        certifications = await DashboardRepository.count_certifications(db)
        active_certifications = (
            await DashboardRepository.count_certifications(
                db,
                active_only=True,
            )
        )
        current_infc = await DashboardRepository.infc_average_in_period(
            db,
            start_date=start,
            end_date=end,
        )
        previous_infc = await DashboardRepository.infc_average_in_period(
            db,
            start_date=previous_start,
            end_date=previous_end,
        )
        latest_infc, latest_infc_count = (
            await DashboardRepository.latest_infc_average(db)
        )
        critical_alerts = await DashboardRepository.active_alert_count(
            db,
            level=4,
        )
        overdue = await DashboardRepository.overdue_deadline_count(db)

        dist = await DashboardService.base_distributions(db)
        geo = await DashboardService.geography(db)

        # Série INFC sur quatre trimestres terminant au trimestre demandé.
        series = []
        series_year = year
        series_quarter = quarter
        for _ in range(4):
            q_start, q_end = quarter_bounds(
                series_year,
                series_quarter,
            )
            value = await DashboardRepository.infc_average_in_period(
                db,
                start_date=q_start,
                end_date=q_end,
            )
            series.append(
                TimeSeriesPoint(
                    period=f"{series_year}-T{series_quarter}",
                    value=value or Decimal("0"),
                )
            )
            if series_quarter == 1:
                series_year -= 1
                series_quarter = 4
            else:
                series_quarter -= 1
        series.reverse()

        findings = [
            f"{enterprises} entreprise(s) enregistrée(s) dans la BNEC.",
            f"{certifications} certification(s) enregistrée(s), dont "
            f"{active_certifications} avec un statut actif reconnu.",
        ]
        if latest_infc is not None:
            findings.append(
                f"INFC moyen des derniers résultats validés : {latest_infc}."
            )

        risks = []
        recommendations = []
        if critical_alerts > 0:
            risks.append(
                f"{critical_alerts} alerte(s) critique(s) sont actuellement actives."
            )
            recommendations.append(
                "Traiter prioritairement les alertes critiques et tracer leur résolution."
            )
        if overdue > 0:
            risks.append(
                f"{overdue} échéance(s) active(s) sont dépassée(s)."
            )
            recommendations.append(
                "Régulariser les échéances dépassées et affecter un responsable."
            )
        if latest_infc_count == 0:
            risks.append(
                "Aucun résultat INFC validé n'est disponible pour le calcul national."
            )
            recommendations.append(
                "Finaliser et valider les résultats INFC avant toute interprétation nationale."
            )

        if not risks:
            risks.append(
                "Aucun signal critique automatique n'est détecté par les indicateurs suivis."
            )
        if not recommendations:
            recommendations.append(
                "Maintenir la surveillance des échéances, alertes et tendances INFC."
            )

        return StrategicDashboardResponse(
            generated_at=utcnow(),
            period=period_response(
                start,
                end,
                f"{year}-T{quarter}",
            ),
            kpis=[
                KpiValue(
                    key="enterprises_count",
                    label="Entreprises",
                    value=enterprises,
                ),
                KpiValue(
                    key="certifications_count",
                    label="Certifications",
                    value=certifications,
                ),
                KpiValue(
                    key="active_certifications_count",
                    label="Certifications actives",
                    value=active_certifications,
                ),
                KpiValue(
                    key="validated_infc_latest_count",
                    label="Certifications avec INFC validé courant",
                    value=latest_infc_count,
                ),
                KpiValue(
                    key="quarter_infc_average",
                    label="INFC moyen du trimestre",
                    value=current_infc,
                    previous_value=previous_infc,
                    delta=delta(current_infc, previous_infc),
                ),
                KpiValue(
                    key="critical_alerts",
                    label="Alertes critiques actives",
                    value=critical_alerts,
                ),
                KpiValue(
                    key="overdue_deadlines",
                    label="Échéances dépassées",
                    value=overdue,
                ),
            ],
            certification_statuses=dist["certification_statuses"],
            sncc_classes=dist["sncc_classes"],
            sncc_risks=dist["sncc_risks"],
            by_region=geo,
            by_sector=dist["by_sector"],
            by_norm=dist["by_norm"],
            by_certification_body=dist["by_certification_body"],
            infc_series=series,
            synthesis=DecisionSynthesis(
                findings=findings,
                major_risks=risks,
                priority_recommendations=recommendations,
            ),
        )

    # ========================================================
    # ANNUEL
    # ========================================================

    @staticmethod
    async def annual(
        db: AsyncSession,
        *,
        year: int,
    ) -> AnnualDashboardResponse:
        start, end = year_bounds(year)
        previous_start, previous_end = year_bounds(year - 1)

        new_certifications = await DashboardRepository.count_certifications(
            db,
            created_start=start,
            created_end=end,
        )
        previous_new_certifications = (
            await DashboardRepository.count_certifications(
                db,
                created_start=previous_start,
                created_end=previous_end,
            )
        )
        current_period = await DashboardRepository.period_counts(
            db,
            start_date=start,
            end_date=end,
        )
        previous_period = await DashboardRepository.period_counts(
            db,
            start_date=previous_start,
            end_date=previous_end,
        )
        latest_infc, infc_count = (
            await DashboardRepository.latest_infc_average(db)
        )
        dist = await DashboardService.base_distributions(db)
        geo = await DashboardService.geography(db)
        governance = await DashboardRepository.annual_governance_counts(
            db,
            start_date=start,
            end_date=end,
        )

        quarterly_certifications = []
        quarterly_infc = []
        for quarter in (1, 2, 3, 4):
            q_start, q_end = quarter_bounds(year, quarter)
            q_cert = await DashboardRepository.count_certifications(
                db,
                created_start=q_start,
                created_end=q_end,
            )
            q_infc = await DashboardRepository.infc_average_in_period(
                db,
                start_date=q_start,
                end_date=q_end,
            )
            quarterly_certifications.append(
                TimeSeriesPoint(
                    period=f"{year}-T{quarter}",
                    value=q_cert,
                )
            )
            quarterly_infc.append(
                TimeSeriesPoint(
                    period=f"{year}-T{quarter}",
                    value=q_infc or Decimal("0"),
                )
            )

        return AnnualDashboardResponse(
            generated_at=utcnow(),
            year=year,
            period=period_response(start, end, str(year)),
            kpis=[
                KpiValue(
                    key="new_certifications",
                    label="Nouvelles certifications",
                    value=new_certifications,
                    previous_value=previous_new_certifications,
                    delta=delta(
                        new_certifications,
                        previous_new_certifications,
                    ),
                ),
                KpiValue(
                    key="submitted_collection_forms",
                    label="Fiches de collecte soumises",
                    value=current_period["fiches_submitted"],
                    previous_value=previous_period["fiches_submitted"],
                    delta=delta(
                        current_period["fiches_submitted"],
                        previous_period["fiches_submitted"],
                    ),
                ),
                KpiValue(
                    key="integrations_completed",
                    label="Intégrations BNEC",
                    value=current_period["integrations_completed"],
                    previous_value=previous_period["integrations_completed"],
                    delta=delta(
                        current_period["integrations_completed"],
                        previous_period["integrations_completed"],
                    ),
                ),
                KpiValue(
                    key="renewal_decisions",
                    label="Décisions de renouvellement",
                    value=current_period["renewal_decisions"],
                    previous_value=previous_period["renewal_decisions"],
                    delta=delta(
                        current_period["renewal_decisions"],
                        previous_period["renewal_decisions"],
                    ),
                ),
                KpiValue(
                    key="latest_national_infc_average",
                    label="INFC national moyen courant",
                    value=latest_infc,
                    definition=(
                        f"Basé sur {infc_count} dernier(s) résultat(s) INFC validé(s)."
                    ),
                ),
            ],
            quarterly_certifications=quarterly_certifications,
            quarterly_infc=quarterly_infc,
            certification_statuses=dist["certification_statuses"],
            sncc_classes=dist["sncc_classes"],
            by_region=geo,
            quality={
                "reviews_validated": current_period[
                    "quality_reviews_validated"
                ],
                "open_action_plans_at_generation": current_period[
                    "open_action_plans"
                ],
            },
            governance={
                "incidents_declared": governance[
                    "incidents_declared"
                ],
                "quality_reviews_created": governance[
                    "quality_reviews_created"
                ],
            },
            continuity={
                "backup_failures": governance["backup_failures"],
            },
        )

    # ========================================================
    # BAROMÈTRE NATIONAL
    # ========================================================

    @staticmethod
    async def barometer(
        db: AsyncSession,
        *,
        start_date: date,
        end_date: date,
    ) -> BarometerResponse:
        if end_date < start_date:
            raise HTTPException(422, "Période du baromètre incohérente.")

        enterprises = await DashboardRepository.count_enterprises(db)
        certifications = await DashboardRepository.count_certifications(db)
        active = await DashboardRepository.count_certifications(
            db,
            active_only=True,
        )
        infc_avg, infc_count = (
            await DashboardRepository.latest_infc_average(db)
        )
        dist = await DashboardService.base_distributions(db)
        geo = await DashboardService.geography(db)

        notes = [
            (
                "Le baromètre présente des composantes nationales séparées. "
                "Aucun indice composite supplémentaire n'est calculé sans "
                "règle institutionnelle publiée."
            ),
            (
                "L'INFC national moyen utilise uniquement les derniers "
                "résultats INFC validés."
            ),
        ]

        return BarometerResponse(
            generated_at=utcnow(),
            period=period_response(
                start_date,
                end_date,
                f"{start_date.isoformat()} → {end_date.isoformat()}",
            ),
            certifications_count=certifications,
            active_certifications_count=active,
            enterprises_count=enterprises,
            validated_infc_count=infc_count,
            national_infc_average=infc_avg,
            certification_statuses=dist["certification_statuses"],
            sncc_classes=dist["sncc_classes"],
            sncc_risks=dist["sncc_risks"],
            by_region=geo,
            by_sector=dist["by_sector"],
            by_norm=dist["by_norm"],
            by_certification_body=dist["by_certification_body"],
            notes=notes,
        )

    # ========================================================
    # PUBLIC AGRÉGÉ AUTORISÉ
    # ========================================================

    @staticmethod
    async def public_indicators(
        db: AsyncSession,
    ) -> PublicIndicatorsResponse:
        rule = await DashboardRepository.public_dashboard_rule(db)
        if rule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucun tableau de bord public n'est actuellement publié.",
            )

        publication = (
            await DashboardRepository.published_public_dashboard_approval(
                db,
                rule_id=rule.id,
            )
        )
        if publication is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucun tableau de bord public n'est actuellement publié.",
            )

        params = (
            rule.parametres
            if isinstance(rule.parametres, dict)
            else {}
        )
        allowed = params.get("allowed_indicators")
        if not isinstance(allowed, list) or not allowed:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "La publication publique ne contient aucun indicateur autorisé."
                ),
            )

        allowed = {
            str(key).strip()
            for key in allowed
            if str(key).strip()
        }

        start = parse_rule_date(
            params.get("period_start"),
            "period_start",
        )
        end = parse_rule_date(
            params.get("period_end"),
            "period_end",
        )
        if end < start:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Période publique invalide.",
            )

        # Candidats sûrs : uniquement valeurs agrégées.
        enterprises = await DashboardRepository.count_enterprises(db)
        certifications = await DashboardRepository.count_certifications(db)
        active = await DashboardRepository.count_certifications(
            db,
            active_only=True,
        )
        infc_avg, _ = await DashboardRepository.latest_infc_average(db)
        dist = await DashboardService.base_distributions(db)
        geo = await DashboardService.geography(db)

        candidates: dict[str, tuple[str, Any]] = {
            "enterprises_count": (
                "Entreprises enregistrées",
                enterprises,
            ),
            "certifications_count": (
                "Certifications enregistrées",
                certifications,
            ),
            "active_certifications_count": (
                "Certifications actives",
                active,
            ),
            "national_infc_average": (
                "INFC national moyen",
                infc_avg,
            ),
            "certification_statuses": (
                "Répartition des certifications par statut",
                [
                    item.model_dump()
                    for item in dist["certification_statuses"]
                ],
            ),
            "sncc_classes": (
                "Répartition SNCC par classe",
                [
                    item.model_dump()
                    for item in dist["sncc_classes"]
                ],
            ),
            "by_sector": (
                "Répartition sectorielle",
                [
                    item.model_dump()
                    for item in dist["by_sector"]
                ],
            ),
            "by_norm": (
                "Répartition par norme",
                [
                    item.model_dump()
                    for item in dist["by_norm"]
                ],
            ),
            "by_certification_body": (
                "Répartition par organisme certificateur",
                [
                    item.model_dump()
                    for item in dist["by_certification_body"]
                ],
            ),
            "by_region": (
                "Répartition géographique",
                [
                    {
                        # Aucun UUID/coordonnée individuelle n'est exposé.
                        "zone_name": item.zone_name,
                        "zone_type": item.zone_type,
                        "enterprises": item.enterprises,
                        "certifications": item.certifications,
                        "active_certifications": (
                            item.active_certifications
                        ),
                        "average_infc": item.average_infc,
                    }
                    for item in geo
                ],
            ),
        }

        # Même si une clé non sûre est ajoutée dans la règle par erreur,
        # elle n'est pas exposée si elle n'existe pas dans `candidates`.
        indicators = [
            PublicIndicatorItem(
                key=key,
                label=candidates[key][0],
                value=candidates[key][1],
            )
            for key in sorted(allowed)
            if key in candidates
        ]

        if not indicators:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Aucun indicateur autorisé ne correspond au catalogue public sûr."
                ),
            )

        return PublicIndicatorsResponse(
            generated_at=utcnow(),
            publication_id=publication.id,
            publication_date=publication.date_publication,
            rule_id=rule.id,
            rule_version=rule.version,
            period=period_response(
                start,
                end,
                f"{start.isoformat()} → {end.isoformat()}",
            ),
            indicators=indicators,
            disclaimer=(
                str(params.get("disclaimer")).strip()
                if params.get("disclaimer")
                else (
                    "Données agrégées publiées après validation institutionnelle. "
                    "Aucune donnée individuelle ou confidentielle n'est exposée."
                )
            ),
        )
