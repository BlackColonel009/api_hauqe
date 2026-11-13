# Apprentissage Docker et transfert SNGSC / HAUQE Certif

## Suite Linux — 2 novembre 2026

Actualisation du 13 novembre : source Contabo PostgreSQL 16.15 (pas 17 comme
le poste Windows), révision k6a0c4e8f2b3. Le Compose Linux et son client pg_dump
sont adaptés à 16. Ne pas importer notre dump Windows 17 dans cette cible.
Voir l'état prioritaire dans le guide de livraison Linux. Aucun export ou
migration Contabo réalisé par l'assistant ; publication Git toujours à faire.

L'utilisateur confirme l'application fonctionnelle sous Docker Windows après
correction des dépendances greenlet/argon2. La livraison Linux est maintenant
préparée dans [GUIDE_LIVRAISON_DOCKER_HAUQE.md](GUIDE_LIVRAISON_DOCKER_HAUQE.md).
Le clone Contabo isolé était resté sur 6f48462 : aucun fichier Docker n'y était
encore publié. Ne pas reprendre compose.test.yaml pour le serveur HAUQE.
compose.linux.yaml comporte DB isolée, API et worker optionnel ; SMTP false
par défaut. Aucune action serveur ni publication Git effectuée automatiquement.
Nouvelle image trixie avec client PostgreSQL 17 à construire et tester.
Les essais Windows déjà validés ne constituent pas une recette Linux.

Guide progressif commencé le 5 octobre 2026. À compléter à chaque étape avec
les commandes, leurs explications et les résultats effectivement confirmés.
Ne pas exécuter toutes les sections à l'aveugle : respecter leur statut.

## 1. Objectif et précautions

Apprendre Docker sur Windows 11 avec une copie locale, puis tester une sauvegarde
du serveur Contabo avant le transfert vers l'infrastructure HAUQE.
Il n'est pas nécessaire de dockeriser Contabo pour exporter sa base.

- Ne pas modifier la base existante ou le `.env` actuel pendant l'apprentissage.
- Ne jamais enregistrer de mots de passe, clés de chiffrement ou dumps dans Git.
- Le dump PostgreSQL ne contient pas les fichiers téléversés stockés sur disque.
  Leur sauvegarde et les clés de chiffrement nécessaires seront traitées séparément.
- Les courriels doivent être désactivés dans la future application de test avant
  de lancer son worker ; aucun worker de test n'est encore configuré.
- Un volume conserve les données mais ne remplace pas une sauvegarde.
- Ne pas utiliser `docker volume prune` ou `docker compose down -v` sur les
  volumes à conserver : ces opérations peuvent supprimer les données.

Une image est le modèle du logiciel. Un conteneur est son instance en cours
d'exécution. Un volume stocke les données indépendamment du conteneur.
Compose décrira ensuite l'application, la base et le worker dans un fichier.

## 2. WSL et installation — confirmés par l'utilisateur

Dans PowerShell :

```powershell
wsl --version
```

Affiche les versions de WSL et de son noyau. Résultat communiqué : WSL 3.0.1.0.
Docker Desktop 4.94.0 installé sur Windows 11.

### Incident rencontré : Virtual Machine Platform non activée

Commande proposée dans PowerShell **administrateur**, uniquement si cette
fonctionnalité est désactivée :

```powershell
Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -All -NoRestart
```

Active la fonctionnalité Windows nécessaire au moteur WSL. Enregistrer son
travail puis redémarrer Windows complètement ; redémarrer Docker seul ne suffit
pas. L'utilisateur a confirmé ensuite que le problème était résolu.
Si le message persiste, vérifier Gestionnaire des tâches → Performances →
Processeur → Virtualisation ; une désactivation peut nécessiter un réglage BIOS/UEFI.
Ne pas relancer cette étape lorsque Docker fonctionne déjà.

## 3. Vérification Docker — réussie

Garder Docker Desktop ouvert. Dans PowerShell, le venv Python peut rester actif.

```powershell
docker version
```

Vérifie le client et le moteur. Résultat communiqué : Client et Server 29.8.2,
contexte `desktop-linux`, moteur `linux/amd64`.

```powershell
docker compose version
```

Vérifie Compose. Résultat communiqué : v5.5.1.

```powershell
docker run --rm hello-world
```

Télécharge l'image si nécessaire, lance le conteneur de démonstration et le
supprime à sa sortie (`--rm`). L'image téléchargée reste disponible.
Résultat confirmé : `Hello from Docker!`. Aucun changement dans PostgreSQL/SNGSC.

