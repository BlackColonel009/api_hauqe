"""
Routes API du domaine Organismes / Certifications.

Le fichier expose le module principal et ses sous-modules en une seule
intégration. Les permissions restent contrôlées côté serveur.
"""

from __future__ import annotations

from uuid import UUID
import csv
import io

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
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
    OrganismeRegistryResponse,
    OrganismeResponse,
    OrganismeUpdateRequest,
    OrganismeVerificationRequest,
    RenouvellementCreateRequest,
    RenouvellementDecisionRequest,
    RenouvellementResponse,
    RenouvellementUpdateRequest,
)

from app.schemas.certification_registry import (
    CertificationFiltersResponse,
    CertificationRegistryItem,
    CertificationRegistryResponse,
)
from app.services.certification_registry_service import (
    CertificationRegistryService,
)

from app.services.auth_service import AuthContext
from app.services.organismes_certifications_service import (
    AccreditationService,
    AuditCertificationService,
    CertificationEventService,
    CertificationService,
    CouvertureService,
    NormeService,
    OrganismeService,
    RenouvellementService,
    accreditation_response,
)


router = APIRouter()


# ============================================================
# NORMES — DÉPENDANCE LECTURE
# ============================================================

@router.get("/normes", response_model=list[NormeResponse], tags=["Référentiels - Normes"])
async def list_normes(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("REFERENTIELS.LIRE")),
):
    return await NormeService.list(db)


@router.get("/normes/{norme_id}", response_model=NormeResponse, tags=["Référentiels - Normes"])
async def get_norme(
    norme_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("REFERENTIELS.LIRE")),
):
    return await NormeService.get(db, norme_id)


# ============================================================
# ORGANISMES
# ============================================================


@router.get(
    "/organismes/filters",
    response_model=OrganismeFiltersResponse,
    tags=["Organismes"],
)
async def organisme_filters(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ORGANISMES.LIRE")),
):
    return await OrganismeService.filters(db)


@router.get(
    "/organismes/registry",
    response_model=OrganismeRegistryResponse,
    tags=["Organismes"],
)
async def organisme_registry(
    search: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    pays: str | None = Query(default=None, max_length=255),
    type_organisme: str | None = Query(default=None, max_length=255),
    accrediteur: str | None = Query(default=None, max_length=255),
    domaine: str | None = Query(default=None, max_length=255),
    sort: str = Query(default="name_asc", max_length=64),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ORGANISMES.LIRE")),
):
    return await OrganismeService.registry(
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


@router.get(
    "/organismes/export",
    tags=["Organismes"],
)
async def export_organismes(
    request: Request,
    motif: str = Query(min_length=3, max_length=500),
    search: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    pays: str | None = Query(default=None, max_length=255),
    type_organisme: str | None = Query(default=None, max_length=255),
    accrediteur: str | None = Query(default=None, max_length=255),
    domaine: str | None = Query(default=None, max_length=255),
    sort: str = Query(default="name_asc", max_length=64),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("ORGANISMES.EXPORTER")
    ),
):
    data = await OrganismeService.export_registry(
        db,
        search=search,
        statut=statut,
        pays=pays,
        type_organisme=type_organisme,
        accrediteur=accrediteur,
        domaine=domaine,
        sort=sort,
        motif=motif,
        actor=actor,
        request=request,
    )

    buffer = io.StringIO()
    writer = csv.writer(
        buffer,
        delimiter=";",
        quoting=csv.QUOTE_MINIMAL,
    )

    writer.writerow(
        [
            "Identifiant",
            "Organisme",
            "Sigle",
            "Type",
            "Pays",
            "Statut",
            "Accréditations",
            "Accréditeurs",
            "Domaines",
            "Certifications",
            "Dernière vérification",
            "Prochaine expiration accréditation",
        ]
    )

    for item in data.items:
        writer.writerow(
            [
                item.identifiant_national or "",
                item.nom_officiel or "",
                item.sigle or "",
                item.type_organisme or "",
                item.pays or "",
                item.statut or "",
                item.accreditation_count,
                item.accreditors or "",
                item.domains or "",
                item.certification_count,
                (
                    item.date_derniere_verification.isoformat()
                    if item.date_derniere_verification
                    else ""
                ),
                (
                    item.next_accreditation_expiration.isoformat()
                    if item.next_accreditation_expiration
                    else ""
                ),
            ]
        )

    content = "\ufeff" + buffer.getvalue()

    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                'attachment; filename="hauqe-organismes.csv"'
        },
    )


