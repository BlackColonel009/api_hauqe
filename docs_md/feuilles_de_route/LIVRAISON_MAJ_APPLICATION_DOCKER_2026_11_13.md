# Lot applicatif et Docker préparé le 13 novembre 2026

## Périmètre du commit

Inclure uniquement les modifications applicatives réelles, les tests associés,
la migration et les fichiers Docker/deploy, leurs modèles SANS secrets et les
feuilles de route/guides techniques utiles. Aucune donnée d'exploitation dans
le commit. Aucun retrait de fichiers historiques du dépôt effectué.

Lots fonctionnels inclus :

- actualisation des données sans reconstruction de page, indicateur de fraîcheur ;
- correctifs boutons/formulaires/modals, login afficher/masquer, rapports et filtres ;
- genre du premier contact actif/promoteur, filtres genre et adresse des rapports ;
- collectes : rappels de brouillon, noms des affectations, vues liste/grille,
  transfert de dossiers et archivage/désarchivage de missions vides ;
- vérifications : confirmation de priorité mission, risques R1–R5, exclusivité
  d'écriture selon affectation active, consultation des autres profils maintenue ;
- validation/intégration : demande de correction, avertissement sous réserve,
  blocage ajournement, resoumission et clôture des rappels correspondants ;
- veille/renouvellements : destinataires, jalons propres aux certifications,
  arrêt des rappels de renouvellements déjà décidés et courriels devenus caducs ;
- Docker : configurations test et Linux distinctes, SMTP et worker optionnels,
  export de transfert, rôle SQL applicatif dédié et guide HAUQE.

Les changements sont regroupés car ils ont été développés ensemble depuis le
dernier commit serveur. Ne pas les présenter comme une modification Docker seule.

## Exclusions

Ne pas inclure les fichiers .env réels, mots de passe, clés privées, dumps,
uploads, avatars, sauvegardes, logs, output, tmp, dépendances node_modules,
livrables personnels et anciennes archives app.zip/app_v1.zip supprimées par
l'utilisateur. Les modèles .env*.example ne contiennent que des placeholders.
Ne pas utiliser git add . ou git add -A à la racine.
Les nouveaux motifs .gitignore n'effacent pas l'historique ni le suivi existant
de documents. Ce nettoyage historique est un sujet distinct.

## Base PostgreSQL : OUI, modification de schéma prévue pour ce lot

État Contabo communiqué : PostgreSQL 16.15, révision k6a0c4e8f2b3.
Head local : l7b1d5f9a304. Une seule migration nouvelle dans ce lot :

`alembic/versions/l7b1d5f9a304_contact_genre.py`

Ajout nullable varchar(20) `contacts_entreprise.genre`, et contrainte
`ck_contacts_entreprise_genre` autorisant FEMME/HOMME/AUTRE ou NULL.
Aucune donnée renseignée par déduction, aucune suppression à l'upgrade.
Le downgrade supprimerait la colonne : ne pas l'exécuter pour un retour de code
sans étude des nouvelles données. Pas de seed nécessaire pour cette colonne.

La préparation de ce commit ne lance ni migration, ni modification des données
locales/Contabo. La source doit être sauvegardée avant déploiement.

## Permissions : ajustement de données distinct de la migration

Le script `app.scripts.seed_validation_integration_permissions` reçoit l'ajout
de VALIDATION.RESOUMETTRE_CORRECTION au rôle POINT_FOCAL_BNEC.
Il est idempotent mais synchronise aussi les autres attributions de sa matrice,
et lie toutes les permissions à ADMIN_HAUQE. Il ne supprime pas les droits.
Ne pas l'assimiler à un seed de données métier nécessaire au champ genre.
Vérifier les permissions actuelles et les personnalisations RBAC avant relance ;
ajouter le droit ciblé via l'administration est une alternative.

Si sa matrice est approuvée et doit être synchronisée :

```bash
./.venv/bin/python -m app.scripts.seed_validation_integration_permissions
```

