# Tests différés au raccordement frontend

Statut : **implémenté / non validé runtime**.

## Avant tout test

Exécuter impérativement :

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_governance_permissions
```

Puis reconnecter le compte si nécessaire.

## Règles métier

- création brouillon ;
- code physique/version dupliqué -> 409 ;
- modification brouillon ;
- publication ;
- modification après publication -> 409 ;
- clone ;
- nouvelle publication -> ancienne version chevauchante retirée ;
- `active/{logical_code}` retourne la version applicable.

## Qualité

- période invalide -> 422 ;
- responsable inactif -> 409 ;
- revue validée verrouillée ;
- plan progression 0..100 ;
- clôture plan -> progression 100.

## Décisions

- BROUILLON modifiable ;
- submit -> SOUMISE ;
- pronounce avant submit -> 409 ;
- pronounce -> DECIDEE ;
- décision prononcée non modifiable.

## Publications

- BROUILLON -> SOUMISE ;
- approve sans SOUMISE -> 409 ;
- REJETEE non publiable ;
- APPROUVEE -> PUBLIEE ;
- PUBLIEE -> RETIREE.

## Rapports

- format hors PDF/XLSX/CSV -> 422 ;
- période invalide -> 422 ;
- demande -> EN_GENERATION -> GENERE ;
- document inexistant -> 404 ;
- téléchargement via Documents ;
- échec historisé.

## Audit

- GET liste ;
- filtres ;
- GET détail ;
- vérifier absence de mutation dans OpenAPI.

## Archives

- archivage motivé ;
- second archivage actif même ressource -> 409 ;
- conservation < 10 ans -> 422 ;
- aucune suppression physique.

## Sauvegardes

- créer politique ;
- créer exécution ;
- complete avec preuve ;
- intégrité false -> ECHEC_INTEGRITE ;
- fail -> ECHEC ;
- test restauration uniquement depuis EXECUTION TERMINEE.

## Incidents

- déclaration ;
- code unique ;
- responsable inactif -> 409 ;
- assign ;
- resolve ;
- close avant resolve -> 409 ;
- close après resolve.

## Contrôle technique

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_governance_permissions
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m alembic check
```

Attendu :

```text
No new upgrade operations detected.
```
