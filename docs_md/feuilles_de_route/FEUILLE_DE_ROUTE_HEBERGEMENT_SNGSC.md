# Feuille de route d’intégration et d’hébergement Linux — SNGSC / HAUQE Certif

**Projet :** SNGSC / HAUQE Certif  
**Serveur MVP :** Contabo — `31.220.87.142`  
**Répertoire applicatif :** `/var/www/api_hauqe`  
**Base PostgreSQL :** `hauqe_certif`  
**Service applicatif prévu :** `sngsc.service`  
**Port interne FastAPI :** `127.0.0.1:8014`  
**Dernière mise à jour :** 3 août 2026  
**Règle de validation :** une étape n’est marquée terminée qu’après contrôle réel sur le serveur.

## 0. Procédure canonique sans oubli

Cette section est la procédure de référence pour une première installation et
pour chaque mise à jour. Les sections historiques qui suivent restent utiles
pour le diagnostic, mais ne remplacent pas cette séquence.

Ordre de lecture :

- **nouveau serveur** : 0.4 jusqu'au clonage et à la création du venv, puis
  0.2, 0.3, 0.5, 0.6, 0.9 et 0.8 ;
- **serveur déjà installé** : 0.7, puis 0.8 ;
- **incident** : 0.10, sans contourner les contrôles des sections 0.5 et 0.6.

### 0.1 Principes obligatoires

- ne jamais lancer l'application avec un code plus récent que le schéma
  PostgreSQL ;
- exécuter les migrations après le `git pull` et avant le redémarrage final ;
- ne jamais utiliser `alembic stamp` pour masquer une migration non exécutée ;
- sauvegarder la base avant toute mise à jour contenant une migration ;
- conserver la même `MFA_FERNET_KEY` tant que des comptes MFA existent ;
- ne jamais placer un mot de passe, une clé SMTP ou une clé MFA dans Git ;
- exécuter les scripts depuis `/var/www/api_hauqe`, environnement virtuel
  activé ;
- vérifier le résultat de chaque commande avant de passer à la suivante.

### 0.2 Variables de production indispensables

Le fichier `/var/www/api_hauqe/.env` doit appartenir au compte du service et
être limité à ce compte :

```bash
cd /var/www/api_hauqe
sudo chown sngsc:sngsc .env
sudo chmod 600 .env
```

Valeurs attendues, sans recopier les exemples littéralement :

```dotenv
APP_NAME=HAUQE Certif
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+psycopg://UTILISATEUR:MOT_DE_PASSE@localhost:5432/hauqe_certif
SECRET_KEY=UNE_CLE_LONGUE_ALEATOIRE
ACCESS_TOKEN_EXPIRE_MINUTES=30
MFA_FERNET_KEY=LA_CLE_FERNET_STABLE_DU_SERVEUR
PASSWORD_RESET_URL_TEMPLATE=https://DOMAINE/#/mot-de-passe-oublie?token={token}
TIMEZONE=Africa/Lome
HAUQE_SMTP_HOST=smtp.gmail.com
HAUQE_SMTP_PORT=587
HAUQE_SMTP_USER=ADRESSE_EXPEDITRICE
HAUQE_SMTP_PASSWORD=MOT_DE_PASSE_APPLICATION
HAUQE_SMTP_FROM=ADRESSE_EXPEDITRICE
HAUQE_SMTP_USE_TLS=true
AUTH_SESSION_MINUTES=480
AUTH_IDLE_TIMEOUT_MINUTES=30
AUTH_MAX_FAILED_ATTEMPTS=5
AUTH_FAILURE_WINDOW_MINUTES=15
AUTH_LOCKOUT_MINUTES=15
```

Les noms `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD` et `MAIL_FROM` ne
sont pas ceux lus par la configuration actuelle. En production, utiliser les
variables `HAUQE_SMTP_*` ci-dessus.

Génération des clés :

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

La seconde commande sert uniquement à la première création de la clé MFA.
Ne jamais régénérer cette clé lors d'un simple déploiement.

### 0.3 Préparation des répertoires d'exécution

Créer le compte système uniquement s'il n'existe pas :

```bash
id sngsc
sudo useradd --system --home /var/www/api_hauqe \
  --shell /usr/sbin/nologin sngsc
```

