# Livraison Docker Linux — SNGSC / HAUQE Certif

## État confirmé le 13 novembre 2026 — prioritaire sur les anciens exemples

Contabo : Docker 29.1.3, Compose 2.40.3, PostgreSQL 16.15 et révision
`k6a0c4e8f2b3`. Clone propre mais toujours sur 6f48462 sans fichiers Docker.
Le lot Docker est encore local sur Windows : aucun pull seul ne le publiera.
La cible Linux et le client de sauvegarde de son image sont désormais en version
majeure 16. Le build Windows de test conserve le défaut 17 ; ne pas mélanger
son dump 17 avec la cible Linux 16. Paquets clients via le dépôt officiel PGDG.
Toute cible/image Linux déjà initialisée en 17 doit être conservée et examinée,
pas réutilisée telle quelle en 16 et surtout pas supprimée sans accord.
Avant nouveau code métier sur Contabo : sauvegarde puis migration
`l7b1d5f9a304` (ajout nullable `contacts_entreprise.genre` et contrainte de valeurs,
sans suppression ni seed). Ne pas exécuter cette migration avant livraison du
code correspondant et validation du plan de déploiement.

Exigence utilisateur : livraison finale obligatoirement Dockerisée. Le paquet
doit réunir image applicative Linux validée, Compose/deploy, dump réel Contabo,
documents/avatars, modèles privés et guide. Une archive de code seule ne suffit
pas. L'export Contabo peut être effectué sans dockeriser la production source.
Le code de l'image et le schéma du dump doivent être compatibles : identifier
la version livrée et examiner les migrations avant de construire le paquet final.

### Ordre confirmé : publier les mises à jour métier, puis Dockeriser

L'utilisateur demande de livrer les vraies mises à jour applicatives, pas
seulement l'ancien code Contabo. Préparer un lot Git cohérent comprenant code,
assets, migrations, scripts nécessaires et fichiers Docker ; exclure les
documents de travail, données privées, dumps, secrets et dépendances locales.
Ne pas ignorer les Dockerfile/Compose pour protéger la production : leur présence
ne les exécute pas. Garder le .env et le service Contabo actuels, appliquer la
procédure normale de mise à jour (sauvegarde, dépendances, migrations exactes et
scripts requis, redémarrage et recette). Ensuite construire/tester l'image Linux
sur la même version approuvée dans le clone isolé et exporter la base mise à
jour avec ses fichiers. Ne pas mêler image nouvelle et dump ancien sans contrôle.
Le déploiement métier en production reste une étape explicitement contrôlée ;
aucun pull ni migration exécutés par l'assistant.

Préparé le 2 novembre 2026. État : Windows validé par l'utilisateur ; Linux
préparé mais pas encore testé sur Contabo/HAUQE. Ne pas annoncer une livraison
validée avant le test de restauration, fichiers, MFA et sauvegarde.

## 1. Ce que reçoit HAUQE

- Code/version Git approuvée ou image `sngsc-hauqe:linux` exportée en tar.
- `compose.linux.yaml`, `deploy/init-db.sh`, modèles de configuration et ce guide.
- `database.dump` provenant de Contabo, `files.tar.gz`, manifeste SHA-256,
  version PostgreSQL, révision Alembic et compteurs de contrôle.
- Par canal sécurisé séparé : clés source SECRET_KEY et MFA_FERNET_KEY,
  réglages SMTP et autres secrets nécessaires. Pas de .env source dans Git.

Le dump contient les comptes et permissions applicatifs, pas les comptes SQL
globaux ni les fichiers sur disque. Le nouveau PostgreSQL initialise un rôle
SQL `hauqe_app` sans superutilisateur ; les objets restaurés lui appartiendront.

## 2. Précontrôles Contabo — ne pas toucher à la production

L'installation actuelle est `/var/www/api_hauqe`, service connu `sngsc`.
Le clone isolé existe dans `/var/www/api_hauqe_docker` mais pointait encore sur
6f48462 sans Dockerfile lors du dernier contrôle. requirements source contient
un ajout local reportlab à conserver. Aucun reset, suppression ou pull dans le
dossier source pour ce transfert.

Exécuter sur Contabo :

```bash
cat /etc/os-release
docker --version
docker compose version
sudo -u postgres psql -Atc 'SELECT version();'
cd /var/www/api_hauqe
git status --short
git log -1 --oneline
sudo -u postgres psql -d hauqe_certif -Atc 'SELECT version_num FROM alembic_version;'
```