## 4. Version de la base et disponibilité du port — confirmées

Dans l'outil SQL connecté à la **base locale actuelle** :

```sql
SELECT version();
```

Résultat communiqué : PostgreSQL 17.6, x86_64-windows, 64-bit.
Nous utilisons donc `postgres:17` pour rester sur la même version majeure.
Ce tag peut télécharger une version corrective 17.x plus récente que 17.6.
La version du serveur Contabo reste à vérifier avant sa restauration.

Dans PowerShell :

```powershell
docker ps -a
```

Liste tous les conteneurs, même arrêtés. Résultat : aucun conteneur existant.

```powershell
Get-NetTCPConnection -LocalPort 5433 -ErrorAction SilentlyContinue
```

Cherche les connexions TCP sur 5433. Aucun résultat communiqué : port apparemment
disponible lors du contrôle. Le lancement reste la vérification définitive.

## 5. Créer PostgreSQL de test — démarrage et requête interne confirmés

Cette étape crée une base vide et un volume dédié ; elle n'importe aucune donnée
et ne modifie pas la base locale existante.

### 5.1 Saisir un mot de passe réservé au test

Dans le même PowerShell pour toute cette étape :

```powershell
$dockerTestSecret = Read-Host "Mot de passe de la base Docker de test" -AsSecureString
$env:POSTGRES_PASSWORD = [System.Net.NetworkCredential]::new("", $dockerTestSecret).Password
```

La saisie est masquée. Choisir un mot de passe non vide, distinct de la production,
et le conserver dans un gestionnaire de mots de passe. Ne pas le communiquer dans
la conversation. La variable d'environnement transmet sa valeur à Docker sans
l'inscrire littéralement dans la commande.

Attention : sa valeur est temporairement en clair dans l'environnement du
processus et reste dans la configuration du conteneur, accessible aux personnes
ayant accès à Docker. C'est une méthode de test, pas la configuration finale des secrets.

### 5.2 Créer le conteneur

```powershell
docker run --detach `
  --name hauqe-postgres-test `
  --publish 127.0.0.1:5433:5432 `
  --mount type=volume,source=hauqe_pg_test_data,target=/var/lib/postgresql/data `
  --env POSTGRES_USER=hauqe_test `
  --env POSTGRES_DB=hauqe_certif_test `
  --env POSTGRES_PASSWORD `
  postgres:17
