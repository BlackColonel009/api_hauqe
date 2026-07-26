"""
Routes API — Échéances / Alertes / Notifications / Cellule de Veille.

PAGES FRONTEND
--------------
- `echeances.html` / `#/echeances`
- `alertes.html` / `#/alertes`
- cloche globale de notifications
- espace CVC `#/veille`

Le scan quotidien est également appelable par une tâche serveur.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.veille import (
    AlertAssignRequest,
    AlertCreateRequest,
    AlertListResponse,
    AlertNotifyRequest,
    AlertResolveRequest,
    AlertResponse,
    AlertUpdateRequest,
    DailyScanResponse,
    DeadlineCloseRequest,
    DeadlineCreateRequest,
    DeadlineListResponse,
    DeadlineResponse,
    DeadlineUpdateRequest,
    FollowUpCreateRequest,
    FollowUpResponse,
    FollowUpResponseRequest,
    FollowUpUpdateRequest,
    NotificationListResponse,
    NotificationResponse,
    NotificationResultRequest,
    WatchCaseCloseRequest,
    WatchCaseCreateRequest,
    WatchCaseListResponse,
    WatchCaseResponse,
    WatchCaseUpdateRequest,
    WatchDashboardResponse,
    WatchReportGenerateRequest,
    WatchReportListResponse,
    WatchReportResponse,
    WatchReportValidateRequest,
)
from app.services.auth_service import AuthContext
from app.services.veille_service import WatchService


deadline_router = APIRouter(
    prefix="/echeances",
    tags=["Échéances"],
)

alert_router = APIRouter(
    prefix="/alertes",
    tags=["Alertes"],
)

notification_router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)

watch_router = APIRouter(
    prefix="/veille",
    tags=["Cellule de veille"],
)


# ============================================================
# ÉCHÉANCES
# ============================================================

@deadline_router.get("", response_model=DeadlineListResponse)
async def list_deadlines(
    ressource_type: str | None = Query(default=None, max_length=255),
    ressource_id: UUID | None = Query(default=None),
    type_echeance: str | None = Query(default=None, max_length=255),
    responsable_id: UUID | None = Query(default=None),
    statut: str | None = Query(default=None, max_length=255),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    overdue_only: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ECHEANCES.LIRE")),
):
    return await WatchService.list_deadlines(
        db,
        ressource_type=ressource_type,
        ressource_id=ressource_id,
        type_echeance=type_echeance,
        responsable_id=responsable_id,
        statut=statut,
        start_date=start_date,
        end_date=end_date,
        overdue_only=overdue_only,
        limit=limit,
        offset=offset,
    )


@deadline_router.post(
    "",
    response_model=DeadlineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_deadline(
    payload: DeadlineCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ECHEANCES.GERER")),
):
    return await WatchService.create_deadline(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@deadline_router.get(
    "/{deadline_id}",
    response_model=DeadlineResponse,
)
async def get_deadline(
    deadline_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ECHEANCES.LIRE")),
):
    item = await WatchService.require_deadline(db, deadline_id)
    return await WatchService.deadline_response(db, item)


@deadline_router.patch(
    "/{deadline_id}",
    response_model=DeadlineResponse,
)
async def update_deadline(
    deadline_id: UUID,
    payload: DeadlineUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ECHEANCES.GERER")),
):
    return await WatchService.update_deadline(
        db,
        deadline_id=deadline_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@deadline_router.post(
    "/{deadline_id}/complete",
    response_model=DeadlineResponse,
)
async def complete_deadline(
    deadline_id: UUID,
    payload: DeadlineCloseRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ECHEANCES.GERER")),
):
    return await WatchService.close_deadline(
        db,
        deadline_id=deadline_id,
        target_status="TERMINEE",
        payload=payload,
        actor=actor,
        request=request,
    )


@deadline_router.post(
    "/{deadline_id}/cancel",
    response_model=DeadlineResponse,
)
async def cancel_deadline(
    deadline_id: UUID,
    payload: DeadlineCloseRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ECHEANCES.GERER")),
):
    return await WatchService.close_deadline(
        db,
        deadline_id=deadline_id,
        target_status="ANNULEE",
        payload=payload,
        actor=actor,
        request=request,
    )


@deadline_router.get(
    "/{deadline_id}/alertes",
    response_model=list[AlertResponse],
)
async def deadline_alerts(
    deadline_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ALERTES.LIRE")),
):
    await WatchService.require_deadline(db, deadline_id)
    from app.repositories.veille_repository import WatchRepository
    rows = await WatchRepository.list_deadline_alerts(db, deadline_id)
    return [
        await WatchService.alert_response(db, row)
        for row in rows
    ]


# ============================================================
# ALERTES
# ============================================================

@alert_router.get("", response_model=AlertListResponse)
async def list_alerts(
    type_alerte: str | None = Query(default=None, max_length=255),
    niveau: int | None = Query(default=None, ge=1, le=4),
    responsable_id: UUID | None = Query(default=None),
    statut: str | None = Query(default=None, max_length=255),
    ressource_type: str | None = Query(default=None, max_length=255),
    ressource_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ALERTES.LIRE")),
):
    return await WatchService.list_alerts(
        db,
        type_alerte=type_alerte,
        niveau=niveau,
        responsable_id=responsable_id,
        statut=statut,
        ressource_type=ressource_type,
        ressource_id=ressource_id,
        limit=limit,
        offset=offset,
    )


@alert_router.post(
    "",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_special_alert(
    payload: AlertCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ALERTES.CREER")),
):
    return await WatchService.create_alert(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@alert_router.get(
    "/{alert_id}",
    response_model=AlertResponse,
)
async def get_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ALERTES.LIRE")),
):
    item = await WatchService.require_alert(db, alert_id)
    return await WatchService.alert_response(db, item)


@alert_router.patch(
    "/{alert_id}",
    response_model=AlertResponse,
)
async def update_alert(
    alert_id: UUID,
    payload: AlertUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ALERTES.GERER")),
):
    return await WatchService.update_alert(
        db,
        alert_id=alert_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@alert_router.post(
    "/{alert_id}/assign",
    response_model=AlertResponse,
)
async def assign_alert(
    alert_id: UUID,
    payload: AlertAssignRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ALERTES.AFFECTER")),
):
    return await WatchService.assign_alert(
        db,
        alert_id=alert_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@alert_router.post(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
)
async def resolve_alert(
    alert_id: UUID,
    payload: AlertResolveRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ALERTES.RESOUDRE")),
):
    return await WatchService.resolve_alert(
        db,
        alert_id=alert_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@alert_router.post(
    "/{alert_id}/notifications",
    response_model=list[NotificationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def notify_alert(
    alert_id: UUID,
    payload: AlertNotifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("NOTIFICATIONS.CREER")),
):
    return await WatchService.queue_alert_notifications(
        db,
        alert_id=alert_id,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# NOTIFICATIONS / CLOCHE
# ============================================================

@notification_router.get("", response_model=NotificationListResponse)
async def my_notifications(
    statut: str | None = Query(default=None, max_length=255),
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("NOTIFICATIONS.LIRE")),
):
    return await WatchService.list_my_notifications(
        db,
        actor=actor,
        statut_filter=statut,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )


@notification_router.get("/unread-count")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("NOTIFICATIONS.LIRE")),
):
    from app.repositories.veille_repository import WatchRepository
    return {
        "unread_count": await WatchRepository.unread_notifications_for_user(
            db,
            actor.user.id,
        )
    }


@notification_router.post("/read-all")
async def read_all(
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("NOTIFICATIONS.LIRE")),
):
    count = await WatchService.mark_all_notifications_read(
        db,
        actor=actor,
        request=request,
    )
    return {"marked_read": count}


@notification_router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
async def read_notification(
    notification_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("NOTIFICATIONS.LIRE")),
):
    return await WatchService.mark_notification_read(
        db,
        notification_id=notification_id,
        actor=actor,
        request=request,
    )


@notification_router.post(
    "/{notification_id}/retry",
    response_model=NotificationResponse,
)
async def retry_notification(
    notification_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("NOTIFICATIONS.TRANSPORT")
    ),
):
    return await WatchService.retry_notification(
        db,
        notification_id=notification_id,
        actor=actor,
        request=request,
    )


@notification_router.post(
    "/{notification_id}/delivery-result",
    response_model=NotificationResponse,
)
async def delivery_result(
    notification_id: UUID,
    payload: NotificationResultRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("NOTIFICATIONS.TRANSPORT")
    ),
):
    return await WatchService.record_notification_delivery(
        db,
        notification_id=notification_id,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# DASHBOARD / SCAN CVC
# ============================================================

@watch_router.get(
    "/dashboard",
    response_model=WatchDashboardResponse,
)
async def watch_dashboard(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.LIRE")),
):
    return await WatchService.dashboard(db, actor)


@watch_router.post(
    "/scans/daily",
    response_model=DailyScanResponse,
)
async def run_daily_scan(
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.SCANNER")),
):
    return await WatchService.run_daily_scan(
        db,
        actor=actor,
        request=request,
    )


# ============================================================
# DOSSIERS DE VEILLE
# ============================================================

@watch_router.get(
    "/dossiers",
    response_model=WatchCaseListResponse,
)
async def list_watch_cases(
    certification_id: UUID | None = Query(default=None),
    responsable_id: UUID | None = Query(default=None),
    statut: str | None = Query(default=None, max_length=255),
    priorite: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.LIRE")),
):
    return await WatchService.list_watch_cases(
        db,
        certification_id=certification_id,
        responsable_id=responsable_id,
        statut=statut,
        priorite=priorite,
        limit=limit,
        offset=offset,
    )


@watch_router.post(
    "/dossiers",
    response_model=WatchCaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_watch_case(
    payload: WatchCaseCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.GERER")),
):
    return await WatchService.create_watch_case(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@watch_router.get(
    "/dossiers/{case_id}",
    response_model=WatchCaseResponse,
)
async def get_watch_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.LIRE")),
):
    item = await WatchService.require_watch_case(db, case_id)
    return await WatchService.watch_case_response(db, item)


@watch_router.patch(
    "/dossiers/{case_id}",
    response_model=WatchCaseResponse,
)
async def update_watch_case(
    case_id: UUID,
    payload: WatchCaseUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.GERER")),
):
    return await WatchService.update_watch_case(
        db,
        case_id=case_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@watch_router.post(
    "/dossiers/{case_id}/close",
    response_model=WatchCaseResponse,
)
async def close_watch_case(
    case_id: UUID,
    payload: WatchCaseCloseRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.CLOTURER")),
):
    return await WatchService.close_watch_case(
        db,
        case_id=case_id,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# RELANCES
# ============================================================

@watch_router.get(
    "/dossiers/{case_id}/relances",
    response_model=list[FollowUpResponse],
)
async def list_followups(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.LIRE")),
):
    return await WatchService.list_followups(db, case_id)


@watch_router.post(
    "/dossiers/{case_id}/relances",
    response_model=FollowUpResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_followup(
    case_id: UUID,
    payload: FollowUpCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.RELANCER")),
):
    return await WatchService.create_followup(
        db,
        case_id=case_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@watch_router.patch(
    "/dossiers/{case_id}/relances/{followup_id}",
    response_model=FollowUpResponse,
)
async def update_followup(
    case_id: UUID,
    followup_id: UUID,
    payload: FollowUpUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.RELANCER")),
):
    return await WatchService.update_followup(
        db,
        case_id=case_id,
        followup_id=followup_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@watch_router.post(
    "/dossiers/{case_id}/relances/{followup_id}/response",
    response_model=FollowUpResponse,
)
async def followup_response(
    case_id: UUID,
    followup_id: UUID,
    payload: FollowUpResponseRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.RELANCER")),
):
    return await WatchService.record_followup_response(
        db,
        case_id=case_id,
        followup_id=followup_id,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# RAPPORTS DE VEILLE
# ============================================================

@watch_router.get(
    "/rapports",
    response_model=WatchReportListResponse,
)
async def list_reports(
    type_rapport: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.LIRE")),
):
    return await WatchService.list_reports(
        db,
        type_rapport=type_rapport,
        statut_filter=statut,
        limit=limit,
        offset=offset,
    )


# Route statique avant /rapports/{report_id}.
@watch_router.post(
    "/rapports/generate",
    response_model=WatchReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_report(
    payload: WatchReportGenerateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.RAPPORTER")),
):
    return await WatchService.generate_report(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@watch_router.get(
    "/rapports/{report_id}",
    response_model=WatchReportResponse,
)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.LIRE")),
):
    item = await WatchService.require_watch_report(db, report_id)
    from app.services.veille_service import report_response
    return report_response(item)


@watch_router.post(
    "/rapports/{report_id}/validate",
    response_model=WatchReportResponse,
)
async def validate_report(
    report_id: UUID,
    payload: WatchReportValidateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.VALIDER_RAPPORT")),
):
    return await WatchService.validate_report(
        db,
        report_id=report_id,
        payload=payload,
        actor=actor,
        request=request,
    )
