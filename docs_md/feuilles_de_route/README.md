# Répertoire unique des feuilles de route HAUQE Certif

### 13 novembre 2026 — Commit ciblé applicatif et Docker

Voir [LIVRAISON_MAJ_APPLICATION_DOCKER_2026_11_13.md](LIVRAISON_MAJ_APPLICATION_DOCKER_2026_11_13.md)
pour le périmètre exact, exclusions, tests et ordre serveur. Une migration genre
l7b1d5f9a304 après k6a0c4e8f2b3 et un ajustement de permission point focal distinct.
99 tests unitaires et 42 frontend réussis. Aucun push/migration serveur automatique.

### 13 novembre 2026 — Diagnostic réel Contabo et cible PostgreSQL 16

Docker 29.1.3 et Compose 2.40.3 installés ; base source PostgreSQL 16.15,
révision k6a0c4e8f2b3. Clone propre resté à 6f48462 sans Dockerfile/Compose/deploy.
Fichiers locaux non publiés : publier un lot applicatif cohérent avant tout pull.
Compose Linux cible désormais postgres:16-bookworm avec argument de build
POSTGRES_MAJOR=16 ; Dockerfile utilise le client PGDG correspondant. Build test
Windows conserve le défaut 17. Ne pas restaurer le dump Windows 17 vers Linux16.
Sept tests ciblés passent ; build Linux réel encore à effectuer.
Base source modifiée par ce diagnostic : non. Migration nécessaire pour les
derniers modèles métier : l7b1d5f9a304 (contacts_entreprise.genre nullable et
contrainte). Non appliquée sur Contabo ; aucun seed pour cette migration.
Déploiement à ordonner : sauvegarde, code/dépendances, migration contrôlée,
redémarrage et recette, puis export et test Docker dans le clone séparé.


### Transfert complet Contabo vers HAUQE

Livraison finale obligatoirement Dockerisée, confirmé par l'utilisateur : export
source indépendant uniquement pour ne pas perturber Contabo ; livrer image Linux,
Compose, dump, fichiers et guide ensemble après test de restauration.

Voir GUIDE_TRANSFERT_COMPLET_CONTABO_HAUQE.md. Export source désormais constitué
du dump, du code applicatif Contabo et des uploads/avatars, avec empreintes.
Secrets séparés et inventaire des chemins nécessaires. Export réel non exécuté.
Docker n'est pas un préalable à cette sauvegarde. Aucun changement de la source.

### 2 novembre 2026 — Livraison Docker Linux HAUQE préparée

Voir GUIDE_LIVRAISON_DOCKER_HAUQE.md : export Contabo lecture seule par
deploy/export-contabo.sh, dump + fichiers/avatars + hashes, secrets séparés.
compose.linux.yaml : base non exposée, API localhost:8002, worker profil
operations et SMTP false par défaut, rôle SQL applicatif non superutilisateur.
Dockerfile passe à Python 3.12 slim trixie avec client PostgreSQL 17 pour backups ;
alias /var/www/api_hauqe vers /srv/sngsc pour anciens chemins documentaires Linux.
Échantillon de chemins et téléchargements à vérifier avant livraison réelle.
Windows confirmé fonctionnel ; nouvelle image/Linux encore à tester. Pas de
commit/push ni action Contabo exécutés. Conserver la production actuelle intacte.
Le clone isolé Contabo doit recevoir un lot Git complet et approuvé ; attention
aux changements métier/migrations antérieurs non publiés. Ne pas git add .
Base PostgreSQL source modifiée : non. Aucune nouvelle migration ni seed Docker.
La restauration prévue écrit uniquement dans la nouvelle base cible vide.


### 29 octobre 2026 — Docker : dépendance Argon2 et contrôle d'import

Ajout argon2-cffi>=23.1,<26 dans requirements pour les imports argon2 déjà
utilisés. Dockerfile : pip check et imports des bibliothèques principales.
Audit AST des imports app effectué ; ne remplace pas un test complet Docker.
Reconstruire web avec Compose --build. Démarrage corrigé encore à confirmer.
Aucun changement de mots de passe, de schéma, de seed ou de migration.
Base PostgreSQL modifiée : non. Guide Docker mis à jour.


### 29 octobre 2026 — Docker : dépendance SQLAlchemy asyncio

