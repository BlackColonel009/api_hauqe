from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.entreprise import (
    EntrepriseCreateRequest,
    EntrepriseResponse,
    EntrepriseUpdateRequest,
)


def test_company_schemas_accept_other_legal_identifier():
    value = "REG-ADMIN-2026-0042"

    create = EntrepriseCreateRequest(
        identifiant_national="HAUQE-ENT-2026-0001",
        zone_siege_id=uuid4(),
        autre_identifiant_juridique=value,
    )
    update = EntrepriseUpdateRequest(
        autre_identifiant_juridique=value,
    )
    response = EntrepriseResponse(
        id=uuid4(),
        identifiant_national="HAUQE-ENT-2026-0001",
        zone_siege_id=uuid4(),
        autre_identifiant_juridique=value,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert create.autre_identifiant_juridique == value
    assert update.autre_identifiant_juridique == value
    assert response.autre_identifiant_juridique == value
