import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.models.contact_entreprise import ContactEntreprise
from app.repositories.validation_bnec_repository import ValidationBnecRepository
from app.services import integration_enrichment_service as module
from app.services.integration_enrichment_service import IntegrationEnrichmentService


class _Rows:
    def __init__(self, items):
        self.items = items

    def scalars(self):
        return self

    def all(self):
        return self.items


class _Db:
    def __init__(self, contacts):
        self.contacts = contacts
        self.added = []

    async def execute(self, _query):
        return _Rows(self.contacts)

    def add(self, item):
        self.added.append(item)
        if isinstance(item, ContactEntreprise):
            self.contacts.append(item)

    async def flush(self):
        for item in self.added:
            if item.id is None:
                item.id = uuid4()


def test_old_collection_completes_only_empty_enterprise_and_contact_fields(monkeypatch):
    async def offers(_db, _fiche_id):
        return [SimpleNamespace(id=uuid4(), description="Transformation de céréales", statut="ACTIF")]

    audits = []

    async def audit(_db, **kwargs):
        audits.append(kwargs)

    monkeypatch.setattr(ValidationBnecRepository, "list_declared_offers", offers)
    monkeypatch.setattr(module, "write_audit_event", audit)
    contact = SimpleNamespace(
        id=uuid4(), nom="Akou", fonction=None, telephone=None,
        email="akou@example.tg", type_contact="DECLARANT_COLLECTE",
    )
    db = _Db([contact])
    fiche = SimpleNamespace(
        id=uuid4(), nom_declarant="Akou", fonction_declarant="Directrice",
        telephone_declarant="90000000", email_declarant="akou@example.tg",
    )
    entreprise = SimpleNamespace(id=uuid4(), activite_principale=None)

    first = asyncio.run(IntegrationEnrichmentService.apply_enterprise(
        db, fiche=fiche, entreprise=entreprise,
        actor_id=uuid4(), integration_id=uuid4(),
    ))
    second = asyncio.run(IntegrationEnrichmentService.apply_enterprise(
        db, fiche=fiche, entreprise=entreprise,
        actor_id=uuid4(), integration_id=uuid4(),
    ))

    assert len(first) == 2
    assert second == []
    assert entreprise.activite_principale == "Transformation de céréales"
    assert contact.nom == "Akou"
    assert contact.fonction == "Directrice"
    assert contact.telephone == "90000000"
    assert contact.email == "akou@example.tg"
    assert len(audits) == 2
    assert db.added == []


def test_ambiguous_offers_do_not_invent_main_activity(monkeypatch):
    async def offers(_db, _fiche_id):
        return [
            SimpleNamespace(id=uuid4(), description="Produit A", statut="ACTIF"),
            SimpleNamespace(id=uuid4(), description="Produit B", statut="ACTIF"),
        ]

    monkeypatch.setattr(ValidationBnecRepository, "list_declared_offers", offers)
    db = _Db([])
    fiche = SimpleNamespace(
        id=uuid4(), nom_declarant=None, fonction_declarant=None,
        telephone_declarant=None, email_declarant=None,
    )
    entreprise = SimpleNamespace(id=uuid4(), activite_principale=None)

    plan = asyncio.run(IntegrationEnrichmentService.plan_enterprise(
        db, fiche=fiche, entreprise=entreprise,
    ))

    assert plan.descriptions() == []
    assert entreprise.activite_principale is None


def test_old_declarant_contact_is_created_once_without_changing_company_email(monkeypatch):
    async def offers(_db, _fiche_id):
        return []

    async def audit(_db, **_kwargs):
        return None

    monkeypatch.setattr(ValidationBnecRepository, "list_declared_offers", offers)
    monkeypatch.setattr(module, "write_audit_event", audit)
    db = _Db([])
    fiche = SimpleNamespace(
        id=uuid4(), nom_declarant="M. Kofi", fonction_declarant="Responsable qualité",
        telephone_declarant="90112233", email_declarant="kofi@example.tg",
    )
    entreprise = SimpleNamespace(
        id=uuid4(), activite_principale="Industrie", email_principal="direction@example.tg",
    )

    first = asyncio.run(IntegrationEnrichmentService.apply_enterprise(
        db, fiche=fiche, entreprise=entreprise,
        actor_id=uuid4(), integration_id=uuid4(),
    ))
    second = asyncio.run(IntegrationEnrichmentService.apply_enterprise(
        db, fiche=fiche, entreprise=entreprise,
        actor_id=uuid4(), integration_id=uuid4(),
    ))

    assert len(first) == 1
    assert second == []
    assert len(db.contacts) == 1
    assert db.contacts[0].email == "kofi@example.tg"
    assert entreprise.email_principal == "direction@example.tg"


def test_organism_name_is_filled_only_when_empty(monkeypatch):
    audits = []

    async def audit(_db, **kwargs):
        audits.append(kwargs)

    monkeypatch.setattr(module, "write_audit_event", audit)
    source = SimpleNamespace(id=uuid4(), organisme_declare="Certificateur Exemple")
    organisme = SimpleNamespace(id=uuid4(), nom_officiel=None, statut="A_VERIFIER")

    first = asyncio.run(IntegrationEnrichmentService.apply_organism_name(
        None, source=source, organisme=organisme,
        actor_id=uuid4(), integration_id=uuid4(),
    ))
    second = asyncio.run(IntegrationEnrichmentService.apply_organism_name(
        None, source=source, organisme=organisme,
        actor_id=uuid4(), integration_id=uuid4(),
    ))

    assert first is True
    assert second is False
    assert organisme.nom_officiel == "Certificateur Exemple"
    assert organisme.statut == "A_VERIFIER"
    assert len(audits) == 1
