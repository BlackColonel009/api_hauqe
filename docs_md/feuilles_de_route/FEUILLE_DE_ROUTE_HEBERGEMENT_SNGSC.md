# Feuille de route d’intégration et d’hébergement Linux — SNGSC / HAUQE Certif

**Projet :** SNGSC / HAUQE Certif  
**Serveur MVP :** Contabo — `31.220.87.142`  
**Répertoire applicatif :** `/var/www/api_hauqe`  
**Base PostgreSQL :** `hauqe_certif`  
**Service applicatif prévu :** `sngsc.service`  
**Port interne FastAPI :** `127.0.0.1:8014`  
**Dernière mise à jour :** 1er octobre 2026
**Règle de validation :** une étape n’est marquée terminée qu’après contrôle réel sur le serveur.

> **Classement SNCC — badge « En attente INFC » (01/10/2026) :** livrer
> `scoring.css` et `index.html`, puis recharger complètement la page.
> Vérifier qu'un certificat non éligible affiche le badge sans débordement,
> y compris à fort zoom. CSS uniquement ; **base PostgreSQL modifiée : non ;
> migration : aucune ; seed : aucun.**

> **Mes notifications — actions lisibles (01/10/2026) :** livrer ensemble
> `alertes.js`, `alertes.css`, `router.js`, `app-shell.js` et `index.html` ;
> recharger complètement l'onglet après déploiement. Vérifier une notification
> non lue avec les deux actions : les boutons restent dans la même zone,
> lisibles au zoom, et « Marquer lue » répond au premier clic. **Base
> PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

> **Administration — copie des identifiants (01/10/2026) :** livrer la vue
> Utilisateurs, son script/style et les nouvelles versions de cache
> `index.html` → `app-shell.js` → `router.js`. Après rechargement, tester
> les boutons de copie du courriel et du mot de passe dans le modal de
> confirmation, ainsi que celui du mot de passe dans l'assistant de création,
> dès le premier clic, notamment sur accès HTTP local. Le script à vérifier
> est `utilisateurs.js?v=20261001-2` ; forcer un rechargement complet après
> le déploiement pour écarter l'ancien gestionnaire resté en mémoire dans
> l'onglet. **Base PostgreSQL
> modifiée : non ; migration : aucune ; seed : aucun.**

> **Exports du catalogue — filtres et configurations (01/10/2026) :** déployer
> ensemble l'API, `rapports.js`, la vue, le style et leurs versions de cache ;
> redémarrer `sngsc` puis recharger l'interface. Tester sur un compte autorisé
> un filtre période/zone/statut, un filtre référentiel des certifications,
> comparer aperçu et CSV, enregistrer puis recharger une configuration. Les
> réglages sont personnels et écrits dans les tables existantes
> `rapports_generes` et journal d'audit. **Schéma PostgreSQL non modifié ;
> migration Alembic : aucune ; seed : aucun.**

> **Bilans BNEC mensuels, trimestriels et annuels (01/10/2026) :** livrer
> ensemble le backend, les vues, les scripts et styles versionnés. Installer
> la nouvelle dépendance ReportLab avec `pip install -r requirements.txt`,
> puis redémarrer `sngsc` et recharger l'interface. Le processus applicatif
> doit pouvoir écrire dans le répertoire privé `DOCUMENT_STORAGE_DIR`
> (par défaut `uploads/private`) : les fichiers PDF/XLSX/CSV y sont conservés.
> Inclure ce répertoire dans les sauvegardes avec PostgreSQL ; restaurer les
> deux ensemble pour préserver les téléchargements de l'historique. Vérifier
> un aperçu et la génération/téléchargement d'un bilan de chaque périodicité.
> **Base PostgreSQL : schéma non modifié ; aucune migration Alembic ni seed.**
> Lorsqu'un bilan est créé, le système insère des données dans les tables
> existantes `documents`, `rapports_generes` et le journal d'audit.

> **Aperçu des séquences de codification BNEC (29/09/2026) :** déployer le
> backend corrigé et redémarrer `sngsc`. L'aperçu d'une intégration contenant
> plusieurs certifications conserve désormais les numéros déjà proposés dans
> le même modèle/périmètre ; la réservation transactionnelle reste inchangée.
> **Base PostgreSQL modifiée : non par le déploiement ; migration : aucune ;
> seed : aucun.** Les intégrations futures continuent bien sûr à enregistrer
> leurs codes et traces métier normalement.

> **Échéances — boutons de navigation du calendrier (29/09/2026) :** livrer
> `echeances.js`, `echeances.css`, les versions du routeur et d'`index.html`,
> puis redémarrer `sngsc` et forcer le rechargement du navigateur. Les trois
> boutons restent désormais stables entre les rendus asynchrones. **Base
> PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

> **Complément des anciennes collectes à l'intégration BNEC — 29/09/2026 :**
> déployer le nouveau code, redémarrer `sngsc` et recharger l'interface. Le
> plan montre les champs vides qui seront complétés depuis la fiche ;
> l'exécution écrit uniquement ces données, avec audit et rollback commun à
> l'intégration. Les dossiers déjà intégrés ne sont pas retraités.
> **Base PostgreSQL modifiée : oui à l'usage (données métier et audit) ;
> schéma modifié : non ; migration Alembic : aucune ; seed : aucun.** La tête
> Alembic de la livraison précédente reste `j5f9b3d7e1a2`. Ne pas relancer
> le script de reprise des offres pour ce seul changement.

> **Déploiement groupé du 28 septembre 2026 :** suivre en priorité
> [la procédure consolidée](DEPLOIEMENT_CONSOLIDE_2026-09-28.md) pour livrer
> les modifications des deux dernières semaines et demie. Elle recense les
> révisions Alembic jusqu'à `j5f9b3d7e1a2`, les scripts RBAC, la reprise
> facultative des offres et la sauvegarde des fichiers joints. Les notes
> historiques ci-dessous décrivent des livraisons ponctuelles et leurs
> anciennes têtes Alembic ne doivent pas servir de cible ce soir.