Si `id sngsc` retourne déjà le compte, ne pas relancer `useradd`.

```bash
cd /var/www/api_hauqe
sudo install -d -o sngsc -g sngsc -m 750 logs backups uploads
sudo chmod 750 logs backups uploads
```

Cette étape évite notamment l'erreur :
`PermissionError: [Errno 13] Permission denied: '/var/www/api_hauqe/logs'`.

### 0.4 Première installation

```bash
cd /var/www
git clone URL_DU_DEPOT api_hauqe
cd /var/www/api_hauqe

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Créer ensuite `.env`, les répertoires privés, la base PostgreSQL et son rôle
applicatif. Contrôler la connexion avant de migrer :

Création initiale de la base, avec un mot de passe propre au serveur :

```bash
sudo -u postgres psql
```

Puis dans `psql` :

```sql
CREATE ROLE hauqe_app LOGIN PASSWORD 'REMPLACER_PAR_UN_MOT_DE_PASSE_FORT';
CREATE DATABASE hauqe_certif OWNER hauqe_app;
\connect hauqe_certif
CREATE EXTENSION IF NOT EXISTS pgcrypto;
GRANT ALL ON SCHEMA public TO hauqe_app;
\quit
```

Si le rôle ou la base existe déjà, ne pas relancer les commandes `CREATE`.

```bash
source .venv/bin/activate
python -c "from app.config.settings import settings; print(settings.environment, settings.database_url.split('@')[-1])"
```

Ne jamais afficher la partie contenant le mot de passe.

### 0.5 Migrations Alembic - chaîne complète

Ordre versionné actuel :

| Ordre | Révision | Objet |
|---:|---|---|
| 1 | `9f89b5d85b6a` | Schéma initial des 66 tables |
| 2 | `c5b7a8f2d901` | Extension sécurité du compte |
| 3 | `d8e9f4a7c210` | Traçabilité de codification BNEC |
| 4 | `e1f0a2b3c4d5` | Motif de clôture des échéances |
| 5 | `f4c7d8e9a012` | Message de confirmation |
| 6 | `a2b3c4d5e6f7` | Message et courriel des relances |
| 7 | `b3c4d5e6f7a8` | Préférences d'actualisation automatique |
| 8 | `c4d5e6f7a8b9` | Situations `EXPIREE` et `AUDIT_INITIAL` |

Commandes obligatoires :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate

alembic heads
alembic current
alembic upgrade head
alembic current
alembic heads
```

Résultat attendu après la mise à jour du 3 août 2026 :

```text
c4d5e6f7a8b9 (head)
```

Contrôles PostgreSQL :

```bash
sudo -u postgres psql -d hauqe_certif -c "SELECT version_num FROM alembic_version;"
sudo -u postgres psql -d hauqe_certif -c "\d preferences_utilisateur"
sudo -u postgres psql -d hauqe_certif -c "\d certifications_declarees"
```

Les colonnes suivantes doivent exister dans `preferences_utilisateur` :

- `actualisation_automatique_active` ;
- `actualisation_intervalle_secondes` ;
- `actualisation_au_retour`.

La colonne `certifications_declarees.situation_declaree` et la contrainte
`ck_certifications_declarees_situation` doivent accepter notamment
`EXPIREE` et `AUDIT_INITIAL`.

#### Cas du correctif SQL historique 2.0

Le fichier `migrations/20260729_correction_2_0.sql` est conservé comme outil
de réparation pour une ancienne base. La migration Alembic
`c4d5e6f7a8b9` crée désormais la colonne manquante et remplace sa contrainte.
Sur une installation normale, exécuter seulement `alembic upgrade head`.

N'exécuter le SQL historique qu'après diagnostic explicite d'une ancienne
base non alignée :

```bash
sudo -u postgres psql -d hauqe_certif \
  -f migrations/20260729_correction_2_0.sql
alembic upgrade head
```

### 0.6 Initialisation de la sécurité et des permissions

#### Première installation uniquement

Le bootstrap est interactif et demande l'identité du premier administrateur :

```bash
python -m app.scripts.bootstrap_security
```

Il crée ou complète le rôle `ADMIN_HAUQE`, le catalogue initial de permissions
et le premier compte administrateur. Le mot de passe doit contenir au moins
12 caractères.

