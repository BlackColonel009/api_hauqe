# Feuille de route du frontend HAUQE Certif

## Informations générales

| Élément | Description |
|---|---|
| Projet | Système national de gestion et de suivi des certifications |
| Bénéficiaire | Haute Autorité de la Qualité et de l'Environnement (HAUQE) |
| Programme | ProComp — GFA Consulting Group |
| Frontend | HTML, CSS, Bootstrap, JavaScript et bibliothèques spécialisées |
| API prévue | FastAPI — Python |
| Base de données prévue | PostgreSQL |
| Principe de réalisation | Maquettes validées, frontend avec données simulées, puis raccordement progressif à l'API |
| Dernière mise à jour | 1er octobre 2026 — badge d'attente INFC du classement SNCC corrigé |

### Classement SNCC — badge d'attente INFC (01/10/2026)

- La règle générique `.scoring-entity-row > span` dimensionnait toutes les balises `span` à 36 × 36 px, y compris le badge « En attente INFC ». Le texte débordait sous la ligne. Réserver la boîte carrée au premier `span` (icône de certification) et laisser au badge sa largeur naturelle.
- Sur petit écran, le badge passe sur une ligne complète de la fiche ; aucun libellé ne doit être coupé ni sortir du cadre. Recette : `tests/frontend/sncc_ineligible_layout_smoke.cjs` à 1490/800/390 px et zoom 200 %.
- Changement de présentation uniquement : aucun calcul SNCC, aucune action et aucune donnée modifiés. **Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Alertes — actions de « Mes notifications » (01/10/2026)

- Une ligne de notification affichait quatre enfants dans une grille à trois colonnes : « Marquer lue » tombait dans la première colonne de la ligne suivante et son texte était comprimé. Regrouper « Ouvrir l’alerte » et « Marquer lue » dans une seule zone d’actions, sans rupture du libellé.
- À largeur réduite et au zoom 200 %, placer la zone d’actions sous le contenu de notification, avec retour à la ligne contrôlé et sans débordement horizontal. Préserver le clic dès la première tentative sur « Marquer lue ».
- Recettes : `tests/frontend/notification_actions_layout_smoke.cjs` (géométrie 1490/720/390 px et zoom 200 %) et `tests/frontend/personal_alerts_smoke.cjs` (marquage lu dès le premier clic).
- **Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Rapports et exports — catalogue historique raccordé (01/10/2026)

- Les filtres de période, de zone administrative (entreprises), de statut et de référentiel (certifications) sont alimentés par les données réelles. Les filtres non applicables au modèle choisi sont désactivés, sans options fictives.
- L'aperçu et les téléchargements PDF, Excel compatible et CSV reposent sur les mêmes lignes filtrées. Les cases de contenu déterminent les colonnes présentes ; les identifiants techniques UUID ne sont jamais exposés comme colonnes métier.
- « Enregistrer la configuration » appelle `POST /api/v1/reports/configurations` et n'affiche le succès qu'après confirmation du serveur. « Mes rapports enregistrés » relit les préférences personnelles avec `GET /api/v1/reports/configurations` et restaure filtres, sections et format.
- Les registres des certifications et organismes exposent désormais leur date d'enregistrement pour appliquer le filtre de période, sans altérer les données existantes.
- Recette `tests/frontend/bnec_reports_smoke.cjs` : aperçu et CSV concordants sur période/zone/statut/référentiel, colonnes sélectionnées, configuration enregistrée puis rechargée, boutons dès le premier clic.
- **Base PostgreSQL : écritures dans `rapports_generes` et journal d'audit lors de l'enregistrement d'une configuration ; schéma inchangé, migration aucune, seed aucun.**

### Menu mobile — ouverture/fermeture involontaire (28 septembre 2026)

- Ne jamais basculer la sidebar à la fois sur `pointerdown` et sur `click` avec une fenêtre arbitraire de 650 ms : selon le navigateur tactile, le clic retardé inverse aussitôt l'ouverture.
- Un seul gestionnaire `click` ouvre/ferme le menu. Les actualisations silencieuses (`hauqe:page-ready`) ne ferment plus la sidebar ; une vraie navigation (`hashchange`, lien du menu), le fond, la croix ou Échap la ferment. Le routeur ne retire plus directement la classe `.open` lors d'une actualisation.
- Recette `tests/frontend/mobile_sidebar_smoke.cjs` en émulation tactile : appui, clic retardé, actualisation silencieuse et fermeture volontaire. Modification frontend seulement ; aucune migration ni seed.

### Échéances — registre consolidé (28 septembre 2026)

- Le statut `EN_RETARD` affiché dans « Toutes les échéances enregistrées » utilise une pastille rouge en thèmes clair et sombre ; `TERMINEE` reste vert. Vérifié par `tests/frontend/deadline_overdue_status_smoke.cjs` sur les styles calculés du navigateur.

### Profil — courriels du système par agent (28 septembre 2026)

- Dans l'onglet Notifications, le bloc « Courriels du système par agent » apparaît uniquement pour `ADMIN_HAUQE` ou `ADMIN_BNEC`. Tous les comptes sont listés par défaut comme destinataires ; décocher une ligne la retire et désactive ses courriels fonctionnels. Le sélecteur propose alors les comptes retirés, avec un bouton pour les réajouter. Chaque action est enregistrée immédiatement via l'API, sans modifier les comptes.
- Ce réglage n'affecte pas les notifications internes ni les messages de sécurité du compte. Le serveur revalide le rôle administrateur ; masquer le bloc ne constitue pas une autorisation.
- Recette isolée `tests/frontend/admin_system_email_profile_smoke.cjs` : tous les comptes visibles par défaut, retrait et réajout dès le premier clic, absence du bloc pour un non-administrateur et absence de débordement à largeur réduite ; API simulée, aucune donnée réelle modifiée.
- Correctif de visibilité : renouveler toute la chaîne de cache `index.html` → `app-shell.js` → `router.js` → `profil.js` lorsqu'une nouvelle rubrique du profil est ajoutée ; ne pas se limiter à la version de `profil.js`.

### Navigation et communication du parcours — 27 septembre 2026

- La page Alertes ouvre d'abord « Mes alertes », filtrées **côté serveur** par destinataire IN_APP ou responsable. Le registre général n'est proposé qu'aux comptes ayant `ALERTES.LIRE` ; `NOTIFICATIONS.LIRE` ne donne jamais accès à ce registre.
- La cloche et le badge latéral se fondent sur les notifications et alertes personnelles. Les lignes EMAIL de transport ne comptent plus comme des notifications non lues dans l'interface.
- La CVC reçoit l'accès opérationnel à la classification entreprise, à l'INFC et au SNCC, sans droit d'administration des modèles publiés.
- Les boutons « Mes alertes » / « Registre général » ont des écouteurs directs. Recette isolée `tests/frontend/personal_alerts_smoke.cjs` : premier clic, visibilité selon permissions et largeur 850/640 px contrôlés avec API simulée. Aucune donnée réelle écrite.
- À confirmer en recette authentifiée : les alertes et courriels générés lors des six transitions métier, avec deux comptes de rôles différents.

### Modals Validation et INFC — 27 septembre 2026

- « Demander une correction » et « Valider le résultat calculé » reprennent le thème des modals Échéances : en-tête illustré, contexte métier lisible, bloc de saisie, pied d’actions distinct.
- Le contexte affiché est dynamique (dossier pour la correction ; entreprise, certification, score et niveau pour l’INFC). Aucun UUID brut n’est présenté.
- Les erreurs de soumission apparaissent dans le modal, sans perte de saisie ; les boutons continuent d’utiliser leurs écouteurs directs au premier clic.
- Le bloc de saisie défile au zoom ; à très faible hauteur, le formulaire entier reste défilable. Contrôle visuel local réalisé avec les vrais fragments HTML à 1280 × 720, 850 × 480, 640 × 360 et 320 × 200, en thème clair et sombre : ouverture/fermeture au premier clic, aucun débordement horizontal, actions accessibles après défilement. Le parcours métier authentifié et l’enregistrement réel restent à vérifier sur une session de test.
- Modification frontend uniquement : aucune migration PostgreSQL, aucun seed.

### Échéances — navigation du calendrier sans « bouton latence » (29/09/2026)

- Les boutons précédent, Aujourd'hui et suivant avaient déjà un écouteur direct, mais `renderCalendar()` les supprimait et les recréait à chaque chargement ; une navigation pouvait déclencher deux rendus successifs et remplacer le bouton pendant le clic suivant.
- Le bouton est maintenant créé une seule fois dans son emplacement neutre après chargement de la vue ; les rendus ultérieurs conservent **la même instance et le même écouteur**, et ne modifient que l'état `disabled` des commandes de zoom. Classe CSS locale avec `pointer-events: auto` et SVG non interactif.
- Test navigateur isolé : trois commandes de navigation au premier clic, identité DOM inchangée après plusieurs rendus et état des commandes de zoom actualisé. La recette de la page authentifiée reste à faire lors de l'essai utilisateur.
- Frontend uniquement ; aucune migration PostgreSQL ni seed. Changer les versions de cache de `echeances.js`, du routeur et de `echeances.css` lors du déploiement.

## Règle permanente et non contournable pour toute mise à jour frontend

Cette règle s'applique à **chaque page ou bloc modifié**, même si la demande
porte sur un simple libellé, un style ou un correctif backend qui change le
comportement visible. Elle fait partie des critères de fin de tâche.

1. **Contrôler les boutons de la page concernée contre le « bouton latence ».**
   Tester au premier clic les actions déjà présentes et celles ajoutées ou
   recréées : navigation, ouverture et fermeture de modal, menus déroulants,
   ajout et retrait de ligne, enregistrement, validation et publication.
   Répéter après un nouveau rendu, une recherche ou un changement d'onglet.
   Les boutons issus d'un rendu dynamique reçoivent immédiatement un écouteur
   direct sur le bouton affiché, suivant la correction validée dans **Gestion
   des campagnes**. Ne pas utiliser le clonage d'un bouton au clic ni un
   `MutationObserver` global comme substitut à ce contrôle.
2. **Vérifier tout modal créé ou touché en situation réelle.** Son contenu
   doit respecter le thème HAUQE adopté pour les modals d'**Échéances** :
   en-tête, hiérarchie des informations, espaces, actions et messages d'erreur
   lisibles. Contrôler son ouverture, ses boutons, sa fermeture autorisée et
   la conservation des saisies après erreur.
3. **Vérifier le zoom et le défilement.** Contrôler au minimum les zooms
   navigateur 100 %, 150 % et 200 %, puis un affichage étroit ou un zoom plus
   fort si le formulaire le nécessite. Aucun champ, message, bouton ou pied
   de modal ne doit être coupé. Le bloc de saisie doit pouvoir défiler
   verticalement, y compris lorsque le clavier ou le zoom réduit la hauteur
   disponible. Vérifier aussi le thème sombre lorsque la page le prend en
   charge.
4. **Ne pas déclarer la correction terminée sur la seule base du code.**
   Vérifier le rendu et l'interaction sur la page concernée. Si l'accès à une
   session connectée empêche cette vérification, l'indiquer explicitement
   dans le rapport comme point non vérifié, avec le parcours exact à tester.

Cette règle prévaut sur les descriptions d'anciennes pages ou de correctifs
ponctuels ci-dessous. Aucune nouvelle livraison frontend ne doit la contourner.

### Contrôle ciblé `/collectes/nouveau` — 27 septembre 2026

- Corrigé : les actions fixes de l'assistant sont branchées avant le chargement
  asynchrone, afin que le premier clic fonctionne dès que la page est visible.
- Corrigé : les formulaires de précréation écoutent leurs propres soumissions ;
  les anciennes visites ne laissent plus d'écouteurs globaux susceptibles de
  créer plusieurs requêtes pour un seul clic. Une soumission en cours est
  protégée contre le double clic.
- Corrigé : la zone créée reste sélectionnée après réaffichage. Les erreurs de
  précréation sont présentées dans le modal ouvert, sans perdre les saisies.
- Ajusté : les cartes de recherche d'organisme et de preuve de certification
  occupent toute la largeur utile ; les lignes d'offres/certifications se
  réorganisent lorsque la largeur disponible diminue. Les actions d'en-tête
  se répartissent sans couper leurs libellés. Les actions non permises
  restent réellement masquées ; une nouvelle collecte n'est plus titrée
  « Modification » avant la création de sa fiche.
- Vérification automatisée avec API simulée : premier clic, ajout et retrait
  d'offres et certifications, ouverture/fermeture des modals, soumission unique,
  erreur affichée dans le modal et largeurs équivalentes aux zooms 100, 150 et
  200 %. Aucune écriture dans la base réelle. Le parcours métier connecté
  complet et le zoom manuel dans le navigateur de l'utilisateur restent à
  confirmer lors de la recette.

## Architecture d'intégration retenue

- FastAPI sert le point d'entrée et les vues frontend ;
- Jinja2 gère le template principal ;
- `app/templates/index.html` contient une seule sidebar et une seule navbar ;
- le routeur JavaScript change uniquement le contenu central ;
- les URL frontend utilisent actuellement des routes de type `#/module` ;
- `app/static/js/core/api.js` centralise les futurs appels à l'API ;
- chaque nouvelle page sera progressivement convertie en module autonome ;
- les anciennes pages complètes sont temporairement conservées dans `app/templates/legacy` comme références de migration.

## Référentiel documentaire désormais pris en compte

La feuille de route a été rapprochée du guide méthodologique complet, des procédures opérationnelles, des fiches de collecte et de contrôle, de la note de cadrage de la Cellule de Veille des Certifications, des documents INFC et SNCC, des deux tableaux de bord ainsi que du document de validation des règles métiers.

Les exigences sont classées selon quatre niveaux afin d'éviter de transformer une proposition non approuvée en règle définitive :

## Mise à jour frontend du 3 au 6 août 2026

- le profil permet d'activer, désactiver et paramétrer l'actualisation
  automatique, tout en conservant le bouton « Actualiser » ;
- le formulaire Collecte utilise explicitement
  `window.history.replaceState`, sans collision avec l'historique métier ;
- « Situation actuelle déclarée » accepte aussi « Expirée » et
  « Audit initial » ;
- les justificatifs sélectionnés sont visibles avant envoi avec leur nom,
  leur taille et une action de retrait ;
- l'écran de verrouillage reprend la photo de profil chargée dans la navbar
  et revient automatiquement aux initiales si l'image est absente ou invalide ;
- la configuration de production doit utiliser
  `apiBaseUrl: window.location.origin` et ne contenir aucune URL locale ;
- après déploiement d'une nouvelle version statique, effectuer un
  rechargement forcé du navigateur afin d'écarter l'ancien cache.

### Point de reprise

Le guide opérationnel V2 est disponible dans
`output/docx/Guide_global_utilisation_SNGSC_HAUQE_v2.docx`, avec des cadres
de captures à compléter. Les derniers correctifs frontend sécurisent le retour
à la connexion après expiration, un échec MFA ou un code de session erroné,
et imposent une reconnexion après changement de mot de passe. La prochaine
action est de poursuivre les corrections fonctionnelles demandées par la
recette utilisateur, puis de tester ces parcours après un rechargement forcé
du navigateur.

- **Prescrit par les procédures et outils HAUQE** : à intégrer dans la conception fonctionnelle ;
- **Documenté mais paramétrable** : à implémenter sous forme de référentiel ou de règle versionnée ;
- **Contradictoire entre les documents** : à soumettre à l'arbitrage de la HAUQE avant codage définitif ;
- **Proposé et en attente de validation** : à conserver comme maquette ou paramètre désactivé.

### Corrections structurantes à apporter au frontend

1. Séparer les étapes **Collecte**, **Vérification**, **Contrôle**, **Validation**, **Intégration BNEC**, **Classement SNCC** et **Veille**. La validation ne doit plus être présentée comme une simple recevabilité ouvrant directement le contrôle.
2. Séparer les trois systèmes de notation et de décision :
   - la grille FUCCS **versionnée et chargée depuis l'API** ; la version frontend active comporte actuellement **24 critères visibles**, mais ni le nombre de critères ni le score maximal global ne doivent être codés en dur ;
   - l'**INFC sur 100 points**, composé de six domaines pondérés : authenticité 20, validité 20, maintien 20, maîtrise documentaire 15, traçabilité et maîtrise opérationnelle 15, suivi et renouvellement 10 ;
   - le **SNCC**, qui combine classe de conformité, statut administratif et niveau de risque.
3. Remplacer les seuls horizons 30, 60 et 90 jours par le moteur validé **180 jours, 90 jours, 30 jours et expiration**. Une information complémentaire à 12 mois reste paramétrable et désactivée tant qu'elle n'est pas confirmée.
4. Créer les cinq niveaux de pilotage : **opérationnel**, **tactique**, **stratégique**, **annuel** et **public**. Le tableau de bord public ne doit afficher que des données agrégées et non confidentielles.
5. Introduire explicitement la **Cellule de Veille des Certifications (CVC)**, rattachée à la Direction Technique, avec ses files de travail, relances, notes mensuelles et rapports trimestriels.
6. Ajouter le suivi des demandes officielles adressées aux organismes certificateurs et aux entreprises : canal, destinataire, date d'envoi, délai attendu, réponse reçue, pièces et relances.
7. Ajouter le cycle de mise à jour de la BNEC : demande, justificatifs, vérification, validation technique, saisie, contrôle qualité, sauvegarde, recalcul des indicateurs et historisation.
8. Ajouter les fonctions documentaires : indexation, type de document, version, statut, auteur, source, date, checksum, historique, archivage et accès restreint.
9. Ajouter les décisions et plans d'action : constats, risques, recommandations, responsable, délai, ressources, indicateur, état d'exécution et évaluation de l'effet.
10. Aligner les rôles sur la gouvernance documentée : Président, Direction Technique, Point focal BNEC, Administrateur fonctionnel, Administrateur système, Agent enquêteur, Agent vérificateur, Cellule de veille et profil de consultation/audit.

## Légende des statuts

- **Terminée** : page créée, responsive et vérifiée avec des données simulées.
- **En cours** : page en cours de conception ou de développement.
- **Planifiée** : page identifiée, mais pas encore créée.
- **À valider** : page créée et soumise à la validation fonctionnelle ou visuelle.

## Avancement général

| N° | Page | Module | Statut |
|---:|---|---|---|
| 01 | `index.html` | Pilotage | Terminée — à valider |
| 02 | `alertes.html` | Pilotage | Terminée — à valider |
| 03 | `echeances.html` | Pilotage | Terminée — à valider |
| 04 | `entreprises.html` | Entreprises | Terminée — à valider |
| 05 | `entreprise-detail.html` | Entreprises | Terminée — à valider |
| 06 | `entreprise-form.html` | Entreprises | Terminée — à valider |
| 07 | `certifications.html` | Certifications | Terminée — à valider |
| 08 | `certification-detail.html` | Certifications | Terminée — à valider |
| 09 | `certification-form.html` | Certifications | Terminée — à valider |
| 10 | `organismes.html` | Organismes certificateurs | Terminée — à valider |
| 11 | `organisme-detail.html` | Organismes certificateurs | Terminée — à valider |
| 11A | `organisme-form.html` | Organismes certificateurs | Terminée — à valider |
| 12 | `collectes.html` | Collecte | Terminée — à valider |
| 13 | `collecte-form.html` | Collecte | Terminée — à valider |
| 14 | `validations.html` | Contrôle | Terminée — à valider |
| 15 | `controle.html` | Contrôle | Terminée — à valider |
| 16 | `scoring.html` | Analyse | Terminée — à valider |
| 17 | `rapports.html` | Reporting | Terminée — à valider |
| 18 | `utilisateurs.html` | Administration | Terminée — à valider |
| 19 | `referentiels.html` | Administration | Terminée — à valider |
| 20 | `regles-codification.html` | Administration | Terminée — à valider |
| 21 | `journal-audit.html` | Administration | Terminée — à valider |
| 22 | `connexion.html` | Authentification | Raccordement API en cours |
| 23 | `mot-de-passe-oublie.html` | Authentification | Terminée — à valider |
| 24 | `profil.html` | Compte utilisateur | Raccordement API en cours |

---

## 01 — `index.html`

Le shell affiche désormais le chargement personnalisé **Option A** commun à toutes les routes : un SVG dessine progressivement la lettre « H » dans un cercle institutionnel, avec une orbite dorée et une feuille verte. Le routeur maintient l'indicateur au moins 420 ms pour éviter un clignotement trop bref, puis le masque lorsque la page et son script sont prêts. L'animation est neutralisée lorsque `prefers-reduced-motion` est activé.

Les cartes d'indicateurs, actions prioritaires, échéance suivante et lignes de certifications récentes sont navigables. Les boutons à trois points ouvrent un menu contextuel vers le certificat, l'entreprise ou l'échéance. Export, nouvelle collecte, filtres, registre et centre des alertes produisent désormais une action visible.

### Statut

**Terminée — à valider**

### Rôle de la page

Fournir une vue nationale synthétique de la situation des entreprises, certifications, contrôles et échéances. Cette page constitue le point d'entrée principal après l'authentification.

### Profils concernés

- Administrateur HAUQE
- Décideur ou responsable HAUQE
- Agent HAUQE, avec indicateurs adaptés à ses droits
- Consultant externe, en lecture seule selon validation

### Fonctionnalités illustrées

- indicateurs du nombre d'entreprises enregistrées ;
- nombre de certifications actives ;
- identification des entreprises à risque ;
- nombre de contrôles à planifier ;
- répartition des certifications par statut ;
- suivi paramétrable des échéances officielles à 12 mois, 6 mois, 3 mois, 1 mois et à expiration ;
- accès différencié aux tableaux de bord opérationnel, tactique, stratégique et annuel selon le profil ;
- affichage de l'INFC national et de ses déclinaisons par région, secteur, référentiel et organisme certificateur ;
- taux de maintien, taux de renouvellement et indicateurs de performance de la HAUQE ;
- évolution de l'activité des certifications ;
- affichage des actions prioritaires ;
- liste des certifications récemment mises à jour ;
- filtres par période, région et secteur ;
- accès aux exports ;
- accès à une nouvelle collecte ;
- navigation générale dans les modules ;
- présentation responsive.

### Fichiers associés

- `index.html`
- `assets/css/styles.css`
- `assets/js/app.js`
- `assets/js/mock-data.js`

### Données API attendues ultérieurement

- statistiques consolidées ;
- répartition des statuts ;
- séries temporelles ;
- échéances prioritaires ;
- dernières modifications ;
- filtres et périmètre autorisé de l'utilisateur.

---

## 02 — `alertes.html`

### Statut

**Terminée — à valider**

### Rôle de la page

Centraliser les alertes générées par le système, permettre leur priorisation, leur affectation et le suivi de leur résolution.

### Profils concernés

- Administrateur HAUQE
- Responsable du suivi
- Agent HAUQE
- Contrôleur HAUQE
- Consultant externe en consultation limitée

### Fonctionnalités illustrées

- indicateurs du nombre total d'alertes ;
- classement en alertes critiques, à surveiller et informatives ;
- recherche par entreprise, certificat, référence ou contenu ;
- filtres par type d'alerte ;
- filtres par état ;
- filtres par responsable ;
- sélection multiple des alertes ;
- distinction entre alertes lues et non lues ;
- états « Nouvelle », « En cours » et « Résolue » ;
- affectation d'une alerte à un responsable ;
- passage progressif d'une alerte vers sa résolution ;
- panneau détaillé de l'alerte sélectionnée ;
- affichage de l'action recommandée ;
- consultation de l'historique récent ;
- marquage global des alertes comme lues ;
- lien vers le suivi des échéances ;
- présentation responsive.

### Fichiers associés

- `alertes.html`
- `assets/css/alertes.css`
- `assets/js/alertes.js`
- `assets/css/styles.css`

### Données API attendues ultérieurement

- alertes générées automatiquement ;
- priorités et catégories ;
- responsables et affectations ;
- historique des changements d'état ;
- actions et commentaires ;
- règles ayant déclenché chaque alerte.
- source de l'événement, échéance de traitement, relances, destinataires externes et preuves de notification ;
- historique de vérification, réponse de l'entreprise ou de l'organisme certificateur et décision de clôture.

---

## 03 — `echeances.html`

### Statut

**Terminée — à valider**

### Rôle de la page

Planifier et suivre dans le temps les événements liés aux certifications et aux opérations de contrôle de la HAUQE.

### Profils concernés

- Administrateur HAUQE
- Responsable du suivi
- Agent HAUQE
- Contrôleur HAUQE
- Décideur HAUQE en consultation

### Fonctionnalités illustrées

- seuils métier 180 jours, 90 jours, 30 jours puis expiration ; d'autres horizons peuvent rester de simples vues calendaires, pas des règles d'alerte ;
- échéances en retard ;
- filtres par période, type, responsable et région ;
- navigation mensuelle ;
- retour rapide au mois courant ;
- vues calendrier et liste ;
- expirations de certifications ;
- audits de surveillance ;
- renouvellements ;
- contrôles HAUQE ;
- légende des différents types d'événements ;
- prochaines échéances prioritaires ;
- charge de travail par responsable ;
- identification des échéances non affectées ;
- fenêtre de planification d'une nouvelle échéance ;
- lien avec le centre des alertes ;
- export des échéances ;
- présentation responsive.

### Fichiers associés

- `echeances.html`
- `assets/css/echeances.css`
- `assets/js/echeances.js`
- `assets/css/styles.css`

### Données API attendues ultérieurement

- événements et échéances calculés ;
- dates des certificats, audits et contrôles ;
- responsables affectés ;
- régions et entreprises concernées ;
- état d'avancement ;
- rappels et alertes liés à chaque événement.

---

## 04 — `entreprises.html`

### Statut

**Terminée — à valider**

### Rôle de la page

Présenter le registre national des entreprises et faire apparaître rapidement leur situation de certification et de conformité.

### Profils concernés

- Administrateur HAUQE
- Agent et contrôleur HAUQE
- Responsable du suivi
- Consultant externe en lecture seule

### Fonctionnalités illustrées

- indicateurs des entreprises enregistrées, certifiées actives, à risque et non conformes ;
- recherche par nom, RCCM, NIF ou responsable ;
- filtres par statut, région et secteur ;
- affichage des identifiants, localisations et certifications ;
- prochaine échéance et score de conformité ;
- statuts automatiques ;
- vues tableau et cartes ;
- sélection multiple, import, export et archivage ;
- pagination et présentation responsive.

