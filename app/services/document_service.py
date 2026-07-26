"""
Service sécurisé de gestion documentaire.

SÉCURITÉ
--------
- stockage hors de `app/static` ;
- nom physique généré par le serveur ;
- liste blanche MIME + extension ;
- taille maximale ;
- checksum SHA-256 ;
- téléchargement uniquement via route authentifiée ;
- `chemin_stockage` jamais exposé ;
- validation de l'existence de la ressource liée.

Les documents ne sont jamais supprimés physiquement par l'API courante :
ils peuvent être désactivés tout en restant traçables.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.config.settings import settings
from app.models.accreditation import Accreditation
from app.models.audit_certification import AuditCertification
from app.models.certification import Certification
from app.models.document import Document
from app.models.entreprise import Entreprise
from app.models.offre_entreprise import OffreEntreprise
from app.models.organisme import Organisme
from app.models.renouvellement_certification import RenouvellementCertification
from app.models.site_entreprise import SiteEntreprise
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.auth_service import AuthContext
from app.models.dossier_verification import DossierVerification
from app.models.point_verification import PointVerification
from app.models.anomalie_verification import AnomalieVerification
from app.models.confirmation_externe import ConfirmationExterne
from app.models.controle_fuccs import ControleFuccs
from app.models.note_critere import NoteCritere
from app.models.constat_controle import ConstatControle
from app.models.fiche_collecte import FicheCollecte
from app.models.offre_declaree import OffreDeclaree
from app.models.certification_declaree import CertificationDeclaree


ALLOWED_FILES = {
    "application/pdf": {".pdf"},
    "image/png": {".png"},
    "image/jpeg": {".jpg", ".jpeg"},
}

RESOURCE_MODELS = {
    "ENTREPRISE": Entreprise,
    "ORGANISME": Organisme,
    "ACCREDITATION": Accreditation,
    "CERTIFICATION": Certification,
    "SITE_ENTREPRISE": SiteEntreprise,
    "OFFRE_ENTREPRISE": OffreEntreprise,
    "AUDIT_CERTIFICATION": AuditCertification,
    "RENOUVELLEMENT_CERTIFICATION": RenouvellementCertification,
    "DOSSIER_VERIFICATION": DossierVerification,
    "POINT_VERIFICATION": PointVerification,
    "ANOMALIE_VERIFICATION": AnomalieVerification,
    "CONFIRMATION_EXTERNE": ConfirmationExterne,
    "CONTROLE_FUCCS": ControleFuccs,
    "NOTE_CRITERE": NoteCritere,
    "CONSTAT_CONTROLE": ConstatControle,
    "FICHE_COLLECTE": FicheCollecte,
    "OFFRE_DECLAREE": OffreDeclaree,
    "CERTIFICATION_DECLAREE": CertificationDeclaree,
}


def storage_root() -> Path:
    raw = getattr(settings, "document_storage_dir", "uploads/private")
    root = Path(raw).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def max_size_bytes() -> int:
    return int(
        getattr(
            settings,
            "document_max_size_bytes",
            10 * 1024 * 1024,
        )
    )


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def build_response(item: Document) -> DocumentResponse:
    return DocumentResponse(
        id=item.id,
        type_document=item.type_document,
        nom_original=item.nom_original,
        nom_stockage=item.nom_stockage,
        format=item.format,
        taille_octets=item.taille_octets,
        checksum=item.checksum,
        version=item.version,
        ressource_type=item.ressource_type,
        ressource_id=item.ressource_id,
        confidentialite=item.confidentialite,
        source=item.source,
        date_document=item.date_document,
        depose_par_id=item.depose_par_id,
        date_depot=item.date_depot,
        statut_verification=item.statut_verification,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


class DocumentService:
    @staticmethod
    async def ensure_resource_exists(
        db: AsyncSession,
        *,
        ressource_type: str,
        ressource_id: UUID,
    ) -> None:
        model = RESOURCE_MODELS.get(ressource_type)
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Type de ressource documentaire non supporté par ce domaine.",
            )

        result = await db.execute(
            select(model.id).where(model.id == ressource_id)
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ressource documentaire cible introuvable.",
            )

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        ressource_type: str | None,
        ressource_id: UUID | None,
        include_inactive: bool,
        limit: int,
        offset: int,
    ) -> DocumentListResponse:
        items, total = await DocumentRepository.list(
            db,
            ressource_type=ressource_type,
            ressource_id=ressource_id,
            include_inactive=include_inactive,
            limit=limit,
            offset=offset,
        )
        return DocumentListResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=[build_response(x) for x in items],
        )

    @staticmethod
    async def get(db: AsyncSession, document_id: UUID) -> Document:
        item = await DocumentRepository.get(db, document_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Document introuvable.")
        return item

    @staticmethod
    async def upload(
        db: AsyncSession,
        *,
        file: UploadFile,
        type_document: str,
        ressource_type: str,
        ressource_id: UUID,
        confidentialite: str | None,
        source: str | None,
        date_document: date | None,
        actor: AuthContext,
        request: Request,
    ) -> DocumentResponse:
        resource_type = ressource_type.strip().upper()
        await DocumentService.ensure_resource_exists(
            db,
            ressource_type=resource_type,
            ressource_id=ressource_id,
        )

        content_type = (file.content_type or "").split(";")[0].strip().lower()
        original_name = file.filename or "document"
        extension = Path(original_name).suffix.lower()
        allowed_extensions = ALLOWED_FILES.get(content_type)

        if allowed_extensions is None or extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Format non autorisé. Formats actuels : PDF, PNG, JPG/JPEG.",
            )

        generated_name = f"{uuid4().hex}{extension}"
        root = storage_root()
        target = (root / generated_name).resolve()

        if root not in target.parents:
            raise HTTPException(status_code=400, detail="Chemin de stockage invalide.")

        digest = sha256()
        size = 0
        max_bytes = max_size_bytes()

        try:
            with target.open("wb") as output:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Le document dépasse la taille maximale autorisée.",
                        )
                    digest.update(chunk)
                    output.write(chunk)

            item = Document(
                type_document=clean_text(type_document),
                nom_original=original_name,
                nom_stockage=generated_name,
                chemin_stockage=str(target),
                format=extension.lstrip(".").upper(),
                taille_octets=size,
                checksum=digest.hexdigest(),
                version="1",
                ressource_type=resource_type,
                ressource_id=ressource_id,
                confidentialite=clean_text(confidentialite) or "INTERNE",
                source=clean_text(source) or "API",
                date_document=date_document,
                depose_par_id=actor.user.id,
                date_depot=datetime.now(timezone.utc),
                statut_verification="A_VERIFIER",
                statut="ACTIF",
            )
            db.add(item)
            await db.flush()

            await write_audit_event(
                db,
                action="DOCUMENT_UPLOAD",
                categorie="DOCUMENTAIRE",
                resultat="SUCCES",
                utilisateur_id=actor.user.id,
                ressource_type="document",
                ressource_id=item.id,
                adresse_ip=client_ip(request),
                valeurs_apres={
                    "type_document": item.type_document,
                    "nom_original": item.nom_original,
                    "format": item.format,
                    "taille_octets": item.taille_octets,
                    "checksum": item.checksum,
                    "ressource_type": item.ressource_type,
                    "ressource_id": str(item.ressource_id),
                    "confidentialite": item.confidentialite,
                    "statut_verification": item.statut_verification,
                },
            )

            await db.commit()
            await db.refresh(item)
            return build_response(item)

        except Exception:
            await db.rollback()
            if target.exists():
                target.unlink(missing_ok=True)
            raise
        finally:
            await file.close()

    @staticmethod
    async def verify(
        db: AsyncSession,
        *,
        document_id: UUID,
        statut_verification: str,
        motif: str | None,
        actor: AuthContext,
        request: Request,
    ) -> DocumentResponse:
        item = await DocumentService.get(db, document_id)
        before = item.statut_verification
        item.statut_verification = statut_verification.strip()

        await write_audit_event(
            db,
            action="DOCUMENT_VERIFY",
            categorie="DOCUMENTAIRE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="document",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant={"statut_verification": before},
            valeurs_apres={"statut_verification": item.statut_verification},
            contexte={"motif": clean_text(motif)},
        )
        await db.commit()
        await db.refresh(item)
        return build_response(item)

    @staticmethod
    async def deactivate(
        db: AsyncSession,
        *,
        document_id: UUID,
        motif: str | None,
        actor: AuthContext,
        request: Request,
    ) -> DocumentResponse:
        item = await DocumentService.get(db, document_id)
        if (item.statut or "").strip().upper() == "INACTIF":
            return build_response(item)

        old = item.statut
        item.statut = "INACTIF"
        await write_audit_event(
            db,
            action="DOCUMENT_DEACTIVATE",
            categorie="DOCUMENTAIRE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="document",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant={"statut": old},
            valeurs_apres={"statut": "INACTIF"},
            contexte={"motif": clean_text(motif)},
        )
        await db.commit()
        await db.refresh(item)
        return build_response(item)

    @staticmethod
    async def restore(
        db: AsyncSession,
        *,
        document_id: UUID,
        motif: str | None,
        actor: AuthContext,
        request: Request,
    ) -> DocumentResponse:
        item = await DocumentService.get(db, document_id)
        if (item.statut or "").strip().upper() != "INACTIF":
            raise HTTPException(status_code=409, detail="Ce document n'est pas désactivé.")

        item.statut = "ACTIF"
        await write_audit_event(
            db,
            action="DOCUMENT_RESTORE",
            categorie="DOCUMENTAIRE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="document",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant={"statut": "INACTIF"},
            valeurs_apres={"statut": "ACTIF"},
            contexte={"motif": clean_text(motif)},
        )
        await db.commit()
        await db.refresh(item)
        return build_response(item)

    @staticmethod
    async def secure_path(
        db: AsyncSession,
        document_id: UUID,
    ) -> tuple[Document, Path]:
        item = await DocumentService.get(db, document_id)
        if (item.statut or "").strip().upper() == "INACTIF":
            raise HTTPException(status_code=409, detail="Le document est désactivé.")
        if not item.chemin_stockage:
            raise HTTPException(status_code=404, detail="Fichier physique indisponible.")

        root = storage_root()
        path = Path(item.chemin_stockage).resolve()
        if root not in path.parents or not path.is_file():
            raise HTTPException(status_code=404, detail="Fichier physique indisponible.")
        return item, path