#### Première installation et resynchronisation après mise à jour RBAC

Exécuter dans cet ordre :

```bash
python -m app.scripts.seed_business_roles
python -m app.scripts.seed_role_permission_matrix
python -m app.scripts.seed_certification_domain_permissions
python -m app.scripts.seed_verification_fuccs_permissions
python -m app.scripts.seed_validation_integration_permissions
python -m app.scripts.seed_scoring_permissions
python -m app.scripts.seed_watch_permissions
python -m app.scripts.seed_dashboard_permissions
python -m app.scripts.seed_governance_permissions
python -m app.scripts.seed_presence_permission
```

Ces scripts synchronisent les permissions et leurs attributions. Ils doivent
être lancés après la création des rôles métier. Lire leur résumé final et
traiter tout message « Rôle absent » avant de redémarrer l'application.

Contrôles rapides :

```bash
sudo -u postgres psql -d hauqe_certif -c "SELECT code, libelle, statut FROM roles ORDER BY niveau DESC;"
sudo -u postgres psql -d hauqe_certif -c "SELECT COUNT(*) AS permissions FROM permissions;"
sudo -u postgres psql -d hauqe_certif -c "SELECT COUNT(*) AS attributions FROM role_permission;"
```

### 0.7 Mise à jour quotidienne après un `git pull`

```bash
cd /var/www/api_hauqe
git status --short
git branch --show-current
git fetch origin
git pull --ff-only

source .venv/bin/activate
python -m pip install -r requirements.txt

mkdir -p backups
sudo -u postgres pg_dump -Fc hauqe_certif \
  > "backups/pre-deploiement-$(date +%Y%m%d-%H%M%S).dump"

alembic heads
alembic current
alembic upgrade head
alembic current
```

Si la mise à jour touche les rôles ou permissions, exécuter également la
séquence complète des seeds de la section 0.6.

Puis :

```bash
sudo chown -R sngsc:sngsc logs backups uploads
sudo systemctl restart sngsc
sudo systemctl status sngsc --no-pager
sudo journalctl -u sngsc -n 100 --no-pager
```

Ne pas continuer si `alembic upgrade head` échoue. Corriger la migration avant
de relancer le service.

### 0.8 Contrôles applicatifs après redémarrage

```bash
curl -fsS http://127.0.0.1:8014/api/v1/health
curl -I http://127.0.0.1:8014/
curl -I https://DOMAINE/
```

Recette minimale dans le navigateur :

1. connexion et déconnexion ;
2. profil et préférences de rafraîchissement ;
3. MFA avec code OTP à six chiffres ;
4. mot de passe oublié et réception du courriel ;
5. création ou reprise d'une collecte ;
6. dépôt d'un justificatif ;
7. notifications et échéances ;
8. consultation des journaux et sauvegardes.

Le frontend doit conserver :

```javascript
apiBaseUrl: window.location.origin
```

Ne jamais déployer une configuration contenant `localhost:8001` dans le
navigateur du serveur.

### 0.9 Services de fond

La file SMTP et les sauvegardes planifiées sont lancées dans le cycle de vie
FastAPI par `app.tasks.run_background_services`. Elles ne nécessitent pas un
second lancement manuel lorsque `sngsc.service` exécute `app.main:app`.

Cette architecture impose **un seul worker Uvicorn**. Plusieurs workers
lanceraient plusieurs boucles de courriels et de sauvegardes. Un service
conforme peut être créé ainsi :