```

Les accents graves en fin de ligne continuent la commande PowerShell : ne pas
ajouter d'espaces après eux. Docker télécharge l'image lors du premier lancement.

| Option | Explication |
| --- | --- |
| `--detach` | Démarre en arrière-plan. |
| `--name` | Donne le nom `hauqe-postgres-test` au conteneur. |
| `--publish` | Rend le port PostgreSQL 5432 accessible sur 5433, uniquement depuis ce PC. |
| `--mount` | Crée/utilise le volume `hauqe_pg_test_data` pour les données PostgreSQL 17. |
| `POSTGRES_USER` | Crée l'utilisateur de test `hauqe_test` ; l'image lui donne les droits superutilisateur. |
| `POSTGRES_DB` | Crée la base vide `hauqe_certif_test`. |
| `POSTGRES_PASSWORD` | Récupère la valeur saisie dans l'environnement PowerShell. |
| `postgres:17` | Utilise l'image officielle PostgreSQL, version majeure 17. |

Les variables d'initialisation agissent lorsque le volume est vide. Changer ces
variables avec un volume déjà initialisé ne change pas automatiquement les
comptes ou mots de passe de la base.
Si le nom de conteneur existe déjà ou si le lancement échoue, s'arrêter et
examiner l'erreur ; ne pas supprimer le volume pour contourner le problème.

### 5.3 Nettoyer les variables temporaires

```powershell
Remove-Item Env:POSTGRES_PASSWORD
Remove-Variable dockerTestSecret
```

Supprime les variables de cette session PowerShell, pas le mot de passe de la
base ni sa valeur enregistrée dans la configuration du conteneur.

### 5.4 Vérifier le démarrage

```powershell
docker logs --tail 30 hauqe-postgres-test
```

Affiche les 30 dernières lignes des journaux. Attendre le message
`database system is ready to accept connections`. Si nécessaire, répéter cette
lecture après quelques secondes.

```powershell
docker exec hauqe-postgres-test psql -U hauqe_test -d hauqe_certif_test -c "SELECT current_database(), version();"
```

Exécute une requête en lecture seule à l'intérieur du conteneur. La base affichée
doit être `hauqe_certif_test`, et la version PostgreSQL doit être 17.x.
Ce test interne ne vérifie pas encore une connexion authentifiée depuis Windows
sur le port 5433 : cela fera partie de la prochaine étape.

### 5.5 Résultats confirmés le 5 octobre 2026

Journal communiqué : `2026-10-05 15:54:42.802 UTC` —
`database system is ready to accept connections`.
La requête interne retourne `hauqe_certif_test` et PostgreSQL 17.11
(Debian, Linux x86_64). Le conteneur est opérationnel ; aucune restauration
SNGSC n'est encore confirmée. Le tag 17 a fourni une version corrective plus
récente que la version locale 17.6, avec la même version majeure.

## 6. Connexion depuis Windows — à exécuter

Dans PowerShell :

```powershell
psql --version
```

Vérifie la disponibilité du client PostgreSQL Windows. Si `psql` n'est pas
reconnu, retrouver le client installé avant de continuer ; il n'est pas nécessaire
de réinstaller PostgreSQL. Ne pas partager les mots de passe.

```powershell
psql -h 127.0.0.1 -p 5433 -U hauqe_test -d hauqe_certif_test -W -c "SELECT current_database(), version();"
```

`-h` et `-p` ciblent explicitement Docker et non la base habituelle sur 5432.
`-W` demande le mot de passe de test saisi à la création. La requête est en
lecture seule. Résultat attendu : `hauqe_certif_test` et PostgreSQL 17.11.
Cette étape contrôle le port publié et l'authentification depuis Windows.
Résultat non confirmé à ce stade.

### Incident : `psql` non reconnu dans PowerShell

L'utilisateur a rencontré `CommandNotFoundException` avec `psql --version`.
Recherche locale en lecture seule : le client existe bien dans
`C:\Program Files\PostgreSQL\17\bin\psql.exe`. Il n'est pas nécessaire de
réinstaller PostgreSQL ni de modifier le PATH global. Utiliser son chemin complet :

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" --version
```

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h 127.0.0.1 -p 5433 -U hauqe_test -d hauqe_certif_test -W -c "SELECT current_database(), version();"
```

L'opérateur PowerShell `&` exécute le programme dont le chemin est entre
guillemets. Saisir le mot de passe Docker de test lorsqu'il est demandé.
Ne pas utiliser le mot de passe de la base locale existante.
La connexion et son résultat restent à confirmer par l'utilisateur.

### Préparation de la sauvegarde locale — contrôles préalables

Après ajout facultatif de `C:\Program Files\PostgreSQL\17\bin` au PATH
utilisateur, rouvrir PowerShell. Ne pas supprimer les entrées PATH existantes.
La connexion Windows vers Docker n'est pas encore confirmée par un résultat.

```powershell
psql -h 127.0.0.1 -p 5433 -U hauqe_test -d hauqe_certif_test -W -c "SELECT current_database(), version();"
```

Dans l'outil SQL habituel connecté à la base **locale SNGSC existante**, et non
à la base Docker, exécuter :

```sql
SELECT current_database() AS base_source,
       current_user AS utilisateur_source,
       inet_server_addr() AS adresse_serveur,
       inet_server_port() AS port_serveur;