Erreur de démarrage greenlet absent : requirements utilise désormais
sqlalchemy[asyncio]>=2.0 et le Dockerfile teste ses imports à la construction.
Reconstruire web : docker compose -f compose.test.yaml up -d --build web.
Résultat du nouveau build/démarrage à confirmer. Ne pas supprimer les volumes.
Base PostgreSQL modifiée : non. Aucune migration ni seed.


### 12 octobre 2026 — Connexion : bouton afficher/masquer sans latence

Ancien bouton initial remplacé par un slot neutre et un bouton natif neuf,
écouteur click direct, data-no-action-loader, SVG stable sans createIcons au clic.
Ne pas reconstruire le bouton ou son icône à chaque interaction. Clic SVG
et clavier traités nativement ; état aria-pressed et libellé accessibles.
Champ désactivé respecté et valeur du mot de passe préservée. Aucun changement
de la connexion, MFA ou soumission du formulaire. Pas de nouveau modal.
Test simulé : 20 clics successifs et champ désactivé réussissent ; syntaxe JS
validée. Test navigateur réel/zoom non effectué, à confirmer par l'utilisateur.
Cache connexion/router/shell 20261012-1. Déployer les assets/templates et faire
Ctrl+F5 ; reconstruire l'image si utilisée sous Docker (code embarqué).
Base PostgreSQL modifiée : non. Migration/seed : aucun.


### 5 octobre 2026 — Préparation Docker pédagogique isolée

Base de test restaurée par l'utilisateur : 73 tables, head l7b1d5f9a304,
trois registres principaux comparés sans écart. Dockerfile non-root Python 3.12,
contexte filtré sans secrets/dumps/uploads, Compose de test sans worker séparé.
API utilise désormais BACKGROUND_SERVICES_ENABLED (défaut true) ; transport
EMAIL utilise HAUQE_SMTP_ENABLED (défaut true), garde la file intacte si false.
Compose force ces deux paramètres à false et vide le SMTP : autres installations
inchangées par défaut. .env actuel préservé, .env.docker.test privé ignoré Git.
Build/lancement non encore validés dans Docker. Documents Windows non encore
copiés ni chemins contrôlés. Production, sauvegardes et worker à finaliser.
Commandes et statuts dans GUIDE_APPRENTISSAGE_DOCKER_SNGSC.md.
Base PostgreSQL modifiée (schéma) : non. Migration/seed : aucun pour ce lot.
Une copie de test a été remplie par restauration, sans changer la source.


### 5 octobre 2026 — Guide progressif Docker Windows puis Linux

Voir [GUIDE_APPRENTISSAGE_DOCKER_SNGSC.md](GUIDE_APPRENTISSAGE_DOCKER_SNGSC.md).
Commandes et explications consignées au fil des essais ; distinguer résultats
confirmés et étapes proposées. Docker et PostgreSQL de test 17.11 validés par
l'utilisateur ; connexion Windows et restauration encore à vérifier.
Cette mise à jour est documentaire uniquement, sans modification de la base existante.

### 4 octobre 2026 — Exclusivité des affectations de vérification

Sans affectation active, tout vérificateur habilité peut intervenir. Dès qu'une
affectation active existe, seuls les vérificateurs affectés peuvent modifier ;
ADMIN_HAUQE et POINT_FOCAL_BNEC conservent leur accès de gestion. Les autres
gardent la consultation. Plusieurs affectations actives autorisent chacun des
agents concernés. Statuts actifs : ACTIF, ACTIVE ou null ; les dates restent
informatives. Désactiver toutes les affectations rend le dossier à nouveau libre.
Contrôle serveur sur les 14 mutations du service de vérification, avec verrou
du dossier partagé avec les changements d'affectation. Les permissions de rôle
restent requises : aucune permission d'affecter accordée aux vérificateurs.
Interface : actions conditionnées par un endpoint de droits du dossier ; ancien
observateur de réouverture retiré pour éviter le réaffichage et les mutations répétées.
Tests unitaires : 89 réussis, dont 5 cas dédiés. Clics/zoom réels non vérifiés.
Base PostgreSQL modifiée : non pour cette mise à jour. Migration/seed : aucun.
Déployer puis redémarrer l'API sngsc ; rechargement navigateur Ctrl+F5.
Cache de détail et shell : 20261004-13. Les migrations des lots antérieurs restent nécessaires.


### 4 octobre 2026 — Ouverture vérification : priorité héritée et risque