```ini
[Unit]
Description=SNGSC - HAUQE Certif FastAPI
After=network.target postgresql.service

[Service]
Type=simple
User=sngsc
Group=sngsc
WorkingDirectory=/var/www/api_hauqe
EnvironmentFile=/var/www/api_hauqe/.env
ExecStart=/var/www/api_hauqe/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8014 --workers 1
Restart=always
RestartSec=5
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

Installation ou actualisation de l'unité :

```bash
sudo nano /etc/systemd/system/sngsc.service
sudo systemctl daemon-reload
sudo systemctl enable sngsc
sudo systemctl restart sngsc
```

Si plusieurs workers deviennent nécessaires, extraire d'abord
`run_background_services` dans un service systemd distinct avant d'augmenter
`--workers`.

Contrôler leur activité :

```bash
sudo journalctl -u sngsc --since "30 minutes ago" --no-pager
ls -lah logs backups uploads
```

### 0.10 Gestion sûre des erreurs

- `UndefinedColumn` après un pull : exécuter `alembic upgrade head`, puis
  redémarrer ;
- permission refusée sur `logs`, `backups` ou `uploads` : corriger le
  propriétaire et les modes de ces répertoires ;
- API appelée sur `localhost:8001` depuis le navigateur : restaurer
  `window.location.origin` dans la configuration frontend ;
- courriel absent : vérifier les variables `HAUQE_SMTP_*`, le mot de passe
  d'application, les journaux et le pare-feu sortant sur le port 587 ;
- erreur MFA après changement de serveur : restaurer exactement l'ancienne
  `MFA_FERNET_KEY` ;
- changements locaux bloquant `git pull` : sauvegarder ou abandonner
  explicitement ces fichiers avant le pull ; ne jamais forcer sans identifier
  ce qui sera perdu.

### 0.11 Interdictions de production

- ne pas lancer `alembic downgrade` sans sauvegarde et plan de retour ;
- ne pas exécuter `DROP`, `TRUNCATE`, `git reset --hard` ou une restauration
  complète par réflexe ;
- ne pas publier `.env`, les archives de sauvegarde ou les fichiers envoyés ;
- ne pas modifier directement `alembic_version` ;
- ne pas relancer `bootstrap_security` pour créer un utilisateur ordinaire ;
- ne pas afficher les secrets dans les journaux ou dans une capture d'écran.

## 1. État synthétique

| Étape | Statut | Contrôle attendu |
|---|---|---|
| Préparation du serveur Linux | Terminée | Accès SSH opérationnel |
| Installation PostgreSQL | Terminée | Service PostgreSQL actif |
| Création du rôle `hauqe_app` | Terminée | Connexion applicative réussie |
| Création de la base `hauqe_certif` | Terminée | Base accessible |
| Clonage Git dans `/var/www/api_hauqe` | Terminée | Dépôt complet présent |
| Environnement virtuel Python | Terminée | `.venv` fonctionnel |
| Installation des dépendances | Terminée | Imports principaux réussis |
| Configuration `.env` | Terminée | Paramètres chargés |
| Migrations Alembic | À remettre à niveau après le pull du 03/08 | `alembic current` doit afficher `c4d5e6f7a8b9 (head)` |
| Correction SQL 2.0 | Intégrée à Alembic | Colonne et contrainte `situation_declaree` gérées par `c4d5e6f7a8b9` |
| Initialisation rôles et permissions | Terminée | Scripts de seed exécutés |
| Test FastAPI local | Terminée | `/api/v1/health` retourne `status=ok` |
| Service systemd `sngsc` | Terminée | Service déclaré opérationnel par l’utilisateur |
| Mise à jour applicative du 03/08/2026 | À finaliser sur le serveur | Pull, sauvegarde, migrations, seeds nécessaires et redémarrage contrôlé |
| Worker courriels et sauvegardes | Intégré au service | Tâche démarrée par le cycle de vie FastAPI |
| Répertoires d’exécution privés | Terminée | `logs`, `backups` et `uploads` accessibles à `sngsc` |
| Reverse proxy Nginx | Terminée pour le test HTTP | Application accessible sous `/sngsc/` |
| Adresse API du frontend | Corrigée | Même origine que l’interface, sans `localhost` codé en dur |
| Clé MFA du serveur | À configurer et valider | Clé Fernet présente dans `.env`, service redémarré et enrôlement MFA testé |
| Réinitialisation du mot de passe | Corrigée, recette à faire | Modèle d’URL chargé, courriel reçu et lien consommé une seule fois |
| DNS du sous-domaine | Prochaine étape | Résolution vers `31.220.87.142` |
| Certificat HTTPS | À faire | Certificat Let’s Encrypt valide |
| Durcissement Nginx et application | À faire | En-têtes, limites, permissions |
| Sauvegardes PostgreSQL | À faire | Sauvegarde et restauration testées |
| Sauvegarde des documents | À faire | Répertoires privés sauvegardés |
| Journalisation et supervision | À faire | Journaux consultables et rotation |
| Recette MVP publique | À faire | Parcours prioritaires validés |
| Documentation d’exploitation | À faire | Procédure de mise à jour et reprise |
| Clôture de l’hébergement MVP | À faire | Procès-verbal technique interne |

## 2. Architecture cible

```text
Utilisateur
    ↓ HTTPS 443
