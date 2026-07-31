# Feuille de route d’intégration et d’hébergement Linux — SNGSC / HAUQE Certif

**Projet :** SNGSC / HAUQE Certif  
**Serveur MVP :** Contabo — `31.220.87.142`  
**Répertoire applicatif :** `/var/www/api_hauqe`  
**Base PostgreSQL :** `hauqe_certif`  
**Service applicatif prévu :** `sngsc.service`  
**Port interne FastAPI :** `127.0.0.1:8014`  
**Dernière mise à jour :** 31 juillet 2026
**Règle de validation :** une étape n’est marquée terminée qu’après contrôle réel sur le serveur.

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
| Migrations Alembic | Terminée | Révision `head` appliquée |
| Correction SQL 2.0 | Terminée | Colonne `situation_declaree` présente |
| Initialisation rôles et permissions | Terminée | Scripts de seed exécutés |
| Test FastAPI local | Terminée | `/api/v1/health` retourne `status=ok` |
| Service systemd `sngsc` | Terminée | Service déclaré opérationnel par l’utilisateur |
| Mise à jour applicative du 31/07/2026 | Terminée | Pull Git et redémarrage du service effectués |
| Worker courriels et sauvegardes | Intégré au service | Tâche démarrée par le cycle de vie FastAPI |
| Répertoires d’exécution privés | Terminée | `logs`, `backups` et `uploads` accessibles à `sngsc` |
| Reverse proxy Nginx | Terminée pour le test HTTP | Application accessible sous `/sngsc/` |
| Adresse API du frontend | Corrigée | Même origine que l’interface, sans `localhost` codé en dur |
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