### Fichiers associés

- `entreprises.html`
- `assets/css/entreprises.css`
- `assets/js/entreprises.js`
- `assets/css/styles.css`

### Données API attendues ultérieurement

- registre paginé des entreprises ;
- identifiants, localisations, secteurs et responsables ;
- certifications, échéances, scores et statuts calculés ;
- opérations d'import, d'export et d'archivage.

---

## 05 — `entreprise-detail.html`

### Statut

**Terminée — à valider**

### Rôle de la page

Présenter dans un dossier unique toutes les informations administratives, certifications, contrôles, scores, documents et opérations relatives à une entreprise.

### Profils concernés

- Administrateur HAUQE
- Agent et contrôleur HAUQE
- Responsable du suivi
- Décideur HAUQE
- Consultant externe en lecture seule

### Fonctionnalités illustrées

- identité, RCCM, NIF, activité et localisation ;
- contacts et responsables ;
- indicateurs des certifications, scores, échéances et contrôles ;
- onglets vue d'ensemble, certifications, contrôles, documents et historique ;
- score HAUQE détaillé sur 56 ;
- décision et recommandations de surveillance ;
- téléchargement et ajout de documents ;
- export et modification du dossier ;
- navigation dynamique depuis le registre ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/entreprise-detail.html`
- `app/static/css/entreprise-detail.css`
- `app/static/js/entreprise-detail.js`

### Données API attendues ultérieurement

- dossier complet de l'entreprise ;
- certifications et échéances ;
- contrôles, critères et scores ;
- documents et pièces justificatives ;
- chronologie issue du journal d'audit.

---

## 06 — `entreprise-form.html`

### Statut

**Terminée — à valider**

### Rôle de la page

Créer ou modifier une entreprise au moyen d'un parcours progressif et contrôlé.

### Profils concernés

- Administrateur HAUQE
- Agent HAUQE autorisé à la saisie

### Fonctionnalités illustrées

- création et modification ;
- cinq étapes : identification, localisation, activités, contacts et vérification ;
- champs RCCM et NIF ;
- contrôle des champs obligatoires ;
- détection simulée des doublons ;
- ajout dynamique de sites, produits et contacts ;
- sauvegarde du brouillon côté serveur ;
- bouton **Réinitialiser le brouillon**, uniquement dans le formulaire et
  uniquement pour une fiche courante en statut `BROUILLON` ;
- réinitialisation des saisies de mission, entreprise, offres, certifications
  et observations ; la campagne, la zone et les affectations restent les
  éléments structurels initiaux de la mission ;
- après la réinitialisation, l'agent habilité peut sélectionner une autre
  campagne et une autre zone : la même mission brouillon est déplacée sans
  créer de doublon ;
- les pièces déjà déposées disparaissent du formulaire car elles sont
  désactivées et restent traçables dans la gestion documentaire ;
- récapitulatif avant enregistrement ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/entreprise-form.html`
- `app/static/css/entreprise-form.css`
- `app/static/js/entreprise-form.js`

### Données API attendues ultérieurement

- création et modification des entreprises ;
- référentiels territoriaux et sectoriels ;
- recherche de doublons RCCM, NIF et nom/localité ;
- gestion des brouillons, sites, produits et contacts.

---

## 07 — `certifications.html`

### Statut

**Terminée — à valider**

### Rôle de la page

Présenter le registre national de tous les certificats et faciliter leur recherche, leur vérification et leur suivi.

### Profils concernés

- Administrateur HAUQE
- Agent et contrôleur HAUQE
- Responsable du suivi
- Consultant externe en lecture seule

### Fonctionnalités illustrées

- indicateurs des certificats valides, à surveiller, expirés et à vérifier ;
- suivi des renouvellements ;
- recherche par numéro, code, entreprise, norme ou organisme ;
- filtres par statut, référentiel et échéance ;
- numéro original et code national ;
- entreprise titulaire et organisme certificateur ;
- portée, validité et état de vérification ;
- sélection multiple, export et pagination ;
- accès au futur dossier détaillé ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/certifications.html`
- `app/static/css/certifications.css`
- `app/static/js/certifications.js`

### Données API attendues ultérieurement

- registre paginé des certifications ;
- entreprises, organismes, référentiels et portées ;
- statuts calculés, vérifications et échéances ;
- exports et actions groupées.

---

## 08 — `certification-detail.html`

### Statut

**Terminée — à valider**

### Rôle de la page

Réunir dans un dossier unique toutes les informations, preuves, vérifications et opérations relatives à un certificat.

### Profils concernés

- Administrateur HAUQE
- Agent et contrôleur HAUQE
- Responsable du suivi
- Consultant externe en lecture seule

### Fonctionnalités illustrées

- numéro original et code national ;
- référentiel, portée, titulaire et organisme certificateur ;
- dates de délivrance, entrée en vigueur et expiration ;
- alertes de renouvellement ;
- audits initiaux, de surveillance et de renouvellement ;
- contrôle de l'authenticité ;
- pièces justificatives ;
- historique des statuts ;
- export et modification ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/certification-detail.html`
- `app/static/css/certification-detail.css`
- `app/static/js/certification-detail.js`

### Données API attendues ultérieurement

- certificat, titulaire, organisme et accréditation ;
- audits et renouvellements ;
- vérifications documentaires et d'authenticité ;
- documents et historique des statuts.

---

## 09 — `certification-form.html`

### Statut

**Terminée — à valider**

### Rôle de la page

Créer ou modifier un certificat au moyen d'un parcours guidé et contrôlé.

### Profils concernés

- Administrateur HAUQE
- Agent HAUQE autorisé à la saisie
- Contrôleur HAUQE pour la vérification

### Fonctionnalités illustrées

- sélection de l'entreprise titulaire et du référentiel ;
- numéro original distinct du code national ;
- organisme certificateur et accréditation ;
- portée, produits, statut et dates ;
- contrôle de cohérence des dates ;
- documents justificatifs et source de vérification ;
- sauvegarde en brouillon ;
- récapitulatif avant enregistrement ;
- modes création et modification ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/certification-form.html`
- `app/static/js/certification-form.js`
- `app/static/css/entreprise-form.css`

### Données API attendues ultérieurement

- création et modification des certificats ;
- entreprises, référentiels, organismes et accréditations ;
- validation des dates et détection des doublons ;
- téléversement des documents et gestion des brouillons.

---

## 10 — `organismes.html`

### Statut

**Terminée — à valider**

### Rôle de la page

Présenter l'annuaire national des organismes certificateurs et leur situation de reconnaissance.

### Profils concernés

- Administrateur, agent et contrôleur HAUQE
- Responsable du suivi
- Consultant externe en lecture seule

### Fonctionnalités illustrées

- indicateurs des organismes reconnus, à vérifier et suspendus ;
- recherche et filtres par statut, pays et référentiel ;
- organismes d'accréditation et domaines couverts ;
- nombre de certificats délivrés ;
- dernière vérification ;
- export et accès au dossier détaillé ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/organismes.html`
- `app/static/js/organismes.js`
- styles partagés du registre des certifications.

### Données API attendues ultérieurement

- annuaire des organismes ;
- accréditations, référentiels, statuts et certificats délivrés.

---

## 11 — `organisme-detail.html`

### Statut

**Terminée — à valider**

### Rôle de la page

Réunir l'identité, les accréditations, les certificats et l'historique de contrôle d'un organisme.

### Profils concernés

- Administrateur, agent et contrôleur HAUQE
- Responsable du suivi
- Consultant externe en lecture seule

### Fonctionnalités illustrées

- identité et coordonnées ;
- statut de reconnaissance ;
- accréditations par référentiel et dates de validité ;
- certificats délivrés ;
- échéances d'accréditation ;
- historique des vérifications ;
- export et modification ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/organisme-detail.html`
- `app/static/js/organisme-detail.js`
- styles partagés des dossiers détaillés.

### Données API attendues ultérieurement

- organisme, accréditations, domaines couverts et statuts ;
- certificats délivrés et journal des vérifications.

---

## 11A — `organisme-form.html`

### Statut

**Terminée — à valider**

### Rôle de la page

Créer ou modifier un organisme, ses coordonnées, ses accréditations et son statut de reconnaissance.

### Profils concernés

- Administrateur HAUQE
- Agent ou contrôleur HAUQE autorisé

### Fonctionnalités illustrées

- modes création et modification ;
- identité, type, pays et présence au Togo ;
- contacts et coordonnées officielles ;
- accréditations multiples par référentiel ;
- dates et numéros d'accréditation ;
- documents et registre officiel ;
- statut et observations HAUQE ;
- brouillon et récapitulatif final ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/organisme-form.html`
- `app/static/js/organisme-form.js`
- `app/static/css/entreprise-form.css`

### Données API attendues ultérieurement

- création et modification des organismes ;
- accréditations, référentiels, documents et statuts ;
- contrôles de doublons et journal des vérifications.

---

## 12 — `collectes.html`

**Terminée — à valider**

### Rôle de la page

Centraliser les missions de collecte de la HAUQE, leur affectation et l'avancement des fiches jusqu'à leur soumission ou validation.

### Profils concernés

- Administrateur HAUQE
- Coordonnateur de campagne
- Agent de collecte
- Contrôleur ou validateur HAUQE

### Fonctionnalités illustrées

- indicateurs des missions, saisies en cours, brouillons, soumissions et corrections ;
- progression globale de la campagne active ;
- recherche par entreprise, zone, agent ou référence ;
- filtres par statut, agent et région ;
- affectation et identification des agents ;
- suivi du taux de complétude de chaque fiche ;
- statuts planifiée, en cours, brouillon, soumise, validée et à corriger ;
- vues liste et cartes ;
- accès à la création et à l'ouverture d'une mission ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/collectes.html`
- `app/static/css/collectes.css`
- `app/static/js/collectes.js`

### Données attendues de l'API

- campagne active et objectifs ;
- missions, entreprises, zones et dates prévues ;
- agents disponibles et affectations ;
- taux de complétude calculé par fiche ;
- statuts, dates de soumission et retours de validation.

### Points à valider

- circuit exact d'affectation et de réaffectation des agents ;
- droits de modification selon le profil et le statut ;
- règles de calcul de la progression globale ;
- format officiel d'export des missions.

---

## 13 — `collecte-form.html`

**Terminée — à valider**

La collecte principale est limitée au noyau nécessaire pour alimenter les dossiers : mission, localisation, identité légale, contacts, activités, produits, marchés, certifications, organismes associés, accréditations, justificatifs et consentement. Les produits, marchés et certifications multiples sont des collections structurées conservées dans le brouillon. Les dates sont contrôlées et une fiche dont les informations primordiales sont incomplètes ne peut pas être soumise. Les critères FUCCS, leur score et la décision restent dans Contrôle/Validation et sont chargés depuis la version de grille publiée.

### Rôle de la page

Permettre à un agent de préparer une mission, saisir sur le terrain la fiche de l'entreprise et transmettre un dossier complet à la HAUQE.

### Profils concernés

- Coordonnateur de campagne
- Agent de collecte
- Contrôleur ou validateur HAUQE en consultation

### Fonctionnalités illustrées

- création et modification d'une collecte ;
- parcours progressif en six étapes ;
- planification, zone et affectation de l'agent ;
- identification de l'entreprise et préfiguration de la recherche dans le registre ;
- ajout dynamique de produits, volumes et marchés ;
- ajout dynamique des certifications et contrôle d'authenticité ;
- dépôt multiple de justificatifs ;
- observations de terrain, consentement et signature ;
- contrôle des champs obligatoires et indicateur de complétude ;
- sauvegarde locale en brouillon ;
- récapitulatif et soumission à la HAUQE ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/collecte-form.html`
- `app/static/css/collecte-form.css`
- `app/static/js/collecte-form.js`

### Données attendues de l'API

- campagnes, zones administratives et agents disponibles ;
- entreprises existantes et mécanisme de détection des doublons ;
- nomenclature des activités, produits, marchés et référentiels ;
- organismes certificateurs et certificats existants ;
- stockage des brouillons, pièces jointes et versions soumises ;
- règles de complétude, verrouillage et retour en correction.

### Points à valider

- champs définitifs transmis par M. Nyanuste ;
- pièces obligatoires selon le type d'entreprise ;
- règles de consentement et de signature ;
- circuit officiel de soumission, correction et verrouillage.

### Gestion des campagnes — accès coordonnateur / administrateur

Depuis `collectes.html`, le bouton **Gérer les campagnes** est visible
uniquement avec `COLLECTE.AFFECTER`. La rubrique dédiée permet de créer,
modifier ou désactiver une campagne et de consulter ses missions liées.

- les agents de collecte sans `COLLECTE.AFFECTER` ne voient pas le bouton ;
- la correction du code, du nom, de l'objet ou des dates est commune à toutes
  les missions rattachées, y compris celles qui possèdent une fiche soumise ;
- une désactivation empêche toute nouvelle sélection dans un formulaire de
  collecte, sans supprimer les missions ni les fiches existantes ;
- la référence et l'objet restent des données propres à chaque mission ; ils
  peuvent être corrigés depuis la liste des missions liées.

Fichiers : `campagnes-collecte.html`, `campagnes-collecte.js` et
`collectes.css`.

---

## 14 — `validations.html`

**Terminée — à valider**

### Rôle de la page

Fournir aux agents habilités une file structurée pour vérifier puis valider les dossiers. La vérification produit un avis technique ; la validation constitue ensuite l'autorisation formelle d'intégration dans la BNEC.

### Profils concernés

- Administrateur HAUQE
- Coordonnateur ou superviseur
- Contrôleur et validateur HAUQE
- Agent de collecte pour la réception des retours

### Fonctionnalités illustrées

- indicateurs des fiches à contrôler, en cours, retournées et validées ;
- délai moyen de traitement ;
- charge de travail par validateur ;
- recherche et filtres par état, priorité et région ;
- files générale, personnelle et non affectée ;
- progression de complétude et signalement des anomalies ;
- priorisation des dossiers ;
- panneau détaillé avec grille de contrôle ;
- note interne du validateur ;
- validation d'une fiche ;
- retour à l'agent avec motif et instructions ;
- avis de vérification : vérifié conforme, vérifié sous réserve, non vérifié, suspect ou rejeté ;
- décisions de validation : validé, validé sous réserve, ajourné ou rejeté ;
- double validation obligatoire et conservation des visas, réserves et preuves ;
- blocage technique de l'intégration tant que la validation formelle n'est pas acquise ;
- actions d'affectation et d'export simulées ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/validations.html`
- `app/static/css/validations.css`
- `app/static/js/validations.js`

### Données attendues de l'API

- fiches soumises, versions et taux de complétude ;
- anomalies automatiques et résultats des contrôles ;
- validateurs, affectations et charge de travail ;
- décisions, motifs de retour, notes internes et horodatages ;
- historique des soumissions et corrections.

### Points à valider

- profils autorisés à valider définitivement ;
- grille officielle de complétude ;
- règles de priorité et délais de traitement ;
- motifs normalisés de retour ;
- conséquences exactes de la validation sur le registre ;
- agents habilités à produire l'avis de vérification et autorités du second niveau de validation ;
- modalités de signature ou de visa électronique.

---

## 15 — `controle.html`

**Terminée — à valider**

### Rôle de la page

Permettre au contrôleur HAUQE d'évaluer méthodiquement un dossier selon la version FUCCS publiée et de formaliser un contrôle traçable.

### Profils concernés

- Contrôleur ou validateur HAUQE
- Superviseur ou administrateur en consultation

### Fonctionnalités illustrées

- contexte de la fiche, de l'agent et du validateur ;
- critères et rubriques chargés dynamiquement depuis la version FUCCS publiée ; la version frontend active comporte actuellement 24 critères visibles ;
- notation de 0 à 2 et score dynamique sur 56 ;
- progression par domaine et progression globale ;
- comptage des non-conformités et points de vigilance ;
- commentaire associé à chaque critère ;
- constats transversaux et niveaux de risque ;
- sauvegarde locale du brouillon ;
- contrôle de complétude avant décision ;
- décision motivée et confirmation du validateur ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/controle.html`
- `app/static/css/controle.css`
- `app/static/js/controle.js`

### Données attendues de l'API

- grille officielle et versions des critères ;
- dossier soumis et pièces justificatives ;
- notes, commentaires et constats ;
- score calculé et règles de décision ;
- auteur, date, statut et historique du contrôle.

### Points à valider

- contenu exact de la version FUCCS publiée ; aucun nombre de critères n'est figé dans le JavaScript ;
- portée exacte des notes 0, 1 et 2 ;
- seuils et conséquences des décisions ;
- caractère obligatoire des commentaires selon la note ;
- droit de réouverture d'un contrôle finalisé.

---

## 16 — `scoring.html`

**Terminée — à valider**

### Rôle de la page

Présenter séparément le score brut de la grille FUCCS, l'INFC institutionnel et le classement SNCC, sans convertir automatiquement l'un en l'autre tant que la méthode de rapprochement n'est pas validée.

### Profils concernés

- Direction et administrateur HAUQE
- Superviseur, contrôleur et validateur
- Profils autorisés à consulter les résultats

### Fonctionnalités illustrées

- sélection de l'entreprise et du contrôle ;
- score brut sur 56 et pourcentage ;
- INFC distinct sur 100 points et détail de ses six domaines pondérés ;
- classement SNCC : classe A+ à D, statut VA/RE/SU/RT/EX/VE et risque R1 à R5 ;
- niveau de conformité et décision proposée ;
- non-conformités, vigilances et évolution ;
- résultats par domaine en barres ou radar ;
- seuils visuels de conformité ;
- détail des notes, pondérations et contributions ;
- comparaison avec le contrôle précédent ;
- actions prioritaires ;
- courbe et chronologie historiques ;
- exports Excel et PDF simulés ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/scoring.html`
- `app/static/css/scoring.css`
- `app/static/js/scoring.js`

### Données attendues de l'API

- contrôles finalisés et scores par domaine ;
- formule versionnée, pondérations et seuils actifs ;
- historique des contrôles et décisions ;
- non-conformités, actions et échéances ;
- autorisations de consultation et d'export.

### Points à valider

- règle officielle permettant ou non d'alimenter l'INFC à partir de la grille FUCCS sur 56 ;
- méthode de calcul de chaque domaine INFC et traitement des valeurs manquantes ;
- validation des seuils INFC et de la matrice de décision SNCC ;
- niveau d'agrégation de l'INFC national, régional, sectoriel, par référentiel et par organisme ;
- visibilité des résultats selon le profil.

---

## 17 — `rapports.html`

**Terminée — à valider**

### Rôle de la page

Centraliser la préparation, la génération, la conservation et le téléchargement des rapports opérationnels et décisionnels.

### Profils concernés

- Direction et administrateur HAUQE
- Superviseurs, contrôleurs et agents autorisés
- Profils de consultation disposant du droit d'export

### Fonctionnalités illustrées

- indicateurs de génération et d'espace utilisé ;
- catalogue par catégorie et recherche de modèles ;
- rapports entreprises, certifications, organismes, contrôles, scoring et échéances ;
- filtres par période, région, statut et référentiel ;
- sélection des sections à inclure ;
- formats PDF, Excel et CSV ;
- aperçu simulé avant génération ;
- configurations enregistrées et favoris ;
- historique filtrable des générations ;
- téléchargement simulé des fichiers disponibles ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/rapports.html`
- `app/static/css/rapports.css`
- `app/static/js/rapports.js`

### Données attendues de l'API

- catalogue, paramètres et droits d'accès aux rapports ;
- données agrégées selon les filtres ;
- tâches de génération et état d'avancement ;
- fichiers produits, formats, tailles et durées de conservation ;
- historique, auteur, horodatage et journal des téléchargements ;
- configurations personnelles et rapports planifiés.

### Points à valider

- modèles officiels et charte documentaire HAUQE ;
- contenu obligatoire de chaque rapport ;
- droits de génération, consultation et téléchargement ;
- durée de conservation et quota de stockage ;
- règles d'anonymisation et de diffusion externe.

---

## 18 — `utilisateurs.html`

**Terminée — à valider**

### Rôle de la page

Administrer les comptes autorisés, leur rôle, leur périmètre d'accès et les événements essentiels de sécurité.

### Profils concernés

- Administrateur HAUQE
- Superviseur disposant d'une délégation limitée, sous réserve de validation

### Fonctionnalités illustrées

- indicateurs des comptes actifs, bloqués et invitations ;
- suivi de l'activation de la double authentification ;
- alerte sur les comptes nécessitant une intervention ;
- recherche et filtres par rôle, statut et région ;
- sélection et actions groupées ;
- détail du compte, autorisations et activité récente ;
- invitation d'un nouvel utilisateur ;
- modification du rôle et de l'affectation ;
- autorisations complémentaires ;
- réinitialisation du mot de passe simulée ;
- activation, désactivation et export simulés ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/utilisateurs.html`
- `app/static/css/utilisateurs.css`
- `app/static/js/utilisateurs.js`

### Données attendues de l'API

- utilisateurs, profils, rôles et permissions ;
- périmètres géographiques et fonctionnels ;
- invitations, activations, blocages et réinitialisations ;
- état MFA, dernières connexions et événements de sécurité ;
- journal des changements de droits.

### Points à valider

- matrice officielle des rôles et permissions ;
- responsables autorisés à créer ou modifier un compte ;
- politique de mot de passe, MFA et durée des sessions ;
- procédure de blocage, déblocage et révocation ;
- durée de conservation des journaux de connexion.

---

## 19 — `referentiels.html`

**Terminée — à valider**

### Rôle de la page

Administrer les nomenclatures communes afin d'assurer une saisie homogène, des calculs fiables et des rapports comparables.

### Profils concernés

- Administrateur fonctionnel HAUQE
- Référent métier expressément autorisé

### Fonctionnalités illustrées

- catégories de référentiels et indicateurs d'utilisation ;
- normes, certifications, produits, marchés, documents, statuts et décisions ;
- hiérarchies secteurs/activités et régions/préfectures ;
- recherche, filtre et ordre d'affichage ;
- création et modification d'un élément ;
- activation et désactivation avec avertissement ;
- contrôle simulé de l'unicité des codes ;
- visualisation des dépendances ;
- import et export simulés ;
- rappel du versionnement et de la journalisation ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/referentiels.html`
- `app/static/css/referentiels.css`
- `app/static/js/referentiels.js`

### Données attendues de l'API

- catégories, éléments, codes et hiérarchies ;
- versions, périodes de validité et ordre d'affichage ;
- nombre et détail des dépendances ;
- historique des modifications et auteur ;
- résultats des imports et erreurs de validation.

### Points à valider

- nomenclatures officielles et autorités responsables ;
- règles de codification et d'unicité ;
- procédure de modification d'un élément déjà utilisé ;
- niveau de détail géographique et économique ;
- droits d'importation, validation et publication.

---

## 20 — `regles-codification.html`

**Terminée — à valider**

### Rôle de la page

Centraliser les paramètres métier qui pilotent les alertes, calculs, délais et identifiants automatiques, tout en conservant leur version d'application.

### Profils concernés

- Administrateur fonctionnel HAUQE
- Responsable métier autorisé à préparer les règles
- Autorité habilitée à valider leur publication

### Fonctionnalités illustrées

- version active, brouillon et historique ;
- seuils actuellement illustrés à 30, 60 et 90 jours, à remplacer par une configuration versionnée couvrant les horizons retenus par la HAUQE ;
- seuils provisoires de conformité ;
- pondérations provisoires des sept domaines, à retirer ou à remapper après séparation de la grille FUCCS et de l'INFC ;
- modèles de codes pour entreprises, certificats, organismes, collectes et contrôles ;
- délais des circuits d'affectation, validation et correction ;
- simulateur sans incidence sur les données ;
- exemples de codification ;
- sauvegarde en brouillon ;
- publication motivée avec référence d'autorisation ;
- versionnement immuable et journalisation simulés ;
- présentation responsive.

### Fichiers associés

- `app/templates/views/regles-codification.html`
- `app/static/css/regles-codification.css`
- `app/static/js/regles-codification.js`

### Données attendues de l'API

- versions, états, auteurs et dates d'effet ;
- seuils, pondérations, modèles et délais ;
- références des décisions d'autorisation ;
- résultats de simulation et contrôles de cohérence ;
- version utilisée par chaque dossier ou calcul.

### Points à valider

- seuils et pondérations officiels ;
- modèles définitifs de codification ;
- profils de préparation, approbation et publication ;
- date d'effet et traitement des dossiers en cours ;
- procédure de retrait ou remplacement d'une version erronée.

---

## 21 à 24 — Audit, authentification et profil

**Terminées — à valider**

### `journal-audit.html`

Journal en lecture seule des connexions, créations, modifications, décisions et exports. Il comprend les filtres, le détail avant/après, l'adresse IP, le résultat, l'export et la vérification d'intégrité simulés. Profils : administrateur et auditeur autorisé.

Fichiers : `app/templates/views/journal-audit.html`, `app/static/js/journal-audit.js`, `app/static/css/final-pages.css`.

Données API : événements immuables, auteur, horodatage, ressource, valeurs avant/après, IP, résultat et preuve d'intégrité. À valider : durée de conservation, accès, anonymisation et mécanisme de scellement.

### `connexion.html`

Authentification professionnelle, visibilité du mot de passe, contrôle des champs, message d'erreur, mémorisation de session et avertissement de blocage. L'API devra gérer les sessions, tentatives, MFA, révocation et journalisation.

### `mot-de-passe-oublie.html`

Demande de lien temporaire, réponse neutre ne révélant pas l'existence du compte, expiration annoncée et renvoi. L'API devra produire un jeton unique, limité dans le temps et invalidé après usage.

### `profil.html`

Informations personnelles, sécurité, changement de mot de passe, MFA, préférences de notification, sessions et déconnexion. Les droits et l'adresse professionnelle ne doivent pas être modifiables librement par l'utilisateur.

Ajout : verrouillage automatique après inactivité, code privé d'au moins cinq caractères, délai configurable de 5 à 30 minutes, bouton de test, écran global bloquant et déconnexion après cinq erreurs. FastAPI devra hacher et vérifier le code ainsi que l'état de la session.

Fichiers : `app/templates/views/{connexion,mot-de-passe-oublie,profil}.html`, `app/static/js/{connexion,mot-de-passe-oublie,profil}.js`, `app/static/css/final-pages.css`.

