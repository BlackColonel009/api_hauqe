from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.collecte_workspace_repository import (
    CollecteWorkspaceRepository,
)
from app.schemas.collecte_workspace import (
    CollecteRegistryItem,
    CollecteRegistryResponse,
    CollecteRegistrySummary,
    CollecteWorkspaceFiltersResponse,
)


class CollecteWorkspaceService:
    @staticmethod
    async def filters(
        db: AsyncSession,
    ) -> CollecteWorkspaceFiltersResponse:
        payload = await CollecteWorkspaceRepository.filters(db)
        return CollecteWorkspaceFiltersResponse(**payload)

    @staticmethod
    async def registry(
        db: AsyncSession,
        *,
        search: str | None,
        campagne_id: UUID | None,
        zone_id: UUID | None,
        assigned_user_id: UUID | None,
        mission_statut: str | None,
        fiche_statut: str | None,
        sort: str,
        limit: int,
        offset: int,
    ) -> CollecteRegistryResponse:
        rows, total = await CollecteWorkspaceRepository.registry(
            db,
            search=search,
            campagne_id=campagne_id,
            zone_id=zone_id,
            assigned_user_id=assigned_user_id,
            mission_statut=mission_statut,
            fiche_statut=fiche_statut,
            sort=sort,
            limit=limit,
            offset=offset,
        )

        summary = await CollecteWorkspaceRepository.summary(
            db,
            search=search,
            campagne_id=campagne_id,
            zone_id=zone_id,
            assigned_user_id=assigned_user_id,
            mission_statut=mission_statut,
            fiche_statut=fiche_statut,
        )

        items = []

        for row in rows:
            mission = row[0]

            items.append(
                CollecteRegistryItem(
                    mission_id=mission.id,
                    mission_code=mission.code,
                    mission_object=mission.objet,
                    mission_status=mission.statut,
                    priority=mission.priorite,
                    progression=mission.progression,
                    planned_start=mission.date_debut_prevue,
                    planned_end=mission.date_fin_prevue,
                    campaign_id=mission.campagne_id,
                    campaign_code=row.campaign_code,
                    campaign_name=row.campaign_name,
                    zone_id=mission.zone_id,
                    zone_name=row.zone_name,
                    zone_type=row.zone_type,
                    assigned_names=row.assigned_names,
                    fiche_id=row.fiche_id,
                    fiche_status=row.fiche_status,
                    completeness=row.completeness,
                    revision_number=row.revision_number,
                    collected_at=row.collected_at,
                    submitted_at=row.submitted_at,
                    entreprise_id=row.entreprise_id,
                    entreprise_name=(
                        row.enterprise_name
                        or row.enterprise_trade_name
                    ),
                )
            )

        return CollecteRegistryResponse(
            total=total,
            limit=limit,
            offset=offset,
            summary=CollecteRegistrySummary(**summary),
            items=items,
        )