Confirmer le vrai nom de base depuis la configuration source privée. Ne pas
publier la valeur de DATABASE_URL. Le modèle cible PostgreSQL 16 ; si la source
est plus récente que 16, ne pas restaurer vers 16. Adapter les images/clients et
refaire les tests. Si Docker absent, installer Docker Engine et le plugin Compose
selon la distribution, sans appliquer au hasard des commandes d'une autre version.

Vérifier aussi les chemins, sans communiquer le contenu des documents :

```sql
SELECT id, chemin_stockage FROM documents WHERE chemin_stockage IS NOT NULL LIMIT 10;
```

L'image possède un alias `/var/www/api_hauqe` vers `/srv/sngsc` : les anciens
chemins Linux sous `/var/www/api_hauqe/uploads` et les avatars associés restent
résolubles après copie. Cela ne couvre pas d'autres dossiers personnalisés ni
les chemins Windows. Tout fichier ailleurs doit être inventorié avant export.
Tester le téléchargement après import, pas seulement les compteurs.

## 3. Publier le code sans données privées

Le poste Windows contient de nombreuses modifications métier non publiées.
Ne pas utiliser `git add .` : vérifier le lot, les fichiers ignorés, les migrations
et les scripts associés. Ne pas expédier une migration sans les modèles/services
correspondants. Publication/commit/push à faire seulement sur accord explicite.

Après publication approuvée, sur le clone isolé uniquement :

```bash
cd /var/www/api_hauqe_docker
git status --short
git pull --ff-only
ls -l Dockerfile compose.linux.yaml deploy/init-db.sh deploy/export-contabo.sh
```

Si le clone a des changements, s'arrêter. Ne pas écraser son contenu.
Les anciennes modifications de production ne sont pas embarquées par ce pull.

## 4. Exporter les données source

Depuis le clone contenant les fichiers récents :

```bash
sudo sh deploy/export-contabo.sh hauqe_certif
```

Le script lit PostgreSQL via l'utilisateur système postgres et archive les
uploads et avatars source. Il crée un dossier privé unique sous
`/var/backups/sngsc-transfer/export-XXXXXXXX`. Aucun arrêt/service/migration ni
modification de la base source. Les clés et le .env ne sont pas inclus.
En cas d'échec, ne pas utiliser l'export incomplet. Ne pas supprimer les anciens
exports automatiquement. Vérifier la version, le catalogue et les avertissements.

Le premier export sert à la répétition. La copie base + fichiers d'un système
actif n'est pas une photographie synchronisée. Pour l'export final, prévoir la
fenêtre d'arrêt des saisies, de l'API source et de tous les workers/tâches
concernés après validation des noms de services. Puis refaire un export complet.
Les compteurs d'un export à chaud peuvent différer si des saisies ont continué.

Transférer le dossier via SFTP/SCP ou un canal chiffré, pas par un dépôt public.
Ces archives contiennent des données personnelles. Après réception :

```bash
cd /chemin/vers/export-recu
sha256sum -c SHA256SUMS
```

## 5. Préparer le nouveau déploiement (clone isolé ou serveur HAUQE)

Travailler dans le dossier de code Docker, jamais le dossier de production.
Préparer deux fichiers privés sans écraser ceux qui existent :

```bash
test -e .env.compose.linux || cp .env.compose.linux.example .env.compose.linux
test -e .env.app.linux || cp .env.app.linux.example .env.app.linux
chmod 600 .env.compose.linux .env.app.linux
```

Renseigner avec un éditeur :

- compose : nom du projet, port HTTP libre (8002 par défaut), deux mots de passe
  SQL distincts admin/app. Éviter `$` ou utiliser les guillemets simples dotenv
  pour empêcher une interpolation involontaire ; ne jamais publier les valeurs.
- app : DATABASE_URL vers `db:5432/hauqe_certif`, rôle hauqe_app, même mot de passe
  applicatif mais encodé pour une URL ; clés SECRET_KEY et MFA_FERNET_KEY source.
- SMTP et URL publique adaptés au futur serveur. Garder HAUQE_ENABLE_SMTP=false
  dans compose pour tous les essais, même si les identifiants SMTP sont présents.