Points communs à valider : politique de mots de passe, MFA, durée des sessions, délais de blocage, canaux de notification et conformité des journaux.

---

## Nouvelles pages et adaptations issues de la lecture documentaire

Les éléments ci-dessous constituent le nouveau backlog fonctionnel du frontend. Ils ne sont pas encore considérés comme terminés.

| Priorité | Route ou adaptation proposée | Objet | Statut |
|---|---|---|---|
| P0 | `/verifications` | File de vérification documentaire, demandes aux OC, anomalies et avis de vérification | Maquette fonctionnelle — à valider |
| P0 | `/integrations` | File des dossiers validés à intégrer, contrôle préalable, codification et contrôle post-intégration | Maquette fonctionnelle — à valider |
| P0 | adaptation `/controle` | Charger la grille FUCCS versionnée depuis l'API ; version frontend active : 24 critères visibles ; nombre de critères et score maximal calculés dynamiquement | À corriger |
| P0 | adaptation `/scoring` | Séparer score FUCCS, INFC sur 100 et SNCC | À refondre |
| P0 | adaptation `/alertes` et `/echeances` | Niveaux validés 180/90/30 jours puis expiration, alertes spéciales, délais et relances | À corriger |
| P0 | adaptation `/utilisateurs` | Profils institutionnels, moindre privilège, double validation et séparation des fonctions | À corriger |
| P1 | `/infc` | Calcul et analyse de l'INFC national et de ses agrégats | Maquette fonctionnelle — à valider |
| P1 | `/classement-sncc` | Classe, statut, risque, matrice de décision et historique des reclassements | Maquette fonctionnelle — à valider |
| P1 | `/veille` | Espace de travail de la CVC : alertes, relances, échéances, qualité des données et rapports | Maquette fonctionnelle — à valider |
| P1 | `/tableaux-de-bord/tactique` | Pilotage mensuel de la Direction Technique | Maquette fonctionnelle — à valider |
| P1 | `/tableaux-de-bord/strategique` | Pilotage trimestriel de la Présidence et synthèse décisionnelle | Maquette fonctionnelle — à valider |
| P1 | `/tableaux-de-bord/annuel` | Bilan institutionnel annuel et tendances | Maquette fonctionnelle — à valider |
| P1 | `/barometre` | Baromètre national périodique des certifications | Maquette fonctionnelle — à valider |
| P1 | `/decisions` | Registre des décisions, recommandations et plans d'action | Maquette fonctionnelle — à valider |
| P1 | `/mises-a-jour` | Demandes de modification, justificatifs, validation et historique | Maquette fonctionnelle — à valider |
| P1 | adaptation dossiers détaillés | Onglets versions, portée, sites, suspensions, retraits, renouvellements et preuves | À compléter |
| P2 | `/public` | Tableau de bord public limité aux données agrégées autorisées | Maquette fonctionnelle — à valider |
| P2 | `/echanges-organismes` | Demandes de confirmation, réponses, délais et pièces des organismes certificateurs | Maquette fonctionnelle — à valider |
| P2 | `/documents` | Registre documentaire, métadonnées, versions, classement et archivage | Maquette fonctionnelle — à valider |
| P2 | `/incidents` | Déclaration, criticité, traitement et clôture des incidents | Maquette fonctionnelle — à valider |
| P2 | `/amelioration-continue` | Audits, retours d'expérience, actions correctives et cycle PDCA | Maquette fonctionnelle — à valider |
| P2 | `/qualite-donnees` | Contrôles de cohérence, doublons, complétude et corrections | Maquette fonctionnelle — à valider |
| P2 | `/sauvegardes` | Supervision des sauvegardes et tests de restauration | Maquette fonctionnelle — à valider |
| P2 | `/publications` | Préparation, validation et diffusion des publications | Maquette fonctionnelle — à valider |

### Exigences détaillées par nouveau module

#### Vérification documentaire

- contrôle de complétude avant examen du certificat ;
- vérification du numéro, du titulaire, de l'adresse ou du site, du référentiel, de sa version, de la portée, des produits, des dates, de la signature, du cachet, du logo et des dispositifs d'authentification ;
- vérification de l'organisme et de son accréditation pour la portée concernée ;
- conservation des sources, preuves, liens officiels, réponses et dates de vérification ;
- anomalies mineures, documentaires, de cohérence ou critiques ;
- retour pour complément et escalade des cas suspects à la Direction Technique.

#### Intégration et mise à jour de la BNEC

- intégration réservée aux dossiers formellement validés ;
- détection des doublons et contrôle des identifiants avant intégration ;
- attribution automatique des codes entreprise, organisme et certification ;
- import manuel, import de fichiers normalisés et future synchronisation autorisée ;
- vérification post-intégration des liens, documents et recherches ;
- notifications internes de fin d'intégration ;
- journal complet des valeurs avant/après, auteur, date, motif et justificatif ;
- aucune suppression de l'historique.

#### INFC

- calcul sur 100 points selon six domaines versionnés ;
- niveaux : Excellence 95–100, Très satisfaisant 90–94, Satisfaisant 75–89, Acceptable 60–74, Faible 40–59 et Critique sous 40 ;
- agrégats national, régional, sectoriel, par référentiel et par organisme certificateur ;
- affichage du nombre d'éléments évalués, de la période, de l'évolution et de la version de formule ;
- exclusion ou signalement explicite des dossiers incomplets afin de ne pas produire un indice trompeur.

#### SNCC

- classes A+, A, B, C et D ;
- statuts VA, RE, SU, RT, EX et VE ;
- risques R1 à R5 ;
- proposition par le contrôleur, vérification par le Point focal et validation par la Direction Technique ;
- reclassement après contrôle, visite, audit, renouvellement, suspension, retrait ou information affectant la validité ;
- historique complet des classements et justification de chaque changement.

#### Cellule de Veille des Certifications

- échéances contrôlées quotidiennement ;
- analyse hebdomadaire des alertes et relances ;
- réunion et note de veille mensuelles ;
- rapport consolidé trimestriel ;
- suivi des documents manquants, données non actualisées, audits, renouvellements, suspensions et retraits ;
- indicateurs de performance de la veille et listes d'entreprises à risque.

#### Pilotage et diffusion

- tableau opérationnel quotidien ou hebdomadaire pour l'Administrateur, le Point focal, les Agents et la CVC ;
- tableau tactique mensuel pour la Direction Technique ;
- tableau stratégique trimestriel pour la Présidence ;
- tableau annuel pour le bilan institutionnel ;
- tableau public semestriel ou annuel, après validation des données diffusables ;
- synthèse décisionnelle structurée en constats, risques majeurs et recommandations prioritaires ;
- cartographie par région, préfecture et commune lorsque les coordonnées sont disponibles.

## Décisions acquises et arbitrages restant à obtenir

| Sujet | Décision acquise ou documents en présence | Suite attendue |
|---|---|---|
| Seuils d'alerte | RM-05 à RM-08 : 180/90/30 jours puis expiration | Implémenter ; confirmer seulement l'éventuelle information complémentaire à 12 mois et la fréquence des relances |
| Score de contrôle | FUCCS versionné ; critères et score maximal issus de la grille publiée | La version frontend active comporte 24 critères visibles ; ne pas figer 24/28 ni 48/56 dans le code |
| INFC | Document INFC : six domaines sur 100 ; guide : dimensions plus larges | Valider la formule exacte, les sources et l'agrégation |
| Classification entreprise | RM-22 à RM-24 : Conforme 85-100, À surveiller 60-84, Non conforme <60 | Implémenter séparément de l'INFC et du SNCC |
| Pondérations | RM-17 à RM-21 : pondérations paramétrables et versionnées | Définir les valeurs initiales sans les coder en dur |
| Statuts | Plusieurs vocabulaires entre les fiches, le guide, le SNCC et les règles validées | Publier un dictionnaire unique avec transitions autorisées |
| Codification | Plusieurs modèles sont proposés dans le corpus | Choisir le format national officiel et les règles de séquence |
| Validation | Guide : niveaux hiérarchisés et double validation | Identifier précisément les habilitations et le visa électronique attendu |
| Données publiques | Tableau public prévu, mais périmètre de diffusion non arrêté | Valider les champs agrégés, fréquence et autorité de publication |

## Pages planifiées

### Module Entreprises

#### `entreprises.html`

- registre national des entreprises ;
- recherche et filtres multicritères ;
- statuts automatiques ;
- détection visuelle des entreprises à risque ;
- export et ouverture du dossier détaillé.

#### `entreprise-detail.html`

- identité complète ;
- produits, marchés et sites ;
- certifications détenues ;
- score et niveau de conformité ;
- contrôles, documents et chronologie.

#### `entreprise-form.html`

- création et modification ;
- contrôles RCCM et NIF ;
- localisation administrative ;
- contacts, produits et activités ;
- détection des doublons.

### Module Certifications

#### `certifications.html`

- registre de tous les certificats ;
- recherche et filtres ;
- statuts, échéances et organismes ;
- export et actions de suivi.

#### `certification-detail.html`

- numéro original et code national ;
- référentiel, portée et produits ;
- organisme certificateur ;
- dates, audits et renouvellements ;
- documents et historique des statuts.

#### `certification-form.html`

- saisie guidée ;
- référentiels configurables ;
- contrôle des dates ;
- pièces justificatives ;
- prévention des doublons.

### Module Organismes certificateurs

#### `organismes.html`

- annuaire des organismes ;
- pays, reconnaissance et statut ;
- domaines d'accréditation ;
- recherche et filtres.

#### `organisme-detail.html`

- identité et coordonnées ;
- accréditations par référentiel ;
- certificats délivrés ;
- suspensions, retraits et historique.

### Module Collecte et contrôle

### Module Analyse et reporting

### Module Administration

### Module Authentification et compte

---

## Référentiel validé RM-01 à RM-51 — impacts obligatoires

Le document **Règles métier validation GFA — version améliorée** est désormais une source normative autorisée par la HAUQE. Il contient 51 règles : 17 validées sans modification, 23 modifiées puis retenues et 11 nouvelles règles RM-41 à RM-51. Trois règles supplémentaires seront ajoutées ultérieurement ; elles doivent être réservées dans le catalogue sans être inventées ni anticipées dans le code.

La priorité d'interprétation devient :

1. règles métiers RM-01 à RM-51 validées ;
2. procédures opérationnelles ;
3. documents INFC et SNCC ;
4. guide méthodologique ;
5. propositions et simulations des maquettes.

Chaque règle devra être reliée à un écran, une permission, une table, une route API, un événement d'audit et au moins un test d'acceptation.

### 1. Certifications

Les listes, fiches détaillées et formulaires de certification doivent intégrer :

- date d'obtention obligatoire ;
- date d'expiration facultative seulement si le référentiel autorise explicitement une validité sans échéance ;
- statut automatique **À vérifier** lorsque l'expiration attendue ou la preuve documentaire manque ;
- blocage des dates d'obtention futures ou postérieures à la date de saisie ;
- blocage d'une expiration antérieure ou égale à l'obtention ;
- au moins une pièce officielle : certificat, décision, rapport d'audit, lettre de renouvellement ou équivalent ;
- contrôle d'unicité par entreprise, organisme, référentiel et périmètre ;
- preuve officielle de la procédure de renouvellement ;
- pondération transitoire paramétrable pendant le renouvellement ;
- statut **Non renouvelée** six mois après expiration, sauf procédure officielle justifiée ;
- historisation de la délivrance, modification, suspension, retrait, expiration et renouvellement ;
- recalcul des statuts, scores, alertes et indicateurs après chaque événement.

### 2. Alertes et échéances

Les niveaux validés à implémenter sont :

| Niveau | Déclenchement | Objet |
|---|---:|---|
| Niveau 1 — Information | 180 jours avant expiration | Préparer le renouvellement |
| Niveau 2 — Surveillance | 90 jours avant expiration | Renouvellement non confirmé |
| Niveau 3 — Urgence | 30 jours avant expiration | Mobilisation prioritaire |
| Niveau 4 — Critique | À l'expiration | Maintien jusqu'à régularisation ou clôture |

Les anciens horizons 12/6/3/1 mois restent documentés comme valeurs historiques ou complémentaires à confirmer. Ils ne doivent plus être présentés comme la règle principale validée.

Le frontend doit afficher le niveau, le responsable, les preuves de renouvellement, la date de déclenchement, les relances, notifications, réponses, escalades et la clôture. Le backend devra générer, dédupliquer et historiser ces événements.

### 3. Entreprises

Les pages Entreprises doivent prévoir :

- RCCM unique comme identifiant juridique principal ;
- enregistrement possible sans RCCM avec le statut **En attente de régularisation** ;
- alerte de régularisation du RCCM ;
- minimum obligatoire : nom, localité, région et téléphone ou courriel principal ;
- statut **Entreprise certifiée active** calculé dès qu'une certification valide existe ;
- classement **À risque** si une certification stratégique expire dans les 90 jours ;
- statut **Non conforme** uniquement en l'absence de certification valide et de renouvellement officiel ;
- détection des doublons par RCCM, IFU/NIF, nom, téléphone et courriel ;
- identifiant national permanent et non réattribuable ;
- versionnement et historique des changements administratifs.

### 4. Organismes certificateurs

Les pages Organismes doivent couvrir :

- organismes non accrédités autorisés, avec certificats classés **À vérifier** ;
- accréditations par référentiel, domaine technique, périmètre et période ;
- statuts active, suspendue, retirée, expirée et réhabilitée ;
- reclassement des certificats **Sous vérification** après suspension ou perte d'accréditation ;
- décision HAUQE avant invalidation définitive ;
- recalcul des scores après validation d'un changement d'accréditation ;
- unicité contrôlée par nom officiel, numéro d'accréditation, pays et domaine ;
- suspension de l'enregistrement en cas de doublon potentiel ;
- historique et versions de l'organisme et de ses accréditations.

### 5. Classification entreprise, INFC et SNCC

La HAUQE confirme que les trois résultats sont distincts :

1. **classification globale de l'entreprise** :
   - 85 à 100 : Conforme ;
   - 60 à 84 : À surveiller ;
   - moins de 60 : Non conforme ;
2. **INFC de la certification sur 100**, composé de six domaines pondérés et de ses niveaux propres ;
3. **SNCC**, composé des classes A+ à D, statuts VA/RE/SU/RT/EX/VE et risques R1 à R5.

Le frontend ne doit jamais fusionner ces résultats. Chaque résultat doit afficher son modèle, sa version, sa date de calcul, ses données sources et son historique. Les pondérations, seuils, règles de complétude et pondérations transitoires sont paramétrables, versionnés et audités.

### 6. Collecte, soumission et validation

Le parcours obligatoire est :

**Brouillon → Soumise → Vérification → Contrôle → Validation définitive → Intégration BNEC → Classification entreprise/INFC → SNCC → Veille**

Exigences :

- brouillon incomplet autorisé ;
- soumission bloquée si un champ obligatoire est absent ;
- rappel pour une fiche papier non saisie dans les cinq jours ouvrables ;
- détection multicritère des doublons avant validation ;
- modification possible jusqu'à la validation définitive ;
- autorisation spécifique et nouvelle version après validation ;
- audit de toute correction ;
- séparation visuelle et fonctionnelle de la vérification, du contrôle, de la validation et de l'intégration.

### 7. Utilisateurs, rôles et exports

La page Utilisateurs et les contrôles d'accès doivent ajouter :

- permissions configurables, sans se limiter à des rôles codés en dur ;
- droits complets de l'administrateur sur utilisateurs, paramètres, référentiels, organismes, sauvegardes et audit ;
- accès en lecture seule par défaut pour consultants, partenaires et prestataires ;
- export interdit sans permission explicite ;
- motif et périmètre obligatoires pour les exports sensibles ;
- audit de l'identité, date, heure, motif et nature des données exportées ;
- désactivation après 180 jours d'inactivité ;
- notification 30 jours avant désactivation ;
- réactivation par un administrateur ;
- verrouillage après cinq échecs de connexion ;
- durée de verrouillage paramétrable et notifications de sécurité.

Le verrouillage local de reprise de session reste distinct du verrouillage du compte d'authentification.

### 8. Audit, archivage, conservation et versions

Le système doit :

- auditer création, consultation, modification, validation, archivage, export, connexion et déconnexion ;
- enregistrer l'adresse IP lorsqu'elle est disponible ;
- rendre le journal non modifiable ;
- interdire la suppression physique des données métier ;
- archiver avec auteur, date et motif ;
- restreindre l'accès aux archives ;
- versionner entreprise, certification et organisme ;
- conserver anciennes valeurs, nouvelles valeurs, auteur, date et motif ;
- conserver les données au moins dix ans après expiration ou retrait de la dernière certification ;
- distinguer les événements métier, de sécurité, d'export, d'archivage et de consultation.

### 9. Sauvegardes et continuité

Un écran d'administration technique est à prévoir pour :

- politiques de sauvegarde quotidienne, hebdomadaire et mensuelle ;
- rétention configurable ;
- état, durée, taille, emplacement et résultat des sauvegardes ;
- incidents et notifications d'échec ;
- demandes et historiques de restauration ;
- tests périodiques de restauration et preuve de leur intégrité.

Les sauvegardes réelles relèvent du backend et de l'infrastructure ; le frontend sert à leur supervision sécurisée.

### 10. Qualité des données et plans d'action

RM-49 impose une revue annuelle de l'exactitude, la complétude, la cohérence, l'unicité, la traçabilité et la conformité. Il faut prévoir :

- campagnes de revue ;
- indicateurs et résultats ;
- registre des anomalies ;
- responsable, délai, priorité et preuves ;
- plans d'actions correctives ;
- suivi de réalisation, évaluation de l'effet et clôture.

Cette exigence confirme les modules **Décisions** et **Plans d'action**.

### 11. Publication et tableaux de bord

Toute diffusion de données, statistiques, indicateurs ou rapports nécessite une validation préalable de la Direction Générale ou de l'autorité compétente.

Le workflow cible est :

**Brouillon → Soumis → Approuvé → Publié → Retiré**

Il faut séparer les données internes des données publiques, journaliser les validations et empêcher le tableau de bord public d'accéder directement aux données confidentielles. Les cinq niveaux de pilotage restent opérationnel, tactique, stratégique, annuel et public.

### 12. Administration des règles

`Règles & codification` devient l'interface d'administration sécurisée de :

- pondérations et modèles de scoring ;
- seuils de conformité ;
- niveaux d'alerte et délais automatiques ;
- référentiels et nomenclatures ;
- catégories d'entreprises ;
- profils et permissions ;
- modèles de codification ;
- règles de complétude ;
- paramètres fonctionnels.

Chaque modification comporte auteur, motif, ancienne valeur, nouvelle valeur, date d'effet, statut brouillon/validé/publié et événement d'audit. Une modification de paramètre ne doit pas nécessiter une modification du code source.

### 13. Tables PostgreSQL supplémentaires

Le modèle de données doit prévoir au minimum :

- `business_rules`, `business_rule_versions`, `business_rule_parameters` ;
- `scoring_models`, `scoring_model_versions`, `scoring_weights` ;
- `enterprise_scores`, `data_completeness_scores` ;
- `renewal_procedures`, `renewal_evidence` ;
- `certification_versions`, `enterprise_versions`, `certification_body_versions` ;
- `accreditation_status_history`, `duplicate_candidates` ;
- `account_lock_events`, `account_inactivity_events`, `security_events` ;
- `archive_records`, `data_retention_policies` ;
- `backup_policies`, `backup_runs`, `restore_tests` ;
- `data_quality_reviews`, `data_quality_findings`, `corrective_action_plans` ;
- `publication_requests`, `publication_approvals`.

Les identifiants nationaux ne sont jamais réutilisés et les suppressions métier sont logiques.

### 14. Routes FastAPI supplémentaires

Groupes de routes à prévoir :

- `/api/v1/business-rules` et `/api/v1/business-rules/{id}/versions` ;
- `/api/v1/scoring-models` ;
- `/api/v1/enterprises/{id}/score` et `/api/v1/enterprises/{id}/completeness` ;
- `/api/v1/certifications/{id}/renewal` et `/api/v1/certifications/{id}/history` ;
- `/api/v1/certification-bodies/{id}/accreditations` ;
- `/api/v1/duplicates/check` ;
- `/api/v1/archives` et `/api/v1/security-events` ;
- `/api/v1/backups` et `/api/v1/restore-tests` ;
- `/api/v1/data-quality-reviews` et `/api/v1/action-plans` ;
- `/api/v1/publications` et `/api/v1/public/indicators`.

Les validations, statuts et calculs automatiques sont exécutés côté FastAPI et PostgreSQL, jamais uniquement dans le JavaScript du navigateur.

### 15. Documentation et traçabilité

Documents à maintenir :

- présente feuille de route ;
- `PASSATION_PROJET_HAUQE_CERTIF.md` ;
- `GUIDE_UTILISATION.md` ;
- dictionnaire de données ;
- catalogue des statuts ;
- matrice rôles/permissions ;
- catalogue versionné RM-01 à RM-51, puis les trois règles futures lorsqu'elles seront reçues ;
- matrice règle → écran → permission → table → API → événement d'audit → test.

### 16. Priorités de réalisation

- **P0** : validations de dates et pièces, doublons, seuils 180/90/30/expiration, séparation classification entreprise/INFC/SNCC, workflow vérification-contrôle-validation-intégration, permissions et audit ;
- **P1** : versionnement, renouvellements, qualité des données, décisions, publications et administration complète des règles ;
- **P2** : supervision des sauvegardes, restauration, revue annuelle et tableaux de bord publics.

---

## Règle de mise à jour de la feuille de route

À chaque nouvelle page créée :

1. mettre son statut à jour dans le tableau d'avancement ;
2. décrire précisément son rôle ;
3. identifier les profils concernés ;
4. énumérer les fonctionnalités effectivement illustrées ;
5. indiquer les fichiers HTML, CSS et JavaScript associés ;
6. préciser les données qui devront provenir de l'API ;
7. noter les points restant à valider par la HAUQE ou GFA ;
8. rattacher les règles RM concernées, les tables, les routes API et les tests.

## Synchronisation API — Vérification + FUCCS

**Statut : backend du lot prêt — raccordement frontend à effectuer**

La règle permanente est désormais :
- chaque endpoint backend doit être associé à sa page frontend ;
- la feuille backend et la feuille frontend sont mises à jour ensemble ;
- le rôle du bouton, onglet, modal ou composant consommateur est documenté.

# Mapping frontend ↔ endpoints — Vérification + FUCCS

## `verifications.html` — route `#/verifications`

| Endpoint | Élément / action frontend | Rôle sur la page |
|---|---|---|
| `GET /api/v1/verifications` | compteurs, file générale, file personnelle, filtres | Charger les dossiers, priorités, avis, nombre de points/anomalies/confirmations |
| `POST /api/v1/verifications/from-fiche/{fiche_id}` | bouton **Ouvrir en vérification** | Créer le dossier depuis une fiche `SOUMISE` |
| `GET /api/v1/verifications/{dossier_id}` | panneau détail | Charger l'en-tête et la synthèse du dossier |
| `PATCH /api/v1/verifications/{dossier_id}` | priorité / risque / synthèse | Mettre à jour le travail courant sans valider |
| `GET /api/v1/verifications/{dossier_id}/affectations` | onglet Affectation | Afficher l'historique des vérificateurs |
| `POST /api/v1/verifications/{dossier_id}/affectations` | modal Assigner | Affecter un vérificateur et une échéance |
| `PATCH /api/v1/verifications/{dossier_id}/affectations/{assignment_id}` | Réaffecter / terminer affectation | Mettre à jour la période et le statut |
| `GET /api/v1/verifications/{dossier_id}/points` | grille documentaire | Charger les contrôles réalisés |
| `POST /api/v1/verifications/{dossier_id}/points` | Ajouter/valider un point | Enregistrer résultat, observation et preuve |
| `PATCH /api/v1/verifications/{dossier_id}/points/{point_id}` | Modifier le point | Corriger un résultat avant clôture |
| `GET /api/v1/verifications/{dossier_id}/anomalies` | panneau Anomalies | Lister incohérences et cas suspects |
| `POST /api/v1/verifications/{dossier_id}/anomalies` | Signaler anomalie | Créer une anomalie générale ou liée à un point |
| `PATCH /api/v1/verifications/{dossier_id}/anomalies/{anomaly_id}` | Modifier gravité/statut | Mettre à jour l'anomalie |
| `POST /api/v1/verifications/{dossier_id}/anomalies/{anomaly_id}/resolve` | bouton Résoudre | Enregistrer la résolution motivée |
| `POST /api/v1/verifications/{dossier_id}/anomalies/{anomaly_id}/escalate` | bouton Escalader | Transmettre un cas suspect à la Direction Technique |
| `GET /api/v1/verifications/{dossier_id}/confirmations` | onglet Confirmations externes | Suivre demandes et réponses externes |
| `POST /api/v1/verifications/{dossier_id}/confirmations` | Nouvelle demande | Journaliser canal, destinataire, objet et échéance |
| `PATCH /api/v1/verifications/{dossier_id}/confirmations/{confirmation_id}` | Modifier la demande | Corriger métadonnées avant réponse |
| `POST /api/v1/verifications/{dossier_id}/confirmations/{confirmation_id}/response` | Enregistrer réponse | Stocker réponse, résultat et document reçu |
| `POST /api/v1/verifications/{dossier_id}/close` | bouton **Prononcer l'avis** | Clôturer avec avis normalisé + synthèse |
| `POST /api/v1/verifications/{dossier_id}/reopen` | action administrative | Réouvrir avec motif et audit |

### Règle frontend de vérification

La page ne doit créer que les points correspondant aux informations réellement demandées dans la version courante du formulaire. Un champ non affiché/non collecté n'est pas une anomalie automatique.

---

## `controle.html` — route `#/controle`

La version frontend actuelle peut afficher 24 critères, mais **le nombre de critères et le score maximal ne doivent jamais être codés en dur**. Ils viennent de la grille publiée.

