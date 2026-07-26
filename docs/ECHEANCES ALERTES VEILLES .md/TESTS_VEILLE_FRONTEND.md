# Tests différés au raccordement frontend

Statut : **implémenté / non validé runtime**.

## `echeances.html`

Tester :
- création manuelle ;
- échéance active identique -> 409 ;
- modification ;
- clôture ;
- annulation ;
- filtre retards ;
- calendrier par période.

## Scan quotidien

Créer des certifications/audits/renouvellements de dates connues puis vérifier :
- création de l'échéance ;
- second scan -> aucune duplication ;
- seuil J-180 -> niveau 1 ;
- J-90 -> niveau 2 ;
- J-30 -> niveau 3 ;
- expiration/dépassement -> niveau 4 ;
- second scan du même seuil -> aucune alerte doublon.

## `alertes.html`

Tester :
- affectation à utilisateur ACTIF ;
- utilisateur INACTIF -> 409 ;
- résolution avec motif ;
- historique conservé ;
- alerte spéciale sans échéance ;
- filtre niveau/statut/responsable.

## Notifications

Tester :
- IN_APP -> ENVOYEE immédiatement ;
- EMAIL -> EN_ATTENTE ;
- compte inactif -> rejet ;
- cloche non lue ;
- read ;
- read-all ;
- retry d'un échec ;
- worker SMTP sans configuration -> file intacte ;
- succès/échec -> nombre_tentatives + audit.

## `#/veille`

Tester :
- création dossier pour certification ;
- doublon actif même certification/type -> 409 ;
- relance ;
- échéance antérieure à l'envoi -> 422 ;
- réponse ;
- clôture ;
- dashboard.

## Rapport

Tester :
- période invalide -> 422 ;
- génération ;
- compte certifications distinctes ;
- nombre alertes ;
- nombre renouvellements ;
- délai moyen de traitement ;
- validation.

## Contrôle technique

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_watch_permissions
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m alembic check
```

Tâches :

```powershell
.\.venv\Scripts\python.exe -m app.tasks.watch_daily_scan
.\.venv\Scripts\python.exe -m app.tasks.process_notification_queue
```

Attendu pour Alembic :

```text
No new upgrade operations detected.
```
