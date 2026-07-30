"""
Schémas API du domaine Organismes / Certifications.

Ce fichier regroupe les contrats HTTP du domaine afin de livrer le module
principal et tous ses sous-modules en un seul bloc cohérent.

Sous-modules couverts :
- normes (lecture minimale, dépendance de certification) ;
- organismes ;
- accréditations ;
- certifications ;
- couvertures ;
- audits de certification ;
- historique des événements ;
- renouvellements.

Les listes institutionnelles de statuts ne sont pas figées ici sauf lorsque
une valeur par défaut technique est nécessaire. Les valeurs définitives
pourront ensuite être pilotées par les référentiels/règles métier.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# NORMES — LECTURE MINIMALE
# ============================================================

class NormeResponse(BaseModel):
    id: UUID
    code: str | None = None
    nom: str | None = None
    version: str | None = None
    autorite_emettrice: str | None = None
    domaine: str | None = None
    portee: str | None = None
    date_debut_application: date | None = None
    date_fin_application: date | None = None
    date_expiration: date | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class NormeCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=255)
    nom: str | None = Field(default=None, max_length=255)
    version: str | None = Field(default=None, max_length=255)
    domaine: str | None = Field(default=None, max_length=255)


# ============================================================
# ORGANISMES
# ============================================================

class OrganismeCreateRequest(BaseModel):
    identifiant_national: str | None = Field(default=None, max_length=255)
    nom_officiel: str = Field(min_length=1, max_length=255)
    sigle: str | None = Field(default=None, max_length=255)
    type_organisme: str | None = Field(default=None, max_length=255)
    pays: str | None = Field(default=None, max_length=255)
    numero_enregistrement: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    telephone: str | None = Field(default=None, max_length=255)
    adresse: str | None = None
    zone_id: UUID | None = None
    site_web: str | None = Field(default=None, max_length=255)
    statut: str | None = Field(default="A_VERIFIER", max_length=255)


class OrganismeUpdateRequest(BaseModel):
    identifiant_national: str | None = Field(default=None, max_length=255)
    nom_officiel: str | None = Field(default=None, max_length=255)
    sigle: str | None = Field(default=None, max_length=255)
    type_organisme: str | None = Field(default=None, max_length=255)
    pays: str | None = Field(default=None, max_length=255)
    numero_enregistrement: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    telephone: str | None = Field(default=None, max_length=255)
    adresse: str | None = None
    zone_id: UUID | None = None
    site_web: str | None = Field(default=None, max_length=255)


class OrganismeVerificationRequest(BaseModel):
    statut: str | None = Field(default=None, max_length=255)
    motif: str | None = Field(default=None, max_length=2000)


class OrganismeResponse(BaseModel):
    id: UUID
    identifiant_national: str | None = None
    nom_officiel: str | None = None
    sigle: str | None = None
    type_organisme: str | None = None
    pays: str | None = None
    numero_enregistrement: str | None = None
    email: str | None = None
    telephone: str | None = None
    adresse: str | None = None
    zone_id: UUID | None = None
    site_web: str | None = None
    statut: str | None = None
    date_derniere_verification: date | None = None
    created_at: datetime
    updated_at: datetime



class OrganismeRegistryItem(BaseModel):
    id: UUID
    identifiant_national: str | None = None
    nom_officiel: str | None = None
    sigle: str | None = None
    type_organisme: str | None = None
    pays: str | None = None
    statut: str | None = None
    date_derniere_verification: date | None = None
    accreditation_count: int = 0
    certification_count: int = 0
    accreditors: str | None = None
    domains: str | None = None
    next_accreditation_expiration: date | None = None


class OrganismeRegistrySummary(BaseModel):
    total: int = 0
    recognized: int = 0
    to_verify: int = 0
    suspended: int = 0
    certifications_total: int = 0


class OrganismeRegistryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    summary: OrganismeRegistrySummary
    items: list[OrganismeRegistryItem] = Field(default_factory=list)


class OrganismeFiltersResponse(BaseModel):
    statuses: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    types: list[str] = Field(default_factory=list)
    accreditors: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    zones: list[dict[str, str]] = Field(default_factory=list)


# ============================================================
# ACCRÉDITATIONS
# ============================================================

class AccreditationCreateRequest(BaseModel):
    numero: str | None = Field(default=None, max_length=255)
    accrediteur: str | None = Field(default=None, max_length=255)
    domaine_technique: str | None = Field(default=None, max_length=255)
    perimetre: str | None = None
    date_delivrance: date | None = None
    date_expiration: date | None = None
    statut: str | None = Field(default="A_VERIFIER", max_length=255)
    reference_officielle: str | None = Field(default=None, max_length=255)


class AccreditationUpdateRequest(BaseModel):
    numero: str | None = Field(default=None, max_length=255)
    accrediteur: str | None = Field(default=None, max_length=255)
    domaine_technique: str | None = Field(default=None, max_length=255)
    perimetre: str | None = None
    date_delivrance: date | None = None
    date_expiration: date | None = None
    statut: str | None = Field(default=None, max_length=255)
    reference_officielle: str | None = Field(default=None, max_length=255)


class AccreditationDecisionRequest(BaseModel):
    decision_hauqe: str = Field(min_length=1, max_length=255)
    statut: str | None = Field(default=None, max_length=255)
    motif: str | None = Field(default=None, max_length=2000)


class AccreditationResponse(BaseModel):
    id: UUID
    organisme_id: UUID
    numero: str | None = None
    accrediteur: str | None = None
    domaine_technique: str | None = None
    perimetre: str | None = None
    date_delivrance: date | None = None
    date_expiration: date | None = None
    statut: str | None = None
    reference_officielle: str | None = None
    decision_hauqe: str | None = None
    date_decision: date | None = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# CERTIFICATIONS
# ============================================================

class CertificationCreateRequest(BaseModel):
    identifiant_national: str = Field(min_length=1, max_length=255)
    entreprise_id: UUID
    organisme_id: UUID
    accreditation_id: UUID | None = None
    norme_id: UUID
    numero_certificat: str | None = Field(default=None, max_length=255)
    portee: str | None = None
    date_obtention: date | None = None
    date_effet: date | None = None
    date_expiration: date | None = None
    statut: str | None = Field(default="A_VERIFIER", max_length=255)
    motif_statut: str | None = Field(default=None, max_length=255)
    certification_strategique: bool | None = False
    source_donnee: str | None = Field(default=None, max_length=255)


class CertificationUpdateRequest(BaseModel):
    numero_certificat: str | None = Field(default=None, max_length=255)
    portee: str | None = None
    date_obtention: date | None = None
    date_effet: date | None = None
    date_expiration: date | None = None
    certification_strategique: bool | None = None
    source_donnee: str | None = Field(default=None, max_length=255)


class CertificationStatusRequest(BaseModel):
    nouveau_statut: str = Field(min_length=1, max_length=255)
    motif: str = Field(min_length=1, max_length=2000)
    source: str | None = Field(default="API", max_length=255)


class CertificationVerificationRequest(BaseModel):
    authenticite_verifiee: bool
    nouveau_statut: str | None = Field(default=None, max_length=255)
    motif: str = Field(min_length=1, max_length=2000)
    source: str | None = Field(default="VERIFICATION", max_length=255)


class CertificationResponse(BaseModel):
    id: UUID
    identifiant_national: str
    entreprise_id: UUID
    organisme_id: UUID
    accreditation_id: UUID | None = None
    norme_id: UUID
    numero_certificat: str | None = None
    portee: str | None = None
    date_obtention: date | None = None
    date_effet: date | None = None
    date_expiration: date | None = None
    statut: str | None = None
    motif_statut: str | None = None
    classification: str | None = None
    authenticite_verifiee: bool | None = None
    certification_strategique: bool | None = None
    source_donnee: str | None = None
    created_at: datetime
    updated_at: datetime


class CertificationListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[CertificationResponse] = Field(default_factory=list)


# ============================================================
# COUVERTURES
# ============================================================

class CouvertureCreateRequest(BaseModel):
    type_couverture: str = Field(min_length=1, max_length=255)
    offre_entreprise_id: UUID | None = None
    site_entreprise_id: UUID | None = None
    libelle_couverture: str | None = Field(default=None, max_length=255)
    details: str | None = Field(default=None, max_length=255)
    statut: str | None = Field(default="ACTIF", max_length=255)


class CouvertureUpdateRequest(BaseModel):
    libelle_couverture: str | None = Field(default=None, max_length=255)
    details: str | None = Field(default=None, max_length=255)
    statut: str | None = Field(default=None, max_length=255)


class CouvertureResponse(BaseModel):
    id: UUID
    certification_id: UUID
    type_couverture: str | None = None
    offre_entreprise_id: UUID | None = None
    site_entreprise_id: UUID | None = None
    libelle_couverture: str | None = None
    details: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# AUDITS DE CERTIFICATION
# ============================================================

class AuditCertificationCreateRequest(BaseModel):
    type_audit: str | None = Field(default=None, max_length=255)
    date_prevue: date | None = None
    date_realisee: date | None = None
    auditeur: str | None = Field(default=None, max_length=255)
    resultat: str | None = None
    prochain_audit_at: datetime | None = None
    observations: str | None = None
    statut: str | None = Field(default="PLANIFIE", max_length=255)


class AuditCertificationUpdateRequest(BaseModel):
    type_audit: str | None = Field(default=None, max_length=255)
    date_prevue: date | None = None
    date_realisee: date | None = None
    auditeur: str | None = Field(default=None, max_length=255)
    resultat: str | None = None
    prochain_audit_at: datetime | None = None
    observations: str | None = None
    statut: str | None = Field(default=None, max_length=255)


class AuditCertificationResponse(BaseModel):
    id: UUID
    certification_id: UUID
    type_audit: str | None = None
    date_prevue: date | None = None
    date_realisee: date | None = None
    auditeur: str | None = None
    resultat: str | None = None
    prochain_audit_at: datetime | None = None
    observations: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# HISTORIQUE CERTIFICATION
# ============================================================

class EvenementCertificationResponse(BaseModel):
    id: UUID
    certification_id: UUID
    type_evenement: str | None = None
    ancien_statut: str | None = None
    nouveau_statut: str | None = None
    date_evenement: datetime | None = None
    motif: str | None = None
    source: str | None = None
    acteur_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# RENOUVELLEMENTS
# ============================================================

class RenouvellementCreateRequest(BaseModel):
    date_ouverture: date | None = None
    date_limite: date | None = None
    preuves: dict[str, Any] | list[Any] | None = None
    statut: str | None = Field(default="OUVERT", max_length=255)


class RenouvellementUpdateRequest(BaseModel):
    date_ouverture: date | None = None
    date_limite: date | None = None
    preuves: dict[str, Any] | list[Any] | None = None
    statut: str | None = Field(default=None, max_length=255)


class RenouvellementDecisionRequest(BaseModel):
    decision: str = Field(min_length=1, max_length=255)
    resultat: str | None = None
    justification: str = Field(min_length=1)
    statut: str | None = Field(default=None, max_length=255)


class RenouvellementCompletionRequest(BaseModel):
    decision: str = Field(min_length=1, max_length=32)
    nouvelle_date_effet: date | None = None
    nouvelle_date_expiration: date | None = None
    nouveau_numero_certificat: str | None = Field(default=None, max_length=255)
    reference_decision: str = Field(min_length=1, max_length=255)
    justification: str = Field(min_length=3)
    justificatif_document_ids: list[UUID] = Field(default_factory=list)
    preuves: dict[str, Any] | list[Any] | None = None


class RenouvellementResponse(BaseModel):
    id: UUID
    certification_id: UUID
    date_ouverture: date | None = None
    date_limite: date | None = None
    date_decision: date | None = None
    decision: str | None = None
    resultat: str | None = None
    justification: str | None = None
    preuves: dict[str, Any] | list[Any] | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class RenouvellementCompletionResponse(BaseModel):
    renouvellement: RenouvellementResponse
    certification: CertificationResponse
    echeances_terminees: int = 0
    alertes_resolues: int = 0
    nouveau_cycle: dict[str, int] = Field(default_factory=dict)
