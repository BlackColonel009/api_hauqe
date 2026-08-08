# Règles Échéances / Alertes / Veille

## Seuils d'alerte

Le moteur implémente le socle validé :

| Jours avant échéance | Niveau technique | Libellé |
|---:|---:|---|
| 180 | 1 | Information |
| 90 | 2 | Surveillance |
| 30 | 3 | Urgence |
| 0 / dépassé | 4 | Critique |

Le mapping numérique est nécessaire parce que `alertes.niveau` est un entier.

## Paramétrage futur sans modification du moteur

Le service recherche d'abord une règle publiée :

```text
code = VEILLE_SEUILS_EXPIRATION
```

dans `regles_metier`.

Exemple de `parametres` :

```json
{
  "thresholds": [
    {"days": 180, "niveau": 1, "code": "INFO_180", "label": "Information"},
    {"days": 90, "niveau": 2, "code": "SURVEILLANCE_90", "label": "Surveillance"},
    {"days": 30, "niveau": 3, "code": "URGENCE_30", "label": "Urgence"},
    {"days": 0, "niveau": 4, "code": "CRITIQUE_EXPIRATION", "label": "Critique"}
  ]
}
```

En absence de règle publiée, ces mêmes valeurs validées sont utilisées comme
fallback technique.

## Déduplication

Une échéance générée est dédupliquée par :

```text
ressource_type
+ ressource_id
+ type_echeance
+ date_echeance
+ statut actif
```

Une alerte automatique est dédupliquée par :

```text
echeance_id
+ regle_notification
+ statut actif
```

Ainsi, un scan quotidien ne multiplie pas les mêmes alertes.

## Sources surveillées par le scan

```text
certifications.date_expiration
audits_certification.date_prevue
renouvellements_certification.date_limite
```

Le scan crée :
- l'échéance si elle n'existe pas ;
- le niveau d'alerte atteint si nécessaire.

Les événements spéciaux (suspension, retrait, incohérence, modification de
portée, etc.) utilisent l'endpoint de création d'alerte tant que leurs règles
automatiques spécifiques ne sont pas publiées dans `regles_metier`.

## Notification

- `IN_APP` : disponible immédiatement dans la cloche ;
- `EMAIL` : mise en file `EN_ATTENTE` ;
- autre canal : également mis en attente jusqu'à son transport dédié.

Les comptes utilisateurs non `ACTIF` sont refusés à la création et à nouveau
contrôlés par le worker EMAIL avant expédition.

## Transport EMAIL

Le worker lit uniquement des secrets d'environnement :

```text
HAUQE_SMTP_HOST
HAUQE_SMTP_PORT
HAUQE_SMTP_USER
HAUQE_SMTP_PASSWORD
HAUQE_SMTP_FROM
HAUQE_SMTP_USE_TLS
```

Aucun secret n'est enregistré dans la base métier.
