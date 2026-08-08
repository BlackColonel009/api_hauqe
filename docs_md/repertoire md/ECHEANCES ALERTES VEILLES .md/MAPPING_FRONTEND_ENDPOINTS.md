# Mapping frontend ↔ API — Échéances / Alertes / Veille

## `echeances.html` — `#/echeances`

| Endpoint | Élément frontend | Rôle |
|---|---|---|
| `GET /api/v1/echeances` | calendrier + liste + filtres | Charger échéances, retards, responsables et priorités |
| `POST /api/v1/echeances` | modal « Planifier une échéance » | Créer une échéance manuelle |
| `GET /api/v1/echeances/{deadline_id}` | panneau détail | Charger la ressource, la date et l'état |
| `PATCH /api/v1/echeances/{deadline_id}` | édition | Modifier date/responsable/priorité |
| `POST /api/v1/echeances/{deadline_id}/complete` | bouton Terminer | Clôturer comme réalisée |
| `POST /api/v1/echeances/{deadline_id}/cancel` | bouton Annuler | Annulation motivée |
| `GET /api/v1/echeances/{deadline_id}/alertes` | lien Centre des alertes | Voir les alertes issues de cette échéance |

Le frontend doit désormais afficher les niveaux validés 180/90/30/expiration,
et non utiliser les anciens horizons comme règle métier.

---

## `alertes.html` — `#/alertes`

| Endpoint | Élément frontend | Rôle |
|---|---|---|
| `GET /api/v1/alertes` | file + compteurs + filtres | Charger les alertes |
| `POST /api/v1/alertes` | « Alerte spéciale » | Créer suspension/retrait/incohérence/etc. |
| `GET /api/v1/alertes/{alert_id}` | panneau détail | Ressource, règle, niveau, responsable |
| `PATCH /api/v1/alertes/{alert_id}` | édition active | Ajuster niveau/message/responsable |
| `POST /api/v1/alertes/{alert_id}/assign` | modal Affecter | Affecter à un utilisateur actif |
| `POST /api/v1/alertes/{alert_id}/resolve` | Résoudre / clôturer | Enregistrer date + motif dans audit |
| `POST /api/v1/alertes/{alert_id}/notifications` | Notifier | Créer notifications internes/email |

### Lu / non lu

Le MPD ne possède pas de champ `lu` dans `alertes`.

L'état lu/non lu de l'interface doit donc être dérivé des
`notifications.date_lecture` du compte connecté, sans ajouter une colonne à
`alertes`.

---

## Cloche globale de notifications

| Endpoint | Élément frontend | Rôle |
|---|---|---|
| `GET /api/v1/notifications/unread-count` | badge de la cloche | Nombre non lu |
| `GET /api/v1/notifications?unread_only=true` | menu de la cloche | Dernières notifications |
| `POST /api/v1/notifications/{notification_id}/read` | clic notification | Marquer comme lue |
| `POST /api/v1/notifications/read-all` | « Tout marquer comme lu » | Marquer toutes les notifications internes |
| `POST /api/v1/notifications/{notification_id}/retry` | admin transport | Remettre un échec externe en file |
| `POST /api/v1/notifications/{notification_id}/delivery-result` | worker/admin | Tracer succès/échec/tentative |

---

## `#/veille` — Cellule de Veille des Certifications

### Tableau de bord

| Endpoint | Rôle |
|---|---|
| `GET /api/v1/veille/dashboard` | Compteurs : dossiers ouverts, échéances en retard, alertes actives/critiques, relances en attente, notifications |
| `POST /api/v1/veille/scans/daily` | Action administrative « Recalculer maintenant » ; le serveur l'exécute aussi par tâche quotidienne |

### Dossiers CVC

| Endpoint | Rôle |
|---|---|
| `GET /api/v1/veille/dossiers` | File de travail CVC |
| `POST /api/v1/veille/dossiers` | Ouvrir un suivi pour une certification |
| `GET /api/v1/veille/dossiers/{case_id}` | Panneau du dossier |
| `PATCH /api/v1/veille/dossiers/{case_id}` | Priorité, responsable, prochaine action |
| `POST /api/v1/veille/dossiers/{case_id}/close` | Clôture motivée |

### Relances

| Endpoint | Rôle |
|---|---|
| `GET /api/v1/veille/dossiers/{case_id}/relances` | Historique |
| `POST /api/v1/veille/dossiers/{case_id}/relances` | Nouvelle relance |
| `PATCH /api/v1/veille/dossiers/{case_id}/relances/{followup_id}` | Modifier avant réponse |
| `POST /api/v1/veille/dossiers/{case_id}/relances/{followup_id}/response` | Enregistrer réponse et résultat |

### Notes / rapports

| Endpoint | Rôle |
|---|---|
| `GET /api/v1/veille/rapports` | Historique notes mensuelles / rapports trimestriels |
| `POST /api/v1/veille/rapports/generate` | Générer les indicateurs depuis la base |
| `GET /api/v1/veille/rapports/{report_id}` | Détail |
| `POST /api/v1/veille/rapports/{report_id}/validate` | Validation Direction Technique |

Le backend ne produit pas encore le PDF de la note : `rapports_veille`
contient d'abord les indicateurs et le statut. La production documentaire
sera reliée au domaine Rapports/Gouvernance.