Nginx
    ↓ proxy HTTP local
FastAPI / Uvicorn — 127.0.0.1:8014
    ↓
PostgreSQL — 127.0.0.1:5432
    ↓
Base hauqe_certif
```

PostgreSQL et Uvicorn ne doivent pas être exposés directement à Internet.

## 3. Phase A — Service applicatif systemd

**Statut : terminée et validée par l’utilisateur le 29 juillet 2026.**

**Configuration retenue :**

```text
Service        : sngsc.service
Utilisateur    : sngsc
Groupe         : sngsc
Application    : /var/www/api_hauqe
Python         : /var/www/api_hauqe/.venv/bin/python
Serveur ASGI   : Uvicorn
Module         : app.main:app
Adresse        : 127.0.0.1
Port interne   : 8014
Journaux       : systemd-journald
Démarrage      : automatique
Redémarrage    : automatique en cas d’arrêt anormal
Tâches internes : courriels toutes les 10 s, sauvegardes planifiées chaque heure
```

### A.1 Objectifs

- exécuter FastAPI sous un utilisateur système non privilégié ;
- démarrer automatiquement au redémarrage du serveur ;
- redémarrer le service en cas d’arrêt anormal ;
- conserver les journaux dans `journald` ;
- écouter uniquement sur `127.0.0.1:8014`.

### A.2 Contrôles de sortie

```bash
systemctl is-active sngsc
systemctl is-enabled sngsc
curl -fsS http://127.0.0.1:8014/api/v1/health
ss -ltnp | grep ':8014'
```

Résultats attendus :

- `active`
- `enabled`
- réponse JSON avec `status: ok`
- écoute uniquement sur `127.0.0.1:8014`

**Validation enregistrée :** le service permanent du SNGSC est considéré opérationnel sur le serveur. Les sorties détaillées de `systemctl`, `curl` et `ss` pourront être annexées lors de la recette technique finale.

**Validation complémentaire :** l’application répond désormais via Nginx sous `http://31.220.87.142/sngsc/`, et la connexion applicative à PostgreSQL fonctionne.

### A.3 Services d’arrière-plan intégrés

Le worker n’est pas exploité comme un second service systemd. Il est lancé par
le `lifespan` FastAPI dans `app.main` lorsque `sngsc.service` démarre.

Il prend en charge :

- la file de notifications et les envois SMTP ;
- les sauvegardes planifiées ;
- l’arrêt propre de la tâche lorsque le service applicatif s’arrête.

Le redémarrage de `sngsc.service` redémarre donc également ces traitements :

```bash
sudo systemctl restart sngsc
sudo journalctl -u sngsc -n 100 --no-pager
```

Il ne faut pas lancer simultanément `python -m app.tasks.run_background_services`
sur le même serveur, afin d’éviter deux workers concurrents.

## 4. Phase B — Nginx

### B.1 Objectifs

- créer un virtual host distinct pour le SNGSC ;
- transmettre les en-têtes `Host`, `X-Real-IP`, `X-Forwarded-For` et `X-Forwarded-Proto` ;
- limiter la taille des téléversements ;
- appliquer des délais adaptés ;
- ne pas rendre les dossiers `uploads` accessibles directement.

### B.2 Contrôles de sortie

```bash
nginx -t
systemctl reload nginx
curl -I http://DOMAINE_SNGSC
```

### B.3 Adresse de l’API utilisée par le navigateur

Le port `8014` est un port interne réservé à Nginx et ne doit pas être appelé
directement par le navigateur. Le frontend doit utiliser la même origine que
l’interface :

```javascript
export const APP_CONFIG = Object.freeze({
  apiBaseUrl: window.location.origin,
  apiPrefix: "/api/v1",
  defaultRoute: "dashboard",
  appName: "HAUQE Certif",
  requestTimeoutMs: 15000,
});
```

Nginx reçoit ainsi les requêtes publiques telles que :

```text
https://DOMAINE_SNGSC/api/v1/auth/login
```

et les transmet au service FastAPI sur :

```text
http://127.0.0.1:8014/api/v1/auth/login
```

