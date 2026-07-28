from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.fuccs_workspace_repository import (
    FuccsWorkspaceRepository,
)
from app.schemas.fuccs_workspace import (
    FuccsControlRegistryItem,
    FuccsControlRegistryResponse,
    FuccsControlRegistrySummary,
    FuccsEligibleVerificationItem,
    FuccsEligibleVerificationsResponse,
    FuccsWorkspaceFiltersResponse,
    FuccsWorkspaceGrid,
)


class FuccsWorkspaceService:
    @staticmethod
    async def filters(
        db: AsyncSession,
    ) -> FuccsWorkspaceFiltersResponse:
        statuses = await FuccsWorkspaceRepository.statuses(
            db
        )

        grid = await FuccsWorkspaceRepository.active_grid(
            db
        )

        active_grid = None

        if grid is not None:
            rubrics, criteria, maximum = (
                await FuccsWorkspaceRepository.grid_counts(
                    db,
                    grid.id,
                )
            )

            active_grid = FuccsWorkspaceGrid(
                id=grid.id,
                code=grid.code,
                label=grid.libelle,
                version=grid.version,
                effective_date=grid.date_effet,
                publication_status=grid.statut_publication,
                rubrics_count=rubrics,
                criteria_count=criteria,
                maximum_score=maximum or 0,
            )

        return FuccsWorkspaceFiltersResponse(
            statuses=statuses,
            active_grid=active_grid,
        )

    @staticmethod
    def registry_item(
        row,
    ) -> FuccsControlRegistryItem:
        control = row[0]

        controller_name = " ".join(
            part
            for part in (
                row.controller_first_names,
                row.controller_last_name,
            )
            if part
        ).strip()

        if not controller_name:
            controller_name = row.controller_email

        return FuccsControlRegistryItem(
            control_id=control.id,
            control_status=control.statut,
            started_on=control.date_debut,
            ended_on=control.date_fin,
            raw_score=control.score_brut,
            maximum_score=control.score_maximal,
            rate=control.taux,
            synthesis=control.synthese,
            grid_id=control.grille_fuccs_id,
            grid_code=row.grid_code,
            grid_label=row.grid_label,
            grid_version=row.grid_version,
            criteria_count=int(
                row.criteria_count or 0
            ),
            dossier_id=control.dossier_verification_id,
            verification_opinion=row.verification_opinion,
            verification_risk=row.verification_risk,
            verification_closed_on=(
                row.verification_closed_on
            ),
            fiche_id=row.fiche_id,
            fiche_revision=row.fiche_revision,
            mission_id=row.mission_id,
            mission_code=row.mission_code,
            campaign_code=row.campaign_code,
            campaign_name=row.campaign_name,
            zone_name=row.zone_name,
            entreprise_id=row.entreprise_id,
            entreprise_name=(
                row.entreprise_name
                or row.entreprise_trade_name
            ),
            entreprise_identifiant=(
                row.entreprise_identifiant
            ),
            controller_id=control.controleur_id,
            controller_name=controller_name,
            notes_count=int(row.notes_count or 0),
            findings_count=int(
                row.findings_count or 0
            ),
            documents_count=int(
                row.documents_count or 0
            ),
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
    ) -> FuccsControlRegistryResponse:
        rows, total = (
            await FuccsWorkspaceRepository.registry(
                db,
                search=search,
                statut=statut,
                sort=sort,
                limit=limit,
                offset=offset,
            )
        )

        summary = (
            await FuccsWorkspaceRepository.summary(
                db,
                search=search,
                statut=statut,
            )
        )

        return FuccsControlRegistryResponse(
            total=total,
            limit=limit,
            offset=offset,
            summary=FuccsControlRegistrySummary(
                **summary
            ),
            items=[
                FuccsWorkspaceService.registry_item(
                    row
                )
                for row in rows
            ],
        )

    @staticmethod
    async def context(
        db: AsyncSession,
        control_id,
    ) -> FuccsControlRegistryItem:
        row = (
            await FuccsWorkspaceRepository
            .control_context(
                db,
                control_id,
            )
        )

        if row is None:
            raise HTTPException(
                404,
                "Contrôle FUCCS introuvable.",
            )

        return FuccsWorkspaceService.registry_item(
            row
        )

    @staticmethod
    async def eligible_verifications(
        db: AsyncSession,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ) -> FuccsEligibleVerificationsResponse:
        rows, total = (
            await FuccsWorkspaceRepository
            .eligible_verifications(
                db,
                search=search,
                limit=limit,
                offset=offset,
            )
        )

        items = []

        for row in rows:
            items.append(
                FuccsEligibleVerificationItem(
                    dossier_id=row.dossier_id,
                    verification_opinion=(
                        row.verification_opinion
                    ),
                    verification_risk=(
                        row.verification_risk
                    ),
                    verification_closed_on=(
                        row.verification_closed_on
                    ),
                    fiche_id=row.fiche_id,
                    fiche_revision=row.fiche_revision,
                    mission_id=row.mission_id,
                    mission_code=row.mission_code,
                    campaign_code=row.campaign_code,
                    campaign_name=row.campaign_name,
                    zone_name=row.zone_name,
                    entreprise_id=row.entreprise_id,
                    entreprise_name=(
                        row.entreprise_name
                        or row.entreprise_trade_name
                    ),
                    entreprise_identifiant=(
                        row.entreprise_identifiant
                    ),
                    controls_count=int(
                        row.controls_count or 0
                    ),
                    latest_control_id=(
                        row.latest_control_id
                    ),
                    latest_control_status=(
                        row.latest_control_status
                    ),
                )
            )

        return FuccsEligibleVerificationsResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=items,
        )
