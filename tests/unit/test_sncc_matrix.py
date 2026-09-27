from datetime import date, timedelta

from app.models.certification import Certification
from app.rules.sncc_matrix import validate_sncc_matrix_parameters
from app.schemas.veille import FollowUpCreateRequest
from app.services.automatic_scoring_service import AutomaticScoringService


def test_sncc_matrix_accepts_complete_non_overlapping_ranges():
    normalized, errors = validate_sncc_matrix_parameters(
        {
            "rows": [
                {"min": 90, "max": 100, "classe": "A+", "statut_administratif": "VA", "niveau_risque": "R1"},
                {"min": 75, "max": 89.99, "classe": "A", "statut_administratif": "VA", "niveau_risque": "R1"},
                {"min": 60, "max": 74.99, "classe": "B", "statut_administratif": "RE", "niveau_risque": "R2"},
                {"min": 40, "max": 59.99, "classe": "C", "statut_administratif": "SU", "niveau_risque": "R3"},
                {"min": 0, "max": 39.99, "classe": "D", "statut_administratif": "RT", "niveau_risque": "R5"},
            ]
        }
    )

    assert errors == []
    assert [row["classe"] for row in normalized["rows"]] == ["D", "C", "B", "A", "A+"]


def test_sncc_matrix_rejects_overlapping_ranges():
    _, errors = validate_sncc_matrix_parameters(
        {
            "rows": [
                {"min": 90, "max": 100, "classe": "A+", "statut_administratif": "VA", "niveau_risque": "R1"},
                {"min": 75, "max": 90, "classe": "A", "statut_administratif": "VA", "niveau_risque": "R1"},
                {"min": 60, "max": 74.99, "classe": "B", "statut_administratif": "RE", "niveau_risque": "R2"},
                {"min": 40, "max": 59.99, "classe": "C", "statut_administratif": "SU", "niveau_risque": "R3"},
                {"min": 0, "max": 39.99, "classe": "D", "statut_administratif": "RT", "niveau_risque": "R5"},
            ]
        }
    )

    assert "Les plages SNCC se chevauchent." in errors


def test_followup_request_extracts_text_from_legacy_component_value():
    payload = FollowUpCreateRequest.model_validate(
        {
            "destinataire": {"label": "Service qualité"},
            "adresse_email": {"value": "qualite@example.org"},
            "canal": {"value": "EMAIL"},
            "objet": {"text": "Relance de confirmation"},
            "contenu": {"value": "Bonjour, merci de nous répondre."},
        }
    )

    assert payload.destinataire == "Service qualité"
    assert payload.adresse_email == "qualite@example.org"
    assert payload.contenu == "Bonjour, merci de nous répondre."


def test_sncc_expiration_has_priority_over_unverified_authenticity():
    certification = Certification(
        date_expiration=date.today() - timedelta(days=1),
        statut="A_VERIFIER",
        authenticite_verifiee=False,
    )

    status, reason = AutomaticScoringService._sncc_priority_status(certification)

    assert status == "EX"
    assert "expiration" in reason.lower()


def test_sncc_unverified_current_certificate_is_in_verification():
    certification = Certification(
        date_expiration=date.today() + timedelta(days=30),
        statut="A_VERIFIER",
        authenticite_verifiee=False,
    )

    status, reason = AutomaticScoringService._sncc_priority_status(certification)

    assert status == "VE"
    assert "authenticité" in reason.lower()
