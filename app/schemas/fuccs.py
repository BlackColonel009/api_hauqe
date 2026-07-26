"""Schémas API du domaine FUCCS.

Le backend ne code en dur ni le nombre de critères ni le score maximal global.
La page frontend doit charger la grille active et ses critères.
"""
from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field

class FuccsGridCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=255)
    libelle: str = Field(min_length=1, max_length=255)
    version: str = Field(min_length=1, max_length=255)
    date_effet: date | None = None

class FuccsGridUpdateRequest(BaseModel):
    libelle: str | None = Field(default=None, max_length=255)
    version: str | None = Field(default=None, max_length=255)
    date_effet: date | None = None

class FuccsGridPublishRequest(BaseModel):
    date_effet: date
    reference_approbation: str = Field(min_length=1, max_length=255)

class FuccsGridRetireRequest(BaseModel):
    date_fin: date
    motif: str = Field(min_length=1, max_length=2000)

class FuccsGridCloneRequest(BaseModel):
    code: str = Field(min_length=1, max_length=255)
    libelle: str = Field(min_length=1, max_length=255)
    version: str = Field(min_length=1, max_length=255)
    date_effet: date | None = None

class FuccsGridResponse(BaseModel):
    id: UUID
    code: str | None = None
    libelle: str | None = None
    version: str | None = None
    date_effet: date | None = None
    date_fin: date | None = None
    reference_approbation: str | None = None
    statut_publication: str | None = None
    rubriques_count: int = 0
    criteres_count: int = 0
    score_maximal_calcule: Decimal = Decimal("0")
    created_at: datetime
    updated_at: datetime

class FuccsRubricCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=255)
    libelle: str = Field(min_length=1, max_length=255)
    description: str | None = None
    ordre_affichage: int | None = None

class FuccsRubricUpdateRequest(BaseModel):
    code: str | None = Field(default=None, max_length=255)
    libelle: str | None = Field(default=None, max_length=255)
    description: str | None = None
    ordre_affichage: int | None = None

class FuccsRubricResponse(BaseModel):
    id: UUID
    grille_fuccs_id: UUID
    code: str | None = None
    libelle: str | None = None
    description: str | None = None
    ordre_affichage: int | None = None
    created_at: datetime
    updated_at: datetime

class FuccsCriterionCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=255)
    libelle: str = Field(min_length=1, max_length=255)
    description: str | None = None
    score_maximal: Decimal = Field(gt=0)
    poids: Decimal | None = Field(default=None, ge=0)
    ordre_affichage: int | None = None
    commentaire_obligatoire: bool = False
    preuve_obligatoire: bool = False

class FuccsCriterionUpdateRequest(BaseModel):
    code: str | None = Field(default=None, max_length=255)
    libelle: str | None = Field(default=None, max_length=255)
    description: str | None = None
    score_maximal: Decimal | None = Field(default=None, gt=0)
    poids: Decimal | None = Field(default=None, ge=0)
    ordre_affichage: int | None = None
    commentaire_obligatoire: bool | None = None
    preuve_obligatoire: bool | None = None

class FuccsCriterionResponse(BaseModel):
    id: UUID
    rubrique_fuccs_id: UUID
    code: str | None = None
    libelle: str | None = None
    description: str | None = None
    score_maximal: Decimal | None = None
    poids: Decimal | None = None
    ordre_affichage: int | None = None
    commentaire_obligatoire: bool | None = None
    preuve_obligatoire: bool | None = None
    created_at: datetime
    updated_at: datetime

class FuccsControlCreateRequest(BaseModel):
    grille_fuccs_id: UUID | None = None

class FuccsControlResponse(BaseModel):
    id: UUID
    dossier_verification_id: UUID
    grille_fuccs_id: UUID
    controleur_id: UUID
    date_debut: date | None = None
    date_fin: date | None = None
    score_brut: Decimal | None = None
    score_maximal: Decimal | None = None
    taux: str | None = None
    synthese: str | None = None
    statut: str | None = None
    notes_count: int = 0
    criteres_count: int = 0
    constats_count: int = 0
    created_at: datetime
    updated_at: datetime

class FuccsControlListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[FuccsControlResponse] = Field(default_factory=list)

class FuccsNoteUpsertRequest(BaseModel):
    score: Decimal = Field(ge=0)
    commentaire: str | None = None
    preuve_document_id: UUID | None = None

class FuccsNoteResponse(BaseModel):
    id: UUID
    controle_fuccs_id: UUID
    critere_fuccs_id: UUID
    score: Decimal | None = None
    commentaire: str | None = None
    preuve_document_id: UUID | None = None
    note_par_id: UUID
    created_at: datetime
    updated_at: datetime

class FuccsFindingCreateRequest(BaseModel):
    type_constat: str | None = Field(default=None, max_length=255)
    gravite: str | None = Field(default=None, max_length=255)
    titre: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    statut: str | None = Field(default="OUVERT", max_length=255)

class FuccsFindingUpdateRequest(BaseModel):
    type_constat: str | None = Field(default=None, max_length=255)
    gravite: str | None = Field(default=None, max_length=255)
    titre: str | None = Field(default=None, max_length=255)
    description: str | None = None
    statut: str | None = Field(default=None, max_length=255)

class FuccsFindingResponse(BaseModel):
    id: UUID
    controle_fuccs_id: UUID
    type_constat: str | None = None
    gravite: str | None = None
    titre: str | None = None
    description: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime

class FuccsFinalizeRequest(BaseModel):
    synthese: str = Field(min_length=1)

class FuccsReopenRequest(BaseModel):
    motif: str = Field(min_length=1, max_length=2000)
