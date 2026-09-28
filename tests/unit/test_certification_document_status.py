from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.organismes_certifications import OrganismeVerificationRequest
from app.schemas.dashboard import ExpiringCertificationItem
from app.services import dashboard_service
from app.services.validation_bnec_service import ValidationBnecService


def test_expired_declaration_is_expired_even_without_copy():
    source = SimpleNamespace(
        copie_disponible=False,
        date_expiration=date.today() - timedelta(days=1),
        situation_declaree="ACTIVE",
    )
    assert ValidationBnecService._certification_status(source) == "EXPIREE"


def test_current_declaration_without_copy_requires_verification():
    source = SimpleNamespace(
        copie_disponible=False,
        date_expiration=date.today() + timedelta(days=30),
        situation_declaree="ACTIVE",
    )
    assert ValidationBnecService._certification_status(source) == "A_VERIFIER"


def test_copy_alone_does_not_validate_authenticity():
    source = SimpleNamespace(
        copie_disponible=True,
        date_expiration=date.today() + timedelta(days=30),
        situation_declaree="ACTIVE",
    )
    assert ValidationBnecService._certification_status(source) == "A_VERIFIER"


def test_organism_verification_accepts_only_explicit_decisions():
    assert OrganismeVerificationRequest(statut="RECONNU", motif="Contrôle effectué").statut == "RECONNU"
    with pytest.raises(ValidationError):
        OrganismeVerificationRequest(statut="VALIDÉ libre", motif="Contrôle effectué")


def test_dashboard_can_build_an_expired_certification_item():
    assert dashboard_service.ExpiringCertificationItem is ExpiringCertificationItem
