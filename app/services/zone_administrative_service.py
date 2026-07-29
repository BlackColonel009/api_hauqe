"""Service métier des zones administratives."""

from __future__ import annotations

import re
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.zone_administrative import ZoneAdministrative
from app.repositories.zone_administrative_repository import (
    ZoneAdministrativeRepository,
)
from app.schemas.zone_administrative import (
    ZoneAdministrativeCreateRequest,
    ZoneAdministrativeListResponse,
    ZoneAdministrativeQuickCreateRequest,
    ZoneAdministrativeResponse,
    ZoneAdministrativeUpdateRequest,
)
from app.services.auth_service import AuthContext


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def normalize_code(value: str | None) -> str | None:
    value = clean_text(value)
    if value is None:
        return None
    value = value.upper().replace(" ", "_")
    value = re.sub(r"[^A-Z0-9_-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or None


class ZoneAdministrativeService:

    @staticmethod
    async def response(
        db: AsyncSession,
        zone: ZoneAdministrative,
        *,
        parent_nom: str | None = None,
        enfants_count: int = 0,
    ) -> ZoneAdministrativeResponse:
        path = await ZoneAdministrativeRepository.path_names(db, zone)
        return ZoneAdministrativeResponse(
            id=zone.id,
            parent_id=zone.parent_id,
            parent_nom=parent_nom,
            type_zone=zone.type_zone,
            code=zone.code,
            nom=zone.nom,
            latitude=zone.latitude,
            longitude=zone.longitude,
            statut=zone.statut,
            enfants_count=enfants_count,
            chemin=" › ".join(path),
            created_at=zone.created_at,
            updated_at=zone.updated_at,
        )

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        search: str | None,
        type_zone: str | None,
        parent_id: UUID | None,
        statut: str | None,
        limit: int,
        offset: int,
    ) -> ZoneAdministrativeListResponse:
        rows, total = await ZoneAdministrativeRepository.list(
            db,
            search=search,
            type_zone=type_zone,
            parent_id=parent_id,
            statut=statut,
            limit=limit,
            offset=offset,
        )

        items = []
        for row in rows:
            zone = row[0]
            items.append(
                await ZoneAdministrativeService.response(
                    db,
                    zone,
                    parent_nom=row.parent_nom,
                    enfants_count=int(row.enfants_count or 0),
                )
            )

        return ZoneAdministrativeListResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=items,
        )

    @staticmethod
    async def get(
        db: AsyncSession,
        zone_id: UUID,
    ) -> ZoneAdministrativeResponse:
        zone = await ZoneAdministrativeRepository.get(db, zone_id)
        if zone is None:
            raise HTTPException(404, "Zone administrative introuvable.")
        return await ZoneAdministrativeService.response(db, zone)

    @staticmethod
    async def validate_parent(
        db: AsyncSession,
        *,
        parent_id: UUID | None,
        zone_id: UUID | None = None,
    ) -> ZoneAdministrative | None:
        if parent_id is None:
            return None
        if zone_id is not None and parent_id == zone_id:
            raise HTTPException(409, "Une zone ne peut pas être son propre parent.")

        parent = await ZoneAdministrativeRepository.get(db, parent_id)
        if parent is None:
            raise HTTPException(422, "La zone parente n'existe pas.")

        if zone_id is not None and await ZoneAdministrativeRepository.is_descendant(
            db,
            candidate_parent_id=parent_id,
            zone_id=zone_id,
        ):
            raise HTTPException(
                409,
                "Cette zone parente créerait une boucle hiérarchique.",
            )
        return parent

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        payload: ZoneAdministrativeCreateRequest | ZoneAdministrativeQuickCreateRequest,
        actor: AuthContext,
        request: Request,
        source: str,
    ) -> ZoneAdministrativeResponse:
        parent = await ZoneAdministrativeService.validate_parent(
            db,
            parent_id=payload.parent_id,
        )

        nom = payload.nom.strip()
        type_zone = payload.type_zone.strip().upper()
        code = normalize_code(payload.code)

        duplicate = await ZoneAdministrativeRepository.duplicate(
            db,
            nom=nom,
            type_zone=type_zone,
            parent_id=payload.parent_id,
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Une zone identique existe déjà.",
                    "zone_id": str(duplicate.id),
                },
            )

        if code:
            owner = await ZoneAdministrativeRepository.code_owner(db, code)
            if owner is not None:
                raise HTTPException(409, "Ce code de zone est déjà utilisé.")

        zone = ZoneAdministrative(
            parent_id=payload.parent_id,
            type_zone=type_zone,
            code=code,
            nom=nom,
            latitude=payload.latitude,
            longitude=payload.longitude,
            statut=(getattr(payload, "statut", None) or "ACTIF").strip().upper(),
        )
        db.add(zone)
        await db.flush()

        await write_audit_event(
            db,
            action=(
                "ZONE_ADMIN_CREATE"
                if source == "ADMINISTRATION"
                else "ZONE_ADMIN_QUICK_CREATE_COLLECTE"
            ),
            categorie="REFERENTIEL",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="zone_administrative",
            ressource_id=zone.id,
            adresse_ip=client_ip(request),
            contexte={"source": source},
            valeurs_apres={
                "parent_id": str(zone.parent_id) if zone.parent_id else None,
                "parent_nom": parent.nom if parent else None,
                "type_zone": zone.type_zone,
                "code": zone.code,
                "nom": zone.nom,
                "statut": zone.statut,
            },
        )

        await db.commit()
        await db.refresh(zone)
        return await ZoneAdministrativeService.response(
            db,
            zone,
            parent_nom=parent.nom if parent else None,
        )

    @staticmethod
    async def update(
        db: AsyncSession,
        *,
        zone_id: UUID,
        payload: ZoneAdministrativeUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> ZoneAdministrativeResponse:
        zone = await ZoneAdministrativeRepository.get(db, zone_id)
        if zone is None:
            raise HTTPException(404, "Zone administrative introuvable.")

        changes = payload.model_dump(exclude_unset=True)
        parent_id = changes.get("parent_id", zone.parent_id)
        parent = await ZoneAdministrativeService.validate_parent(
            db,
            parent_id=parent_id,
            zone_id=zone.id,
        )

        nom = clean_text(changes.get("nom", zone.nom))
        type_zone = clean_text(changes.get("type_zone", zone.type_zone))
        if not nom or not type_zone:
            raise HTTPException(422, "Le nom et le type de zone sont obligatoires.")
        type_zone = type_zone.upper()

        duplicate = await ZoneAdministrativeRepository.duplicate(
            db,
            nom=nom,
            type_zone=type_zone,
            parent_id=parent_id,
            exclude_id=zone.id,
        )
        if duplicate is not None:
            raise HTTPException(409, "Une zone identique existe déjà.")

        code = normalize_code(changes.get("code", zone.code))
        if code:
            owner = await ZoneAdministrativeRepository.code_owner(
                db,
                code,
                exclude_id=zone.id,
            )
            if owner is not None:
                raise HTTPException(409, "Ce code de zone est déjà utilisé.")

        before = {
            "parent_id": str(zone.parent_id) if zone.parent_id else None,
            "type_zone": zone.type_zone,
            "code": zone.code,
            "nom": zone.nom,
            "latitude": str(zone.latitude) if zone.latitude is not None else None,
            "longitude": str(zone.longitude) if zone.longitude is not None else None,
            "statut": zone.statut,
        }

        zone.parent_id = parent_id
        zone.type_zone = type_zone
        zone.code = code
        zone.nom = nom
        if "latitude" in changes:
            zone.latitude = changes["latitude"]
        if "longitude" in changes:
            zone.longitude = changes["longitude"]
        if "statut" in changes:
            zone.statut = clean_text(changes["statut"]).upper() if clean_text(changes["statut"]) else None

        await write_audit_event(
            db,
            action="ZONE_ADMIN_UPDATE",
            categorie="REFERENTIEL",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="zone_administrative",
            ressource_id=zone.id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
            valeurs_apres={
                "parent_id": str(zone.parent_id) if zone.parent_id else None,
                "type_zone": zone.type_zone,
                "code": zone.code,
                "nom": zone.nom,
                "latitude": str(zone.latitude) if zone.latitude is not None else None,
                "longitude": str(zone.longitude) if zone.longitude is not None else None,
                "statut": zone.statut,
            },
        )
        await db.commit()
        await db.refresh(zone)
        return await ZoneAdministrativeService.response(
            db,
            zone,
            parent_nom=parent.nom if parent else None,
        )

    @staticmethod
    async def change_status(
        db: AsyncSession,
        *,
        zone_id: UUID,
        new_status: str,
        motif: str | None,
        actor: AuthContext,
        request: Request,
    ) -> ZoneAdministrativeResponse:
        zone = await ZoneAdministrativeRepository.get(db, zone_id)
        if zone is None:
            raise HTTPException(404, "Zone administrative introuvable.")

        normalized = new_status.strip().upper()
        if normalized not in {"ACTIF", "INACTIF"}:
            raise HTTPException(422, "Statut de zone invalide.")

        if normalized == "INACTIF":
            rows, count = await ZoneAdministrativeRepository.list(
                db,
                search=None,
                type_zone=None,
                parent_id=zone.id,
                statut="ACTIF",
                limit=1,
                offset=0,
            )
            if count:
                raise HTTPException(
                    409,
                    "Désactivez ou déplacez d'abord les zones enfants actives.",
                )

        old_status = zone.statut
        zone.statut = normalized

        await write_audit_event(
            db,
            action="ZONE_ADMIN_STATUS_CHANGE",
            categorie="REFERENTIEL",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="zone_administrative",
            ressource_id=zone.id,
            adresse_ip=client_ip(request),
            contexte={"motif": clean_text(motif)},
            valeurs_avant={"statut": old_status},
            valeurs_apres={"statut": normalized},
        )
        await db.commit()
        await db.refresh(zone)
        return await ZoneAdministrativeService.response(db, zone)