- BACKGROUND_SERVICES_ENABLED=false : le worker intégré est toujours désactivé.
  Le worker séparé est optionnel et ne doit pas démarrer pendant les répétitions.

Les variables DB sont lues uniquement à l'initialisation d'un volume vide :
modifier le fichier plus tard ne change pas le mot de passe SQL existant.
Garder les fichiers secrets sauvegardés séparément avec contrôle d'accès.

Définir une fonction courte pour les commandes suivantes (même terminal Bash) :

```bash
dc() { docker compose --env-file .env.compose.linux -f compose.linux.yaml "$@"; }
dc config --quiet
dc build web
dc up -d db
dc ps
```

Attendre db healthy. PostgreSQL n'expose aucun port hôte : aucun conflit avec le
5432 de Contabo. Le projet/les volumes sont indépendants du test Windows.
L'API n'est pas encore démarrée et aucune migration n'est automatique.

## 6. Restaurer uniquement dans la nouvelle base vide

Placer l'export reçu dans `livraison_privee/` (ignoré Git), puis vérifier SHA256SUMS.
Ne pas laisser ces données accessibles par Nginx. Contrôler la cible :

```bash
dc exec -T db psql -U postgres -d hauqe_certif -Atc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';"
```

Continuer seulement si 0. Sinon s'arrêter ; aucun `DROP`, `--clean`, ou
`docker compose down -v` ne fait partie de cette procédure.

```bash
dc exec -T db pg_restore -U hauqe_app -d hauqe_certif --no-owner --no-privileges --single-transaction --exit-on-error < livraison_privee/database.dump
```

Le code de sortie doit être 0. En cas d'erreur SQL : annulation de la transaction,
examiner le message, ne pas ignorer l'erreur. Si des extensions nécessitant les
droits admin sont requises, les faire examiner/précréer par l'administrateur,
ne pas rendre le rôle applicatif superutilisateur.

```bash
dc exec -T db psql -U hauqe_app -d hauqe_certif -c 'SELECT version_num FROM alembic_version;'
dc exec -T db psql -U hauqe_app -d hauqe_certif -c "SELECT 'utilisateurs',count(*) FROM utilisateurs UNION ALL SELECT 'entreprises',count(*) FROM entreprises UNION ALL SELECT 'certifications',count(*) FROM certifications;"
dc run --rm --no-deps web python -m alembic heads
dc run --rm --no-deps web python -m alembic current
```

Comparer révision importée à celle du code. Dernier head local connu :
`l7b1d5f9a304`. Si déjà identiques, pas de migration. Sinon identifier exactement
les migrations manquantes et les scripts métier avant autorisation explicite.
L'import écrit dans la nouvelle base ; ce n'est pas une modification du schéma
de la source. Aucun seed à exécuter systématiquement après restauration.

## 7. Restaurer les fichiers et droits Linux

Archive de confiance produite par notre export uniquement. Examiner d'abord :

```bash
tar -tzf livraison_privee/files.tar.gz | head -30
```

Contenu attendu : `uploads/` et éventuellement `app/uploads/avatars/`, sans
chemin absolu ni `..`. Sur des volumes de destination neufs uniquement :

```bash
dc run --rm --no-deps --user 0 --entrypoint sh \
  -v "$PWD/livraison_privee:/restore:ro" web -c \
  'tar --no-same-owner -xzf /restore/files.tar.gz -C /srv/sngsc && chown -R 10001:10001 /srv/sngsc/uploads /srv/sngsc/app/uploads/avatars'
```

Le compte applicatif UID 10001 doit pouvoir lire/écrire ses fichiers. Aucune
modification des fichiers source. Ne pas répéter l'extraction sur des données
HAUQE nouvelles sans sauvegarde/plan de fusion : elle pourrait les remplacer.

## 8. Démarrer et tester sans courriels

```bash
dc up -d web
dc ps
dc logs --since 2m --tail 80 web
curl -f http://127.0.0.1:8002/
curl -f http://127.0.0.1:8002/api/v1/health
```

Adapter le port si différent dans compose. /health vérifie aussi une requête DB.
Le port n'est accessible que depuis le serveur. Pour une répétition sur Contabo,
utiliser un tunnel SSH sur un port local libre depuis Windows, par exemple :

```powershell
ssh -L 18002:127.0.0.1:8002 root@ADRESSE_CONTABO
```