| Endpoint | Élément / action frontend | Rôle sur la page |
|---|---|---|
| `GET /api/v1/fuccs/grilles/active` | initialisation page | Trouver la version de grille applicable |
| `GET /api/v1/fuccs/grilles/{grid_id}/rubriques` | navigation par rubrique | Construire les groupes de critères |
| `GET /api/v1/fuccs/grilles/{grid_id}/criteres` | liste de critères | Construire dynamiquement notation/commentaires/preuves |
| `POST /api/v1/verifications/{dossier_id}/fuccs-controles` | bouton Démarrer FUCCS | Ouvrir un contrôle après vérification admissible |
| `GET /api/v1/fuccs/controles` | file des contrôles | Rechercher contrôles en cours/finalisés |
| `GET /api/v1/fuccs/controles/{control_id}` | en-tête contrôle | Charger score, taux, progression et statut |
| `GET /api/v1/fuccs/controles/{control_id}/notes` | chargement des notes | Restaurer le brouillon serveur |
| `PUT /api/v1/fuccs/controles/{control_id}/notes/{criterion_id}` | widget de notation | Enregistrer note/commentaire/preuve et recalculer serveur |
| `GET /api/v1/fuccs/controles/{control_id}/constats` | panneau Constats | Afficher constats transversaux |
| `POST /api/v1/fuccs/controles/{control_id}/constats` | Ajouter constat | Enregistrer risque/non-conformité/observation |
| `PATCH /api/v1/fuccs/controles/{control_id}/constats/{finding_id}` | Éditer constat | Mettre à jour avant finalisation |
| `POST /api/v1/fuccs/controles/{control_id}/finalize` | bouton Finaliser | Vérifier toutes notes/preuves/commentaires puis verrouiller |
| `POST /api/v1/fuccs/controles/{control_id}/reopen` | action habilitée | Réouvrir un contrôle avec motif audité |

---

## `referentiels.html` / `regles-codification.html`

Ces pages administrent **la grille**, pas le contrôle opérationnel.

| Endpoint | Rôle frontend |
|---|---|
| `GET /api/v1/fuccs/grilles` | afficher toutes les versions et leur état |
| `POST /api/v1/fuccs/grilles` | créer une version brouillon |
| `GET /api/v1/fuccs/grilles/{grid_id}` | afficher métadonnées et score maximal calculé |
| `PATCH /api/v1/fuccs/grilles/{grid_id}` | modifier uniquement un brouillon |
| `POST /api/v1/fuccs/grilles/{grid_id}/clone` | créer la prochaine version à partir d'une version existante |
| `POST /api/v1/fuccs/grilles/{grid_id}/publish` | publier avec référence d'approbation |
| `POST /api/v1/fuccs/grilles/{grid_id}/retire` | retirer une version sans supprimer l'historique |
| `GET/POST/PATCH/DELETE .../rubriques` | administrer les rubriques du brouillon |
| `GET/POST/PATCH/DELETE .../criteres` | administrer les critères du brouillon |

Une grille publiée est immuable.

---

## `validations.html`

La page Validation ne doit pas modifier Vérification ou FUCCS.

Le prochain domaine lui fournira :
- avis final de vérification ;
- contrôle FUCCS finalisé ;
- score/taux calculés ;
- constats ;
- preuves ;
pour prononcer la décision institutionnelle.


### Correction importante de la doctrine FUCCS frontend

La version frontend active comporte actuellement **24 critères visibles**.

Le frontend ne doit cependant jamais coder comme constante :
- 24 ou 28 critères ;
- 48 ou 56 points.

Il doit charger :
- la version publiée ;
- les rubriques ;
- les critères ;
- `score_maximal_calcule`
depuis l'API.

### Prochaine synchronisation frontend

Le prochain domaine `Validation / Intégration BNEC` précisera les endpoints qui alimenteront :
- `validations.html` ;
- la future page/file d'intégration BNEC.

## Synchronisation API — Validation / Intégration BNEC

**Backend : implémenté — non validé runtime.**  
**Recette : lors du raccordement frontend, page par page.**

### `validations.html` — `#/validations`

Cette page ne doit plus mélanger Vérification, FUCCS et Validation.
Vérification/FUCCS sont affichés en lecture ; les mutations de la page
portent sur N1, N2 et les corrections.

| Endpoint | Composant / action | Permission |
|---|---|---|
| `GET /api/v1/validations/queue` | File À valider | `VALIDATION.LIRE` |
| `GET /api/v1/validations` | Historique et filtres | `VALIDATION.LIRE` |
| `GET /api/v1/validations/{validation_id}` | Détail décision | `VALIDATION.LIRE` |
| `POST /api/v1/validations/from-fiche/{fiche_id}/level-1` | Revue technique N1 | `VALIDATION.REVUE_N1` |
| `POST /api/v1/validations/from-fiche/{fiche_id}/level-2` | Validation définitive N2 | `VALIDATION.DECIDER_N2` |
| `GET /api/v1/validations/{validation_id}/corrections` | Onglet Corrections | `VALIDATION.LIRE` |
| `POST /api/v1/validations/{validation_id}/corrections` | Demander correction | `VALIDATION.DEMANDER_CORRECTION` |
| `PATCH /api/v1/validations/{validation_id}/corrections/{correction_id}` | Modifier la demande | `VALIDATION.DEMANDER_CORRECTION` |
| `POST /api/v1/validations/{validation_id}/corrections/{correction_id}/resubmit` | Réponse/resoumission | `VALIDATION.RESOUMETTRE_CORRECTION` |

Panneau recommandé :

```text
Avis Vérification
Résultat FUCCS
Constats / anomalies / preuves
-------------------------------
Revue N1
Validation N2
Corrections
Historique
```

### `/integrations` — `#/integrations`

Cette route existe déjà dans le backlog frontend comme maquette P0.

| Endpoint | Composant / action | Permission |
|---|---|---|
| `GET /api/v1/integrations-bnec/queue` | File À intégrer | `INTEGRATION.LIRE` |
| `GET /api/v1/integrations-bnec` | Historique/filtres | `INTEGRATION.LIRE` |
| `POST /api/v1/validations/{validation_id}/integration-bnec` | Ouvrir intégration | `INTEGRATION.OUVRIR` |
| `GET /api/v1/integrations-bnec/{integration_id}` | Détail/progression | `INTEGRATION.LIRE` |
| `POST /api/v1/integrations-bnec/{integration_id}/precontrol` | Précontrôle | `INTEGRATION.PRECONTROLER` |
| `POST /api/v1/integrations-bnec/{integration_id}/start` | Démarrage | `INTEGRATION.EXECUTER` |
| `GET /api/v1/integrations-bnec/{integration_id}/elements` | Tableau source→cible | `INTEGRATION.LIRE` |
| `POST /api/v1/integrations-bnec/{integration_id}/elements` | Ajouter élément | `INTEGRATION.EXECUTER` |
| `PATCH /api/v1/integrations-bnec/{integration_id}/elements/{element_id}` | Préparer/corriger élément | `INTEGRATION.EXECUTER` |
| `POST /api/v1/integrations-bnec/{integration_id}/elements/{element_id}/result` | Intégré/Échec | `INTEGRATION.EXECUTER` |
| `POST /api/v1/integrations-bnec/{integration_id}/postcontrol` | Postcontrôle | `INTEGRATION.POSTCONTROLER` |
| `POST /api/v1/integrations-bnec/{integration_id}/complete` | Clôturer | `INTEGRATION.CLOTURER` |

Progression UI :

```text
EN_ATTENTE → PRECONTROLE → INTEGRATION_EN_COURS → POSTCONTROLE → INTEGREE
```

### Règle de test désormais appliquée

Lors du raccordement de chaque page :
1. remplacer mocks/localStorage par `core/api.js` ;
2. tester permissions ;
3. tester transitions et erreurs 409/422 ;
4. contrôler le journal d'audit ;
5. seulement ensuite marquer l'endpoint « raccordé et validé ».

### Prochaine synchronisation

```text
scoring.html
#/infc
#/classement-sncc
```

avec le domaine Scoring / Classification / INFC / SNCC.

## Synchronisation API — Scoring / Classification / INFC / SNCC

**Backend : implémenté — non validé runtime.**

### `scoring.html` — `#/scoring`

La page doit séparer quatre cartes/résultats :

```text
FUCCS
Classification entreprise
INFC
SNCC
```

Aucune règle de conversion automatique entre ces résultats.

#### Classification entreprise

| Endpoint | Élément UI | Permission |
|---|---|---|
| `GET /api/v1/entreprises/{enterprise_id}/classifications/latest` | carte Classification | `CLASSIFICATION.LIRE` |
| `GET /api/v1/entreprises/{enterprise_id}/classifications` | historique / courbe | `CLASSIFICATION.LIRE` |
| `POST /api/v1/entreprises/{enterprise_id}/classifications/evaluate` | Calculer et enregistrer | `CLASSIFICATION.CALCULER_VALIDER` |

#### INFC

| Endpoint | Élément UI | Permission |
|---|---|---|
| `GET /api/v1/certifications/{certification_id}/infc/latest` | carte INFC | `INFC.LIRE` |
| `GET /api/v1/certifications/{certification_id}/infc` | historique | `INFC.LIRE` |
| `POST /api/v1/certifications/{certification_id}/infc/calculate` | Calculer | `INFC.CALCULER` |
| `POST /api/v1/infc/results/{result_id}/validate` | Valider | `INFC.VALIDER` |
| `GET /api/v1/infc/results` | recherche globale | `INFC.LIRE` |

#### SNCC

| Endpoint | Élément UI | Permission |
|---|---|---|
| `GET /api/v1/certifications/{certification_id}/sncc/current` | carte Classement | `SNCC.LIRE` |
| `GET /api/v1/certifications/{certification_id}/sncc` | historique | `SNCC.LIRE` |
| `POST /api/v1/certifications/{certification_id}/sncc` | Premier classement | `SNCC.CLASSER` |
| `POST /api/v1/certifications/{certification_id}/sncc/reclassify` | Reclasser | `SNCC.RECLASSER` |
| `POST /api/v1/sncc/{sncc_id}/close` | Clôturer période | `SNCC.RECLASSER` |
| `GET /api/v1/sncc` | filtres globaux | `SNCC.LIRE` |

---

### `#/infc`

Page P1 spécialisée à créer/raccorder.

Rôle :
- afficher la version du modèle ;
- charger les pondérations ;
- recueillir/afficher les valeurs domaine par domaine ;
- demander le calcul au serveur ;
- afficher contributions et niveau ;
- soumettre à validation ;
- comparer l'historique.

Le JavaScript ne doit pas recalculer la formule officielle.

---

### `#/classement-sncc`

Page P1 spécialisée à créer/raccorder.

Rôle :
- afficher classement courant ;
- classe ;
- statut administratif ;
- risque ;
- justification ;
- date d'effet / fin ;
- historique ;
- reclassement motivé.

Les codes/classes/statuts/risques ne doivent pas être codés définitivement
dans le frontend tant que le dictionnaire institutionnel n'est pas finalisé.

---

### `regles-codification.html`

Ajouter une section **Modèles de scoring**.

| Endpoint | Élément UI | Permission |
|---|---|---|
| `GET /api/v1/scoring/models` | tableau Versions | `SCORING.LIRE` |
| `GET /api/v1/scoring/models/active` | badge modèle actif | `SCORING.LIRE` |
| `POST /api/v1/scoring/models` | Nouveau brouillon | `SCORING.ADMINISTRER_MODELE` |
| `GET /api/v1/scoring/models/{model_id}` | détail modèle | `SCORING.LIRE` |
| `PATCH /api/v1/scoring/models/{model_id}` | Modifier brouillon | `SCORING.ADMINISTRER_MODELE` |
| `POST /api/v1/scoring/models/{model_id}/clone` | Nouvelle version | `SCORING.ADMINISTRER_MODELE` |
| `POST /api/v1/scoring/models/{model_id}/publish` | Publier | `SCORING.ADMINISTRER_MODELE` |
| `POST /api/v1/scoring/models/{model_id}/retire` | Retirer | `SCORING.ADMINISTRER_MODELE` |
| `GET /api/v1/scoring/models/{model_id}/weights` | pondérations | `SCORING.LIRE` |
| `POST /api/v1/scoring/models/{model_id}/weights` | Ajouter domaine | `SCORING.ADMINISTRER_MODELE` |
| `PATCH /api/v1/scoring/models/{model_id}/weights/{weight_id}` | Modifier pondération | `SCORING.ADMINISTRER_MODELE` |
| `POST /api/v1/scoring/models/{model_id}/weights/{weight_id}/deactivate` | Désactiver | `SCORING.ADMINISTRER_MODELE` |
| `POST /api/v1/scoring/preview/{object_type}` | Simulateur sans écriture | `SCORING.LIRE` |

### Recette

Lors du raccordement :
1. remplacer données simulées/localStorage ;
2. charger modèles/pondérations API ;
3. tester données manquantes ;
4. vérifier modèle/version affichés ;
5. vérifier audit ;
6. tester historiques ;
7. marquer seulement ensuite le lot validé.

## Synchronisation API — Échéances / Alertes / Veille

**Backend : implémenté — non validé runtime.**

### Correction des horizons métier

Les anciennes mentions :

```text
12 mois / 6 mois / 3 mois / 1 mois / 15 jours
```

ne doivent plus être utilisées comme seuils métier principaux.

Le raccordement doit afficher le socle :

```text
180 jours
90 jours
30 jours
expiration
```

Le moteur restera paramétrable via `regles_metier`.

---

### `echeances.html` — `#/echeances`

| Endpoint | Composant UI | Permission |
|---|---|---|
| `GET /api/v1/echeances` | calendrier/liste/filtres | `ECHEANCES.LIRE` |
| `POST /api/v1/echeances` | Planifier une échéance | `ECHEANCES.GERER` |
| `GET /api/v1/echeances/{deadline_id}` | panneau détail | `ECHEANCES.LIRE` |
| `PATCH /api/v1/echeances/{deadline_id}` | Modifier | `ECHEANCES.GERER` |
| `POST /api/v1/echeances/{deadline_id}/complete` | Terminer | `ECHEANCES.GERER` |
| `POST /api/v1/echeances/{deadline_id}/cancel` | Annuler | `ECHEANCES.GERER` |
| `GET /api/v1/echeances/{deadline_id}/alertes` | lien Alertes liées | `ALERTES.LIRE` |

À afficher :
- Jours restants ;
- responsable ;
- type ;
- priorité ;
- alertes actives ;
- retard.

---

### `alertes.html` — `#/alertes`

| Endpoint | Composant UI | Permission |
|---|---|---|
| `GET /api/v1/alertes` | file/compteurs/filtres | `ALERTES.LIRE` |
| `POST /api/v1/alertes` | Alerte spéciale | `ALERTES.CREER` |
| `GET /api/v1/alertes/{alert_id}` | détail | `ALERTES.LIRE` |
| `PATCH /api/v1/alertes/{alert_id}` | Modifier active | `ALERTES.GERER` |
| `POST /api/v1/alertes/{alert_id}/assign` | Affecter | `ALERTES.AFFECTER` |
| `POST /api/v1/alertes/{alert_id}/resolve` | Résoudre/clôturer | `ALERTES.RESOUDRE` |
| `POST /api/v1/alertes/{alert_id}/notifications` | Notifier | `NOTIFICATIONS.CREER` |

Mapping niveau :

```text
1 Information
2 Surveillance
3 Urgence
4 Critique
```

Le lu/non-lu doit provenir des notifications du compte et non d'un champ
inventé dans `alertes`.

---

### Cloche de notifications

| Endpoint | Composant UI | Permission |
|---|---|---|
| `GET /api/v1/notifications/unread-count` | badge | `NOTIFICATIONS.LIRE` |
| `GET /api/v1/notifications` | menu cloche | `NOTIFICATIONS.LIRE` |
| `POST /api/v1/notifications/{notification_id}/read` | clic notification | `NOTIFICATIONS.LIRE` |
| `POST /api/v1/notifications/read-all` | Tout marquer lu | `NOTIFICATIONS.LIRE` |

Les endpoints de retry/transport sont réservés à l'administration/worker et
ne doivent pas apparaître dans l'interface utilisateur standard.

---

### `#/veille`

La page CVC devient le poste opérationnel de la Cellule de Veille.

#### Dashboard

| Endpoint | Rôle |
|---|---|
| `GET /api/v1/veille/dashboard` | cartes CVC |
| `POST /api/v1/veille/scans/daily` | bouton administratif Recalculer |

Cartes :
- dossiers ouverts ;
- échéances en retard ;
- alertes actives ;
- alertes critiques ;
- relances en attente ;
- notifications non lues.

#### Dossiers

| Endpoint | Rôle |
|---|---|
| `GET /api/v1/veille/dossiers` | file CVC |
| `POST /api/v1/veille/dossiers` | ouvrir un suivi |
| `GET /api/v1/veille/dossiers/{case_id}` | panneau dossier |
| `PATCH /api/v1/veille/dossiers/{case_id}` | priorité/responsable/prochaine action |
| `POST /api/v1/veille/dossiers/{case_id}/close` | clôture |

#### Relances

| Endpoint | Rôle |
|---|---|
| `GET /api/v1/veille/dossiers/{case_id}/relances` | historique |
| `POST /api/v1/veille/dossiers/{case_id}/relances` | nouvelle relance |
| `PATCH /api/v1/veille/dossiers/{case_id}/relances/{followup_id}` | édition |
| `POST /api/v1/veille/dossiers/{case_id}/relances/{followup_id}/response` | réponse/résultat |

#### Notes et rapports

| Endpoint | Rôle |
|---|---|
| `GET /api/v1/veille/rapports` | historique |
| `POST /api/v1/veille/rapports/generate` | générer indicateurs |
| `GET /api/v1/veille/rapports/{report_id}` | détail |
| `POST /api/v1/veille/rapports/{report_id}/validate` | visa Direction Technique |

### Recette

À faire au raccordement :
1. remplacer les mocks ;
2. tester scan/déduplication ;
3. tester seuils ;
4. tester affectation/résolution ;
5. tester cloche ;
6. tester relances ;
7. tester génération de rapport ;
8. vérifier audit ;
9. seulement ensuite marquer le lot validé.

## Correctif RBAC notifications

Un test réel de `GET /api/v1/notifications` a mis en évidence un `403 Permission insuffisante`.

Cause identifiée :
- la route exige correctement `NOTIFICATIONS.LIRE` ;
- le seed initial n'accordait cette permission qu'à une partie des rôles métier ;
- or cette route ne retourne que les notifications du compte connecté.

Correction appliquée dans :

```text
app/scripts/seed_watch_permissions.py
```

`NOTIFICATIONS.LIRE` est désormais accordé à tous les rôles métier prévus :
- ADMIN_HAUQE ;
- DIRECTION_TECHNIQUE ;
- POINT_FOCAL_BNEC ;
- VERIFICATEUR ;
- CONTROLEUR_FUCCS ;
- ADMIN_BNEC ;
- AGENT_COLLECTE ;
- CELLULE_VEILLE ;
- LECTEUR.

Les permissions sensibles restent limitées :
- `NOTIFICATIONS.CREER` : rôles opérationnels habilités ;
- `NOTIFICATIONS.TRANSPORT` : administration/transport uniquement.

Après intégration du correctif :

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_watch_permissions
```

puis recharger la session si le client conserve localement des permissions mises en cache.

Statut du correctif :
- code seed corrigé ✅
- bundle reconstruit ✅
- seed `app.scripts.seed_watch_permissions` exécuté ✅
- `GET /api/v1/notifications` passe désormais ✅
- raccordement complet de la cloche et des pages Veille encore à tester ⏳

## Synchronisation API — Gouvernance / Qualité / Continuité

**Backend : implémenté — non validé runtime.**

Avant raccordement/test :

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_governance_permissions
```

### `regles-codification.html`

Ajouter le panneau **Règles métier** :

```text
GET   /api/v1/governance/rules
GET   /api/v1/governance/rules/active/{logical_code}
POST  /api/v1/governance/rules
GET   /api/v1/governance/rules/{rule_id}
PATCH /api/v1/governance/rules/{rule_id}
POST  /api/v1/governance/rules/{rule_id}/clone
POST  /api/v1/governance/rules/{rule_id}/publish
POST  /api/v1/governance/rules/{rule_id}/retire
```

### `#/amelioration-continue`

Revues qualité :

```text
GET   /api/v1/quality/reviews
POST  /api/v1/quality/reviews
GET   /api/v1/quality/reviews/{review_id}
PATCH /api/v1/quality/reviews/{review_id}
POST  /api/v1/quality/reviews/{review_id}/validate
```

Plans d'action :

```text
GET   /api/v1/quality/action-plans
POST  /api/v1/quality/action-plans
GET   /api/v1/quality/action-plans/{plan_id}
PATCH /api/v1/quality/action-plans/{plan_id}
POST  /api/v1/quality/action-plans/{plan_id}/progress
POST  /api/v1/quality/action-plans/{plan_id}/close
```

### `#/decisions`

```text
GET   /api/v1/decisions
POST  /api/v1/decisions
GET   /api/v1/decisions/{decision_id}
PATCH /api/v1/decisions/{decision_id}
POST  /api/v1/decisions/{decision_id}/submit
POST  /api/v1/decisions/{decision_id}/pronounce
```

### `#/publications`

```text
GET  /api/v1/publications
POST /api/v1/publications
GET  /api/v1/publications/{publication_id}
POST /api/v1/publications/{publication_id}/submit
POST /api/v1/publications/{publication_id}/approve
POST /api/v1/publications/{publication_id}/publish
POST /api/v1/publications/{publication_id}/retire
```

### `rapports.html`

```text
GET  /api/v1/reports
POST /api/v1/reports
GET  /api/v1/reports/{report_id}
POST /api/v1/reports/{report_id}/start
POST /api/v1/reports/{report_id}/complete
POST /api/v1/reports/{report_id}/fail
```

### `journal-audit.html`

```text
GET /api/v1/audit/events
GET /api/v1/audit/events/{event_id}
```

Aucune route de mutation.

### `#/archives`

```text
GET  /api/v1/archives
POST /api/v1/archives
GET  /api/v1/archives/{archive_id}
```

### `#/sauvegardes`

```text
GET   /api/v1/backups
POST  /api/v1/backups/policies
PATCH /api/v1/backups/policies/{policy_id}
POST  /api/v1/backups/policies/{policy_id}/runs
GET   /api/v1/backups/{backup_id}
POST  /api/v1/backups/{backup_id}/complete
POST  /api/v1/backups/{backup_id}/fail
POST  /api/v1/backups/{backup_id}/restore-tests
```

### `#/incidents`

```text
GET   /api/v1/incidents
POST  /api/v1/incidents
GET   /api/v1/incidents/{incident_id}
PATCH /api/v1/incidents/{incident_id}
POST  /api/v1/incidents/{incident_id}/assign
POST  /api/v1/incidents/{incident_id}/resolve
POST  /api/v1/incidents/{incident_id}/close
```

### Raccordement des règles existantes

Le frontend n'est pas concerné directement, mais le backend Veille et Collecte
doit utiliser le nouveau `business_rule_resolver.py` afin de supporter
l'historique des versions malgré la contrainte UNIQUE sur `regles_metier.code`.

### Prochaine synchronisation

```text
/tableaux-de-bord/tactique
/tableaux-de-bord/strategique
/tableaux-de-bord/annuel
/barometre
/public
```

puis recette page par page de l'ensemble du projet.

## Synchronisation API — Pilotage / Tableaux de bord / Baromètre

**Backend : implémenté — non validé runtime.**

Avant test :

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_dashboard_permissions
```

### `index.html`

```text
GET /api/v1/dashboards/operational
GET /api/v1/dashboards/filters
GET /api/v1/dashboards/indicator-definitions
```

Remplacer les statistiques de `mock-data.js` par ces endpoints.

### `/tableaux-de-bord/tactique`

```text
GET /api/v1/dashboards/tactical?year=2026&month=7
```

### `/tableaux-de-bord/strategique`

```text
GET /api/v1/dashboards/strategic?year=2026&quarter=3
```

### `/tableaux-de-bord/annuel`

```text
GET /api/v1/dashboards/annual?year=2026
```

### `/barometre`

```text
GET /api/v1/barometer
```

ou avec période explicite.

### `/public`

```text
GET /api/v1/public/indicators
```

Le frontend public ne doit utiliser que cet endpoint. Il reste en 404 tant
que la règle de diffusion et la publication institutionnelle ne sont pas
publiées.

### Recette

Pour chaque page :
1. remplacer les mocks ;
2. tester permissions ;
3. vérifier filtres et périodes ;
4. vérifier agrégats et états vides ;
5. vérifier 403/404/422 ;
6. vérifier qu'aucune donnée individuelle ne sort de `/public` ;
7. seulement ensuite marquer la page validée.

## Synchronisation API — `profil.html` / Mon compte

**Backend : implémenté — non validé runtime.**

### Informations personnelles

```text
GET   /api/v1/me/profile
PATCH /api/v1/me/profile
```

Remplacer les valeurs codées en dur du hero et du formulaire par l'API.

Éditables :
- prénom(s) ;
- nom ;
- téléphone ;
- langue ;
- fuseau ;
- avatar.

Readonly :
- email ;
- fonction ;
- région ;
- statut ;
- rôles / permissions.

### Mot de passe

```text
POST /api/v1/me/password/change
```

### MFA

```text
GET  /api/v1/me/mfa
POST /api/v1/me/mfa/enable
POST /api/v1/me/mfa/verify
POST /api/v1/me/mfa/disable
```

Login MFA :

```text
POST /api/v1/auth/login
      ↓ si mfa_required
