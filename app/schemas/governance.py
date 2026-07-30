"""
Schémas API — Gouvernance / Qualité / Continuité.

Sous-domaines :
- règles métier versionnées ;
- revues qualité ;
- plans d'action ;
- décisions institutionnelles ;
- publications ;
- rapports générés ;
- journal d'audit en lecture seule ;
- archives ;
- sauvegardes ;
- incidents.

Aucune suppression physique n'est exposée.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# RÈGLES MÉTIER
# ============================================================

class BusinessRuleCreateRequest(BaseModel):
    logical_code: str = Field(min_length=1, max_length=200)
    famille: str | None = Field(default=None, max_length=255)
    libelle: str = Field(min_length=1, max_length=255)
    description: str | None = None
    version: str = Field(min_length=1, max_length=100)
    parametres: dict[str, Any] = Field(default_factory=dict)
    date_debut_effet: date | None = None


class BusinessRuleUpdateRequest(BaseModel):
    famille: str | None = Field(default=None, max_length=255)
    libelle: str | None = Field(default=None, max_length=255)
    description: str | None = None
    parametres: dict[str, Any] | None = None
    date_debut_effet: date | None = None


class BusinessRuleCloneRequest(BaseModel):
    version: str = Field(min_length=1, max_length=100)
    libelle: str | None = Field(default=None, max_length=255)
    date_debut_effet: date | None = None


class BusinessRulePublishRequest(BaseModel):
    reference_approbation: str = Field(min_length=1, max_length=255)
    date_debut_effet: date
    commentaire: str | None = Field(default=None, max_length=2000)


class BusinessRuleRetireRequest(BaseModel):
    date_fin_effet: date
    motif: str = Field(min_length=1, max_length=2000)


class BusinessRuleResponse(BaseModel):
    id: UUID
    code: str
    logical_code: str
    famille: str | None = None
    libelle: str | None = None
    description: str | None = None
    version: str | None = None
    parametres: dict[str, Any] | None = None
    date_debut_effet: date | None = None
    date_fin_effet: date | None = None
    reference_approbation: str | None = None
    approuve_par_id: UUID | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# REVUES QUALITÉ / PLANS D'ACTION
# ============================================================

class QualityReviewCreateRequest(BaseModel):
    periode_debut: str = Field(min_length=10, max_length=255)
    periode_fin: str = Field(min_length=10, max_length=255)
    perimetre: str = Field(min_length=1)
    resultat_global: str | None = Field(default=None, max_length=255)
    constats: dict[str, Any] = Field(default_factory=dict)
    preuves: dict[str, Any] = Field(default_factory=dict)
    responsable_id: UUID


class QualityReviewUpdateRequest(BaseModel):
    periode_debut: str | None = Field(default=None, max_length=255)
    periode_fin: str | None = Field(default=None, max_length=255)
    perimetre: str | None = None
    resultat_global: str | None = Field(default=None, max_length=255)
    constats: dict[str, Any] | None = None
    preuves: dict[str, Any] | None = None
    responsable_id: UUID | None = None


class QualityReviewValidateRequest(BaseModel):
    resultat_global: str = Field(min_length=1, max_length=255)
    commentaire: str | None = Field(default=None, max_length=2000)


class QualityReviewResponse(BaseModel):
    id: UUID
    periode_debut: str | None = None
    periode_fin: str | None = None
    perimetre: str | None = None
    resultat_global: str | None = None
    constats: dict[str, Any] | None = None
    preuves: dict[str, Any] | None = None
    responsable_id: UUID
    date_validation: date | None = None
    statut: str | None = None
    plans_action_count: int = 0
    created_at: datetime
    updated_at: datetime


class QualityReviewListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[QualityReviewResponse] = Field(default_factory=list)


class ActionPlanCreateRequest(BaseModel):
    revue_qualite_id: UUID | None = None
    titre: str = Field(min_length=1, max_length=255)
    objectif: str = Field(min_length=1, max_length=255)
    responsable_id: UUID
    date_debut: date | None = None
    date_echeance: date
    priorite: str | None = Field(default=None, max_length=255)
    indicateur: str = Field(min_length=1, max_length=255)


class ActionPlanUpdateRequest(BaseModel):
    titre: str | None = Field(default=None, max_length=255)
    objectif: str | None = Field(default=None, max_length=255)
    responsable_id: UUID | None = None
    date_debut: date | None = None
    date_echeance: date | None = None
    priorite: str | None = Field(default=None, max_length=255)
    indicateur: str | None = Field(default=None, max_length=255)


class ActionPlanProgressRequest(BaseModel):
    progression: int = Field(ge=0, le=100)
    commentaire: str | None = Field(default=None, max_length=2000)


class ActionPlanCloseRequest(BaseModel):
    resultat: str = Field(min_length=1, max_length=2000)


class ActionPlanResponse(BaseModel):
    id: UUID
    revue_qualite_id: UUID | None = None
    titre: str | None = None
    objectif: str | None = None
    responsable_id: UUID
    date_debut: date | None = None
    date_echeance: date | None = None
    priorite: str | None = None
    indicateur: str | None = None
    progression: int | None = None
    date_cloture: date | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# DÉCISIONS INSTITUTIONNELLES
# ============================================================

class ActionPlanListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ActionPlanResponse] = Field(default_factory=list)


class InstitutionalDecisionCreateRequest(BaseModel):
    ressource_type: str = Field(min_length=1, max_length=255)
    ressource_id: UUID
    type_decision: str = Field(min_length=1, max_length=255)
    titre: str = Field(min_length=1, max_length=255)
    contexte: str = Field(min_length=1)
    constats: dict[str, Any] = Field(default_factory=dict)
    risques: str | None = Field(default=None, max_length=255)
    options: str | None = Field(default=None, max_length=255)
    recommandation: str | None = Field(default=None, max_length=255)
    autorite: str | None = Field(default=None, max_length=255)
    priorite: str | None = Field(default=None, max_length=255)


class InstitutionalDecisionUpdateRequest(BaseModel):
    titre: str | None = Field(default=None, max_length=255)
    contexte: str | None = None
    constats: dict[str, Any] | None = None
    risques: str | None = Field(default=None, max_length=255)
    options: str | None = Field(default=None, max_length=255)
    recommandation: str | None = Field(default=None, max_length=255)
    autorite: str | None = Field(default=None, max_length=255)
    priorite: str | None = Field(default=None, max_length=255)


class InstitutionalDecisionSubmitRequest(BaseModel):
    commentaire: str | None = Field(default=None, max_length=2000)


class InstitutionalDecisionPronounceRequest(BaseModel):
    decision: str = Field(min_length=1, max_length=255)
    justification: str = Field(min_length=1)


class InstitutionalDecisionResponse(BaseModel):
    id: UUID
    ressource_type: str | None = None
    ressource_id: UUID | None = None
    type_decision: str | None = None
    titre: str | None = None
    contexte: str | None = None
    constats: dict[str, Any] | None = None
    risques: str | None = None
    options: str | None = None
    decision: str | None = None
    recommandation: str | None = None
    autorite: str | None = None
    decide_par_id: UUID | None = None
    date_decision: date | None = None
    priorite: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# PUBLICATIONS
# ============================================================

class InstitutionalDecisionListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[InstitutionalDecisionResponse] = Field(default_factory=list)


class PublicationCreateRequest(BaseModel):
    ressource_type: str = Field(min_length=1, max_length=255)
    ressource_id: UUID
    objet: str = Field(min_length=1, max_length=255)
    perimetre: str = Field(min_length=1)
    niveau_confidentialite: str = Field(min_length=1, max_length=255)


class PublicationSubmitRequest(BaseModel):
    commentaire: str | None = Field(default=None, max_length=2000)


class PublicationApprovalRequest(BaseModel):
    decision: Literal["APPROUVE", "REJETE"]
    autorite_approbation: str = Field(min_length=1, max_length=255)
    reserve: str | None = Field(default=None, max_length=255)


class PublicationPublishRequest(BaseModel):
    date_publication: date | None = None
    commentaire: str | None = Field(default=None, max_length=2000)


class PublicationRetireRequest(BaseModel):
    motif: str = Field(min_length=1, max_length=2000)


class PublicationResponse(BaseModel):
    id: UUID
    ressource_type: str | None = None
    ressource_id: UUID | None = None
    objet: str | None = None
    perimetre: str | None = None
    niveau_confidentialite: str | None = None
    demande_par_id: UUID
    date_demande: date | None = None
    decision: str | None = None
    autorite_approbation: str | None = None
    approuve_par_id: UUID | None = None
    date_approbation: date | None = None
    reserve: str | None = None
    date_publication: date | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# RAPPORTS GÉNÉRÉS
# ============================================================

class PublicationListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[PublicationResponse] = Field(default_factory=list)


class ReportRequestCreate(BaseModel):
    code_modele: str = Field(min_length=1, max_length=255)
    nom_modele: str = Field(min_length=1, max_length=255)
    categorie: str = Field(min_length=1, max_length=255)
    filtres: dict[str, Any] = Field(default_factory=dict)
    sections: dict[str, Any] = Field(default_factory=dict)
    format: Literal["PDF", "XLSX", "CSV"]
    periode_debut: str | None = Field(default=None, max_length=255)
    periode_fin: str | None = Field(default=None, max_length=255)


class ReportStartRequest(BaseModel):
    commentaire: str | None = Field(default=None, max_length=2000)


class ReportCompleteRequest(BaseModel):
    document_id: UUID
    resultat: str | None = None


class ReportFailRequest(BaseModel):
    resultat: str = Field(min_length=1)


class GeneratedReportResponse(BaseModel):
    id: UUID
    code_modele: str | None = None
    nom_modele: str | None = None
    categorie: str | None = None
    demandeur_id: UUID
    filtres: dict[str, Any] | None = None
    sections: dict[str, Any] | None = None
    format: str | None = None
    periode_debut: str | None = None
    periode_fin: str | None = None
    date_demande: date | None = None
    date_generation: date | None = None
    document_id: UUID | None = None
    resultat: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class GeneratedReportListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[GeneratedReportResponse] = Field(default_factory=list)


# ============================================================
# JOURNAL D'AUDIT# ============================================================
# JOURNAL D'AUDIT
# ============================================================

class AuditEventResponse(BaseModel):
    id: UUID
    utilisateur_id: UUID | None = None
    utilisateur_nom: str | None = None
    utilisateur_email: str | None = None
    action: str | None = None
    categorie: str | None = None
    ressource_type: str | None = None
    ressource_id: UUID | None = None
    adresse_ip: str | None = None
    contexte: str | None = None
    valeurs_avant: dict[str, Any] | None = None
    valeurs_apres: dict[str, Any] | None = None
    empreinte: str | None = None
    resultat: str | None = None
    date_evenement: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AuditEventListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[AuditEventResponse] = Field(default_factory=list)


# ============================================================
# ARCHIVES
# ============================================================

class ArchiveCreateRequest(BaseModel):
    ressource_type: str = Field(min_length=1, max_length=255)
    ressource_id: UUID
    categorie_donnees: str = Field(min_length=1, max_length=255)
    motif: str = Field(min_length=1)
    duree_conservation: str | None = Field(default=None, max_length=255)
    date_suppression_prevue: date | None = None
    emplacement: str | None = Field(default=None, max_length=255)


class ArchiveResponse(BaseModel):
    id: UUID
    ressource_type: str | None = None
    ressource_id: UUID | None = None
    categorie_donnees: str | None = None
    date_archivage: datetime | None = None
    motif: str | None = None
    auteur_id: UUID
    duree_conservation: str | None = None
    date_suppression_prevue: date | None = None
    emplacement: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class ArchiveListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ArchiveResponse] = Field(default_factory=list)


# ============================================================
# SAUVEGARDES / TESTS DE RESTAURATION# ============================================================
# SAUVEGARDES / TESTS DE RESTAURATION
# ============================================================

class BackupPolicyCreateRequest(BaseModel):
    frequence: str = Field(min_length=1, max_length=255)
    retention: str = Field(min_length=1, max_length=255)
    perimetre: str = Field(min_length=1)
    emplacement_stockage: str = Field(min_length=1, max_length=255)


class BackupPolicyUpdateRequest(BaseModel):
    frequence: str | None = Field(default=None, max_length=255)
    retention: str | None = Field(default=None, max_length=255)
    perimetre: str | None = None
    emplacement_stockage: str | None = Field(default=None, max_length=255)


class BackupRunCreateRequest(BaseModel):
    date_debut: date | None = None


class BackupRunCompleteRequest(BaseModel):
    date_fin: date | None = None
    taille_octets: int | None = Field(default=None, ge=0)
    integrite_validee: bool
    resultat: str = Field(min_length=1)
    preuve_document_id: UUID | None = None


class BackupRunFailRequest(BaseModel):
    date_fin: date | None = None
    message_erreur: str = Field(min_length=1, max_length=255)
    resultat: str | None = None


class RestoreTestCreateRequest(BaseModel):
    perimetre: str | None = None


class BackupResponse(BaseModel):
    id: UUID
    type_enregistrement: str | None = None
    parent_id: UUID | None = None
    frequence: str | None = None
    retention: str | None = None
    perimetre: str | None = None
    emplacement_stockage: str | None = None
    date_debut: date | None = None
    date_fin: date | None = None
    taille_octets: int | None = None
    integrite_validee: bool | None = None
    resultat: str | None = None
    preuve_document_id: UUID | None = None
    message_erreur: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class BackupListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[BackupResponse] = Field(default_factory=list)


# ============================================================
# INCIDENTS# ============================================================
# INCIDENTS
# ============================================================

class IncidentCreateRequest(BaseModel):
    categorie: str = Field(min_length=1, max_length=255)
    gravite: str = Field(min_length=1, max_length=255)
    titre: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    responsable_id: UUID | None = None
    ressource_type: str | None = Field(default=None, max_length=255)
    ressource_id: UUID | None = None
    preuves: dict[str, Any] = Field(default_factory=dict)


class IncidentUpdateRequest(BaseModel):
    categorie: str | None = Field(default=None, max_length=255)
    gravite: str | None = Field(default=None, max_length=255)
    titre: str | None = Field(default=None, max_length=255)
    description: str | None = None
    responsable_id: UUID | None = None
    preuves: dict[str, Any] | None = None


class IncidentAssignRequest(BaseModel):
    responsable_id: UUID
    commentaire: str | None = Field(default=None, max_length=2000)


class IncidentResolveRequest(BaseModel):
    resolution: str = Field(min_length=1)


class IncidentCloseRequest(BaseModel):
    commentaire: str | None = Field(default=None, max_length=2000)


class IncidentResponse(BaseModel):
    id: UUID
    code: str
    categorie: str | None = None
    gravite: str | None = None
    titre: str | None = None
    description: str | None = None
    date_declaration: date | None = None
    declare_par_id: UUID
    responsable_id: UUID | None = None
    ressource_type: str | None = None
    ressource_id: UUID | None = None
    preuves: dict[str, Any] | None = None
    resolution: str | None = None
    date_resolution: date | None = None
    date_cloture: date | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class IncidentListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[IncidentResponse] = Field(default_factory=list)


# ============================================================
# DASHBOARD# ============================================================
# DASHBOARD
# ============================================================

class GovernanceDashboardResponse(BaseModel):
    draft_rules: int
    open_action_plans: int
    open_incidents: int
    pending_publications: int
    pending_reports: int
    failed_backups: int