Ne jamais utiliser `http://localhost:8001` dans la configuration frontend de
production. Dans le navigateur d’un agent, `localhost` désigne son propre
ordinateur et provoque `ERR_CONNECTION_REFUSED`.

Après une mise à jour de cette configuration :

```bash
sudo systemctl restart sngsc
```

Effectuer ensuite un rechargement forcé du navigateur avec `Ctrl + Shift + R`
ou vider le cache du site. Dans l’onglet Réseau des outils de développement,
l’URL de connexion doit utiliser l’adresse publique du SNGSC et ne doit plus
contenir `localhost:8001`.

## 5. Phase C — DNS et HTTPS

### C.1 DNS

Créer un enregistrement de type `A` :

```text
DOMAINE_SNGSC → 31.220.87.142
```

### C.2 HTTPS

Installer un certificat Let’s Encrypt avec Certbot, puis vérifier :

```bash
certbot certificates
curl -I https://DOMAINE_SNGSC
```

## 6. Phase D — Sécurité minimale du MVP

- garder `.env` hors Git ;
- conserver les secrets SMTP uniquement dans `.env` ;
- interdire l’accès public à PostgreSQL ;
- exécuter FastAPI sans privilèges root ;
- limiter les permissions sur `.env` et les fichiers privés ;
- activer le pare-feu uniquement pour SSH, HTTP et HTTPS ;
- protéger les téléversements privés ;
- vérifier les cookies et en-têtes de sécurité ;
- ne pas activer `/docs` publiquement sans décision explicite ;
- conserver les opérations sensibles dans le journal d’audit.

### D.1 Permissions des répertoires d’exécution

Le service fonctionne avec l’utilisateur et le groupe `sngsc`. Le code source
reste en lecture seule pour ce compte, mais les répertoires utilisés à
l’exécution doivent lui appartenir :

```bash
sudo install -d -o sngsc -g sngsc -m 0750 /var/www/api_hauqe/logs
sudo install -d -o sngsc -g sngsc -m 0750 /var/www/api_hauqe/backups
sudo install -d -o sngsc -g sngsc -m 0750 /var/www/api_hauqe/uploads
sudo install -d -o sngsc -g sngsc -m 0750 /var/www/api_hauqe/uploads/private
sudo install -d -o sngsc -g sngsc -m 0750 /var/www/api_hauqe/app/uploads/avatars
```

Cette configuration corrige l’erreur observée au démarrage :

```text
PermissionError: [Errno 13] Permission denied: '/var/www/api_hauqe/logs'
```

Éviter un `chown -R` sur tout le dépôt. Seuls les répertoires dans lesquels
l’application écrit doivent appartenir à `sngsc`.

### D.2 Configuration et conservation de la clé MFA

Le MFA TOTP chiffre les secrets des comptes avec `MFA_FERNET_KEY`. Cette
variable est déclarée dans `app.config.settings` et doit contenir une clé
Fernet URL-safe de 32 octets encodée en Base64, soit normalement 44
caractères.

Génération pour l’environnement local Windows, depuis PowerShell :

```powershell
Set-Location "C:\Users\hp\Documents\APK WEB Projets R.1.3.5 et R1.4.3"
$mfaKey = & ".\.venv\Scripts\python.exe" -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
$mfaKey
```

Reporter une seule fois la valeur obtenue dans le fichier `.env` :

```env
MFA_FERNET_KEY=VALEUR_GENEREE
```

Puis lancer l’application locale :

