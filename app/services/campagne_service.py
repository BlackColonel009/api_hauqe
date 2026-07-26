"""
Service métier des campagnes de collecte.

Contrôles :
- code unique ;
- responsable existant et actif ;
- cohérence chronologique de la période ;
- mutations auditées.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.campagne import Campagne
from app.repositories.campagne_repository import CampagneRepository
from app.schemas.campagne import (
    CampagneCreateRequest,
    CampagneListResponse,
    CampagneResponse,
    CampagneUpdateRequest,
)
from app.services.auth_service import AuthContext


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def validate_dates(start, end) -> None:
    if start is not None and end is not None and end < start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La date de fin ne peut pas précéder la date de début.",
        )


def build_response(item: Campagne) -> CampagneResponse:
    return CampagneResponse(
        id=item.id,
        code=item.code,
        nom=item.nom,
        objet=item.objet,
        objectif=item.objectif,
        date_debut=item.date_debut,
        date_fin=item.date_fin,
        responsable_id=item.responsable_id,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


class CampagneService:

    @staticmethod
    async def get(db: AsyncSession, campagne_id: UUID) -> Campagne:
        item = await CampagneRepository.get_by_id(db, campagne_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campagne introuvable.",
            )
        return item

    @staticmethod
    async def ensure_active_user(
        db: AsyncSession,
        user_id: UUID,
    ) -> None:
        user = await CampagneRepository.get_user(db, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Responsable introuvable.",
            )

        if (user.statut or "").strip().upper() != "ACTIF":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Le responsable sélectionné n'est pas actif.",
            )

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
        limit: int,
        offset: int,
    ) -> CampagneListResponse:
        items, total = await CampagneRepository.list(
            db,
            search=search,
            statut=statut,
            limit=limit,
            offset=offset,
        )
        return CampagneListResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=[build_response(x) for x in items],
        )

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        payload: CampagneCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> CampagneResponse:
        code = payload.code.strip().upper()

        if await CampagneRepository.get_by_code(db, code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Une campagne possède déjà ce code.",
            )

        await CampagneService.ensure_active_user(
            db,
            payload.responsable_id,
        )
        validate_dates(payload.date_debut, payload.date_fin)

        item = Campagne(
            code=code,
            nom=clean_text(payload.nom),
            objet=clean_text(payload.objet),
            objectif=clean_text(payload.objectif),
            date_debut=payload.date_debut,
            date_fin=payload.date_fin,
            responsable_id=payload.responsable_id,
            statut=clean_text(payload.statut),
        )

        db.add(item)

        try:
            await db.flush()

            await write_audit_event(
                db,
                action="COLLECTE_CAMPAIGN_CREATE",
                categorie="COLLECTE",
                resultat="SUCCES",
                utilisateur_id=actor.user.id,
                ressource_type="campagne",
                ressource_id=item.id,
                adresse_ip=client_ip(request),
                valeurs_apres={
                    "code": item.code,
                    "nom": item.nom,
                    "responsable_id": str(item.responsable_id),
                    "date_debut": (
                        item.date_debut.isoformat()
                        if item.date_debut else None
                    ),
                    "date_fin": (
                        item.date_fin.isoformat()
                        if item.date_fin else None
                    ),
                    "statut": item.statut,
                },
            )

            await db.commit()

        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflit d'intégrité sur la campagne.",
            )

        await db.refresh(item)
        return build_response(item)

    @staticmethod
    async def update(
        db: AsyncSession,
        *,
        campagne_id: UUID,
        payload: CampagneUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> CampagneResponse:
        item = await CampagneService.get(db, campagne_id)
        changes = payload.model_dump(exclude_unset=True)

        if "responsable_id" in changes and changes["responsable_id"]:
            await CampagneService.ensure_active_user(
                db,
                changes["responsable_id"],
            )

        validate_dates(
            changes.get("date_debut", item.date_debut),
            changes.get("date_fin", item.date_fin),
        )

        before = {
            "nom": item.nom,
            "objet": item.objet,
            "objectif": item.objectif,
            "date_debut": (
                item.date_debut.isoformat()
                if item.date_debut else None
            ),
            "date_fin": (
                item.date_fin.isoformat()
                if item.date_fin else None
            ),
            "responsable_id": str(item.responsable_id),
            "statut": item.statut,
        }

        text_fields = {"nom", "objet", "objectif", "statut"}

        for field, value in changes.items():
            if field in text_fields:
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db,
            action="COLLECTE_CAMPAIGN_UPDATE",
            categorie="COLLECTE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="campagne",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
            valeurs_apres={
                "nom": item.nom,
                "objet": item.objet,
                "objectif": item.objectif,
                "date_debut": (
                    item.date_debut.isoformat()
                    if item.date_debut else None
                ),
                "date_fin": (
                    item.date_fin.isoformat()
                    if item.date_fin else None
                ),
                "responsable_id": str(item.responsable_id),
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return build_response(item)
