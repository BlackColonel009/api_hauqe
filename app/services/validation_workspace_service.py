from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.validation_workspace_repository import (
    FAVORABLE,
    ValidationWorkspaceRepository,
)
from app.schemas.validation_workspace import (
    ValidationLevelSummary,
    ValidationWorkspaceFiltersResponse,
    ValidationWorkspaceItem,
    ValidationWorkspaceRegistryResponse,
    ValidationWorkspaceSummary,
)


class ValidationWorkspaceService:
    @staticmethod
    async def level_summary(
        db: AsyncSession,
        *,
        fiche_id,
        level: str,
    ) -> ValidationLevelSummary:
        item = await ValidationWorkspaceRepository.latest_validation(
            db,
            fiche_id=fiche_id,
            level=level,
        )

        if item is None:
            return ValidationLevelSummary(
                level=level,
            )

        total, pending, resubmitted = (
            await ValidationWorkspaceRepository
            .correction_counts(
                db,
                item.id,
            )
        )

        return ValidationLevelSummary(
            validation_id=item.id,
            level=level,
            validator_id=item.validateur_id,
            validator_name=(
                await ValidationWorkspaceRepository
                .validator_name(
                    db,
                    item.validateur_id,
                )
            ),
            decision=item.decision,
            validation_date=item.date_validation,
            reserves=item.reserves,
            justification=item.justification,
            status=item.statut,
            corrections_count=total,
            pending_corrections_count=pending,
            resubmitted_corrections_count=resubmitted,
        )

    @staticmethod
    def stage_for(
        level_1: ValidationLevelSummary,
        level_2: ValidationLevelSummary,
    ) -> str:
        pending = (
            level_1.pending_corrections_count
            + level_2.pending_corrections_count
        )

        if pending > 0:
            return "CORRECTION_PENDING"

        if level_2.decision in FAVORABLE:
            return "COMPLETE"

        if level_2.validation_id is not None:
            return "N2_REVIEW"

        if level_1.decision in FAVORABLE:
            return "READY_N2"

        if level_1.validation_id is not None:
            return "N1_REVIEW"

        return "READY_N1"

    @staticmethod
    async def item_from_row(
        db: AsyncSession,
        row,
    ) -> ValidationWorkspaceItem:
        fiche = row[0]

        level_1 = (
            await ValidationWorkspaceService.level_summary(
                db,
                fiche_id=fiche.id,
                level="NIVEAU_1",
            )
        )

        level_2 = (
            await ValidationWorkspaceService.level_summary(
                db,
                fiche_id=fiche.id,
                level="NIVEAU_2",
            )
        )

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

        pending_corrections = (
            level_1.pending_corrections_count
            + level_2.pending_corrections_count
        )

        return ValidationWorkspaceItem(
            fiche_id=fiche.id,
            fiche_revision=fiche.numero_revision,
            fiche_status=fiche.statut,
            completeness=(
                float(fiche.taux_completude)
                if fiche.taux_completude is not None
                else None
            ),
            submitted_at=fiche.soumise_at,
            entreprise_id=fiche.entreprise_id,
            entreprise_name=(
                row.entreprise_name
                or row.entreprise_trade_name
            ),
            entreprise_identifiant=(
                row.entreprise_identifiant
            ),
            mission_id=row.mission_id,
            mission_code=row.mission_code,
            campaign_code=row.campaign_code,
            campaign_name=row.campaign_name,
            zone_name=row.zone_name,
            verification_id=row.verification_id,
            verification_opinion=row.verification_opinion,
            verification_risk=row.verification_risk,
            control_id=row.control_id,
            control_status=row.control_status,
            control_score=(
                str(row.control_score)
                if row.control_score is not None
                else None
            ),
            control_maximum=(
                str(row.control_maximum)
                if row.control_maximum is not None
                else None
            ),
            control_rate=row.control_rate,
            control_ended_on=row.control_ended_on,
            controller_name=controller_name,
            level_1=level_1,
            level_2=level_2,
            stage=ValidationWorkspaceService.stage_for(
                level_1,
                level_2,
            ),
            integration_possible=bool(
                level_1.decision in FAVORABLE
                and level_2.decision in FAVORABLE
            ),
            pending_corrections_count=pending_corrections,
        )

    @staticmethod
    async def filters(
        db: AsyncSession,
    ) -> ValidationWorkspaceFiltersResponse:
        decisions = (
            await ValidationWorkspaceRepository.decisions(
                db
            )
        )

        return ValidationWorkspaceFiltersResponse(
            decisions=decisions,
        )

    @staticmethod
    async def registry(
        db: AsyncSession,
        *,
        search: str | None,
        stage: str | None,
        decision: str | None,
        limit: int,
        offset: int,
    ) -> ValidationWorkspaceRegistryResponse:
        # Fetch a broad page then apply workflow filters after resolving
        # the latest N1/N2 decisions. This preserves the existing
        # validation history as the source of truth.
        fetch_limit = min(max(limit * 5, limit), 200)

        rows, _ = (
            await ValidationWorkspaceRepository.queue_rows(
                db,
                search=search,
                limit=fetch_limit,
                offset=0,
            )
        )

        items = []

        for row in rows:
            item = (
                await ValidationWorkspaceService
                .item_from_row(
                    db,
                    row,
                )
            )

            if stage and item.stage != stage:
                continue

            if decision:
                if (
                    item.level_1.decision != decision
                    and item.level_2.decision != decision
                ):
                    continue

            items.append(item)

        total = len(items)

        page_items = items[
            offset : offset + limit
        ]

        summary = ValidationWorkspaceSummary(
            total=total,
            ready_n1=sum(
                1
                for item in items
                if item.stage == "READY_N1"
            ),
            ready_n2=sum(
                1
                for item in items
                if item.stage == "READY_N2"
            ),
            correction_pending=sum(
                1
                for item in items
                if item.stage == "CORRECTION_PENDING"
            ),
            complete=sum(
                1
                for item in items
                if item.stage == "COMPLETE"
            ),
        )

        return ValidationWorkspaceRegistryResponse(
            total=total,
            limit=limit,
            offset=offset,
            summary=summary,
            items=page_items,
        )

    @staticmethod
    async def context(
        db: AsyncSession,
        fiche_id,
    ) -> ValidationWorkspaceItem:
        row = (
            await ValidationWorkspaceRepository.context_row(
                db,
                fiche_id,
            )
        )

        if row is None:
            raise HTTPException(
                404,
                "Aucun contrôle FUCCS finalisé n'est disponible pour cette fiche.",
            )

        return await ValidationWorkspaceService.item_from_row(
            db,
            row,
        )
