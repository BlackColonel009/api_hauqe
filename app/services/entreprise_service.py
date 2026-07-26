"""
Service métier du module Entreprises.

RÔLE DU FICHIER
---------------
Appliquer les règles métier avant toute modification de PostgreSQL.

Responsabilités principales :
- vérifier l'unicité de l'identifiant national ;
- vérifier la zone administrative ;
- empêcher la modification d'une entreprise archivée ;
- effectuer l'archivage logique ;
- journaliser les actions ;
- contrôler les transactions.

IMPORTANT
---------
Une entreprise n'est jamais supprimée physiquement par ce service.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import (
    HTTPException,
    Request,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.entreprise import Entreprise
from app.repositories.entreprise_repository import (
    EntrepriseRepository,
)
from app.schemas.entreprise import (
    EntrepriseCreateRequest,
    EntrepriseListResponse,
    EntrepriseResponse,
    EntrepriseUpdateRequest,
)
from app.services.auth_service import AuthContext


# ============================================================
# IP CLIENT
# ============================================================

def client_ip(
    request: Request,
) -> str | None:

    if request.client is None:
        return None

    return request.client.host


# ============================================================
# NORMALISATION TEXTE
# ============================================================

def clean_text(
    value: str | None,
) -> str | None:
    """
    Supprime les espaces inutiles.

    Une chaîne vide devient NULL afin de ne pas stocker
    inutilement "" dans PostgreSQL.
    """

    if value is None:
        return None

    value = value.strip()

    return value or None


# ============================================================
# SERIALISATION
# ============================================================

def build_response(
    entreprise: Entreprise,
) -> EntrepriseResponse:
    """
    Construit la réponse API.

    chiffre_affaires, niveau_risque et les autres données
    internes non prévues dans le périmètre actuel restent
    volontairement absents.
    """

    return EntrepriseResponse(
        id=entreprise.id,

        identifiant_national=(
            entreprise.identifiant_national
        ),

        raison_sociale=entreprise.raison_sociale,
        nom_commercial=entreprise.nom_commercial,
        forme_juridique=entreprise.forme_juridique,

        rccm=entreprise.rccm,
        nif=entreprise.nif,
        ifu=entreprise.ifu,

        date_creation=entreprise.date_creation,
        nationalite=entreprise.nationalite,

        capital_social=entreprise.capital_social,
        effectif=entreprise.effectif,

        email_principal=entreprise.email_principal,
        telephone_principal=(
            entreprise.telephone_principal
        ),
        site_web=entreprise.site_web,

        adresse_siege=entreprise.adresse_siege,
        zone_siege_id=entreprise.zone_siege_id,

        activite_principale=(
            entreprise.activite_principale
        ),

        secteurs_secondaires=(
            entreprise.secteurs_secondaires
        ),

        statut=entreprise.statut,

        created_at=entreprise.created_at,
        updated_at=entreprise.updated_at,
    )


# ============================================================
# SERVICE ENTREPRISE
# ============================================================

class EntrepriseService:

    # ========================================================
    # LISTE
    # ========================================================

    @staticmethod
    async def list_entreprises(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
        zone_siege_id: UUID | None,
        include_archived: bool,
        limit: int,
        offset: int,
    ) -> EntrepriseListResponse:

        entreprises, total = (
            await EntrepriseRepository
            .list_entreprises(
                db,
                search=search,
                statut=statut,
                zone_siege_id=zone_siege_id,
                include_archived=include_archived,
                limit=limit,
                offset=offset,
            )
        )

        return EntrepriseListResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=[
                build_response(entreprise)
                for entreprise in entreprises
            ],
        )


    # ========================================================
    # DÉTAIL
    # ========================================================

    @staticmethod
    async def get_entreprise(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
    ) -> EntrepriseResponse:

        entreprise = (
            await EntrepriseRepository.get_by_id(
                db,
                entreprise_id,
            )
        )

        if entreprise is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Entreprise introuvable.",
            )

        return build_response(
            entreprise
        )


    # ========================================================
    # CRÉATION
    # ========================================================

    @staticmethod
    async def create_entreprise(
        db: AsyncSession,
        *,
        payload: EntrepriseCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> EntrepriseResponse:
        """
        Crée une nouvelle entreprise.

        Contrôles avant insertion :
        1. identifiant national renseigné ;
        2. absence de doublon exact ;
        3. zone administrative existante.
        """

        identifiant = (
            payload.identifiant_national
            .strip()
            .upper()
        )

        # ----------------------------------------------------
        # Unicité métier
        # ----------------------------------------------------

        existing = (
            await EntrepriseRepository
            .get_by_identifiant_national(
                db,
                identifiant,
            )
        )

        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Une entreprise possède déjà "
                    "cet identifiant national."
                ),
            )

        # ----------------------------------------------------
        # Intégrité géographique
        # ----------------------------------------------------

        if not await EntrepriseRepository.zone_exists(
            db,
            payload.zone_siege_id,
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "La zone administrative du siège "
                    "n'existe pas."
                ),
            )

        entreprise = Entreprise(
            identifiant_national=identifiant,

            raison_sociale=clean_text(
                payload.raison_sociale
            ),

            nom_commercial=clean_text(
                payload.nom_commercial
            ),

            forme_juridique=clean_text(
                payload.forme_juridique
            ),

            rccm=clean_text(payload.rccm),
            nif=clean_text(payload.nif),
            ifu=clean_text(payload.ifu),

            date_creation=payload.date_creation,

            nationalite=clean_text(
                payload.nationalite
            ),

            capital_social=payload.capital_social,
            effectif=payload.effectif,

            email_principal=clean_text(
                payload.email_principal
            ),

            telephone_principal=clean_text(
                payload.telephone_principal
            ),

            site_web=clean_text(
                payload.site_web
            ),

            adresse_siege=clean_text(
                payload.adresse_siege
            ),

            zone_siege_id=payload.zone_siege_id,

            activite_principale=clean_text(
                payload.activite_principale
            ),

            secteurs_secondaires=(
                payload.secteurs_secondaires
            ),

            # ------------------------------------------------
            # Convention opérationnelle de la fiche entreprise.
            #
            # Ce statut n'est pas le workflow des fiches de
            # collecte ou des certifications.
            # ------------------------------------------------
            statut="ACTIF",
        )

        db.add(entreprise)

        try:
            # ------------------------------------------------
            # Flush nécessaire pour obtenir l'UUID avant audit.
            # ------------------------------------------------

            await db.flush()

            await write_audit_event(
                db,
                action="ENTREPRISE_CREATE",
                categorie="DONNEES_METIER",
                resultat="SUCCES",
                utilisateur_id=actor.user.id,
                ressource_type="entreprise",
                ressource_id=entreprise.id,
                adresse_ip=client_ip(request),
                valeurs_apres={
                    "identifiant_national":
                        entreprise.identifiant_national,
                    "raison_sociale":
                        entreprise.raison_sociale,
                    "nom_commercial":
                        entreprise.nom_commercial,
                    "zone_siege_id":
                        str(entreprise.zone_siege_id),
                    "statut":
                        entreprise.statut,
                },
            )

            await db.commit()

        except IntegrityError:
            # ------------------------------------------------
            # Protection contre une concurrence entre deux
            # requêtes créant le même identifiant au même
            # instant.
            # ------------------------------------------------

            await db.rollback()

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Conflit d'intégrité lors de la "
                    "création de l'entreprise."
                ),
            )

        await db.refresh(
            entreprise
        )

        return build_response(
            entreprise
        )


    # ========================================================
    # MODIFICATION
    # ========================================================

    @staticmethod
    async def update_entreprise(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        payload: EntrepriseUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> EntrepriseResponse:

        entreprise = (
            await EntrepriseRepository.get_by_id(
                db,
                entreprise_id,
            )
        )

        if entreprise is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Entreprise introuvable.",
            )

        # ----------------------------------------------------
        # Une archive n'est pas modifiable par cette route.
        # ----------------------------------------------------

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

        changes = payload.model_dump(
            exclude_unset=True
        )

        # ----------------------------------------------------
        # Si la zone change, vérifier d'abord la FK.
        # ----------------------------------------------------

        new_zone_id = changes.get(
            "zone_siege_id"
        )

        if new_zone_id is not None:

            if not await EntrepriseRepository.zone_exists(
                db,
                new_zone_id,
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_422_UNPROCESSABLE_ENTITY
                    ),
                    detail=(
                        "La zone administrative du siège "
                        "n'existe pas."
                    ),
                )

        # ----------------------------------------------------
        # Snapshot AVANT modification pour le journal.
        # ----------------------------------------------------

        before = {
            "raison_sociale":
                entreprise.raison_sociale,
            "nom_commercial":
                entreprise.nom_commercial,
            "forme_juridique":
                entreprise.forme_juridique,
            "rccm":
                entreprise.rccm,
            "nif":
                entreprise.nif,
            "ifu":
                entreprise.ifu,
            "zone_siege_id":
                str(entreprise.zone_siege_id),
            "activite_principale":
                entreprise.activite_principale,
        }

        # ----------------------------------------------------
        # Champs texte nécessitant une normalisation.
        # ----------------------------------------------------

        text_fields = {
            "raison_sociale",
            "nom_commercial",
            "forme_juridique",
            "rccm",
            "nif",
            "ifu",
            "nationalite",
            "email_principal",
            "telephone_principal",
            "site_web",
            "adresse_siege",
            "activite_principale",
        }

        for field, value in changes.items():

            if field in text_fields:
                value = clean_text(value)

            setattr(
                entreprise,
                field,
                value,
            )

        await write_audit_event(
            db,
            action="ENTREPRISE_UPDATE",
            categorie="DONNEES_METIER",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="entreprise",
            ressource_id=entreprise.id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
            valeurs_apres={
                "raison_sociale":
                    entreprise.raison_sociale,
                "nom_commercial":
                    entreprise.nom_commercial,
                "forme_juridique":
                    entreprise.forme_juridique,
                "rccm":
                    entreprise.rccm,
                "nif":
                    entreprise.nif,
                "ifu":
                    entreprise.ifu,
                "zone_siege_id":
                    str(entreprise.zone_siege_id),
                "activite_principale":
                    entreprise.activite_principale,
            },
        )

        await db.commit()

        await db.refresh(
            entreprise
        )

        return build_response(
            entreprise
        )


    # ========================================================
    # ARCHIVAGE LOGIQUE
    # ========================================================

    @staticmethod
    async def archive_entreprise(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        motif: str | None,
        actor: AuthContext,
        request: Request,
    ) -> EntrepriseResponse:
        """
        Archive sans DELETE SQL.

        L'historique de l'entreprise reste donc entièrement
        disponible pour les certifications, contrôles,
        audits et décisions déjà liés à cette entreprise.
        """

        entreprise = (
            await EntrepriseRepository.get_by_id(
                db,
                entreprise_id,
            )
        )

        if entreprise is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Entreprise introuvable.",
            )

        # ----------------------------------------------------
        # Archivage idempotent :
        # une seconde demande ne crée pas une nouvelle action.
        # ----------------------------------------------------

        if (
            entreprise.statut or ""
        ).strip().upper() == "ARCHIVE":
            return build_response(
                entreprise
            )

        previous_status = (
            entreprise.statut
        )

        entreprise.statut = "ARCHIVE"

        await write_audit_event(
            db,
            action="ENTREPRISE_ARCHIVE",
            categorie="DONNEES_METIER",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="entreprise",
            ressource_id=entreprise.id,
            adresse_ip=client_ip(request),
            valeurs_avant={
                "statut":
                    previous_status,
            },
            valeurs_apres={
                "statut":
                    "ARCHIVE",
            },
            contexte={
                "motif":
                    clean_text(motif),
            },
        )

        await db.commit()

        await db.refresh(
            entreprise
        )

        return build_response(
            entreprise
        )
    
    # ========================================================
    # DÉSARCHIVAGE / RESTAURATION
    # ========================================================

    @staticmethod
    async def restore_entreprise(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        motif: str | None,
        actor: AuthContext,
        request: Request,
    ) -> EntrepriseResponse:
        """
        Restaure une entreprise précédemment archivée.

        La restauration :
        - ne recrée aucune ligne ;
        - conserve le même UUID ;
        - remet simplement le statut à ACTIF ;
        - journalise l'opération.
        """

        entreprise = (
            await EntrepriseRepository.get_by_id(
                db,
                entreprise_id,
            )
        )

        if entreprise is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entreprise introuvable.",
            )

        # ----------------------------------------------------
        # Seules les entreprises réellement archivées peuvent
        # être restaurées.
        # ----------------------------------------------------

        if (
            entreprise.statut or ""
        ).strip().upper() != "ARCHIVE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cette entreprise n'est pas archivée."
                ),
            )

        previous_status = entreprise.statut

        entreprise.statut = "ACTIF"

        # ----------------------------------------------------
        # Traçabilité obligatoire du désarchivage.
        # ----------------------------------------------------

        await write_audit_event(
            db,
            action="ENTREPRISE_RESTORE",
            categorie="DONNEES_METIER",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="entreprise",
            ressource_id=entreprise.id,
            adresse_ip=client_ip(request),

            valeurs_avant={
                "statut": previous_status,
            },

            valeurs_apres={
                "statut": "ACTIF",
            },

            contexte={
                "motif": clean_text(motif),
            },
        )

        await db.commit()

        await db.refresh(
            entreprise
        )

        return build_response(
            entreprise
        )