@router.get("/organismes", tags=["Organismes"])
async def list_organismes(
    search: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ORGANISMES.LIRE")),
):
    return await OrganismeService.list(
        db, search=search, statut=statut, limit=limit, offset=offset
    )


@router.get("/organismes/{organisme_id}", response_model=OrganismeResponse, tags=["Organismes"])
async def get_organisme(
    organisme_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ORGANISMES.LIRE")),
):
    return await OrganismeService.detail(db, organisme_id)


@router.post("/organismes", response_model=OrganismeResponse, status_code=status.HTTP_201_CREATED, tags=["Organismes"])
async def create_organisme(
    payload: OrganismeCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ORGANISMES.CREER")),
):
    return await OrganismeService.create(
        db, payload=payload, actor=actor, request=request
    )


@router.patch("/organismes/{organisme_id}", response_model=OrganismeResponse, tags=["Organismes"])
async def update_organisme(
    organisme_id: UUID,
    payload: OrganismeUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ORGANISMES.MODIFIER")),
):
    return await OrganismeService.update(
        db, organisme_id=organisme_id, payload=payload, actor=actor, request=request
    )


@router.post("/organismes/{organisme_id}/verification", response_model=OrganismeResponse, tags=["Organismes"])
async def verify_organisme(
    organisme_id: UUID,
    payload: OrganismeVerificationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.VERIFIER")),
):
    return await OrganismeService.verify(
        db, organisme_id=organisme_id, payload=payload, actor=actor, request=request
    )


# ============================================================
# ACCRÉDITATIONS
# ============================================================

@router.get("/organismes/{organisme_id}/accreditations", response_model=list[AccreditationResponse], tags=["Organismes - Accréditations"])
async def list_accreditations(
    organisme_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ORGANISMES.LIRE")),
):
    return await AccreditationService.list(db, organisme_id)


@router.get("/organismes/{organisme_id}/accreditations/{accreditation_id}", response_model=AccreditationResponse, tags=["Organismes - Accréditations"])
async def get_accreditation(
    organisme_id: UUID,
    accreditation_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ORGANISMES.LIRE")),
):
    item = await AccreditationService.require(
        db, organisme_id=organisme_id, accreditation_id=accreditation_id
    )
    return accreditation_response(item)


@router.post("/organismes/{organisme_id}/accreditations", response_model=AccreditationResponse, status_code=status.HTTP_201_CREATED, tags=["Organismes - Accréditations"])
async def create_accreditation(
    organisme_id: UUID,
    payload: AccreditationCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ORGANISMES.MODIFIER")),
):
    return await AccreditationService.create(
        db, organisme_id=organisme_id, payload=payload, actor=actor, request=request
    )


@router.patch("/organismes/{organisme_id}/accreditations/{accreditation_id}", response_model=AccreditationResponse, tags=["Organismes - Accréditations"])
async def update_accreditation(
    organisme_id: UUID,
    accreditation_id: UUID,
    payload: AccreditationUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ORGANISMES.MODIFIER")),
):
    return await AccreditationService.update(
        db, organisme_id=organisme_id, accreditation_id=accreditation_id,
        payload=payload, actor=actor, request=request
    )


@router.post("/organismes/{organisme_id}/accreditations/{accreditation_id}/decision", response_model=AccreditationResponse, tags=["Organismes - Accréditations"])
async def decide_accreditation(
    organisme_id: UUID,
    accreditation_id: UUID,
    payload: AccreditationDecisionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.VERIFIER")),
):
    return await AccreditationService.decide(
        db, organisme_id=organisme_id, accreditation_id=accreditation_id,
        payload=payload, actor=actor, request=request
    )