```

Cette lecture identifie les paramètres de la source sans afficher son mot de
passe. Le nom `hauqe_certif` apparaît dans l'historique, mais doit être confirmé
avant export. Une adresse/port null peut indiquer une connexion par socket local.
Vérifier également la disponibilité de l'outil de sauvegarde Windows :

```powershell
pg_dump --version
```

Si absent du PATH, utiliser :

```powershell
& "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" --version
```

Aucune sauvegarde ou restauration effectuée par ces commandes. Les commandes
d'export seront ajoutées une fois la source et le client confirmés.

## 7. Sauvegarde de la base locale — à exécuter

Contrôles confirmés par l'utilisateur : connexion Windows vers Docker réussie
(`hauqe_certif_test`, PostgreSQL 17.11) ; source locale `hauqe_certif`, utilisateur
`postgres`, adresse IPv6 `::1`, port 5432 ; client `pg_dump` 17.6.
Le client 17.6 correspond au serveur source 17.6. L'archive sera destinée au
serveur Docker 17.11, de même version majeure. Pas de restauration encore effectuée.

Les commandes suivantes fonctionnent depuis n'importe quel dossier PowerShell,
y compris `C:\Windows\System32`, grâce au chemin absolu de destination.
Stocker le dump hors du dépôt Git : il contient les données et les comptes.

```powershell
$sngscBackupDir = "C:\Users\hp\Documents\Sauvegardes_SNGSC"
New-Item -ItemType Directory -Path $sngscBackupDir -Force | Out-Null
$sngscDumpPath = Join-Path $sngscBackupDir ("hauqe_certif_local_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".dump")
```

Crée le dossier si nécessaire et prépare un nom horodaté. Ne supprime aucun
fichier existant. Conserver ces variables dans le même terminal pour la suite.

```powershell
pg_dump -h localhost -p 5432 -U postgres -d hauqe_certif -W -Fc -f "$sngscDumpPath"
if ($LASTEXITCODE -ne 0) { throw "Sauvegarde échouée : ne pas poursuivre la restauration." }
```

Saisir ici le mot de passe de **PostgreSQL local**, et non celui de Docker.
`localhost` correspond à la source locale, dont la connexion confirmée utilise
`::1`. `-Fc` produit une archive au format personnalisé, restaurable par
`pg_restore`. `-f` écrit directement le fichier : ne pas remplacer par une
redirection PowerShell `>` pour une archive binaire.
L'export ne modifie pas les données source. Il crée une sauvegarde cohérente de
la base ; pour un test reproductible, éviter les saisies pendant l'export.
Les fichiers téléversés sur disque et les rôles PostgreSQL globaux ne sont pas
inclus dans ce dump. Les comptes applicatifs stockés en tables sont inclus.

Après réussite :

```powershell
Get-Item -LiteralPath $sngscDumpPath | Select-Object FullName, Length, LastWriteTime
pg_restore --list "$sngscDumpPath" | Select-Object -First 20
```

Vérifie l'existence/taille et la lecture du catalogue de l'archive, sans restaurer.
Ce contrôle ne remplace pas un test complet de restauration. Ne pas envoyer le
dump dans la conversation ; communiquer seulement le chemin, la taille et les
éventuelles erreurs. Si `pg_restore` n'est pas reconnu, utiliser son chemin
complet dans `C:\Program Files\PostgreSQL\17\bin`.
Exécution et succès de l'export à confirmer avant de poursuivre.

### 7.1 Sauvegarde confirmée le 5 octobre 2026

Deux essais ont échoué : `no password supplied`, puis authentification refusée
pour `postgres`. Un troisième essai s'est terminé avec succès (code de sortie
vérifié). Aucun changement de mot de passe ni de configuration d'authentification
n'a été nécessaire.

- Fichier : `C:\Users\hp\Documents\Sauvegardes_SNGSC\hauqe_certif_local_20261005_162443.dump`.
- Taille : 666 691 octets.
- Catalogue lisible : 370 entrées, format CUSTOM, compression gzip.
- Source/client de sauvegarde : PostgreSQL 17.6.
- La lecture du catalogue confirme le format, pas encore la restauration complète.

## 8. Précontrôle de restauration — à exécuter

Vérifier qu'aucune table applicative n'existe dans la **cible Docker de test** :

```powershell
docker exec hauqe-postgres-test psql -U hauqe_test -d hauqe_certif_test -c "SELECT count(*) AS tables_existantes FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"
```

Résultat attendu : 0. Si différent de zéro, ne pas lancer de restauration ni
supprimer des tables : examiner d'abord la cible. La commande reste en lecture
seule. Les commandes d'import seront ajoutées après confirmation de ce contrôle.
Ne pas confondre la cible `hauqe_certif_test` avec la source `hauqe_certif`.

### 8.1 Cible vide confirmée

L'utilisateur confirme 0 table de base dans le schéma public de
`hauqe_certif_test`. Ce contrôle autorise l'import ci-dessous pour cette cible.
Ne pas répéter l'import après réussite sans réexaminer la base.

## 9. Restaurer dans Docker — à exécuter

Copier l'archive dans le conteneur, sans modifier la source :

```powershell
docker cp "C:\Users\hp\Documents\Sauvegardes_SNGSC\hauqe_certif_local_20261005_162443.dump" hauqe-postgres-test:/tmp/hauqe_certif_local.dump
if ($LASTEXITCODE -ne 0) { throw "Copie échouée : ne pas poursuivre." }
```

Puis utiliser le client pg_restore du conteneur PostgreSQL 17.11 :

```powershell
docker exec hauqe-postgres-test pg_restore -U hauqe_test -d hauqe_certif_test --no-owner --no-privileges --single-transaction --exit-on-error /tmp/hauqe_certif_local.dump
if ($LASTEXITCODE -ne 0) { throw "Restauration échouée : conserver le message et ne pas poursuivre." }
```

- `-d hauqe_certif_test` : cible explicitement la base Docker de test.
- `--no-owner` : ne tente pas d'attribuer les objets au rôle source `postgres` ;
  les objets créés appartiennent à `hauqe_test`.
- `--no-privileges` : ne rejoue pas les droits SQL de la source. Ils devront
  être adaptés pour le déploiement final avec un compte applicatif dédié.
- `--single-transaction` et `--exit-on-error` : l'import est atomique ; une
  erreur SQL arrête la restauration et annule ses modifications transactionnelles.
- Ni `--clean` ni `--create` : aucune suppression préalable ou autre base créée.

Les comptes utilisateurs SNGSC sont des données de tables : ces options ne
retirent pas leurs rôles/permissions applicatifs. Les rôles PostgreSQL globaux
sont distincts et ne sont pas restaurés par ce dump de base.
Une exécution réussie peut ne produire aucun message. Ne pas lancer le worker
ou connecter l'application à cette copie avant son isolation/configuration.

Après réussite :

```powershell
docker exec hauqe-postgres-test psql -U hauqe_test -d hauqe_certif_test -c "SELECT count(*) AS tables_importees FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'; SELECT version_num FROM public.alembic_version;"
```

Lit le nombre de tables restaurées et la révision Alembic de la sauvegarde.
Ne pas lancer `alembic upgrade head` automatiquement : comparer d'abord la
révision restaurée à celle attendue par le code. L'import reste à confirmer.

### 9.1 Résultat de restauration confirmé

L'utilisateur confirme 73 tables publiques importées et la révision Alembic
`l7b1d5f9a304`. Ces contrôles confirment la présence du schéma restauré ; ils
ne constituent pas encore un test de l'application ou des documents sur disque.
Ne pas répéter la restauration dans cette base désormais remplie.

### 9.2 Comparer les volumes de données — à exécuter

Dans l'outil SQL habituel connecté à la base locale source :

```sql
SELECT 'utilisateurs' AS rubrique, count(*) AS nombre FROM utilisateurs
UNION ALL SELECT 'entreprises', count(*) FROM entreprises
UNION ALL SELECT 'certifications', count(*) FROM certifications;
```

Dans PowerShell, pour la copie Docker :

```powershell
docker exec hauqe-postgres-test psql -U hauqe_test -d hauqe_certif_test -c "SELECT 'utilisateurs' AS rubrique, count(*) AS nombre FROM utilisateurs UNION ALL SELECT 'entreprises', count(*) FROM entreprises UNION ALL SELECT 'certifications', count(*) FROM certifications;"
```

Ces lectures comparent trois registres principaux sans afficher leurs données
personnelles. Les nombres doivent correspondre à la sauvegarde ; de nouvelles
saisies dans la source depuis l'export peuvent expliquer un écart.
Les documents téléversés sur disque ne sont toujours pas copiés. Les courriels
et rappels historiques sont présents dans la base : ne pas lancer le worker de
test sans désactivation sûre des envois.

### 9.3 Comparaison des registres confirmée

L'utilisateur confirme des nombres identiques entre source et copie pour
utilisateurs, entreprises et certifications. Pas de test des fichiers ou de
connexion applicative encore effectué.

## 10. Préparer l'image de l'application — à exécuter

Fichiers préparés dans le projet : `Dockerfile`, `.dockerignore`,
`compose.test.yaml`, `.env.docker.test.example`. Aucune modification du `.env`
existant. Le fichier privé `.env.docker.test` est exclu de Git.
Le build ne copie ni `.env`, ni dumps, ni documents téléversés dans l'image.
L'image utilise Python 3.12 et un utilisateur non-root. Les dépendances actuelles
du projet ne sont pas verrouillées à des versions exactes ; le verrouillage et
les outils techniques de sauvegarde seront à finaliser avant production.

Le code dispose désormais de deux réglages, tous deux vrais par défaut pour
préserver le comportement habituel : `BACKGROUND_SERVICES_ENABLED` et
`HAUQE_SMTP_ENABLED`. Compose de test force les deux à false et vide les
identifiants SMTP. Le premier empêche le worker intégré de démarrer dans l'API.
Le second bloque le traitement EMAIL et le transport SMTP direct sans vider
la file de messages. Aucun changement de schéma PostgreSQL.
Lancer séparément le worker permanent ferait toujours démarrer ses autres
tâches : ne pas le lancer pendant cette étape de test.
Trois tests dédiés réussissent : SMTP direct bloqué, file EMAIL non ouverte
quand SMTP désactivé, worker intégré non démarré quand désactivé.
La suite complète a été interrompue car elle ne terminait pas dans cet
environnement Windows ; ne pas considérer ce lot comme validé de bout en bout.

Depuis PowerShell :

```powershell
Set-Location "C:\Users\hp\Documents\APK WEB Projets R.1.3.5 et R1.4.3"
docker build -t sngsc-hauqe:test .
if ($LASTEXITCODE -ne 0) { throw "Construction échouée : ne pas poursuivre." }
```

Le point final désigne le dossier du projet comme contexte de construction.
`-t` donne le nom `sngsc-hauqe:test` à l'image. Cette commande télécharge Python,
installe les dépendances et empaquette le code. Elle ne lance pas l'application,
ne se connecte pas à la base et n'exécute aucune migration.
La première construction peut prendre plusieurs minutes. En cas d'erreur,
conserver les dernières lignes et ne pas passer au lancement.

```powershell
docker image ls sngsc-hauqe
```

Vérifie la présence de l'image ; sa construction reste à confirmer.

### Configuration du lancement — préparée mais pas encore à exécuter

Compose utilisera un réseau externe `hauqe-test-network`, auquel la base
existante devra être raccordée sans la recréer. Dans ce réseau, l'API joindra
`hauqe-postgres-test:5432` (pas localhost:5433). Le navigateur Windows utilisera
`http://localhost:8001`. Aucune exposition de l'API sur le réseau local.
Les volumes des documents, avatars, logs et sauvegardes seront distincts des
fichiers Windows ; les documents sont encore absents de ces nouveaux volumes.

Avant lancement : créer le fichier privé à partir de l'exemple, renseigner le
mot de passe de test encodé pour l'URL et reprendre les clés source privées
nécessaires à la MFA. Ne jamais afficher ces valeurs dans la conversation.
Ne pas démarrer avec les valeurs `REPLACE_...` du modèle. La copie de documents
devra tenir compte des chemins enregistrés dans la base Windows avant de
prétendre qu'ils sont utilisables sous Linux.
Cette configuration est pédagogique, pas encore un déploiement HAUQE final.

### 10.1 Construction confirmée

L'utilisateur confirme l'image `sngsc-hauqe:test`, ID `b757f26ef8f9`,
427 MB d'utilisation disque et 98,6 MB de contenu selon Docker Desktop.
Ces chiffres sont deux mesures de stockage Docker, pas deux images différentes.
La construction réussie ne confirme pas encore le démarrage applicatif.

## 11. Réseau Docker et configuration privée — à exécuter

Un réseau dédié permettra à l'API de joindre la base par son nom de conteneur.
Dans un conteneur, localhost désigne ce conteneur lui-même, pas PostgreSQL voisin.
Le port 5433 est utilisé depuis Windows ; entre conteneurs ce sera 5432.

```powershell
docker network inspect hauqe-test-network --format '{{.Name}}'
```

Si Docker indique que ce réseau n'existe pas, le créer :

```powershell
docker network create hauqe-test-network
```

Puis raccorder la base existante, sans recréer son volume ou restaurer de nouveau :

```powershell
docker network connect hauqe-test-network hauqe-postgres-test
```

Cette dernière commande est à exécuter une seule fois. Si Docker indique que
l'endpoint existe déjà, la base est déjà raccordée : vérifier le réseau plutôt
que supprimer quoi que ce soit. Contrôler :

```powershell
docker network inspect hauqe-test-network --format '{{range .Containers}}{{println .Name}}{{end}}'
```

Le nom `hauqe-postgres-test` doit apparaître. Aucun lancement de l'application
ni changement des tables avec ces commandes.

### Préparer le fichier privé sans écraser un fichier existant

Dans le dossier du projet :

```powershell
if (Test-Path -LiteralPath '.env.docker.test') {
    Write-Host 'Le fichier existe déjà : le conserver et vérifier son contenu.'
} else {
    Copy-Item -LiteralPath '.env.docker.test.example' -Destination '.env.docker.test' -ErrorAction Stop
}
```

Éditer ensuite `.env.docker.test` localement, sans envoyer son contenu. Renseigner
DATABASE_URL avec le mot de passe de test encodé pour une URL, SECRET_KEY et
MFA_FERNET_KEY avec les clés privées de la source lorsque nécessaires.
Ne jamais remplacer le `.env` actuel, ni y changer DATABASE_URL.
Le raccordement réseau est confirmé par l'utilisateur : l'inspection de
`hauqe-test-network` affiche `hauqe-postgres-test`. La configuration privée
reste à renseigner.
Ne pas lancer Compose avec les placeholders `REPLACE_...`.

### Valeurs à renseigner localement

1. DATABASE_URL : conserver utilisateur `hauqe_test`, hôte
   `hauqe-postgres-test`, port 5432, base `hauqe_certif_test`. Remplacer seulement
   `REPLACE_ENCODED_TEST_PASSWORD` par le mot de passe Docker, encodé pour une URL.
2. SECRET_KEY : recopier la valeur privée de la source depuis le `.env` existant
   vers le fichier de test, sans modifier la source.
3. MFA_FERNET_KEY : recopier la clé source si elle est configurée pour pouvoir
   déchiffrer les secrets MFA importés. Si absente dans la source, laisser vide
   dans le test plutôt que conserver le placeholder. La MFA ne sera alors pas
   utilisable sans configuration supplémentaire ; ne pas inventer une clé pour
   déchiffrer des données historiques.
4. Garder les deux interrupteurs de test à false et les champs SMTP vides.

Pour encoder le mot de passe sans l'inscrire en clair dans l'historique des
commandes, saisir dans PowerShell :

```powershell
$sngscTestSecret = Read-Host 'Mot de passe PostgreSQL Docker de test' -AsSecureString
$sngscEncodedPassword = [Uri]::EscapeDataString([System.Net.NetworkCredential]::new('', $sngscTestSecret).Password)
$sngscEncodedPassword
```

Le résultat affiché reste un secret (l'encodage n'est pas du chiffrement).
Ne pas envoyer de capture ou copier la sortie dans la conversation.
Après avoir remplacé le placeholder dans le fichier privé, nettoyer :

```powershell
Remove-Variable sngscTestSecret, sngscEncodedPassword
```

Éviter d'afficher la configuration résolue avec `docker compose config`, qui
pourrait exposer les secrets. Les fichiers privés restent exclus de Git et
de l'image Docker. Une validation et un démarrage seront faits à l'étape suivante.

### 11.1 Reprise du 29 octobre 2026

L'utilisateur confirme avoir renseigné `.env.docker.test`. Les secrets n'ont
pas été affichés. Une vérification de disponibilité Docker échoue sur le pipe
`dockerDesktopLinuxEngine` introuvable : le moteur Linux n'est pas disponible
dans cette session. Aucun démarrage applicatif ni migration effectué.
Ouvrir Docker Desktop et attendre le démarrage du moteur, puis :

```powershell
docker version
docker ps --format '{{.Names}} {{.Status}} {{.Ports}}'
```

`docker version` doit afficher Client et Server sans erreur. La base
`hauqe-postgres-test` doit être en cours d'exécution. Si elle existe mais est
arrêtée, la démarrer, sans la recréer ni restaurer de nouveau :

```powershell
docker start hauqe-postgres-test
```

Si elle est introuvable, s'arrêter pour vérifier le contexte et les conteneurs.
Ne pas supposer que le volume ou les données ont disparu.
Le lancement Compose sera poursuivi une fois le moteur et la base confirmés.

### 11.2 Redémarrage de la base confirmé

L'utilisateur a exécuté `docker start hauqe-postgres-test` avec retour du nom
du conteneur. La base était arrêtée ; pas de recréation ou nouvelle restauration.
Vérifier sa disponibilité avant le lancement web :

```powershell
docker exec hauqe-postgres-test pg_isready -U hauqe_test -d hauqe_certif_test
```

Résultat attendu : `accepting connections`. Ce contrôle ne remplace pas une
connexion authentifiée de l'application.

## 12. Premier démarrage de l'application de test — à exécuter

Depuis le dossier du projet, valider sans afficher les secrets :

```powershell
docker compose -f compose.test.yaml config --quiet
```

En cas d'erreur, s'arrêter. Cette validation contrôle la configuration Compose,
pas la validité du mot de passe ou des clés. Ne pas publier la sortie de
`docker compose config` sans `--quiet` : elle peut contenir les secrets.

Si PostgreSQL est prêt et la validation réussit :

```powershell
docker compose -f compose.test.yaml up -d --build web
```

`--build` met à jour l'image avec le code courant (notamment le correctif login
du 12 octobre). `-d` lance en arrière-plan ; `web` désigne l'application seule.
Compose réutilise la base externe sur le réseau existant et crée les volumes
séparés de l'application si absents. SMTP et worker intégré restent désactivés
par les valeurs forcées du fichier Compose. Aucune migration ni seed automatique.