Prompts libres remplacés par modal HAUQE scrollable. Mission réellement liée
résolue au clic ; priorité affichée en lecture seule puis confirmation requise.
Si absente, message Non renseignée sans inventer de priorité. Choix requis
R1 faible, R2 modéré, R3 significatif, R4 élevé, R5 critique ; API d'ouverture
accepte uniquement R1–R5 ou null. Autres écrans et risques existants inchangés.
Boutons natifs directs, verrou contre double ouverture, annulation sans création.
Deux tests dédiés passent ; zoom/clics réels encore à confirmer.
Base PostgreSQL modifiée : non. Migration/seed : aucun. Cache 20261004-12.
Déployer backend/assets puis redémarrer API sngsc.

### 4 octobre 2026 — Marges et alignement en-tête Collecte

En-tête explicitement flex : flex-wrap seul ne suffisait pas sans display.
Commandes Liste/Grille/tri : margin-top 8px, marges latérales neutralisées ;
padding extérieur conservé desktop/mobile. Aucune modification événementielle.
Contrôle CSS effectué ; rendu réel encore à confirmer. Cache 20261004-11.
Base PostgreSQL modifiée : non. Aucune migration ni seed pour ce lot.

### 4 octobre 2026 — Commandes du registre alignées

Liste/Grille et tri Date prévue regroupés dans un conteneur flex sur la même
ligne. Identifiants et événements préservés. Base PostgreSQL modifiée : non.
Migration/seed : aucun. Cache CSS 20261004-10. Rendu navigateur à confirmer.

### 4 octobre 2026 — Padding des blocs Liste/Grille Collecte

Marges intérieures ajustées pour en-tête, cartes, missions dépliées, lignes
de collecte et pagination ; padding réduit sur mobile et au zoom.
CSS limité à collectes-panel, sans modification des boutons/événements.
Contrôle visuel réel encore à confirmer. Base PostgreSQL modifiée : non.
Migration/seed : aucun. Cache collectes.css 20261004-9.

### 4 octobre 2026 — Vues Liste / Grille des campagnes terrain

Sélecteur natif Liste/Grille dans l'en-tête du registre ; grille de cartes
campagnes, mêmes missions/collectes/actions que la liste. Un seul arbre DOM
actif, slots uniques et écouteurs directs réhydratés. Filtres, pagination et
état déplié conservés ; changement de vue sans appel API ni écriture serveur.
Responsive/dark prévus, test statique passe ; clics/zoom réels à confirmer.
Base PostgreSQL modifiée : non. Migration/seed : aucun. Cache 20261004-8.

### 4 octobre 2026 — Résumé du registre Collecte terrain

Trois compteurs séparés campagnes/missions/collectes et pagination distincte.
Mention Sur cette page car compteurs calculés sur les lignes chargées, non
sur la base entière. Styles verts discrets, flex-wrap, thème sombre et mobile.
Boutons et calculs conservés ; syntaxe JS vérifiée, rendu réel à confirmer.
Base PostgreSQL modifiée : non. Migration/seed : aucun. Cache 20261004-7.

### 4 octobre 2026 — État visible des missions dans Déplacer

Listes source/destination : Archivée — désarchivage requis, ou Non archivée
avec statut métier traduit. État de source également affiché sous la liste.
Après archivage/désarchivage : libellés actualisés et destinations ajustées
sans fermer/réouvrir. Test des libellés passe ; test navigateur encore requis.
Base PostgreSQL modifiée : non. Migration/seed : aucun. Cache 20261004-6.

### 4 octobre 2026 — Désarchivage et visibilité terrain

Gérer les campagnes > Déplacer / archiver les missions : sélectionner une
mission archivée puis Désarchiver, avec motif et confirmation. POST dédié
réservé aux admins HAUQE/point focal, audit et reprise au statut PLANIFIEE
(ancien statut non stocké séparément). Campagne active requise.
Nouvelle collecte sur mission ARCHIVEE : alerte avant navigation, message
coordonnateur « veuillez désarchiver » ou collecteur « contactez le point
focal ». Formulaire direct et écriture serveur également bloqués.
Registre et synthèse Collecte terrain filtrent les campagnes inactives ;
aucune suppression, historique toujours accessible dans Gérer les campagnes.
Tests transfert/archivage/désarchivage/filtrage : 5 passent. Validation réelle
navigateur encore requise. Assets version 20261004-5.
Schéma PostgreSQL modifié : non ; statut modifié seulement au clic confirmé.
Aucune migration ni seed. Déployer backend/assets et redémarrer API sngsc.

### 4 octobre 2026 — Déplacement de dossiers entre missions/campagnes

