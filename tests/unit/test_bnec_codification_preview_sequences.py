import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.repositories.validation_bnec_repository import ValidationBnecRepository
from app.services.codification_service import CodificationService


def _rule(scope):
    return SimpleNamespace(
        id=uuid4(),
        libelle="Codification des certifications",
        version="1.1",
        reference_approbation=None,
        parametres={
            "objet": "CERTIFICATION",
            "format": "{CERTIF}-{NORME}-{ANNEE4}-{SEQ3}",
            "sequence_portee": scope,
            "sequence_reinitialisation": "JAMAIS",
            "separateur": "-",
            "constantes": {"CERTIF": "CERT"},
        },
    )


def _mock_repository(monkeypatch, rule):
    async def active(_db, _object_type):
        return rule

    async def maximum(_db, *, rule_id, scope_key):
        assert rule_id == rule.id
        return 2

    async def code_exists(_db, *, object_type, code, exclude_element_id=None):
        return False

    monkeypatch.setattr(CodificationService, "active_rule", active)
    monkeypatch.setattr(ValidationBnecRepository, "max_codification_sequence", maximum)
    monkeypatch.setattr(ValidationBnecRepository, "generated_code_exists", code_exists)


def test_preview_increments_sequence_for_two_norms_in_same_scope(monkeypatch):
    rule = _rule("GLOBALE")
    _mock_repository(monkeypatch, rule)
    reserved_sequences = set()
    reserved_codes = set()

    async def preview(norm):
        item = await CodificationService.preview(
            None, object_type="CERTIFICATION",
            context={"NORME": norm, "CODE_ENTREPRISE": "ENT-001"},
            excluded_codes=reserved_codes,
            excluded_sequences=reserved_sequences,
        )
        reserved_codes.add(item.code)
        reserved_sequences.add((item.rule_id, item.scope_key, item.sequence))
        return item

    first = asyncio.run(preview("ISO22000"))
    second = asyncio.run(preview("ISO9000"))

    assert first.code.endswith("-003")
    assert second.code.endswith("-004")
    assert first.scope_key == second.scope_key


def test_preview_allows_same_sequence_in_distinct_enterprise_scopes(monkeypatch):
    rule = _rule("PAR_ENTREPRISE")
    _mock_repository(monkeypatch, rule)
    reserved_sequences = set()

    async def preview(company):
        item = await CodificationService.preview(
            None, object_type="CERTIFICATION",
            context={"NORME": "ISO22000", "CODE_ENTREPRISE": company},
            excluded_sequences=reserved_sequences,
        )
        reserved_sequences.add((item.rule_id, item.scope_key, item.sequence))
        return item

    first = asyncio.run(preview("ENT-001"))
    second = asyncio.run(preview("ENT-002"))

    assert first.sequence == second.sequence == 3
    assert first.scope_key != second.scope_key
