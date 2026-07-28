from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accreditation import Accreditation
from app.models.certification import Certification
from app.models.document import Document
from app.models.entreprise import Entreprise
from app.models.norme import Norme
from app.models.organisme import Organisme
from app.models.renouvellement_certification import (
    RenouvellementCertification,
)


class CertificationRegistryRepository:
    @staticmethod
    async def filters(db: AsyncSession) -> dict:
        status_result = await db.execute(
            select(Certification.statut)
            .where(
                Certification.statut.is_not(None),
                func.trim(Certification.statut) != "",
            )
            .distinct()
            .order_by(Certification.statut)
        )

        norm_result = await db.execute(
            select(
                Norme.id,
                Norme.code,
                Norme.nom,
                Norme.version,
            )
            .order_by(Norme.code, Norme.nom)
        )

        organism_result = await db.execute(
            select(
                Organisme.id,
                Organisme.identifiant_national,
                Organisme.nom_officiel,
                Organisme.sigle,
            )
            .order_by(Organisme.nom_officiel, Organisme.sigle)
        )

        return {
            "statuses": [
                str(value).strip()
                for value in status_result.scalars().all()
                if value
            ],
            "norms": [
                {
                    "id": row.id,
                    "code": row.code,
                    "label": " ".join(
                        part
                        for part in (
                            row.code,
                            f"v{row.version}" if row.version else None,
                            f"— {row.nom}" if row.nom else None,
                        )
                        if part
                    ) or "Norme sans libellé",
                }
                for row in norm_result.all()
            ],
            "organisms": [
                {
                    "id": row.id,
                    "code": row.sigle or row.identifiant_national,
                    "label": (
                        " — ".join(
                            part
                            for part in (
                                row.sigle or row.identifiant_national,
                                row.nom_officiel,
                            )
                            if part
                        )
                        or "Organisme sans libellé"
                    ),
                }
                for row in organism_result.all()
            ],
        }

    @staticmethod
    def build_filters(
        *,
        search: str | None,
        statut: str | None,
        entreprise_id: UUID | None,
        organisme_id: UUID | None,
        norme_id: UUID | None,
        deadline: str | None,
        verification: str | None,
    ):
        filters = []

        if statut:
            filters.append(
                func.upper(Certification.statut)
                == statut.strip().upper()
            )

        if entreprise_id:
            filters.append(
                Certification.entreprise_id == entreprise_id
            )

        if organisme_id:
            filters.append(
                Certification.organisme_id == organisme_id
            )

        if norme_id:
            filters.append(
                Certification.norme_id == norme_id
            )

        if verification == "verified":
            filters.append(
                Certification.authenticite_verifiee.is_(True)
            )
        elif verification == "pending":
            filters.append(
                or_(
                    Certification.authenticite_verifiee.is_(False),
                    Certification.authenticite_verifiee.is_(None),
                )
            )

        today = date.today()

        if deadline == "expired":
            filters.extend(
                [
                    Certification.date_expiration.is_not(None),
                    Certification.date_expiration < today,
                ]
            )
        elif deadline in {"30", "90", "180"}:
            days = int(deadline)
            filters.extend(
                [
                    Certification.date_expiration.is_not(None),
                    Certification.date_expiration >= today,
                    Certification.date_expiration
                    <= today + timedelta(days=days),
                ]
            )
        elif deadline == "none":
            filters.append(
                Certification.date_expiration.is_(None)
            )

        if search and search.strip():
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Certification.identifiant_national.ilike(pattern),
                    Certification.numero_certificat.ilike(pattern),
                    Certification.portee.ilike(pattern),
                    Entreprise.raison_sociale.ilike(pattern),
                    Entreprise.nom_commercial.ilike(pattern),
                    Organisme.nom_officiel.ilike(pattern),
                    Organisme.sigle.ilike(pattern),
                    Norme.code.ilike(pattern),
                    Norme.nom.ilike(pattern),
                )
            )

        return filters

    @staticmethod
    def base_select():
        document_count = (
            select(func.count(Document.id))
            .where(
                Document.ressource_type == "CERTIFICATION",
                Document.ressource_id == Certification.id,
                or_(
                    Document.statut.is_(None),
                    func.upper(Document.statut) == "ACTIF",
                ),
            )
            .correlate(Certification)
            .scalar_subquery()
        )

        renewal_open_count = (
            select(func.count(RenouvellementCertification.id))
            .where(
                RenouvellementCertification.certification_id
                == Certification.id,
                RenouvellementCertification.date_decision.is_(None),
            )
            .correlate(Certification)
            .scalar_subquery()
        )

        return (
            select(
                Certification,
                Entreprise.raison_sociale.label("entreprise_name"),
                Entreprise.nom_commercial.label(
                    "entreprise_trade_name"
                ),
                Organisme.nom_officiel.label("organisme_name"),
                Organisme.sigle.label("organisme_sigle"),
                Norme.code.label("norme_code"),
                Norme.nom.label("norme_name"),
                Norme.version.label("norme_version"),
                Accreditation.accrediteur.label("accrediteur"),
                document_count.label("document_count"),
                renewal_open_count.label("renewal_open_count"),
            )
            .select_from(Certification)
            .join(
                Entreprise,
                Entreprise.id == Certification.entreprise_id,
            )
            .join(
                Organisme,
                Organisme.id == Certification.organisme_id,
            )
            .join(
                Norme,
                Norme.id == Certification.norme_id,
            )
            .outerjoin(
                Accreditation,
                Accreditation.id == Certification.accreditation_id,
            )
        )

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
    ):
        filters = CertificationRegistryRepository.build_filters(
            search=search,
            statut=statut,
            entreprise_id=entreprise_id,
            organisme_id=organisme_id,
            norme_id=norme_id,
            deadline=deadline,
            verification=verification,
        )

        order_by = {
            "recent": Certification.created_at.desc(),
            "company": Entreprise.raison_sociale.asc(),
            "standard": Norme.code.asc(),
            "status": Certification.statut.asc(),
        }.get(
            sort,
            Certification.date_expiration.asc().nullslast(),
        )

        stmt = (
            CertificationRegistryRepository.base_select()
            .where(*filters)
            .order_by(
                order_by,
                Certification.identifiant_national.asc(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(stmt)

        count_stmt = (
            select(func.count(Certification.id))
            .select_from(Certification)
            .join(
                Entreprise,
                Entreprise.id == Certification.entreprise_id,
            )
            .join(
                Organisme,
                Organisme.id == Certification.organisme_id,
            )
            .join(
                Norme,
                Norme.id == Certification.norme_id,
            )
            .where(*filters)
        )

        count_result = await db.execute(count_stmt)

        return result.all(), int(count_result.scalar_one() or 0)

    @staticmethod
    async def summary(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
        entreprise_id: UUID | None,
        organisme_id: UUID | None,
        norme_id: UUID | None,
        deadline: str | None,
        verification: str | None,
    ) -> dict:
        filters = CertificationRegistryRepository.build_filters(
            search=search,
            statut=statut,
            entreprise_id=entreprise_id,
            organisme_id=organisme_id,
            norme_id=norme_id,
            deadline=deadline,
            verification=verification,
        )

        today = date.today()

        renewal_exists = (
            select(RenouvellementCertification.id)
            .where(
                RenouvellementCertification.certification_id
                == Certification.id,
                RenouvellementCertification.date_decision.is_(None),
            )
            .exists()
        )

        stmt = (
            select(
                func.count(Certification.id).label("total"),
                func.sum(
                    case(
                        (
                            func.upper(
                                func.coalesce(
                                    Certification.statut,
                                    "",
                                )
                            ).in_(
                                ["ACTIF", "ACTIVE", "VALIDE"]
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("active_status"),
                func.sum(
                    case(
                        (
                            Certification.authenticite_verifiee.is_(True),
                            1,
                        ),
                        else_=0,
                    )
                ).label("verified"),
                func.sum(
                    case(
                        (
                            or_(
                                Certification.authenticite_verifiee.is_(False),
                                Certification.authenticite_verifiee.is_(None),
                                func.upper(
                                    func.coalesce(
                                        Certification.statut,
                                        "",
                                    )
                                ).in_(
                                    [
                                        "A_VERIFIER",
                                        "À_VERIFIER",
                                        "A VERIFIER",
                                    ]
                                ),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("to_verify"),
                func.sum(
                    case(
                        (
                            and_(
                                Certification.date_expiration.is_not(None),
                                Certification.date_expiration < today,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("expired"),
                func.sum(
                    case(
                        (
                            and_(
                                Certification.date_expiration >= today,
                                Certification.date_expiration
                                <= today + timedelta(days=30),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("expiring_30"),
                func.sum(
                    case(
                        (
                            and_(
                                Certification.date_expiration
                                > today + timedelta(days=30),
                                Certification.date_expiration
                                <= today + timedelta(days=90),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("expiring_90"),
                func.sum(
                    case(
                        (
                            and_(
                                Certification.date_expiration
                                > today + timedelta(days=90),
                                Certification.date_expiration
                                <= today + timedelta(days=180),
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("expiring_180"),
                func.sum(
                    case(
                        (
                            func.upper(
                                func.coalesce(
                                    Certification.statut,
                                    "",
                                )
                            ) == "SUSPENDU",
                            1,
                        ),
                        else_=0,
                    )
                ).label("suspended"),
                func.sum(
                    case(
                        (renewal_exists, 1),
                        else_=0,
                    )
                ).label("renewals_open"),
            )
            .select_from(Certification)
            .join(
                Entreprise,
                Entreprise.id == Certification.entreprise_id,
            )
            .join(
                Organisme,
                Organisme.id == Certification.organisme_id,
            )
            .join(
                Norme,
                Norme.id == Certification.norme_id,
            )
            .where(*filters)
        )

        result = await db.execute(stmt)
        row = result.one()

        return {
            "total": int(row.total or 0),
            "active_status": int(row.active_status or 0),
            "verified": int(row.verified or 0),
            "to_verify": int(row.to_verify or 0),
            "expired": int(row.expired or 0),
            "expiring_30": int(row.expiring_30 or 0),
            "expiring_90": int(row.expiring_90 or 0),
            "expiring_180": int(row.expiring_180 or 0),
            "suspended": int(row.suspended or 0),
            "renewals_open": int(row.renewals_open or 0),
        }

    @staticmethod
    async def registry_item(
        db: AsyncSession,
        certification_id: UUID,
    ):
        result = await db.execute(
            CertificationRegistryRepository.base_select()
            .where(Certification.id == certification_id)
        )
        return result.one_or_none()
