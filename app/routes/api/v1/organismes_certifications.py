"""
Routes API du domaine Organismes / Certifications.

Le fichier expose le module principal et ses sous-modules en une seule
intégration. Les permissions restent contrôlées côté serveur.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
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
    OrganismeResponse,
    OrganismeUpdateRequest,
    OrganismeVerificationRequest,
    RenouvellementCreateRequest,
    RenouvellementDecisionRequest,
    RenouvellementResponse,
    RenouvellementUpdateRequest,
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