Gérer les campagnes : Déplacer / archiver les missions, modal thème HAUQE
avec scroll, source, sélection des dossiers, destination (toutes campagnes),
motif et confirmation. Boutons natifs neufs avec écouteurs directs.
Accès exige COLLECTE.AFFECTER ET rôle ADMIN_HAUQE ou POINT_FOCAL_BNEC.
POST missions/{id}/deplacer-collectes déplace toutes les révisions des dossiers
sélectionnés sans recréer fiches, preuves, vérifications, contrôles, validations
ou intégrations. Refus si doublon entreprise destination, campagne inactive,
mission destination archivée/annulée ou responsables non affectés activement.
Les affectations ne sont pas copiées silencieusement : les préparer avant.
POST missions/{id}/archiver refuse toute mission contenant une fiche/révision,
préserve historique et affectations. Verrous mission pour transfert/archivage
et écriture collecte ; archivage direct via PATCH générique refusé.
Ancien lien reprise : GET missions/dossiers/{fiche_id}/localisation résout la
mission réelle au chargement du formulaire et ajuste l'URL sans recréer page.
Contexte campagne/mission des pages aval reflète la destination. Messages déjà
envoyés et codes BNEC existants non réécrits. Motif/origine/destination audités.
Tests automatisés permissions, déplacement intercampagne avec révisions,
mission non vide et interdiction d'écrire dans une mission archivée.
Test navigateur zoom/boutons et parcours réel encore à confirmer ; aucun
déplacement de données réelles exécuté pendant le développement.
Schéma PostgreSQL modifié : non. Migration/seed/script : aucun pour ce lot.
Les données de mission_id/statut changent uniquement sur action confirmée.
Déployer code backend/templates/assets puis sudo systemctl restart sngsc.
Cache scripts collecte/campagnes/router/shell et CSS : 20261004-4.

### 4 octobre 2026 — Boutons information du tableau de bord

dashboard-api.css enfin chargé dans index : styles des boutons arrondis,
positionnement et définitions, dont mode sombre. Espace réservé aux libellés.
Boutons natifs neufs, SVG stable et écouteur click direct ; activation clavier
native, sans déclencher la navigation de la carte. Chargeur automatique exclu.
Syntaxe JS vérifiée, 12 tests de rafraîchissement passent ; rendu/clics réels
encore à confirmer. Aucun changement aux données ou calculs des indicateurs.
Base PostgreSQL modifiée : non. Migration/seed : aucun. Cache 20261004-3.

### 4 octobre 2026 — Noms dans Affectations actuelles

Liste des affectations enrichie par utilisateur_nom depuis utilisateurs,
sans dépendre de la liste des collecteurs actifs. Le formulaire affiche ce
nom en priorité, jamais utilisateur_id comme texte de secours.
UUID conservés seulement pour les liaisons techniques. Boutons inchangés.
Syntaxes JS/Python vérifiées ; contrôle interactif encore à confirmer.
Base PostgreSQL modifiée : non. Migration/seed : aucun pour ce lot.
Déployer backend et assets, redémarrer API sngsc. Cache version 20261004-2.

### 4 octobre 2026 — Son du rappel brouillon

Cloche synthétisée Web Audio : un coup à l'apparition, deux à la fermeture,
un quand un lien de reprise est cliqué. Navigation non bloquée par l'audio.
Autoplay refusé : apparition silencieuse, sans son retardé au clic suivant ;
actions utilisateur tentent de reprendre l'audio. Arrêt à la déconnexion.
Trois tests passent dont nombre de coups et autoplay bloqué ; écoute réelle
encore à confirmer. Assets shell/rappel version 20261004-1.
Base PostgreSQL modifiée : non. Aucune migration, aucun seed pour ce lot.

### 4 octobre 2026 — Rappel personnel des collectes en brouillon

Après connexion/chargement de session, cloche animée (sans son) et message
avec entreprise, mission et liens pour reprendre ses brouillons. Responsable
de fiche ciblé quel que soit son rôle, jamais tous les brouillons pour un admin.
GET authentifié /collectes/mes-brouillons, lecture seule des données existantes.
Fermeture native directe, affichage unique par chargement/session ; purge à la
déconnexion et rejet des réponses anciennes. Animation réduite si préférence
accessibilité. Scroll/mobile/thème sombre prévus. Aucun mail ni échéance créé.
Trois tests passent : requête personnelle, absence/double initialisation,
déconnexion pendant requête. Animation et clics réels encore à confirmer.
Base PostgreSQL modifiée : non. Migration/seed : aucun pour ce lot.
Déployer backend et assets, redémarrer le service API sngsc ; aucun worker
supplémentaire. Cache shell et rappel : 20261003-13.