# ============================================================
# CERTIFICATIONS
# ============================================================


# ------------------------------------------------------------
# Projection registre Certifications
#
# IMPORTANT :
# Ces routes statiques sont déclarées AVANT
# /certifications/{certification_id}. FastAPI teste les routes
# dans l'ordre ; cela évite que "filters", "registry" ou "export"
# soient interprétés comme un UUID.
# ------------------------------------------------------------

@router.get(
    "/certifications/filters",
    response_model=CertificationFiltersResponse,
    tags=["Certifications - Registre"],
)
async def certification_filters(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("CERTIFICATIONS.LIRE")
    ),
):
    return await CertificationRegistryService.filters(db)


@router.get(
    "/certifications/registry",
    response_model=CertificationRegistryResponse,
    tags=["Certifications - Registre"],
)
async def certification_registry(
    search: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    entreprise_id: UUID | None = Query(default=None),
    organisme_id: UUID | None = Query(default=None),
    norme_id: UUID | None = Query(default=None),
    deadline: str | None = Query(default=None, max_length=32),
    verification: str | None = Query(default=None, max_length=32),
    sort: str = Query(default="deadline", max_length=32),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("CERTIFICATIONS.LIRE")
    ),
):
    return await CertificationRegistryService.registry(
        db,
        search=search,
        statut=statut,
        entreprise_id=entreprise_id,
        organisme_id=organisme_id,
        norme_id=norme_id,
        deadline=deadline,
        verification=verification,
        sort=sort,
        limit=limit,
        offset=offset,
    )


def _certification_registry_csv(
    data: CertificationRegistryResponse,
) -> str:
    buffer = io.StringIO()

    writer = csv.writer(
        buffer,
        delimiter=";",
        quoting=csv.QUOTE_MINIMAL,
    )

    writer.writerow(
        [
            "Identifiant national",
            "Numéro certificat",
            "Entreprise",
            "Organisme",
            "Norme",
            "Version",
            "Portée",
            "Date obtention",
            "Date expiration",
            "Jours restants",
            "Statut",
            "Authenticité vérifiée",
            "Certification stratégique",
            "Renouvellement ouvert",
        ]
    )

    for item in data.items:
        writer.writerow(
            [
                item.identifiant_national,
                item.numero_certificat or "",
                item.entreprise_name,
                item.organisme_name,
                item.norme_code or item.norme_name or "",
                item.norme_version or "",
                item.portee or "",
                (
                    item.date_obtention.isoformat()
                    if item.date_obtention
                    else ""
                ),
                (
                    item.date_expiration.isoformat()
                    if item.date_expiration
                    else ""
                ),
                (
                    item.days_remaining
                    if item.days_remaining is not None
                    else ""
                ),
                item.statut or "",
                (
                    "OUI"
                    if item.authenticite_verifiee
                    else "NON"
                ),
                (
                    "OUI"
                    if item.certification_strategique
                    else "NON"
                ),
                (
                    "OUI"
                    if item.renewal_open
                    else "NON"
                ),
            ]
        )

    return "\ufeff" + buffer.getvalue()


@router.get(
    "/certifications/export",
    tags=["Certifications - Registre"],
)
async def export_certifications_registry(
    request: Request,
    motif: str = Query(min_length=3, max_length=500),
    search: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    entreprise_id: UUID | None = Query(default=None),
    organisme_id: UUID | None = Query(default=None),
    norme_id: UUID | None = Query(default=None),
    deadline: str | None = Query(default=None, max_length=32),
    verification: str | None = Query(default=None, max_length=32),
    sort: str = Query(default="deadline", max_length=32),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("CERTIFICATIONS.EXPORTER")
    ),
):
    filters = {
        "search": search,
        "statut": statut,
        "entreprise_id": (
            str(entreprise_id)
            if entreprise_id
            else None
        ),
        "organisme_id": (
            str(organisme_id)
            if organisme_id
            else None
        ),
        "norme_id": (
            str(norme_id)
            if norme_id
            else None
        ),
        "deadline": deadline,
        "verification": verification,
        "sort": sort,
    }

    data = await CertificationRegistryService.registry(
        db,
        search=search,
        statut=statut,
        entreprise_id=entreprise_id,
        organisme_id=organisme_id,
        norme_id=norme_id,
        deadline=deadline,
        verification=verification,
        sort=sort,
        limit=5000,
        offset=0,
    )

    await CertificationRegistryService.audit_export(
        db,
        actor=actor,
        request=request,
        motif=motif,
        filters=filters,
        count=data.total,
    )

    return Response(
        content=_certification_registry_csv(data),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                'attachment; filename="hauqe-certifications.csv"'
        },
    )