POST /api/v1/auth/mfa/verify
```

### Verrou automatique

Supprimer le stockage :

```text
hauqe-session-lock-settings
code privé dans localStorage
comparaison JS du code
```

et utiliser :

```text
GET   /api/v1/me/security-lock
PATCH /api/v1/me/security-lock
POST  /api/v1/me/security-lock/lock
POST  /api/v1/me/security-lock/verify
```

Le timer frontend peut rester, mais l'état et la vérification sont serveur.

Le frontend doit traiter :

```text
HTTP 423
SESSION_SCREEN_LOCKED
```

### Notifications

```text
GET   /api/v1/me/notification-preferences
PATCH /api/v1/me/notification-preferences
```

Mapping :

```text
Alertes critiques  → alertes_critiques
Affectations        → affectations
Corrections         → corrections
Rapports planifiés  → rapports_planifies
Résumé hebdomadaire → resume_hebdomadaire
```

### Sessions

```text
GET  /api/v1/me/sessions
POST /api/v1/me/sessions/{session_id}/revoke
POST /api/v1/me/sessions/revoke-others
```

Remplacer les trois sessions simulées Windows/Chrome/Android par les sessions
réelles.

### Mot de passe oublié

```text
POST /api/v1/auth/password/forgot
POST /api/v1/auth/password/reset
```

Réponse neutre, token 30 minutes, usage unique.

### Extension runtime

Le backend ajoute :

```text
preferences_utilisateur
securite_compte_utilisateur
verrous_session_utilisateur
jetons_securite_utilisateur
```

### Recette de la page

À valider :
1. profil réel ;
2. édition ;
3. mot de passe ;
4. activation/login/désactivation MFA ;
5. préférences ;
6. sessions/révocation ;
7. verrou 5/10/15/30 ;
8. 5 erreurs code privé ;
9. forgot/reset ;
10. états 401/409/422/423 ;
11. audit.

# PLAN FINAL DE RACCORDEMENT API ↔ FRONTEND

## Statut de passage

**GO pour le raccordement progressif.**

Le frontend reste visuellement avancé, mais une page n'est plus considérée fonctionnellement terminée tant que ses données et actions essentielles ne sont pas reliées aux endpoints FastAPI réels.

## Ordre de raccordement

```text
0. core/api.js + gestion globale des erreurs
1. Authentification + shell + verrou de session
2. profil.html / Mon compte
3. index.html / dashboard opérationnel
4. Entreprises
5. Organismes / Certifications / Documents
6. Collecte
7. Vérification
8. FUCCS
9. Validation / Intégration BNEC
10. Classification / INFC / SNCC
11. Échéances / Alertes / Notifications / Veille
12. Gouvernance / Qualité / Continuité
13. Tactique / Stratégique / Annuel / Baromètre / Public
```

## Contrat commun `api.js`

Toutes les pages doivent passer par la même couche :

```text
Authorization Bearer
JSON
loaders
erreurs 401 / 403 / 409 / 422 / 423 / 5xx
timeout réseau
permissions
prévention double soumission
```

Règles :
- `401` → session invalide/expirée, retour connexion ;
- `403` → permission insuffisante ;
- `409` → conflit métier affiché sans écraser l'état courant ;
- `422` → erreurs reliées aux champs du formulaire ;
- `423` + `SESSION_SCREEN_LOCKED` → écran global de code privé ;
- `5xx` → message serveur neutre + possibilité de réessayer.

## Sprint 1 — Authentification d'abord

Aucun écran métier n'est raccordé avant stabilisation de :

```text
POST /api/v1/auth/login
GET  /api/v1/me
POST /api/v1/auth/logout
POST /api/v1/auth/mfa/verify
POST /api/v1/auth/password/forgot
POST /api/v1/auth/password/reset
GET/POST /api/v1/me/security-lock...
```

Le verrou utilisateur et `AUTH_IDLE_TIMEOUT_MINUTES` restent deux mécanismes distincts.

## SMTP

L'e-mail réel est volontairement différé :

```text
IN_APP       → à raccorder/recetter maintenant
EMAIL        → peut rester EN_ATTENTE
SMTP         → phase infrastructure ultérieure
```

L'absence de SMTP ne bloque donc pas la connexion API ↔ frontend.

## Definition of Done par page

Une page passe de « maquette » à « raccordée » uniquement après :

- suppression des données simulées principales ;
- appels API centralisés via `core/api.js` ;
- actions réelles ;
- permissions ;
- états chargement/vide/erreur ;
- validation des erreurs API ;
- audit lorsque requis ;
- responsive conservé ;
- test fonctionnel ;
- mise à jour simultanée des deux feuilles de route.

## Première tranche à ouvrir

```text
core/api.js
   ↓
connexion.html
   ↓
/auth/login
   ↓
/me
   ↓
shell / permissions
   ↓
logout
   ↓
MFA / 423 verrouillage
   ↓
profil.html
```

# SPRINT ACTIF — CONNEXION + PROFIL + DESIGN LÉGER

## Statut

🟡 **Raccordement API en cours — non validé runtime**

Le premier sprint frontend raccorde désormais ensemble :

```text
connexion.html
profil.html
```

avant le dashboard métier.

Cette décision évite de valider une authentification incomplète sans tester
immédiatement :
- identité utilisateur ;
- sécurité ;
- sessions ;
- verrouillage ;
- MFA ;
- préférences.

## Connexion

Code raccordé à :

```text
POST /api/v1/auth/login
GET  /api/v1/me
POST /api/v1/auth/logout
POST /api/v1/auth/mfa/verify
```

Fonctions frontend implémentées en code :
- erreurs API ;
- chargement bouton ;
- « Rester connecté » ;
- retour à la page demandée avant login ;
- étape MFA conditionnelle ;
- 401/403/422/423 ;
- token centralisé.

## Profil

Valeurs simulées remplacées en code par :

```text
GET /api/v1/me/profile
```

Mise à jour :

```text
PATCH /api/v1/me/profile
```

Le frontend n'envoie que les champs réellement modifiés.

Sécurité :

```text
POST /api/v1/me/password/change
GET/POST /api/v1/me/mfa...
GET/PATCH/POST /api/v1/me/security-lock...
```

Préférences :

```text
GET/PATCH /api/v1/me/notification-preferences
```

Sessions :

```text
GET /api/v1/me/sessions
POST /api/v1/me/sessions/{id}/revoke
POST /api/v1/me/sessions/revoke-others
```

## Verrouillage localStorage supprimé du nouveau code

Ancienne logique :

```text
hauqe-session-lock-settings
code privé stocké côté navigateur
comparaison JS
```

Nouvelle logique :

```text
timer frontend
→ FastAPI
→ verrou PostgreSQL
→ HTTP 423
→ code vérifié côté serveur
```

## Animation / design

Le layout actuel est conservé pour ne pas mélanger UX et logique.

Une zone dédiée existe désormais :

```text
#authAnimationSlot
```

Le petit design / animation demandé sera appliqué à :
- `connexion.html` ;
- éventuellement des micro-transitions cohérentes sur `profil.html`.

L'animation doit rester :
- légère ;
- non bloquante ;
- responsive ;
- compatible `prefers-reduced-motion` ;
- indépendante de la réussite API.

## Recette

Statut :

```text
Syntaxe JS                       ✅
Connexion API                    ✅ code
Profil API                       ✅ code
Sessions API                     ✅ code
Verrou API                       ✅ code
MFA UI                           ✅ code

Validation navigateur            ⏳
Validation FastAPI réelle        ⏳
Animation/design final           ⏳
```

Une fois ce sprint validé, la page suivante reste :

```text
index.html — Dashboard opérationnel
```

# POINT D’INTÉGRATION LOCAL — AUTH + PROFIL

Base API frontend :

```text
http://localhost:8001
```

Fichier de configuration :

```text
app/static/js/core/config.js
```

Premier vertical :

```text
connexion.html
→ login réel
→ MFA éventuel
→ GET /me
→ profil.html
→ sécurité / préférences / sessions / verrou
```

Micro-design de connexion inclus :

```text
logo HAUQE + 🇹🇬
Piloter la conformité.
Anticiper les risques.
```

Animation :

```text
frappe → pause → effacement → pause → boucle
```

Statut :

```text
code préparé                 ✅
JS vérifié                   ✅
API localhost:8001 ciblée    ✅
recette navigateur/API       ⏳
```

Prochaine étape après validation Auth + Profil :

```text
index.html → dashboard opérationnel
```

# AJUSTEMENT PROFIL.HTML — BOUTON GLOBAL / AVATAR / MFA

## Statut

🟡 **Code frontend prêt — recette navigateur à effectuer**

### Bouton supérieur

Dans l'onglet Sécurité :

```text
Enregistrer la sécurité
```

enregistre désormais :
- changement du mot de passe si les trois champs sont renseignés ;
- configuration du code privé / délai de verrouillage si modifiée.

Le MFA reste volontairement une action séparée car il nécessite
un cycle d'activation + vérification TOTP.

### Avatar

Le bouton caméra ouvre maintenant un vrai sélecteur :

```text
PNG / JPG / JPEG
maximum 3 Mo
```

Flux :

```text
POST /api/v1/me/avatar
GET  /api/v1/me/profile
GET  /api/v1/me/avatar
```

La photo est affichée :
- dans le hero de `profil.html` ;
- dans la navbar après chargement.

Isolation de session : lors d'une déconnexion ou d'un changement de compte,
la navbar révoque l'URL Blob de l'avatar et revient immédiatement aux initiales.
Toute réponse asynchrone commencée par une ancienne session est ignorée. Une
photo ne doit jamais être réutilisée pour un autre compte.

Les appels API authentifiés utilisent `cache: no-store`, y compris le profil,
les préférences et les fichiers privés. Les réglages d'actualisation conservés
par l'interface sont limités à la session courante puis purgés à la
déconnexion ; la source de vérité reste `preferences_utilisateur` du compte
connecté.

### MFA

L'interface n'est pas désactivée.

Elle reste raccordée à :

```text
GET  /api/v1/me/mfa
POST /api/v1/me/mfa/enable
POST /api/v1/me/mfa/verify
POST /api/v1/me/mfa/disable
```

Elle sera utilisable dès que la configuration backend MFA sera appliquée.

### Autres corrections

- largeur Email / Mot de passe homogénéisée sur `connexion.html` ;
- loader global du nouveau frontend conservé ;
- API cible toujours `http://localhost:8001`.

### Tests techniques

```text
35 fichiers JavaScript : syntaxe ✅
runtime navigateur/API : ⏳
```

# AUDIT DESIGN AUTH / PROFIL — 27/07/2026

Statut : **code corrigé, recette navigateur locale à confirmer**.

Contrôles réalisés :

```text
29/29 CSS chargés                ✅
22/22 vues avec .page-content    ✅
35 JS — syntaxe                  ✅
connexion inputs homogènes       ✅ code
drapeau + typewriter             ✅ code
avatar circulaire / object-fit   ✅ code
responsive Auth / Profil         ✅ code
thème sombre Auth / Profil       ✅ code
loader global                    ✅ préservé
runtime localhost:8001           ⏳
```

Défaut corrigé : `auth-profile-api.css` existait mais n'était pas chargé dans
`index.html`. Les styles récents Auth / Profil étaient donc ignorés.

Prochaine recette :
1. connexion desktop ;
2. connexion mobile ;
3. profil avec avatar paysage et portrait ;
4. onglet Sécurité ;
5. mode sombre ;
6. sessions sur petit écran.

# LOT — MENU FLOTTANT UTILISATEURS ACTIFS

## Statut

🟡 **Code produit — recette navigateur à effectuer**

### Emplacement

Topbar globale, à côté des outils de shell.

### Composant

```text
👥 Actifs [N]
      ↓
Utilisateurs actifs
photo / initiales
nom
rôle
Actif maintenant / Actif il y a X min
```

### Comportement

- fenêtre : 15 dernières minutes ;
- ONLINE en vert ;
- RECENT en ambre ;
- maximum 6 lignes dans le menu ;
- avatar chargé par Bearer token ;
- fallback initiales ;
- `Vous` pour le compte courant ;
- actualisation automatique 60 s ;
- bouton d'actualisation ;
- lien `Voir tous les utilisateurs` → `#/utilisateurs`;
- menu masqué automatiquement sur 403.

### Responsive / thème

```text
desktop      bouton Actifs + badge
écran étroit bouton icône seulement
mobile       dropdown pleine largeur utile
dark mode    pris en charge
```

### Fichiers

```text
templates/index.html
static/js/core/app-shell.js
static/css/topbar-dropdowns.css
static/css/theme.css
```

### API

```text
GET  /api/v1/presence/users?minutes=15&limit=6
POST /api/v1/presence/heartbeat
GET  /api/v1/presence/users/{user_id}/avatar
```

### Tests

```text
35 JS — syntaxe                   ✅
affichage avec API réelle         ⏳
2 utilisateurs simultanés         ⏳
responsive                        ⏳
dark mode                         ⏳
```

# LOT 01 — DASHBOARD OPÉRATIONNEL + ACTION LOADER GLOBAL

## Statut

🟡 **Code frontend produit — recette navigateur/API locale à confirmer**

## Dashboard

Ancien comportement :

```text
window.HAUQE_MOCK
```

Remplacé sur `#/dashboard` par :

```text
GET /api/v1/dashboards/filters
GET /api/v1/dashboards/indicator-definitions
GET /api/v1/dashboards/operational
```

### Éléments raccordés

```text
KPI principaux                   ✅ code
statuts certifications           ✅ code
échéances 180/90/30/retard       ✅ code
actions prioritaires             ✅ code
certifications récentes          ✅ code
activité 6 mois                  ✅ code
INFC national moyen              ✅ code
horodatage de génération         ✅ code
```

### Filtres

```text
Période (7/30/60/90 jours)
Région / zone
Secteur
Norme
Organisme certificateur
```

Chaque changement recharge le backend.

### Navigation

```text
KPI → module concerné
priorité → Alertes / Échéances
certification récente → dossier certification
entreprise récente → dossier entreprise
Nouvelle collecte → formulaire collecte
```

### Correctif production — contenu et export du dashboard (14/09/2026)

- le message interne « Aucune information fictive… » ne doit jamais être
  affiché ; lorsqu’aucun certificat n’arrive à échéance, seul le constat
  « Aucun certificat à échéance dans les 180 jours » est rendu ;
- `ACTIF` et `ACTIVE` sont deux variantes historiques du même statut. Le
  dashboard les regroupe et affiche exclusivement **Active** ; aucune donnée
  métier existante n’est modifiée ;
- le bouton **Exporter Excel** télécharge un vrai fichier `.xlsx` mis en
  forme. Il présente les indicateurs, les certifications à échéance et les
  actions prioritaires avec leurs repères métier ;
- aucun UUID ne doit apparaître dans une action, une alerte, une échéance ou
  l’export. Les doublons techniques d’une même action sont regroupés avant
  affichage.

## Action Loader global

Nouveau module :

```text
static/js/core/action-loader.js
static/css/action-loader.css
```

Exposé comme :

```javascript
window.HAUQE_ACTION_LOADER
```

Fonctions :

```text
show()
update()
hide()
run()
bind()
```

Comportement :

- modal flottant institutionnel ;
- loader H animé ;
- texte dynamique ;
- points de suspension animés ;
- barre de progression indéterminée ;
- bouton temporairement désactivé ;
- `aria-busy` ;
- double `requestAnimationFrame` avant traitement ;
- `finally` pour restaurer l'UI ;
- dark mode ;
- responsive ;
- reduced-motion ;
- priorité inférieure au verrouillage de session.

Le module est utilisé dans le Dashboard pour :
- chargement initial ;
- filtres ;
- réinitialisation ;
- export CSV ;
- export graphique ;
- Nouvelle collecte ;
- navigations métier issues du Dashboard.

## Fichiers

Modifiés :

```text
templates/index.html
static/js/core/app-shell.js
static/js/app.js
```

Ajoutés :

```text
templates/views/dashboard.html
static/js/core/action-loader.js
static/css/action-loader.css
static/css/dashboard-api.css
```

## Tests

```text
syntaxe JS de tout le frontend     ✅
mock dashboard supprimé du flux    ✅
loader global installable          ✅ code
API réelle localhost:8001          ⏳
responsive visuel                  ⏳
dark mode visuel                   ⏳
```

## Étape suivante

Après recette du Dashboard :

```text
02 — Entreprises
```

## Correctif runtime — période Dashboard opérationnel

Erreur observée :

```text
GET /api/v1/dashboards/operational?days=Année+2026
422 Unprocessable Entity
```

Cause :
`/dashboards/operational` exige `days: int` entre 1 et 90.
L'ancienne vue pouvait encore exposer une valeur texte `Année 2026`.

Correctif :
- normalisation stricte de `days` côté frontend ;
- fallback sûr à 7 jours ;
- remplacement automatique des anciennes options par :
  7 / 30 / 60 / 90 jours ;
- aucune valeur annuelle envoyée à l'endpoint opérationnel.

Le tableau annuel reste réservé à :

```text
GET /api/v1/dashboards/annual?year=2026
```

Statut : code corrigé, recette navigateur à confirmer.

## Clôture Dashboard 01 — raccordements manquants

Statut : 🟡 code complété, recette navigateur finale à confirmer.

Supprimé :
- badge Alertes `12` fictif ;
- badges Vérifications `7` / Validations `4` fictifs ;
- contenu statique des échéances ;
- export local non souverain.

Raccordé :
- Exporter → `/api/v1/dashboards/operational/export` ;
- Nouvelle collecte → `#/collectes/nouveau` ;
- filtres chargés depuis `/api/v1/dashboards/filters` ;
- Réinitialiser → reset + rechargement backend ;
- échéances → `expiring_certifications` réel ;
- Actions d'urgence → `priority_actions` réel ;
- badge Alertes sidebar → KPI `active_alerts` réel ;
- navigations priorité → ressource réelle quand son type/id est disponible.

États vides :
- aucune échéance = message vide explicite ;
- aucune action = message vide explicite ;
- aucune donnée fictive conservée.

## AUDIT RUNTIME RÉEL — DASHBOARD 01

Statut corrigé : 🔴 **NON VALIDÉ / SOURCE FRONTEND À UNIFIER**

L'audit de la base frontend `app(1).zip` montre que le Dashboard historique est
encore présent dans `templates/legacy/index.html` et que `static/js/app.js` utilise
toujours `window.HAUQE_MOCK`.

Constats :
- `templates/views/dashboard.html` absent de la base originale auditée ;
- `mock-data.js` encore chargé globalement ;
- Exporter = toast ;
- filtres = statiques + toast ;
- échéances = valeurs HTML fictives ;
- Actions prioritaires = mock + badge 12 ;
- graphiques = mock ;
- certifications récentes = mock + faux identifiants numériques ;
- Nouvelle collecte navigue vers un formulaire encore basé sur localStorage.

Action bloquante avant validation :
identifier dans `app/main.py` le template réellement renvoyé par `/views/dashboard`,
puis rendre une seule vue Dashboard souveraine.

Le Dashboard 01 ne doit pas être marqué terminé avant cette unification et une recette
Network de tous ses appels.

## Correctif bloquant Dashboard 01 — route runtime réellement servie

Statut : 🟡 **correctif produit ; recette navigateur locale à confirmer**.

Audit de `app(2).zip` :

```text
#/dashboard
→ router.js
→ GET /views/dashboard
→ app/main.py
→ legacy/index.html   ❌
```

Alors que les fichiers API déjà présents sont :

```text
templates/views/dashboard.html
static/js/app.js
static/css/dashboard-api.css
static/js/core/action-loader.js
static/css/action-loader.css
```

Correction appliquée :

```text
app/main.py : dashboard → views/dashboard.html
```

Le shell charge désormais explicitement :

```text
/static/css/dashboard-api.css
/static/css/action-loader.css
```

Les badges shell fictifs `12`, `7`, `4` sont retirés. Le badge Alertes devient
`#navAlertBadge`, initialement masqué, puis alimenté par le KPI réel
`active_alerts` du Dashboard.

Important : `mock-data.js` reste chargé temporairement au niveau du shell car
d'autres pages non migrées en dépendent encore. Le nouveau `static/js/app.js`
Dashboard ne consomme plus `window.HAUQE_MOCK`.

Validation statique :

```text
app/main.py py_compile                         ✅
Jinja views/dashboard.html                     ✅
route dashboard ciblant views/dashboard.html  ✅
ancien AGROVITA absent de la nouvelle vue      ✅
TestClient complet dans l'environnement outil  ⛔ psycopg absent de l'environnement outil
Recette localhost:8001 utilisateur             ⏳
```

## ÉTAPE 02 — ENTREPRISES — RACCORDEMENT FRONTEND PRÉPARÉ

Statut : 🟡 code API réel, recette navigateur à confirmer.

Pages :
- `#/entreprises` : registre réel, KPI, filtres, recherche, tri, pagination, archives, export, archivage groupé ;
- `#/entreprises/{uuid}` : dossier réel (contacts, sites, offres, certifications, classification, FUCCS, documents, audit) ;
- `#/entreprises/nouveau` : création réelle ;
- `#/entreprises/modifier/{uuid}` : modification réelle et synchronisation contacts/sites/offres.

Mapping runtime obligatoire : `"entreprises": "views/entreprises.html"`.

Aucun `window.HAUQE_MOCK`, aucune entreprise AGROVITA, aucun faux ID numérique dans les scripts remplacés.

Import : volontairement non exposé ; aucun endpoint/permission d'import contrôlé n'existe dans le backend audité.

Loader d'action global utilisé pour appels longs et exports.

Tests code : node --check ✅. Runtime navigateur/API ⏳.

Prochaine étape : recette écran par écran puis seulement Étape 03 — Organismes.

## ÉTAPE 03 — ORGANISMES CERTIFICATEURS

Statut : 🟡 **Raccordement API produit — recette utilisateur à venir**

Pages raccordées :

```text
#/organismes
#/organismes/{uuid}
#/organismes/nouveau
#/organismes/modifier/{uuid}
```

Suppression des données fictives :
- Bureau Veritas / SGS / Ecocert codés en dur : supprimés ;
- KPI 14 / 11 / 2 / 1 / 143 : supprimés ;
- faux identifiants `/organismes/1` : supprimés ;
- accréditations et certificats de démonstration : supprimés ;
- brouillon localStorage du formulaire : supprimé.

Fonctionnalités :
- registre paginé ;
- recherche ;
- filtres statut/pays/accréditeur/domaine depuis PostgreSQL ;
- tri ;
- export serveur avec motif ;
- détail réel ;
- accréditations réelles ;
- certifications liées réelles ;
- documents réels et téléchargement sécurisé ;
- vérification de l'organisme ;
- création/modification ;
- ajout/modification d'accréditations ;
- dépôt de documents ;
- Action Loader sur les traitements réseau.

Étape suivante après validation :
`04 — Certifications`.

## ÉTAPE 05 — CAMPAGNES → MISSIONS → COLLECTE

Statut : 🟡 **raccordement API réel — recette navigateur à faire**

Pages :
- `#/collectes`
- `#/collectes/nouveau`
- `#/collectes/modifier/{mission_uuid}`

Décisions de raccordement :
- suppression complète de `localStorage` ;
- suppression des campagnes, agents, entreprises et certifications fictifs ;
- suppression du faux calcul frontend de complétude ;
- la complétude affichée vient uniquement de `fiches_collecte.taux_completude` ;
- la soumission reste contrôlée par la règle publiée
  `COLLECTE_COMPLETUDE` côté backend ;
- la collecte référence une entreprise existante du registre au lieu de
  recopier toute sa fiche identité ;
- offres et certifications déclarées sont persistées dans leurs tables ;
- documents déposés via le stockage privé ;
- une fiche soumise devient lecture seule ;
- une nouvelle révision est créée par l'endpoint métier existant.

Le formulaire est organisé en 6 niveaux :
1. mission ;
2. entreprise et déclarant ;
3. offres déclarées ;
4. certifications déclarées ;
5. preuves et observations ;
6. contrôle backend et soumission.

Aucun critère FUCCS n'est saisi ici.


## ÉTAPE 06 — VÉRIFICATION DOCUMENTAIRE
Statut : 🟡 vraie page raccordée — recette navigateur à faire.

Routes UI : `#/verifications` et `#/verifications/{dossier_uuid}`.
Le placeholder `governance-module` n'est plus utilisé.

Fonctions : dossiers réels, fiches SOUMISES éligibles, affectations, documents,
points, anomalies, confirmations externes, paramètres risque/priorité/synthèse,
clôture et réouverture.

## ÉTAPE 07 — CONTRÔLE FUCCS

Statut : 🟡 **grille dynamique raccordée — recette navigateur à faire**

Routes UI :

```text
#/controle
#/controle/{control_uuid}
```

L'ancienne maquette codée en dur est supprimée :
- 7 domaines JS ;
- 28 critères JS ;
- score maximal 56 JS ;
- calcul local du score ;
- `localStorage` du brouillon ;
- décision simulée.

Le nouvel écran charge :
- grille publiée ;
- rubriques ;
- critères ;
- note maximale de chaque critère ;
- commentaire obligatoire ;
- preuve obligatoire ;
- documents de la fiche source ;
- notes existantes ;
- constats existants.

Chaque note est sauvegardée par :

```text
PUT /api/v1/fuccs/controles/{control_id}/notes/{criterion_id}
```

Le score global reste calculé exclusivement côté backend.

La finalisation appelle :

```text
POST /api/v1/fuccs/controles/{control_id}/finalize
```

et reste distincte :
- de l'INFC ;
- du classement SNCC ;
- de la validation définitive BNEC.

## ÉTAPE 08 — VALIDATION + CORRECTIONS

Statut : 🟡 **raccordement réel — recette navigateur à faire**

Routes UI :

```text
#/validations
#/validations/{fiche_uuid}
```

Suppression de la maquette :
- entreprises fictives;
- validateurs fictifs;
- affectations de validations simulées;
- export fictif;
- statuts locaux;
- données statiques de file.

La nouvelle page expose :
- dossier issu d'un FUCCS finalisé;
- score FUCCS en lecture seule;
- décision N1;
- décision N2;
- corrections liées à chaque décision;
- resoumission;
- historique complet.

Les actions utilisent les endpoints existants :

```text
POST /validations/from-fiche/{fiche_id}/level-1
POST /validations/from-fiche/{fiche_id}/level-2
POST /validations/{validation_id}/corrections
POST /validations/{validation_id}/corrections/{correction_id}/resubmit
```

Aucun `window.prompt` n'est utilisé sur cette page : les décisions et
corrections passent par des dialogues UI structurés.

## ÉTAPE 09 — INTÉGRATION BNEC

Statut : 🟡 **vraie page raccordée — recette navigateur à faire**

Routes UI : `#/integrations` et `#/integrations/{integration_uuid}`.

Le placeholder `governance-module` est supprimé. La page suit le workflow `EN_ATTENTE → PRECONTROLE → INTEGRATION_EN_COURS → POSTCONTROLE → INTEGREE`; `ECHEC` reste terminal pour une tentative.

`elements_integration` reste un registre source→cible. Le frontend ne prétend pas créer automatiquement les ressources officielles et n'invente aucun code national.

## ÉTAPE 10 — SCORING / CLASSIFICATION ENTREPRISE / INFC / SNCC

Statut : 🟡 **vraies pages raccordées — recette navigateur à faire**