### 3 octobre 2026 — Réactivation des campagnes

Campagne inactive : action Réactiver avec confirmation, bouton natif neuf
et écouteur direct. PATCH existant du seul statut vers ACTIVE, puis relecture
du registre. Missions et collectes non modifiées ; permissions inchangées.
Trois tests : activation, annulation et retry après erreur. Test navigateur
encore à confirmer. Assets campagne/router/shell version 20261003-12.
Schéma PostgreSQL modifié : non ; seule la campagne choisie change de statut
lors du clic confirmé. Aucune migration, aucun seed ni script serveur.

### 3 octobre 2026 — Latence corbeilles et observateur métier

business-rules-ui observait ses propres modifications puis relançait enhance
et createIcons après 20ms, alimentant une boucle de remplacement DOM.
Observateur déconnecté pendant enhance, rétabli en finally ; conversion des
icônes seulement si un i[data-lucide] non converti existe. Corbeilles Entreprise
avec SVG définitif sans data-lucide et pointer-events:none sur l'icône.
Conserver ce principe : aucun observateur ne doit boucler sur ses écritures.
Tests automatisés création/modification et observateur ; clics réels à confirmer.
Assets version 20261003-11. Base PostgreSQL modifiée : non.
Migration, seed et script serveur : aucun pour ce correctif.

### 3 octobre 2026 — X de l'aperçu : emplacement neutre

Après persistance signalée, X créé à chaque ouverture dans closePreviewSlot,
avec écouteur direct et SVG définitif non remplacé par Lucide. Cible 36px,
icône sans interception des événements. Trois tests passent dont remontage
et fermeture répétés. Vérification réelle dans navigateur encore requise.
Assets JS/CSS/router/shell version 20261003-10.
Base PostgreSQL modifiée : non. Aucune migration ni seed pour ce correctif.

### 3 octobre 2026 — Fermeture de l'aperçu Rapports

X et Fermer recréés comme boutons natifs avec écouteur direct, type button
et exclusion du chargeur automatique. Même patron pour Aperçu et Générer.
Règle hidden prioritaire pour garantir le masquage de l'overlay.
Test automatisé : trois ouvertures/fermetures successives, clic depuis icône.
10 tests rapports passent ; contrôle interactif navigateur restant à confirmer.
Cache rapports JS/CSS et chaîne router/shell : 20261003-9.
Base PostgreSQL modifiée : non. Migration/seed/script : aucun pour ce lot.

### 3 octobre 2026 — Catalogue rapports : périmètre par défaut

Toutes les périodes est désormais le choix par défaut, au lieu du mois en
cours qui excluait les enregistrements plus anciens. Sans bornes, les lignes
non datées sont conservées ; une période explicite reste strictement filtrée.
Configurations déjà sauvegardées conservées, bilans officiels BNEC inchangés.
Libellé de période harmonisé dans aperçu, CSV, Excel et PDF.
8 tests frontend passent ; test interactif des boutons encore à confirmer.
Base PostgreSQL modifiée : non. Migration/seed : aucun. Assets version 20261003-8.

### 3 octobre 2026 — Champs des modals Résoudre / Rapport de veille

Classe operational-field appliquée aux champs ; styles explicitement limités
aux deux modals themed-business-dialog (bordures, espacements, focus,
thème sombre et case de clôture distincte). Scroll au zoom conservé.
Identifiants et gestionnaires de boutons inchangés ; aucun changement métier.
Tests statiques des champs et identifiants : contrôle navigateur encore requis.
Base PostgreSQL modifiée : non. Migration et seed : aucun pour ce correctif.
Déployer les templates et business-dialogs.css version 20261003-7.

## 3 octobre 2026 — Boutons du formulaire Entreprise

Correction création/modification : suppression de la double capture de
l'ancien DOM après retrait d'une ligne ; boutons natifs neufs avec écouteurs
directs pour étapes, navigation, enregistrement et vérifications d'identifiant.
Corbeilles contacts/sites/offres couvertes par les tests automatisés.
Base PostgreSQL modifiée pour ce correctif : non. Aucun script ni seed.
Contrôle réel des clics dans le navigateur restant à confirmer.

## Mise à jour du 3 octobre 2026 — Genre et rapports

