"""
Schémas API du contrôle des doublons d'entreprises.

Le MPD représente `candidats_doublon` comme un résultat de contrôle reliant
deux entreprises. Le MCD précise qu'il ne s'agit pas d'une entité métier
centrale mais d'un contrôle de doublon historisé.

Aucune fusion automatique n'est autorisée par ces schémas.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CandidatDoublonCreateRequest(BaseModel):
    """
    Création d'un candidat de doublon.

    `examine_par_id` n'est jamais fourni par le client : le service utilise
    l'utilisateur authentifié, conformément au contrôle serveur.
    """

    entreprise_source_id: UUID
    entreprise_cible_id: UUID

    criteres_concordants: dict[str, Any] | list[str] | None = None
    score_similarite: Decimal | None = None

    # Aucun vocabulaire de statuts n'est figé ici tant qu'il n'est pas
    # officiellement validé. Le champ peut donc être fourni si nécessaire.
    statut_examen: str | None = Field(default=None, max_length=255)


class CandidatDoublonDecisionRequest(BaseModel):
    """
    Décision humaine motivée.

    La procédure HAUQE interdit de fusionner ou écarter automatiquement
    un doublon potentiel ; une décision motivée doit être enregistrée.
    """

    statut_examen: str = Field(min_length=1, max_length=255)
    decision: str = Field(min_length=1, max_length=255)
    motif_decision: str = Field(min_length=1, max_length=255)


class CandidatDoublonResponse(BaseModel):
    id: UUID

    entreprise_source_id: UUID
    entreprise_cible_id: UUID

    criteres_concordants: dict[str, Any] | list[str] | None = None
    score_similarite: Decimal | None = None

    statut_examen: str | None = None
    decision: str | None = None
    motif_decision: str | None = None

    examine_par_id: UUID
    examine_at: datetime | None = None

    created_at: datetime
    updated_at: datetime


class CandidatDoublonListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[CandidatDoublonResponse] = Field(default_factory=list)
