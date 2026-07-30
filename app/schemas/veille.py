"""
Schémas API — Échéances / Alertes / Notifications / Veille.

PRINCIPES
---------
- une échéance représente un événement futur ou dépassé ;
- une alerte représente une situation nécessitant attention/action ;
- les alertes automatiques d'expiration utilisent les seuils validés
  180 / 90 / 30 jours / expiration, mais le moteur sait déjà charger
  une règle `regles_metier` pour remplacer ces valeurs sans changer le code ;
- les relances, notifications, erreurs et résolutions sont historisées ;
- aucune suppression physique n'est exposée par l'API ;
- les rapports de veille sont générés depuis les données réellement présentes.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# ÉCHÉANCES
# ============================================================

class DeadlineCreateRequest(BaseModel):
    ressource_type: str = Field(min_length=1, max_length=255)
    ressource_id: UUID
    type_echeance: str = Field(min_length=1, max_length=255)
    titre: str = Field(min_length=1, max_length=255)
    description: str | None = None
    date_echeance: date
    responsable_id: UUID | None = None
    priorite: str | None = Field(default=None, max_length=255)


class DeadlineUpdateRequest(BaseModel):
    titre: str | None = Field(default=None, max_length=255)
    description: str | None = None
    date_echeance: date | None = None
    responsable_id: UUID | None = None
    priorite: str | None = Field(default=None, max_length=255)


class DeadlineCloseRequest(BaseModel):
    motif: str = Field(min_length=1, max_length=2000)


class DeadlineResponse(BaseModel):
    id: UUID
    ressource_type: str | None = None
    ressource_id: UUID | None = None
    type_echeance: str | None = None
    titre: str | None = None
    description: str | None = None
    date_echeance: date | None = None
    responsable_id: UUID | None = None
    priorite: str | None = None
    statut: str | None = None
    motif_cloture: str | None = None
    jours_restants: int | None = None
    alertes_actives_count: int = 0
    created_at: datetime
    updated_at: datetime


class DeadlineListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[DeadlineResponse] = Field(default_factory=list)


# ============================================================
# ALERTES
# ============================================================

class AlertCreateRequest(BaseModel):
    echeance_id: UUID | None = None
    type_alerte: str = Field(min_length=1, max_length=255)
    niveau: int = Field(ge=1, le=4)
    titre: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1)
    ressource_type: str = Field(min_length=1, max_length=255)
    ressource_id: UUID
    responsable_id: UUID | None = None
    regle_notification: str | None = Field(default=None, max_length=255)


class AlertAssignRequest(BaseModel):
    responsable_id: UUID
    commentaire: str | None = Field(default=None, max_length=2000)


class AlertUpdateRequest(BaseModel):
    niveau: int | None = Field(default=None, ge=1, le=4)
    titre: str | None = Field(default=None, max_length=255)
    message: str | None = None
    responsable_id: UUID | None = None


class AlertResolveRequest(BaseModel):
    resolution: str = Field(min_length=1)
    cloturer: bool = False


class AlertResponse(BaseModel):
    id: UUID
    echeance_id: UUID | None = None
    type_alerte: str | None = None
    niveau: int | None = None
    titre: str | None = None
    message: str | None = None
    ressource_type: str | None = None
    ressource_id: UUID | None = None
    responsable_id: UUID | None = None
    date_detection: date | None = None
    date_resolution: date | None = None
    regle_notification: str | None = None
    statut: str | None = None
    notifications_count: int = 0
    notifications_non_lues_count: int = 0
    created_at: datetime
    updated_at: datetime


class AlertListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[AlertResponse] = Field(default_factory=list)


# ============================================================
# NOTIFICATIONS
# ============================================================

class NotificationRecipient(BaseModel):
    destinataire_utilisateur_id: UUID | None = None
    adresse_externe: str | None = Field(default=None, max_length=255)
    canal: str = Field(min_length=1, max_length=255)


class AlertNotifyRequest(BaseModel):
    objet: str = Field(min_length=1, max_length=255)
    contenu: str = Field(min_length=1)
    destinataires: list[NotificationRecipient] = Field(min_length=1)


class NotificationResultRequest(BaseModel):
    success: bool
    resultat: str | None = None
    message_erreur: str | None = Field(default=None, max_length=255)


class NotificationResponse(BaseModel):
    id: UUID
    alerte_id: UUID | None = None
    destinataire_utilisateur_id: UUID | None = None
    adresse_externe: str | None = None
    canal: str | None = None
    objet: str | None = None
    contenu: str | None = None
    date_envoi: date | None = None
    date_lecture: date | None = None
    resultat: str | None = None
    nombre_tentatives: int | None = None
    message_erreur: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    total: int
    unread_count: int
    limit: int
    offset: int
    items: list[NotificationResponse] = Field(default_factory=list)


# ============================================================
# DOSSIERS DE VEILLE
# ============================================================

class WatchCaseCreateRequest(BaseModel):
    certification_id: UUID
    type_evenement: str = Field(min_length=1, max_length=255)
    priorite: str | None = Field(default=None, max_length=255)
    responsable_id: UUID
    prochaine_action_at: datetime | None = None


class WatchCaseUpdateRequest(BaseModel):
    type_evenement: str | None = Field(default=None, max_length=255)
    priorite: str | None = Field(default=None, max_length=255)
    responsable_id: UUID | None = None
    prochaine_action_at: datetime | None = None


class WatchCaseCloseRequest(BaseModel):
    motif: str = Field(min_length=1, max_length=2000)


class WatchCaseResponse(BaseModel):
    id: UUID
    certification_id: UUID
    type_evenement: str | None = None
    priorite: str | None = None
    date_ouverture: date | None = None
    responsable_id: UUID
    prochaine_action_at: datetime | None = None
    date_cloture: date | None = None
    statut: str | None = None
    relances_count: int = 0
    relances_en_attente_count: int = 0
    created_at: datetime
    updated_at: datetime


class WatchCaseListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[WatchCaseResponse] = Field(default_factory=list)


# ============================================================
# RELANCES
# ============================================================

class FollowUpCreateRequest(BaseModel):
    destinataire: str = Field(min_length=1, max_length=255)
    adresse_email: str = Field(min_length=3, max_length=320)
    canal: str = Field(min_length=1, max_length=255)
    objet: str = Field(min_length=1, max_length=255)
    contenu: str = Field(min_length=1)
    date_envoi: date | None = None
    date_echeance: date | None = None


class FollowUpUpdateRequest(BaseModel):
    destinataire: str | None = Field(default=None, max_length=255)
    adresse_email: str | None = Field(default=None, max_length=320)
    canal: str | None = Field(default=None, max_length=255)
    objet: str | None = Field(default=None, max_length=255)
    contenu: str | None = None
    date_envoi: date | None = None
    date_echeance: date | None = None
    statut: str | None = Field(default=None, max_length=255)


class FollowUpResponseRequest(BaseModel):
    date_reponse: date | None = None
    reponse: str = Field(min_length=1)
    resultat: str | None = None


class FollowUpResponse(BaseModel):
    id: UUID
    dossier_veille_id: UUID
    destinataire: str | None = None
    adresse_email: str | None = None
    canal: str | None = None
    objet: str | None = None
    contenu: str | None = None
    date_envoi: date | None = None
    date_echeance: date | None = None
    date_reponse: date | None = None
    reponse: str | None = None
    resultat: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# RAPPORTS DE VEILLE
# ============================================================

class WatchReportGenerateRequest(BaseModel):
    type_rapport: str = Field(min_length=1, max_length=255)
    periode_debut: str = Field(min_length=10, max_length=255)
    periode_fin: str = Field(min_length=10, max_length=255)


class WatchReportValidateRequest(BaseModel):
    commentaire: str | None = Field(default=None, max_length=2000)


class WatchReportResponse(BaseModel):
    id: UUID
    type_rapport: str | None = None
    periode_debut: str | None = None
    periode_fin: str | None = None
    nombre_certifications_suivies: int | None = None
    nombre_alertes: int | None = None
    nombre_renouvellements: int | None = None
    delai_moyen_traitement: Decimal | None = None
    indicateurs: dict[str, Any] | None = None
    prepare_par_id: UUID
    valide_par_id: UUID | None = None
    date_validation: date | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class WatchReportListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[WatchReportResponse] = Field(default_factory=list)


# ============================================================
# MOTEUR QUOTIDIEN / DASHBOARD
# ============================================================

class DailyScanResponse(BaseModel):
    scan_date: date
    deadlines_created: int = 0
    alerts_created: int = 0
    certification_deadlines_seen: int = 0
    audit_deadlines_seen: int = 0
    renewal_deadlines_seen: int = 0


class WatchDashboardResponse(BaseModel):
    open_watch_cases: int
    overdue_deadlines: int
    active_alerts: int
    critical_alerts: int
    pending_followups: int
    unread_notifications: int
