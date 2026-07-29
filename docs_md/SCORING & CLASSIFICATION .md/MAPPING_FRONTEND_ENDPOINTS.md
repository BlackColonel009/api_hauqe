# Mapping frontend ↔ API — Scoring / Classification / INFC / SNCC

## `scoring.html` — `#/scoring`

Cette page doit présenter **sans fusion** :
1. le résultat FUCCS déjà finalisé ;
2. la classification entreprise ;
3. le résultat INFC de la certification ;
4. le classement SNCC.

### Classification entreprise

| Endpoint | Composant / action | Rôle |
|---|---|---|
| `GET /api/v1/entreprises/{enterprise_id}/classifications` | historique entreprise | Courbe/chronologie des classifications |
| `GET /api/v1/entreprises/{enterprise_id}/classifications/latest` | carte Classification | Afficher le résultat le plus récent |
| `POST /api/v1/entreprises/{enterprise_id}/classifications/evaluate` | bouton Calculer/Enregistrer | Appliquer le modèle publié et historiser le résultat |

### INFC

| Endpoint | Composant / action | Rôle |
|---|---|---|
| `GET /api/v1/certifications/{certification_id}/infc/latest` | carte INFC | Afficher score, niveau et version de modèle |
| `GET /api/v1/certifications/{certification_id}/infc` | historique INFC | Courbe et comparaisons |
| `POST /api/v1/certifications/{certification_id}/infc/calculate` | calcul INFC | Calculer avec domaines/pondérations du modèle |
| `POST /api/v1/infc/results/{result_id}/validate` | bouton Valider | Valider le résultat calculé |
| `GET /api/v1/infc/results` | filtres / administration | Recherche globale des résultats |

### SNCC

| Endpoint | Composant / action | Rôle |
|---|---|---|
| `GET /api/v1/certifications/{certification_id}/sncc/current` | carte Classement | Classe/statut/risque courant |
| `GET /api/v1/certifications/{certification_id}/sncc` | historique SNCC | Chronologie des reclassements |
| `POST /api/v1/certifications/{certification_id}/sncc` | premier classement | Créer le classement initial |
| `POST /api/v1/certifications/{certification_id}/sncc/reclassify` | bouton Reclasser | Fermer la période précédente et créer la nouvelle |
| `POST /api/v1/sncc/{sncc_id}/close` | clôture | Fermer explicitement une période |
| `GET /api/v1/sncc` | recherche globale | Filtres classe/statut/risque |

---

## `#/infc`

Page spécialisée pour :
- saisie ou récupération des scores par domaine ;
- simulation ;
- calcul ;
- détail des contributions ;
- validation ;
- historique par certification ;
- comparaison des versions de formule.

Le frontend ne doit jamais faire lui-même la formule finale.

---

## `#/classement-sncc`

Page spécialisée pour :
- classement courant ;
- classe ;
- statut administratif ;
- niveau de risque ;
- justification ;
- date d'effet ;
- historique des reclassements.

Les listes de valeurs devront être chargées depuis le référentiel/règle
institutionnelle dès que le dictionnaire final est confirmé.

---

## `regles-codification.html`

Cette page administre désormais également les modèles de scoring.

| Endpoint | Composant / action | Rôle |
|---|---|---|
| `GET /api/v1/scoring/models` | tableau Versions scoring | Lister les modèles |
| `GET /api/v1/scoring/models/active?objet_evalue=...` | badge Version active | Afficher la version applicable |
| `POST /api/v1/scoring/models` | Nouveau modèle | Créer un BROUILLON |
| `GET /api/v1/scoring/models/{model_id}` | détail | Règle, dates, référence, total pondérations |
| `PATCH /api/v1/scoring/models/{model_id}` | éditer brouillon | Modifier règle ou métadonnées |
| `POST /api/v1/scoring/models/{model_id}/clone` | Nouvelle version | Copier modèle + pondérations |
| `POST /api/v1/scoring/models/{model_id}/publish` | Publier | Figer avec référence d'approbation |
| `POST /api/v1/scoring/models/{model_id}/retire` | Retirer | Fermer la période d'application |
| `GET /api/v1/scoring/models/{model_id}/weights` | tableau pondérations | Charger les domaines |
| `POST /api/v1/scoring/models/{model_id}/weights` | Ajouter domaine | Créer une pondération |
| `PATCH /api/v1/scoring/models/{model_id}/weights/{weight_id}` | Modifier domaine | Ajuster un brouillon |
| `POST /api/v1/scoring/models/{model_id}/weights/{weight_id}/deactivate` | Désactiver | Retirer une pondération du brouillon |
| `POST /api/v1/scoring/preview/{object_type}` | Simulateur | Tester le calcul sans enregistrer de résultat |

Une version publiée est immuable.
