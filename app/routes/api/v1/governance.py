"""
Routes API — Gouvernance / Qualité / Continuité.

Pages frontend concernées :
- `regles-codification.html`
- `#/amelioration-continue`
- `#/decisions`
- `#/publications`
- `rapports.html`
- `journal-audit.html`
- `#/archives`
- `#/sauvegardes`
- `#/incidents`

Le journal d'audit n'expose aucune route de mutation.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.governance import *
from app.services.auth_service import AuthContext
from app.services.governance_service import GovernanceService


governance_router = APIRouter(
    prefix="/governance",
    tags=["Gouvernance"],
)

quality_router = APIRouter(
    prefix="/quality",
    tags=["Qualité / Amélioration continue"],
)

decision_router = APIRouter(
    prefix="/decisions",
    tags=["Décisions institutionnelles"],
)

publication_router = APIRouter(
    prefix="/publications",
    tags=["Publications"],
)

report_router = APIRouter(
    prefix="/reports",
    tags=["Rapports générés"],
)

audit_router = APIRouter(
    prefix="/audit",
    tags=["Journal d'audit"],
)

archive_router = APIRouter(
    prefix="/archives",
    tags=["Archives"],
)

backup_router = APIRouter(
    prefix="/backups",
    tags=["Sauvegardes / Continuité"],
)

incident_router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)


# ============================================================
# DASHBOARD GOUVERNANCE
# ============================================================

@governance_router.get(
    "/dashboard",
    response_model=GovernanceDashboardResponse,
)
async def governance_dashboard(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("GOUVERNANCE.LIRE")),
):
    return await GovernanceService.dashboard(db)


# ============================================================
# RÈGLES MÉTIER
# ============================================================

@governance_router.get(
    "/rules",
    response_model=list[BusinessRuleResponse],
)
async def list_rules(
    logical_code: str | None = Query(default=None, max_length=200),
    famille: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("GOUVERNANCE.LIRE")),
):
    return await GovernanceService.list_rules(
        db,
        logical_code=logical_code,
        famille=famille,
        statut_filter=statut,
    )


@governance_router.get(
    "/rules/active/{logical_code}",
    response_model=BusinessRuleResponse,
)
async def active_rule(
    logical_code: str,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("GOUVERNANCE.LIRE")),
):
    return await GovernanceService.active_rule(db, logical_code)


@governance_router.post(
    "/rules",
    response_model=BusinessRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_rule(
    payload: BusinessRuleCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("GOUVERNANCE.ADMINISTRER_REGLES")
    ),
):
    return await GovernanceService.create_rule(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@governance_router.get(
    "/rules/{rule_id}",
    response_model=BusinessRuleResponse,
)
async def get_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("GOUVERNANCE.LIRE")),
):
    item = await GovernanceService.require_rule(db, rule_id)
    return GovernanceService.rule_response(item)


@governance_router.patch(
    "/rules/{rule_id}",
    response_model=BusinessRuleResponse,
)
async def update_rule(
    rule_id: UUID,
    payload: BusinessRuleUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("GOUVERNANCE.ADMINISTRER_REGLES")
    ),
):
    return await GovernanceService.update_rule(
        db,
        rule_id=rule_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@governance_router.post(
    "/rules/{rule_id}/clone",
    response_model=BusinessRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def clone_rule(
    rule_id: UUID,
    payload: BusinessRuleCloneRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("GOUVERNANCE.ADMINISTRER_REGLES")
    ),
):
    return await GovernanceService.clone_rule(
        db,
        rule_id=rule_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@governance_router.post(
    "/rules/{rule_id}/publish",
    response_model=BusinessRuleResponse,
)
async def publish_rule(
    rule_id: UUID,
    payload: BusinessRulePublishRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("GOUVERNANCE.ADMINISTRER_REGLES")
    ),
):
    return await GovernanceService.publish_rule(
        db,
        rule_id=rule_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@governance_router.post(
    "/rules/{rule_id}/retire",
    response_model=BusinessRuleResponse,
)
async def retire_rule(
    rule_id: UUID,
    payload: BusinessRuleRetireRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("GOUVERNANCE.ADMINISTRER_REGLES")
    ),
):
    return await GovernanceService.retire_rule(
        db,
        rule_id=rule_id,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# REVUES QUALITÉ
# ============================================================

@quality_router.get(
    "/reviews",
    response_model=QualityReviewListResponse,
)
async def list_quality_reviews(
    statut: str | None = Query(default=None, max_length=255),
    responsable_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("QUALITE.LIRE")),
):
    return await GovernanceService.list_reviews(
        db,
        statut=statut,
        responsable_id=responsable_id,
        limit=limit,
        offset=offset,
    )


@quality_router.post(
    "/reviews",
    response_model=QualityReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_quality_review(
    payload: QualityReviewCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("QUALITE.GERER")),
):
    return await GovernanceService.create_review(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@quality_router.get(
    "/reviews/{review_id}",
    response_model=QualityReviewResponse,
)
async def get_quality_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("QUALITE.LIRE")),
):
    item = await GovernanceService.require_review(db, review_id)
    return await GovernanceService.review_response(db, item)


@quality_router.patch(
    "/reviews/{review_id}",
    response_model=QualityReviewResponse,
)
async def update_quality_review(
    review_id: UUID,
    payload: QualityReviewUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("QUALITE.GERER")),
):
    return await GovernanceService.update_review(
        db,
        review_id=review_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@quality_router.post(
    "/reviews/{review_id}/validate",
    response_model=QualityReviewResponse,
)
async def validate_quality_review(
    review_id: UUID,
    payload: QualityReviewValidateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("QUALITE.VALIDER")),
):
    return await GovernanceService.validate_review(
        db,
        review_id=review_id,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# PLANS D'ACTION
# ============================================================

@quality_router.get(
    "/action-plans",
    response_model=ActionPlanListResponse,
)
async def list_action_plans(
    review_id: UUID | None = Query(default=None),
    responsable_id: UUID | None = Query(default=None),
    statut: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("QUALITE.LIRE")),
):
    return await GovernanceService.list_action_plans(
        db,
        review_id=review_id,
        responsable_id=responsable_id,
        statut=statut,
        limit=limit,
        offset=offset,
    )


@quality_router.post(
    "/action-plans",
    response_model=ActionPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_action_plan(
    payload: ActionPlanCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("QUALITE.GERER")),
):
    return await GovernanceService.create_action_plan(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@quality_router.get(
    "/action-plans/{plan_id}",
    response_model=ActionPlanResponse,
)
async def get_action_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("QUALITE.LIRE")),
):
    item = await GovernanceService.require_action_plan(db, plan_id)
    return GovernanceService.plan_response(item)


@quality_router.patch(
    "/action-plans/{plan_id}",
    response_model=ActionPlanResponse,
)
async def update_action_plan(
    plan_id: UUID,
    payload: ActionPlanUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("QUALITE.GERER")),
):
    return await GovernanceService.update_action_plan(
        db,
        plan_id=plan_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@quality_router.post(
    "/action-plans/{plan_id}/progress",
    response_model=ActionPlanResponse,
)
async def progress_action_plan(
    plan_id: UUID,
    payload: ActionPlanProgressRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("QUALITE.GERER")),
):
    return await GovernanceService.progress_action_plan(
        db,
        plan_id=plan_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@quality_router.post(
    "/action-plans/{plan_id}/close",
    response_model=ActionPlanResponse,
)
async def close_action_plan(
    plan_id: UUID,
    payload: ActionPlanCloseRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("QUALITE.VALIDER")),
):
    return await GovernanceService.close_action_plan(
        db,
        plan_id=plan_id,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# DÉCISIONS INSTITUTIONNELLES
# ============================================================

@decision_router.get(
    "",
    response_model=InstitutionalDecisionListResponse,
)
async def list_decisions(
    ressource_type: str | None = Query(default=None, max_length=255),
    ressource_id: UUID | None = Query(default=None),
    statut: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("DECISIONS.LIRE")),
):
    return await GovernanceService.list_decisions(
        db,
        ressource_type=ressource_type,
        ressource_id=ressource_id,
        statut=statut,
        limit=limit,
        offset=offset,
    )


@decision_router.post(
    "",
    response_model=InstitutionalDecisionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_decision(
    payload: InstitutionalDecisionCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("DECISIONS.PREPARER")),
):
    return await GovernanceService.create_decision(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@decision_router.get(
    "/{decision_id}",
    response_model=InstitutionalDecisionResponse,
)
async def get_decision(
    decision_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("DECISIONS.LIRE")),
):
    item = await GovernanceService.require_decision(db, decision_id)
    return GovernanceService.decision_response(item)


@decision_router.patch(
    "/{decision_id}",
    response_model=InstitutionalDecisionResponse,
)
async def update_decision(
    decision_id: UUID,
    payload: InstitutionalDecisionUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("DECISIONS.PREPARER")),
):
    return await GovernanceService.update_decision(
        db,
        decision_id=decision_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@decision_router.post(
    "/{decision_id}/submit",
    response_model=InstitutionalDecisionResponse,
)
async def submit_decision(
    decision_id: UUID,
    payload: InstitutionalDecisionSubmitRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("DECISIONS.PREPARER")),
):
    return await GovernanceService.submit_decision(
        db,
        decision_id=decision_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@decision_router.post(
    "/{decision_id}/pronounce",
    response_model=InstitutionalDecisionResponse,
)
async def pronounce_decision(
    decision_id: UUID,
    payload: InstitutionalDecisionPronounceRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("DECISIONS.PRONONCER")),
):
    return await GovernanceService.pronounce_decision(
        db,
        decision_id=decision_id,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# PUBLICATIONS
# ============================================================

@publication_router.get(
    "",
    response_model=PublicationListResponse,
)
async def list_publications(
    statut: str | None = Query(default=None, max_length=255),
    niveau_confidentialite: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("PUBLICATIONS.LIRE")),
):
    return await GovernanceService.list_publications(
        db,
        statut=statut,
        niveau_confidentialite=niveau_confidentialite,
        limit=limit,
        offset=offset,
    )


@publication_router.post(
    "",
    response_model=PublicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_publication(
    payload: PublicationCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("PUBLICATIONS.DEMANDER")),
):
    return await GovernanceService.create_publication(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@publication_router.get(
    "/{publication_id}",
    response_model=PublicationResponse,
)
async def get_publication(
    publication_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("PUBLICATIONS.LIRE")),
):
    item = await GovernanceService.require_publication(db, publication_id)
    return GovernanceService.publication_response(item)


@publication_router.post(
    "/{publication_id}/submit",
    response_model=PublicationResponse,
)
async def submit_publication(
    publication_id: UUID,
    payload: PublicationSubmitRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("PUBLICATIONS.DEMANDER")),
):
    return await GovernanceService.submit_publication(
        db,
        publication_id=publication_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@publication_router.post(
    "/{publication_id}/approve",
    response_model=PublicationResponse,
)
async def approve_publication(
    publication_id: UUID,
    payload: PublicationApprovalRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("PUBLICATIONS.APPROUVER")),
):
    return await GovernanceService.approve_publication(
        db,
        publication_id=publication_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@publication_router.post(
    "/{publication_id}/publish",
    response_model=PublicationResponse,
)
async def publish_publication(
    publication_id: UUID,
    payload: PublicationPublishRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("PUBLICATIONS.PUBLIER")),
):
    return await GovernanceService.publish_publication(
        db,
        publication_id=publication_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@publication_router.post(
    "/{publication_id}/retire",
    response_model=PublicationResponse,
)
async def retire_publication(
    publication_id: UUID,
    payload: PublicationRetireRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("PUBLICATIONS.PUBLIER")),
):
    return await GovernanceService.retire_publication(
        db,
        publication_id=publication_id,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# RAPPORTS GÉNÉRÉS
# ============================================================

@report_router.get(
    "",
    response_model=GeneratedReportListResponse,
)
async def list_reports(
    categorie: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    demandeur_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("RAPPORTS.LIRE")),
):
    return await GovernanceService.list_reports(
        db,
        categorie=categorie,
        statut=statut,
        demandeur_id=demandeur_id,
        limit=limit,
        offset=offset,
    )


@report_router.post(
    "",
    response_model=GeneratedReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_report(
    payload: ReportRequestCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("RAPPORTS.DEMANDER")),
):
    return await GovernanceService.create_report_request(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@report_router.get(
    "/{report_id}",
    response_model=GeneratedReportResponse,
)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("RAPPORTS.LIRE")),
):
    item = await GovernanceService.require_report(db, report_id)
    return GovernanceService.report_response(item)


@report_router.post(
    "/{report_id}/start",
    response_model=GeneratedReportResponse,
)
async def start_report(
    report_id: UUID,
    payload: ReportStartRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("RAPPORTS.GENERER")),
):
    return await GovernanceService.start_report(
        db,
        report_id=report_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@report_router.post(
    "/{report_id}/complete",
    response_model=GeneratedReportResponse,
)
async def complete_report(
    report_id: UUID,
    payload: ReportCompleteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("RAPPORTS.GENERER")),
):
    return await GovernanceService.complete_report(
        db,
        report_id=report_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@report_router.post(
    "/{report_id}/fail",
    response_model=GeneratedReportResponse,
)
async def fail_report(
    report_id: UUID,
    payload: ReportFailRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("RAPPORTS.GENERER")),
):
    return await GovernanceService.fail_report(
        db,
        report_id=report_id,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# JOURNAL D'AUDIT — STRICTEMENT LECTURE
# ============================================================

@audit_router.get(
    "/events",
    response_model=AuditEventListResponse,
)
async def list_audit_events(
    utilisateur_id: UUID | None = Query(default=None),
    action: str | None = Query(default=None, max_length=255),
    categorie: str | None = Query(default=None, max_length=255),
    ressource_type: str | None = Query(default=None, max_length=255),
    ressource_id: UUID | None = Query(default=None),
    resultat: str | None = Query(default=None, max_length=255),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("AUDIT.LIRE")),
):
    return await GovernanceService.list_audit_events(
        db,
        utilisateur_id=utilisateur_id,
        action=action,
        categorie=categorie,
        ressource_type=ressource_type,
        ressource_id=ressource_id,
        resultat=resultat,
        start_at=start_at,
        end_at=end_at,
        limit=limit,
        offset=offset,
    )


@audit_router.get(
    "/events/{event_id}",
    response_model=AuditEventResponse,
)
async def get_audit_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("AUDIT.LIRE")),
):
    return await GovernanceService.get_audit_event(db, event_id)


# ============================================================
# ARCHIVES
# ============================================================

@archive_router.get(
    "",
    response_model=ArchiveListResponse,
)
async def list_archives(
    ressource_type: str | None = Query(default=None, max_length=255),
    ressource_id: UUID | None = Query(default=None),
    statut: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ARCHIVES.LIRE")),
):
    return await GovernanceService.list_archives(
        db,
        ressource_type=ressource_type,
        ressource_id=ressource_id,
        statut=statut,
        limit=limit,
        offset=offset,
    )


@archive_router.post(
    "",
    response_model=ArchiveResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_archive(
    payload: ArchiveCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ARCHIVES.CREER")),
):
    return await GovernanceService.create_archive(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@archive_router.get(
    "/{archive_id}",
    response_model=ArchiveResponse,
)
async def get_archive(
    archive_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ARCHIVES.LIRE")),
):
    item = await GovernanceService.require_archive(db, archive_id)
    return GovernanceService.archive_response(item)


# ============================================================
# SAUVEGARDES
# ============================================================

@backup_router.get(
    "",
    response_model=BackupListResponse,
)
async def list_backups(
    type_enregistrement: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    parent_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SAUVEGARDES.LIRE")),
):
    return await GovernanceService.list_backups(
        db,
        type_enregistrement=type_enregistrement,
        statut=statut,
        parent_id=parent_id,
        limit=limit,
        offset=offset,
    )


@backup_router.post(
    "/policies",
    response_model=BackupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_backup_policy(
    payload: BackupPolicyCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SAUVEGARDES.GERER")),
):
    return await GovernanceService.create_backup_policy(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@backup_router.patch(
    "/policies/{policy_id}",
    response_model=BackupResponse,
)
async def update_backup_policy(
    policy_id: UUID,
    payload: BackupPolicyUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SAUVEGARDES.GERER")),
):
    return await GovernanceService.update_backup_policy(
        db,
        backup_id=policy_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@backup_router.post(
    "/policies/{policy_id}/runs",
    response_model=BackupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_backup_run(
    policy_id: UUID,
    payload: BackupRunCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SAUVEGARDES.GERER")),
):
    return await GovernanceService.create_backup_run(
        db,
        policy_id=policy_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@backup_router.get(
    "/{backup_id}",
    response_model=BackupResponse,
)
async def get_backup(
    backup_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SAUVEGARDES.LIRE")),
):
    item = await GovernanceService.require_backup(db, backup_id)
    return GovernanceService.backup_response(item)


@backup_router.post(
    "/{backup_id}/complete",
    response_model=BackupResponse,
)
async def complete_backup(
    backup_id: UUID,
    payload: BackupRunCompleteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SAUVEGARDES.GERER")),
):
    return await GovernanceService.complete_backup_run(
        db,
        backup_id=backup_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@backup_router.post(
    "/{backup_id}/fail",
    response_model=BackupResponse,
)
async def fail_backup(
    backup_id: UUID,
    payload: BackupRunFailRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SAUVEGARDES.GERER")),
):
    return await GovernanceService.fail_backup_run(
        db,
        backup_id=backup_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@backup_router.post(
    "/{backup_id}/restore-tests",
    response_model=BackupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_restore_test(
    backup_id: UUID,
    payload: RestoreTestCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SAUVEGARDES.GERER")),
):
    return await GovernanceService.create_restore_test(
        db,
        backup_id=backup_id,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# INCIDENTS
# ============================================================

@incident_router.get(
    "",
    response_model=IncidentListResponse,
)
async def list_incidents(
    categorie: str | None = Query(default=None, max_length=255),
    gravite: str | None = Query(default=None, max_length=255),
    responsable_id: UUID | None = Query(default=None),
    statut: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INCIDENTS.LIRE")),
):
    return await GovernanceService.list_incidents(
        db,
        categorie=categorie,
        gravite=gravite,
        responsable_id=responsable_id,
        statut=statut,
        limit=limit,
        offset=offset,
    )


@incident_router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_incident(
    payload: IncidentCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INCIDENTS.DECLARER")),
):
    return await GovernanceService.create_incident(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@incident_router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
)
async def get_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INCIDENTS.LIRE")),
):
    item = await GovernanceService.require_incident(db, incident_id)
    return GovernanceService.incident_response(item)


@incident_router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
)
async def update_incident(
    incident_id: UUID,
    payload: IncidentUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INCIDENTS.GERER")),
):
    return await GovernanceService.update_incident(
        db,
        incident_id=incident_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@incident_router.post(
    "/{incident_id}/assign",
    response_model=IncidentResponse,
)
async def assign_incident(
    incident_id: UUID,
    payload: IncidentAssignRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INCIDENTS.GERER")),
):
    return await GovernanceService.assign_incident(
        db,
        incident_id=incident_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@incident_router.post(
    "/{incident_id}/resolve",
    response_model=IncidentResponse,
)
async def resolve_incident(
    incident_id: UUID,
    payload: IncidentResolveRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INCIDENTS.GERER")),
):
    return await GovernanceService.resolve_incident(
        db,
        incident_id=incident_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@incident_router.post(
    "/{incident_id}/close",
    response_model=IncidentResponse,
)
async def close_incident(
    incident_id: UUID,
    payload: IncidentCloseRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INCIDENTS.CLOTURER")),
):
    return await GovernanceService.close_incident(
        db,
        incident_id=incident_id,
        payload=payload,
        actor=actor,
        request=request,
    )
