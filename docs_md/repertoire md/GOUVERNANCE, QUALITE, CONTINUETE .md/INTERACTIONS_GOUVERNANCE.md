# Interactions du domaine Gouvernance / Qualité / Continuité

```text
REGLES_METIER
    ├── Collecte : complétude
    ├── Veille : seuils
    ├── Scoring : paramètres complémentaires
    └── futurs statuts / délais / nomenclatures

REVUES_QUALITE
    └── PLANS_ACTION
            ↓
    décisions / amélioration continue

DECISIONS_INSTITUTIONNELLES
    └── ressource_type + ressource_id
            ↓
    décision transversale historisée

PUBLICATIONS
    └── ressource_type + ressource_id
            ↓
    BROUILLON → SOUMISE → APPROUVEE → PUBLIEE

RAPPORTS_GENERES
    └── DOCUMENTS
            ↓
    téléchargement privé contrôlé

EVENEMENTS_AUDIT
    └── lecture seule

ARCHIVES
    └── registre de conservation sans suppression physique

SAUVEGARDES
    ├── POLITIQUE
    │      └── EXECUTION
    │              └── TEST_RESTAURATION
    └── DOCUMENT preuve facultatif

INCIDENTS
    └── ressource_type + ressource_id
```

## RM structurantes couvertes

- RM-29 : export soumis à autorisation et audit ;
- RM-31 : journal d'audit non modifiable ;
- RM-32 : pas de suppression définitive ;
- RM-46 : données BNEC officielles et protégées ;
- RM-47 : conservation minimale de dix ans ;
- RM-50 : diffusion/publication avec approbation ;
- RM-51 : paramètres métier administrables sans modification de code.
