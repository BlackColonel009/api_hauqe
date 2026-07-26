# Interactions — Pilotage / Tableaux de bord

```text
ENTREPRISES
CERTIFICATIONS
NORMES
ORGANISMES
    │
    ├──────────────┐
    │              │
COLLECTE       VERIFICATION
    │              │
    └──────→ FUCCS
               │
          VALIDATION
               │
        INTEGRATION BNEC
               │
          SCORING / INFC
               │
             SNCC
               │
        VEILLE / ALERTES
               │
      QUALITE / CONTINUITE
               │
               ↓
      TABLEAUX DE BORD
               │
     ┌─────────┼─────────┐
     ↓         ↓         ↓
opérationnel tactique stratégique
                     │
                   annuel
                     │
                 baromètre
                     │
         règle + publication
                     │
                     ↓
              PUBLIC AGRÉGÉ
```

## Aucune table supplémentaire

Les tableaux de bord sont des projections calculées des 66 tables métier
existantes.

Cela évite :
- duplication ;
- divergence entre source et dashboard ;
- migration supplémentaire.

Si les volumes futurs l'exigent, le repository pourra être remplacé par des
vues matérialisées PostgreSQL tout en conservant les contrats API.
