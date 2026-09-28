# Déploiement consolidé SNGSC / HAUQE Certif — 28 septembre 2026

Ce guide prépare **le déploiement de ce soir**. Il ne constate pas l'état réel du
serveur : relever d'abord son commit, sa révision Alembic et ses modifications
locales. Ne pas exécuter les blocs suivants à l'aveugle. Les commandes Linux
sont prévues pour `/var/www/api_hauqe`, la base `hauqe_certif` et le service
`sngsc`, tels qu'indiqués dans la feuille de route d'hébergement.

## 1. Ce qui sera livré

Le dépôt local comporte quatre commits datés des 14, 16, 21 et 27 septembre,
**plus de nombreuses modifications encore non commitées** et plusieurs fichiers
nouveaux. Un `git pull` sur le serveur ne peut transférer que ce qui a été
commité et poussé. Avant le déploiement, vérifier la liste exacte des fichiers,
en particulier la migration `j5f9b3d7e1a2` et les scripts `sync_*`.

**Base PostgreSQL modifiée : oui.** La tête Alembic locale est
`j5f9b3d7e1a2`. Depuis `d9f2a7c4e318`, la chaîne comporte :

| Révision | Effet principal |
| --- | --- |
| `f7a1e2c3d4b5` | Identifiant juridique complémentaire des entreprises. |
| `b4c8d1e2f3a6` | Plans d'alerte propres aux certifications (JSONB). |
| `e1b7c4d9a206` | Dossier et responsable de collecte ; rapproche les fiches historiques d'une même entreprise/mission comme révisions. |
| `g2c8d4e1f509` | Lien entre certification déclarée et organisme. |
| `h3d9e4f1a607` | Marque les offres historiques répétées `DOUBLON_ANNULE` et ajoute un index d'unicité. |
| `i4e8a2c6d0b4` | Rapproche les organismes historiques ; peut précréer des organismes `A_VERIFIER`. |
| `j5f9b3d7e1a2` | `preferences_utilisateur.courriels_systeme_actifs`, à `TRUE` par défaut. |

Ces migrations **ne suppriment pas physiquement les collectes, offres ou
certifications**, mais certaines réécrivent leurs liens ou leur statut. Les
scripts de permissions et l'éventuelle reprise des offres modifient également
des données. Faire une sauvegarde testable avant toute opération.

Si le serveur est en deçà de `d9f2a7c4e318`, `alembic upgrade head` traversera
**aussi les migrations plus anciennes** : examiner l'historique et leurs
prérequis avant de continuer. Ne jamais faire `alembic stamp head` pour sauter
une migration.

## 2. Sur le poste local, avant de pousser

Dans le dossier du projet, avec PowerShell :

```powershell
git status --short --branch
git diff --stat
git diff --check
& .\.venv\Scripts\python.exe -m alembic heads
& .\.venv\Scripts\python.exe -m pytest -q tests/unit
```

Au contrôle du 28/09 : une seule tête `j5f9b3d7e1a2` et 37 tests unitaires
réussis. Ces contrôles ne prouvent pas la compatibilité avec les données du
serveur. Vérifier les modifications et les fichiers nouveaux, puis **ne
commiter que les fichiers validés pour cette livraison**. Les répertoires
`backups/` et certains fichiers de `uploads/` sont historiquement suivis par
Git : ne pas les ajouter à un commit ni publier de nouveau dump, document,
`.env` ou secret. Vérifier aussi la confidentialité du dépôt distant.

Exemple de périmètre à sélectionner **après revue**, à adapter si d'autres
fichiers fonctionnels sont réellement nécessaires : `app/`, `alembic/`,
`scripts/`, `tests/`, `.env.example` et `docs_md/feuilles_de_route/`.
Contrôler `git diff --cached --stat` et `git diff --cached --name-only` avant
`git commit`, puis pousser la branche effectivement utilisée par le serveur.
Ne pas lancer `git add -A` à la racine. Conserver les données et la configuration
propres au serveur hors du commit.

## 3. Sur le serveur : relevé et arrêt de décision

```bash
cd /var/www/api_hauqe
git status --short --branch
git rev-parse HEAD
git branch --show-current
sudo -u postgres psql -d hauqe_certif -Atc 'SELECT version_num FROM alembic_version;'
df -h /var/www/api_hauqe
```

Si `git status` montre des fichiers modifiés ou non suivis **dans les chemins
qui seront remplacés**, s'arrêter et les sauvegarder/qualifier : ne pas faire
de `git reset`, `checkout` ou `clean`. Si la révision Alembic est inconnue du
code local ou s'il y a plusieurs têtes, s'arrêter. Si la base n'est pas
`hauqe_certif` ou que le service n'est pas `sngsc`, adapter les commandes
seulement après vérification de la configuration serveur.

Contrôle préalable à la migration `e1b7c4d9a206`, si elle n'est pas encore
appliquée :

```bash
sudo -u postgres psql -d hauqe_certif -c \
  'SELECT count(*) AS collectes_sans_collecteur FROM fiches_collecte WHERE collecte_par_id IS NULL;'
```

Le résultat doit être `0` : cette migration rend `responsable_id` obligatoire
en reprenant `collecte_par_id`. Si ce n'est pas le cas, arrêter et corriger
le plan de migration avant de poursuivre, sans modifier les données à la main.

## 4. Sauvegarde et fenêtre de maintenance