Routes UI : `#/scoring`, `#/infc`, `#/classement-sncc`.

L'ancienne maquette scoring fictive est supprimée : entreprises fictives, score `/56`, indice artificiel `/100`, seuils provisoires, graphiques simulés, décision locale, localStorage et exports simulés.

Le formulaire de calcul se construit depuis le modèle publié et ses pondérations. INFC et SNCC disposent de leurs pages réelles. Le design suit le Modern UI V2.

## ÉTAPE 11 — ÉCHÉANCES / ALERTES / NOTIFICATIONS / VEILLE

Statut : 🟡 **pages réelles raccordées — recette navigateur à faire**

### `#/echeances`

L'ancienne vue statique est remplacée par :
- calendrier réel ;
- vue liste ;
- filtres réels ;
- compteurs réels ;
- création manuelle d'une échéance liée à une certification réelle ;
- clôture et annulation motivées ;
- scan quotidien si l'utilisateur possède `VEILLE.SCANNER` ;
- charge visible par responsable.

### `#/alertes`

L'ancienne file fictive est supprimée :
- alertes PostgreSQL ;
- niveaux N1 à N4 ;
- filtres ;
- détail ;
- affectation ;
- résolution ;
- notifications IN_APP / EMAIL ;
- création d'une alerte spéciale sur une certification réelle.

La page contient également un onglet **Mes notifications**.

### Cloche globale

Le tableau JavaScript de notifications fictives de `app-shell.js` est
supprimé.

La cloche utilise :

```text
GET  /api/v1/notifications
POST /api/v1/notifications/{notification_id}/read
POST /api/v1/notifications/read-all
```

Un rafraîchissement léger est réalisé toutes les 60 secondes lorsque
l'utilisateur est authentifié.

### `#/veille`

Le placeholder `governance-module` est supprimé.

La page réelle expose :
- dashboard CVC ;
- scan quotidien ;
- dossiers de veille ;
- certification / entreprise / norme ;
- responsable ;
- relances ;
- réponses aux relances ;
- clôture ;
- rapports de veille ;
- génération des indicateurs ;
- validation Direction Technique.

Aucun PDF fictif n'est généré. La production documentaire reste réservée
au domaine Rapports.

Design aligné sur le langage visuel Modern UI V2.


## ÉTAPE 11 BIS — RÈGLES & CODIFICATION RÉELLES

`#/regles-codification` devient le centre de paramétrage réel.

Il permet :
- conception / validation / publication de COLLECTE_COMPLETUDE ;
- liste, création, édition de brouillon, clonage et publication des règles ;
- création des modèles de scoring ;
- gestion des pondérations ;
- publication avec référence d'approbation ;
- contrôle de readiness.

Aucune exigence de collecte n'est imposée automatiquement.

Le préremplissage Classification entreprise est un brouillon contrôlable,
jamais auto-publié.

Les six domaines INFC documentés peuvent être chargés dans un brouillon,
mais la formule opérationnelle et le mapping numérique restent à valider
avant publication institutionnelle définitive.

## PRÉPARATION MVP — FUCCS 24 + ADMINISTRATION

### Règles & codification
- bouton de préremplissage des 24 critères historiques ;
- dialogue de confirmation ;
- rechargement automatique après insertion.

### Utilisateurs
- suppression complète des comptes fictifs ;
- liste PostgreSQL réelle ;
- création de compte avec mot de passe initial ;
- attribution multi-rôles ;
- modification du compte ;
- activation/désactivation ;
- gestion des rôles dans le panneau latéral ;
- aucun export ni envoi d'invitation simulé.

## CORRECTIF MVP — BOUTON « NOUVEL UTILISATEUR »

Statut : 🟡 **corrigé statiquement — recette navigateur à exécuter**

Cause identifiée : Lucide transforme les balises `<i>` en `<svg>`. La validation du mot de passe recherchait ensuite uniquement `#passwordLengthCheck i` et `#passwordVarietyCheck i`. L'accès à un élément devenu absent déclenchait une exception avant `showModal()`, donnant l'impression que le bouton ne répondait pas.

Correctifs :
- ouverture du dialogue avant la génération automatique du mot de passe ;
- remplacement d'icône compatible avec `<i>` et `<svg>` ;
- formulaire maintenu ouvert même si le générateur cryptographique est indisponible ;
- message explicite permettant une saisie manuelle ;
- aucun changement d'API, de permission ou de base de données.

## Correctif — clic « Préremplir 24 critères » FUCCS

- cause identifiée : le bouton était physiquement désactivé lorsque
  `FUCCS.ADMINISTRER_GRILLE` n’était pas encore résolue dans `/api/v1/me` ;
  un bouton HTML `disabled` ne déclenche aucun événement de clic ;
- délégation d’événement persistante ajoutée sur les deux déclencheurs FUCCS ;
- branchement exécuté avant les chargements API secondaires de la page ;
- rechargement paresseux de `/api/v1/me` et des grilles FUCCS au clic ;
- retour utilisateur explicite pour permission absente, grille non sélectionnée,
  grille non brouillon, grille déjà remplie ou dialogue HTML absent ;
- ouverture du dialogue sécurisée ;
- aucun changement d’API ni de structure HTML requis ;
- validation `node --check` réussie ;
- recette navigateur à confirmer.

## Correctif — boucle de connexion après inactivité ou déconnexion

- cause : un `401` ou une révocation supprimait le Bearer token sans supprimer
  les caches de l'utilisateur et du profil ;
- la page `#/connexion` redirigeait alors vers le tableau de bord dès qu'un
  cache existait, même sans token ; le routeur revenait aussitôt à la connexion,
  provoquant une boucle de navigation et le scintillement des icônes ;
- correctif : `clearAccessToken()` efface désormais également les caches
  `hauqe-current-user-cache` et `hauqe-current-profile-cache` ;
- la redirection automatique depuis la connexion est conditionnée à la
  présence d'un token, puis à la validation de l'utilisateur côté API ;
- validation syntaxique JavaScript réussie avec le runtime Node du projet ;
- recette navigateur à exécuter : laisser expirer/révoquer une session, revenir
  à la connexion puis vérifier que les champs restent immédiatement utilisables.

## Correctif — formulaire de connexion bloqué après un échec

- cause : le chargeur automatique détectait la requête de connexion alors que
  le formulaire d'authentification gérait déjà lui-même son état `disabled` ;
- après une erreur, il restaurait le bouton « Se connecter » dans l'état
  désactivé mémorisé au départ de la requête ;
- correctif : les interfaces d'authentification (`connexion`, MFA et mot de
  passe oublié) sont exclues du chargeur automatique, y compris lorsqu'une
  action précédente est encore mémorisée ;
- validation syntaxique JavaScript réussie ;
- recette navigateur à exécuter : tester un mot de passe erroné, un token
  expiré et un code MFA erroné, puis vérifier qu'une nouvelle saisie est
  immédiatement possible sans actualiser la page.

Le même correctif couvre également `#sessionUnlockForm` lorsque le modal de
session sécurisée est affiché : un code privé erroné ne doit plus laisser le
bouton de déverrouillage désactivé.

## Correctif — changement de mot de passe

- après confirmation de `POST /api/v1/me/password/change`, le frontend efface
  immédiatement le token et les caches locaux ;
- un message « Mot de passe modifié. Reconnexion requise. » est affiché avant
  le retour vers `#/connexion` ;
- les éventuels réglages de verrouillage renseignés en même temps ne sont pas
  envoyés après le changement, car la session est déjà invalidée ; ils pourront
  être enregistrés après la nouvelle connexion ;
- validation syntaxique JavaScript réussie.

## Mise à jour — `#/echeances` : rappels configurables (01/09/2026)

La fiche d’échéance expose désormais un modal « Configurer les rappels » avec :

- interrupteur des rappels de l’agent affecté ;
- nombre de jours avant la date à partir duquel les rappels sont quotidiens ;
- interrupteur d’escalade aux administrateurs HAUQE au jour J ;
- liste d’exclusion individuelle des administrateurs pour cette seule échéance.

Le réglage est visible dans la fiche et ne modifie pas les autres échéances.

## Correctif — échéances et tableau de bord public (14/09/2026)

- le calendrier distingue visuellement une échéance **Terminée** (vert) et une
  échéance **Annulée** (gris violacé), indépendamment de son ancien retard ;
- le registre consolidé affiche des statuts métier lisibles, le motif d’une
  annulation et n’expose aucun UUID dans sa ligne ou sa fiche détail ;
- les rubriques « Échéances prioritaires » et la liste de la page appliquent
  le même nettoyage des libellés métier ;
- le bouton d’ouverture du registre est recréé et lié directement après chaque
  rendu, afin de rester réactif malgré le chargeur global d’actions ;
- la fiche restitue exactement les deux interrupteurs enregistrés du plan de
  rappel ; après enregistrement, elle se rouvre avec la valeur relue depuis
  l’API afin que le bloc « Notifications automatiques — Plan de rappel » soit
  immédiatement à jour ;
- le tableau de bord public masque les indicateurs non publiables en carte
  (valeur absente ou structurée) : la chaîne technique `[object Object]` ne
  doit jamais être affichée.

Aucune migration ni seed n’est requis pour ce correctif.

### Registre Entreprises — basculement Liste / Grille

Les boutons **Liste**, **Grille** et les actions de ligne reproduisent le procédé
validé dans **Gestion des campagnes**. Le rendu place d'abord un emplacement
neutre. JavaScript crée ensuite le vrai bouton avec `document.createElement()`,
une classe locale `company-action-button`, `pointer-events: auto`, un `z-index`
local, `data-no-action-loader` et un écouteur `click` direct et unique. Le mode
Liste/Grille s’appuie sur un état unique conservé localement.

Audit complémentaire : un fragment de page SPA ne doit pas être repris depuis
le cache avec un script plus récent. Le routeur charge donc les vues avec
`cache: "no-store"`. Chaque emplacement de ligne transporte une copie sérialisée
des informations de son entreprise, comme l'emplacement d'une campagne. Le
bouton reçoit donc directement l'entreprise nécessaire à son action et ne
dépend pas d'une nouvelle recherche dans le DOM au moment du clic.

## À éviter impérativement — UUID visibles (01/09/2026)

Les UUID sont des identifiants techniques. Ils ne doivent jamais apparaître
dans les pages utilisateur, modals, alertes, messages, champs préremplis,
infobulles ou e-mails. Utiliser à la place un libellé métier compréhensible
(entreprise, mission, certification, norme, organisme, date ou statut).

## Standard d’interface — modals HAUQE (01/09/2026)

La référence obligatoire pour tout nouveau modal ou formulaire opérationnel est
le thème déjà utilisé dans **Échéances**. Il comprend : en-tête avec icône et
contexte, corps aéré en sections, champs homogènes, bouton de fermeture compact
et pied de page avec actions alignées.

Ne pas créer un nouveau style isolé. Réutiliser les classes
`operational-form-dialog`, `operational-dialog-header`,
`operational-dialog-body` et `operational-dialog-footer`, puis adapter
uniquement l’icône et la couleur d’accent si nécessaire.

Écrans harmonisés avec cette règle : Nouvelle décision, Déposer un document,
Nouvelle confirmation, Nouvelle revue, Nouvelle politique, Nouvelle campagne
et Corriger la référence de mission. Le constructeur de modèle BNEC reste une
page et reprend la même hiérarchie visuelle sans être transformé en modal.

### Règle de lisibilité au zoom

La hauteur du modal est limitée à la fenêtre. Seul le corps du formulaire
défile ; l’en-tête et les actions restent accessibles. Cette règle couvre
Nouvelle décision, Déposer un document, Nouvelle confirmation, Nouvelle revue
et Nouvelle politique.

## Correctif — alertes et actions urgentes compréhensibles (01/09/2026)

Les alertes de dossier de veille et les actions urgentes du tableau de bord
affichent désormais l’entreprise, la certification concernée, la norme ou le
numéro de certificat lorsque ces informations existent. Un UUID est supprimé
du rendu même en cas de donnée ancienne incomplète.

## Correctif — actions de gestion des campagnes fiables au premier clic (03/09/2026)

- cause : les boutons d’action des lignes (« Modifier », « Désactiver »,
  « Voir les missions ») recevaient des écouteurs de clic recréés après chaque
  rendu de la liste. Lors d’un rafraîchissement ou de réponses réseau arrivant
  dans un ordre différent, une ligne pouvait momentanément ne plus porter
  l’écouteur attendu ;
- correctif : un unique écouteur délégué est désormais posé sur le conteneur
  stable des lignes. Il intercepte les actions des lignes actuelles et de toute
  ligne affichée après une recherche, une sauvegarde ou un rafraîchissement ;
- les actions « Modifier » et « Désactiver » transportent aussi les données
  métier de leur propre ligne, comme « Corriger » sur une mission liée. Elles
  ne dépendent donc plus d’un état JavaScript de liste qui pourrait être
  remplacé entre l’affichage et le clic ;
- les deux actions sont construites dans le DOM après les lignes et reçoivent
  chacune leur écouteur direct, sur le même principe que « Corriger » dans les
  missions liées. Elles n’utilisent plus la classe générique `more-button` ni
  le chargeur global d’action ;
- les réponses plus anciennes de chargement sont ignorées, afin qu’elles ne
  remplacent pas une liste plus récente ; la désactivation est aussi protégée
  contre les doubles envois ;
- à éviter : attacher les événements directement aux éléments recréés par
  `innerHTML` lorsqu’une liste est susceptible d’être actualisée. Préférer la
  délégation sur un parent durable ou recréer les écouteurs de façon atomique.

Un second facteur a été neutralisé : l’actualisation collaborative silencieuse
ne s’exécute plus sur `#/campagnes-collecte`. Cette page comporte des actions
immédiates et des modals ; elle ne doit jamais être remplacée en arrière-plan
pendant qu’un utilisateur vise une icône. L’actualisation reste disponible
uniquement sur demande explicite via son bouton dédié.

Enfin, le routeur identifie chaque navigation et ignore toute réponse devenue
ancienne avant d’insérer son HTML ou de lancer son script. Les paramètres de
version des scripts sont ajoutés avec `&` lorsqu’une URL possède déjà `?` :
cela évite de réutiliser un code JavaScript en cache ou d’associer un script à
une page différente après deux navigations rapprochées.

## Incident transversal — boutons initiaux inactifs ou exigeant plusieurs clics (03/09/2026)

### Symptôme à rechercher sur chaque écran

Un bouton présent dès le premier affichage d’une page peut sembler actif, mais
ne déclencher son modal, sa confirmation ou son action qu’après plusieurs
clics, voire seulement après avoir actualisé la page. À l’inverse, un bouton
créé après une recherche, le déploiement d’un détail ou l’ajout d’une ligne
peut fonctionner immédiatement. Ce comportement est **bloquant** pour la
recette et la formation : aucun utilisateur ne doit avoir à cliquer plusieurs
fois ou actualiser pour utiliser une action.

### RÈGLE PRIORITAIRE ET OBLIGATOIRE — modèle de correction validé

> **Cette règle est la référence primordiale pour corriger les boutons non
> réactifs sur toutes les autres pages du SNGSC / HAUQE Certif. Ne pas déclarer
> un bouton corrigé avec une autre méthode tant que ce modèle n'a pas été essayé
> et validé au premier clic.**

Le cas des campagnes a confirmé une interaction fragile entre :

- les boutons d’icône initiaux utilisant la classe générique `more-button` ;
- leur branchement pendant le premier rendu de liste ;
- l’état global de chargement et, plus généralement, les écrans SPA dont les
  scripts peuvent être remplacés après la page.

La correction de référence est celle validée successivement sur
`#/campagnes-collecte` puis sur `#/entreprises` :

1. rendre les lignes de données ;
2. rendre dans chaque ligne un **emplacement neutre** contenant une copie
   sérialisée des seules données métier utiles à l'action ;
3. après le rendu, relire ces emplacements et créer chaque vrai bouton avec
   `document.createElement("button")` ;
4. utiliser une classe locale explicite par module, par exemple
   `campaign-action-button` ou `company-action-button`, et ne pas réutiliser
   `more-button` pour ces actions ;
5. garantir en CSS `cursor: pointer`, `pointer-events: auto`,
   `position: relative` et `z-index: 1` ; l'icône SVG interne porte
   `pointer-events: none` ;
6. poser `data-no-action-loader="true"` lorsque le clic ouvre un modal, un menu,
   une confirmation ou une autre interface locale ;
7. poser sur le bouton créé un écouteur `click` **direct et unique** avec
   `preventDefault()` et `stopPropagation()` ;
8. fournir directement au gestionnaire la donnée désérialisée de son
   emplacement, sans rechercher à nouveau la ligne métier au moment du clic ;
9. relancer cette hydratation immédiatement après chaque nouveau rendu,
   recherche, filtre, pagination ou actualisation de la liste ;
10. empêcher une ancienne réponse réseau de remplacer un rendu plus récent.

Le même procédé s'applique aux commandes Liste/Grille ou aux boutons présents
au chargement lorsqu'ils présentent le même défaut : emplacement neutre dans le
template, création par la fabrique locale, puis écouteur direct. Une délégation
d'événements ou un simple `onclick` ajouté au HTML ne constitue plus la
correction de référence pour ce bug.

Patron minimal obligatoire :

```javascript
function createActionButton({ label, iconName, handler }) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "module-action-button";
  button.setAttribute("data-no-action-loader", "true");
  button.setAttribute("aria-label", label);
  button.innerHTML = `<i data-lucide="${iconName}"></i>`;
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    handler();
  });
  return button;
}

function hydrateActionButtons() {
  document.querySelectorAll("[data-action-slot]").forEach((slot) => {
    const payload = deserialize(slot.dataset.actionPayload);
    slot.replaceChildren(createActionButton({
      label: "Exécuter l'action",
      iconName: "pencil",
      handler: () => openAction(payload),
    }));
  });
}
```

**Validation terrain du 14/09/2026 :** le modèle appliqué aux boutons Liste,
Grille et actions de ligne de la page Entreprises a été confirmé fonctionnel
par l'utilisateur. Cette validation fait de ce patron la base obligatoire de
l'audit et des corrections des autres pages.

**Application en cours — Échéances :** les actions injectées dans le calendrier,
la liste de la période, les échéances prioritaires et le registre consolidé ont
été converties au même patron. Chaque zone rend un emplacement neutre avec
l'identifiant sérialisé, puis `hydrateDeadlineActionButtons()` fabrique le
bouton local, son écouteur direct et son style propre. La classe générique
`more-button` n'est plus utilisée pour ces actions. À contrôler en recette au
premier clic après chargement, recherche, filtre et changement de période.

**Application — Référentiels et nomenclatures (21/09/2026) :** les crayons de
modification des valeurs de référentiel sont rendus dans un emplacement neutre.
`hydrateReferenceEditButtons()` désérialise la valeur de la ligne et crée le
bouton `reference-edit-button` avec un seul écouteur `click` direct. La version
du JavaScript et de la feuille de style est incrémentée pour empêcher le cache
du navigateur de conserver l'ancienne logique. Recette attendue : ouverture de
la modification au premier clic, après recherche, filtre, changement de
catégorie et enregistrement d'une valeur.

**Application — Zones administratives (21/09/2026) :** les boutons de ligne
« Modifier » et « Changer le statut » sont rendus dans des emplacements neutres.
`hydrateZoneActionButtons()` crée leurs boutons locaux et leurs écouteurs
directs après chaque chargement ou filtre. Les commandes fixes Nouvelle zone,
Actualiser, Réinitialiser et Fermer sont également liées avec un écouteur direct
et `data-no-action-loader="true"`. Les versions CSS/JavaScript sont incrémentées.
Recette attendue : toutes les actions répondent au premier clic, y compris après
recherche, filtre par type/statut et actualisation du référentiel.

**Application — Règles et codification (21/09/2026) :** une protection commune
est appliquée à chaque bouton de la page, y compris aux actions créées après
chargement d'une règle, d'un modèle de scoring ou d'une grille FUCCS.
`stabilizeRuleButtons()` ajoute `data-no-action-loader="true"`, un style local
avec surface cliquable et focus visible ; un observateur couvre immédiatement
les boutons ajoutés par les rendus dynamiques. Les versions CSS/JavaScript sont
incrémentées. Recette attendue : chaque commande et action de ligne répond au
premier clic dans les six onglets.

### Audit obligatoire du menu

Auditer chaque entrée de la barre latérale et ses sous-écrans selon ces blocs :

1. Pilotage : Tableau de bord, Alertes, Échéances ;
2. Registre national : Entreprises, Certifications, Organismes, Zones,
   Collectes, Vérifications, Contrôle FUCCS, Validations, Intégrations BNEC ;
3. Analyse : Scoring, INFC, SNCC, Veille, Décisions et actions ;
4. Pilotage avancé : tableaux tactique, stratégique, annuel, baromètre,
   tableau public, rapports ;
5. Administration, Référentiels, Règles et codification, Publications,
   Documents, Échanges organismes ;
6. Audit et traçabilité : Journal, Mises à jour BNEC, Qualité des données,
   Sauvegardes ;
7. Profil, préférences, connexion, MFA, mot de passe oublié et session
   sécurisée.

Pour chaque page, tester au minimum : action initiale au premier clic,
ouverture/fermeture/réouverture de modal, action après recherche ou filtre,
action après actualisation de la liste et absence de bouton bloqué après une
erreur API. Consigner l’écran, le bouton, le résultat et la correction dans
cette feuille avant de passer au bloc suivant.

### Recette en cours — bloc 7 : Compte, sécurité et NavBar (03/09/2026)

Le bouton de sélection de la photo sur `#/profil` applique désormais le patron
prioritaire validé : emplacement neutre dans `.profile-avatar`, création du
vrai bouton par `createAvatarActionButton()`, classe locale
`profile-avatar-action-button`, `pointer-events: auto`, `z-index` local, icône
non cliquable et écouteur direct unique qui ouvre l'input fichier. La cause
structurelle était un emplacement placé hors de `.profile-avatar` : les règles
CSS définissant la surface cliquable de `.profile-avatar button` ne pouvaient
donc pas s'appliquer. Recette utilisateur au premier clic encore requise.

Premier risque corrigé sur `#/profil` : les onglets, l’enregistrement, le
changement d’avatar et la déconnexion étaient branchés seulement après le
chargement asynchrone du profil, de l’avatar et des données de l’onglet. Ils
sont maintenant branchés immédiatement. Si les données sont encore en cours
de lecture, le premier clic affiche une information au lieu d’être perdu.

La NavBar est permanente, mais ses commandes locales (menu mobile, thème,
présence, notifications, menu utilisateur et marquage des notifications) sont
désormais explicitement exclues du chargeur automatique global. Elles ouvrent
ou ferment leur interface dès le premier clic ; les appels réseau éventuels
restent ensuite silencieux et ne neutralisent pas la commande déclencheuse.

Lorsqu’un contrôle initial de la NavBar est reconstruit pour neutraliser un
ancien écouteur, toute référence vers un élément enfant doit être relue depuis
la nouvelle instance. Cette règle est appliquée au compteur de présence
`#presenceCount` : il est désormais rattaché au nouveau bouton de présence,
afin que son total continue de se mettre à jour après la correction de
réactivité.

Le formulaire `#/mot-de-passe-oublie` est également lié avant la résolution du
module API. La demande de lien, le renvoi et la définition du nouveau mot de
passe interceptent donc immédiatement leur première soumission, puis attendent
le client API si nécessaire ; aucune soumission native ou clic perdu ne peut
survenir pendant l’initialisation.

Restent à recetter dans ce bloc : connexion avec erreur, MFA avec erreur et
retour, demande/réinitialisation du mot de passe, verrouillage/déverrouillage
de session, préférences, sessions actives et fermeture/réouverture de tous les
menus de la NavBar.

**État de recette révisé : bloquant.** Les corrections initiales n’ont pas
encore démontré une réactivité fiable sur l’ensemble du bloc. Ne pas déclarer
Profil, préférences ou NavBar conformes tant que chaque bouton visible au
chargement, menu déroulant, action d’onglet, modal et soumission de formulaire
n’a pas été contrôlé au premier clic, puis après fermeture et réouverture.

#### Registre de contrôle — bloc 7

| Écran / zone | Contrôles à vérifier | État |
|---|---|---|
| NavBar | menu mobile, thème, présence, actualisation de présence, notifications, marquer comme lu, menu utilisateur, raccourcis compte, déconnexion | 🟡 instances reconstruites et écouteurs directs — recette navigateur requise |
| Profil — structure initiale | onglets, enregistrer, photo, déconnexion | 🟡 instances reconstruites après lecture du profil — recette navigateur requise |
| Profil — sécurité | mot de passe, MFA, code privé, test de verrouillage, sessions | 🟡 actions générées après rendu — recette navigateur requise |
| Profil — préférences | choix de notification, actualisation et enregistrement | 🟡 actions générées après rendu — recette navigateur requise |
| Connexion / MFA | afficher mot de passe, retour, soumettre, erreurs | 🟡 écouteurs synchrones — recette avec cas réel requise |
| Mot de passe oublié | envoyer, renvoyer, enregistrer le nouveau mot de passe, retours | 🟡 formulaires liés avant API — recette avec cas réel requise |
| Session sécurisée | afficher code, déverrouiller, déconnexion | 🟡 écouteurs synchrones — recette avec cas réel requise |

### Ergonomie des notations FUCCS, classification, INFC et SNCC (21/09/2026)

Objectif : guider l'utilisateur dans sa saisie sans introduire de règle métier,
de seuil, de pondération ou de décision qui ne serait pas publié et validé par
la HAUQE. Cette évolution est strictement frontend : **Base PostgreSQL
modifiée : non ; migration : aucune.**

- **FUCCS** : chaque critère conserve sa description, ses exigences de preuve
  et son maximum issu de la grille publiée. Pour les critères notés sur 2, les
  choix 0, 1 et 2 sont désormais explicités respectivement par « Non conforme
  », « Partiellement conforme » et « Conforme ». Les autres échelles ne sont
  pas interprétées par l'interface.
- **Classification entreprise et INFC** : le formulaire rappelle le mode du
  modèle actif, les bornes de saisie disponibles et l'état d'avancement de la
  saisie. La prévisualisation affiche le score, le maximum lorsqu'il est
  déterminable par le modèle, la progression et la version du modèle. Une
  saisie directe reste disponible uniquement si le modèle publié l'autorise.