Contrôler :

```powershell
docker compose -f compose.test.yaml ps
docker compose -f compose.test.yaml logs --tail 60 web
```

Attendre `Application startup complete` et Uvicorn sur 0.0.0.0:8000 dans le
conteneur. Ouvrir depuis Windows `http://localhost:8001` (ou
`http://127.0.0.1:8001`). Le port 8001 doit être libre. Le démarrage et la
connexion applicative restent à confirmer ; les documents ne sont pas encore
copiés dans les volumes de test. Masquer toute information sensible avant de
partager un message d'erreur. Ne pas supprimer de volume en cas d'échec.

### 12.1 Incident de démarrage : dépendance greenlet absente

Le premier lancement web échoue avec `ImportError: The SQLAlchemy asyncio
module requires that the Python 'greenlet' library is installed`.
Correction : `sqlalchemy[asyncio]>=2.0` dans requirements.txt afin d'installer
l'extra officiel asyncio, incluant greenlet. Le Dockerfile teste également
l'import greenlet et create_async_engine pendant la construction.
Ne pas installer manuellement le paquet dans un conteneur éphémère : corriger
l'image pour conserver le résultat aux prochains déploiements.

```powershell
docker compose -f compose.test.yaml up -d --build web
docker compose -f compose.test.yaml logs --since 2m --tail 60 web
```

