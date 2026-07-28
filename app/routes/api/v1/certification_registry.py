from __future__ import annotations

import csv
import io
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.certification_registry import (
    CertificationFiltersResponse,
    CertificationRegistryItem,
    CertificationRegistryResponse,
)
from app.services.auth_service import AuthContext
from app.services.certification_registry_service import (
    CertificationRegistryService,
)


router = APIRouter(
    prefix="/certifications",
    tags=["Certifications - Registre"],
)


@router.get(
    "/filters",
    response_model=CertificationFiltersResponse,
)
async def certification_filters(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("CERTIFICATIONS.LIRE")
    ),
):
    return await CertificationRegistryService.filters(db)


@router.get(
    "/registry",
    response_model=CertificationRegistryResponse,
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




def write_registry_csv(data: CertificationRegistryResponse) -> str:
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
                "OUI" if item.authenticite_verifiee else "NON",
                "OUI" if item.certification_strategique else "NON",
                "OUI" if item.renewal_open else "NON",
            ]
        )

    return "\ufeff" + buffer.getvalue()


@router.get("/export")
async def export_certifications(
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
        "entreprise_id": str(entreprise_id) if entreprise_id else None,
        "organisme_id": str(organisme_id) if organisme_id else None,
        "norme_id": str(norme_id) if norme_id else None,
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
        content=write_registry_csv(data),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                'attachment; filename="hauqe-certifications.csv"'
        },
    )


@router.get(
    "/{certification_id}/context",
    response_model=CertificationRegistryItem,
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


@router.get("/{certification_id}/export")
async def export_certification(
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
        content=write_registry_csv(data),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                "attachment; "
                f'filename="certification-{certification_id}.csv"'
            )
        },
    )
