from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.repositories.certification_registry_repository import (
    CertificationRegistryRepository,
)
from app.schemas.certification_registry import (
    CertificationFiltersResponse,
    CertificationRegistryItem,
    CertificationRegistryResponse,
    CertificationRegistrySummary,
)
from app.services.auth_service import AuthContext


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


class CertificationRegistryService:
    @staticmethod
    def build_item(row) -> CertificationRegistryItem:
        certification = row[0]

        days_remaining = None
        if certification.date_expiration:
            days_remaining = (
                certification.date_expiration - date.today()
            ).days

        return CertificationRegistryItem(
            id=certification.id,
            identifiant_national=certification.identifiant_national,
            numero_certificat=certification.numero_certificat,
            entreprise_id=certification.entreprise_id,
            entreprise_name=(
                row.entreprise_name
                or row.entreprise_trade_name
                or "Entreprise"
            ),
            organisme_id=certification.organisme_id,
            organisme_name=row.organisme_name or "Organisme",
            organisme_sigle=row.organisme_sigle,
            norme_id=certification.norme_id,
            norme_code=row.norme_code,
            norme_name=row.norme_name,
            norme_version=row.norme_version,
            accreditation_id=certification.accreditation_id,
            accrediteur=row.accrediteur,
            portee=certification.portee,
            date_obtention=certification.date_obtention,
            date_effet=certification.date_effet,
            date_expiration=certification.date_expiration,
            days_remaining=days_remaining,
            statut=certification.statut,
            authenticite_verifiee=(
                certification.authenticite_verifiee
            ),
            certification_strategique=(
                certification.certification_strategique
            ),
            document_count=int(row.document_count or 0),
            renewal_open=bool(row.renewal_open_count or 0),
        )

    @staticmethod
    async def filters(
        db: AsyncSession,
    ) -> CertificationFiltersResponse:
        payload = await CertificationRegistryRepository.filters(db)
        return CertificationFiltersResponse(**payload)

    @staticmethod
    async def registry(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
        entreprise_id: UUID | None,
        organisme_id: UUID | None,
        norme_id: UUID | None,
        deadline: str | None,
        verification: str | None,
        sort: str,
        limit: int,
        offset: int,
    ) -> CertificationRegistryResponse:
        rows, total = await CertificationRegistryRepository.registry(
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

        summary = await CertificationRegistryRepository.summary(
            db,
            search=search,
            statut=statut,
            entreprise_id=entreprise_id,
            organisme_id=organisme_id,
            norme_id=norme_id,
            deadline=deadline,
            verification=verification,
        )

        return CertificationRegistryResponse(
            total=total,
            limit=limit,
            offset=offset,
            summary=CertificationRegistrySummary(**summary),
            items=[
                CertificationRegistryService.build_item(row)
                for row in rows
            ],
        )

    @staticmethod
    async def item(
        db: AsyncSession,
        certification_id: UUID,
    ) -> CertificationRegistryItem:
        row = await CertificationRegistryRepository.registry_item(
            db,
            certification_id,
        )

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Certification introuvable.",
            )

        return CertificationRegistryService.build_item(row)

    @staticmethod
    async def audit_export(
        db: AsyncSession,
        *,
        actor: AuthContext,
        request: Request,
        motif: str,
        filters: dict,
        count: int,
        certification_id: UUID | None = None,
    ) -> None:
        await write_audit_event(
            db,
            action=(
                "CERTIFICATION_EXPORT"
                if certification_id
                else "CERTIFICATIONS_EXPORT"
            ),
            categorie="EXPORT",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="certification",
            ressource_id=certification_id,
            adresse_ip=client_ip(request),
            contexte={
                "motif": motif.strip(),
                "filtres": filters,
                "nombre": count,
            },
        )
        await db.commit()