@router.get(
    "/certifications/{certification_id}/context",
    response_model=CertificationRegistryItem,
    tags=["Certifications - Registre"],
)
async def certification_context(
    certification_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("CERTIFICATIONS.LIRE")
    ),
):
    return await CertificationRegistryService.item(
        db,
        certification_id,
    )


@router.get(
    "/certifications/{certification_id}/export",
    tags=["Certifications - Registre"],
)
async def export_certification_registry_item(
    certification_id: UUID,
    request: Request,
    motif: str = Query(min_length=3, max_length=500),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("CERTIFICATIONS.EXPORTER")
    ),
):
    item = await CertificationRegistryService.item(
        db,
        certification_id,
    )

    data = CertificationRegistryResponse(
        total=1,
        limit=1,
        offset=0,
        summary={
            "total": 1,
        },
        items=[item],
    )

    await CertificationRegistryService.audit_export(
        db,
        actor=actor,
        request=request,
        motif=motif,
        filters={},
        count=1,
        certification_id=certification_id,
    )

    return Response(
        content=_certification_registry_csv(data),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                "attachment; "
                f'filename="certification-{certification_id}.csv"'
            )
        },
    )



@router.get("/certifications", response_model=CertificationListResponse, tags=["Certifications"])
async def list_certifications(
    search: str | None = Query(default=None, max_length=255),
    entreprise_id: UUID | None = Query(default=None),
    organisme_id: UUID | None = Query(default=None),
    norme_id: UUID | None = Query(default=None),
    statut: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.LIRE")),
):
    return await CertificationService.list(
        db, search=search, entreprise_id=entreprise_id,
        organisme_id=organisme_id, norme_id=norme_id,
        statut=statut, limit=limit, offset=offset
    )


@router.get("/certifications/{certification_id}", response_model=CertificationResponse, tags=["Certifications"])
async def get_certification(
    certification_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.LIRE")),
):
    return await CertificationService.detail(db, certification_id)


@router.post("/certifications", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED, tags=["Certifications"])
async def create_certification(
    payload: CertificationCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.CREER")),
):
    return await CertificationService.create(
        db, payload=payload, actor=actor, request=request
    )


@router.patch("/certifications/{certification_id}", response_model=CertificationResponse, tags=["Certifications"])
async def update_certification(
    certification_id: UUID,
    payload: CertificationUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.MODIFIER")),
):
    return await CertificationService.update(
        db, certification_id=certification_id, payload=payload,
        actor=actor, request=request
    )


@router.post("/certifications/{certification_id}/status", response_model=CertificationResponse, tags=["Certifications"])
async def change_certification_status(
    certification_id: UUID,
    payload: CertificationStatusRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.MODIFIER")),
):
    return await CertificationService.change_status(
        db, certification_id=certification_id, payload=payload,
        actor=actor, request=request
    )


@router.post("/certifications/{certification_id}/verification", response_model=CertificationResponse, tags=["Certifications"])
async def verify_certification(
    certification_id: UUID,
    payload: CertificationVerificationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.VERIFIER")),
):
    return await CertificationService.verify(
        db, certification_id=certification_id, payload=payload,
        actor=actor, request=request
    )


@router.get("/certifications/{certification_id}/history", response_model=list[EvenementCertificationResponse], tags=["Certifications - Historique"])
async def certification_history(
    certification_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.LIRE")),
):
    await CertificationService.require(db, certification_id)
    return await CertificationEventService.list(db, certification_id)


