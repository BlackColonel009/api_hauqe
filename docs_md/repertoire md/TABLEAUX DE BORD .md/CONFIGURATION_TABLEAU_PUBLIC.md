# Configuration du tableau de bord public

Le endpoint :

```text
GET /api/v1/public/indicators
```

est anonyme, mais il reste **fermé par défaut**.

Il ne retourne des données que si deux conditions sont réunies.

## 1. Règle publiée

Créer une règle métier avec :

```text
logical_code = PUBLIC_DASHBOARD_INDICATORS
```

Exemple technique :

```json
{
  "logical_code": "PUBLIC_DASHBOARD_INDICATORS",
  "famille": "PUBLICATION",
  "libelle": "Indicateurs autorisés du tableau public",
  "version": "1.0",
  "date_debut_effet": "2026-01-01",
  "parametres": {
    "allowed_indicators": [
      "enterprises_count",
      "certifications_count",
      "active_certifications_count",
      "national_infc_average",
      "certification_statuses",
      "sncc_classes",
      "by_region",
      "by_sector",
      "by_norm"
    ],
    "period_start": "2026-01-01",
    "period_end": "2026-12-31",
    "disclaimer": "Données nationales agrégées validées pour publication."
  }
}
```

Cette liste est un **exemple de configuration**. La HAUQE doit choisir
explicitement les indicateurs publiables.

Publier ensuite la règle via :

```text
POST /api/v1/governance/rules/{rule_id}/publish
```

## 2. Publication institutionnelle

Créer une demande de publication liée à cette règle :

```json
{
  "ressource_type": "PUBLIC_DASHBOARD_RULE",
  "ressource_id": "<UUID_DE_LA_REGLE>",
  "objet": "Tableau de bord public BNEC",
  "perimetre": "Indicateurs agrégés autorisés",
  "niveau_confidentialite": "PUBLIC"
}
```

Workflow :

```text
POST /api/v1/publications
POST /api/v1/publications/{id}/submit
POST /api/v1/publications/{id}/approve
POST /api/v1/publications/{id}/publish
```

Seulement après ce workflow, `/api/v1/public/indicators` devient disponible.

## Catalogue public sûr

Même si une règle est mal configurée, le backend ne peut exposer que les clés
présentes dans sa liste sûre :

```text
enterprises_count
certifications_count
active_certifications_count
national_infc_average
certification_statuses
sncc_classes
by_region
by_sector
by_norm
by_certification_body
```

Le backend public ne retourne jamais :
- identifiants d'entreprise ;
- identifiants de certification ;
- numéros de certificat ;
- contacts ;
- documents ;
- coordonnées individuelles ;
- ressources d'audit ;
- alertes détaillées.
