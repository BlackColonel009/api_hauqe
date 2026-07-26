"""
Service métier des sites entreprise.

RÈGLES ACTUELLES
----------------
- l'entreprise doit exister ;
- une entreprise archivée ne peut plus recevoir de nouveau site ;
- zone_id doit exister ;
- le site doit appartenir à l'entreprise de l'URL ;
- un site INACTIF n'est pas modifiable ;
- aucune suppression physique ;
- toutes les modifications importantes sont auditées.

NOTE
----
La relation future entre un site et
`couvertures_certification` existe déjà dans le MPD,
mais aucune règle supplémentaire n'est imposée ici
tant que le module Certification n'est pas encore actif.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import (
    HTTPException,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.site_entreprise import SiteEntreprise
from app.repositories.site_entreprise_repository import (
    SiteEntrepriseRepository,
)
from app.schemas.site_entreprise import (
    SiteEntrepriseCreateRequest,
    SiteEntrepriseResponse,
    SiteEntrepriseUpdateRequest,
)
from app.services.auth_service import AuthContext


# ============================================================
# OUTILS
# ============================================================

def client_ip(
    request: Request,
) -> str | None:

    if request.client is None:
        return None

    return request.client.host


def clean_text(
    value: str | None,
) -> str | None:
    """
    Une chaîne vide devient NULL.
    """

    if value is None:
        return None

    value = value.strip()

    return value or None


def build_response(
    site: SiteEntreprise,
) -> SiteEntrepriseResponse:

    return SiteEntrepriseResponse(
        id=site.id,
        entreprise_id=site.entreprise_id,

        nom=site.nom,
        type_site=site.type_site,

        adresse=site.adresse,
        zone_id=site.zone_id,

        latitude=site.latitude,
        longitude=site.longitude,

        date_ouverture=site.date_ouverture,
        effectif=site.effectif,

        statut=site.statut,

        created_at=site.created_at,
        updated_at=site.updated_at,
    )


# ============================================================
# SERVICE
# ============================================================

class SiteEntrepriseService:

    # ========================================================
    # ENTREPRISE OBLIGATOIRE
    # ========================================================

    @staticmethod
    async def require_entreprise(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
    ):
        """
        Vérifie l'existence de l'entreprise.
        """

        entreprise = (
            await SiteEntrepriseRepository
            .get_entreprise(
                db,
                entreprise_id,
            )
        )

        if entreprise is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entreprise introuvable.",
            )

        return entreprise


    # ========================================================
    # LISTE
    # ========================================================

    @staticmethod
    async def list_sites(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        include_inactive: bool,
    ) -> list[SiteEntrepriseResponse]:

        await SiteEntrepriseService.require_entreprise(
            db,
            entreprise_id=entreprise_id,
        )

        sites = (
            await SiteEntrepriseRepository
            .list_sites(
                db,
                entreprise_id=entreprise_id,
                include_inactive=include_inactive,
            )
        )

        return [
            build_response(site)
            for site in sites
        ]


    # ========================================================
    # CRÉATION
    # ========================================================

    @staticmethod
    async def create_site(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        payload: SiteEntrepriseCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> SiteEntrepriseResponse:

        entreprise = (
            await SiteEntrepriseService
            .require_entreprise(
                db,
                entreprise_id=entreprise_id,
            )
        )

        # ----------------------------------------------------
        # Les archives restent consultables mais ne doivent
        # plus recevoir de nouvelles données opérationnelles.
        # ----------------------------------------------------

        if (
            entreprise.statut or ""
        ).strip().upper() == "ARCHIVE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Impossible d'ajouter un site "
                    "à une entreprise archivée."
                ),
            )

        # ----------------------------------------------------
        # Intégrité géographique
        # ----------------------------------------------------

        if not await SiteEntrepriseRepository.zone_exists(
            db,
            payload.zone_id,
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "La zone administrative du site "
                    "n'existe pas."
                ),
            )

        site = SiteEntreprise(
            entreprise_id=entreprise_id,

            nom=clean_text(payload.nom),

            type_site=clean_text(
                payload.type_site
            ),

            adresse=clean_text(
                payload.adresse
            ),

            zone_id=payload.zone_id,

            latitude=payload.latitude,
            longitude=payload.longitude,

            date_ouverture=payload.date_ouverture,
            effectif=payload.effectif,

            statut="ACTIF",
        )

        db.add(site)

        await db.flush()

        await write_audit_event(
            db,
            action="ENTREPRISE_SITE_CREATE",
            categorie="DONNEES_METIER",
            resultat="SUCCES",

            utilisateur_id=actor.user.id,

            ressource_type="site_entreprise",
            ressource_id=site.id,

            adresse_ip=client_ip(request),

            valeurs_apres={
                "entreprise_id":
                    str(entreprise_id),
                "nom":
                    site.nom,
                "type_site":
                    site.type_site,
                "zone_id":
                    str(site.zone_id),
                "statut":
                    site.statut,
            },
        )

        await db.commit()
        await db.refresh(site)

        return build_response(site)


    # ========================================================
    # MODIFICATION
    # ========================================================

    @staticmethod
    async def update_site(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        site_id: UUID,
        payload: SiteEntrepriseUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> SiteEntrepriseResponse:

        entreprise = (
            await SiteEntrepriseService
            .require_entreprise(
                db,
                entreprise_id=entreprise_id,
            )
        )

        if (
            entreprise.statut or ""
        ).strip().upper() == "ARCHIVE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Une entreprise archivée "
                    "ne peut pas être modifiée."
                ),
            )

        site = (
            await SiteEntrepriseRepository
            .get_site(
                db,
                entreprise_id=entreprise_id,
                site_id=site_id,
            )
        )

        if site is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site introuvable.",
            )

        if (
            site.statut or ""
        ).strip().upper() == "INACTIF":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Un site désactivé doit être restauré "
                    "avant modification."
                ),
            )

        changes = payload.model_dump(
            exclude_unset=True
        )

        # ----------------------------------------------------
        # Nouvelle zone éventuelle
        # ----------------------------------------------------

        new_zone_id = changes.get(
            "zone_id"
        )

        if (
            new_zone_id is not None
            and not await SiteEntrepriseRepository.zone_exists(
                db,
                new_zone_id,
            )
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "La zone administrative du site "
                    "n'existe pas."
                ),
            )

        before = {
            "nom": site.nom,
            "type_site": site.type_site,
            "adresse": site.adresse,
            "zone_id": str(site.zone_id),
            "latitude": (
                str(site.latitude)
                if site.latitude is not None
                else None
            ),
            "longitude": (
                str(site.longitude)
                if site.longitude is not None
                else None
            ),
            "effectif": site.effectif,
        }

        text_fields = {
            "nom",
            "type_site",
            "adresse",
        }

        for field, value in changes.items():

            if field in text_fields:
                value = clean_text(value)

            setattr(
                site,
                field,
                value,
            )

        await write_audit_event(
            db,
            action="ENTREPRISE_SITE_UPDATE",
            categorie="DONNEES_METIER",
            resultat="SUCCES",

            utilisateur_id=actor.user.id,

            ressource_type="site_entreprise",
            ressource_id=site.id,

            adresse_ip=client_ip(request),

            valeurs_avant=before,

            valeurs_apres={
                "nom": site.nom,
                "type_site": site.type_site,
                "adresse": site.adresse,
                "zone_id": str(site.zone_id),
                "latitude": (
                    str(site.latitude)
                    if site.latitude is not None
                    else None
                ),
                "longitude": (
                    str(site.longitude)
                    if site.longitude is not None
                    else None
                ),
                "effectif": site.effectif,
            },
        )

        await db.commit()
        await db.refresh(site)

        return build_response(site)


    # ========================================================
    # DÉSACTIVATION
    # ========================================================

    @staticmethod
    async def deactivate_site(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        site_id: UUID,
        motif: str | None,
        actor: AuthContext,
        request: Request,
    ) -> SiteEntrepriseResponse:
        """
        Aucun DELETE SQL.
        """

        site = (
            await SiteEntrepriseRepository
            .get_site(
                db,
                entreprise_id=entreprise_id,
                site_id=site_id,
            )
        )

        if site is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site introuvable.",
            )

        if (
            site.statut or ""
        ).strip().upper() == "INACTIF":
            return build_response(site)

        previous_status = site.statut

        site.statut = "INACTIF"

        await write_audit_event(
            db,
            action="ENTREPRISE_SITE_DEACTIVATE",
            categorie="DONNEES_METIER",
            resultat="SUCCES",

            utilisateur_id=actor.user.id,

            ressource_type="site_entreprise",
            ressource_id=site.id,

            adresse_ip=client_ip(request),

            valeurs_avant={
                "statut": previous_status,
            },

            valeurs_apres={
                "statut": "INACTIF",
            },

            contexte={
                "motif": clean_text(motif),
            },
        )

        await db.commit()
        await db.refresh(site)

        return build_response(site)


    # ========================================================
    # RESTAURATION
    # ========================================================

    @staticmethod
    async def restore_site(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        site_id: UUID,
        motif: str | None,
        actor: AuthContext,
        request: Request,
    ) -> SiteEntrepriseResponse:

        entreprise = (
            await SiteEntrepriseService
            .require_entreprise(
                db,
                entreprise_id=entreprise_id,
            )
        )

        if (
            entreprise.statut or ""
        ).strip().upper() == "ARCHIVE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Impossible de restaurer un site "
                    "d'une entreprise archivée."
                ),
            )

        site = (
            await SiteEntrepriseRepository
            .get_site(
                db,
                entreprise_id=entreprise_id,
                site_id=site_id,
            )
        )

        if site is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site introuvable.",
            )

        if (
            site.statut or ""
        ).strip().upper() != "INACTIF":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ce site n'est pas désactivé.",
            )

        site.statut = "ACTIF"

        await write_audit_event(
            db,
            action="ENTREPRISE_SITE_RESTORE",
            categorie="DONNEES_METIER",
            resultat="SUCCES",

            utilisateur_id=actor.user.id,

            ressource_type="site_entreprise",
            ressource_id=site.id,

            adresse_ip=client_ip(request),

            valeurs_avant={
                "statut": "INACTIF",
            },

            valeurs_apres={
                "statut": "ACTIF",
            },

            contexte={
                "motif": clean_text(motif),
            },
        )

        await db.commit()
        await db.refresh(site)

        return build_response(site)