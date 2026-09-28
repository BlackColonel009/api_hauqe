from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from app.models.document import Document
from app.services.fiche_collecte_service import FicheCollecteService
from app.services.validation_bnec_service import ValidationBnecService


def test_revision_document_keeps_file_and_resets_verification():
    original = Document(
        id=uuid4(),
        nom_original="preuve.pdf",
        nom_stockage="fichier-prive.pdf",
        chemin_stockage="/private/fichier-prive.pdf",
        checksum="sha256-original",
        ressource_type="CERTIFICATION",
        ressource_id=uuid4(),
        statut_verification="VERIFIE",
        statut="ACTIF",
    )
    new_declaration_id = uuid4()

    copy = FicheCollecteService.revision_document_copy(
        original,
        resource_type="CERTIFICATION_DECLAREE",
        resource_id=new_declaration_id,
    )

    assert copy.ressource_id == new_declaration_id
    assert copy.chemin_stockage == original.chemin_stockage
    assert copy.checksum == original.checksum
    assert copy.statut_verification == "A_VERIFIER"
    assert copy.source == f"REVISION_COLLECTE:{original.id}"
    assert original.statut_verification == "VERIFIE"


def test_reintegration_preserves_only_identical_claim():
    organisme_id, norme_id = uuid4(), uuid4()
    source = SimpleNamespace(
        numero="CERT-2026-01",
        portee="Agroalimentaire",
        date_obtention=date(2026, 1, 1),
        date_expiration=date(2027, 1, 1),
    )
    target = SimpleNamespace(
        organisme_id=organisme_id,
        norme_id=norme_id,
        numero_certificat="cert-2026-01",
        portee="agroalimentaire",
        date_obtention=source.date_obtention,
        date_expiration=source.date_expiration,
    )

    assert ValidationBnecService._same_certification_claim(
        target, source, organisme_id=organisme_id, norme_id=norme_id,
    )
    source.date_expiration = date(2028, 1, 1)
    assert not ValidationBnecService._same_certification_claim(
        target, source, organisme_id=organisme_id, norme_id=norme_id,
    )
