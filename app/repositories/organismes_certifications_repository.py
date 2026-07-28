"""
Repositories PostgreSQL du domaine Organismes / Certifications.

Le fichier regroupe les accès SQLAlchemy de ce domaine pour faciliter
l'intégration groupée. Les décisions métier restent dans les services.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import distinct, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accreditation import Accreditation
from app.models.audit_certification import AuditCertification
from app.models.certification import Certification
from app.models.couverture_certification import CouvertureCertification
from app.models.document import Document
from app.models.entreprise import Entreprise
from app.models.evenement_certification import EvenementCertification
from app.models.norme import Norme
from app.models.offre_entreprise import OffreEntreprise
from app.models.organisme import Organisme
from app.models.renouvellement_certification import RenouvellementCertification
from app.models.site_entreprise import SiteEntreprise
from app.models.zone_administrative import ZoneAdministrative


class NormeRepository:
    @staticmethod
    async def list(db: AsyncSession) -> list[Norme]:
        result = await db.execute(
            select(Norme).order_by(Norme.code, Norme.nom)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, norme_id: UUID) -> Norme | None:
        result = await db.execute(
            select(Norme).where(Norme.id == norme_id)
        )
        return result.scalar_one_or_none()


class OrganismeRepository:
    @staticmethod
    async def get(db: AsyncSession, organisme_id: UUID) -> Organisme | None:
        result = await db.execute(
            select(Organisme).where(Organisme.id == organisme_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def zone_exists(db: AsyncSession, zone_id: UUID) -> bool:
        result = await db.execute(
            select(ZoneAdministrative.id).where(
                ZoneAdministrative.id == zone_id
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Organisme], int]:
        filters = []

        if statut:
            filters.append(Organisme.statut == statut.strip())

        if search and search.strip():
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Organisme.identifiant_national.ilike(pattern),
                    Organisme.nom_officiel.ilike(pattern),
                    Organisme.sigle.ilike(pattern),
                    Organisme.numero_enregistrement.ilike(pattern),
                )
            )

        result = await db.execute(
            select(Organisme)
            .where(*filters)
            .order_by(Organisme.nom_officiel, Organisme.sigle)
            .limit(limit)
            .offset(offset)
        )

        total_result = await db.execute(
            select(func.count(Organisme.id)).where(*filters)
        )

        return list(result.scalars().all()), int(total_result.scalar_one())


    @staticmethod
    async def filters(db: AsyncSession) -> dict:
        async def distinct_strings(column):
            result = await db.execute(
                select(column)
                .where(
                    column.is_not(None),
                    func.trim(column) != "",
                )
                .distinct()
                .order_by(column)
            )
            return [
                str(value).strip()
                for value in result.scalars().all()
                if value
            ]

        zones_result = await db.execute(
            select(
                ZoneAdministrative.id,
                ZoneAdministrative.nom,
                ZoneAdministrative.type_zone,
            )
            .where(
                or_(
                    ZoneAdministrative.statut.is_(None),
                    func.upper(ZoneAdministrative.statut) == "ACTIF",
                )
            )
            .order_by(
                ZoneAdministrative.type_zone,
                ZoneAdministrative.nom,
            )
        )

        zones = [
            {
                "id": str(row.id),
                "name": row.nom or "",
                "type": row.type_zone or "",
            }
            for row in zones_result.all()
        ]

        return {
            "statuses": await distinct_strings(Organisme.statut),
            "countries": await distinct_strings(Organisme.pays),
            "types": await distinct_strings(Organisme.type_organisme),
            "accreditors": await distinct_strings(Accreditation.accrediteur),
            "domains": await distinct_strings(Accreditation.domaine_technique),
            "zones": zones,
        }

    @staticmethod
    def registry_filters(
        *,
        search: str | None,
        statut: str | None,
        pays: str | None,
        type_organisme: str | None,
        accrediteur: str | None,
        domaine: str | None,
    ):
        filters = []

        if statut:
            filters.append(
                func.upper(Organisme.statut)
                == statut.strip().upper()
            )

        if pays:
            filters.append(
                func.upper(Organisme.pays)
                == pays.strip().upper()
            )

        if type_organisme:
            filters.append(
                func.upper(Organisme.type_organisme)
                == type_organisme.strip().upper()
            )

        if search and search.strip():
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Organisme.identifiant_national.ilike(pattern),
                    Organisme.nom_officiel.ilike(pattern),
                    Organisme.sigle.ilike(pattern),
                    Organisme.numero_enregistrement.ilike(pattern),
                    Organisme.pays.ilike(pattern),
                )
            )

        if accrediteur:
            filters.append(
                select(Accreditation.id)
                .where(
                    Accreditation.organisme_id == Organisme.id,
                    func.upper(Accreditation.accrediteur)
                    == accrediteur.strip().upper(),
                )
                .exists()
            )

        if domaine:
            filters.append(
                select(Accreditation.id)
                .where(
                    Accreditation.organisme_id == Organisme.id,
                    func.upper(Accreditation.domaine_technique)
                    == domaine.strip().upper(),
                )
                .exists()
            )

        return filters

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
    ):
        filters = OrganismeRepository.registry_filters(
            search=search,
            statut=statut,
            pays=pays,
            type_organisme=type_organisme,
            accrediteur=accrediteur,
            domaine=domaine,
        )

        accreditation_count = (
            select(func.count(Accreditation.id))
            .where(Accreditation.organisme_id == Organisme.id)
            .correlate(Organisme)
            .scalar_subquery()
        )

        certification_count = (
            select(func.count(Certification.id))
            .where(Certification.organisme_id == Organisme.id)
            .correlate(Organisme)
            .scalar_subquery()
        )

        accreditors = (
            select(
                func.string_agg(
                    distinct(Accreditation.accrediteur),
                    literal(", "),
                )
            )
            .where(
                Accreditation.organisme_id == Organisme.id,
                Accreditation.accrediteur.is_not(None),
                func.trim(Accreditation.accrediteur) != "",
            )
            .correlate(Organisme)
            .scalar_subquery()
        )

        domains = (
            select(
                func.string_agg(
                    distinct(Accreditation.domaine_technique),
                    literal(", "),
                )
            )
            .where(
                Accreditation.organisme_id == Organisme.id,
                Accreditation.domaine_technique.is_not(None),
                func.trim(Accreditation.domaine_technique) != "",
            )
            .correlate(Organisme)
            .scalar_subquery()
        )

        next_expiration = (
            select(func.min(Accreditation.date_expiration))
            .where(
                Accreditation.organisme_id == Organisme.id,
                Accreditation.date_expiration >= func.current_date(),
            )
            .correlate(Organisme)
            .scalar_subquery()
        )

        order_by = {
            "name_desc": Organisme.nom_officiel.desc(),
            "certifications_desc": certification_count.desc(),
            "verification_desc":
                Organisme.date_derniere_verification
                .desc()
                .nullslast(),
        }.get(
            sort,
            Organisme.nom_officiel.asc(),
        )

        result = await db.execute(
            select(
                Organisme,
                accreditation_count.label("accreditation_count"),
                certification_count.label("certification_count"),
                accreditors.label("accreditors"),
                domains.label("domains"),
                next_expiration.label(
                    "next_accreditation_expiration"
                ),
            )
            .where(*filters)
            .order_by(order_by, Organisme.sigle)
            .limit(limit)
            .offset(offset)
        )

        count_result = await db.execute(
            select(func.count(Organisme.id)).where(*filters)
        )
        total = int(count_result.scalar_one() or 0)

        base_ids = (
            select(Organisme.id)
            .where(*filters)
        )

        cert_total_result = await db.execute(
            select(func.count(Certification.id)).where(
                Certification.organisme_id.in_(base_ids)
            )
        )

        status_rows = await db.execute(
            select(
                func.upper(
                    func.coalesce(
                        Organisme.statut,
                        "NON_RENSEIGNE",
                    )
                ),
                func.count(Organisme.id),
            )
            .where(*filters)
            .group_by(Organisme.statut)
        )

        status_counts = {
            str(key or "NON_RENSEIGNE"): int(value or 0)
            for key, value in status_rows.all()
        }

        recognized = sum(
            status_counts.get(key, 0)
            for key in ("RECONNU", "VALIDE", "ACTIF")
        )

        to_verify = sum(
            status_counts.get(key, 0)
            for key in (
                "A_VERIFIER",
                "À_VERIFIER",
                "A VERIFIER",
            )
        )

        suspended = sum(
            status_counts.get(key, 0)
            for key in ("SUSPENDU", "SUSPENDED")
        )

        return (
            result.all(),
            total,
            {
                "total": total,
                "recognized": recognized,
                "to_verify": to_verify,
                "suspended": suspended,
                "certifications_total": int(
                    cert_total_result.scalar_one() or 0
                ),
            },
        )

class AccreditationRepository:
    @staticmethod
    async def list_for_organisme(
        db: AsyncSession,
        organisme_id: UUID,
    ) -> list[Accreditation]:
        result = await db.execute(
            select(Accreditation)
            .where(Accreditation.organisme_id == organisme_id)
            .order_by(Accreditation.date_expiration.desc(), Accreditation.numero)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_for_organisme(
        db: AsyncSession,
        *,
        organisme_id: UUID,
        accreditation_id: UUID,
    ) -> Accreditation | None:
        result = await db.execute(
            select(Accreditation).where(
                Accreditation.id == accreditation_id,
                Accreditation.organisme_id == organisme_id,
            )
        )
        return result.scalar_one_or_none()


class CertificationRepository:
    @staticmethod
    async def get(db: AsyncSession, certification_id: UUID) -> Certification | None:
        result = await db.execute(
            select(Certification).where(Certification.id == certification_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_identifiant(
        db: AsyncSession,
        identifiant_national: str,
    ) -> Certification | None:
        result = await db.execute(
            select(Certification).where(
                Certification.identifiant_national == identifiant_national
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_entreprise(db: AsyncSession, entreprise_id: UUID) -> Entreprise | None:
        result = await db.execute(
            select(Entreprise).where(Entreprise.id == entreprise_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_organisme(db: AsyncSession, organisme_id: UUID) -> Organisme | None:
        result = await db.execute(
            select(Organisme).where(Organisme.id == organisme_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_norme(db: AsyncSession, norme_id: UUID) -> Norme | None:
        return await NormeRepository.get(db, norme_id)

    @staticmethod
    async def get_accreditation_for_organisme(
        db: AsyncSession,
        *,
        organisme_id: UUID,
        accreditation_id: UUID,
    ) -> Accreditation | None:
        return await AccreditationRepository.get_for_organisme(
            db,
            organisme_id=organisme_id,
            accreditation_id=accreditation_id,
        )

    @staticmethod
    async def find_same_scope(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        organisme_id: UUID,
        norme_id: UUID,
        portee: str | None,
    ) -> Certification | None:
        filters = [
            Certification.entreprise_id == entreprise_id,
            Certification.organisme_id == organisme_id,
            Certification.norme_id == norme_id,
        ]

        normalized = (portee or "").strip()
        if normalized:
            filters.append(
                func.lower(func.trim(Certification.portee)) == normalized.lower()
            )
        else:
            filters.append(
                or_(
                    Certification.portee.is_(None),
                    func.trim(Certification.portee) == "",
                )
            )

        result = await db.execute(
            select(Certification).where(*filters).limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def has_active_document(
        db: AsyncSession,
        certification_id: UUID,
    ) -> bool:
        result = await db.execute(
            select(Document.id)
            .where(
                Document.ressource_type == "CERTIFICATION",
                Document.ressource_id == certification_id,
                or_(Document.statut.is_(None), Document.statut == "ACTIF"),
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        search: str | None,
        entreprise_id: UUID | None,
        organisme_id: UUID | None,
        norme_id: UUID | None,
        statut: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Certification], int]:
        filters = []

        if entreprise_id:
            filters.append(Certification.entreprise_id == entreprise_id)
        if organisme_id:
            filters.append(Certification.organisme_id == organisme_id)
        if norme_id:
            filters.append(Certification.norme_id == norme_id)
        if statut:
            filters.append(Certification.statut == statut.strip())

        if search and search.strip():
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Certification.identifiant_national.ilike(pattern),
                    Certification.numero_certificat.ilike(pattern),
                    Certification.portee.ilike(pattern),
                )
            )

        result = await db.execute(
            select(Certification)
            .where(*filters)
            .order_by(Certification.date_expiration, Certification.identifiant_national)
            .limit(limit)
            .offset(offset)
        )

        total_result = await db.execute(
            select(func.count(Certification.id)).where(*filters)
        )

        return list(result.scalars().all()), int(total_result.scalar_one())


class CouvertureRepository:
    @staticmethod
    async def list(db: AsyncSession, certification_id: UUID) -> list[CouvertureCertification]:
        result = await db.execute(
            select(CouvertureCertification)
            .where(CouvertureCertification.certification_id == certification_id)
            .order_by(
                CouvertureCertification.type_couverture,
                CouvertureCertification.libelle_couverture,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get(
        db: AsyncSession,
        *,
        certification_id: UUID,
        couverture_id: UUID,
    ) -> CouvertureCertification | None:
        result = await db.execute(
            select(CouvertureCertification).where(
                CouvertureCertification.id == couverture_id,
                CouvertureCertification.certification_id == certification_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_offre(db: AsyncSession, offre_id: UUID) -> OffreEntreprise | None:
        result = await db.execute(
            select(OffreEntreprise).where(OffreEntreprise.id == offre_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_site(db: AsyncSession, site_id: UUID) -> SiteEntreprise | None:
        result = await db.execute(
            select(SiteEntreprise).where(SiteEntreprise.id == site_id)
        )
        return result.scalar_one_or_none()


class AuditCertificationRepository:
    @staticmethod
    async def list(db: AsyncSession, certification_id: UUID) -> list[AuditCertification]:
        result = await db.execute(
            select(AuditCertification)
            .where(AuditCertification.certification_id == certification_id)
            .order_by(AuditCertification.date_prevue.desc(), AuditCertification.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get(
        db: AsyncSession,
        *,
        certification_id: UUID,
        audit_id: UUID,
    ) -> AuditCertification | None:
        result = await db.execute(
            select(AuditCertification).where(
                AuditCertification.id == audit_id,
                AuditCertification.certification_id == certification_id,
            )
        )
        return result.scalar_one_or_none()


class EvenementCertificationRepository:
    @staticmethod
    async def list(db: AsyncSession, certification_id: UUID) -> list[EvenementCertification]:
        result = await db.execute(
            select(EvenementCertification)
            .where(EvenementCertification.certification_id == certification_id)
            .order_by(EvenementCertification.date_evenement.desc(), EvenementCertification.created_at.desc())
        )
        return list(result.scalars().all())


class RenouvellementRepository:
    @staticmethod
    async def list(db: AsyncSession, certification_id: UUID) -> list[RenouvellementCertification]:
        result = await db.execute(
            select(RenouvellementCertification)
            .where(RenouvellementCertification.certification_id == certification_id)
            .order_by(RenouvellementCertification.date_ouverture.desc(), RenouvellementCertification.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get(
        db: AsyncSession,
        *,
        certification_id: UUID,
        renouvellement_id: UUID,
    ) -> RenouvellementCertification | None:
        result = await db.execute(
            select(RenouvellementCertification).where(
                RenouvellementCertification.id == renouvellement_id,
                RenouvellementCertification.certification_id == certification_id,
            )
        )
        return result.scalar_one_or_none()
