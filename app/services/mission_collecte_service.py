"""
Service métier des missions de collecte et des affectations.

RÈGLES
------
- une mission appartient obligatoirement à une campagne dans le MPD ;
- la zone administrative doit exister ;
- dates prévues et réelles sont contrôlées séparément ;
- progression comprise entre 0 et 100 ;
- une affectation cible un utilisateur actif ;
- une seconde affectation active identique est refusée ;
- `attribue_par_id` vient toujours de l'utilisateur authentifié.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.affectation_mission import AffectationMission
from app.models.mission_collecte import MissionCollecte
from app.repositories.mission_collecte_repository import (
    MissionCollecteRepository,
)
from app.schemas.mission_collecte import (
    AffectationMissionCreateRequest,
    AffectationMissionResponse,
    AffectationMissionUpdateRequest,
    MissionCollecteCreateRequest,
    MissionCollecteListResponse,
    MissionCollecteResponse,
    MissionCollecteUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.campagne_service import CampagneService


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def validate_period(start, end, label: str) -> None:
    if start is not None and end is not None and end < start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"La fin {label} ne peut pas précéder le début.",
        )


def build_mission(item: MissionCollecte) -> MissionCollecteResponse:
    return MissionCollecteResponse(
        id=item.id,
        campagne_id=item.campagne_id,
        code=item.code,
        objet=item.objet,
        zone_id=item.zone_id,
        date_debut_prevue=item.date_debut_prevue,
        date_fin_prevue=item.date_fin_prevue,
        date_debut_reelle=item.date_debut_reelle,
        date_fin_reelle=item.date_fin_reelle,
        priorite=item.priorite,
        progression=item.progression,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def build_assignment(
    item: AffectationMission,
) -> AffectationMissionResponse:
    return AffectationMissionResponse(
        id=item.id,
        mission_id=item.mission_id,
        utilisateur_id=item.utilisateur_id,
        role_mission=item.role_mission,
        date_debut=item.date_debut,
        date_fin=item.date_fin,
        attribue_par_id=item.attribue_par_id,
        motif=item.motif,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


class MissionCollecteService:

    @staticmethod
    async def get(
        db: AsyncSession,
        mission_id: UUID,
    ) -> MissionCollecte:
        item = await MissionCollecteRepository.get_by_id(
            db,
            mission_id,
        )
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mission de collecte introuvable.",
            )
        return item

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        campagne_id: UUID | None,
        zone_id: UUID | None,
        statut: str | None,
        assigned_user_id: UUID | None,
        limit: int,
        offset: int,
    ) -> MissionCollecteListResponse:
        items, total = await MissionCollecteRepository.list(
            db,
            campagne_id=campagne_id,
            zone_id=zone_id,
            statut=statut,
            assigned_user_id=assigned_user_id,
            limit=limit,
            offset=offset,
        )
        return MissionCollecteListResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=[build_mission(x) for x in items],
        )

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        campagne_id: UUID,
        payload: MissionCollecteCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> MissionCollecteResponse:
        await CampagneService.get(db, campagne_id)

        if not await MissionCollecteRepository.zone_exists(
            db,
            payload.zone_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Zone administrative introuvable.",
            )

        validate_period(
            payload.date_debut_prevue,
            payload.date_fin_prevue,
            "prévue",
        )
        validate_period(
            payload.date_debut_reelle,
            payload.date_fin_reelle,
            "réelle",
        )

        item = MissionCollecte(
            campagne_id=campagne_id,
            code=clean_text(payload.code),
            objet=clean_text(payload.objet),
            zone_id=payload.zone_id,
            date_debut_prevue=payload.date_debut_prevue,
            date_fin_prevue=payload.date_fin_prevue,
            date_debut_reelle=payload.date_debut_reelle,
            date_fin_reelle=payload.date_fin_reelle,
            priorite=clean_text(payload.priorite),
            progression=payload.progression,
            statut=clean_text(payload.statut),
        )

        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="COLLECTE_MISSION_CREATE",
            categorie="COLLECTE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="mission_collecte",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "campagne_id": str(campagne_id),
                "code": item.code,
                "zone_id": str(item.zone_id),
                "progression": item.progression,
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return build_mission(item)

    @staticmethod
    async def update(
        db: AsyncSession,
        *,
        campagne_id: UUID,
        mission_id: UUID,
        payload: MissionCollecteUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> MissionCollecteResponse:
        await CampagneService.get(db, campagne_id)

        item = await MissionCollecteRepository.get_for_campaign(
            db,
            campagne_id=campagne_id,
            mission_id=mission_id,
        )
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mission introuvable dans cette campagne.",
            )

        changes = payload.model_dump(exclude_unset=True)

        if "zone_id" in changes and changes["zone_id"] is not None:
            if not await MissionCollecteRepository.zone_exists(
                db,
                changes["zone_id"],
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Zone administrative introuvable.",
                )

        validate_period(
            changes.get("date_debut_prevue", item.date_debut_prevue),
            changes.get("date_fin_prevue", item.date_fin_prevue),
            "prévue",
        )
        validate_period(
            changes.get("date_debut_reelle", item.date_debut_reelle),
            changes.get("date_fin_reelle", item.date_fin_reelle),
            "réelle",
        )

        before = {
            "code": item.code,
            "objet": item.objet,
            "zone_id": str(item.zone_id),
            "priorite": item.priorite,
            "progression": item.progression,
            "statut": item.statut,
        }

        for field, value in changes.items():
            if field in {"code", "objet", "priorite", "statut"}:
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db,
            action="COLLECTE_MISSION_UPDATE",
            categorie="COLLECTE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="mission_collecte",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
            valeurs_apres={
                "code": item.code,
                "objet": item.objet,
                "zone_id": str(item.zone_id),
                "priorite": item.priorite,
                "progression": item.progression,
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return build_mission(item)

    @staticmethod
    async def list_assignments(
        db: AsyncSession,
        mission_id: UUID,
    ) -> list[AffectationMissionResponse]:
        await MissionCollecteService.get(db, mission_id)
        items = await MissionCollecteRepository.list_assignments(
            db,
            mission_id,
        )
        return [build_assignment(x) for x in items]

    @staticmethod
    async def assign(
        db: AsyncSession,
        *,
        mission_id: UUID,
        payload: AffectationMissionCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> AffectationMissionResponse:
        await MissionCollecteService.get(db, mission_id)

        user = await MissionCollecteRepository.get_user(
            db,
            payload.utilisateur_id,
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur à affecter introuvable.",
            )
        if (user.statut or "").strip().upper() != "ACTIF":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Un utilisateur inactif ne peut pas être affecté.",
            )

        validate_period(payload.date_debut, payload.date_fin, "d'affectation")

        existing = (
            await MissionCollecteRepository
            .get_active_assignment_for_user(
                db,
                mission_id=mission_id,
                utilisateur_id=payload.utilisateur_id,
            )
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cet utilisateur possède déjà une affectation active "
                    "sur cette mission."
                ),
            )

        item = AffectationMission(
            mission_id=mission_id,
            utilisateur_id=payload.utilisateur_id,
            role_mission=clean_text(payload.role_mission),
            date_debut=payload.date_debut,
            date_fin=payload.date_fin,
            attribue_par_id=actor.user.id,
            motif=clean_text(payload.motif),
            statut=clean_text(payload.statut) or "ACTIF",
        )

        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="COLLECTE_MISSION_ASSIGN",
            categorie="AFFECTATION",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="affectation_mission",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "mission_id": str(mission_id),
                "utilisateur_id": str(item.utilisateur_id),
                "role_mission": item.role_mission,
                "attribue_par_id": str(item.attribue_par_id),
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return build_assignment(item)

    @staticmethod
    async def update_assignment(
        db: AsyncSession,
        *,
        mission_id: UUID,
        affectation_id: UUID,
        payload: AffectationMissionUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> AffectationMissionResponse:
        await MissionCollecteService.get(db, mission_id)

        item = await MissionCollecteRepository.get_assignment(
            db,
            mission_id=mission_id,
            affectation_id=affectation_id,
        )
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Affectation introuvable.",
            )

        changes = payload.model_dump(exclude_unset=True)

        validate_period(
            changes.get("date_debut", item.date_debut),
            changes.get("date_fin", item.date_fin),
            "d'affectation",
        )

        before = {
            "role_mission": item.role_mission,
            "date_debut": (
                item.date_debut.isoformat() if item.date_debut else None
            ),
            "date_fin": (
                item.date_fin.isoformat() if item.date_fin else None
            ),
            "motif": item.motif,
            "statut": item.statut,
        }

        for field, value in changes.items():
            if field in {"role_mission", "motif", "statut"}:
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db,
            action="COLLECTE_MISSION_ASSIGN_UPDATE",
            categorie="AFFECTATION",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="affectation_mission",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
            valeurs_apres={
                "role_mission": item.role_mission,
                "date_debut": (
                    item.date_debut.isoformat() if item.date_debut else None
                ),
                "date_fin": (
                    item.date_fin.isoformat() if item.date_fin else None
                ),
                "motif": item.motif,
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return build_assignment(item)
