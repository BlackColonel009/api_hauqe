# Mapping frontend ↔ API — Gouvernance / Qualité / Continuité

## `regles-codification.html`

Ajouter une section **Règles métier**.

| Endpoint | Action UI |
|---|---|
| `GET /api/v1/governance/rules` | Historique/version des règles |
| `GET /api/v1/governance/rules/active/{logical_code}` | Version active |
| `POST /api/v1/governance/rules` | Nouveau brouillon |
| `GET /api/v1/governance/rules/{rule_id}` | Détail |
| `PATCH /api/v1/governance/rules/{rule_id}` | Modifier brouillon |
| `POST /api/v1/governance/rules/{rule_id}/clone` | Nouvelle version |
| `POST /api/v1/governance/rules/{rule_id}/publish` | Publier avec approbation |
| `POST /api/v1/governance/rules/{rule_id}/retire` | Retirer |

`GET /api/v1/governance/dashboard` peut alimenter une carte d'administration.

---

## `#/amelioration-continue`

### Revues qualité

```text
GET   /api/v1/quality/reviews
POST  /api/v1/quality/reviews
GET   /api/v1/quality/reviews/{review_id}
PATCH /api/v1/quality/reviews/{review_id}
POST  /api/v1/quality/reviews/{review_id}/validate
```

UI :
- campagne annuelle/périodique ;
- périmètre ;
- constats ;
- preuves ;
- résultat global ;
- responsable ;
- validation.

### Plans d'action

```text
GET   /api/v1/quality/action-plans
POST  /api/v1/quality/action-plans
GET   /api/v1/quality/action-plans/{plan_id}
PATCH /api/v1/quality/action-plans/{plan_id}
POST  /api/v1/quality/action-plans/{plan_id}/progress
POST  /api/v1/quality/action-plans/{plan_id}/close
```

UI :
- objectif ;
- responsable ;
- échéance ;
- priorité ;
- indicateur ;
- progression ;
- clôture.

---

## `#/decisions`

```text
GET   /api/v1/decisions
POST  /api/v1/decisions
GET   /api/v1/decisions/{decision_id}
PATCH /api/v1/decisions/{decision_id}
POST  /api/v1/decisions/{decision_id}/submit
POST  /api/v1/decisions/{decision_id}/pronounce
```

Progression :

```text
BROUILLON → SOUMISE → DECIDEE
```

La page affiche :
- constats ;
- risques ;
- options ;
- recommandation ;
- autorité ;
- priorité ;
- décision finale.

---

## `#/publications`

```text
GET  /api/v1/publications
POST /api/v1/publications
GET  /api/v1/publications/{publication_id}

POST /api/v1/publications/{publication_id}/submit
POST /api/v1/publications/{publication_id}/approve
POST /api/v1/publications/{publication_id}/publish
POST /api/v1/publications/{publication_id}/retire
```

Workflow :

```text
BROUILLON
→ SOUMISE
→ APPROUVEE / REJETEE
→ PUBLIEE
→ RETIREE
```

Aucune route publique anonyme n'est créée dans ce lot, car le périmètre des
données diffusables reste à valider.

---

## `rapports.html`

```text
GET  /api/v1/reports
POST /api/v1/reports
GET  /api/v1/reports/{report_id}

POST /api/v1/reports/{report_id}/start
POST /api/v1/reports/{report_id}/complete
POST /api/v1/reports/{report_id}/fail
```

Le formulaire crée une demande de rapport :
- modèle ;
- catégorie ;
- filtres ;
- sections ;
- PDF/XLSX/CSV ;
- période.

Le moteur documentaire officiel n'est pas inventé.
Lorsqu'un document est généré, `document_id` pointe vers le registre privé
Documents et le téléchargement continue via la route Documents sécurisée.

---

## `journal-audit.html`

```text
GET /api/v1/audit/events
GET /api/v1/audit/events/{event_id}
```

Lecture seule stricte :
- aucune route POST ;
- aucune route PATCH ;
- aucune route DELETE.

Filtres :
- utilisateur ;
- action ;
- catégorie ;
- ressource ;
- résultat ;
- période.

La vérification cryptographique de `empreinte` n'est pas inventée tant que
l'algorithme officiel du service d'audit n'est pas confirmé.

---

## `#/archives`

```text
GET  /api/v1/archives
POST /api/v1/archives
GET  /api/v1/archives/{archive_id}
```

Le registre conserve :
- ressource ;
- catégorie ;
- auteur ;
- motif ;
- conservation ;
- suppression prévue ;
- emplacement.

Aucune suppression physique n'est exécutée par ces endpoints.

---

## `#/sauvegardes`

```text
GET   /api/v1/backups
POST  /api/v1/backups/policies
PATCH /api/v1/backups/policies/{policy_id}
POST  /api/v1/backups/policies/{policy_id}/runs

GET  /api/v1/backups/{backup_id}
POST /api/v1/backups/{backup_id}/complete
POST /api/v1/backups/{backup_id}/fail
POST /api/v1/backups/{backup_id}/restore-tests
```

La page supervise :
- politiques ;
- exécutions ;
- intégrité ;
- taille ;
- emplacement ;
- erreurs ;
- tests de restauration.

Le backend métier ne lance aucune commande système de sauvegarde.

---

## `#/incidents`

```text
GET   /api/v1/incidents
POST  /api/v1/incidents
GET   /api/v1/incidents/{incident_id}
PATCH /api/v1/incidents/{incident_id}

POST /api/v1/incidents/{incident_id}/assign
POST /api/v1/incidents/{incident_id}/resolve
POST /api/v1/incidents/{incident_id}/close
```

Workflow :

```text
OUVERT → EN_COURS → RESOLU → CLOTURE
```

Le code incident est technique et unique ; ce n'est pas un identifiant
national métier.