Les commandes suivantes supposent une session SSH ayant `sudo`. Le répertoire
de sauvegarde est **hors Git** et réservé à l'administrateur. Prévoir une
fenêtre d'indisponibilité : arrêter l'application avant le dump et ne la
redémarrer qu'après migrations et scripts réussis.

```bash
sudo install -d -m 700 /var/backups/hauqe_certif
cd /var/www/api_hauqe
sudo systemctl stop sngsc
DEPLOY_STAMP=$(date +%Y%m%d-%H%M%S)
sudo sh -c "sudo -u postgres pg_dump -Fc hauqe_certif > /var/backups/hauqe_certif/pre-${DEPLOY_STAMP}.dump"
sudo pg_restore -l "/var/backups/hauqe_certif/pre-${DEPLOY_STAMP}.dump" >/dev/null
sudo ls -lh "/var/backups/hauqe_certif/pre-${DEPLOY_STAMP}.dump"
sudo tar -C /var/www/api_hauqe -czf "/var/backups/hauqe_certif/uploads-${DEPLOY_STAMP}.tar.gz" uploads
sudo install -m 600 .env "/var/backups/hauqe_certif/env-${DEPLOY_STAMP}.bak"
```

Le dump PostgreSQL ne comprend **pas** les fichiers `uploads/`, ni `.env`.
Vérifier que les trois sauvegardes existent, sont lisibles et stockées sur un
volume avec assez d'espace. Ne pas diffuser le dump ni la copie de `.env`.
Si l'une des sauvegardes échoue, ne pas migrer et remettre le service en route.

## 5. Code, dépendances, migration

```bash
cd /var/www/api_hauqe
git fetch origin
git pull --ff-only
git rev-parse HEAD
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m alembic heads
python -m alembic current
python -m alembic history -r base:head
python -m alembic upgrade head
python -m alembic current
```

La révision affichée après migration doit être **`j5f9b3d7e1a2`**, si la
livraison locale complète a été poussée. Vérifier le résultat de **chaque**
commande ; une erreur de `git pull`, de `pip` ou d'Alembic interdit la suite.
Ne pas démarrer le nouveau code avec l'ancien schéma.

## 6. Permissions et reprise métier

Après migration, depuis le même venv :

```bash
python -m app.scripts.seed_verification_fuccs_permissions
python -m app.scripts.sync_workflow_communication_permissions
python -m app.scripts.seed_scoring_permissions
python -m app.scripts.sync_direction_consultation_dossiers
python -m app.scripts.sync_agent_collecte_organismes_create
python -m app.scripts.sync_verificateur_collecte_read
```

Ces scripts sont prévus pour être relancés sans doubler les attributions.
Le dernier **retire volontairement** `VERIFICATION.AFFECTER` au rôle
`VERIFICATEUR` et maintient `COLLECTE.LIRE` : ne pas l'omettre ni exécuter
ensuite un ancien seed qui rétablirait ce droit. Les autres scripts ajoutent
les droits de contrôle, de notification personnelle et de calculs à la CVC.
Ne pas lancer `bootstrap_security` sur un serveur déjà initialisé.

Reprise des offres des collectes déjà soumises dans les fiches entreprises :

```bash
python -m app.scripts.synchronize_collection_offers_to_enterprise --all
```

Cette commande est un **aperçu sans écriture**. Après lecture du nombre de
fiches concernées et si cette reprise des données historiques est souhaitée :

```bash
python -m app.scripts.synchronize_collection_offers_to_enterprise --all --apply
```

La seconde commande écrit des offres d'entreprise et des traces d'audit ; elle
ne traite pas les brouillons. Elle n'est pas nécessaire au démarrage du code.
Ne pas confondre cette reprise avec une migration Alembic. En cas de doute sur
le volume ou les rapprochements, la reporter après une recette ciblée.

## 7. Configuration, redémarrage et recette

Dans `.env` serveur, **vérifier sans afficher les secrets dans un journal** :

- `LIEN_VERS_SNGSC` : véritable URL publique utilisable par les agents, avec
  `https://` et le chemin réel (`/sngsc` uniquement si le proxy le sert ainsi) ;
- `PASSWORD_RESET_EXPIRE_MINUTES=3` et URL de réinitialisation valide ;
- `HAUQE_SMTP_*` fonctionnels ; `HAUQE_CONTACT_*` si la signature est voulue ;
- conserver les valeurs existantes de `DATABASE_URL`, clés de session et
  `MFA_FERNET_KEY` ; **ne jamais écraser `.env` avec `.env.example`**.

```bash
sudo systemctl start sngsc
sudo systemctl status sngsc --no-pager
sudo journalctl -u sngsc -n 100 --no-pager
curl -fsS http://127.0.0.1:8014/api/v1/health
```

Ne pas lancer un second worker SMTP : il est déjà inclus dans le service.
Après déploiement, tester avec des comptes de rôles distincts : connexion,
notifications et préférences de courriels, campagne → mission → collecte,
vérification/FUCCS/validation/intégration, pièces jointes, scoring/INFC/SNCC,
et réception effective d'un **nouveau** courriel. Les courriels d'événements
antérieurs ne sont pas rejoués. Forcer un rechargement du navigateur pour les
nouveaux JS/CSS. Vérifier qu'une matrice SNCC est publiée si le calcul
automatique doit être utilisé.

En cas d'échec, **ne pas faire de downgrade Alembic ni de restauration
partielle improvisée** : garder le service arrêté, relever l'erreur et les
révisions, puis décider d'une restauration complète base + uploads + code
compatible à partir des sauvegardes du même instant. Le dump est l'outil de
retour arrière, pas `alembic stamp`.