Modals Résoudre une alerte / Générer un rapport de veille harmonisés. Genre
facultatif des contacts et filtres genre/adresse du catalogue Entreprises et
Certifications ajoutés. **Migration serveur requise : l7b1d5f9a304**, déjà
appliquée localement. Consulter la feuille Hébergement avant déploiement.

## Extension du 3 octobre 2026 (20261003-3)

Le rafraîchissement couvre désormais seize écrans métier avec horodatage à la
seconde. La suspension après saisie dans un modal et la registration tardive
d'une page quittée sont corrigées ; l'audit d'actualisation précise le périmètre
restant. Aucune migration/seed, aucun changement PostgreSQL.

## Actualisation automatique — 3 octobre 2026

Le minuteur recharge désormais les données des registres raccordés sans
renaviguer ni réinitialiser la page. La feuille Frontend précise le périmètre,
les protections des saisies/modals et les tests. Aucun changement PostgreSQL,
aucune migration, aucun seed pour ce correctif.

**Dernière consolidation :** 11 août 2026

Ce répertoire constitue le point d'entrée unique de la continuité du projet.

## Documents canoniques à maintenir

1. `FEUILLE_DE_ROUTE_HEBERGEMENT_SNGSC.md` : installation, mise à jour,
   migrations, seeds, exploitation et dépannage du serveur Linux.
   Pour transférer la base, les comptes et les fichiers vers un autre serveur,
   utiliser `GUIDE_TRANSFERT_NOUVEAU_SERVEUR_SNGSC.md` ; il distingue la
   restauration complète d'une installation vierge.
2. `FEUILLE_DE_ROUTE_BACKEND_HAUQE_CERTIF.md` : état réel du backend,
   décisions techniques, services et endpoints.
3. `FEUILLE_DE_ROUTE_FRONTEND.md` : état réel des pages, parcours, correctifs
   et recette de l'interface.
4. `PLAN_ETAPES_FRONTEND.md` : vue synthétique des étapes fonctionnelles.
5. `PLAN_DEVELOPPEMENT_BACKEND.md` : plan directeur historique du backend.
6. `PLAN_GUIDE_UTILISATION_GLOBAL.md` : plan validé du futur manuel Word
   imprimable destiné aux utilisateurs du système.

## Archives de continuité

- `FEUILLE_DE_ROUTE_FRONTEND_v2.md`
- `FEUILLE_DE_ROUTE_BACKEND_HAUQE_CERTIF_v2.md`

Les fichiers suffixés `_v2` sont des instantanés historiques. Ils ne doivent
pas remplacer les trois documents canoniques lors d'un déploiement.

## Règle de mise à jour

Toute modification qui touche une table, une permission, une variable
d'environnement, une tâche serveur ou un parcours frontend doit être reportée
dans les feuilles Backend, Frontend et Hébergement avant mise en production.

## Point de reprise - 11 août 2026

Les correctifs Collecte, situations déclarées, préférences de rafraîchissement
et affichage de l'avatar sur l'écran de verrouillage sont réalisés dans le
code local. Une version rédigée, professionnelle et modifiable du guide global
d'utilisation est disponible dans
`output/docx/Guide_global_utilisation_SNGSC_HAUQE_v2.docx`, sans captures
d'écran. La prochaine action documentaire est sa relecture métier et
l'insertion des captures nettoyées par la HAUQE, selon
`PLAN_GUIDE_UTILISATION_GLOBAL.md`.

Les correctifs de sécurité d'authentification sont réalisés localement et
documentés dans les feuilles Frontend et Backend :

- purge des caches utilisateur/profil avec le token afin d'éviter la boucle
  connexion → tableau de bord → connexion après expiration ou révocation ;
- exclusion des formulaires de connexion, MFA, mot de passe oublié et session
  sécurisée du chargeur automatique afin qu'un échec ne bloque plus le bouton ;
- changement de mot de passe : toutes les sessions, y compris la session
  courante, sont révoquées ; l'utilisateur est renvoyé vers la connexion ;
- notification interne et courriel de sécurité HAUQE générés sans jamais
  transmettre le mot de passe en clair ;
- signature de courriel institutionnelle configurable via `HAUQE_CONTACT_*`
  dans `.env`.

Recette à exécuter avant déploiement : tester un mot de passe erroné, un code
MFA erroné, un code de session sécurisée erroné, l'expiration d'un token et un
changement de mot de passe suivi d'une reconnexion avec le nouveau mot de
passe.
