"""
Services métier du domaine Organismes / Certifications.

Ce fichier centralise la logique métier de la famille afin que le module
principal et ses sous-modules puissent être intégrés et testés ensemble.

Principes :
- aucune règle de sécurité n'est laissée au frontend ;
- les relations parent/enfant sont vérifiées côté serveur ;
- les changements sensibles sont audités ;
- l'historique métier des certifications est distinct du journal technique ;
- le MPD existant est respecté sans ajout de colonne ni migration.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.accreditation import Accreditation
from app.models.audit_certification import AuditCertification
from app.models.certification import Certification
from app.models.couverture_certification import CouvertureCertification
from app.models.evenement_certification import EvenementCertification
from app.models.organisme import Organisme
from app.models.renouvellement_certification import RenouvellementCertification
from app.repositories.organismes_certifications_repository import (
    AccreditationRepository,
    AuditCertificationRepository,
    CertificationRepository,
    CouvertureRepository,
    EvenementCertificationRepository,
    NormeRepository,
    OrganismeRepository,
    RenouvellementRepository,
)
from app.schemas.organismes_certifications import (
    AccreditationCreateRequest,
    AccreditationDecisionRequest,
    AccreditationResponse,
    AccreditationUpdateRequest,
    AuditCertificationCreateRequest,
    AuditCertificationResponse,
    AuditCertificationUpdateRequest,
    CertificationCreateRequest,
    CertificationListResponse,
    CertificationResponse,
    CertificationStatusRequest,
    CertificationUpdateRequest,
    CertificationVerificationRequest,
    CouvertureCreateRequest,
    CouvertureResponse,
    CouvertureUpdateRequest,
    EvenementCertificationResponse,
    NormeResponse,
    OrganismeCreateRequest,
    OrganismeFiltersResponse,
    OrganismeRegistryItem,
    OrganismeRegistryResponse,
    OrganismeRegistrySummary,
    OrganismeResponse,
    OrganismeUpdateRequest,
    OrganismeVerificationRequest,
    RenouvellementCreateRequest,
    RenouvellementDecisionRequest,
    RenouvellementResponse,
    RenouvellementUpdateRequest,
)
from app.services.auth_service import AuthContext


# ============================================================
# OUTILS COMMUNS
# ============================================================

def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def validate_certification_dates(obtention, effet, expiration) -> None:
    """Contrôles chronologiques bloquants prévus par les règles métier."""
    if obtention and effet and effet < obtention:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La date d'effet ne peut pas précéder la date d'obtention.",
        )

    reference = effet or obtention
    if reference and expiration and expiration < reference:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "La date d'expiration ne peut pas précéder la date "
                "d'obtention/d'effet."
            ),
        )


def validate_period(start, end, label: str) -> None:
    if start and end and end < start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"La date de fin de {label} ne peut pas précéder sa date de début.",
        )


# ============================================================
# SERIALISATION
# ============================================================

def norme_response(item) -> NormeResponse:
    return NormeResponse(
        id=item.id,
        code=item.code,
        nom=item.nom,
        version=item.version,
        autorite_emettrice=item.autorite_emettrice,
        domaine=item.domaine,
        portee=item.portee,
        date_debut_application=item.date_debut_application,
        date_fin_application=item.date_fin_application,
        date_expiration=item.date_expiration,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def organisme_response(item: Organisme) -> OrganismeResponse:
    return OrganismeResponse(
        id=item.id,
        identifiant_national=item.identifiant_national,
        nom_officiel=item.nom_officiel,
        sigle=item.sigle,
        type_organisme=item.type_organisme,
        pays=item.pays,
        numero_enregistrement=item.numero_enregistrement,
        email=item.email,
        telephone=item.telephone,
        adresse=item.adresse,
        zone_id=item.zone_id,
        site_web=item.site_web,
        statut=item.statut,
        date_derniere_verification=item.date_derniere_verification,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def accreditation_response(item: Accreditation) -> AccreditationResponse:
    return AccreditationResponse(
        id=item.id,
        organisme_id=item.organisme_id,
        numero=item.numero,
        accrediteur=item.accrediteur,
        domaine_technique=item.domaine_technique,
        perimetre=item.perimetre,
        date_delivrance=item.date_delivrance,
        date_expiration=item.date_expiration,
        statut=item.statut,
        reference_officielle=item.reference_officielle,
        decision_hauqe=item.decision_hauqe,
        date_decision=item.date_decision,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def certification_response(item: Certification) -> CertificationResponse:
    return CertificationResponse(
        id=item.id,
        identifiant_national=item.identifiant_national,
        entreprise_id=item.entreprise_id,
        organisme_id=item.organisme_id,
        accreditation_id=item.accreditation_id,
        norme_id=item.norme_id,
        numero_certificat=item.numero_certificat,
        portee=item.portee,
        date_obtention=item.date_obtention,
        date_effet=item.date_effet,
        date_expiration=item.date_expiration,
        statut=item.statut,
        motif_statut=item.motif_statut,
        classification=item.classification,
        authenticite_verifiee=item.authenticite_verifiee,
        certification_strategique=item.certification_strategique,
        source_donnee=item.source_donnee,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def couverture_response(item: CouvertureCertification) -> CouvertureResponse:
    return CouvertureResponse(
        id=item.id,
        certification_id=item.certification_id,
        type_couverture=item.type_couverture,
        offre_entreprise_id=item.offre_entreprise_id,
        site_entreprise_id=item.site_entreprise_id,
        libelle_couverture=item.libelle_couverture,
        details=item.details,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def audit_response(item: AuditCertification) -> AuditCertificationResponse:
    return AuditCertificationResponse(
        id=item.id,
        certification_id=item.certification_id,
        type_audit=item.type_audit,
        date_prevue=item.date_prevue,
        date_realisee=item.date_realisee,
        auditeur=item.auditeur,
        resultat=item.resultat,
        prochain_audit_at=item.prochain_audit_at,
        observations=item.observations,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def event_response(item: EvenementCertification) -> EvenementCertificationResponse:
    return EvenementCertificationResponse(
        id=item.id,
        certification_id=item.certification_id,
        type_evenement=item.type_evenement,
        ancien_statut=item.ancien_statut,
        nouveau_statut=item.nouveau_statut,
        date_evenement=item.date_evenement,
        motif=item.motif,
        source=item.source,
        acteur_id=item.acteur_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def renewal_response(item: RenouvellementCertification) -> RenouvellementResponse:
    return RenouvellementResponse(
        id=item.id,
        certification_id=item.certification_id,
        date_ouverture=item.date_ouverture,
        date_limite=item.date_limite,
        date_decision=item.date_decision,
        decision=item.decision,
        resultat=item.resultat,
        justification=item.justification,
        preuves=item.preuves,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


# ============================================================
# NORMES
# ============================================================

class NormeService:
    @staticmethod
    async def list(db: AsyncSession) -> list[NormeResponse]:
        return [norme_response(x) for x in await NormeRepository.list(db)]

    @staticmethod
    async def get(db: AsyncSession, norme_id: UUID) -> NormeResponse:
        item = await NormeRepository.get(db, norme_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Norme introuvable.")
        return norme_response(item)


# ============================================================
# ORGANISMES
# ============================================================

class OrganismeService:
    @staticmethod
    async def require(db: AsyncSession, organisme_id: UUID) -> Organisme:
        item = await OrganismeRepository.get(db, organisme_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Organisme introuvable.")
        return item

    @staticmethod
    async def list(
        db: AsyncSession,
        *, search: str | None, statut: str | None, limit: int, offset: int,
    ) -> dict:
        items, total = await OrganismeRepository.list(
            db, search=search, statut=statut, limit=limit, offset=offset
        )
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [organisme_response(x) for x in items],
        }


    @staticmethod
    async def filters(
        db: AsyncSession,
    ) -> OrganismeFiltersResponse:
        payload = await OrganismeRepository.filters(db)
        return OrganismeFiltersResponse(**payload)

    @staticmethod
    async def registry(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
        pays: str | None,
        type_organisme: str | None,
        accrediteur: str | None,
        domaine: str | None,
        sort: str,
        limit: int,
        offset: int,
    ) -> OrganismeRegistryResponse:
        rows, total, summary = await OrganismeRepository.registry(
            db,
            search=search,
            statut=statut,
            pays=pays,
            type_organisme=type_organisme,
            accrediteur=accrediteur,
            domaine=domaine,
            sort=sort,
            limit=limit,
            offset=offset,
        )

        items = []

        for row in rows:
            organisme = row[0]

            items.append(
                OrganismeRegistryItem(
                    id=organisme.id,
                    identifiant_national=organisme.identifiant_national,
                    nom_officiel=organisme.nom_officiel,
                    sigle=organisme.sigle,
                    type_organisme=organisme.type_organisme,
                    pays=organisme.pays,
                    statut=organisme.statut,
                    date_derniere_verification=(
                        organisme.date_derniere_verification
                    ),
                    accreditation_count=int(
                        row.accreditation_count or 0
                    ),
                    certification_count=int(
                        row.certification_count or 0
                    ),
                    accreditors=row.accreditors,
                    domains=row.domains,
                    next_accreditation_expiration=(
                        row.next_accreditation_expiration
                    ),
                )
            )

        return OrganismeRegistryResponse(
            total=total,
            limit=limit,
            offset=offset,
            summary=OrganismeRegistrySummary(**summary),
            items=items,
        )

    @staticmethod
    async def export_registry(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
        pays: str | None,
        type_organisme: str | None,
        accrediteur: str | None,
        domaine: str | None,
        sort: str,
        motif: str,
        actor: AuthContext,
        request: Request,
    ) -> OrganismeRegistryResponse:
        data = await OrganismeService.registry(
            db,
            search=search,
            statut=statut,
            pays=pays,
            type_organisme=type_organisme,
            accrediteur=accrediteur,
            domaine=domaine,
            sort=sort,
            limit=200,
            offset=0,
        )

        await write_audit_event(
            db,
            action="ORGANISMES_EXPORT",
            categorie="EXPORT",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="organisme",
            adresse_ip=client_ip(request),
            contexte={
                "motif": clean_text(motif),
                "filtres": {
                    "search": search,
                    "statut": statut,
                    "pays": pays,
                    "type_organisme": type_organisme,
                    "accrediteur": accrediteur,
                    "domaine": domaine,
                    "sort": sort,
                },
                "nombre": data.total,
            },
        )

        await db.commit()

        return data

    @staticmethod
    async def detail(db: AsyncSession, organisme_id: UUID) -> OrganismeResponse:
        return organisme_response(await OrganismeService.require(db, organisme_id))

    @staticmethod
    async def create(
        db: AsyncSession, *, payload: OrganismeCreateRequest,
        actor: AuthContext, request: Request,
    ) -> OrganismeResponse:
        if payload.zone_id and not await OrganismeRepository.zone_exists(db, payload.zone_id):
            raise HTTPException(status_code=422, detail="Zone administrative introuvable.")

        item = Organisme(
            identifiant_national=clean_text(payload.identifiant_national),
            nom_officiel=payload.nom_officiel.strip(),
            sigle=clean_text(payload.sigle),
            type_organisme=clean_text(payload.type_organisme),
            pays=clean_text(payload.pays),
            numero_enregistrement=clean_text(payload.numero_enregistrement),
            email=clean_text(payload.email),
            telephone=clean_text(payload.telephone),
            adresse=clean_text(payload.adresse),
            zone_id=payload.zone_id,
            site_web=clean_text(payload.site_web),
            statut=clean_text(payload.statut) or "A_VERIFIER",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db, action="ORGANISME_CREATE", categorie="DONNEES_METIER",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="organisme", ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "nom_officiel": item.nom_officiel,
                "sigle": item.sigle,
                "pays": item.pays,
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return organisme_response(item)

    @staticmethod
    async def update(
        db: AsyncSession, *, organisme_id: UUID,
        payload: OrganismeUpdateRequest, actor: AuthContext, request: Request,
    ) -> OrganismeResponse:
        item = await OrganismeService.require(db, organisme_id)
        changes = payload.model_dump(exclude_unset=True)

        if changes.get("zone_id") and not await OrganismeRepository.zone_exists(db, changes["zone_id"]):
            raise HTTPException(status_code=422, detail="Zone administrative introuvable.")

        before = {
            "identifiant_national": item.identifiant_national,
            "nom_officiel": item.nom_officiel,
            "sigle": item.sigle,
            "type_organisme": item.type_organisme,
            "pays": item.pays,
            "numero_enregistrement": item.numero_enregistrement,
            "email": item.email,
            "telephone": item.telephone,
            "adresse": item.adresse,
            "zone_id": str(item.zone_id) if item.zone_id else None,
            "site_web": item.site_web,
        }

        text_fields = {
            "identifiant_national", "nom_officiel", "sigle", "type_organisme",
            "pays", "numero_enregistrement", "email", "telephone", "adresse", "site_web"
        }
        for field, value in changes.items():
            if field in text_fields:
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db, action="ORGANISME_UPDATE", categorie="DONNEES_METIER",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="organisme", ressource_id=item.id,
            adresse_ip=client_ip(request), valeurs_avant=before,
            valeurs_apres={
                "identifiant_national": item.identifiant_national,
                "nom_officiel": item.nom_officiel,
                "sigle": item.sigle,
                "type_organisme": item.type_organisme,
                "pays": item.pays,
                "numero_enregistrement": item.numero_enregistrement,
                "email": item.email,
                "telephone": item.telephone,
                "adresse": item.adresse,
                "zone_id": str(item.zone_id) if item.zone_id else None,
                "site_web": item.site_web,
            },
        )
        await db.commit()
        await db.refresh(item)
        return organisme_response(item)

    @staticmethod
    async def verify(
        db: AsyncSession, *, organisme_id: UUID,
        payload: OrganismeVerificationRequest,
        actor: AuthContext, request: Request,
    ) -> OrganismeResponse:
        item = await OrganismeService.require(db, organisme_id)
        before = {
            "statut": item.statut,
            "date_derniere_verification": (
                item.date_derniere_verification.isoformat()
                if item.date_derniere_verification else None
            ),
        }
        if payload.statut is not None:
            item.statut = payload.statut.strip()
        item.date_derniere_verification = date.today()

        await write_audit_event(
            db, action="ORGANISME_VERIFY", categorie="VERIFICATION",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="organisme", ressource_id=item.id,
            adresse_ip=client_ip(request), valeurs_avant=before,
            valeurs_apres={
                "statut": item.statut,
                "date_derniere_verification": item.date_derniere_verification.isoformat(),
            },
            contexte={"motif": clean_text(payload.motif)},
        )
        await db.commit()
        await db.refresh(item)
        return organisme_response(item)


# ============================================================
# ACCRÉDITATIONS
# ============================================================

class AccreditationService:
    @staticmethod
    async def require(
        db: AsyncSession, *, organisme_id: UUID, accreditation_id: UUID,
    ) -> Accreditation:
        await OrganismeService.require(db, organisme_id)
        item = await AccreditationRepository.get_for_organisme(
            db, organisme_id=organisme_id, accreditation_id=accreditation_id
        )
        if item is None:
            raise HTTPException(status_code=404, detail="Accréditation introuvable pour cet organisme.")
        return item

    @staticmethod
    async def list(db: AsyncSession, organisme_id: UUID) -> list[AccreditationResponse]:
        await OrganismeService.require(db, organisme_id)
        return [
            accreditation_response(x)
            for x in await AccreditationRepository.list_for_organisme(db, organisme_id)
        ]

    @staticmethod
    async def create(
        db: AsyncSession, *, organisme_id: UUID,
        payload: AccreditationCreateRequest, actor: AuthContext, request: Request,
    ) -> AccreditationResponse:
        await OrganismeService.require(db, organisme_id)
        validate_period(payload.date_delivrance, payload.date_expiration, "l'accréditation")

        item = Accreditation(
            organisme_id=organisme_id,
            numero=clean_text(payload.numero),
            accrediteur=clean_text(payload.accrediteur),
            domaine_technique=clean_text(payload.domaine_technique),
            perimetre=clean_text(payload.perimetre),
            date_delivrance=payload.date_delivrance,
            date_expiration=payload.date_expiration,
            statut=clean_text(payload.statut) or "A_VERIFIER",
            reference_officielle=clean_text(payload.reference_officielle),
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db, action="ACCREDITATION_CREATE", categorie="DONNEES_METIER",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="accreditation", ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "organisme_id": str(organisme_id),
                "numero": item.numero,
                "accrediteur": item.accrediteur,
                "domaine_technique": item.domaine_technique,
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return accreditation_response(item)

    @staticmethod
    async def update(
        db: AsyncSession, *, organisme_id: UUID, accreditation_id: UUID,
        payload: AccreditationUpdateRequest, actor: AuthContext, request: Request,
    ) -> AccreditationResponse:
        item = await AccreditationService.require(
            db, organisme_id=organisme_id, accreditation_id=accreditation_id
        )
        changes = payload.model_dump(exclude_unset=True)
        validate_period(
            changes.get("date_delivrance", item.date_delivrance),
            changes.get("date_expiration", item.date_expiration),
            "l'accréditation",
        )

        before = {
            "numero": item.numero,
            "accrediteur": item.accrediteur,
            "domaine_technique": item.domaine_technique,
            "perimetre": item.perimetre,
            "date_delivrance": item.date_delivrance.isoformat() if item.date_delivrance else None,
            "date_expiration": item.date_expiration.isoformat() if item.date_expiration else None,
            "statut": item.statut,
            "reference_officielle": item.reference_officielle,
        }

        text_fields = {"numero", "accrediteur", "domaine_technique", "perimetre", "statut", "reference_officielle"}
        for field, value in changes.items():
            if field in text_fields:
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db, action="ACCREDITATION_UPDATE", categorie="DONNEES_METIER",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="accreditation", ressource_id=item.id,
            adresse_ip=client_ip(request), valeurs_avant=before,
            valeurs_apres={
                "numero": item.numero,
                "accrediteur": item.accrediteur,
                "domaine_technique": item.domaine_technique,
                "perimetre": item.perimetre,
                "date_delivrance": item.date_delivrance.isoformat() if item.date_delivrance else None,
                "date_expiration": item.date_expiration.isoformat() if item.date_expiration else None,
                "statut": item.statut,
                "reference_officielle": item.reference_officielle,
            },
        )
        await db.commit()
        await db.refresh(item)
        return accreditation_response(item)

    @staticmethod
    async def decide(
        db: AsyncSession, *, organisme_id: UUID, accreditation_id: UUID,
        payload: AccreditationDecisionRequest, actor: AuthContext, request: Request,
    ) -> AccreditationResponse:
        item = await AccreditationService.require(
            db, organisme_id=organisme_id, accreditation_id=accreditation_id
        )
        before = {
            "decision_hauqe": item.decision_hauqe,
            "date_decision": item.date_decision.isoformat() if item.date_decision else None,
            "statut": item.statut,
        }
        item.decision_hauqe = payload.decision_hauqe.strip()
        item.date_decision = date.today()
        if payload.statut is not None:
            item.statut = payload.statut.strip()

        await write_audit_event(
            db, action="ACCREDITATION_DECISION", categorie="DECISION_METIER",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="accreditation", ressource_id=item.id,
            adresse_ip=client_ip(request), valeurs_avant=before,
            valeurs_apres={
                "decision_hauqe": item.decision_hauqe,
                "date_decision": item.date_decision.isoformat(),
                "statut": item.statut,
            },
            contexte={"motif": clean_text(payload.motif)},
        )
        await db.commit()
        await db.refresh(item)
        return accreditation_response(item)


# ============================================================
# HISTORIQUE MÉTIER CERTIFICATION
# ============================================================

class CertificationEventService:
    @staticmethod
    async def record(
        db: AsyncSession, *, certification_id: UUID,
        type_evenement: str, ancien_statut: str | None,
        nouveau_statut: str | None, motif: str | None,
        source: str | None, acteur_id: UUID | None,
    ) -> EvenementCertification:
        item = EvenementCertification(
            certification_id=certification_id,
            type_evenement=type_evenement,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            date_evenement=datetime.now(timezone.utc),
            motif=motif,
            source=source,
            acteur_id=acteur_id,
        )
        db.add(item)
        await db.flush()
        return item

    @staticmethod
    async def list(db: AsyncSession, certification_id: UUID) -> list[EvenementCertificationResponse]:
        return [
            event_response(x)
            for x in await EvenementCertificationRepository.list(db, certification_id)
        ]


# ============================================================
# CERTIFICATIONS
# ============================================================

class CertificationService:
    @staticmethod
    async def require(db: AsyncSession, certification_id: UUID) -> Certification:
        item = await CertificationRepository.get(db, certification_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Certification introuvable.")
        return item

    @staticmethod
    async def list(
        db: AsyncSession, *, search: str | None,
        entreprise_id: UUID | None, organisme_id: UUID | None,
        norme_id: UUID | None, statut: str | None,
        limit: int, offset: int,
    ) -> CertificationListResponse:
        items, total = await CertificationRepository.list(
            db, search=search, entreprise_id=entreprise_id,
            organisme_id=organisme_id, norme_id=norme_id,
            statut=statut, limit=limit, offset=offset,
        )
        return CertificationListResponse(
            total=total, limit=limit, offset=offset,
            items=[certification_response(x) for x in items],
        )

    @staticmethod
    async def detail(db: AsyncSession, certification_id: UUID) -> CertificationResponse:
        return certification_response(await CertificationService.require(db, certification_id))

    @staticmethod
    async def create(
        db: AsyncSession, *, payload: CertificationCreateRequest,
        actor: AuthContext, request: Request,
    ) -> CertificationResponse:
        identifier = payload.identifiant_national.strip().upper()

        if await CertificationRepository.get_by_identifiant(db, identifier):
            raise HTTPException(status_code=409, detail="Une certification possède déjà cet identifiant national.")

        entreprise = await CertificationRepository.get_entreprise(db, payload.entreprise_id)
        if entreprise is None:
            raise HTTPException(status_code=404, detail="Entreprise introuvable.")
        if (entreprise.statut or "").strip().upper() == "ARCHIVE":
            raise HTTPException(status_code=409, detail="Impossible de créer une certification pour une entreprise archivée.")

        organisme = await CertificationRepository.get_organisme(db, payload.organisme_id)
        if organisme is None:
            raise HTTPException(status_code=404, detail="Organisme certificateur introuvable.")

        norme = await CertificationRepository.get_norme(db, payload.norme_id)
        if norme is None:
            raise HTTPException(status_code=404, detail="Norme introuvable.")

        if payload.accreditation_id:
            acc = await CertificationRepository.get_accreditation_for_organisme(
                db, organisme_id=payload.organisme_id,
                accreditation_id=payload.accreditation_id,
            )
            if acc is None:
                raise HTTPException(status_code=422, detail="L'accréditation indiquée n'appartient pas à cet organisme.")

        validate_certification_dates(payload.date_obtention, payload.date_effet, payload.date_expiration)

        duplicate = await CertificationRepository.find_same_scope(
            db, entreprise_id=payload.entreprise_id,
            organisme_id=payload.organisme_id,
            norme_id=payload.norme_id, portee=payload.portee,
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="Une certification existe déjà pour cette combinaison entreprise / organisme / norme / portée.")

        item = Certification(
            identifiant_national=identifier,
            entreprise_id=payload.entreprise_id,
            organisme_id=payload.organisme_id,
            accreditation_id=payload.accreditation_id,
            norme_id=payload.norme_id,
            numero_certificat=clean_text(payload.numero_certificat),
            portee=clean_text(payload.portee),
            date_obtention=payload.date_obtention,
            date_effet=payload.date_effet,
            date_expiration=payload.date_expiration,
            statut=clean_text(payload.statut) or "A_VERIFIER",
            motif_statut=clean_text(payload.motif_statut),
            authenticite_verifiee=False,
            certification_strategique=payload.certification_strategique,
            source_donnee=clean_text(payload.source_donnee),
        )
        db.add(item)

        try:
            await db.flush()
            await CertificationEventService.record(
                db, certification_id=item.id, type_evenement="CREATION",
                ancien_statut=None, nouveau_statut=item.statut,
                motif=item.motif_statut, source=item.source_donnee or "API",
                acteur_id=actor.user.id,
            )
            await write_audit_event(
                db, action="CERTIFICATION_CREATE", categorie="DONNEES_METIER",
                resultat="SUCCES", utilisateur_id=actor.user.id,
                ressource_type="certification", ressource_id=item.id,
                adresse_ip=client_ip(request),
                valeurs_apres={
                    "identifiant_national": item.identifiant_national,
                    "entreprise_id": str(item.entreprise_id),
                    "organisme_id": str(item.organisme_id),
                    "accreditation_id": str(item.accreditation_id) if item.accreditation_id else None,
                    "norme_id": str(item.norme_id),
                    "portee": item.portee,
                    "statut": item.statut,
                    "authenticite_verifiee": False,
                },
            )
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=409, detail="Conflit d'intégrité lors de la création de la certification.")

        await db.refresh(item)
        return certification_response(item)

    @staticmethod
    async def update(
        db: AsyncSession, *, certification_id: UUID,
        payload: CertificationUpdateRequest, actor: AuthContext, request: Request,
    ) -> CertificationResponse:
        item = await CertificationService.require(db, certification_id)
        changes = payload.model_dump(exclude_unset=True)
        validate_certification_dates(
            changes.get("date_obtention", item.date_obtention),
            changes.get("date_effet", item.date_effet),
            changes.get("date_expiration", item.date_expiration),
        )
        before = {
            "numero_certificat": item.numero_certificat,
            "portee": item.portee,
            "date_obtention": item.date_obtention.isoformat() if item.date_obtention else None,
            "date_effet": item.date_effet.isoformat() if item.date_effet else None,
            "date_expiration": item.date_expiration.isoformat() if item.date_expiration else None,
            "certification_strategique": item.certification_strategique,
            "source_donnee": item.source_donnee,
        }

        for field, value in changes.items():
            if field in {"numero_certificat", "portee", "source_donnee"}:
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db, action="CERTIFICATION_UPDATE", categorie="DONNEES_METIER",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="certification", ressource_id=item.id,
            adresse_ip=client_ip(request), valeurs_avant=before,
            valeurs_apres={
                "numero_certificat": item.numero_certificat,
                "portee": item.portee,
                "date_obtention": item.date_obtention.isoformat() if item.date_obtention else None,
                "date_effet": item.date_effet.isoformat() if item.date_effet else None,
                "date_expiration": item.date_expiration.isoformat() if item.date_expiration else None,
                "certification_strategique": item.certification_strategique,
                "source_donnee": item.source_donnee,
            },
        )
        await db.commit()
        await db.refresh(item)
        return certification_response(item)

    @staticmethod
    async def change_status(
        db: AsyncSession, *, certification_id: UUID,
        payload: CertificationStatusRequest, actor: AuthContext, request: Request,
    ) -> CertificationResponse:
        item = await CertificationService.require(db, certification_id)
        old_status = item.statut
        new_status = payload.nouveau_statut.strip()
        if old_status == new_status:
            return certification_response(item)

        item.statut = new_status
        item.motif_statut = payload.motif.strip()
        await CertificationEventService.record(
            db, certification_id=item.id, type_evenement="CHANGEMENT_STATUT",
            ancien_statut=old_status, nouveau_statut=new_status,
            motif=payload.motif.strip(), source=clean_text(payload.source) or "API",
            acteur_id=actor.user.id,
        )
        await write_audit_event(
            db, action="CERTIFICATION_STATUS_CHANGE", categorie="DONNEES_METIER",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="certification", ressource_id=item.id,
            adresse_ip=client_ip(request), valeurs_avant={"statut": old_status},
            valeurs_apres={"statut": new_status, "motif_statut": item.motif_statut},
        )
        await db.commit()
        await db.refresh(item)
        return certification_response(item)

    @staticmethod
    async def verify(
        db: AsyncSession, *, certification_id: UUID,
        payload: CertificationVerificationRequest, actor: AuthContext, request: Request,
    ) -> CertificationResponse:
        item = await CertificationService.require(db, certification_id)
        if payload.authenticite_verifiee and not await CertificationRepository.has_active_document(db, certification_id):
            raise HTTPException(status_code=409, detail="Une vérification positive exige au moins un document actif lié à la certification.")

        old_status = item.statut
        old_auth = item.authenticite_verifiee
        item.authenticite_verifiee = payload.authenticite_verifiee
        if payload.nouveau_statut is not None:
            item.statut = payload.nouveau_statut.strip()
            item.motif_statut = payload.motif.strip()

        await CertificationEventService.record(
            db, certification_id=item.id, type_evenement="VERIFICATION_AUTHENTICITE",
            ancien_statut=old_status, nouveau_statut=item.statut,
            motif=payload.motif.strip(), source=clean_text(payload.source) or "VERIFICATION",
            acteur_id=actor.user.id,
        )
        await write_audit_event(
            db, action="CERTIFICATION_VERIFY", categorie="VERIFICATION",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="certification", ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant={"authenticite_verifiee": old_auth, "statut": old_status},
            valeurs_apres={"authenticite_verifiee": item.authenticite_verifiee, "statut": item.statut},
            contexte={"motif": payload.motif.strip()},
        )
        await db.commit()
        await db.refresh(item)
        return certification_response(item)


# ============================================================
# COUVERTURES
# ============================================================

class CouvertureService:
    ALLOWED_TYPES = {"PRODUIT", "SERVICE", "SITE", "ACTIVITE"}

    @staticmethod
    async def list(db: AsyncSession, certification_id: UUID) -> list[CouvertureResponse]:
        await CertificationService.require(db, certification_id)
        return [couverture_response(x) for x in await CouvertureRepository.list(db, certification_id)]

    @staticmethod
    async def create(
        db: AsyncSession, *, certification_id: UUID,
        payload: CouvertureCreateRequest, actor: AuthContext, request: Request,
    ) -> CouvertureResponse:
        certification = await CertificationService.require(db, certification_id)
        type_cov = payload.type_couverture.strip().upper()
        if type_cov not in CouvertureService.ALLOWED_TYPES:
            raise HTTPException(status_code=422, detail="type_couverture doit être PRODUIT, SERVICE, SITE ou ACTIVITE.")

        offre_id = payload.offre_entreprise_id
        site_id = payload.site_entreprise_id

        if type_cov in {"PRODUIT", "SERVICE"}:
            if offre_id is None or site_id is not None:
                raise HTTPException(status_code=422, detail="Une couverture PRODUIT/SERVICE exige offre_entreprise_id et interdit site_entreprise_id.")
            offre = await CouvertureRepository.get_offre(db, offre_id)
            if offre is None:
                raise HTTPException(status_code=404, detail="Offre d'entreprise introuvable.")
            if offre.entreprise_id != certification.entreprise_id:
                raise HTTPException(status_code=409, detail="L'offre n'appartient pas à l'entreprise titulaire de la certification.")
            if (offre.type_offre or "").strip().upper() != type_cov:
                raise HTTPException(status_code=409, detail="Le type de couverture ne correspond pas au type de l'offre.")
            if (offre.statut or "").strip().upper() == "INACTIF":
                raise HTTPException(status_code=409, detail="L'offre liée est inactive.")

        elif type_cov == "SITE":
            if site_id is None or offre_id is not None:
                raise HTTPException(status_code=422, detail="Une couverture SITE exige site_entreprise_id et interdit offre_entreprise_id.")
            site = await CouvertureRepository.get_site(db, site_id)
            if site is None:
                raise HTTPException(status_code=404, detail="Site d'entreprise introuvable.")
            if site.entreprise_id != certification.entreprise_id:
                raise HTTPException(status_code=409, detail="Le site n'appartient pas à l'entreprise titulaire de la certification.")
            if (site.statut or "").strip().upper() == "INACTIF":
                raise HTTPException(status_code=409, detail="Le site lié est inactif.")

        else:
            if offre_id is not None or site_id is not None:
                raise HTTPException(status_code=422, detail="Une couverture ACTIVITE est décrite textuellement dans le MPD actuel.")

        item = CouvertureCertification(
            certification_id=certification_id,
            type_couverture=type_cov,
            offre_entreprise_id=offre_id,
            site_entreprise_id=site_id,
            libelle_couverture=clean_text(payload.libelle_couverture),
            details=clean_text(payload.details),
            statut=clean_text(payload.statut) or "ACTIF",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db, action="CERTIFICATION_COVERAGE_CREATE", categorie="DONNEES_METIER",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="couverture_certification", ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "certification_id": str(certification_id),
                "type_couverture": item.type_couverture,
                "offre_entreprise_id": str(item.offre_entreprise_id) if item.offre_entreprise_id else None,
                "site_entreprise_id": str(item.site_entreprise_id) if item.site_entreprise_id else None,
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return couverture_response(item)

    @staticmethod
    async def update(
        db: AsyncSession, *, certification_id: UUID, couverture_id: UUID,
        payload: CouvertureUpdateRequest, actor: AuthContext, request: Request,
    ) -> CouvertureResponse:
        await CertificationService.require(db, certification_id)
        item = await CouvertureRepository.get(db, certification_id=certification_id, couverture_id=couverture_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Couverture introuvable.")

        before = {"libelle_couverture": item.libelle_couverture, "details": item.details, "statut": item.statut}
        for field, value in payload.model_dump(exclude_unset=True).items():
            value = clean_text(value) if isinstance(value, str) or value is None else value
            setattr(item, field, value)

        await write_audit_event(
            db, action="CERTIFICATION_COVERAGE_UPDATE", categorie="DONNEES_METIER",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="couverture_certification", ressource_id=item.id,
            adresse_ip=client_ip(request), valeurs_avant=before,
            valeurs_apres={"libelle_couverture": item.libelle_couverture, "details": item.details, "statut": item.statut},
        )
        await db.commit()
        await db.refresh(item)
        return couverture_response(item)


# ============================================================
# AUDITS CERTIFICATION
# ============================================================

class AuditCertificationService:
    @staticmethod
    async def list(db: AsyncSession, certification_id: UUID) -> list[AuditCertificationResponse]:
        await CertificationService.require(db, certification_id)
        return [audit_response(x) for x in await AuditCertificationRepository.list(db, certification_id)]

    @staticmethod
    async def create(
        db: AsyncSession, *, certification_id: UUID,
        payload: AuditCertificationCreateRequest, actor: AuthContext, request: Request,
    ) -> AuditCertificationResponse:
        await CertificationService.require(db, certification_id)
        item = AuditCertification(
            certification_id=certification_id,
            type_audit=clean_text(payload.type_audit),
            date_prevue=payload.date_prevue,
            date_realisee=payload.date_realisee,
            auditeur=clean_text(payload.auditeur),
            resultat=clean_text(payload.resultat),
            prochain_audit_at=payload.prochain_audit_at,
            observations=clean_text(payload.observations),
            statut=clean_text(payload.statut) or "PLANIFIE",
        )
        db.add(item)
        await db.flush()
        await write_audit_event(
            db, action="CERTIFICATION_AUDIT_CREATE", categorie="DONNEES_METIER",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="audit_certification", ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "certification_id": str(certification_id),
                "type_audit": item.type_audit,
                "date_prevue": item.date_prevue.isoformat() if item.date_prevue else None,
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return audit_response(item)

    @staticmethod
    async def update(
        db: AsyncSession, *, certification_id: UUID, audit_id: UUID,
        payload: AuditCertificationUpdateRequest, actor: AuthContext, request: Request,
    ) -> AuditCertificationResponse:
        await CertificationService.require(db, certification_id)
        item = await AuditCertificationRepository.get(db, certification_id=certification_id, audit_id=audit_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Audit de certification introuvable.")

        before = {
            "type_audit": item.type_audit,
            "date_prevue": item.date_prevue.isoformat() if item.date_prevue else None,
            "date_realisee": item.date_realisee.isoformat() if item.date_realisee else None,
            "auditeur": item.auditeur,
            "resultat": item.resultat,
            "prochain_audit_at": item.prochain_audit_at.isoformat() if item.prochain_audit_at else None,
            "observations": item.observations,
            "statut": item.statut,
        }
        for field, value in payload.model_dump(exclude_unset=True).items():
            if field in {"type_audit", "auditeur", "resultat", "observations", "statut"}:
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db, action="CERTIFICATION_AUDIT_UPDATE", categorie="DONNEES_METIER",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="audit_certification", ressource_id=item.id,
            adresse_ip=client_ip(request), valeurs_avant=before,
            valeurs_apres={
                "type_audit": item.type_audit,
                "date_prevue": item.date_prevue.isoformat() if item.date_prevue else None,
                "date_realisee": item.date_realisee.isoformat() if item.date_realisee else None,
                "auditeur": item.auditeur,
                "resultat": item.resultat,
                "prochain_audit_at": item.prochain_audit_at.isoformat() if item.prochain_audit_at else None,
                "observations": item.observations,
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return audit_response(item)


# ============================================================
# RENOUVELLEMENTS
# ============================================================

class RenouvellementService:
    @staticmethod
    async def list(db: AsyncSession, certification_id: UUID) -> list[RenouvellementResponse]:
        await CertificationService.require(db, certification_id)
        return [renewal_response(x) for x in await RenouvellementRepository.list(db, certification_id)]

    @staticmethod
    async def create(
        db: AsyncSession, *, certification_id: UUID,
        payload: RenouvellementCreateRequest, actor: AuthContext, request: Request,
    ) -> RenouvellementResponse:
        await CertificationService.require(db, certification_id)
        validate_period(payload.date_ouverture, payload.date_limite, "la procédure de renouvellement")

        item = RenouvellementCertification(
            certification_id=certification_id,
            date_ouverture=payload.date_ouverture,
            date_limite=payload.date_limite,
            preuves=payload.preuves,
            statut=clean_text(payload.statut) or "OUVERT",
        )
        db.add(item)
        await db.flush()
        await write_audit_event(
            db, action="CERTIFICATION_RENEWAL_CREATE", categorie="DONNEES_METIER",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="renouvellement_certification", ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "certification_id": str(certification_id),
                "date_ouverture": item.date_ouverture.isoformat() if item.date_ouverture else None,
                "date_limite": item.date_limite.isoformat() if item.date_limite else None,
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return renewal_response(item)

    @staticmethod
    async def update(
        db: AsyncSession, *, certification_id: UUID, renouvellement_id: UUID,
        payload: RenouvellementUpdateRequest, actor: AuthContext, request: Request,
    ) -> RenouvellementResponse:
        await CertificationService.require(db, certification_id)
        item = await RenouvellementRepository.get(
            db, certification_id=certification_id, renouvellement_id=renouvellement_id
        )
        if item is None:
            raise HTTPException(status_code=404, detail="Procédure de renouvellement introuvable.")

        changes = payload.model_dump(exclude_unset=True)
        validate_period(
            changes.get("date_ouverture", item.date_ouverture),
            changes.get("date_limite", item.date_limite),
            "la procédure de renouvellement",
        )
        before = {
            "date_ouverture": item.date_ouverture.isoformat() if item.date_ouverture else None,
            "date_limite": item.date_limite.isoformat() if item.date_limite else None,
            "preuves": item.preuves,
            "statut": item.statut,
        }
        for field, value in changes.items():
            if field == "statut":
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db, action="CERTIFICATION_RENEWAL_UPDATE", categorie="DONNEES_METIER",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="renouvellement_certification", ressource_id=item.id,
            adresse_ip=client_ip(request), valeurs_avant=before,
            valeurs_apres={
                "date_ouverture": item.date_ouverture.isoformat() if item.date_ouverture else None,
                "date_limite": item.date_limite.isoformat() if item.date_limite else None,
                "preuves": item.preuves,
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return renewal_response(item)

    @staticmethod
    async def decide(
        db: AsyncSession, *, certification_id: UUID, renouvellement_id: UUID,
        payload: RenouvellementDecisionRequest, actor: AuthContext, request: Request,
    ) -> RenouvellementResponse:
        await CertificationService.require(db, certification_id)
        item = await RenouvellementRepository.get(
            db, certification_id=certification_id, renouvellement_id=renouvellement_id
        )
        if item is None:
            raise HTTPException(status_code=404, detail="Procédure de renouvellement introuvable.")

        before = {
            "date_decision": item.date_decision.isoformat() if item.date_decision else None,
            "decision": item.decision,
            "resultat": item.resultat,
            "justification": item.justification,
            "statut": item.statut,
        }
        item.date_decision = date.today()
        item.decision = payload.decision.strip()
        item.resultat = clean_text(payload.resultat)
        item.justification = payload.justification.strip()
        if payload.statut is not None:
            item.statut = payload.statut.strip()

        await write_audit_event(
            db, action="CERTIFICATION_RENEWAL_DECISION", categorie="DECISION_METIER",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="renouvellement_certification", ressource_id=item.id,
            adresse_ip=client_ip(request), valeurs_avant=before,
            valeurs_apres={
                "date_decision": item.date_decision.isoformat(),
                "decision": item.decision,
                "resultat": item.resultat,
                "justification": item.justification,
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return renewal_response(item)
