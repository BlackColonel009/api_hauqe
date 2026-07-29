# Mapping frontend ↔ API — Validation / Intégration BNEC

## `validations.html` — `#/validations`

La page devient exclusivement la page de décision institutionnelle après
Vérification + FUCCS.

| Endpoint | Élément frontend | Rôle |
|---|---|---|
| `GET /api/v1/validations/queue` | file « À valider » | Afficher les dossiers avec FUCCS finalisé et état N1/N2 |
| `GET /api/v1/validations` | historique / filtres | Rechercher toutes les décisions |
| `GET /api/v1/validations/{validation_id}` | panneau décision | Afficher validateur, niveau, décision, réserves, justification |
| `POST /api/v1/validations/from-fiche/{fiche_id}/level-1` | bouton « Revue technique N1 » | Enregistrer la première décision hiérarchique |
| `POST /api/v1/validations/from-fiche/{fiche_id}/level-2` | bouton « Validation définitive N2 » | Prononcer la décision finale |
| `GET /api/v1/validations/{validation_id}/corrections` | onglet Corrections | Afficher les demandes et resoumissions |
| `POST /api/v1/validations/{validation_id}/corrections` | bouton « Demander correction » | Créer motif, instructions et échéance |
| `PATCH /api/v1/validations/{validation_id}/corrections/{correction_id}` | modal correction | Modifier avant resoumission |
| `POST /api/v1/validations/{validation_id}/corrections/{correction_id}/resubmit` | action agent/entreprise | Enregistrer réponse et date de resoumission |

### Affichage recommandé

```text
Avis Vérification
Score / taux FUCCS
Constats FUCCS
Anomalies / réserves
--------------------------------
Revue N1
Validation N2
Corrections
Historique
```

La page ne modifie ni Vérification ni le contrôle FUCCS.

---

## `integrations.html` — `#/integrations`

La feuille frontend existante prévoit déjà cette route comme file P0
d'intégration BNEC.

| Endpoint | Élément frontend | Rôle |
|---|---|---|
| `GET /api/v1/integrations-bnec/queue` | onglet « À intégrer » | Afficher validations N2 favorables |
| `GET /api/v1/integrations-bnec` | historique / filtres | Afficher toutes les intégrations |
| `POST /api/v1/validations/{validation_id}/integration-bnec` | bouton « Ouvrir l'intégration » | Créer le dossier technique d'intégration |
| `GET /api/v1/integrations-bnec/{integration_id}` | panneau détail | Statut, contrôles, sauvegarde et progression |
| `POST /api/v1/integrations-bnec/{integration_id}/precontrol` | étape 1 | Enregistrer contrôle préalable |
| `POST /api/v1/integrations-bnec/{integration_id}/start` | étape 2 | Démarrer l'intégration |
| `GET /api/v1/integrations-bnec/{integration_id}/elements` | tableau des objets | Voir entreprise/organisme/certification/etc. à traiter |
| `POST /api/v1/integrations-bnec/{integration_id}/elements` | « Ajouter élément » | Créer la ligne de traçabilité source→cible |
| `PATCH /api/v1/integrations-bnec/{integration_id}/elements/{element_id}` | préparer l'élément | Corriger cible/action/code avant résultat |
| `POST /api/v1/integrations-bnec/{integration_id}/elements/{element_id}/result` | « Marquer intégré / échec » | Journaliser résultat et ressource cible |
| `POST /api/v1/integrations-bnec/{integration_id}/postcontrol` | étape 3 | Contrôle qualité après intégration |
| `POST /api/v1/integrations-bnec/{integration_id}/complete` | bouton « Clôturer » | Déclarer l'intégration BNEC réussie |

### Progression visuelle

```text
EN_ATTENTE
    ↓
PRECONTROLE
    ↓
INTEGRATION_EN_COURS
    ↓
POSTCONTROLE
    ↓
INTEGREE
```

`ECHEC` reste visible dans l'historique ; une nouvelle tentative ouvre une
nouvelle ligne d'intégration au lieu d'effacer l'échec précédent.