> **Courriels du système par agent — 28 septembre 2026 :** base PostgreSQL
> modifiée : **oui après exécution de la migration**
> `j5f9b3d7e1a2_user_system_email_policy.py`. Elle ajoute uniquement
> `preferences_utilisateur.courriels_systeme_actifs BOOLEAN NOT NULL DEFAULT TRUE`.
> Après déploiement, exécuter dans `/var/www/api_hauqe` avec `.venv` activé :
> `python -m alembic upgrade head`, puis `sudo systemctl restart sngsc`.
> Aucun seed. Les courriels fonctionnels annulés par ce réglage ne sont pas
> renvoyés automatiquement lors d'une réactivation. Le worker SMTP intégré au
> service `sngsc` doit être redémarré ; ne pas lancer un second worker.

> **Communication inter-rôles — 27 septembre 2026 :** base PostgreSQL
> modifiée : **oui, données de permissions uniquement** après exécution du
> script ciblé ci-dessous. Schéma modifié : **non**. Migration Alembic :
> **aucune nouvelle**. Aucune colonne supprimée, aucune donnée métier effacée.
> Après déploiement du code, dans `/var/www/api_hauqe` et avec `.venv`
> activé : `python -m app.scripts.sync_workflow_communication_permissions`.
> Ce script ajoute `NOTIFICATIONS.LIRE` aux rôles existants et les droits
> opérationnels Scoring/INFC/SNCC à `CELLULE_VEILLE`, sans retirer de droit.
> Puis `sudo systemctl restart sngsc` : le worker SMTP est déjà intégré au
> service, **ne pas lancer un second worker**. Vérifier `LIEN_VERS_SNGSC` et
> la configuration SMTP du serveur avant une recette réelle. Tester avec des
> comptes de rôles différents ; les courriels antérieurs ne sont pas rejoués.

> **Modals Validation / INFC — 27 septembre 2026 :** modification frontend
> uniquement (`validation-detail.html`, `infc.html`, leurs CSS/JS et versions
> de cache). Base PostgreSQL modifiée : **non**. Migration : **aucune**.
> Seed : **aucun**. Après déploiement des fichiers, forcer un rechargement
> du navigateur pour obtenir les nouvelles versions des scripts et styles.

> **Point de reprise du 11 août 2026 :** les correctifs d'authentification,
> d'affichage du mail HAUQE et de changement de mot de passe ne requièrent
> aucune migration ni seed. Après le pull, redémarrer `sngsc` afin de charger
> le backend, puis forcer le rechargement du navigateur pour les scripts
> frontend. Conserver `alembic upgrade head` dans la procédure standard : la
> tête connue reste `d9f2a7c4e318` au moment du déploiement. Ne jamais se
> fier à l’ancienne valeur `c4d5e6f7a8b9` : les migrations de rappels
> d’échéances doivent être appliquées avant le redémarrage.

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

Le fichier `/var/www/api_hauqe/.env` doit être lisible par le service, sans
être modifiable par ce dernier. Configuration retenue :

```bash
cd /var/www/api_hauqe
sudo chown root:sngsc .env
sudo chmod 640 .env
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
# Coordonnées affichées dans la signature institutionnelle des courriels
HAUQE_CONTACT_SERVICE=Cellule_de_veille_HAUQE
HAUQE_CONTACT_EMAIL=contact@votre-domaine.tg
HAUQE_CONTACT_PHONE=+228_XX_XX_XX_XX
AUTH_SESSION_MINUTES=480
AUTH_IDLE_TIMEOUT_MINUTES=30
AUTH_MAX_FAILED_ATTEMPTS=5
AUTH_FAILURE_WINDOW_MINUTES=15
AUTH_LOCKOUT_MINUTES=15
```

Les noms `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD` et `MAIL_FROM` ne
sont pas ceux lus par la configuration actuelle. En production, utiliser les
variables `HAUQE_SMTP_*` ci-dessus.

Les variables `HAUQE_CONTACT_*` sont facultatives, mais recommandées : elles
alimentent la signature officielle ajoutée à chaque courriel. Renseigner des
coordonnées institutionnelles, jamais les coordonnées privées d'un agent.

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
| 9 | `a6d4e8f1b203` | Politique et journal des rappels d’échéance |
| 10 | `b7e5f9a2c314` | Valeurs techniques du journal des rappels |
| 11 | `c8f6a0b3d425` | Exclusion individuelle d’administrateur des rappels |
| 12 | `d9f2a7c4e318` | Unicité de raison sociale normalisée des entreprises |

Avant d'appliquer `d9f2a7c4e318`, contrôler les doublons historiques. Une
sortie vide permet de poursuivre ; une sortie non vide doit être examinée et
traitée fonctionnellement avant la migration :

```bash
sudo -u postgres psql -d hauqe_certif -c "
SELECT lower(regexp_replace(btrim(raison_sociale), '[[:space:][:punct:]]+', '', 'g')) AS cle,
       count(*) AS total
FROM entreprises
WHERE raison_sociale IS NOT NULL AND btrim(raison_sociale) <> ''
GROUP BY 1
HAVING count(*) > 1
ORDER BY total DESC, cle;"
```

Cette migration n'efface ni ne fusionne aucune entreprise : elle refuse de
s'exécuter tant que des doublons historiques subsistent.

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

Résultat attendu pour le déploiement actuel :