- **SNCC** : l'écran et le formulaire distinguent clairement classe, statut
  administratif et risque. Les libellés A+ à D, VA à VE et R1 à R5 servent de
  repères opérationnels ; ils doivent être confirmés par la HAUQE si une
  définition institutionnelle différente est publiée. Le SNCC reste saisi et
  justifié, sans conversion automatique depuis l'INFC.

Recette attendue : ouvrir un dossier FUCCS, une évaluation entreprise, un
calcul INFC et un classement SNCC ; vérifier que les textes d'aide, limites,
aperçus et sélections restent lisibles sur ordinateur et mobile, et que le
résultat final provient toujours du backend et du modèle publié.

**Correctif critique — cache et boutons Scoring/INFC (21/09/2026) :** tout
script de page qui appelle une nouvelle fonction d'un module JavaScript partagé
doit versionner également l'import de ce module. Versionner seulement la route
de la page peut laisser le navigateur charger une ancienne copie du module et
faire échouer le clic avec une fonction absente. Les boutons dynamiques
« Évaluer », « Calculer » et « Recalculer » suivent aussi le patron validé de
Gestion des campagnes : emplacement neutre, création du vrai bouton après le
rendu, `data-no-action-loader`, écouteur direct unique et propagation arrêtée.
Recette obligatoire au premier clic, puis après actualisation de la liste.

**Guidage par règle publiée — Scoring et INFC (21/09/2026) :** les blocs
d'aide de `#/scoring` et `#/infc` doivent être produits depuis le modèle
publié réellement actif, jamais depuis un seuil figé dans le frontend. La
classification affiche les classes et leurs plages issues de `classes` ; l'INFC
explique le mode de calcul, les bornes de saisie, les pondérations et les
niveaux lorsqu'ils sont présents. Pour le modèle INFC pondéré, chaque domaine
est saisi sur 100 ; une valeur telle que 15 correspond à son poids relatif et
non à une note maximale. L'aperçu de saisie calcule alors la moyenne pondérée
de manière informative ; le résultat officiel reste celui du backend.

Le modèle actif au contrôle du 21/09/2026 est `INFC-03` v1.3 : moyenne pondérée
sur 100, six domaines obligatoires (poids 20, 20, 20, 15, 15, 10) et niveaux
1 : 85–100, 2 : 70–84,99, 3 : 50–69,99, 4 : 0–49,99. La règle de
classification active est `CONFORME` à partir de 85, `A_SURVEILLER` de 60 à
moins de 85, et `NON_CONFORME` sous 60. Ces valeurs sont affichées depuis les
règles publiées et changeront avec une nouvelle version de modèle.

Pour préserver la lisibilité opérationnelle, les pages affichent uniquement
des cartes colorées de seuils/niveaux, avec une lueur légère (vert, ambre,
rouge selon la position dans la règle). Les explications de méthode, de poids,
de prévisualisation et de validation sont regroupées dans les guides PDF
Scoring et INFC accessibles depuis chaque page. Ces guides rappellent que les
cartes restent la source dynamique de la version publiée.

### Parcours de dossier Collecte → BNEC (21/09/2026)

Les fiches de collecte et les écrans de détail **Vérification**, **Contrôle
FUCCS**, **Validation** et **Intégration BNEC** affichent le même parcours
opérationnel en six étapes : collecte, vérification, contrôle FUCCS, validation
N1, validation N2 et intégration BNEC. Chaque étape est déterminée par l'état
réel enregistré côté serveur et porte l'un des statuts lisibles : terminée, en
cours, à faire ou bloquée.

La carte en tête indique la prochaine action attendue et le nombre d'étapes
restantes. Un ajournement ou rejet N1/N2, ou un contrôle/intégration bloqué,
est explicitement signalé sans afficher d'UUID. Cette fonction est de lecture
seule : **Base PostgreSQL modifiée : non ; migration : aucune.**

### Saisie de collecte limitée aux affectations (23/09/2026)

La restriction est appliquée par l'API, donc elle protège également un appel
direct hors interface. Dans les formulaires de collecte, une tentative de
création, modification, réinitialisation, soumission, révision ou ajout d'une
offre/certification par un agent non affecté doit afficher le message `403`
renvoyé par le serveur : une affectation active à la mission est requise.

L'amélioration UX ultérieure consiste à ne proposer à l'agent collecteur que
ses missions affectées ; elle ne doit jamais remplacer le contrôle côté
serveur. **Base PostgreSQL modifiée : non ; migration : aucune.**

### Catalogue des rôles à la création d'utilisateur (24/09/2026)

La fenêtre **Utilisateurs → Nouvel utilisateur** affiche tous les rôles dont
le statut est actif, y compris les données historiques écrites `ACTIVE` au
lieu de `ACTIF`. Le nombre de rôles disponibles est affiché dans la section
afin de rendre une absence ou un filtre visible. Un rôle inactif demeure
volontairement non attribuable. Le script et la feuille de style sont
versionnés pour empêcher qu'une copie navigateur ancienne masque le correctif.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Rapports et exports — bilans périodiques BNEC (01/10/2026)

- La rubrique « Rapports et exports » propose en tête trois bilans : mensuel,
  trimestriel et annuel. L'année et le mois/trimestre choisis sont transmis au
  serveur ; « Vérifier les indicateurs » montre la période réelle et les valeurs
  calculées avant « Générer et télécharger ».
- Les tableaux de bord avancés mensuel, trimestriel et annuel offrent un accès
  direct à la création du bilan en conservant la période affichée. Le PDF,
  l'Excel ou le CSV généré est conservé dans l'historique et retéléchargeable.
- Les exports de registres interrogent les données courantes et les filtrent
  selon la période métier affichée. Ils ne sont pas archivés comme bilans BNEC.
  Aucun UUID ne doit être montré comme nom du demandeur.
- Vérifier les trois types de bilan, l'aperçu, le premier clic de génération,
  le téléchargement et l'absence de débordement à 100 % et 200 % de zoom.
  Recette : `tests/frontend/bnec_reports_smoke.cjs`.
- L'aperçu ne doit jamais exposer une sérialisation technique du type
  « Indicateurs clés 1 / Valeur ». Afficher d'abord « En bref », puis un
  libellé métier et une explication pour chaque chiffre. Les textes longs
  doivent revenir à la ligne, y compris à fort zoom.
- Recette du 01/10 : l'aperçu mensuel/trimestriel/annuel doit s'ouvrir
  plusieurs fois sans rechargement. Une requête lente affiche « Calcul… » ;
  un changement de type ou de période invalide son ancienne réponse pour
  qu'un aperçu trimestriel tardif n'écrase pas l'annuel. Distinguer « Aperçu
  du bilan BNEC » de « Aperçu de l'export » (registre courant). Le modal de
  ce dernier garde ses actions accessibles par défilement en hauteur réduite.
- L'aperçu annuel indique visiblement « bilan provisoire » et la date d'arrêté
  quand l'année est en cours. Il ne doit pas faire passer le 31 décembre futur
  pour une date d'observation effective. Recette avec une année en cours et
  des trimestres sans résultat INFC validé.
- Ne jamais retirer ou masquer les commandes du catalogue historique en
  ajoutant un nouveau bilan. La tentative du 01/10/2026 avait caché
  « Périmètre et filtres », « Contenu du rapport » et « Enregistrer la
  configuration » ; ces blocs sont restaurés et désormais raccordés.
  Un bouton de sauvegarde ne doit jamais annoncer un succès fictif.

**Base PostgreSQL : schéma inchangé ; migration : aucune ; seed : aucun.**

### Dossiers certification et organisme — preuves, statut et tableau de bord (27/09/2026)

**Dossier entreprise — justificatifs de collecte (27/09/2026) :** l’onglet Documents affiche désormais à la fois les documents déposés directement sur l’entreprise et les justificatifs généraux de toutes ses fiches de collecte explicitement liées. Chaque ligne indique « Document de l’entreprise » ou « Collecte · révision N » et conserve le téléchargement privé existant. Les boutons d’ajout et de téléchargement restent branchés au rendu de l’onglet ; version du script incrémentée pour éviter l’ancien cache navigateur. Une fiche historique sans `entreprise_id` explicite n’est pas rattachée par supposition.

**Rectificatif interface dépôt de preuve (27/09/2026) :** le bouton « Déposer la preuve » ouvrait auparavant une erreur de dossier si aucun fichier n'était sélectionné. Le champ fichier est maintenant visible et présenté comme étape 1, le dépôt comme étape 2. Un clic prématuré ouvre le sélecteur de fichier ; le nom sélectionné et les erreurs sont affichés dans le bloc de dépôt. Le bandeau général n'intitule plus ces erreurs « Impossible de charger le dossier ». Ressources front-end versionnées pour éviter l'ancien script en cache.

- L’onglet **Documents** de l’organisme distingue ses propres pièces et les preuves des certifications délivrées. Il s’agit d’une vue liée, sans duplication des fichiers.
- La fiche certification permet le dépôt d’une preuve directement sur le certificat. Une pièce ancienne attachée uniquement à la fiche de collecte n’est pas attribuée automatiquement à un certificat ambigu : l’utilisateur doit déposer la bonne pièce sur la certification concernée.
- La décision de vérification de l’organisme se fait dans un modal HAUQE avec deux choix explicites, **Reconnu** et **Pas encore vérifié**, et un motif obligatoire. Boutons liés dès l’ouverture de la page ; contenu et actions restent accessibles au zoom grâce au défilement interne.
- La liste du tableau de bord inclut désormais les certificats expirés ; le nombre de jours est calculé depuis la date courante. Le `0` des échéances à 90 jours ne comprend pas les certificats déjà expirés, affichés séparément.
- Régression à vérifier après chaque retouche : premier clic des boutons, validation du modal, défilement au zoom, actualisation des pièces et des statuts.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Collecte — organisme certificateur et preuves par certification (27/09/2026)

Dans **Collecte & contrôle > Nouvelle collecte > Certifications déclarées**,
la saisie de l’organisme certificateur déclenche une recherche après deux
caractères. Les organismes du registre sont proposés sous le champ ; un clic
les rattache à la déclaration. Si aucun résultat n’existe — ou si l’organisme
recherché n’est pas dans la liste — le lien discret **Précréer « … »** ouvre le
modal HAUQE existant, prérempli avec le nom saisi. Le gros bouton de
précréation affiché dans chaque ligne est retiré.

Chaque certification déclarée possède désormais sa propre zone **Preuves de
cette certification**. L’ajout enregistre au besoin la déclaration brouillon,
puis rattache le fichier à cette ligne plutôt qu’à toute la fiche. Les preuves
générales restent disponibles dans l’étape **Preuves & observations**.

Le rendu suit le langage visuel HAUQE : cartes compactes, libellés lisibles,
choix existants clairement séparés, action de précréation secondaire et prise
en charge du thème sombre. Aucun grand bouton structurel ne doit encombrer une
ligne de certification.

Correctif visuel du 27/09/2026 : `.organisme-lookup` et
`.declared-cert-evidence` sont des enfants directs de la grille des
certifications déclarées. Leur classe `full` ne suffisait pas, car les règles
de largeur complète ne ciblaient que `.form-field.full`. Les deux blocs
occupent explicitement `grid-column: 1 / -1`, à toutes les largeurs et au
zoom. La zone de preuve est placée après les autres champs. À éviter : ajouter
un nouveau bloc dans une grille à 13 colonnes sans vérifier son placement
réel au navigateur ou sur capture d’écran.

Dans **Règles et codification > Classement SNCC**, la matrice commence vide
lorsqu’aucun brouillon n’existe. Le préremplissage affiche alors ses cinq
classes dans le tableau, un état de réussite visible et un petit modal HAUQE
expliquant que les valeurs restent modifiables et ne sont pas enregistrées.
Le bouton **Publier la matrice** est toujours visible : il devient disponible
après enregistrement du brouillon et une aide indique l’étape attendue.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Compte et sécurité — lien de réinitialisation limité à trois minutes (27/09/2026)

Le courriel de réinitialisation HAUQE indique désormais clairement : « ce
lien est valable 3 minutes et une seule fois ; passé ce délai, il ne sera plus
valable ». La durée affichée provient de la configuration serveur : elle ne
peut donc pas diverger de l’expiration réellement vérifiée par l’API.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Collecte — codes proposés pour supprimer la saisie répétitive (27/09/2026)

Dans **Nouvelle campagne**, **Nouvelle mission**, **Nouvelle collecte** et les
deux créations de **zone administrative**, l'interface propose immédiatement
le prochain code lisible : `HAUQE-CAMP-AAAA-NNNN`,
`HAUQE-MIS-AAAA-NNNN` ou `HAUQE-ZON-AAAA-NNNN`.

Le champ n'est jamais bloquant : l'utilisateur peut le corriger si une règle
interne le demande et, si la proposition est momentanément indisponible, le
serveur l'attribue à l'enregistrement. Les scripts versionnés garantissent que
le nouveau comportement est rechargé sans conserver une ancienne version en
cache.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Collecte — précréer et lier l’organisme certificateur (27/09/2026)

Chaque ligne de **Certifications déclarées** affiche une action directe
**Précréer l’organisme**. Elle ouvre le modal HAUQE de précréation terrain :
coordonnées essentielles de l’organisme puis accréditation déclarée
(accréditeur, numéro, domaine, portée et dates lorsque connus). Après succès,
le nom reste lisible dans la ligne et le lien `organisme_id` est conservé avec
la certification déclarée.

Le bouton est créé après chaque rendu avec le patron d’écouteur direct de
Gestion des campagnes afin d’éviter le bug de latence. Modifier manuellement
le nom de l’organisme retire le lien existant et affiche clairement qu’un
nouveau rapprochement est requis. Le modal respecte le thème HAUQE et son
corps défile verticalement au zoom.

**Base PostgreSQL modifiée : oui, données RBAC uniquement ; migration :
aucune ; seed : aucun.**

### Administration — assistant « Nouvel utilisateur » lisible au zoom (27/09/2026)

Le modal **Administration > Nouvel utilisateur** utilise une hauteur bornée à
la fenêtre et un défilement vertical unique dans son corps. Les sections
**Identité professionnelle**, **Mot de passe initial** et **Rôles initiaux**
conservent désormais leur hauteur naturelle : aucun champ ne doit être rogné
lorsque l'utilisateur augmente le zoom du navigateur. L'option **Envoyer
directement les identifiants par courriel** dispose de son propre espace et ne
peut pas écraser sa case à cocher. La liste des rôles
garde son propre défilement uniquement lorsqu'elle contient beaucoup de rôles.

La création est organisée en trois étapes : **Identité professionnelle**,
**Mot de passe initial** puis **Rôles initiaux**. Les boutons **Continuer** et
**Précédent** font entrer la carte suivante par une courte transition latérale.
Le bouton **Créer le compte** n’est présenté qu’à la dernière étape. Chaque
étape valide ses prérequis avant de continuer ; le formulaire de modification
d’un compte conserve, lui, son affichage simple.

Le modal porte `data-static="true"` : le clic sur son fond et la touche
Échap ne doivent jamais annuler une saisie. Seules la croix de fermeture et
le bouton **Annuler** peuvent le fermer volontairement.

Ne pas réintroduire de `max-height` sur une carte isolée de ce modal : cela
masquerait à nouveau ses derniers champs au zoom. Le défilement doit rester
porté par `.dialog-body`.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Parcours de traitement — actualisation sans rechargement (27/09/2026)

Le composant partagé **Suivi du dossier / Parcours de traitement** s’enregistre
lorsqu’il est affiché. Après toute écriture API réussie, il reçoit un événement
commun et relit son état côté serveur, avec un léger regroupement des actions
successives. Cela couvre les fiches de collecte, vérifications, contrôles
FUCCS, validations N1/N2 et intégrations BNEC, sans actualisation manuelle de
la page.

Les conteneurs d’une page quittée sont supprimés du registre. Aucun observateur
DOM global n’est utilisé : la mise à jour ne doit ni déclencher de boucle de
rendu ni rendre les boutons moins réactifs.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Échéances — navigation réactive et détail par date (27/09/2026)

Les chevrons précédent/suivant, Aujourd’hui et les commandes de zoom du
calendrier sont recréés après chaque rendu avec un écouteur direct. Ils suivent
le patron validé de **Gestion des campagnes** : pas de délégation fragile ni de
bouton conservant un ancien gestionnaire, afin d’éviter la « latence bouton ».

Un clic sur le numéro ou l’espace libre d’une date ouvre un modal HAUQE qui
liste toutes ses échéances. Un clic sur une échéance du calendrier reste dédié
à son détail individuel ; les deux interactions ne se confondent pas.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Vérification — modal de réouverture guidée (27/09/2026)

Le bouton **Réouvrir** ouvre désormais un modal HAUQE suivant le thème des
échéances. Il explique l’impact réel avant toute écriture : réouverture simple,
reprise FUCCS confirmée ou révision obligatoire après validation/BNEC.

Lorsqu’une révision est obligatoire, le modal ne propose aucune action
destructive : son bouton **Ouvrir la collecte à réviser** mène directement à
la fiche liée, où l’utilisateur crée la nouvelle révision. Une flèche animée
met visuellement en évidence cette étape. Le bouton Réouvrir est aligné sur la
permission `VERIFICATION.CLOTURER`, et non sur la permission d’affectation.

**Règle d’interface :** ne jamais présenter une réouverture comme une simple
modification quand un jalon aval (FUCCS, validation, BNEC) existe. Le serveur
reste la source de décision.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Cellule de veille — relance : validation texte fiable (25/09/2026)

Le formulaire **Nouvelle relance** lit directement ses champs par leurs
identifiants stables avant l'appel API. Les données `destinataire`, `adresse
e-mail`, `canal`, `objet` et `contenu` sont donc toujours des chaînes de texte
primitives, même si une ancienne copie du modèle HTML est encore en mémoire.

Les champs obligatoires vides sont signalés avant l'envoi. Si l'API répond
malgré tout `422`, la page identifie le libellé du champ concerné au lieu
d'afficher seulement « Input should be a valid string ». Le script Veille est
versionné dans le routeur : un rechargement forcé charge impérativement la
correction.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Cellule de veille — un seul propriétaire de soumission (25/09/2026)

Le formulaire **Nouvelle relance** est soumis uniquement par `veille.js`. Le
script global d’ajout d’informations partagées peut enrichir l’interface mais
ne doit jamais intercepter, empêcher ou réémettre ce formulaire. Cette règle
évite qu’un mapping ancien de noms de champs transmette des valeurs vides alors
que les champs visibles sont remplis.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Matrice SNCC — continuité au centième (25/09/2026)

Les bornes du préremplissage SNCC sont au centième (`39,99 → 40`, `59,99 →
60`, `74,99 → 75`, `89,99 → 90`). La vérification navigateur arrondit la
différence au centième avant de rechercher une lacune. Ainsi, les imprécisions
binaires de JavaScript ne peuvent plus empêcher la création du brouillon ; une
vraie plage non couverte reste signalée.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Matrice SNCC — reprise d’un brouillon existant (25/09/2026)

À l'ouverture de l’onglet **Classement SNCC**, la page recherche désormais un
brouillon de matrice existant et recharge ses libellés, ses plages et ses
associations classe/statut/risque. Le bouton devient **Enregistrer le
brouillon SNCC** et met à jour cette version au lieu de tenter de recréer le
même code/version. Le bouton de publication devient immédiatement disponible.

La version est volontairement verrouillée pendant l’édition d’un brouillon,
car elle participe au code physique de la règle. Une nouvelle version est à
créer après publication.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Règles et codification — matrice SNCC guidée (25/09/2026)

L’onglet **Classement SNCC** est ajouté à la page **Règles et codification**.
Il remplace la saisie technique d’un JSON par un tableau lisible des cinq
classes : **A+** très favorable, **A** favorable, **B** à suivre, **C** fragile
et **D** critique.

Le bouton **Charger le préremplissage** propose des plages modifiables, une
association initiale statut/risque et tous les choix institutionnels :

- statuts `VA`, `RE`, `SU`, `RT`, `EX`, `VE` ;
- risques `R1` à `R5` ;
- classes `A+`, `A`, `B`, `C`, `D`.

L’utilisateur vérifie d’abord la matrice, crée un brouillon, puis utilise le
modal HAUQE de publication avec une référence d’approbation. Les boutons sont
liés avec le patron réactif direct de Gestion des campagnes afin de répondre au
premier clic.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Collecte soumise → offres de l'entreprise (24/09/2026)

À la soumission, chaque offre déclarée nommée est reprise dans
**Entreprise → Offres / produits**. Le rapprochement utilise le type, le nom
et la catégorie : une ligne déjà existante est mise à jour, elle n'est pas
dupliquée. Les marchés visés de la collecte deviennent les **Marchés cibles**
et les **Destinations** de l'offre entreprise. Les brouillons et les offres
sans nom ne sont jamais synchronisés.

**Base PostgreSQL modifiée : oui, données des offres uniquement ; migration :
aucune ; seed : aucun.**

### Offres de collecte — doublons bloqués (24/09/2026)

Une offre est désormais identifiée dans une fiche par **type + nom +
catégorie**. L'interface masque les anciennes lignes répétées même si leurs
volumes ou capacités divergent. L'API retourne l'offre existante en cas de
double envoi ; l'utilisateur ne voit donc pas deux cartes après
l'enregistrement.

**Base PostgreSQL modifiée : oui ; migration :
`h3d9e4f1a607_declared_offer_duplicate_protection.py` ; seed : aucun.**

### Collecte soumise → offres de l'entreprise (24/09/2026)

À la soumission, chaque offre déclarée nommée est reprise dans
**Entreprise → Offres / produits**. Le rapprochement utilise le type, le nom
et la catégorie : une ligne déjà existante est mise à jour, elle n'est pas
dupliquée. Les marchés visés de la collecte deviennent les **Marchés cibles**
et les **Destinations** de l'offre entreprise. Les brouillons et les offres
sans nom ne sont jamais synchronisés.

**Base PostgreSQL modifiée : oui, données des offres uniquement ; migration :
aucune ; seed : aucun.**

### Journal d'audit et fiches de collecte — recherche et actions stables (24/09/2026)

- **Journal d'audit** : la recherche retrouve désormais un auteur par nom,
  prénoms ou e-mail, y compris lorsqu'il ne figurait pas dans les 500 lignes
  initialement chargées. Les boutons Réinitialiser, Fermer, Vérifier
  l'intégrité et Exporter sont recréés avec le patron d'action directe.
- **Fiche de collecte soumise** : les offres et certifications affichées sont
  normalisées par identifiant puis par contenu. Les sauvegardes simultanées de
  ces deux listes partagent maintenant une requête unique afin d'empêcher la
  création involontaire de doublons par clics rapprochés.
- **Collectes & contrôles** : le bouton vert **Ouvrir la collecte** est créé
  après rendu avec son écouteur direct, protège sa navigation et présente un
  libellé explicite. Lorsqu'un bouton est corrigé, auditer les autres actions
  de son bloc et employer ce même patron plutôt que `onclick` sur du HTML
  remplacé.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Stabilité des boutons et thème nuit du suivi de dossier (24/09/2026)

Cause racine documentée : l'actualisation automatique remplaçait le DOM de
pages opérationnelles toutes les trente secondes. Pendant ce remplacement,
les boutons injectés pouvaient être visibles sans leur écouteur courant ou
accumuler des écouteurs après réexécution du script. Les pages
**Gestion des campagnes** et **Profil** ne présentaient pas le défaut car
elles étaient déjà exclues de ce mécanisme.

L'actualisation silencieuse est maintenant limitée au **Tableau de bord**,
qui est une vue consultative. Tous les écrans opérationnels utilisent le
bouton **Actualiser** explicite : aucune saisie, modal ni action ne sera
remplacé en arrière-plan. Cette règle est prioritaire pour tout nouveau
bouton ou formulaire dynamique.

Le composant partagé **Suivi du dossier / Parcours de traitement** reçoit une
palette complète en thème nuit : Collecte, Vérification, Contrôle FUCCS,
Validation et Intégration BNEC utilisent les mêmes contrastes pour étapes à
faire, en cours, terminées et bloquées.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Fiabilité des actions structurées et lecture Collecte → Entreprise (24/09/2026)

Dans les formulaires **Entreprise** (création et modification), les boutons
Ajouter / corbeille des contacts, sites et produits-services sont désormais
créés après chaque rendu par `document.createElement`, avec écouteur direct,
`preventDefault`, `stopPropagation` et `data-no-action-loader="true"`.
Le même patron est appliqué aux offres, certifications déclarées et fichiers
en attente dans la **Nouvelle collecte**. Une ligne déjà enregistrée peut être
retirée uniquement dans une fiche brouillon ; la suppression est refusée dès
la soumission afin de préserver le parcours de contrôle.

Les données de collecte restent des données déclarées : elles ne remplacent
pas automatiquement les données institutionnelles de l'entreprise avant
vérification. `marchés visés` dans la collecte décrit le marché commercial
déclaré ; `destinations` dans l'entreprise décrit les destinations
géographiques. L'activité principale peut être initialisée par la première
offre collectée sans écraser une valeur existante. Toute synchronisation des
marchés vers le dossier entreprise doit être une règle métier explicite,
validée et traçable — elle ne doit pas être assimilée à une destination.

La vue **Collectes & contrôles** renforce la hiérarchie visuelle : campagne
comme cadre principal, missions comme paliers et collectes entreprises comme
fiches distinctes. Le thème nuit est appliqué à l'intégralité du détail
**Intégration BNEC** (cartes, plan, informations d'entreprise et modal).

Dans **Règles et codification**, les listes et actions dynamiques de règles,
modèles, pondérations, codification et grille FUCCS sont reconstruites avant
leur écouteur direct afin que les icônes Ajouter, Modifier et Supprimer
répondent au premier clic.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Fiabilité des actions structurées et lecture Collecte → Entreprise (24/09/2026)

Dans les formulaires **Entreprise** (création et modification), les boutons
Ajouter / corbeille des contacts, sites et produits-services sont désormais
créés après chaque rendu par `document.createElement`, avec écouteur direct,
`preventDefault`, `stopPropagation` et `data-no-action-loader="true"`.
Le même patron est appliqué aux offres, certifications déclarées et fichiers
en attente dans la **Nouvelle collecte**. Une ligne déjà enregistrée peut être
retirée uniquement dans une fiche brouillon ; la suppression est refusée dès
la soumission afin de préserver le parcours de contrôle.

Les données de collecte restent des données déclarées : elles ne remplacent
pas automatiquement les données institutionnelles de l'entreprise avant
vérification. `marchés visés` dans la collecte décrit le marché commercial
déclaré ; `destinations` dans l'entreprise décrit les destinations
géographiques. L'activité principale peut être initialisée par la première
offre collectée sans écraser une valeur existante. Toute synchronisation des
marchés vers le dossier entreprise doit être une règle métier explicite,
validée et traçable — elle ne doit pas être assimilée à une destination.

La vue **Collectes & contrôles** renforce la hiérarchie visuelle : campagne
comme cadre principal, missions comme paliers et collectes entreprises comme
fiches distinctes. Le thème nuit est appliqué à l'intégralité du détail
**Intégration BNEC** (cartes, plan, informations d'entreprise et modal).

Dans **Règles et codification**, les listes et actions dynamiques de règles,
modèles, pondérations, codification et grille FUCCS sont reconstruites avant
leur écouteur direct afin que les icônes Ajouter, Modifier et Supprimer
répondent au premier clic.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Échéances — libellé de statut et planification (24/09/2026)

Dans le modal de détail d'une échéance, un défaut de rendu pouvait convertir
la fonction JavaScript de traduction des statuts en texte visible. Règle à
préserver : toute valeur affichée dans un template doit être le **résultat**
d'une fonction (ex. `statusLabel(item.statut)`), jamais la fonction elle-même.

Le statut affiche désormais uniquement un libellé métier lisible : Planifiée,
En cours, Terminée, Annulée ou En retard. Le filtre de statut utilise les mêmes
libellés. La planification impose une sélection explicite de certification et
informe l'utilisateur si aucune certification n'est encore disponible. Le
message de veille indique que les seuils peuvent être configurés par
certification, avec repli sur la règle publiée.

Le modal de détail conserve son motif HAUQE, mais son en-tête adopte la couleur
du statut affiché : **orange** pour Planifiée, **bleu** pour En cours, **vert**
pour Terminée, **rouge** pour En retard/expirée et gris violacé pour Annulée.
Une date passée est rendue « En retard » même si l'enregistrement historique
porte encore `PLANIFIEE` ; cette couleur ne modifie pas la base.

Le modal de détail d'une **alerte** utilise le même motif et suit son statut :
**orange** pour Nouvelle ou Affectée, **bleu** pour En cours et **vert** pour
Résolue ou Clôturée. La criticité de l'alerte reste affichée séparément dans
sa pastille et ne change pas artificiellement le statut.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Collecte & contrôle — arborescence mission / collectes / responsable (24/09/2026)

La liste opérationnelle suit explicitement la structure **Campagne → Mission
→ Collectes entreprises**. Une mission n'est affichée qu'une fois ; elle
contient ensuite toutes ses fiches d'entreprise courantes. Chaque collecte
montre son entreprise, son statut, sa complétude et le **responsable de la
fiche**, c'est-à-dire l'agent qui l'a créée. Les agents affectés à la mission
restent visibles séparément : ils ne sont pas confondus avec le responsable
d'une collecte particulière.

Le bouton **Nouvelle collecte** d'une mission ouvre une fiche vierge pour
cette mission précise (`#/collectes/nouveau/{mission_id}`), même si d'autres
entreprises possèdent déjà une fiche. Les boutons restent créés après rendu,
avec écouteur direct et `data-no-action-loader="true"`.

