"""Schémas API du domaine Vérification.

La vérification intervient après une fiche SOUMISE et avant le contrôle FUCCS.
Elle ne vaut ni validation définitive ni intégration BNEC.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field

VerificationOpinion = Literal[
    "verified_compliant",
    "verified_with_reservation",
    "not_verified",
    "suspect",
    "rejected",
]

class VerificationOpenRequest(BaseModel):
    priorite: str | None = Field(default=None, max_length=255)
    niveau_risque: str | None = Field(default=None, max_length=255)

class VerificationUpdateRequest(BaseModel):
    priorite: str | None = Field(default=None, max_length=255)
    niveau_risque: str | None = Field(default=None, max_length=255)
    synthese: str | None = None

class VerificationCloseRequest(BaseModel):
    avis: VerificationOpinion
    synthese: str = Field(min_length=1)
    niveau_risque: str | None = Field(default=None, max_length=255)

class VerificationReopenRequest(BaseModel):
    motif: str = Field(min_length=1, max_length=2000)

class VerificationDossierResponse(BaseModel):
    id: UUID
    fiche_collecte_id: UUID
    date_ouverture: date | None = None
    date_fin: date | None = None
    statut: str | None = None
    avis: str | None = None
    synthese: str | None = None
    niveau_risque: str | None = None
    priorite: str | None = None
    points_count: int = 0
    anomalies_count: int = 0
    confirmations_pending_count: int = 0
    affectations_count: int = 0
    created_at: datetime
    updated_at: datetime

class VerificationDossierListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[VerificationDossierResponse] = Field(default_factory=list)


class VerificationOption(BaseModel):
    id: UUID
    label: str
    code: str | None = None

class VerificationWorkspaceFiltersResponse(BaseModel):
    statuses: list[str] = Field(default_factory=list)
    opinions: list[str] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    verifiers: list[VerificationOption] = Field(default_factory=list)

class VerificationRegistryItem(BaseModel):
    dossier_id: UUID
    fiche_collecte_id: UUID
    dossier_status: str | None = None
    opinion: str | None = None
    priority: str | None = None
    risk_level: str | None = None
    opened_on: date | None = None
    closed_on: date | None = None
    mission_id: UUID
    mission_code: str | None = None
    campaign_code: str | None = None
    campaign_name: str | None = None
    zone_name: str | None = None
    entreprise_id: UUID | None = None
    entreprise_name: str | None = None
    entreprise_identifiant: str | None = None
    fiche_status: str | None = None
    fiche_revision: int | None = None
    completeness: float | None = None
    submitted_at: datetime | None = None
    points_count: int = 0
    anomalies_count: int = 0
    unresolved_anomalies_count: int = 0
    confirmations_pending_count: int = 0
    assignments_count: int = 0
    assigned_names: str | None = None
    documents_count: int = 0

class VerificationRegistrySummary(BaseModel):
    total: int = 0
    open: int = 0
    finished: int = 0
    unassigned: int = 0
    with_unresolved_anomalies: int = 0
    with_pending_confirmations: int = 0

class VerificationRegistryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    summary: VerificationRegistrySummary
    items: list[VerificationRegistryItem] = Field(default_factory=list)

class VerificationEligibleFicheItem(BaseModel):
    fiche_id: UUID
    mission_id: UUID
    mission_code: str | None = None
    campaign_code: str | None = None
    campaign_name: str | None = None
    zone_name: str | None = None
    entreprise_id: UUID | None = None
    entreprise_name: str | None = None
    entreprise_identifiant: str | None = None
    fiche_revision: int | None = None
    completeness: float | None = None
    submitted_at: datetime | None = None

class VerificationEligibleFichesResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[VerificationEligibleFicheItem] = Field(default_factory=list)

class VerificationAssignmentCreateRequest(BaseModel):
    verificateur_id: UUID
    date_debut: date | None = None
    date_fin: date | None = None
    date_echeance: date | None = None
    motif: str | None = None
    statut: str | None = Field(default="ACTIF", max_length=255)

class VerificationAssignmentUpdateRequest(BaseModel):
    date_debut: date | None = None
    date_fin: date | None = None
    date_echeance: date | None = None
    motif: str | None = None
    statut: str | None = Field(default=None, max_length=255)

class VerificationAssignmentResponse(BaseModel):
    id: UUID
    dossier_verification_id: UUID
    verificateur_id: UUID
    date_debut: date | None = None
    date_fin: date | None = None
    date_echeance: date | None = None
    motif: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime

class VerificationPointCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=255)
    libelle: str = Field(min_length=1, max_length=255)
    categorie: str | None = Field(default=None, max_length=255)
    resultat: str = Field(min_length=1)
    observation: str | None = None
    preuve_document_id: UUID | None = None

class VerificationPointUpdateRequest(BaseModel):
    libelle: str | None = Field(default=None, max_length=255)
    categorie: str | None = Field(default=None, max_length=255)
    resultat: str | None = None
    observation: str | None = None
    preuve_document_id: UUID | None = None

class VerificationPointResponse(BaseModel):
    id: UUID
    dossier_verification_id: UUID
    code: str | None = None
    libelle: str | None = None
    categorie: str | None = None
    resultat: str | None = None
    observation: str | None = None
    date_verification: date | None = None
    preuve_document_id: UUID | None = None
    verifie_par_id: UUID
    created_at: datetime
    updated_at: datetime

class VerificationAnomalyCreateRequest(BaseModel):
    point_verification_id: UUID | None = None
    categorie: str | None = Field(default=None, max_length=255)
    gravite: str | None = Field(default=None, max_length=255)
    description: str = Field(min_length=1)
    statut: str | None = Field(default="OUVERTE", max_length=255)
    escalade: bool = False

class VerificationAnomalyUpdateRequest(BaseModel):
    categorie: str | None = Field(default=None, max_length=255)
    gravite: str | None = Field(default=None, max_length=255)
    description: str | None = None
    statut: str | None = Field(default=None, max_length=255)
    escalade: bool | None = None

class VerificationAnomalyResolveRequest(BaseModel):
    resolution: str = Field(min_length=1)
    statut: str = Field(default="RESOLUE", min_length=1, max_length=255)

class VerificationAnomalyEscalateRequest(BaseModel):
    motif: str = Field(min_length=1, max_length=2000)

class VerificationAnomalyResponse(BaseModel):
    id: UUID
    dossier_verification_id: UUID
    point_verification_id: UUID | None = None
    categorie: str | None = None
    gravite: str | None = None
    description: str | None = None
    statut: str | None = None
    resolution: str | None = None
    date_resolution: date | None = None
    escalade: bool | None = None
    created_at: datetime
    updated_at: datetime

class ExternalConfirmationCreateRequest(BaseModel):
    organisme_id: UUID | None = None
    canal: str | None = Field(default=None, max_length=255)
    destinataire: str = Field(min_length=1, max_length=255)
    objet: str = Field(min_length=1, max_length=255)
    contenu_demande: str = Field(min_length=1)
    date_envoi: date | None = None
    date_echeance: date | None = None
    statut: str | None = Field(default="EN_ATTENTE", max_length=255)

class ExternalConfirmationUpdateRequest(BaseModel):
    organisme_id: UUID | None = None
    canal: str | None = Field(default=None, max_length=255)
    destinataire: str | None = Field(default=None, max_length=255)
    objet: str | None = Field(default=None, max_length=255)
    contenu_demande: str | None = None
    date_envoi: date | None = None
    date_echeance: date | None = None
    statut: str | None = Field(default=None, max_length=255)

class ExternalConfirmationResponseRequest(BaseModel):
    date_reponse: date | None = None
    contenu_reponse: str = Field(min_length=1)
    resultat: str | None = None
    document_id: UUID | None = None
    statut: str | None = Field(default="REPONDU", max_length=255)

class ExternalConfirmationResponse(BaseModel):
    id: UUID
    dossier_verification_id: UUID
    organisme_id: UUID | None = None
    canal: str | None = None
    destinataire: str | None = None
    objet: str | None = None
    contenu_demande: str | None = None
    date_envoi: date | None = None
    date_echeance: date | None = None
    date_reponse: date | None = None
    contenu_reponse: str | None = None
    resultat: str | None = None
    document_id: UUID | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime
