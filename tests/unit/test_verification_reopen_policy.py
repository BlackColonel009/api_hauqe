from app.services.verification_service import VerificationService


def test_open_dossier_cannot_be_reopened():
    policy = VerificationService.reopen_policy(
        is_closed=False,
        fuccs_finalized_count=0,
        validation_levels=[],
        bnec_integrated=False,
    )

    assert policy["mode"] == "DEJA_OUVERT"


def test_bnec_integration_requires_a_collection_revision():
    policy = VerificationService.reopen_policy(
        is_closed=True,
        fuccs_finalized_count=1,
        validation_levels=["NIVEAU_1", "NIVEAU_2"],
        bnec_integrated=True,
    )

    assert policy["mode"] == "REVISION_OBLIGATOIRE"
    assert "BNEC" in policy["message"]


def test_final_validation_requires_a_collection_revision():
    policy = VerificationService.reopen_policy(
        is_closed=True,
        fuccs_finalized_count=1,
        validation_levels=["NIVEAU_1"],
        bnec_integrated=False,
    )

    assert policy["mode"] == "REVISION_OBLIGATOIRE"
    assert "NIVEAU_1" in policy["message"]


def test_finalized_fuccs_requires_explicit_retake():
    policy = VerificationService.reopen_policy(
        is_closed=True,
        fuccs_finalized_count=1,
        validation_levels=[],
        bnec_integrated=False,
    )

    assert policy["mode"] == "REPRISE_FUCCS"
    assert "Brouillon" in policy["message"]


def test_closed_dossier_without_downstream_step_reopens_normally():
    policy = VerificationService.reopen_policy(
        is_closed=True,
        fuccs_finalized_count=0,
        validation_levels=[],
        bnec_integrated=False,
    )

    assert policy["mode"] == "REOUVERTURE_SIMPLE"