Reconstruit/recrée uniquement web selon la configuration, sans supprimer la base
externe ou ses volumes. Le changement de requirements invalide la couche pip :
pas besoin de `--no-cache`. Le nouveau démarrage reste à confirmer.
Schéma PostgreSQL modifié : non. Migration et seed : aucun.

### 12.2 Incident de démarrage : module argon2 absent

Après greenlet, le démarrage signale `ModuleNotFoundError: No module named
'argon2'`. La dépendance de distribution correspondante est `argon2-cffi` ;
elle était absente de requirements malgré son utilisation dans les utilitaires
de sécurité et services de compte/MFA/mot de passe.
Ajout de `argon2-cffi>=23.1,<26`. Aucun changement des algorithmes ou mots de passe.
Audit AST des imports Python app : les racines externes relevées sont argon2,
cryptography, fastapi, openpyxl, pydantic, pydantic_settings, reportlab, sqlalchemy ;
après correction, elles sont toutes déclarées. Ce contrôle ne couvre pas toutes
les dépendances optionnelles/dynamiques ou ressources système.
Le Dockerfile exécute désormais pip check et un contrôle d'import des principales
bibliothèques (dont greenlet, argon2 et psycopg) pendant le build.

```powershell
docker compose -f compose.test.yaml up -d --build web
docker compose -f compose.test.yaml logs --since 2m --tail 60 web
```

