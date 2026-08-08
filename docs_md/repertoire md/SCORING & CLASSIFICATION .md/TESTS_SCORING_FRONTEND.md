# Tests — à réaliser lors du raccordement frontend

Statut du lot : **implémenté / non validé runtime**.

## Modèles de scoring

Tester depuis `regles-codification.html` :
- création BROUILLON ;
- version code/version dupliquée -> 409 ;
- règle JSON avec mode invalide -> 422 ;
- modèle pondéré sans pondération -> publication 409 ;
- publication avec référence -> PUBLIE ;
- modification après publication -> 409 ;
- clone -> nouveau BROUILLON avec pondérations copiées ;
- retrait -> RETIRE.

## Simulateur

Tester :
- DIRECT_SCORE sans `score_direct` -> 422 ;
- domaine manquant + missing_policy=REJECT -> 409 ;
- score domaine > 100 en WEIGHTED_AVERAGE_100 -> 422 ;
- score domaine > maximum en SUM_DOMAIN_POINTS -> 422 ;
- aucun seuil correspondant -> 409.

## Classification entreprise

Tester :
- entreprise inexistante -> 404 ;
- aucun modèle CLASSIFICATION_ENTREPRISE publié -> 409 ;
- calcul valide -> nouvelle ligne historisée ;
- second calcul -> nouvelle ligne, ancienne conservée ;
- latest -> dernière ligne.

## INFC

Tester :
- certification inexistante -> 404 ;
- modèle INFC publié requis ;
- domaines incomplets -> 409 ;
- calcul -> statut CALCULE ;
- validation -> statut VALIDE + date_validation ;
- historique conservé.

## SNCC

Tester :
- création initiale ;
- second classement sans reclassify -> 409 ;
- reclassement avec date antérieure/égale -> 422 ;
- reclassement valide -> ancien `date_fin = nouvelle date_effet - 1 jour` ;
- current -> nouvelle ligne ;
- close -> fin explicite ;
- aucune enum A+/VA/R1 n'est imposée par ce lot tant que le dictionnaire final
  n'est pas confirmé.

## Contrôle technique

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_scoring_permissions
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m alembic check
```

Attendu :

```text
No new upgrade operations detected.
```
