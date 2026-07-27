"""
Routes API — Pilotage / Tableaux de bord / Baromètre / Public.

ROUTES INTERNES
---------------
- `/api/v1/dashboards/operational`
- `/api/v1/dashboards/tactical`
- `/api/v1/dashboards/strategic`
- `/api/v1/dashboards/annual`
- `/api/v1/barometer`

ROUTE PUBLIQUE
--------------
- `/api/v1/public/indicators`

La route publique n'exige pas de token, mais le service refuse toute réponse
si aucune règle + publication institutionnelle valide ne l'autorise.
"""

from __future__ import annotations

from datetime import date
import csv
import io
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.dashboard import (
    AnnualDashboardResponse,
    BarometerResponse,
    DashboardFiltersResponse,
    IndicatorDefinitionsResponse,
    OperationalDashboardResponse,
    PublicIndicatorsResponse,
    StrategicDashboardResponse,
    TacticalDashboardResponse,
)
from app.services.auth_service import AuthContext
from app.services.dashboard_service import DashboardService


dashboard_router = APIRouter(
    prefix="/dashboards",
    tags=["Pilotage / Tableaux de bord"],
)

barometer_router = APIRouter(
    prefix="/barometer",
    tags=["Baromètre national"],
)

public_dashboard_router = APIRouter(
    prefix="/public",
    tags=["Données publiques agrégées"],
)


# ============================================================
# MÉTADONNÉES PARTAGÉES
# ============================================================

@dashboard_router.get(
    "/filters",
    response_model=DashboardFiltersResponse,
)
async def dashboard_filters(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("DASHBOARDS.LIRE_REFERENTIELS")
    ),
):
    """
    Alimente les filtres région/secteur/norme/organisme du frontend.
    """
    return await DashboardService.filters(db)


@dashboard_router.get(
    "/indicator-definitions",
    response_model=IndicatorDefinitionsResponse,
)
async def indicator_definitions(
    actor: AuthContext = Depends(
        require_permission("DASHBOARDS.LIRE_REFERENTIELS")
    ),
):
    """
    Définitions fonctionnelles affichables dans les infobulles du frontend.
    """
    return DashboardService.definitions()


# ============================================================
# OPÉRATIONNEL
# ============================================================

@dashboard_router.get(
    "/operational/export",
)
async def operational_dashboard_export(
    days: int = Query(default=7, ge=1, le=90),
    zone_id: UUID | None = Query(default=None),
    sector: str | None = Query(default=None, max_length=255),
    norm_id: UUID | None = Query(default=None),
    organisme_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("DASHBOARDS.OPERATIONNEL")
    ),
):
    """
    Export CSV du même snapshot que le Dashboard opérationnel.

    Les filtres sont exactement ceux de `/operational`.
    Aucun chiffre n'est recalculé dans le frontend.
    """
    dashboard = await DashboardService.operational(
        db,
        days=days,
        zone_id=zone_id,
        sector=sector,
        norm_id=norm_id,
        organisme_id=organisme_id,
    )

    buffer = io.StringIO()
    writer = csv.writer(
        buffer,
        delimiter=";",
        quoting=csv.QUOTE_MINIMAL,
    )

    writer.writerow(
        ["HAUQE Certif", "Dashboard opérationnel"]
    )
    writer.writerow(
        ["Période", dashboard.period.label]
    )
    writer.writerow(
        ["Généré le", dashboard.generated_at.isoformat()]
    )
    writer.writerow([])

    writer.writerow(
        ["INDICATEURS", "Valeur", "Unité"]
    )
    for item in dashboard.kpis:
        writer.writerow(
            [item.label, item.value, item.unit or ""]
        )

    writer.writerow([])
    writer.writerow(
        ["CERTIFICATIONS À ÉCHÉANCE", "Entreprise", "Expiration", "Jours restants"]
    )
    for item in dashboard.expiring_certifications:
        writer.writerow(
            [
                item.certification_code or "",
                item.enterprise_name,
                item.expiration_date.isoformat(),
                item.days_remaining,
            ]
        )

    writer.writerow([])
    writer.writerow(
        ["ACTIONS PRIORITAIRES", "Type", "Échéance"]
    )
    for item in dashboard.priority_actions:
        writer.writerow(
            [
                item.title,
                item.type,
                item.due_date.isoformat()
                if item.due_date
                else "",
            ]
        )

    content = "\ufeff" + buffer.getvalue()

    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                "attachment; "
                'filename="hauqe-dashboard-operationnel.csv"'
            )
        },
    )


@dashboard_router.get(
    "/operational",
    response_model=OperationalDashboardResponse,
)
async def operational_dashboard(
    days: int = Query(default=7, ge=1, le=90),
    zone_id: UUID | None = Query(default=None),
    sector: str | None = Query(default=None, max_length=255),
    norm_id: UUID | None = Query(default=None),
    organisme_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("DASHBOARDS.OPERATIONNEL")
    ),
):
    return await DashboardService.operational(
        db,
        days=days,
        zone_id=zone_id,
        sector=sector,
        norm_id=norm_id,
        organisme_id=organisme_id,
    )


# ============================================================
# TACTIQUE MENSUEL
# ============================================================

@dashboard_router.get(
    "/tactical",
    response_model=TacticalDashboardResponse,
)
async def tactical_dashboard(
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("DASHBOARDS.TACTIQUE")
    ),
):
    return await DashboardService.tactical(
        db,
        year=year,
        month=month,
    )


# ============================================================
# STRATÉGIQUE TRIMESTRIEL
# ============================================================

@dashboard_router.get(
    "/strategic",
    response_model=StrategicDashboardResponse,
)
async def strategic_dashboard(
    year: int = Query(ge=2000, le=2100),
    quarter: int = Query(ge=1, le=4),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("DASHBOARDS.STRATEGIQUE")
    ),
):
    return await DashboardService.strategic(
        db,
        year=year,
        quarter=quarter,
    )


# ============================================================
# ANNUEL
# ============================================================

@dashboard_router.get(
    "/annual",
    response_model=AnnualDashboardResponse,
)
async def annual_dashboard(
    year: int = Query(ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("DASHBOARDS.ANNUEL")
    ),
):
    return await DashboardService.annual(
        db,
        year=year,
    )


# ============================================================
# BAROMÈTRE NATIONAL
# ============================================================

@barometer_router.get(
    "",
    response_model=BarometerResponse,
)
async def national_barometer(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("BAROMETRE.LIRE")
    ),
):
    today = date.today()
    start = start_date or date(today.year, 1, 1)
    end = end_date or today

    return await DashboardService.barometer(
        db,
        start_date=start,
        end_date=end,
    )


# ============================================================
# TABLEAU PUBLIC AGRÉGÉ
# ============================================================

@public_dashboard_router.get(
    "/indicators",
    response_model=PublicIndicatorsResponse,
)
async def public_indicators(
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint volontairement anonyme.

    La couche service vérifie néanmoins :
    - règle publiée ;
    - allowlist d'indicateurs ;
    - période publiée ;
    - publication institutionnelle PUBLIEE.

    Cache court uniquement : une nouvelle publication doit devenir visible
    rapidement.
    """
    response.headers["Cache-Control"] = "public, max-age=300"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return await DashboardService.public_indicators(db)