```powershell
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Génération sur le serveur Linux :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Après ajout de la valeur dans `/var/www/api_hauqe/.env` :

```bash
sudo systemctl restart sngsc
sudo journalctl -u sngsc -n 50 --no-pager
```

#### D.2.1 Copier une clé Windows existante vers le serveur

Cette méthode est utile lorsque la base Windows doit être restaurée ou
reproduite sur Linux avec des comptes MFA déjà enrôlés. Si les bases sont
indépendantes et qu’aucun compte MFA n’est encore actif, il est préférable de
générer une clé différente directement sur le serveur.

Sous PowerShell, placer la clé déjà chargée dans `$mfaKey` dans le
presse-papiers :

```powershell
$mfaKey | Set-Clipboard
```

Ouvrir ensuite une session SSH :

```powershell
ssh UTILISATEUR_SERVEUR@31.220.87.142
```

Sur le serveur, ouvrir le fichier avec un éditeur privilégié :

```bash
sudoedit /var/www/api_hauqe/.env
```

Ajouter ou remplacer une seule ligne, sans chevrons ni guillemets :

```env
MFA_FERNET_KEY=COLLER_ICI_LA_CLE_DE_44_CARACTERES
```

Ne pas écrire la clé dans une commande `echo`, dans un message ou dans Git :
elle pourrait rester dans l’historique du terminal. Après enregistrement,
protéger le fichier et vérifier uniquement le format de la clé, sans
l’afficher :

```bash
sudo chown root:sngsc /var/www/api_hauqe/.env
sudo chmod 640 /var/www/api_hauqe/.env
sudo grep -qE '^MFA_FERNET_KEY=[A-Za-z0-9_-]{43}=$' /var/www/api_hauqe/.env \
  && echo "Clé MFA présente et format valide" \
  || echo "Clé MFA absente ou format invalide"
sudo systemctl restart sngsc
systemctl is-active sngsc
curl -fsS http://127.0.0.1:8014/api/v1/health
sudo journalctl -u sngsc -n 50 --no-pager
```

La clé ne doit jamais apparaître dans les sorties de contrôle. La validation
fonctionnelle finale consiste à activer le MFA sur un compte de recette, à se
déconnecter, puis à vérifier qu’une nouvelle connexion exige bien le code
TOTP.

Règles impératives :

- ne jamais enregistrer cette clé dans Git ;
- conserver la même clé entre les redémarrages et les déploiements ;
- sauvegarder la clé dans le gestionnaire de secrets de l’exploitation ;
- ne pas recopier la clé Windows sur Linux si les deux bases doivent rester
  cryptographiquement séparées ;
- ne jamais régénérer la clé d’un environnement contenant déjà des comptes
  MFA actifs, car leurs secrets deviendraient indéchiffrables.

Contrôle réalisé le 31 juillet 2026 : le raccordement de
`MFA_FERNET_KEY` aux settings Python a été corrigé. Le chiffrement Fernet,
le déchiffrement, la génération et la vérification TOTP, l’URI
d’enrôlement et la génération des codes de récupération ont été validés
avec une clé temporaire conforme. La valeur locale de 12 caractères
détectée pendant l’audit doit être remplacée avant le test utilisateur du
MFA.

## 7. Phase E — Sauvegardes

### E.1 PostgreSQL

Prévoir :

- sauvegarde quotidienne ;
- rétention locale courte ;
- copie distante ou stockage secondaire ;
- chiffrement des sauvegardes ;
- test réel de restauration.

### E.2 Documents privés

Inclure au minimum :

```text
/var/www/api_hauqe/uploads/private
/var/www/api_hauqe/app/uploads/avatars
```

## 8. Phase F — Déploiements futurs

Ordre de mise à jour recommandé :

```text
git pull
→ activation .venv
→ installation des dépendances
→ alembic upgrade head
→ scripts d’initialisation nécessaires
→ redémarrage systemd
→ test health
→ contrôle des journaux
```

Chaque mise à jour doit prévoir un point de retour et une sauvegarde préalable de la base lorsque la migration est sensible.

### F.1 Procédure de mise à jour validée pour le serveur

```bash
cd /var/www/api_hauqe
git status
git branch --show-current
git pull --ff-only origin main
source .venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head
sudo systemctl restart sngsc
systemctl is-active sngsc
curl -fsS http://127.0.0.1:8014/api/v1/health
sudo journalctl -u sngsc -n 100 --no-pager
```

Révision Alembic attendue après la mise à jour du 31 juillet 2026 :

```text
a2b3c4d5e6f7
```

Contrôle :

```bash
python -m alembic current
```

### F.2 Cas des modifications locales sur le serveur

Un pull a été bloqué parce que les fichiers suivants avaient été modifiés
directement sur le serveur :

```text
app/static/css/collecte-form.css
app/static/js/collecte-form.js
app/static/js/core/config.js
app/static/js/regles-codification.js
```

Avant remplacement, conserver une copie récupérable :

```bash
git diff > ~/sngsc-modifications-serveur-avant-remplacement.patch
```

Si la décision est de remplacer ces modifications par la version Git :

```bash
git restore -- \
  app/static/css/collecte-form.css \
  app/static/js/collecte-form.js \
  app/static/js/core/config.js \
  app/static/js/regles-codification.js

