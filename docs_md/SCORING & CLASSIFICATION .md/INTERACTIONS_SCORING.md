# Interactions — Scoring / Classification / INFC / SNCC

```text
DONNEES BNEC VALIDEES
        │
        ├──────────────→ ENTREPRISE
        │                  ↓
        │         CLASSIFICATION_ENTREPRISE
        │                  ↓
        │            historique
        │
        └──────────────→ CERTIFICATION
                           │
                           ├────→ RESULTAT_INFC
                           │       └── modele_scoring
                           │             └── ponderations_scoring
                           │
                           └────→ CLASSEMENT_SNCC
                                   └── historique par périodes
```

## Modèle de scoring

```text
modeles_scoring
    └── ponderations_scoring
```

Le MPD fusionne conceptuellement modèle + version dans une même table
`modeles_scoring` grâce aux champs `code`, `version`, dates, référence
d'approbation et `statut`.

## Classification entreprise

```text
entreprises.id
    ↓
classifications_entreprise.entreprise_id

modeles_scoring.id
    ↓
classifications_entreprise.modele_scoring_id
```

Chaque nouveau calcul crée une nouvelle ligne ; l'ancien résultat reste
consultable.

## INFC

```text
certifications.id
    ↓
resultats_infc.certification_id

modeles_scoring.id
    ↓
resultats_infc.modele_scoring_id
```

`scores_domaines` JSONB conserve :
- valeurs d'entrée ;
- contributions calculées.

`sources` JSONB conserve les références métier qui ont alimenté le résultat.

Le calcul est bloqué si les domaines exigés par le modèle sont manquants.

## SNCC

```text
certifications.id
    ↓
classements_sncc.certification_id
```

Le MPD ne contient pas de FK :
- `classements_sncc -> resultats_infc`
- `classements_sncc -> modeles_scoring`

Le backend ne fabrique donc pas cette relation.

Un reclassement :
1. fixe `date_fin` du classement courant à J-1 ;
2. crée une nouvelle ligne avec la nouvelle `date_effet` ;
3. conserve l'historique ;
4. journalise le motif dans l'audit.

## Séparation stricte

```text
FUCCS
≠
CLASSIFICATION ENTREPRISE
≠
INFC
≠
SNCC
```

Aucune règle de trois automatique FUCCS → INFC n'est présente.
