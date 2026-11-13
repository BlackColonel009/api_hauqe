import pytest
from app.schemas.verification import VerificationOpenRequest


def test_opening_risk_choices_are_explicit():
    for value in ['R1','R2','R3','R4','R5']:
        assert VerificationOpenRequest(niveau_risque=value).niveau_risque==value
    with pytest.raises(ValueError):
        VerificationOpenRequest(niveau_risque='critique au hasard')