```text
d9f2a7c4e318 (head)
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
| Migrations Alembic | Obligatoires avant le redémarrage | `alembic current` doit afficher `d9f2a7c4e318 (head)` |
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

## 13. Worker de rappels d’échéances (01/09/2026)

Le processus `app.tasks.run_background_services` doit rester actif. Il réalise
désormais, une fois par date calendrier :

1. le scan des échéances et la préparation des rappels ;
2. le traitement de la file SMTP ;
3. le traitement planifié des sauvegardes.

Le même worker traite également le contrôle quotidien d’inactivité des comptes
et le résumé hebdomadaire le lundi. Les échecs SMTP sont relancés au maximum
trois fois, après un délai de 15 minutes entre deux tentatives.

Après déploiement, appliquer les migrations jusqu’à la révision
`d9f2a7c4e318`, puis redémarrer ce worker. Les e-mails restent dépendants des
variables SMTP HAUQE valides ; les erreurs d’authentification Gmail sont
enregistrées dans la file et les journaux sans perdre les données métier.

## 14. Préparation obligatoire avant l’hébergement public (01/09/2026)

### 14.1 Changements récents à prendre en compte

| Élément | Impact serveur | Action obligatoire |
|---|---|---|
| Rappels d’échéance configurables et unicité entreprise | **Migration PostgreSQL requise** | Sauvegarder la base, vérifier l'absence de doublon historique de raison sociale, puis exécuter `alembic upgrade head` jusqu’à `d9f2a7c4e318`. Aucun seed requis. |
| Tâches quotidiennes et résumé hebdomadaire | Le worker intégré doit être relancé | Garder exactement un worker Uvicorn, puis redémarrer `sngsc`. |
| Relances SMTP et identité HAUQE | Dépend du fichier `.env` | Renseigner une adresse Gmail autorisée, son mot de passe d’application et les coordonnées `HAUQE_CONTACT_*`. |
| Sauvegardes applicatives | `pg_dump` et espace disque requis | Installer les outils PostgreSQL client, vérifier `pg_dump` / `pg_restore` et réserver au moins 5 Gio libres. |
| Nouveaux styles frontend | Cache navigateur possible | Redémarrer le service et effectuer un rechargement forcé (`Ctrl + Shift + R`). |
| Précréation entreprise HAUQE | Code applicatif uniquement | Aucun changement PostgreSQL ; redémarrer `sngsc` après le déploiement. Les nouvelles précréations reçoivent `HAUQE-ENT-AAAA-XXXX`, puis BNEC les recodifie après N2. |
| Gestion des campagnes de collecte | Code applicatif uniquement | Aucun changement PostgreSQL ni seed. Redémarrer `sngsc` puis recharger le navigateur (`Ctrl + Shift + R`) pour charger la rubrique, la correction de code et le filtrage des campagnes désactivées. |
| Réinitialisation sécurisée d'un brouillon de collecte | Code applicatif uniquement | Aucun changement PostgreSQL ni seed. Redémarrer `sngsc` après le déploiement ; l'action est disponible seulement dans le formulaire et seulement pour la fiche courante en `BROUILLON`. |
| Écriture de collecte limitée aux agents affectés | Code applicatif uniquement | Aucun changement PostgreSQL ni seed. Déployer puis redémarrer `sngsc`. Avant la saisie, l'administrateur ou le point focal doit créer une affectation active pour chaque agent et chaque mission ; les détenteurs de `COLLECTE.AFFECTER` gardent l'accès d'encadrement. |
| Catalogue de rôles dans Nouvel utilisateur | Code applicatif uniquement | Aucun changement PostgreSQL ni seed. Déployer puis recharger le navigateur avec `Ctrl + Shift + R` : le script et la feuille de style sont versionnés afin de charger la liste complète des rôles actifs. |
| Libellés des certifications déclarées | Code applicatif uniquement | Aucun changement PostgreSQL ni seed. Déployer puis recharger le navigateur avec `Ctrl + Shift + R` ; `collecte-form.js` est versionné pour charger les libellés de certificat corrigés. |
| Autre identifiant juridique d'entreprise | **Migration PostgreSQL requise** | Sauvegarder la base, exécuter `alembic upgrade head` jusqu'à `f7a1e2c3d4b5`, puis redémarrer `sngsc` et recharger le navigateur (`Ctrl + Shift + R`). Aucune donnée existante n'est supprimée et aucun seed n'est requis. |
| Plans d’alerte d’expiration par certification | **Migration PostgreSQL requise** | Sauvegarder la base, exécuter `alembic upgrade head` jusqu’à `b4c8d1e2f3a6`, puis redémarrer `sngsc` et recharger le navigateur (`Ctrl + Shift + R`). La migration ajoute seulement une colonne JSONB nullable ; les certifications historiques conservent la règle générale jusqu’à leur premier paramétrage. Aucun seed requis. |
| Géolocalisation de précréation et carte des sites | Code applicatif uniquement | Aucun changement PostgreSQL ni seed. Déployer, redémarrer `sngsc` et recharger le navigateur (`Ctrl + Shift + R`). En production, publier le site en HTTPS : le navigateur peut refuser la géolocalisation sur HTTP hors `localhost`. |
| Isolation du profil, des préférences et des avatars au changement de compte | Code applicatif uniquement | Aucun changement PostgreSQL ni seed. Redémarrer `sngsc`, puis recharger le navigateur (`Ctrl + Shift + R`) : l'API privée n'est plus lue depuis le cache et les réglages temporaires sont purgés à la déconnexion. |
| Export Excel du dashboard opérationnel | **Nouvelle dépendance Python** | Exécuter `python -m pip install -r requirements.txt` pour installer `openpyxl`, puis redémarrer `sngsc`. L’export devient un fichier `.xlsx` mis en forme. Aucune migration ni seed. |

La migration utilise `gen_random_uuid()` ; l’extension PostgreSQL `pgcrypto`
doit donc rester disponible dans la base. Contrôle serveur :

```bash
sudo -u postgres psql -d hauqe_certif -c "SELECT extname FROM pg_extension WHERE extname = 'pgcrypto';"
```

### 14.2 Précontrôle prêt à exécuter

Le script `scripts/preflight_hebergement_linux.sh` est non destructif. Il
contrôle les commandes PostgreSQL, le `.env` sans afficher les secrets, les
droits d’écriture du compte `sngsc`, l’espace disque, le service et l’état
Alembic. Après le pull et avant le redémarrage final :

```bash
cd /var/www/api_hauqe
chmod +x scripts/preflight_hebergement_linux.sh
sudo ./scripts/preflight_hebergement_linux.sh
```

Une sortie `ECHEC` est bloquante. Le script ne crée, ne supprime et ne modifie
aucune donnée.

### 14.3 Fichiers d’exploitation prêts à copier

- `installation/sngsc.service` : unité systemd à **un seul worker**, avec un
  `PATH` explicite permettant au worker de trouver `pg_dump` ;
- `installation/nginx-hauqe-certif.conf.example` : virtual host Nginx à la
  racine du domaine, avec limitation de taille, en-têtes de base et refus
  d’accès à `uploads`, `backups`, `logs` et à la documentation API.

Copier d’abord ces fichiers vers les emplacements système, adapter uniquement
`DOMAINE_SNGSC`, puis valider avec `nginx -t` et `systemctl daemon-reload`.
Ne pas servir l’application sous `/sngsc/` en production finale : le frontend
utilise l’origine du domaine pour `/api/v1`, `/static` et les vues. Le domaine
final doit donc publier HAUQE Certif à sa racine.

### 14.4 Données privées : blocage de sécurité Git

Les nouvelles archives `backups/*`, les documents `uploads/private/*` et les
avatars sont désormais ignorés pour les futurs fichiers. En revanche, des
archives et documents historiques sont déjà suivis par Git dans le dépôt
actuel. Ils ne doivent pas être envoyés vers un dépôt partagé ou public.

Avant un push vers un dépôt qui n’est pas strictement privé, décider d’une
opération dédiée de retrait de ces fichiers de l’index et, si nécessaire, de
l’historique Git. Cette opération est volontairement séparée du déploiement :
elle ne sera jamais faite automatiquement, car elle peut modifier l’historique
et les copies de sauvegarde.

### 14.5 Séquence de déploiement actualisée

```bash
cd /var/www/api_hauqe
git status --short
git pull --ff-only

source .venv/bin/activate
python -m pip install -r requirements.txt

sudo -u postgres pg_dump -Fc hauqe_certif \
  > "backups/pre-deploiement-$(date +%Y%m%d-%H%M%S).dump"
alembic upgrade head
alembic current

sudo ./scripts/preflight_hebergement_linux.sh
sudo systemctl restart sngsc
sudo systemctl status sngsc --no-pager
curl -fsS http://127.0.0.1:8014/api/v1/health
sudo journalctl -u sngsc -n 100 --no-pager
```

Résultat attendu après migration : `e1b7c4d9a206 (head)`. La migration
`e1b7c4d9a206_collection_case_ownership.py` ajoute les références de dossier
et de responsable aux fiches de collecte, indexe les dossiers par mission et
regroupe les doublons historiques dans leur dossier d'origine. Elle ne supprime
aucune fiche, aucune entreprise et aucune révision. Aucune seed n'est requise.

Aucune migration ne
doit être contournée, aucune seed n’est requise pour les correctifs récents.

### 14.6 Vérificateur — lecture des collectes, sans affectation (27/09/2026)

Après déploiement du code, appliquer la synchronisation RBAC suivante pour
donner au rôle `VERIFICATEUR` la lecture des collectes et retirer une ancienne
attribution éventuelle de `VERIFICATION.AFFECTER` :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
python -m app.scripts.sync_verificateur_collecte_read
sudo systemctl restart sngsc
```

Cette opération ne modifie pas le schéma PostgreSQL et n'exige aucune
migration. Elle ajoute `COLLECTE.LIRE` et, si nécessaire, retire
`VERIFICATION.AFFECTER` du seul rôle `VERIFICATEUR`.

Redéployer le code applicatif, puis redémarrer `sngsc`. L'utilisateur concerné
doit actualiser sa session afin que l'interface recharge ses permissions.

### 14.6.2 Direction technique — consultation de dossier (27/09/2026)

Après déploiement, synchroniser les deux droits de lecture de la Direction
technique :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
python -m app.scripts.sync_direction_consultation_dossiers
sudo systemctl restart sngsc
```

Cette opération ne modifie pas le schéma PostgreSQL : elle ajoute uniquement
`COLLECTE.LIRE` et `VERIFICATION.LIRE` à `DIRECTION_TECHNIQUE` si nécessaire.

### 14.6.1 Calculs automatiques Scoring / INFC / SNCC (25/09/2026)

Déployer le code applicatif puis redémarrer le service :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.17 Cellule de veille — correction du formulaire de relance (25/09/2026)

Cette livraison corrige le `422 Input should be a valid string` lors de
l'enregistrement d'une relance : le navigateur lit les champs texte par leurs
identifiants stables, sans dépendre du cache d’un modèle HTML, et affiche le
libellé du champ réellement rejeté.

**Base PostgreSQL modifiée : non.** Aucune migration et aucun seed ne sont
requis. Déployer le code, redémarrer l'API, puis effectuer un rechargement
forcé du navigateur afin de charger `veille.js` versionné :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.18 Matrice SNCC — correction des bornes au centième (25/09/2026)

Le préremplissage `39,99 → 40`, `59,99 → 60`, `74,99 → 75` et `89,99 → 90`
ne doit plus être rejeté comme une lacune. La correction est uniquement dans
le script navigateur de Règles et codification.

**Base PostgreSQL modifiée : non.** Aucune migration et aucun seed. Déployer
le code, redémarrer le service, puis faire `Ctrl + Shift + R` :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.19 Veille — compatibilité des relances existantes (25/09/2026)

Le schéma API de relance convertit les valeurs texte apportées par un ancien
composant de formulaire (`value`, `label`, `text` ou `name`) avant validation.
Cette protection évite le rejet `422 Input should be a valid string` sans
relâcher les contrôles des champs obligatoires.

**Base PostgreSQL modifiée : non.** Aucune migration et aucun seed. Redémarrer
le service après déploiement :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.20 SNCC — reprise du brouillon existant (25/09/2026)

L’écran SNCC recharge désormais automatiquement le brouillon `v1.0` déjà
présent, afin de l’enregistrer ou de le publier au lieu de tenter une seconde
création de la même version.

**Base PostgreSQL modifiée : non.** Aucune migration et aucun seed. Déployer
le code, redémarrer le service, puis faire `Ctrl + Shift + R` :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.21 Veille — journalisation sûre de validation (25/09/2026)

En cas de rejet d’une relance, le journal affiche le champ et le motif sans
écrire le contenu du message ni l’adresse du destinataire. Cette trace permet
de diagnostiquer un formulaire navigateur ou un cache incohérent sans exposer
de données métier.

**Base PostgreSQL modifiée : non.** Aucune migration et aucun seed. Déployer
le code puis redémarrer l’API :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.22 Veille — correctif de soumission de relance (25/09/2026)

Le script global de contexte partagé ne doit plus intercepter la soumission
des relances Veille. Cela corrige l’envoi d’un destinataire vide alors que le
champ était renseigné à l’écran. La page Veille est désormais l’unique
propriétaire de la requête API.

**Base PostgreSQL modifiée : non.** Aucune migration et aucun seed. Déployer
le code, puis faire `Ctrl + Shift + R` afin de recharger le script global :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

Aucune migration et aucun seed ne sont nécessaires. Après déploiement,
l'administrateur doit publier une règle métier `SNCC_CLASSIFICATION_MATRIX`
avant de pouvoir enregistrer des classements SNCC automatiques. Le système ne
crée aucun classement si cette matrice de risques n'est pas publiée.

### 14.7 Arborescence collecte entreprise par mission (24/09/2026)

Déployer le code puis redémarrer le service afin d'appliquer le correctif de
présentation et de réinitialisation des fiches de collecte :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

Ensuite effectuer un rechargement forcé du navigateur (`Ctrl + Shift + R`) :
les scripts et la feuille de style Collectes sont versionnés. Aucune migration
PostgreSQL, aucun seed et aucune modification de données ne sont requis.

### 14.8 Échéances — correction de rendu du statut (24/09/2026)

Déployer le code puis redémarrer le service :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

Ensuite effectuer un rechargement forcé (`Ctrl + Shift + R`) afin de charger
les scripts et feuilles de style Échéances / Alertes versionnés. Cette correction est uniquement front-end :
aucune migration PostgreSQL, aucun seed, aucune suppression ni modification de
données ne sont requis.

### 14.10 Direction Technique, stabilité des actions et suivi du dossier (24/09/2026)

Cette livraison limite le rechargement automatique aux tableaux de bord afin
de stabiliser tous les boutons et formulaires opérationnels. Elle ajoute aussi
le thème nuit du Suivi du dossier et la consultation des vérifications pour
la Direction Technique.

```bash
cd /var/www/api_hauqe
git pull --ff-only
source .venv/bin/activate
python -m app.scripts.seed_verification_fuccs_permissions
sudo systemctl restart sngsc
```

Faire ensuite un rechargement forcé (`Ctrl + Shift + R`), puis demander au
directeur de se déconnecter/reconnecter afin de régénérer son jeton de
permissions. Aucune migration Alembic n'est requise ; le seed ne modifie que
les liaisons rôle-permission.

### 14.9 Actions structurées, intégration sombre et règles (24/09/2026)

Cette livraison ajoute des routes de suppression protégées pour les offres et
certifications déclarées d'une fiche de collecte au statut brouillon. Aucun
changement de schéma ni donnée de référence n'est nécessaire.

```bash
cd /var/www/api_hauqe
git status --short
git pull --ff-only
source .venv/bin/activate
sudo systemctl restart sngsc
sudo systemctl status sngsc --no-pager
curl -fsS http://127.0.0.1:8014/api/v1/health
```

Faire ensuite un rechargement forcé (`Ctrl + Shift + R`) : les scripts
Entreprise, Fiche de collecte, Règles et codification, ainsi que les styles
Collectes et Intégration sont versionnés. **Ne pas lancer `alembic upgrade
head` pour cette livraison : aucune migration n'est requise.**

### 14.11 Journal d'audit et ouvertures de collecte (24/09/2026)

Cette livraison ajoute la recherche serveur du journal d'audit et corrige
l'affichage/sauvegarde des offres et certifications d'une fiche de collecte.
Elle améliore aussi le bouton **Ouvrir la collecte** dans une mission.

```bash
cd /var/www/api_hauqe
git pull --ff-only
source .venv/bin/activate
sudo systemctl restart sngsc
sudo systemctl status sngsc --no-pager
curl -fsS http://127.0.0.1:8014/api/v1/health
```

Effectuer ensuite `Ctrl + Shift + R` dans le navigateur. **Ne pas lancer
`alembic upgrade head` et ne lancer aucun seed : aucune migration, donnée ou
permission PostgreSQL n'est modifiée par cette livraison.**

### 14.12 Synchronisation des offres collectées (24/09/2026)

Les nouvelles fiches soumises alimentent automatiquement les offres de leur
entreprise. Aucun changement de schéma n'est requis.

```bash
cd /var/www/api_hauqe
git pull --ff-only
source .venv/bin/activate
sudo systemctl restart sngsc
```

Pour reprendre les données existantes d'une entreprise précise, exécuter une
seule fois après le déploiement :

```bash
python -m app.scripts.synchronize_collection_offers_to_enterprise \
  --enterprise-name "AgroNoura SARL" --apply
```

La commande modifie uniquement `offres_entreprise` et ajoute les traces dans
`evenements_audit`. **Ne pas lancer Alembic : aucune migration ni seed n'est
requis.**

### 14.13 Doublons d'offres et reprise globale (24/09/2026)

Cette livraison rend impossible l'enregistrement de deux offres actives ayant
le même type, nom et catégorie dans une même fiche. Elle assainit les anciens
doublons sans suppression physique.

```bash
cd /var/www/api_hauqe
git pull --ff-only
source .venv/bin/activate
python -m alembic upgrade head
python -m app.scripts.synchronize_collection_offers_to_enterprise --all --apply
sudo systemctl restart sngsc
```

Faire ensuite un rechargement forcé (`Ctrl + Shift + R`). Cette livraison
applique la migration
`h3d9e4f1a607_declared_offer_duplicate_protection.py`, aucune seed n'est
requise.

### 14.14 Déploiement consolidé des corrections du 24–25/09/2026

Cette livraison regroupe les corrections de collecte, de rattachement des
organismes certificateurs, de recherche du journal d'audit, de suivi de
dossier, de droits du vérificateur, de rendu Échéances / Alertes et de
réactivité des boutons dans Règles et codification.

La base PostgreSQL doit atteindre la révision Alembic
`h3d9e4f1a607`. Les migrations ajoutent le rattachement explicite des
certifications déclarées à leur organisme et protègent les offres déclarées
contre les doublons actifs. Les doublons historiques d'offres sont conservés
avec le statut `DOUBLON_ANNULE` ; aucune ligne métier n'est supprimée.

Après la sauvegarde PostgreSQL, exécuter :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m app.scripts.seed_role_permission_matrix
python -m app.scripts.seed_verification_fuccs_permissions
python -m app.scripts.synchronize_collection_offers_to_enterprise --all --apply
sudo systemctl restart sngsc
```

Les deux seeds ne touchent pas au schéma : ils synchronisent les permissions
de la Direction Technique et du Vérificateur. Le script de synchronisation
ajoute les offres collectées absentes aux fiches entreprise et laisse une trace
d'audit. Il peut être relancé sans créer de doublon. Aucun autre seed n'est
requis. Faire ensuite un rechargement forcé du navigateur (`Ctrl + Shift + R`)
et demander aux utilisateurs dont les permissions ont changé de se déconnecter
puis se reconnecter.

### 14.15 Rapprochement global des organismes certificateurs historiques (25/09/2026)

Cette livraison corrige le blocage BNEC « organisme certificateur non
rapproché dans le registre » pour les fiches de collecte déjà enregistrées et
évite sa réapparition pour les nouvelles collectes et leurs révisions.

**Base PostgreSQL modifiée : oui.** La migration de données
`i4e8a2c6d0b4_backfill_declared_certification_organisms.py` ne supprime aucune
colonne ni certification. Elle :

- relie chaque certification déclarée historique à l'organisme déjà présent
  lorsque le nom ou le sigle correspond exactement ;
- précrée seulement les organismes absents à partir du libellé déjà déclaré ;
- leur affecte le statut `A_VERIFIER` : l'administrateur HAUQE doit compléter
  ou confirmer les informations de registre avant leur validation métier.

Aucun seed n'est requis. Après sauvegarde PostgreSQL :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
python -m alembic upgrade head
sudo systemctl restart sngsc
```

Contrôle après déploiement (doit retourner `0`) :

```sql
SELECT count(*) AS certifications_sans_organisme
FROM certifications_declarees
WHERE organisme_id IS NULL
  AND nullif(btrim(organisme_declare), '') IS NOT NULL;
```

### 14.16 Matrice SNCC administrable (25/09/2026)

La page **Règles et codification** contient désormais l’onglet **Classement
SNCC** : tableau de seuils, préremplissage modifiable, brouillon et publication
avec référence d’approbation. Le calcul SNCC recherche correctement la règle
versionnée publiée par son code logique.

**Base PostgreSQL modifiée : non.** Aucune migration et aucun seed ne sont
requis. Déployer le code, redémarrer l’API, puis effectuer un rechargement
forcé du navigateur :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.17 SNCC — statuts prioritaires et explication des dossiers (26/09/2026)

Cette livraison applique la priorité de la situation réelle du certificat sur
le statut administratif calculé : expiration `EX`, retrait `RT`, suspension
`SU`, authenticité à vérifier `VE`. La matrice SNCC conserve la classe, le
risque et le statut normal `VA` ou `RE`. Elle ajoute également l'analyse en
lecture seule des manquements dans la fiche certification et corrige les
compteurs d'expiration du tableau de bord : une certification datée est
comptée même lorsqu'elle est encore `A_VERIFIER`.

**Base PostgreSQL modifiée : non.** Aucune migration et aucun seed ne sont
requis. Déployer le code, redémarrer le service puis recharger le navigateur :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.23 Lien SNGSC dans les alertes et échéances internes (26/09/2026)

Cette livraison ajoute un lien vers l'application uniquement aux e-mails
d'alertes et d'échéances destinés à un utilisateur HAUQE. Les destinataires
externes (organismes, relances, confirmations) ne reçoivent pas ce lien.

**Base PostgreSQL modifiée : non.** Aucune migration et aucun seed ne sont
requis. Sur le serveur, ajouter ou corriger la variable dans `/var/www/api_hauqe/.env`
puis redémarrer le service :

```bash
LIEN_VERS_SNGSC=http://31.220.87.142/sngsc
sudo systemctl restart sngsc
```

Si le site est accessible en HTTPS, remplacer impérativement `http://` par
`https://`. Ne pas ajouter d'espace autour du signe `=`.

### 14.24 Réouverture contrôlée des dossiers de vérification (27/09/2026)

Cette livraison est uniquement applicative : elle ajoute l’analyse de
réouverture, la protection des jalons FUCCS/N1/N2/BNEC et le modal de guidage
vers une révision de collecte. Aucune table, colonne, donnée ou variable `.env`
ne change.

**Base PostgreSQL modifiée : non.** Aucune migration et aucun seed ne sont
requis. Déployer le code, redémarrer le service, puis effectuer un
rechargement forcé du navigateur afin de recevoir le nouveau JavaScript et le
nouveau style :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.25 Parcours de traitement dynamique (27/09/2026)

Le rafraîchissement immédiat du bloc **Suivi du dossier** est une mise à jour
front-end uniquement. Il n’y a ni migration, ni seed, ni modification `.env`.
Après déploiement, redémarrer le service qui sert l’application puis effectuer
un rechargement forcé du navigateur afin de charger les modules JavaScript
versionnés.

**Base PostgreSQL modifiée : non.**

### Livraison du rapprochement des preuves et des cinq corrections du 27/09/2026

**Complément de livraison — preuves/révisions/entreprises (27/09/2026) :** publier les nouveaux code API et script `entreprise-detail.js`, puis redémarrer le service et recharger le navigateur. Aucun `alembic upgrade` ni seed nouveau n’est requis. La table `documents` existante reçoit de nouvelles références seulement lorsqu’un utilisateur crée une nouvelle révision. Les justificatifs historiques sont visibles depuis l’entreprise si la fiche possède un `entreprise_id` explicite ; la base locale comporte une fiche historique sans entreprise liée, non attribuée automatiquement pour éviter une erreur métier. **Base PostgreSQL modifiée par le déploiement : non ; migration : aucune.**

Les modifications concernent le code API, le tableau de bord, les fiches certification/organisme et une feuille de style nouvelle `app/static/css/organisme-verification.css`. Les preuves de certifications sont visibles depuis l’organisme par une vue liée ; aucun fichier n’est copié pendant le déploiement. Les anciens documents uniquement attachés à une fiche de collecte ne sont pas réaffectés automatiquement à un certificat, pour éviter un rapprochement erroné.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun ; variable `.env` nouvelle : aucune.** Déployer le code, redémarrer `sngsc` et recharger le navigateur afin de récupérer les ressources front-end versionnées. La création volontaire de nouvelles preuves par les utilisateurs reste une écriture applicative normale dans la table existante `documents`.

### 14.38 Affichage collecte et actions SNCC (27/09/2026)

Correction de la grille des certifications déclarées : la recherche
d’organisme et les preuves occupent toute la largeur. Le classement SNCC
affiche le résultat du préremplissage et garde la publication visible avec
son état d’activation. Aucun schéma ou contenu PostgreSQL ne change.

Après déploiement du code, redémarrer l’API et forcer le rechargement du
navigateur pour charger `collecte-form.js?v=20260927-6`,
`collecte-form.css?v=20260927-7`, `regles-codification.js?v=20260927-5`
et `regles-codification.css?v=20260927-4`.

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

**Base PostgreSQL modifiée : non. Migration : aucune. Seed : aucun.**

### 14.37 Collecte — preuves par certification et recherche d’organisme (27/09/2026)

Cette livraison modifie l’interface de collecte et le service d’intégration
BNEC. Déployer le code puis redémarrer l’API ; aucune migration, seed ou
variable `.env` n’est nécessaire. Effectuer un rechargement forcé pour charger
`collecte-form.js?v=20260927-5` et `collecte-form.css?v=20260927-6`.

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

**Base PostgreSQL modifiée : non.**

### 14.36 Lien « Mot de passe oublié » — expiration de trois minutes (27/09/2026)

La durée de validité est désormais réglable avec
`PASSWORD_RESET_EXPIRE_MINUTES`. La valeur recommandée et livrée est `3`.
Elle est utilisée à la fois pour le jeton stocké et le texte du courriel.

Ajouter ou vérifier la ligne suivante dans `/var/www/api_hauqe/.env`, sans
modifier les autres secrets :

```env
PASSWORD_RESET_EXPIRE_MINUTES=3
```

**Base PostgreSQL modifiée : non.** Aucune migration Alembic et aucun seed ne
sont requis. Après modification du fichier `.env`, redémarrer le service :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.30 Codes automatiques de collecte (27/09/2026)

Les campagnes, missions et zones reçoivent désormais une proposition de code
automatique fondée sur les données de production :
`HAUQE-CAMP-AAAA-NNNN`, `HAUQE-MIS-AAAA-NNNN` et
`HAUQE-ZON-AAAA-NNNN`. Il s'agit d'une évolution applicative ; aucun schéma
et aucune donnée existante ne sont modifiés.

**Base PostgreSQL modifiée : non.** Aucune migration Alembic et aucun seed ne
sont requis. Après déploiement, redémarrer le service et effectuer un
rechargement forcé du navigateur afin de recevoir les scripts versionnés :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.28 Assistant de création des campagnes (27/09/2026)

La création et la modification d’une campagne s’effectuent désormais dans un
assistant en trois étapes. Cette livraison est exclusivement front-end : aucun
schéma, donnée, rôle ou variable d’environnement ne change.

**Base PostgreSQL modifiée : non.** Aucune migration et aucun seed ne sont
requis. Déployer le code, redémarrer le service, puis recharger le navigateur
en forçant l’actualisation afin de recevoir `campagnes-collecte.js` et
`collectes.css` versionnés :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.29 Modals de précréation de collecte (27/09/2026)

La présentation des modals de précréation d’entreprise, de zone
administrative et d’organisme certificateur est harmonisée. Cette livraison
est uniquement front-end ; les endpoints et la base restent inchangés.

**Base PostgreSQL modifiée : non.** Aucune migration et aucun seed ne sont
requis. Après déploiement, redémarrer le service et recharger le navigateur en
forçant l’actualisation afin de charger `collecte-form.css` versionné :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.31 Défilement du modal « Créer une mission » (27/09/2026)

La correction est exclusivement front-end : le contenu du modal de création
et d'affectation des agents défile correctement au zoom, sans masquer son
pied de formulaire. Aucun endpoint ni modèle de données ne change.

**Base PostgreSQL modifiée : non.** Aucune migration Alembic et aucun seed ne
sont requis. Redémarrer le service et forcer le rechargement du navigateur
pour recevoir `collectes.css` versionné :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.32 Boutons réactifs — Règles et codification (27/09/2026)

Cette correction concerne uniquement `regles-codification.js`. Elle retire le
clonage des boutons et l'observateur global qui pouvaient produire une
latence apparente, puis fixe un écouteur direct unique sur chaque action
affichée. Les actions de grilles FUCCS recréées après rendu restent couvertes.

**Base PostgreSQL modifiée : non.** Aucune migration Alembic et aucun seed ne
sont requis. Déployer le code, redémarrer le service puis forcer le
rechargement du navigateur afin de charger
`regles-codification.js?v=20260927-3` :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.33 SNCC — confirmation du contrôle et du brouillon (27/09/2026)

La page **Classement SNCC** affiche à présent, directement sous ses boutons,
le résultat de la vérification des plages et une fiche du brouillon enregistré
(version, libellé, statut et cinq plages). Cette évolution est strictement
front-end : elle ne crée aucune donnée seule ; la création reste déclenchée
uniquement par l’utilisateur via **Créer le brouillon SNCC**.

**Base PostgreSQL modifiée : non.** Aucune migration Alembic et aucun seed ne
sont requis. Déployer le code, redémarrer le service puis faire un
rechargement forcé afin de charger :
`regles-codification.js?v=20260927-4` et
`regles-codification.css?v=20260927-3`.

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.34 Erreurs de saisie conservées dans les modals (27/09/2026)

Le gestionnaire central de modals affiche maintenant les erreurs de validation
et les erreurs API dans la fenêtre où la saisie a été faite. Les valeurs déjà
saisies ne sont pas effacées et l’utilisateur est guidé vers le premier champ
à corriger. Cette livraison couvre les modals de tous les modules métier ; elle
ne modifie aucune route ni aucun schéma PostgreSQL.

**Base PostgreSQL modifiée : non.** Aucune migration Alembic et aucun seed ne
sont requis. Déployer le code, redémarrer le service et effectuer un
rechargement forcé du navigateur pour charger les fichiers versionnés :
`app-shell.js?v=20260927-2`, `dialog-manager.js?v=20260927-1` et
`dialog-system.css?v=20260927-4`.

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.35 Réinitialisation de mot de passe — correctif client (27/09/2026)

Le script de l’écran public **Mot de passe oublié** charge maintenant son
client API avant la soumission du nouveau mot de passe. Cela supprime l’erreur
`api is not defined`. Aucun endpoint, secret, règle de sécurité ou donnée ne
change.

**Base PostgreSQL modifiée : non.** Aucune migration Alembic et aucun seed ne
sont requis. Déployer le code, redémarrer le service et forcer le
rechargement du navigateur pour charger
`mot-de-passe-oublie.js?v=20260927-1` :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

### 14.27 Précréation terrain des organismes certificateurs (27/09/2026)

Cette livraison permet à un agent affecté à une mission de précréer un
organisme certificateur et son accréditation depuis la ligne de certification
déclarée. Les deux éléments restent `A_VERIFIER` jusqu’au contrôle HAUQE. La
création est protégée contre les doublons et la fiche conserve désormais le
lien explicite vers l’organisme.

**Base PostgreSQL modifiée : oui, données RBAC uniquement.** Aucune migration
Alembic et aucun seed ne sont requis. Après déploiement du code, accorder la
permission nouvelle aux agents existants, puis redémarrer le service :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
python -m app.scripts.sync_agent_collecte_organismes_create
sudo systemctl restart sngsc
```

Effectuer ensuite un rechargement forcé du navigateur pour charger le nouveau
JavaScript et la feuille de style versionnée.

### 14.26 Assistant « Nouvel utilisateur » compatible avec le zoom (27/09/2026)

Cette correction concerne uniquement l'interface d'administration : le modal
de création devient un assistant en trois étapes et son style reste lisible au
zoom. Aucune table, migration, seed ou variable `.env` ne change. Après déploiement,
redémarrer le service puis faire un rechargement forcé du navigateur afin de
charger la feuille de style versionnée :

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
sudo systemctl restart sngsc
```

**Base PostgreSQL modifiée : non.**

### Collecte et codification BNEC — livraison du 27/09/2026

Déployer le backend et les fichiers statiques ensemble, puis redémarrer
`sngsc` et recharger l'interface. Aucune migration Alembic ni seed n'est
nécessaire. Les nouveaux dépôts de preuves positionnent « Copie disponible »
à oui ; les nouvelles précréations renseignent `date_creation`. Les modèles
de codification existants ne sont pas republiés : `{REGION}` lit le nom de la
région administrative, jamais son code ; `{SECTEUR}` concatène les catégories
des offres de l'entreprise. Vérifier les noms des régions avant une nouvelle
intégration utilisant `{REGION}`. Aucun code national déjà attribué n'est
modifié rétroactivement.

**Base PostgreSQL modifiée : non (schéma) ; écriture de données métier : oui
sur les nouveaux dossiers.**

### Modals de précréation de collecte — zoom (27/09/2026)

La feuille de style `collecte-form.css` doit être déployée avec la version
du cache `20260927-13` dans `index.html`. Les modals zone, entreprise et
organisme ont été contrôlés au zoom normal et élevé. Après déploiement,
redémarrer le service puis recharger l'interface pour obtenir la nouvelle CSS.
**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Documents de collecte visibles dans Vérifications et FUCCS (27/09/2026)

Déployer ensemble `document_repository.py`, `document_service.py`, la route
`documents.py`, le compteur de vérification et les scripts des pages
Vérifications, Contrôle FUCCS et Entreprise. Redémarrer `sngsc`, puis recharger
l'interface pour prendre les nouveaux fichiers JavaScript versionnés. Les
preuves existantes deviennent visibles grâce à la vue liée ; aucun déplacement
de fichier, script de rattrapage, migration Alembic ou seed n'est requis.
**Base PostgreSQL modifiée : non.**
### Déploiement de la clôture coordonnée de veille (01/10/2026)

**Base PostgreSQL modifiée : oui.** Appliquer la migration Alembic
`k6a0c4e8f2b3_watch_followup_notification_link.py` avant de redémarrer
l'application et le worker SMTP. Elle ajoute la colonne nullable
`notifications.relance_veille_id`, une clé étrangère et un index ; elle
rapproche de façon conservatrice les anciens courriels de relance lorsque
le lien est unique. Aucun seed. Aucun courriel ni document n'est supprimé.
La migration a été appliquée et vérifiée sur la base locale le 01/10/2026 ;
elle reste à appliquer séparément sur le serveur Linux.

```bash
cd /var/www/api_hauqe
source .venv/bin/activate
python -m alembic upgrade head
python -m alembic current
sudo systemctl restart sngsc
```

Le worker est intégré au lifespan FastAPI de `sngsc.service` dans la
configuration documentée ; ne pas lancer de second processus SMTP en parallèle.
Déployer backend, templates, JS et CSS ensemble,
puis recharger le navigateur. Vérifier une ouverture, une clôture avec
relance programmée, la déduplication des destinataires et le réglage de
courriel par le point focal. Les anciens courriels sans rapprochement certain
restent inchangés : les vérifier manuellement avant de clôturer un ancien
dossier contenant une relance programmée.
### Modals et logo HAUQE officiel (01/10/2026)

Déployer impérativement le nouveau fichier `app/static/logo.jpg` avec les
templates, feuilles CSS, scripts JS, le service de rapports BNEC et le worker
SMTP. Redémarrer `sngsc.service` (le worker de fond est intégré), puis faire
un rechargement complet du navigateur. Contrôler le logo dans la connexion,
les PDF/Excel et un courriel HTML réel ; vérifier les modals Alertes et
Échéances avec un zoom élevé et les trois étapes de planification.
**Base PostgreSQL modifiée : non pour cette livraison ; migration : aucune ;
seed : aucun.** La migration de veille `k6a0c4e8f2b3` mentionnée ci-dessus
reste néanmoins requise sur le serveur si elle n'y a pas encore été appliquée.