Nouveau démarrage encore à confirmer. Ni migration, ni seed, ni suppression de
volume. Base PostgreSQL modifiée : non.

## 13. Prochaines étapes — pas encore exécutées

1. Journaux et requête interne : confirmé.
2. Vérifier la connexion depuis Windows au port 5433.
3. Sauvegarder la base locale puis restaurer dans la base Docker isolée.
4. Configurer une application de test séparée : fichiers, clés, courriels désactivés.
5. Tester les données, comptes, documents et parcours métier.
6. Passer à Compose et préparer un déploiement reproductible.
7. Vérifier la version de Contabo et tester une copie de sa sauvegarde.
8. Préparer le paquet de transfert HAUQE et le plan de bascule/retour arrière.

Les commandes de restauration et de déploiement seront ajoutées après vérification
des noms réels, des versions et des chemins. Aucune migration Alembic exécutée
dans Docker à ce stade. Les mises à jour du serveur actuel restent un lot distinct.

## 14. Références officielles

- [Installation Windows](https://docs.docker.com/desktop/setup/install/windows-install/)
- [Moteur WSL 2](https://docs.docker.com/desktop/features/wsl/)
- [Image PostgreSQL et variables d'initialisation](https://hub.docker.com/_/postgres)
- [Volumes persistants](https://docs.docker.com/engine/storage/volumes/)
- [Docker Compose](https://docs.docker.com/compose/intro/compose-application-model/)
- [Restauration PostgreSQL](https://www.postgresql.org/docs/current/app-pgrestore.html)
