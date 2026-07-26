# Interactions — Validation + Intégration BNEC

```text
FICHE
  ↓
DOSSIER VERIFICATION TERMINE
  ↓
CONTROLE FUCCS FINALISE
  ↓
VALIDATION NIVEAU 1
  │
  ├── AJOURNE ──→ CORRECTION ──→ RESOUMISSION ──→ nouvelle revue
  ├── REJETE ───→ clôture motivée
  └── VALIDE / VALIDE_SOUS_RESERVE
              ↓
       VALIDATION NIVEAU 2
              │
              ├── AJOURNE ──→ CORRECTION
              ├── REJETE
              └── VALIDE / VALIDE_SOUS_RESERVE
                          ↓
                   FILE INTEGRATION BNEC
                          ↓
                     PRECONTROLE
                          ↓
                    ELEMENTS A INTEGRER
                          ↓
                     POSTCONTROLE
                          ↓
                       INTEGREE
                          ↓
               SCORING / INFC / SNCC
```

## Double validation

Les deux décisions sont deux lignes distinctes de `validations` :
- `NIVEAU_1`
- `NIVEAU_2`

Le même utilisateur ne peut pas prononcer les deux niveaux.

L'autorité est imposée par RBAC, pas uniquement par le texte `niveau_validation`.

## Corrections

Une correction est rattachée à la décision qui l'a provoquée.

Le MPD ne possède pas de FK directe vers la nouvelle révision de fiche.
La resoumission conserve donc :
- validation source ;
- motif ;
- instructions ;
- échéance ;
- date de resoumission ;
- réponse.

La nouvelle révision de collecte reste gérée par le module Collecte.

## Intégration

Une validation N2 favorable autorise l'ouverture d'une intégration.

La validation ne crée pas automatiquement les ressources officielles.

`elements_integration` sert de registre de passage entre :
- ressource source ;
- ressource cible ;
- action ;
- révision source ;
- code généré ;
- statut ;
- erreur éventuelle.

Le format du code national n'est pas inventé dans ce lot.

## Précontrôle / postcontrôle

États techniques utilisés :

```text
EN_ATTENTE
PRECONTROLE
INTEGRATION_EN_COURS
POSTCONTROLE
INTEGREE
ECHEC
```

Une intégration réussie exige :
- validation N2 favorable ;
- précontrôle `OK` ;
- au moins un élément ;
- tous les éléments `INTEGRE` ;
- postcontrôle `OK` ;
- référence de sauvegarde.
