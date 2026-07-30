# Déploiement — Correctif normes Intégration BNEC V4.1

**Date :** 29 juillet 2026  
**Migration Alembic :** aucune.  
**Prérequis :** lot Intégration BNEC/Codification V4 déjà installé.

## 1. Fichiers du correctif

```text
app/rules/norme_matching.py
app/repositories/validation_bnec_repository.py
app/services/codification_service.py
app/services/validation_bnec_service.py
tests/unit/test_norme_matching.py
FEUILLE_DE_ROUTE_BACKEND_HAUQE_CERTIF(43).md
```

## 2. Sauvegarde serveur

```bash
cd /var/www/api_hauqe
mkdir -p backups/bnec-normes-v4-1/app/{rules,repositories,services}

cp app/repositories/validation_bnec_repository.py \
  backups/bnec-normes-v4-1/app/repositories/
cp app/services/codification_service.py \
  backups/bnec-normes-v4-1/app/services/
cp app/services/validation_bnec_service.py \
  backups/bnec-normes-v4-1/app/services/
```

## 3. Installation Bash — Contabo

```bash
cd /var/www/api_hauqe
unzip -o HAUQE_CORRECTIF_NORMES_INTEGRATION_BNEC_V4_1.zip

source .venv/bin/activate
python -m py_compile \
  app/rules/norme_matching.py \
  app/repositories/validation_bnec_repository.py \
  app/services/codification_service.py \
  app/services/validation_bnec_service.py

pytest -q tests/unit/test_norme_matching.py tests/unit/test_codification_rules.py

sudo systemctl restart sngsc
sudo systemctl status sngsc --no-pager -l
curl -fsS http://127.0.0.1:8014/api/v1/health
```

## 4. Installation PowerShell — environnement local

Depuis la racine du projet :

```powershell
Expand-Archive `
  -Path .\HAUQE_CORRECTIF_NORMES_INTEGRATION_BNEC_V4_1.zip `
  -DestinationPath . `
  -Force

.\.venv\Scripts\python.exe -m py_compile `
  app\rules\norme_matching.py `
  app\repositories\validation_bnec_repository.py `
  app\services\codification_service.py `
  app\services\validation_bnec_service.py

.\.venv\Scripts\python.exe -m pytest -q `
  tests\unit\test_norme_matching.py `
  tests\unit\test_codification_rules.py
```

Aucune commande `alembic upgrade head` n'est nécessaire pour ce correctif.

## 5. Action obligatoire dans l'interface

Le plan actuel conserve encore les anciens blocages en base. Après redémarrage :

```text
Intégration BNEC
→ ouvrir le dossier
→ cliquer sur Actualiser l'analyse
```

Le serveur reconstruit alors les éléments et relit les deux modèles publiés.

## 6. Résultat attendu

Pour une norme absente mais exploitable :

```text
Modèles manquants : aucun
Norme à créer automatiquement : ISO 9001 — version 2015
Code de certification proposé : visible
État : Prête à intégrer
```

Pour une norme déjà présente sous une variante de saisie :

```text
Norme rapprochée : ISO 9001 — version 2015
État : Prête à intégrer
```

Pour une ambiguïté réelle :

```text
Intégration bloquée
Norme ambiguë dans le référentiel (...candidats...)
```

## 7. Contrôles PostgreSQL après intégration

```sql
SELECT id, code, nom, version, statut, created_at
FROM normes
ORDER BY created_at DESC
LIMIT 20;

SELECT id, norme_declaree, certification_officielle_id,
       statut_rapprochement
FROM certifications_declarees
ORDER BY updated_at DESC
LIMIT 20;

SELECT action, categorie, ressource_type, ressource_id,
       valeurs_apres, date_evenement
FROM evenements_audit
WHERE action = 'BNEC_NORME_AUTO_CREATE'
ORDER BY date_evenement DESC
LIMIT 20;
```

## 8. Journaux

```bash
journalctl -u sngsc -f
```
