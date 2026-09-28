import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService


def test_fiche_lists_general_and_two_distinct_certification_proofs(monkeypatch):
    fiche_id = uuid4()
    first_id, second_id, official_id = uuid4(), uuid4(), uuid4()
    declarations = [
        SimpleNamespace(
            id=first_id,
            certification_officielle_id=official_id,
            nom_certification="Certificat qualité",
            norme_declaree="ISO 9001",
            numero="A-001",
        ),
        SimpleNamespace(
            id=second_id,
            certification_officielle_id=None,
            nom_certification="Certificat sécurité",
            norme_declaree="ISO 45001",
            numero="B-002",
        ),
    ]

    def document(resource_type, resource_id, filename):
        now = datetime.now(timezone.utc)
        return Document(
            id=uuid4(),
            ressource_type=resource_type,
            ressource_id=resource_id,
            nom_original=filename,
            created_at=now,
            updated_at=now,
        )

    rows = [
        document("FICHE_COLLECTE", fiche_id, "fiche.pdf"),
        document("CERTIFICATION_DECLAREE", first_id, "qualite.pdf"),
        document("CERTIFICATION_DECLAREE", second_id, "securite.pdf"),
        document("CERTIFICATION", official_id, "preuve-integree.pdf"),
    ]

    async def list_for_fiche(_db, _fiche_id, *, limit, offset):
        assert _fiche_id == fiche_id
        assert limit == 200 and offset == 0
        return rows, declarations, len(rows)

    monkeypatch.setattr(DocumentRepository, "list_for_fiche", list_for_fiche)
    result = asyncio.run(DocumentService.list_for_fiche(
        None, fiche_id=fiche_id, limit=200, offset=0
    ))

    assert result.total == 4
    assert len({item.id for item in result.items}) == 4
    assert result.items[0].contexte_documentaire == "Justificatif général de la fiche"
    assert result.items[1].contexte_documentaire == "Certificat qualité — n° A-001"
    assert result.items[2].contexte_documentaire == "Certificat sécurité — n° B-002"
    assert result.items[3].contexte_documentaire == "Certificat qualité — n° A-001"


def test_fiche_query_covers_general_declared_and_integrated_documents():
    fiche_id, declared_id, official_id = uuid4(), uuid4(), uuid4()
    declaration = SimpleNamespace(
        id=declared_id, certification_officielle_id=official_id
    )

    class Result:
        def __init__(self, value):
            self.value = value

        def scalars(self):
            return self

        def all(self):
            return self.value

        def scalar_one(self):
            return self.value

    class DB:
        def __init__(self):
            self.statements = []

        async def execute(self, statement):
            self.statements.append(statement)
            return Result([[declaration], [], 0][len(self.statements) - 1])

    db = DB()
    asyncio.run(DocumentRepository.list_for_fiche(db, fiche_id, limit=200, offset=0))
    documents_query = db.statements[1].compile(
        compile_kwargs={"literal_binds": True}
    )
    sql = str(documents_query)

    assert "FICHE_COLLECTE" in sql
    assert "CERTIFICATION_DECLAREE" in sql
    assert "CERTIFICATION" in sql
    assert fiche_id.hex in sql
    assert declared_id.hex in sql
    assert official_id.hex in sql
    assert "ACTIF" in sql


def test_enterprise_document_query_includes_declared_and_official_proofs():
    enterprise_id = uuid4()

    class Result:
        def all(self):
            return []

    class DB:
        statement = None

        async def execute(self, statement):
            self.statement = statement
            return Result()

    db = DB()
    asyncio.run(DocumentRepository.list_for_entreprise(db, enterprise_id))
    sql = str(db.statement.compile(compile_kwargs={"literal_binds": True}))

    assert "certifications_declarees" in sql
    assert "certifications" in sql
    assert "fiches_collecte" in sql
    assert enterprise_id.hex in sql
    assert "ACTIF" in sql