La réinitialisation d'un brouillon ne vide désormais que les données de cette
fiche. Elle ne modifie jamais la campagne, la mission, la zone, la période ou
les agents affectés, car ces informations sont partagées par les autres
collectes de la mission.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

#### Étape préparatoire — dossiers de collecte par entreprise (24/09/2026)

Le backend distingue maintenant le dossier de collecte et son responsable
stable. L’interface de création et la liste « Mes collectes » seront branchées
sur ce socle dans l’étape suivante. Cette séparation ne doit pas être rendue
partiellement visible avant que les contrôles d’accès par fiche soient actifs.

**Base PostgreSQL modifiée : oui ; migration :
`e1b7c4d9a206_collection_case_ownership.py` ; seed : aucun.**

### Plan d’alerte d’expiration d’une certification (24/09/2026)

Dans **Certifications → fiche d’une certification → Vue d’ensemble**, la carte
« Alertes d’expiration » affiche les jalons applicables sous une forme lisible
(`J-120`, `J-45`, `J-15`, `Jour J`). Le bouton **Paramétrer** est visible aux
détenteurs de `VEILLE.GERER` : la Cellule de veille et l’administrateur HAUQE
peuvent ajouter ou retirer des jours entre 1 et 3 650, sans doublon et dans la
limite de douze jalons. Le jour J est affiché, verrouillé et ne peut pas être
retiré.

Le dialogue utilise le thème modal HAUQE : en-tête vert, corps défilant et
actions fixes. Après enregistrement, la carte se met à jour et le backend
recalcule l’alerte active immédiatement. La mention « règle générale » reste
visible sur les certifications historiques non encore personnalisées.

**Base PostgreSQL modifiée : oui ; migration :
`b4c8d1e2f3a6_certification_expiration_alert_policy.py` ; seed : aucun.**

#### Réactivité des actions du plan d’alerte (24/09/2026)

Les commandes **Paramétrer**, **Ajouter** et **Retirer J-n** suivent le patron
validé de **Gestion des campagnes** : un emplacement neutre est rendu, puis le
vrai bouton est créé avec `document.createElement` après le rendu, reçoit un
écouteur direct unique qui annule la propagation, ainsi que
`data-no-action-loader="true"`. Ce mécanisme est obligatoire pour les actions
redessinées dans le modal ; il évite les clics ignorés ou nécessitant un
rafraîchissement. Le bouton de sauvegarde conserve son chargeur métier manuel,
mais est également exclu du chargeur global.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Collecte & contrôle — arborescence opérationnelle campagne / mission (24/09/2026)

La page **Collectes & contrôles** présente désormais d’abord les campagnes du
registre courant. Chaque ligne de campagne possède un bouton **Voir les
missions** qui ouvre sous cette ligne la liste de ses missions, avec la zone,
les agents affectés, l’entreprise liée, l’état de la fiche, la période prévue
et une action **Ouvrir**. Le paramétrage reste dans **Gérer les campagnes** ;
cette arborescence est l’espace de consultation opérationnelle.

Les boutons d’ouverture sont obligatoirement créés après le rendu de la liste
avec `document.createElement`, `data-no-action-loader="true"`,
`preventDefault`, `stopPropagation` et un écouteur direct unique. Un bouton
recréé par un filtre, une recherche ou une pagination doit ainsi répondre dès
le premier clic.

Cette évolution organise l’affichage. La future évolution métier
**Mission → plusieurs fiches de collecte d’entreprises** reste distincte : elle
nécessitera des règles d’accès par fiche et une migration dédiée ; elle ne doit
pas être simulée par l’interface seule.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

#### Création autonome des missions et affectation multiple (24/09/2026)

Depuis chaque ligne de campagne de **Collectes & contrôles**, le bouton
**Créer une mission** ouvre le modal HAUQE dédié. Il demande la référence,
la zone, les dates et l’objet de mission ; la sélection des agents se fait par
cases à cocher et ne possède aucune limite fonctionnelle de cinq agents. La
mission est enregistrée sans créer de fiche entreprise. Les collecteurs
affectés pourront ensuite ouvrir la mission pour démarrer la collecte qui leur
sera attribuée dans la prochaine évolution par fiche.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Précréation terrain, contacts et cartographie des sites (24/09/2026)

Dans **Collectes & contrôle → Nouvelle collecte → Entreprise → Précréer
l’entreprise**, le formulaire inclut désormais une adresse terrain, latitude,
longitude et le bouton **Utiliser ma position**. Le navigateur demande le
consentement de l’agent ; un refus ou une indisponibilité laisse les champs
manuels utilisables. La position nécessite un contexte sécurisé (HTTPS) ou
`localhost`, selon les règles du navigateur.

Après précréation, le site « Siège / site collecté » est disponible dans la
fiche entreprise. Si latitude et longitude sont renseignées, le bouton
**Voir la carte** ouvre Google Maps dans un nouvel onglet. Les informations de
déclarant d’une fiche alimentent les **Contacts → Interlocuteurs actifs** et
la première description d’offre complète une **Activité principale** vide sans
écraser une valeur déjà présente.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Autre identifiant juridique d'entreprise (24/09/2026)

Dans **Nouvelle entreprise** et **Modifier entreprise**, le champ facultatif
« Autre identifiant juridique » est rangé avec RCCM, NIF et IFU sous
l'interrupteur **Identifiants juridiques**. Sa valeur est reprise dans l'étape
de vérification avant enregistrement. Le formulaire active automatiquement ce
bloc lorsqu'une valeur juridique historique existe et son script est versionné.

**Base PostgreSQL modifiée : oui ; migration :
`f7a1e2c3d4b5_other_legal_identifier.py` ; seed : aucun.**

### Libellés des certifications déclarées dans la collecte (24/09/2026)

Dans la fiche de collecte, les noms présentés à l'agent sont désormais
« Numéro du certificat », « Organisme certificateur » et « Norme / référentiel
du certificat ». Les clés API et les colonnes existantes restent inchangées
afin de préserver les données et l'intégration BNEC. Le script est versionné
dans le routeur pour assurer le rechargement de ces libellés.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Collecte par entreprise dans une mission et gestion des affectations (24/09/2026)

Le bouton **Nouvelle collecte** ne crée plus ni campagne ni mission. Il ouvre
une fiche qui demande d'abord une **mission existante à laquelle l'agent est
affecté**, présente ses informations en lecture seule, puis laisse l'agent
choisir ou précréer l'entreprise et créer sa fiche indépendante.

Dans **Collectes & contrôles**, chaque mission propose à l'administrateur
HAUQE le bouton **Agents**. Le modal HAUQE permet d'ajouter autant d'agents
actifs que nécessaire à une mission déjà enregistrée, y compris si des fiches
de cette mission sont clôturées. Cette action ne réouvre aucune fiche et ne
crée aucune révision. Le modal **Créer une mission** propose également le
bouton **Créer** près de la zone administrative ; la zone est créée puis
sélectionnée immédiatement.

Les actions utilisent le patron réactif de Gestion des campagnes : boutons
créés après rendu avec `document.createElement`, écouteur direct unique,
`preventDefault`, `stopPropagation` et `data-no-action-loader="true"`.

**Base PostgreSQL modifiée : oui ; migration :
`e1b7c4d9a206_collection_case_ownership.py` ; seed : aucun.**

### Vérifications — consultation des collectes sans affectation (27/09/2026)

Un utilisateur portant uniquement le rôle **Vérificateur** peut consulter les
collectes grâce à `COLLECTE.LIRE`, sans bouton ni API de création, modification
ou soumission. Il traite les dossiers de vérification, mais les actions
d'affectation et de réaffectation restent invisibles et refusées par l'API : le
rôle ne possède pas `VERIFICATION.AFFECTER`.

L'affectation des vérificateurs relève du **Point focal BNEC** ou de
l'**Administrateur HAUQE**. Après le changement des droits, l'utilisateur doit
actualiser sa session afin que l'interface recharge ses permissions.

**Base PostgreSQL modifiée : oui, données RBAC uniquement ; migration :
aucune ; script : `python -m app.scripts.sync_verificateur_collecte_read`.**

### Direction technique — lecture du parcours de dossier (27/09/2026)

La Direction technique peut ouvrir les pages **Collecte & contrôle** et
**Vérifications** en consultation. Les boutons opérationnels (création,
modification, soumission, affectation, traitement et clôture) restent absents
ou refusés par l'API, car le rôle possède seulement `COLLECTE.LIRE` et
`VERIFICATION.LIRE` pour ces modules.

**Base PostgreSQL modifiée : oui, données RBAC uniquement ; migration :
aucune ; script : `python -m app.scripts.sync_direction_consultation_dossiers`.**

### Scoring, INFC et SNCC automatiques avec rapport (25/09/2026)

Les boutons **Évaluer automatiquement**, **Calculer automatiquement** et
**Calculer automatiquement** du SNCC appellent les endpoints métier sans
ouvrir de formulaire de saisie de notes. Le modal de rapport indique le score,
la classe ou le niveau, la règle publiée utilisée, les informations conformes,
les alertes et les blocages. Un résultat est rechargé seulement après la
fermeture de ce rapport afin de rendre l'opération lisible.

Le SNCC reste volontairement bloqué tant que la matrice de classement publiée
`SNCC_CLASSIFICATION_MATRIX` n'a pas été paramétrée et publiée par la HAUQE.
Cette protection évite d'afficher une classe ou un risque non approuvé.

Les écrans Scoring, INFC et SNCC doivent charger le moteur de calcul
automatique avant leur script propre. Un bouton ne doit jamais appeler une
fonction optionnelle silencieuse : si le moteur ne peut pas être chargé, l'état
de page affiche l'erreur ; sinon le clic ouvre systématiquement le rapport de
calcul ou de blocage. Les boutons sont créés après le rendu avec un écouteur
direct, selon le patron réactif de Gestion des campagnes.

Pour le SNCC, le rapport automatique présente le **score**, la **classe**, le
**statut administratif** et le **niveau de risque** retournés par la ligne
applicable de `SNCC_CLASSIFICATION_MATRIX`. Aucune de ces valeurs ne doit être
demandée à l'utilisateur lorsque le bouton **Calculer automatiquement** est
utilisé.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Vérification — résolution fiable des anomalies (25/09/2026)

Dans le dossier **Vérifications > Anomalies**, l'action **Résoudre** ne doit
jamais utiliser une fenêtre native `prompt()`. Elle ouvre le modal opérationnel
HAUQE, exige la mesure de résolution et recrée son bouton après chaque rendu de
la liste avec un écouteur direct unique. Ainsi, l'action reste disponible au
premier clic après un changement d'onglet, une erreur ou le redessin de la
liste.

Un observateur DOM ne doit cibler que le conteneur métier concerné et ne doit
relancer les icônes que lorsqu'il a réellement recréé une action. Observer
`document.body` puis appeler le moteur d'icônes à chaque mutation crée une
boucle de rendu susceptible de bloquer la page.

Après validation, la ligne affiche immédiatement le statut **Résolue** et la
mesure saisie. Toute erreur est affichée dans le modal sans fermer celui-ci.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Administration — copie des identifiants initiaux (01/10/2026)

Après création d'un utilisateur, les icônes de copie du courriel et du mot de
passe initial utilisent d'abord `navigator.clipboard` en HTTPS/localhost,
puis un secours par sélection temporaire et `document.execCommand("copy")`.
La copie reste donc utilisable via une adresse HTTP du réseau local, où l'API
moderne du presse-papiers est volontairement bloquée par le navigateur. Une
valeur vide ou indisponible affiche un message clair.

Correctif du 01/10 : sélectionner directement la valeur visible **dans le
dialog modal ouvert**, jamais un champ temporaire ajouté à `document.body`
rendu inactif par `showModal()`. Si l'API moderne refuse malgré HTTPS,
tenter aussi le secours. En cas de refus total, laisser la valeur
sélectionnée pour `Ctrl+C`. Afficher succès ou échec **dans le modal**, pas
dans l'état de page masqué derrière. Les trois boutons de copie (mot de passe
avant création, courriel et mot de passe après création) utilisent un seul
écouteur `click` en capture sur `document`, remplacé proprement à chaque
réinjection SPA : un bouton recréé fonctionne encore au premier clic.
Recette : `tests/frontend/user_credentials_copy_smoke.cjs` (copie réelle dans
Chrome/Edge sur HTTPS et HTTP, interface locale servie par l'application,
bouton recréé, échec visible).

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### SNCC — statuts métier prioritaires et explication de statut (26/09/2026)

Dans **Règles et codification > Classement SNCC**, le préremplissage ne propose
plus que les statuts normaux de score **VA** et **RE**. La page explique que la
matrice fixe la classe et le risque, tandis que **EX** (expiré), **VE** (en
vérification), **SU** (suspendu) et **RT** (retiré) sont appliqués par le
moteur selon la situation effective de la certification.

La fiche d'une certification affiche désormais le bloc **« Pourquoi ce
statut ? »** à partir d'une analyse côté serveur : expiration, document actif,
authenticité, collecte liée, renouvellement ouvert et motif enregistré. Chaque
constat expose une action directe vers **Documents**, **Renouvellement** ou
**Historique des décisions et vérifications**. Il ne s'agit donc pas d'un
texte fixe ou d'une interprétation faite par le navigateur.

Le tableau de bord compte toute certification ayant une date d'expiration,
indépendamment de son statut documentaire : un certificat à vérifier mais déjà
expiré apparaît bien dans le compteur **Expirées** et dans les échéances à
surveiller.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Gestion des campagnes — assistant « Nouvelle campagne » (27/09/2026)

Le modal **Nouvelle campagne** est un assistant HAUQE en trois étapes :
**Identification**, **Cadre opérationnel** et **Période prévisionnelle**.
L’utilisateur utilise Précédent / Continuer et ne peut pas passer une étape
future tant que son contrôle n’est pas valide. Le code est proposé
automatiquement et reste facultatif à la saisie ; la date de fin ne peut pas
précéder la date de début.

Les étapes déjà validées restent consultables depuis l’indicateur du modal.
Le bouton **Enregistrer** n’apparaît qu’à l’étape finale. Une nouvelle
campagne est proposée avec le statut **Active** par défaut. Le modal conserve
le thème HAUQE, le défilement vertical et le rendu sombre.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Collecte — harmonisation des modals de précréation (27/09/2026)

Les modals de précréation d’**entreprise**, de **zone administrative** et
d’**organisme certificateur** utilisent le même thème HAUQE : entête vert et
icône, message de portée, sections numérotées, champs regroupés, pied de
modal stable et zone de contenu à défilement vertical. Le rendu mobile et le
thème sombre sont pris en charge.

Les identifiants de champs, les actions de géolocalisation, les validations et
les appels API existants ne changent pas : il s’agit uniquement d’une
amélioration de lisibilité et d’ordonnancement.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Collecte — défilement du modal « Créer une mission » (27/09/2026)

Le contenu de **Créer une mission** défile désormais à l'intérieur du bloc de
saisie, tandis que l'entête et les boutons Annuler / Créer la mission restent
visibles. Au zoom élevé, les champs de mission et la liste des agents ne sont
donc plus coupés. Le même comportement est appliqué au modal de gestion des
agents d'une mission, qui utilise le même composant.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Règles et codification — prévention du « bouton latence » (27/09/2026)

Les boutons de **COLLECTE_COMPLETUDE**, codification BNEC, règles métier,
scoring, SNCC et grilles FUCCS utilisent un écouteur direct unique sur le
bouton réellement affiché. Les listes recréées après une recherche ou une
modification reçoivent leur écouteur immédiatement après le rendu.

À éviter : cloner un bouton déjà affiché pour lui attacher un écouteur, ou
surveiller en permanence toute la page avec un `MutationObserver`. Ces deux
pratiques peuvent créer un délai apparent ou perdre le premier clic. Pour les
actions FUCCS générées dynamiquement, créer le bouton JavaScript avec son
écouteur direct au moment du rendu, comme dans Gestion des campagnes.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### SNCC — résultat visible de la vérification et du brouillon (27/09/2026)

Dans **Règles et codification > Classement SNCC**, le bouton **Vérifier la
matrice** affiche désormais son résultat directement sous les actions :
contrôle réussi ou liste précise des corrections à apporter, puis rappel des
cinq plages avec leur classe, statut et risque.

Après **Créer le brouillon SNCC**, une fiche visible confirme ce qui vient
d’être enregistré : version, statut *Brouillon*, libellé et plages retenues.
Elle rappelle clairement que ce brouillon n’a aucun effet sur les classements
tant que le bouton **Publier la matrice** n’a pas été utilisé après approbation
HAUQE. Aucun UUID ni détail interne n’est exposé à l’utilisateur.

Les actions conservent l’écouteur direct unique défini pour corriger le
« bouton latence ».

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Système entier — erreurs de formulaires directement dans les modals (27/09/2026)

Le gestionnaire de modals HAUQE applique un comportement commun à tous les
formulaires ouverts dans un modal. Une erreur de champ ne doit jamais imposer
la fermeture du modal, ni perdre la saisie déjà réalisée :

- un encadré rouge apparaît en haut de la zone de saisie du modal ;
- le ou les champs concernés reçoivent une bordure rouge et leur explication
  directement sous le champ ;
- le modal défile vers la première correction et le focus y est placé ;
- dès qu’un champ est corrigé, son erreur locale est retirée ;
- les erreurs FastAPI (`400`, `409`, `422`, `5xx`, réseau) sont renvoyées dans
  le modal actif, y compris lorsque l’écran les affichait auparavant seulement
  dans son bandeau général.

**Périmètre cartographié :** les modals des alertes, échéances, entreprises,
certifications, organismes, campagnes et missions, fiche de collecte et ses
précréations, vérifications, contrôles FUCCS, validations, intégrations BNEC,
scoring, INFC, SNCC, veille, publications, règles et codification, qualité des
données, sauvegardes, zones administratives et administration utilisateurs.
Les modals purement informatifs (historique, aperçu, détail) restent sans
message de formulaire puisqu’ils ne saisissent aucune donnée.

**Règle à respecter dans les nouveaux écrans :** tout appel API privé passe
par `core/api.js`, et tout nouveau formulaire modal doit rester dans un
`dialog` HAUQE ou un modal reconnu par `dialog-manager.js`. Pour une erreur
locale qui n’est pas issue d’une API, le module peut appeler
`window.HAUQE_MODAL_FEEDBACK.show("…")` au lieu d’un bandeau de page.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Compte et sécurité — réinitialisation du mot de passe (27/09/2026)

Le formulaire **Mot de passe oublié > Choisir un nouveau mot de passe** attend
désormais explicitement le chargement du client API avant d’appeler
`/api/v1/auth/password/reset`. Cela corrige l’erreur JavaScript `api is not
defined` qui pouvait apparaître après la saisie du nouveau mot de passe et de
sa confirmation. Les contrôles métier existants restent inchangés : le jeton,
la confirmation, la révocation des anciennes sessions et la notification de
sécurité continuent d’être traités côté serveur.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Collecte — preuves et précréation entreprise (27/09/2026)

Dans « Certifications déclarées », les fichiers choisis sont maintenant listés
avant leur enregistrement. L'agent confirme ou annule la sélection ; les
preuves enregistrées restent visibles sur la ligne du certificat. Après le
premier dépôt réussi, « Copie disponible » passe automatiquement à « Oui ».
Le modal « Précréer l'entreprise » garde ses champs accessibles au zoom élevé :
le formulaire complet défile lorsque l'en-tête et les actions prennent toute
la hauteur disponible. Vérifier systématiquement le premier clic des boutons
et le défilement des modals aux zooms usuels et élevés après chaque évolution.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Précréations de collecte — zoom et défilement des trois modals (27/09/2026)

La correction de zoom concerne ensemble **zone administrative**, **entreprise**
et **organisme certificateur**. À hauteur normale, le corps du modal défile et
son pied reste visible. À hauteur très réduite (fort zoom), tout le formulaire
défile, y compris l'en-tête et le pied, afin de pouvoir atteindre les derniers
champs et les actions. Les lignes de la grille de contenu gardent leur hauteur
réelle ; elles ne doivent jamais comprimer une section et masquer ses inputs.
Contrôle navigateur effectué sur les trois vrais formulaires à 1280 × 800 et
320 × 200 px, avec accès vérifié jusqu'aux actions du bas.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

### Documents de la fiche — preuves par certification (27/09/2026)

Vérifications > Documents et Points, Contrôle FUCCS > Preuve documentaire et
Entreprise > Documents utilisent désormais les preuves des certifications
déclarées en plus des justificatifs généraux. Chaque preuve affiche le nom et,
si disponible, le numéro du certificat concerné. Après intégration BNEC, la
preuve reste consultable depuis la certification officielle et la vue de la
fiche liée ; elle n'est pas copiée pour l'affichage. Dans FUCCS, un bouton
permet d'ouvrir la preuve sélectionnée avant l'enregistrement de la note.

Éviter à l'avenir de limiter « Documents de la fiche » au seul type
`FICHE_COLLECTE` : il faut également considérer `CERTIFICATION_DECLAREE` et
les `CERTIFICATION` officiellement rapprochées. Un document apparaît une
fois par dossier et son contexte métier reste lisible, sans UUID affiché.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**
### Veille — confirmation de clôture et préférence du point focal (01/10/2026)

Le modal HAUQE de clôture charge avant confirmation les nombres de relances,
d'échéances, d'alertes et de courriels non envoyés concernés. Le bouton de
confirmation reste inactif jusqu'au chargement et le motif reste obligatoire.
Le contenu du modal défile au zoom, sans cacher les actions. La rubrique
« Courriels du système par agent » du profil est visible et modifiable par le
point focal BNEC, en plus des administrateurs autorisés. À vérifier après
déploiement : premier clic, zoom, thème sombre et rafraîchissement du cache JS.
### Modals au zoom et identité visuelle officielle (01/10/2026)

Les modals « Alerte spéciale » et « Planifier une échéance » utilisent un
défilement continu sur le formulaire complet, y compris quand le navigateur
réduit fortement l'espace disponible. Le formulaire d'échéance présente
désormais trois étapes : certification, organisation du suivi et contexte.
Le formulaire « Alerte spéciale » présente également trois étapes : source du
signalement, criticité et contenu. Le passage à l'étape suivante contrôle les
champs obligatoires de l'étape courante ; le retour conserve les valeurs saisies.
Les boutons Précédent/Continuer répondent au premier clic et les champs
obligatoires de chaque étape sont contrôlés avant progression. Les données
saisies sont conservées en revenant à l'étape précédente.

Le fichier officiel `app/static/logo.jpg` remplace les monogrammes « HQ » dans
la connexion, la session sécurisée, la navigation, la sauvegarde, l'aperçu des
rapports et les anciens écrans HTML conservés. Les exports PDF et Excel
incorporent l'image ; les courriels HTML la contiennent en pièce liée inline
(CID), et gardent une version texte sans image. Recharger complètement les
fichiers CSS/JS versionnés après déploiement. **Base PostgreSQL modifiée : non.**
