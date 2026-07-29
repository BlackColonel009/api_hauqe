# Règles versionnées — moteur de scoring

## Pourquoi aucun seuil n'est codé en dur

La Classification entreprise, l'INFC et le SNCC sont des résultats distincts.

Le frontend actuel contient encore des valeurs historiques ou provisoires.
Le backend ne doit donc pas figer les seuils ou pondérations tant qu'ils
n'ont pas été publiés comme modèle HAUQE.

`modeles_scoring.regle_calcul` stocke la règle approuvée sous forme JSON
sérialisée.

## Modes techniques supportés

### 1. DIRECT_SCORE

Le système reçoit un score déjà calculé par la règle institutionnelle et
utilise le modèle pour déterminer une classe ou un niveau.

```json
{
  "calculation_mode": "DIRECT_SCORE",
  "rounding": 2,
  "score_min": 0,
  "score_max": 100,
  "classes": [
    {"code": "EXEMPLE_A", "min": 80, "max": 100},
    {"code": "EXEMPLE_B", "min": 0, "max": 79.9999}
  ]
}
```

Ces valeurs sont des **exemples techniques**, pas les seuils officiels.

### 2. WEIGHTED_AVERAGE_100

Chaque domaine reçu est noté de 0 à 100.

```text
score =
Σ(score_domaine × pondération)
─────────────────────────────
      Σ(pondérations)
```

Le nombre de domaines n'est pas imposé par le moteur.

### 3. SUM_DOMAIN_POINTS

Chaque pondération représente le maximum de points du domaine.

```text
score_global = Σ(points_obtenus_par_domaine)
```

Exemple : un domaine pondéré à `20` accepte une valeur entre `0` et `20`.

## Manquants

Par défaut :

```json
{
  "missing_policy": "REJECT"
}
```

Une donnée manquante bloque le calcul afin de ne pas produire un score
trompeur.

Aucune imputation silencieuse n'est réalisée.

## Classes

Pour la classification entreprise :

```json
{
  "classes": [
    {"code": "CLASSE_1", "min": 0, "max": 100}
  ]
}
```

Les véritables codes/seuils doivent être chargés depuis la règle validée.

## Niveaux INFC

```json
{
  "levels": [
    {"niveau": 1, "min": 0, "max": 100}
  ]
}
```

Les valeurs officielles ne sont pas préchargées par ce bundle.

## SNCC

Le MPD `classements_sncc` ne possède ni `modele_scoring_id` ni
`resultat_infc_id`.

Par conséquent :
- le SNCC reste un résultat distinct ;
- l'API n'invente aucune conversion INFC → SNCC ;
- la classe, le statut administratif et le niveau de risque sont saisis
  selon la matrice institutionnelle qui sera validée ;
- l'historique est garanti par de nouvelles lignes de classement et des
  périodes `date_effet` / `date_fin`.
