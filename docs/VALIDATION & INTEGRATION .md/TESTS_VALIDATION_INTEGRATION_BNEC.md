# Tests à effectuer lors du raccordement frontend

Le projet avance sans campagne Swagger intermédiaire. Ce lot est donc marqué
**implémenté mais non validé runtime** jusqu'aux tests page par page.

## Validation

Tester depuis `validations.html` :
- aucune validation sans contrôle FUCCS FINALISE ;
- N2 impossible sans N1 favorable ;
- même utilisateur N1 + N2 -> 409 ;
- `VALIDE_SOUS_RESERVE` sans réserve -> 422 ;
- N1/N2 AJOURNE -> correction possible ;
- correction resoumise -> nouvelle décision possible ;
- N2 favorable -> intégration admissible ;
- N2 rejeté/ajourné -> intégration bloquée.

## Intégration

Tester depuis `integrations.html` :
- ouverture sans N2 favorable -> 409 ;
- deuxième intégration active -> 409 ;
- précontrôle ECHEC -> intégration ECHEC ;
- start sans précontrôle OK -> 409 ;
- création/édition des éléments ;
- résultat INTEGRE et ECHEC ;
- postcontrôle OK impossible avec élément non intégré ;
- complete impossible sans sauvegarde_reference ;
- complete réussie -> statut INTEGREE ;
- nouvelle ouverture après INTEGREE -> 409.

## Audit attendu

```text
VALIDATION_LEVEL1_DECISION
VALIDATION_LEVEL2_DECISION
VALIDATION_CORRECTION_REQUEST
VALIDATION_CORRECTION_UPDATE
VALIDATION_CORRECTION_RESUBMIT

BNEC_INTEGRATION_OPEN
BNEC_PRECONTROL
BNEC_INTEGRATION_START
BNEC_INTEGRATION_ELEMENT_CREATE
BNEC_INTEGRATION_ELEMENT_UPDATE
BNEC_INTEGRATION_ELEMENT_RESULT
BNEC_POSTCONTROL
BNEC_INTEGRATION_COMPLETE
```

## Contrôle technique

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_validation_integration_permissions
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m alembic check
```

Attendu :

```text
No new upgrade operations detected.
```