git pull --ff-only origin main
```

Cette opération ne réalise aucun push. Le fichier `.env` et les documents
téléversés ne doivent jamais être inclus dans ces remplacements.

## 9. Phase G — Recette MVP publique

Parcours prioritaires :

1. connexion administrateur ;
2. création et gestion utilisateur ;
3. zones administratives ;
4. collecte rapide d’entreprise ;
5. création et modification d’une fiche ;
6. vérification et contrôle ;
7. validation et intégration BNEC ;
8. classification, INFC et SNCC ;
9. alertes, notifications et veille ;
10. téléversement et téléchargement de document ;
11. journal d’audit ;
12. verrouillage et reprise de session.

## 10. Journal des validations d’hébergement

| Date | Étape | Résultat | Preuve / commande | Observation |
|---|---|---|---|---|
| 29/07/2026 | Base PostgreSQL | Validée par l’utilisateur | Connexion et migrations réussies | Base MVP opérationnelle |
| 29/07/2026 | Dépôt Git | Validé par l’utilisateur | Clonage dans `/var/www/api_hauqe` | Projet complet présent |
| 29/07/2026 | Alembic et initialisation | Validés par l’utilisateur | `upgrade head`, seeds et test API | Socle applicatif prêt |
| 29/07/2026 | Service systemd `sngsc` | Validé par l’utilisateur | Service permanent créé et lancement confirmé | FastAPI exploité localement sur `127.0.0.1:8014` |
| 29/07/2026 | Reverse proxy Nginx | Validé pour HTTP | Accès opérationnel sous `/sngsc/` | La page Nginx par défaut reste disponible sur `/` |
| 29/07/2026 | Connexion application ↔ PostgreSQL | Validée par l’utilisateur | Authentification fonctionnelle après stabilisation | Surveiller les journaux lors de la recette |
| 31/07/2026 | Mise à jour Git | Validée après remplacement des modifications locales | `git pull --ff-only origin main` | Une sauvegarde `.patch` a été recommandée avant remplacement |
| 31/07/2026 | Worker intégré | Chargé avec FastAPI | `app.tasks.run_background_services` lancé par le lifespan | Courriels et sauvegardes utilisent le service `sngsc` |
| 31/07/2026 | Permissions des journaux | Corrigées | Création de `/var/www/api_hauqe/logs` pour `sngsc:sngsc` | L’absence du répertoire empêchait le démarrage |
| 31/07/2026 | Connexion frontend à l’API | Corrigée | `apiBaseUrl: window.location.origin` | L’ancienne valeur `localhost:8001` provoquait `ERR_CONNECTION_REFUSED` depuis les postes utilisateurs |
| 31/07/2026 | Profil et MFA | Raccordement corrigé, configuration locale à finaliser | `mfa_fernet_key` déclaré et cycle cryptographique TOTP contrôlé | Remplacer la clé locale invalide avant l’enrôlement ; conserver ensuite la clé définitivement |

## 11. Prochaine action immédiate

Associer maintenant un domaine ou sous-domaine au SNGSC, puis activer HTTPS avec Certbot :

```text
Domaine SNGSC
→ DNS A vers 31.220.87.142
→ Nginx
→ HTTPS Let’s Encrypt
→ proxy_pass http://127.0.0.1:8014
→ service sngsc
```

Informations requises pour finaliser cette phase :

- domaine ou sous-domaine définitif du SNGSC ;
- enregistrement DNS `A` pointant vers `31.220.87.142` ;
- validation HTTP avant activation de HTTPS.

## 12. Critères de clôture


L’hébergement MVP sera considéré terminé lorsque :

- le domaine public répond exclusivement en HTTPS ;
- le service `sngsc` démarre automatiquement ;
- Nginx transmet correctement les requêtes ;
- la base reste privée ;
- les sauvegardes sont opérationnelles et restaurables ;
- les parcours MVP prioritaires sont testés ;
- les journaux et procédures d’exploitation sont documentés ;
- la feuille de route ne contient plus d’étape critique « À faire ».