Aucun autre script de rattrapage de données n'est ajouté par ce commit.

## Ordre serveur non Docker, après push approuvé

1. Vérifier services API et worker existants, leurs commandes et éventuels
   rechargements automatiques : ne pas supposer le nom du worker séparé.
2. Réaliser une sauvegarde vérifiée base/fichiers, conserver les secrets source
   séparément, préparer une fenêtre de maintenance adaptée.
3. Arrêter les processus d'écriture confirmés avant de modifier code et schéma,
   particulièrement si rechargement automatique activé.
4. Préserver l'ajout local reportlab de requirements.txt, dans une copie hors
   dépôt ; ne pas reset/checkout le fichier. La version entrante contient déjà
   reportlab avec version minimale. Résoudre proprement ce changement AVANT pull.
5. Pull contrôlé du lot, puis dépendances et migration :

```bash
cd /var/www/api_hauqe
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m alembic current
./.venv/bin/python -m alembic heads
./.venv/bin/python -m alembic upgrade head
./.venv/bin/python -m alembic current
```

Ne continuer vers upgrade que si le chemin attendu est confirmé :
k6a0c4e8f2b3 → l7b1d5f9a304. Si la base est déjà au head, l'upgrade n'ajoute rien.
6. Contrôler/mettre à jour le droit de resoumission du point focal si nécessaire.
7. Redémarrer API et le worker effectivement utilisé. L'API historique démarre
   déjà le worker intégré par défaut : éviter deux workers simultanés. Le choix
   d'un worker séparé impose BACKGROUND_SERVICES_ENABLED=false dans l'API.
8. Vérifier santé DB, connexion/MFA, entreprises/certifications, rapports,
   collectes, boutons, permissions et pièces téléchargées, puis rouvrir les saisies.

## Docker et transfert HAUQE

Le même code reste utilisable sans Docker avec le .env source. Les réglages
BACKGROUND_SERVICES_ENABLED et HAUQE_SMTP_ENABLED sont vrais par défaut ;
les configurations de test les désactivent explicitement, pas la production.

Compose Linux : PostgreSQL 16, client de sauvegarde 16 via PGDG ; pas de port DB
publié, web 127.0.0.1:8002, worker profil operations et SMTP désactivé par défaut.
Dockerfile garde le défaut de build client 17 pour les essais Windows existants ;
Compose Linux force 16. Le dump Windows 17 ne doit pas servir à restaurer Linux16.
Image Linux nouvelle à construire/tester. Aucun build final livré à ce stade.

Une fois la vraie mise à jour Contabo validée : exporter sa base et ses fichiers,
restaurer/tester dans le clone Docker séparé, puis fournir l'image et le paquet
HAUQE selon GUIDE_LIVRAISON_DOCKER_HAUQE.md. Aucun pull dans le clone séparé ne
publie les changements Windows à lui seul : commit et push préalables requis.

## Vérifications de ce lot

- 99 tests unitaires passent. La première tentative sandbox Windows bloquait sur
  socketpair avant les tests async ; relance autorisée hors sandbox réussie.
- 42 tests frontend passent, dont les clics successifs du toggle de mot de passe.
- Head Alembic vérifié : l7b1d5f9a304. Aucune migration exécutée lors de la préparation.
- Compose Linux contrôlé sur modèles sans secrets ; pas de test serveur réel ici.
- Syntaxe des deux scripts shell vérifiée avec Bash sans les exécuter.
- 33 fichiers JavaScript modifiés vérifiés avec node --check, fichiers Python
  du lot analysés par AST. Contrôle des chemins de l'index : aucun fichier privé,
  dump, upload, livrable personnel ou suppression dans le lot préparé.
- Analyse indicative des littéraux sensibles : les occurrences relevées dans
  les guides sont des placeholders, sans copie des valeurs du .env actuel.
- Ces tests ne remplacent pas une recette navigateur et une restauration Linux.

Statut de publication à vérifier dans Git : pas de push automatique.
