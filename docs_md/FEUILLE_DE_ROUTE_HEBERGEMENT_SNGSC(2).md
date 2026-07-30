# Feuille de route d’intégration et d’hébergement Linux — SNGSC / HAUQE Certif

**Projet :** SNGSC / HAUQE Certif  
**Serveur MVP :** Contabo — `31.220.87.142`  
**Répertoire applicatif :** `/var/www/api_hauqe`  
**Base PostgreSQL :** `hauqe_certif`  
**Service applicatif prévu :** `sngsc.service`  
**Port interne FastAPI :** `127.0.0.1:8014`  
**Dernière mise à jour :** 29 juillet 2026 à 13:22 UTC  
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
| Reverse proxy Nginx | Terminée pour le test HTTP | Application accessible sous `/sngsc/` |
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
- interdire l’accès public à PostgreSQL ;
- exécuter FastAPI sans privilèges root ;
- limiter les permissions sur `.env` et les fichiers privés ;
- activer le pare-feu uniquement pour SSH, HTTP et HTTPS ;
- protéger les téléversements privés ;
- vérifier les cookies et en-têtes de sécurité ;
- ne pas activer `/docs` publiquement sans décision explicite ;
- conserver les opérations sensibles dans le journal d’audit.

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
