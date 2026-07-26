"""
Service métier des offres d'entreprise.

INTERACTION MÉTIER
------------------
entreprises
    -> offres_entreprise
        -> couvertures_certification (future étape Certifications)

Une offre décrit un produit ou un service réellement proposé par
l'entreprise. Une certification pourra ensuite couvrir une offre précise
sans signifier que toutes les offres de l'entreprise sont certifiées.

RÈGLES ACTUELLES
----------------
- l'entreprise doit exister ;
- une entreprise ARCHIVE ne reçoit plus de nouvelle offre ;
- type_offre est limité à PRODUIT ou SERVICE selon le modèle fonctionnel ;
- une offre INACTIF doit être restaurée avant modification ;
- aucune suppression physique ;
- toute mutation est auditée.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.offre_entreprise import OffreEntreprise
from app.repositories.offre_entreprise_repository import (
    OffreEntrepriseRepository,
)
from app.schemas.offre_entreprise import (
    OffreEntrepriseCreateRequest,
    OffreEntrepriseResponse,
    OffreEntrepriseUpdateRequest,
)
from app.services.auth_service import AuthContext


ALLOWED_OFFER_TYPES = {"PRODUIT", "SERVICE"}


def client_ip(request: Request) -> str | None:
    if request.client is None:
        return None
    return request.client.host


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def normalize_offer_type(value: str) -> str:
    normalized = value.strip().upper()

    if normalized not in ALLOWED_OFFER_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="type_offre doit être PRODUIT ou SERVICE.",
        )

    return normalized


def build_response(offre: OffreEntreprise) -> OffreEntrepriseResponse:
    return OffreEntrepriseResponse(
        id=offre.id,
        entreprise_id=offre.entreprise_id,
        type_offre=offre.type_offre,
        nom=offre.nom,
        description=offre.description,
        categorie=offre.categorie,
        volume_annuel=offre.volume_annuel,
        unite=offre.unite,
        capacite_production=offre.capacite_production,
        marches_cibles=offre.marches_cibles,
        destinations=offre.destinations,
        statut=offre.statut,
        created_at=offre.created_at,
        updated_at=offre.updated_at,
    )


class OffreEntrepriseService:

    @staticmethod
    async def require_entreprise(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
    ):
        entreprise = await OffreEntrepriseRepository.get_entreprise(
            db,
            entreprise_id,
        )

        if entreprise is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entreprise introuvable.",
            )

        return entreprise

    @staticmethod
    async def list_offres(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        include_inactive: bool,
    ) -> list[OffreEntrepriseResponse]:
        await OffreEntrepriseService.require_entreprise(
            db,
            entreprise_id=entreprise_id,
        )

        offres = await OffreEntrepriseRepository.list_offres(
            db,
            entreprise_id=entreprise_id,
            include_inactive=include_inactive,
        )

        return [build_response(offre) for offre in offres]

    @staticmethod
    async def get_offre(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        offre_id: UUID,
    ) -> OffreEntrepriseResponse:
        await OffreEntrepriseService.require_entreprise(
            db,
            entreprise_id=entreprise_id,
        )

        offre = await OffreEntrepriseRepository.get_offre(
            db,
            entreprise_id=entreprise_id,
            offre_id=offre_id,
        )

        if offre is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offre introuvable.",
            )

        return build_response(offre)

    @staticmethod
    async def create_offre(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        payload: OffreEntrepriseCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> OffreEntrepriseResponse:
        entreprise = await OffreEntrepriseService.require_entreprise(
            db,
            entreprise_id=entreprise_id,
        )

        if (entreprise.statut or "").strip().upper() == "ARCHIVE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Impossible d'ajouter une offre à une entreprise archivée."
                ),
            )

        offre = OffreEntreprise(
            entreprise_id=entreprise_id,
            type_offre=normalize_offer_type(payload.type_offre),
            nom=clean_text(payload.nom),
            description=clean_text(payload.description),
            categorie=clean_text(payload.categorie),
            volume_annuel=payload.volume_annuel,
            unite=clean_text(payload.unite),
            capacite_production=payload.capacite_production,
            marches_cibles=payload.marches_cibles,
            destinations=payload.destinations,
            statut="ACTIF",
        )

        db.add(offre)
        await db.flush()

        await write_audit_event(
            db,
            action="ENTREPRISE_OFFRE_CREATE",
            categorie="DONNEES_METIER",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="offre_entreprise",
            ressource_id=offre.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "entreprise_id": str(entreprise_id),
                "type_offre": offre.type_offre,
                "nom": offre.nom,
                "categorie": offre.categorie,
                "volume_annuel": (
                    str(offre.volume_annuel)
                    if offre.volume_annuel is not None
                    else None
                ),
                "capacite_production": (
                    str(offre.capacite_production)
                    if offre.capacite_production is not None
                    else None
                ),
                "statut": offre.statut,
            },
        )

        await db.commit()
        await db.refresh(offre)
        return build_response(offre)

    @staticmethod
    async def update_offre(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        offre_id: UUID,
        payload: OffreEntrepriseUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> OffreEntrepriseResponse:
        entreprise = await OffreEntrepriseService.require_entreprise(
            db,
            entreprise_id=entreprise_id,
        )

        if (entreprise.statut or "").strip().upper() == "ARCHIVE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Une entreprise archivée ne peut pas être modifiée.",
            )

        offre = await OffreEntrepriseRepository.get_offre(
            db,
            entreprise_id=entreprise_id,
            offre_id=offre_id,
        )

        if offre is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offre introuvable.",
            )

        if (offre.statut or "").strip().upper() == "INACTIF":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Une offre désactivée doit être restaurée avant modification."
                ),
            )

        before = {
            "type_offre": offre.type_offre,
            "nom": offre.nom,
            "description": offre.description,
            "categorie": offre.categorie,
            "volume_annuel": (
                str(offre.volume_annuel)
                if offre.volume_annuel is not None
                else None
            ),
            "unite": offre.unite,
            "capacite_production": (
                str(offre.capacite_production)
                if offre.capacite_production is not None
                else None
            ),
            "marches_cibles": offre.marches_cibles,
            "destinations": offre.destinations,
        }

        changes = payload.model_dump(exclude_unset=True)

        text_fields = {
            "nom",
            "description",
            "categorie",
            "unite",
        }

        for field, value in changes.items():
            if field == "type_offre":
                if value is None:
                    continue
                value = normalize_offer_type(value)
            elif field in text_fields:
                value = clean_text(value)

            setattr(offre, field, value)

        await write_audit_event(
            db,
            action="ENTREPRISE_OFFRE_UPDATE",
            categorie="DONNEES_METIER",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="offre_entreprise",
            ressource_id=offre.id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
            valeurs_apres={
                "type_offre": offre.type_offre,
                "nom": offre.nom,
                "description": offre.description,
                "categorie": offre.categorie,
                "volume_annuel": (
                    str(offre.volume_annuel)
                    if offre.volume_annuel is not None
                    else None
                ),
                "unite": offre.unite,
                "capacite_production": (
                    str(offre.capacite_production)
                    if offre.capacite_production is not None
                    else None
                ),
                "marches_cibles": offre.marches_cibles,
                "destinations": offre.destinations,
            },
        )

        await db.commit()
        await db.refresh(offre)
        return build_response(offre)

    @staticmethod
    async def deactivate_offre(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        offre_id: UUID,
        motif: str | None,
        actor: AuthContext,
        request: Request,
    ) -> OffreEntrepriseResponse:
        offre = await OffreEntrepriseRepository.get_offre(
            db,
            entreprise_id=entreprise_id,
            offre_id=offre_id,
        )

        if offre is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offre introuvable.",
            )

        if (offre.statut or "").strip().upper() == "INACTIF":
            return build_response(offre)

        previous_status = offre.statut
        offre.statut = "INACTIF"

        await write_audit_event(
            db,
            action="ENTREPRISE_OFFRE_DEACTIVATE",
            categorie="DONNEES_METIER",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="offre_entreprise",
            ressource_id=offre.id,
            adresse_ip=client_ip(request),
            valeurs_avant={"statut": previous_status},
            valeurs_apres={"statut": "INACTIF"},
            contexte={"motif": clean_text(motif)},
        )

        await db.commit()
        await db.refresh(offre)
        return build_response(offre)

    @staticmethod
    async def restore_offre(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        offre_id: UUID,
        motif: str | None,
        actor: AuthContext,
        request: Request,
    ) -> OffreEntrepriseResponse:
        entreprise = await OffreEntrepriseService.require_entreprise(
            db,
            entreprise_id=entreprise_id,
        )

        if (entreprise.statut or "").strip().upper() == "ARCHIVE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Impossible de restaurer une offre d'une entreprise archivée."
                ),
            )

        offre = await OffreEntrepriseRepository.get_offre(
            db,
            entreprise_id=entreprise_id,
            offre_id=offre_id,
        )

        if offre is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offre introuvable.",
            )

        if (offre.statut or "").strip().upper() != "INACTIF":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cette offre n'est pas désactivée.",
            )

        offre.statut = "ACTIF"

        await write_audit_event(
            db,
            action="ENTREPRISE_OFFRE_RESTORE",
            categorie="DONNEES_METIER",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="offre_entreprise",
            ressource_id=offre.id,
            adresse_ip=client_ip(request),
            valeurs_avant={"statut": "INACTIF"},
            valeurs_apres={"statut": "ACTIF"},
            contexte={"motif": clean_text(motif)},
        )

        await db.commit()
        await db.refresh(offre)
        return build_response(offre)
