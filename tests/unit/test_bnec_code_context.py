import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.repositories.validation_bnec_repository import ValidationBnecRepository
from app.services.validation_bnec_service import ValidationBnecService


def test_code_context_uses_region_name_and_all_distinct_offer_categories(monkeypatch):
    async def zone_for_enterprise(_db, _entreprise):
        return (
            SimpleNamespace(code="GOLFE3", nom="Golfe 3"),
            SimpleNamespace(code="MAR", nom="Maritime"),
        )

    async def categories_for_enterprise(_db, _enterprise_id):
        return ["Agroalimentaire", "Textile", "AGROALIMENTAIRE"]

    monkeypatch.setattr(ValidationBnecService, "_region_for_enterprise", zone_for_enterprise)
    monkeypatch.setattr(
        ValidationBnecRepository,
        "list_enterprise_offer_categories",
        categories_for_enterprise,
    )
    entreprise = SimpleNamespace(
        id=uuid4(),
        raison_sociale="Entreprise exemple",
        nom_commercial=None,
        activite_principale="Ancien secteur à ignorer",
    )

    context = asyncio.run(ValidationBnecService._enterprise_code_context(None, entreprise))

    assert context["REGION"] == "Maritime"
    assert context["ZONE"] == "GOLFE3"
    assert context["SECTEUR"] == "AGROALIMENTAIREETTEXTILE"


def test_code_context_uses_region_name_even_without_code(monkeypatch):
    async def zone_for_enterprise(_db, _entreprise):
        return (SimpleNamespace(code=None, nom="Maritime"),) * 2

    async def categories_for_enterprise(_db, _enterprise_id):
        return []

    monkeypatch.setattr(ValidationBnecService, "_region_for_enterprise", zone_for_enterprise)
    monkeypatch.setattr(
        ValidationBnecRepository,
        "list_enterprise_offer_categories",
        categories_for_enterprise,
    )
    entreprise = SimpleNamespace(id=uuid4(), raison_sociale="Exemple", nom_commercial=None)

    context = asyncio.run(ValidationBnecService._enterprise_code_context(None, entreprise))

    assert context["REGION"] == "Maritime"
    assert context["SECTEUR"] == ""


def test_code_context_does_not_use_region_code_when_name_is_missing(monkeypatch):
    async def zone_for_enterprise(_db, _entreprise):
        return (SimpleNamespace(code="MAR", nom=None),) * 2

    async def categories_for_enterprise(_db, _enterprise_id):
        return []

    monkeypatch.setattr(ValidationBnecService, "_region_for_enterprise", zone_for_enterprise)
    monkeypatch.setattr(
        ValidationBnecRepository,
        "list_enterprise_offer_categories",
        categories_for_enterprise,
    )
    entreprise = SimpleNamespace(id=uuid4(), raison_sociale="Exemple", nom_commercial=None)

    context = asyncio.run(ValidationBnecService._enterprise_code_context(None, entreprise))

    assert context["REGION"] == ""