Puis navigateur `http://localhost:18002`. Tester comptes, MFA, rôles, entreprise,
certifications, documents/preuves de différentes origines et avatar ; puis un
parcours fictif sur la copie, pas en production. Le worker ne doit pas être
lancé, même avec SMTP bloqué (il ferait d'autres tâches métier).

## 9. Fournir l'image à HAUQE si le build n'est pas fait sur leur serveur

Même architecture CPU à vérifier (ex. linux/amd64) :

```bash
docker image inspect sngsc-hauqe:linux --format '{{.Os}}/{{.Architecture}} {{.Id}}'
docker save -o livraison_privee/sngsc-hauqe-linux.tar sngsc-hauqe:linux
sha256sum livraison_privee/sngsc-hauqe-linux.tar
```

Sur HAUQE, après transfert et vérification du hash :

```bash
docker load -i livraison_privee/sngsc-hauqe-linux.tar
```

Il faut aussi les fichiers Compose/deploy, et l'image PostgreSQL téléchargeable
ou livrée séparément pour un serveur sans accès Internet. `docker save` ne
contient pas les volumes ni les données de la base.

## 10. Nginx, sauvegarde et bascule finale

Le modèle `deploy/nginx-hauqe.conf.example` est à adapter : domaine, port,
certificats HTTPS, taille maximale des fichiers, stratégie proxy de l'hébergeur.
Nginx sur l'hôte relaye vers 127.0.0.1:8002. Si Nginx lui-même est conteneurisé,
adapter le réseau/upstream avec l'informaticien ; ce modèle ne convient pas tel quel.
Vérifier `nginx -t` avant reload. Ne pas remplacer le site Contabo actuel.

Avant bascule : nouvelle sauvegarde finale cohérente, vérification des compteurs,
documents, MFA, URL des liens e-mail et mot de passe oublié, SMTP et destinataire
test, plan de sauvegarde hors serveur et test réel de restauration.

Un seul worker doit fonctionner sur la base finale. Après arrêt confirmé du
traitement sur l'ancien système, validation et réglage SMTP :

```bash
# .env.compose.linux : HAUQE_ENABLE_SMTP=true, seulement après accord de bascule.
dc --profile operations up -d web worker
dc logs --since 2m --tail 80 worker
```

La commande cible explicitement worker et active les scans, sauvegardes,
inactivité et résumés. Attention aux anciens messages planifiés et aux comptes
inactifs restaurés : les examiner avant ce démarrage ; SMTP false seul n'arrête
pas les autres tâches. Le réglage individuel d'envoi aux agents reste applicable.

Le client pg_dump 16 est inclus dans l'image Linux pour les sauvegardes internes.
Les sauvegardes hors serveur doivent aussi inclure base, uploads, avatars et
secrets séparés. Le module historique de sauvegarde documentaire n'archive que
uploads : ne pas le considérer seul comme une sauvegarde des avatars.
Les paramètres SQL de droits source ne sont pas reproduits : rôle applicatif
dédié et droits limités selon init-db.sh. Ne pas restaurer les superutilisateurs
source sans nécessité validée.

Retour arrière : conserver Contabo intact ; arrêter web/worker de la nouvelle
installation avant de réactiver l'ancienne. Les nouvelles saisies HAUQE ne sont
pas automatiquement renvoyées vers Contabo : décider de leur récupération avant
le retour. Ne jamais faire fonctionner deux systèmes d'écriture en parallèle.

## 11. Statut et impact

Fichiers de déploiement préparés ; Compose à valider et image Linux à reconstruire
et tester. Aucun commit/push, SSH ou export serveur exécuté par l'assistant.
Validation Compose effectuée sur modèles sans résolution des secrets : réussie.
Six tests ciblés réussis (ports, worker/SMTP, volumes, rôle SQL, export, image).
Contrôle de syntaxe shell sous Git Bash réussi le 13 novembre après autorisation
hors sandbox (la première tentative MSYS était bloquée par les permissions).
Avant usage sur Linux : `sh -n deploy/init-db.sh` puis
`sh -n deploy/export-contabo.sh`. Test d'exécution réel encore nécessaire.
Base PostgreSQL source modifiée : non. Migration créée pour Docker : aucune.
La restauration remplit seulement une nouvelle cible. Toute migration métier
manquante issue des changements antérieurs doit être déclarée séparément.
