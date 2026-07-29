from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alerte import Alerte
from app.models.dossier_veille import DossierVeille
from app.models.echeance import Echeance
from app.models.rapport_veille import RapportVeille
from app.repositories.watch_workspace_repository import WatchWorkspaceRepository
from app.schemas.watch_workspace import (
    AlertWorkspaceItem, AlertWorkspaceResponse, AlertWorkspaceSummary,
    DeadlineWorkspaceItem, DeadlineWorkspaceResponse, DeadlineWorkspaceSummary,
    WatchCaseWorkspaceItem, WatchCaseWorkspaceResponse,
    WatchFilters, WatchFormOptions, WatchOption,
    WatchReportWorkspaceItem, WatchReportWorkspaceResponse,
)
from app.services.veille_service import WatchService


LEVEL_LABELS = {
    1: "Information",
    2: "Surveillance",
    3: "Urgence",
    4: "Critique",
}


class WatchWorkspaceService:
    @staticmethod
    async def filters(db: AsyncSession):
        return WatchFilters(
            deadline_types=await WatchWorkspaceRepository.distinct_values(db, Echeance.type_echeance),
            deadline_statuses=await WatchWorkspaceRepository.distinct_values(db, Echeance.statut),
            alert_types=await WatchWorkspaceRepository.distinct_values(db, Alerte.type_alerte),
            alert_statuses=await WatchWorkspaceRepository.distinct_values(db, Alerte.statut),
            watch_case_statuses=await WatchWorkspaceRepository.distinct_values(db, DossierVeille.statut),
            watch_case_priorities=await WatchWorkspaceRepository.distinct_values(db, DossierVeille.priorite),
            report_types=await WatchWorkspaceRepository.distinct_values(db, RapportVeille.type_rapport),
            report_statuses=await WatchWorkspaceRepository.distinct_values(db, RapportVeille.statut),
        )

    @staticmethod
    async def form_options(db: AsyncSession):
        users = await WatchWorkspaceRepository.active_users(db)
        certs = await WatchWorkspaceRepository.certifications(db)

        return WatchFormOptions(
            users=[
                WatchOption(
                    id=u.id,
                    label=" ".join(p for p in (u.prenoms, u.nom) if p).strip() or u.email,
                    subtitle=" · ".join(v for v in (u.fonction, u.email) if v) or None,
                )
                for u in users
            ],
            certifications=[
                WatchOption(
                    id=r.id,
                    label=f"{r.raison_sociale or r.nom_commercial or 'Entreprise'} · {r.identifiant_national}",
                    subtitle=" · ".join(v for v in (r.numero_certificat, r.code, r.nom) if v) or None,
                )
                for r in certs
            ],
        )

    @staticmethod
    async def deadlines(db: AsyncSession, **filters):
        payload = await WatchService.list_deadlines(db, **filters)
        items = []

        for item in payload.items:
            resource = await WatchWorkspaceRepository.resource_context(
                db,
                resource_type=item.ressource_type,
                resource_id=item.ressource_id,
            )
            items.append(
                DeadlineWorkspaceItem(
                    **item.model_dump(),
                    resource_label=resource["label"],
                    resource_subtitle=resource["subtitle"],
                    resource_route=resource["route"],
                    responsable_name=await WatchWorkspaceRepository.user_name(db, item.responsable_id),
                )
            )

        return DeadlineWorkspaceResponse(
            total=payload.total,
            limit=payload.limit,
            offset=payload.offset,
            summary=DeadlineWorkspaceSummary(
                **await WatchWorkspaceRepository.deadline_summary(db)
            ),
            items=items,
        )

    @staticmethod
    async def alerts(db: AsyncSession, **filters):
        payload = await WatchService.list_alerts(db, **filters)
        items = []

        for item in payload.items:
            resource = await WatchWorkspaceRepository.resource_context(
                db,
                resource_type=item.ressource_type,
                resource_id=item.ressource_id,
            )
            items.append(
                AlertWorkspaceItem(
                    **item.model_dump(),
                    level_label=LEVEL_LABELS.get(item.niveau),
                    resource_label=resource["label"],
                    resource_subtitle=resource["subtitle"],
                    resource_route=resource["route"],
                    responsable_name=await WatchWorkspaceRepository.user_name(db, item.responsable_id),
                )
            )

        return AlertWorkspaceResponse(
            total=payload.total,
            limit=payload.limit,
            offset=payload.offset,
            summary=AlertWorkspaceSummary(
                **await WatchWorkspaceRepository.alert_summary(db)
            ),
            items=items,
        )

    @staticmethod
    async def watch_cases(db: AsyncSession, **filters):
        payload = await WatchService.list_watch_cases(db, **filters)
        items = []

        for item in payload.items:
            row = await WatchWorkspaceRepository.watch_case_context(db, item.id)
            if row is None:
                continue

            responsible = " ".join(
                p for p in (row.responsible_first_names, row.responsible_last_name) if p
            ).strip() or row.responsible_email

            organization = (
                f"{row.organization_name} ({row.organization_acronym})"
                if row.organization_name and row.organization_acronym
                else row.organization_name or row.organization_acronym
            )

            items.append(
                WatchCaseWorkspaceItem(
                    **item.model_dump(),
                    certification_identifier=row.identifiant_national,
                    certificate_number=row.numero_certificat,
                    expiry_date=row.date_expiration,
                    enterprise_name=row.raison_sociale or row.nom_commercial,
                    standard_code=row.standard_code,
                    organization_name=organization,
                    responsable_name=responsible,
                )
            )

        return WatchCaseWorkspaceResponse(
            total=payload.total,
            limit=payload.limit,
            offset=payload.offset,
            items=items,
        )

    @staticmethod
    async def reports(db: AsyncSession, **filters):
        payload = await WatchService.list_reports(db, **filters)
        items = []

        for item in payload.items:
            prepared = await WatchWorkspaceRepository.user_name(db, item.prepare_par_id)
            validated = await WatchWorkspaceRepository.user_name(db, item.valide_par_id)

            items.append(
                WatchReportWorkspaceItem(
                    **item.model_dump(),
                    prepare_par_name=prepared,
                    valide_par_name=validated,
                )
            )

        return WatchReportWorkspaceResponse(
            total=payload.total,
            limit=payload.limit,
            offset=payload.offset,
            items=items,
        )
