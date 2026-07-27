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

import csv
import io
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
from app.repositories.contact_entreprise_repository import (
    ContactEntrepriseRepository,
)
from app.repositories.site_entreprise_repository import (
    SiteEntrepriseRepository,
)
from app.repositories.offre_entreprise_repository import (
    OffreEntrepriseRepository,
)
from app.repositories.organismes_certifications_repository import (
    CertificationRepository,
)
from app.schemas.entreprise import (
    EntrepriseControlSummaryItem,
    EntrepriseControlSummaryResponse,
    EntrepriseCreateRequest,
    EntrepriseFiltersResponse,
    EntrepriseListResponse,
    EntrepriseRegistryItem,
    EntrepriseRegistryResponse,
    EntrepriseRegistrySummary,
    EntrepriseResponse,
    EntrepriseUpdateRequest,
    EntrepriseZoneOption,
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


def normalize_code(value: str | None) -> str | None:
    cleaned = clean_text(value)
    return cleaned.upper() if cleaned else None


def validate_minimum_company_data(
    *,
    raison_sociale: str | None,
    adresse_siege: str | None,
    telephone_principal: str | None,
    email_principal: str | None,
) -> None:
    """Applique le noyau obligatoire de RM-13 au niveau serveur."""

    if not clean_text(raison_sociale):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La raison sociale est obligatoire.",
        )

    if not clean_text(adresse_siege):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="L'adresse ou la localité du siège est obligatoire.",
        )

    if not clean_text(telephone_principal) and not clean_text(email_principal):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Un téléphone principal ou un courriel principal "
                "est obligatoire."
            ),
        )


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
        secteur: str | None = None,
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
                secteur=secteur,
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

        validate_minimum_company_data(
            raison_sociale=payload.raison_sociale,
            adresse_siege=payload.adresse_siege,
            telephone_principal=payload.telephone_principal,
            email_principal=payload.email_principal,
        )

        normalized_rccm = normalize_code(payload.rccm)

        if normalized_rccm is not None:
            rccm_owner = await EntrepriseRepository.get_by_rccm(
                db,
                normalized_rccm,
            )
            if rccm_owner is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Une entreprise possède déjà ce numéro RCCM."
                    ),
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

            rccm=normalized_rccm,
            nif=normalize_code(payload.nif),
            ifu=normalize_code(payload.ifu),

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
            # RM-12 : absence de RCCM = dossier à régulariser.
            # Avec RCCM, aucun statut de conformité n'est inventé ici :
            # la classification dépend des certifications et du scoring.
            statut=(
                "EN_ATTENTE_REGULARISATION"
                if normalized_rccm is None
                else None
            ),
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

        prospective_reason = changes.get(
            "raison_sociale", entreprise.raison_sociale
        )
        prospective_address = changes.get(
            "adresse_siege", entreprise.adresse_siege
        )
        prospective_phone = changes.get(
            "telephone_principal", entreprise.telephone_principal
        )
        prospective_email = changes.get(
            "email_principal", entreprise.email_principal
        )

        validate_minimum_company_data(
            raison_sociale=prospective_reason,
            adresse_siege=prospective_address,
            telephone_principal=prospective_phone,
            email_principal=prospective_email,
        )

        if "rccm" in changes:
            normalized_rccm = normalize_code(changes.get("rccm"))
            changes["rccm"] = normalized_rccm

            if normalized_rccm is not None:
                rccm_owner = await EntrepriseRepository.get_by_rccm(
                    db,
                    normalized_rccm,
                    exclude_id=entreprise.id,
                )
                if rccm_owner is not None:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            "Une entreprise possède déjà ce numéro RCCM."
                        ),
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
                if field in {"rccm", "nif", "ifu"}:
                    value = normalize_code(value)
                else:
                    value = clean_text(value)

            setattr(
                entreprise,
                field,
                value,
            )

        if not entreprise.rccm:
            entreprise.statut = "EN_ATTENTE_REGULARISATION"
        elif (entreprise.statut or "").strip().upper() == "EN_ATTENTE_REGULARISATION":
            # On retire uniquement le statut administratif lié au RCCM.
            # Le statut de conformité sera calculé par le domaine concerné.
            entreprise.statut = None

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

        entreprise.statut = (
            "EN_ATTENTE_REGULARISATION"
            if not entreprise.rccm
            else None
        )

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
                "statut": entreprise.statut,
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

    # ========================================================
    # FILTRES DU REGISTRE
    # ========================================================

    @staticmethod
    async def registry_filters(
        db: AsyncSession,
    ) -> EntrepriseFiltersResponse:
        zones, sectors, statuses = (
            await EntrepriseRepository.registry_filters(db)
        )

        return EntrepriseFiltersResponse(
            zones=[
                EntrepriseZoneOption(
                    id=row.id,
                    parent_id=row.parent_id,
                    code=row.code,
                    nom=row.nom,
                    type_zone=row.type_zone,
                )
                for row in zones
                if row.nom
            ],
            sectors=sectors,
            statuses=statuses,
        )


    # ========================================================
    # REGISTRE ENRICHI
    # ========================================================

    @staticmethod
    async def registry(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
        zone_id: UUID | None,
        secteur: str | None,
        include_archived: bool,
        sort: str,
        limit: int,
        offset: int,
    ) -> EntrepriseRegistryResponse:
        rows, total = await EntrepriseRepository.registry_rows(
            db,
            search=search,
            statut=statut,
            zone_id=zone_id,
            secteur=secteur,
            include_archived=include_archived,
            sort=sort,
            limit=limit,
            offset=offset,
        )

        summary = await EntrepriseRepository.registry_summary(
            db,
            search=search,
            zone_id=zone_id,
            secteur=secteur,
            include_archived=include_archived,
        )

        return EntrepriseRegistryResponse(
            total=total,
            limit=limit,
            offset=offset,
            summary=EntrepriseRegistrySummary(**summary),
            items=[
                EntrepriseRegistryItem(
                    id=row.Entreprise.id,
                    identifiant_national=(
                        row.Entreprise.identifiant_national
                    ),
                    raison_sociale=row.Entreprise.raison_sociale,
                    nom_commercial=row.Entreprise.nom_commercial,
                    rccm=row.Entreprise.rccm,
                    nif=row.Entreprise.nif,
                    ifu=row.Entreprise.ifu,
                    zone_siege_id=row.Entreprise.zone_siege_id,
                    zone_nom=row.zone_nom,
                    zone_type=row.zone_type,
                    activite_principale=(
                        row.Entreprise.activite_principale
                    ),
                    statut=row.Entreprise.statut,
                    certifications_count=int(
                        row.certifications_count or 0
                    ),
                    next_expiration=row.next_expiration,
                    classification_score=row.classification_score,
                    classification_classe=row.classification_classe,
                    updated_at=row.Entreprise.updated_at,
                )
                for row in rows
            ],
        )


    # ========================================================
    # CONTRÔLES FUCCS LIÉS À L'ENTREPRISE
    # ========================================================

    @staticmethod
    async def controls_summary(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
    ) -> EntrepriseControlSummaryResponse:
        if await EntrepriseRepository.get_by_id(db, entreprise_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entreprise introuvable.",
            )

        controls = await EntrepriseRepository.enterprise_controls(
            db,
            entreprise_id,
        )

        return EntrepriseControlSummaryResponse(
            items=[
                EntrepriseControlSummaryItem(
                    id=item.id,
                    dossier_verification_id=(
                        item.dossier_verification_id
                    ),
                    date_debut=item.date_debut,
                    date_fin=item.date_fin,
                    score_brut=item.score_brut,
                    score_maximal=item.score_maximal,
                    taux=item.taux,
                    synthese=item.synthese,
                    statut=item.statut,
                )
                for item in controls
            ]
        )


    # ========================================================
    # EXPORT CSV DU REGISTRE
    # ========================================================

    @staticmethod
    async def export_registry_csv(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
        zone_id: UUID | None,
        secteur: str | None,
        include_archived: bool,
        sort: str,
        motif: str,
        actor: AuthContext,
        request: Request,
    ) -> str:
        rows, total = await EntrepriseRepository.registry_rows(
            db,
            search=search,
            statut=statut,
            zone_id=zone_id,
            secteur=secteur,
            include_archived=include_archived,
            sort=sort,
            limit=10000,
            offset=0,
        )

        buffer = io.StringIO()
        writer = csv.writer(
            buffer,
            delimiter=";",
            quoting=csv.QUOTE_MINIMAL,
        )

        writer.writerow(
            [
                "Identifiant national",
                "Raison sociale",
                "Nom commercial",
                "RCCM",
                "NIF",
                "IFU",
                "Zone du siège",
                "Activité principale",
                "Certifications",
                "Prochaine expiration",
                "Score classification",
                "Classe",
                "Statut",
            ]
        )

        for row in rows:
            item = row.Entreprise
            writer.writerow(
                [
                    item.identifiant_national,
                    item.raison_sociale or "",
                    item.nom_commercial or "",
                    item.rccm or "",
                    item.nif or "",
                    item.ifu or "",
                    row.zone_nom or "",
                    item.activite_principale or "",
                    int(row.certifications_count or 0),
                    (
                        row.next_expiration.isoformat()
                        if row.next_expiration
                        else ""
                    ),
                    (
                        str(row.classification_score)
                        if row.classification_score is not None
                        else ""
                    ),
                    row.classification_classe or "",
                    item.statut or "",
                ]
            )

        await write_audit_event(
            db,
            action="ENTREPRISES_EXPORT",
            categorie="EXPORT",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="entreprises",
            adresse_ip=client_ip(request),
            contexte={
                "motif": clean_text(motif),
                "nombre_lignes": total,
                "filtres": {
                    "search": clean_text(search),
                    "statut": clean_text(statut),
                    "zone_id": str(zone_id) if zone_id else None,
                    "secteur": clean_text(secteur),
                    "include_archived": include_archived,
                    "sort": sort,
                },
            },
        )
        await db.commit()

        return "\ufeff" + buffer.getvalue()

    # ========================================================
    # EXPORT CSV D'UN DOSSIER ENTREPRISE
    # ========================================================

    @staticmethod
    async def export_dossier_csv(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        motif: str,
        actor: AuthContext,
        request: Request,
    ) -> str:
        entreprise = await EntrepriseRepository.get_by_id(
            db,
            entreprise_id,
        )

        if entreprise is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entreprise introuvable.",
            )

        contacts = await ContactEntrepriseRepository.list_contacts(
            db,
            entreprise_id=entreprise_id,
            include_inactive=True,
        )
        sites = await SiteEntrepriseRepository.list_sites(
            db,
            entreprise_id=entreprise_id,
            include_inactive=True,
        )
        offres = await OffreEntrepriseRepository.list_offres(
            db,
            entreprise_id=entreprise_id,
            include_inactive=True,
        )
        certifications, _ = await CertificationRepository.list(
            db,
            search=None,
            entreprise_id=entreprise_id,
            organisme_id=None,
            norme_id=None,
            statut=None,
            limit=200,
            offset=0,
        )

        buffer = io.StringIO()
        writer = csv.writer(
            buffer,
            delimiter=";",
            quoting=csv.QUOTE_MINIMAL,
        )

        writer.writerow(["HAUQE Certif", "Dossier entreprise"])
        writer.writerow(["Identifiant national", entreprise.identifiant_national])
        writer.writerow(["Raison sociale", entreprise.raison_sociale or ""])
        writer.writerow(["Nom commercial", entreprise.nom_commercial or ""])
        writer.writerow(["RCCM", entreprise.rccm or ""])
        writer.writerow(["NIF", entreprise.nif or ""])
        writer.writerow(["IFU", entreprise.ifu or ""])
        writer.writerow(["Forme juridique", entreprise.forme_juridique or ""])
        writer.writerow(["Date création", entreprise.date_creation.isoformat() if entreprise.date_creation else ""])
        writer.writerow(["Nationalité", entreprise.nationalite or ""])
        writer.writerow(["Effectif", entreprise.effectif if entreprise.effectif is not None else ""])
        writer.writerow(["Email", entreprise.email_principal or ""])
        writer.writerow(["Téléphone", entreprise.telephone_principal or ""])
        writer.writerow(["Site web", entreprise.site_web or ""])
        writer.writerow(["Adresse siège", entreprise.adresse_siege or ""])
        writer.writerow(["Activité principale", entreprise.activite_principale or ""])
        writer.writerow(["Statut", entreprise.statut or ""])

        writer.writerow([])
        writer.writerow(["CONTACTS"])
        writer.writerow(["Nom", "Prénoms", "Fonction", "Téléphone", "Email", "Type", "Principal", "Statut"])
        for item in contacts:
            writer.writerow([
                item.nom or "", item.prenoms or "", item.fonction or "",
                item.telephone or "", item.email or "", item.type_contact or "",
                "OUI" if item.contact_principal else "NON", item.statut or "",
            ])

        writer.writerow([])
        writer.writerow(["SITES"])
        writer.writerow(["Nom", "Type", "Adresse", "Zone", "Latitude", "Longitude", "Effectif", "Statut"])
        for item in sites:
            writer.writerow([
                item.nom or "", item.type_site or "", item.adresse or "",
                str(item.zone_id), item.latitude if item.latitude is not None else "",
                item.longitude if item.longitude is not None else "",
                item.effectif if item.effectif is not None else "", item.statut or "",
            ])

        writer.writerow([])
        writer.writerow(["OFFRES"])
        writer.writerow(["Type", "Nom", "Catégorie", "Description", "Volume annuel", "Unité", "Capacité", "Marchés", "Destinations", "Statut"])
        for item in offres:
            writer.writerow([
                item.type_offre or "", item.nom or "", item.categorie or "",
                item.description or "", item.volume_annuel if item.volume_annuel is not None else "",
                item.unite or "", item.capacite_production if item.capacite_production is not None else "",
                ", ".join(item.marches_cibles or []), ", ".join(item.destinations or []), item.statut or "",
            ])

        writer.writerow([])
        writer.writerow(["CERTIFICATIONS"])
        writer.writerow(["Identifiant national", "Numéro", "Statut", "Obtention", "Effet", "Expiration", "Stratégique", "Authenticité"])
        for item in certifications:
            writer.writerow([
                item.identifiant_national,
                item.numero_certificat or "",
                item.statut or "",
                item.date_obtention.isoformat() if item.date_obtention else "",
                item.date_effet.isoformat() if item.date_effet else "",
                item.date_expiration.isoformat() if item.date_expiration else "",
                "OUI" if item.certification_strategique else "NON",
                "OUI" if item.authenticite_verifiee else "NON",
            ])

        await write_audit_event(
            db,
            action="ENTREPRISE_DOSSIER_EXPORT",
            categorie="EXPORT",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="entreprise",
            ressource_id=entreprise_id,
            adresse_ip=client_ip(request),
            contexte={
                "motif": clean_text(motif),
                "contacts": len(contacts),
                "sites": len(sites),
                "offres": len(offres),
                "certifications": len(certifications),
            },
        )
        await db.commit()

        return "\ufeff" + buffer.getvalue()

