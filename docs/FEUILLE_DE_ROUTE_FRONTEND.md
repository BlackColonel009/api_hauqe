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
| Dernière mise à jour | 26 juillet 2026 — check-up final avant raccordement API ↔ frontend |

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
- sauvegarde locale en brouillon ;
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
