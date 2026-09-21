"""Schémas du parcours opérationnel d'un dossier de collecte."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


ParcoursStatut = Literal["TERMINE", "EN_COURS", "A_FAIRE", "BLOQUE"]


class ParcoursEtapeResponse(BaseModel):
    code: str
    libelle: str
    statut: ParcoursStatut
    detail: str
    ressource_id: UUID | None = None


class ParcoursDossierResponse(BaseModel):
    fiche_collecte_id: UUID
    etapes: list[ParcoursEtapeResponse] = Field(default_factory=list)
    prochaine_action: str
    etapes_restantes: int = 0
    bloque: bool = False
