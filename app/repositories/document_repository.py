"""Repository PostgreSQL des documents privés."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.certification import Certification
from app.models.certification_declaree import CertificationDeclaree
from app.models.entreprise import Entreprise
from app.models.fiche_collecte import FicheCollecte


class DocumentRepository:
    @staticmethod
    async def list_for_fiche(
        db: AsyncSession, fiche_id: UUID, *, limit: int, offset: int
    ):
        """Pièces générales et preuves de chaque certificat déclaré, même après BNEC."""
        declarations = list((await db.execute(
            select(CertificationDeclaree)
            .where(CertificationDeclaree.fiche_collecte_id == fiche_id)
            .order_by(CertificationDeclaree.created_at, CertificationDeclaree.id)
        )).scalars().all())
        declaration_ids = [item.id for item in declarations]
        certification_ids = list(dict.fromkeys(
            item.certification_officielle_id for item in declarations
            if item.certification_officielle_id is not None
        ))
        scopes = [and_(
            Document.ressource_type == "FICHE_COLLECTE",
            Document.ressource_id == fiche_id,
        )]
        if declaration_ids:
            scopes.append(and_(
                Document.ressource_type == "CERTIFICATION_DECLAREE",
                Document.ressource_id.in_(declaration_ids),
            ))
        if certification_ids:
            scopes.append(and_(
                Document.ressource_type == "CERTIFICATION",
                Document.ressource_id.in_(certification_ids),
            ))
        filters = [
            or_(*scopes),
            or_(Document.statut.is_(None), Document.statut == "ACTIF"),
        ]
        documents = list((await db.execute(
            select(Document)
            .where(*filters)
            .order_by(Document.date_depot.desc(), Document.created_at.desc(), Document.id)
            .limit(limit).offset(offset)
        )).scalars().all())
        total = int((await db.execute(
            select(func.count(Document.id)).where(*filters)
        )).scalar_one())
        return documents, declarations, total

    @staticmethod
    async def list_for_entreprise(db: AsyncSession, entreprise_id: UUID):
        """Pièces directes, collectes et certificats de cette entreprise."""
        result = await db.execute(
            select(
                Document,
                FicheCollecte.id.label("fiche_collecte_id"),
                FicheCollecte.numero_revision.label("numero_revision"),
                CertificationDeclaree.nom_certification.label("declared_name"),
                CertificationDeclaree.numero.label("declared_number"),
                Certification.identifiant_national.label("certification_code"),
                Certification.numero_certificat.label("certification_number"),
            )
            .outerjoin(
                CertificationDeclaree,
                and_(
                    Document.ressource_type == "CERTIFICATION_DECLAREE",
                    Document.ressource_id == CertificationDeclaree.id,
                ),
            )
            .outerjoin(
                FicheCollecte,
                or_(
                    and_(
                        Document.ressource_type == "FICHE_COLLECTE",
                        Document.ressource_id == FicheCollecte.id,
                    ),
                    CertificationDeclaree.fiche_collecte_id == FicheCollecte.id,
                ),
            )
            .outerjoin(
                Certification,
                and_(
                    Document.ressource_type == "CERTIFICATION",
                    Document.ressource_id == Certification.id,
                ),
            )
            .where(
                or_(
                    and_(
                        Document.ressource_type == "ENTREPRISE",
                        Document.ressource_id == entreprise_id,
                    ),
                    FicheCollecte.entreprise_id == entreprise_id,
                    Certification.entreprise_id == entreprise_id,
                ),
                or_(Document.statut.is_(None), Document.statut == "ACTIF"),
            )
            .order_by(Document.date_depot.desc(), Document.created_at.desc())
        )
        return result.all()

    @staticmethod
    async def list_for_organisme(db: AsyncSession, organisme_id: UUID):
        """Pièces propres à l'organisme et preuves de ses certificats, sans copie."""
        result = await db.execute(
            select(
                Document,
                Certification.id.label("certification_id"),
                Certification.identifiant_national.label("certification_code"),
                Entreprise.raison_sociale.label("entreprise_name"),
            )
            .outerjoin(
                Certification,
                and_(
                    Document.ressource_type == "CERTIFICATION",
                    Document.ressource_id == Certification.id,
                ),
            )
            .outerjoin(Entreprise, Entreprise.id == Certification.entreprise_id)
            .where(
                or_(
                    and_(
                        Document.ressource_type == "ORGANISME",
                        Document.ressource_id == organisme_id,
                    ),
                    Certification.organisme_id == organisme_id,
                ),
                or_(Document.statut.is_(None), Document.statut == "ACTIF"),
            )
            .order_by(Document.date_depot.desc(), Document.created_at.desc())
        )
        return result.all()

    @staticmethod
    async def get(db: AsyncSession, document_id: UUID) -> Document | None:
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        ressource_type: str | None,
        ressource_id: UUID | None,
        include_inactive: bool,
        limit: int,
        offset: int,
    ) -> tuple[list[Document], int]:
        filters = []

        if ressource_type:
            filters.append(Document.ressource_type == ressource_type.strip().upper())
        if ressource_id:
            filters.append(Document.ressource_id == ressource_id)
        if not include_inactive:
            filters.append(or_(Document.statut.is_(None), Document.statut == "ACTIF"))

        result = await db.execute(
            select(Document)
            .where(*filters)
            .order_by(Document.date_depot.desc(), Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count_result = await db.execute(
            select(func.count(Document.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count_result.scalar_one())
