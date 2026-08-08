# Tests Pilotage — différés au raccordement frontend

Statut : **implémenté / non validé runtime**.

## Avant test

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_dashboard_permissions
```

Puis reconnecter le compte si nécessaire.

## Opérationnel

Tester :
- GET sans filtre ;
- days=7 / 30 / 90 ;
- days=0 -> 422 ;
- filtre région ;
- filtre secteur ;
- filtre norme ;
- filtre organisme ;
- contrôles à planifier ;
- buckets 180/90/30/expiration ;
- actions prioritaires ;
- INFC moyen seulement sur résultats validés.

## Tactique

Tester :
- mois valide ;
- month=13 -> 422 ;
- comparaison mois précédent ;
- janvier -> comparaison décembre année précédente ;
- contrôles FUCCS finalisés ;
- intégrations terminées ;
- alertes créées/résolues.

## Stratégique

Tester :
- T1..T4 ;
- T1 compare T4 année précédente ;
- distribution SNCC courante ;
- quatre trimestres INFC ;
- synthèse lorsqu'il existe une alerte critique ;
- synthèse lorsqu'il n'existe aucun INFC validé.

## Annuel

Tester :
- année N ;
- comparaison N/N-1 ;
- quatre séries trimestrielles ;
- incidents ;
- revues qualité ;
- échecs de sauvegarde.

## Baromètre

Tester :
- période par défaut ;
- période personnalisée ;
- end < start -> 422 ;
- aucune règle de trois FUCCS -> INFC ;
- aucun score composite inventé.

## Public

Sans configuration :

```text
GET /api/v1/public/indicators -> 404
```

Puis :
1. publier `PUBLIC_DASHBOARD_INDICATORS` ;
2. créer la publication liée ;
3. soumettre ;
4. approuver ;
5. publier ;
6. retester.

Vérifier :
- seules les clés allowlistées sont retournées ;
- une clé inconnue est ignorée ;
- aucun UUID entreprise/certification ;
- aucun numéro certificat ;
- aucun contact ;
- aucun document ;
- aucune coordonnée individuelle.

## Contrôle technique

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_dashboard_permissions
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m alembic check
```

Attendu :

```text
No new upgrade operations detected.
```
