from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, select

from app.models.entreprise import Entreprise
from app.schemas.contact_entreprise import ContactEntrepriseCreateRequest, ContactEntrepriseUpdateRequest


def test_gender_is_optional_and_strict():
    assert ContactEntrepriseCreateRequest(nom="Marie").genre is None
    assert ContactEntrepriseCreateRequest(genre="FEMME").genre == "FEMME"
    assert ContactEntrepriseUpdateRequest(genre=None).model_dump(exclude_unset=True) == {"genre": None}
    assert "genre" not in ContactEntrepriseUpdateRequest(nom="Nom").model_dump(exclude_unset=True)
    with pytest.raises(ValidationError):
        ContactEntrepriseCreateRequest(genre="valeur inconnue")


def test_promoter_is_first_active_contact_not_first_known_gender():
    engine = create_engine("sqlite://")
    a, b, c = [uuid4() for _ in range(3)]
    with engine.begin() as db:
        db.exec_driver_sql("CREATE TABLE entreprises (id TEXT PRIMARY KEY)")
        db.exec_driver_sql("CREATE TABLE contacts_entreprise (id TEXT PRIMARY KEY, entreprise_id TEXT, genre TEXT, statut TEXT, created_at TEXT)")
        for identifier in (a,b,c):
            db.exec_driver_sql("INSERT INTO entreprises VALUES (?)", (identifier.hex,))
        for company, date, gender, status in [
            (a,"2026-01-01",None,"ACTIF"), (a,"2026-02-01","FEMME","ACTIF"),
            (b,"2026-01-01","HOMME","INACTIF"), (b,"2026-02-01","FEMME","ACTIF"),
        ]:
            db.exec_driver_sql("INSERT INTO contacts_entreprise VALUES (?,?,?,?,?)",
                               (uuid4().hex, company.hex, gender, status, date))
        result = dict(db.execute(select(Entreprise.id, Entreprise.genre_promoteur)).all())
        assert result[a] is None
        assert result[b] == "FEMME"
        assert result[c] is None
