from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.entreprise import Entreprise
from app.repositories.collecte_workspace_repository import (
    CollecteWorkspaceRepository,
)
from app.schemas.collecte_workspace import (
    CollecteRegistryItem,
    CollecteRegistryResponse,
    CollecteRegistrySummary,
    CollecteWorkspaceFiltersResponse,
    CollecteQuickEnterpriseCreateRequest,
    CollecteQuickEnterpriseResponse,
)
from app.services.auth_service import AuthContext


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


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

    @staticmethod
    async def quick_create_enterprise(
        db: AsyncSession,
        *,
        payload: CollecteQuickEnterpriseCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> CollecteQuickEnterpriseResponse:
        name = payload.raison_sociale.strip()
        zone = await CollecteWorkspaceRepository.get_zone(
            db,
            payload.zone_siege_id,
        )
        if zone is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Zone administrative active introuvable.",
            )

        existing = await CollecteWorkspaceRepository.find_exact_enterprise(
            db,
            name=name,
            zone_id=payload.zone_siege_id,
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": (
                        "Une entreprise portant exactement ce nom "
                        "existe déjà dans cette zone."
                    ),
                    "entreprise_id": str(existing.id),
                },
            )

        item = Entreprise(
            identifiant_national=f"TMP-COL-{uuid4().hex[:12].upper()}",
            raison_sociale=name,
            zone_siege_id=payload.zone_siege_id,
            adresse_siege=(
                payload.adresse_siege
                or zone.nom
                or "À compléter"
            ).strip(),
            telephone_principal=payload.telephone_principal,
            email_principal=payload.email_principal,
            statut="INCOMPLET_COLLECTE",
            source_donnee="COLLECTE_TERRAIN",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="COLLECTE_ENTERPRISE_QUICK_CREATE",
            categorie="COLLECTE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="entreprise",
            ressource_id=item.id,
            adresse_ip=_client_ip(request),
            valeurs_apres={
                "identifiant_national": item.identifiant_national,
                "raison_sociale": item.raison_sociale,
                "zone_siege_id": str(item.zone_siege_id),
                "statut": item.statut,
                "source_donnee": item.source_donnee,
            },
        )
        await db.commit()
        await db.refresh(item)

        return CollecteQuickEnterpriseResponse(
            id=item.id,
            identifiant_national=item.identifiant_national,
            raison_sociale=item.raison_sociale or name,
            zone_siege_id=item.zone_siege_id,
            adresse_siege=item.adresse_siege,
            telephone_principal=item.telephone_principal,
            email_principal=item.email_principal,
            statut=item.statut or "INCOMPLET_COLLECTE",
            source_donnee=item.source_donnee or "COLLECTE_TERRAIN",
        )