# ============================================================
# COUVERTURES
# ============================================================

@router.get("/certifications/{certification_id}/couvertures", response_model=list[CouvertureResponse], tags=["Certifications - Couvertures"])
async def list_couvertures(
    certification_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.LIRE")),
):
    return await CouvertureService.list(db, certification_id)


@router.post("/certifications/{certification_id}/couvertures", response_model=CouvertureResponse, status_code=status.HTTP_201_CREATED, tags=["Certifications - Couvertures"])
async def create_couverture(
    certification_id: UUID,
    payload: CouvertureCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.MODIFIER")),
):
    return await CouvertureService.create(
        db, certification_id=certification_id, payload=payload,
        actor=actor, request=request
    )


@router.patch("/certifications/{certification_id}/couvertures/{couverture_id}", response_model=CouvertureResponse, tags=["Certifications - Couvertures"])
async def update_couverture(
    certification_id: UUID,
    couverture_id: UUID,
    payload: CouvertureUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.MODIFIER")),
):
    return await CouvertureService.update(
        db, certification_id=certification_id, couverture_id=couverture_id,
        payload=payload, actor=actor, request=request
    )


# ============================================================
# AUDITS CERTIFICATION
# ============================================================

@router.get("/certifications/{certification_id}/audits", response_model=list[AuditCertificationResponse], tags=["Certifications - Audits"])
async def list_audits(
    certification_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.LIRE")),
):
    return await AuditCertificationService.list(db, certification_id)


@router.post("/certifications/{certification_id}/audits", response_model=AuditCertificationResponse, status_code=status.HTTP_201_CREATED, tags=["Certifications - Audits"])
async def create_audit(
    certification_id: UUID,
    payload: AuditCertificationCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.MODIFIER")),
):
    return await AuditCertificationService.create(
        db, certification_id=certification_id, payload=payload,
        actor=actor, request=request
    )


@router.patch("/certifications/{certification_id}/audits/{audit_id}", response_model=AuditCertificationResponse, tags=["Certifications - Audits"])
async def update_audit(
    certification_id: UUID,
    audit_id: UUID,
    payload: AuditCertificationUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.MODIFIER")),
):
    return await AuditCertificationService.update(
        db, certification_id=certification_id, audit_id=audit_id,
        payload=payload, actor=actor, request=request
    )


# ============================================================
# RENOUVELLEMENTS
# ============================================================

@router.get("/certifications/{certification_id}/renewals", response_model=list[RenouvellementResponse], tags=["Certifications - Renouvellements"])
async def list_renewals(
    certification_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.LIRE")),
):
    return await RenouvellementService.list(db, certification_id)


@router.post("/certifications/{certification_id}/renewals", response_model=RenouvellementResponse, status_code=status.HTTP_201_CREATED, tags=["Certifications - Renouvellements"])
async def create_renewal(
    certification_id: UUID,
    payload: RenouvellementCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.MODIFIER")),
):
    return await RenouvellementService.create(
        db, certification_id=certification_id, payload=payload,
        actor=actor, request=request
    )


@router.patch("/certifications/{certification_id}/renewals/{renouvellement_id}", response_model=RenouvellementResponse, tags=["Certifications - Renouvellements"])
async def update_renewal(
    certification_id: UUID,
    renouvellement_id: UUID,
    payload: RenouvellementUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.MODIFIER")),
):
    return await RenouvellementService.update(
        db, certification_id=certification_id, renouvellement_id=renouvellement_id,
        payload=payload, actor=actor, request=request
    )


@router.post("/certifications/{certification_id}/renewals/{renouvellement_id}/decision", response_model=RenouvellementResponse, tags=["Certifications - Renouvellements"])
async def decide_renewal(
    certification_id: UUID,
    renouvellement_id: UUID,
    payload: RenouvellementDecisionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CERTIFICATIONS.VERIFIER")),
):
    return await RenouvellementService.decide(
        db, certification_id=certification_id, renouvellement_id=renouvellement_id,
        payload=payload, actor=actor, request=request
    )
