# PASSATION — PROJET HAUQE CERTIF

> Document de continuité destiné à démarrer une nouvelle discussion sans perdre le contexte du projet.
> Dernière mise à jour : 23 juillet 2026, après intégration des 51 règles métiers validées par la HAUQE/GFA.

## 1. Instruction pour la prochaine discussion

Lire entièrement ce document avant toute modification du projet. Le frontend est déjà largement maquetté et fonctionnel avec des données simulées. Les règles RM-01 à RM-51 sont désormais autorisées par la HAUQE/GFA et doivent guider le réalignement des écrans sur le cycle Collecte → Vérification → Contrôle → Validation → Intégration → Classement → Veille. Seuls les sujets explicitement laissés ouverts restent à arbitrer.

Les seuils d'alerte principaux 180/90/30 jours puis expiration sont validés par les règles RM. La classification entreprise 85-100/60-84/<60 est distincte de l'INFC et du SNCC. La fiche FUCCS confirme par ailleurs la grille de 28 critères sur 56. Ces quatre résultats ou mécanismes ne doivent pas être fusionnés.

## 2. Identité et objectif du projet

- **Nom de travail :** HAUQE Certif.
- **Bénéficiaire :** Haute Autorité de la Qualité et de l'Environnement (HAUQE), Togo.
- **Contexte :** mission liée aux TDR GIZ / ProComp / GFA.
- **Périmètre initial :** collecte, vérification et harmonisation des informations concernant environ 100 entreprises certifiées et les organismes certificateurs, puis constitution d'une base de données préliminaire exploitable.
- **Périmètre fonctionnel développé dans la maquette :** gestion des organismes, entreprises, certifications, collectes, validations, contrôles, scoring, alertes, échéances, référentiels, utilisateurs, rapports et audit.
- **Position du développeur :** expert à court terme. La solution doit donc être documentée, transférable, maintenable et administrable sans dépendance permanente envers son auteur.

Les TDR imposent surtout la collecte, la structuration des données et le reporting. Plusieurs fonctions avancées de l'interface sont des améliorations professionnelles utiles proposées pour rendre le système cohérent et durable ; elles ne doivent pas toutes être présentées comme des obligations contractuelles sans validation.

## 2A. Corpus lu et hiérarchie d'interprétation

La présente passation tient désormais compte du contenu intégral du guide méthodologique, de la fiche unique FUCCS, des fiches de collecte et de contrôle, des procédures de collecte, de mise à jour et de gestion des alertes, de la note de cadrage de la CVC, des documents INFC et SNCC, des tableaux de bord intégré et stratégique, ainsi que du document de validation des règles métiers.

Hiérarchie de travail à appliquer :

1. appliquer les règles métiers RM-01 à RM-51 validées ;
2. utiliser les procédures et formulaires opérationnels pour compléter les parcours et données à saisir ;
3. utiliser les documents spécialisés INFC et SNCC pour leurs mécanismes respectifs ;
4. utiliser le guide méthodologique pour la gouvernance, les rôles, le cycle de vie, la sécurité et les modules ;
5. lorsqu'un point non tranché subsiste, le rendre configurable et inscrire l'arbitrage dans la recette fonctionnelle.

### Écarts majeurs identifiés

- Le frontend actuel passe trop directement de la recevabilité au contrôle ; la vérification, la validation hiérarchique et l'intégration BNEC doivent être des étapes distinctes.
- Le scoring actuel mélange la grille FUCCS sur 56 avec un indice provisoire sur 100 ; l'INFC et le SNCC doivent devenir des fonctions séparées et versionnées.
- Les anciens documents présentent plusieurs horizons d'alerte. Les règles validées retiennent désormais 180, 90 et 30 jours puis expiration ; une éventuelle information complémentaire à 12 mois reste configurable et à confirmer.
- Un seul tableau de bord ne suffit pas : cinq niveaux sont documentés, dont un tableau public agrégé.
- Le rôle de la Cellule de Veille des Certifications doit être représenté dans les droits, les files de travail, les rapports et les indicateurs.
- Les demandes de vérification aux organismes certificateurs, les réponses et les délais doivent être suivies comme des objets métier traçables.

## 3. Choix techniques et état actuel

### Technologies retenues

- Frontend : HTML5, CSS3, Bootstrap et JavaScript.
- Backend prévu : Python avec FastAPI.
- Base prévue : PostgreSQL.
- Moteur de templates : Jinja2.
- Serveur de développement : Uvicorn.
- Exports prévus : PDF, XLSX et CSV.

### État réel

- Les maquettes frontend sont créées sous forme d'une application monopage (SPA).
- La barre latérale et la barre supérieure sont communes à toutes les vues.
- Le routeur JavaScript charge les pages sans recopier le shell sur chaque fichier.
- Le chargement global retenu est l'option A : SVG animé avec dessin progressif du « H », cercle institutionnel, orbite dorée et feuille verte. Il est piloté par le routeur et respecte `prefers-reduced-motion`.
- Un switch global permet de choisir le thème clair ou sombre. Le choix est enregistré sous `hauqe-theme` dans `localStorage` et appliqué dans le `<head>` avant le rendu afin d'éviter un flash de thème incorrect.
- Les interactions principales sont simulées en JavaScript et avec `localStorage`.
- Aucune base métier PostgreSQL n'est encore créée.
- Les API métier FastAPI ne sont pas encore implémentées.
- L'application a été lancée et testée par l'utilisateur sur le port `8001`.

Commande habituelle depuis la racine du projet :

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Adresse : `http://127.0.0.1:8001/`

## 4. Architecture existante importante

```text
app/
├── main.py                         # application FastAPI et routes des vues
├── templates/
│   ├── index.html                  # shell SPA : navbar + sidebar + zone centrale
│   ├── legacy/                     # anciennes pages complètes conservées
│   └── ...                         # fragments/vues HTML
└── static/
    ├── css/                        # styles généraux et styles des pages
    ├── js/
    │   ├── core/
    │   │   ├── router.js           # navigation par hash et chargement dynamique
    │   │   ├── app-shell.js        # navbar, sidebar et interactions communes
    │   │   ├── api.js              # futur client des API
    │   │   └── config.js           # configuration frontend
    │   └── ...                     # scripts fonctionnels des écrans
    └── ...
```

Dans `app/main.py` :

- `/` sert le shell `index.html` ;
- `/static` sert les ressources statiques ;
- `/views/{page_name}` sert seulement les vues autorisées ;
- `/api/health` vérifie la disponibilité du serveur.

Fichiers de documentation à conserver et enrichir :

- `FEUILLE_DE_ROUTE_FRONTEND.md` : inventaire fonctionnel détaillé des pages ;
- `GUIDE_UTILISATION.md` : futur guide utilisateur, à compléter à chaque ajout ;
- `PASSATION_PROJET_HAUQE_CERTIF.md` : le présent dossier de continuité.

## 5. Inventaire des pages frontend

Les 24 pages initialement prévues sont créées côté maquette. Elles restent à valider fonctionnellement et plusieurs doivent maintenant être corrigées ou complétées à la lumière du corpus documentaire.

| N° | Route logique | Page | Rôle principal |
|---:|---|---|---|
| 1 | `/dashboard` | Tableau de bord | Synthèse des indicateurs, alertes et activités |
| 2 | `/alertes` | Alertes | Priorisation, affectation et suivi des anomalies |
| 3 | `/echeances` | Échéances | Calendrier, retards, planification et responsables |
| 4 | `/entreprises` | Entreprises | Répertoire, recherche, filtres et états |
| 5 | `/entreprises/detail` | Détail entreprise | Dossier complet, sites, contacts, produits et historique |
| 6 | `/entreprises/form` | Formulaire entreprise | Création et modification d'une entreprise |
| 7 | `/certifications` | Certifications | Registre et suivi de validité des certificats |
| 8 | `/certifications/detail` | Détail certification | Certificat, norme, périmètre, audits et preuves |
| 9 | `/certifications/form` | Formulaire certification | Création et modification d'un certificat |
| 10 | `/organismes` | Organismes | Répertoire des organismes certificateurs |
| 11 | `/organismes/detail` | Détail organisme | Coordonnées, reconnaissances et accréditations |
| 11A | `/organismes/form` | Formulaire organisme | Création **et modification** d'un organisme |
| 12 | `/collectes` | Collectes et missions | Missions, progression et accès aux dossiers |
| 13 | `/collectes/nouveau` | Nouvelle collecte | Formulaire numérique de collecte terrain |
| 14 | `/validations` | Validations | File d'attente, affectations et recevabilité |
| 15 | `/controle` | Grille de contrôle | Évaluation des critères et décision |
| 16 | `/scoring` | Scoring | Calcul, analyse du risque et planification du suivi |
| 17 | `/rapports` | Rapports | Paramétrage et export PDF/XLSX/CSV |
| 18 | `/utilisateurs` | Utilisateurs | Comptes, rôles, statut et habilitations |
| 19 | `/referentiels` | Référentiels | Valeurs communes : régions, normes, secteurs, etc. |
| 20 | `/regles-codification` | Règles et codification | Versions des règles et génération des identifiants |
| 21 | `/journal-audit` | Journal d'audit | Traçabilité des actions et changements |
| 22 | `/connexion` | Connexion | Authentification |
| 23 | `/mot-de-passe-oublie` | Mot de passe oublié | Demande de réinitialisation sécurisée |
| 24 | `/profil` | Profil | Informations personnelles et préférences |

### Pages ou vues à ajouter après réalignement documentaire

| Priorité | Route proposée | Finalité |
|---|---|---|
| P0 | `/verifications` | Vérification documentaire, anomalies, demandes aux OC et avis technique |
| P0 | `/integrations` | Contrôle préalable, codification, intégration et contrôle post-intégration |
| P1 | `/infc` | Calcul versionné de l'INFC et agrégats nationaux |
| P1 | `/classement-sncc` | Classe, statut, risque et historique du classement |
| P1 | `/veille` | Espace de travail de la Cellule de Veille des Certifications |
| P1 | `/tableaux-de-bord/tactique` | Pilotage mensuel de la Direction Technique |
| P1 | `/tableaux-de-bord/strategique` | Pilotage trimestriel et synthèse décisionnelle |
| P1 | `/tableaux-de-bord/annuel` | Bilan institutionnel annuel |
| P1 | `/barometre` | Baromètre national des certifications |
| P1 | `/mises-a-jour` | Demandes de modification et circuit de validation |
| P1 | `/decisions` | Notes de décision, décisions et plans d'action |
| P2 | `/public` | Données nationales agrégées et autorisées |
| P2 | `/echanges-organismes` | Correspondances, confirmations, réponses et délais |
| P2 | `/documents` | Métadonnées, indexation, versions et archivage |
| P2 | `/incidents` | Déclaration et traitement des incidents |
| P2 | `/amelioration-continue` | Audits, retours d'expérience et actions PDCA |

### Interactions déjà ajoutées ou corrigées

- Notification et menu utilisateur dans la navbar.
- Verrouillage global après inactivité : code privé configurable dans Profil/Sécurité, délai de 5 à 30 minutes, écran bloquant, test immédiat, cinq tentatives puis déconnexion.
- Fenêtre professionnelle d'affectation d'une alerte : responsable, priorité, échéance, instruction et notification.
- Création et modification des organismes.
- Boutons des modèles de règles/codification rendus interactifs.
- Depuis la validation, le bouton **Recevable — démarrer le contrôle** ouvre la grille.
- La grille FUCCS comprend 28 critères répartis en quatre rubriques : contrôle documentaire, authenticité, mise en œuvre et traçabilité. Chaque critère vaut 0, 1 ou 2, soit un total brut sur 56.
- L'INFC sur 100 est un mécanisme distinct comportant six domaines pondérés. Le scoring actuel doit être refondu pour éviter toute confusion entre les deux calculs.
- Le SNCC est un troisième mécanisme combinant classe A+ à D, statut administratif VA/RE/SU/RT/EX/VE et risque R1 à R5.
- Depuis le scoring, **Planifier le suivi** préremplit une échéance.
- Dans les échéances, la planification, les éléments du calendrier et la liste prioritaire ouvrent les informations attendues.
- Les exports des rapports sont pour l'instant simulés.

## 6. Profils et responsabilités proposés

| Profil | Responsabilités |
|---|---|
| Administrateur HAUQE | Référentiels, comptes, rôles, règles, codification et supervision générale |
| Administrateur système | Infrastructure, sécurité technique, sauvegardes, restauration, incidents et maintenance |
| Administrateur fonctionnel BNEC | Intégration des données validées, qualité, codification, référentiels et tableaux de bord |
| Coordonnateur / superviseur | Planification des missions, affectation des dossiers, arbitrage et pilotage |
| Point focal BNEC | Coordination quotidienne, contrôle qualité, validation opérationnelle et reporting |
| Agent de collecte | Création des collectes, saisie terrain, ajout des justificatifs et correction |
| Agent vérificateur | Vérification documentaire, authenticité, anomalies et avis technique |
| Validateur HAUQE | Validation, validation sous réserve, ajournement ou rejet avec traçabilité |
| Contrôleur / évaluateur | Application de la grille FUCCS, constatations, risques et recommandations |
| Cellule de Veille des Certifications | Échéances, alertes, relances, renouvellements et rapports de veille |
| Direction / décideur | Consultation des indicateurs, décisions et rapports consolidés |
| Auditeur / consultation | Lecture contrôlée des données et du journal, sans modification métier |

Les habilitations définitives doivent être configurables par permissions et non uniquement codées en dur par profil.

## 7. Parcours métier de référence

### Cycle complet de traitement

1. Le superviseur programme une campagne ou une mission de collecte.
2. L'agent clique sur **Nouvelle collecte**.
3. Il choisit ou crée l'entreprise, complète la fiche numérique et joint les documents.
4. Il sauvegarde éventuellement un brouillon, puis soumet la fiche.
5. La fiche arrive dans la file des dossiers à vérifier.
6. Le Point focal affecte le dossier à un agent vérificateur et conserve l'historique de l'affectation.
7. Le vérificateur contrôle la complétude, les pièces, les dates, la portée, le référentiel, l'organisme et son accréditation.
8. Il peut adresser une demande de confirmation à l'organisme certificateur ou retourner le dossier pour complément.
9. Il produit un avis : vérifié conforme, vérifié sous réserve, non vérifié, suspect ou rejeté.
10. Le contrôle approfondi applique ensuite les 28 critères FUCCS et enregistre les preuves, commentaires, non-conformités et risques.
11. Le système calcule le score brut sur 56 et son taux, sans le confondre avec l'INFC.
12. Le dossier est soumis au circuit de validation hiérarchisé : validé, validé sous réserve, ajourné ou rejeté.
13. La double validation, les visas, réserves et justifications sont conservés.
14. Seul un dossier formellement validé peut entrer dans la file d'intégration BNEC.
15. L'Administrateur fonctionnel contrôle les doublons, attribue les codes, intègre les données et réalise le contrôle post-intégration.
16. Le système calcule ou recalcule l'INFC selon la formule versionnée, puis propose le classement SNCC.
17. Le classement est vérifié par le Point focal et validé par la Direction Technique.
18. Les résultats alimentent la veille, les alertes, les tableaux de bord et les rapports.

### Répartition retenue pour la fiche numérique

La fiche Word HAUQE/FUCCS/01 contient environ 170 saisies manuelles pour une entreprise avec une certification. Il a été décidé de ne pas reproduire ces saisies dans un formulaire terrain unique.

Le frontend doit désormais représenter sept niveaux : **collecte**, **vérification documentaire**, **contrôle approfondi**, **validation**, **intégration BNEC**, **classement SNCC** et **veille**.

`collecte-form` couvre désormais : mission et zone ; identité légale et contacts ; secteur, activité, capacité et exportation ; produits et volumes multiples ; marchés multiples ; certifications multiples ; organismes et accréditations associés ; justificatifs, consentement et signature.

Chaque certification est structurée avec référentiel, organisme, pays, accréditeur, numéro d'accréditation, numéro du certificat, portée, produits couverts, délivrance, entrée en vigueur, expiration, statut, nature initiale/renouvellement et disponibilité de la copie. Les produits, marchés et certifications sont conservés comme tableaux dans le brouillon frontend. La soumission est bloquée si le noyau primordial est incomplet.

Les fichiers sélectionnés restent temporaires dans la maquette : leur téléversement et leurs métadonnées devront être gérés par FastAPI. Les champs du contrôle approfondi restent dans `validations` et `controle` afin de séparer les responsabilités.

### Affectation des dossiers

L'affectation ne signifie pas que la fiche est validée. Elle désigne le validateur responsable du contrôle de recevabilité. Toute affectation et réaffectation doit conserver l'auteur, la date, l'ancien responsable, le nouveau responsable, l'échéance et le motif.

### Certification

Une entreprise peut avoir plusieurs certifications. Une certification appartient à une entreprise, est délivrée par un organisme, vise une norme et peut couvrir plusieurs produits et sites. Sa délivrance, son expiration, sa suspension, son renouvellement et ses audits alimentent les échéances et alertes.

### Alertes et échéances

- Une échéance représente un événement futur ou dépassé : expiration, audit, renouvellement, contrôle HAUQE ou action corrective.
- Une alerte représente une situation exigeant une attention ou une action.
- Une alerte peut provenir d'une échéance ou d'une règle métier, puis être affectée à un responsable.
- Résoudre une alerte ne doit pas supprimer son historique.
- La configuration cible applique 180, 90 et 30 jours puis expiration. Une information complémentaire à 12 mois peut rester désactivée et paramétrable jusqu'à confirmation.
- Les alertes spéciales couvrent aussi suspension, retrait, changement d'organisme, modification de portée, changement de raison sociale, fermeture, audit en retard, absence de renouvellement, anomalie documentaire et incohérence.
- Le cycle doit conserver détection, vérification, notification, réponse, contrôle éventuel, mise à jour et clôture.
- Les alertes d'audit, d'expiration et d'échéance doivent pouvoir déclencher des courriels. L'administrateur configure dans `Règles & codification > Pilotage` l'activation, le premier délai, la fréquence de répétition, l'adresse d'expédition, l'adresse de réponse, les utilisateurs actifs destinataires et les adresses supplémentaires.
- Les destinataires internes sont sélectionnés parmi les comptes créés dans `Utilisateurs et accès`. Un compte bloqué ou inactif doit être exclu automatiquement lors de l'envoi.

## 8. Modèle PostgreSQL proposé

### Conventions générales

- Clés principales métier en `UUID`.
- Dates techniques en `timestamptz`, enregistrées en UTC et affichées en `Africa/Lome`.
- Dates civiles (`date_expiration`, `date_audit`) en type `date`.
- Courriels en `citext` si l'extension PostgreSQL est activée.
- Montants et scores décimaux en `numeric`, jamais en flottant.
- Paramètres flexibles et instantanés de calcul en `jsonb`.
- Colonnes communes recommandées : `created_at`, `created_by`, `updated_at`, `updated_by`, `version`.
- Ne pas supprimer physiquement les référentiels ou dossiers déjà utilisés : prévoir `is_active`, archivage ou désactivation.
- Les noms ci-dessous sont une proposition de dictionnaire logique, pas encore des migrations SQL.

### 8.1 Sécurité et habilitations

#### `users`

`id PK`, `email UNIQUE`, `password_hash`, `session_pin_hash NULL`, `session_pin_enabled`, `pin_updated_at NULL`, `first_name`, `last_name`, `phone`, `job_title`, `region_id FK NULL`, `status`, `mfa_enabled`, `failed_login_attempts`, `locked_until`, `last_login_at`, `created_at`, `updated_at`.

#### `roles`

`id PK`, `code UNIQUE`, `label`, `description`, `is_active`.

#### `permissions`

`id PK`, `code UNIQUE`, `label`, `description`.

#### `user_roles`

`user_id PK/FK`, `role_id PK/FK`, `valid_from`, `valid_to`, `assigned_by`.

#### `role_permissions`

`role_id PK/FK`, `permission_id PK/FK`.

#### Tables complémentaires

- `user_sessions(id, user_id FK, token_hash, ip_address, user_agent, last_activity_at, locked_at, unlocked_at, failed_unlock_attempts, expires_at, revoked_at, created_at)`.
- `password_reset_tokens(id, user_id FK, token_hash UNIQUE, expires_at, used_at, created_at)`.
- `notification_preferences(user_id FK, event_code, in_app, email, sms)`.
- `notifications(id, user_id FK, type, severity, title, message, resource_type, resource_id, read_at, created_at)`.

Relations : un utilisateur possède plusieurs rôles ; un rôle possède plusieurs permissions ; un utilisateur reçoit plusieurs notifications.

### 8.2 Géographie et référentiels

#### Géographie

- `regions(id PK, code UNIQUE, label, is_active)`.
- `prefectures(id PK, region_id FK, code UNIQUE, label, is_active)`.
- `communes(id PK, prefecture_id FK, code UNIQUE, label, is_active)`.

#### Référentiels génériques

- `reference_categories(id PK, code UNIQUE, label, description)`.
- `reference_items(id PK, category_id FK, parent_id FK NULL, code, label, description, sort_order, is_active, valid_from, valid_to, version)`.
- Contrainte unique recommandée : `(category_id, code, version)`.

Catégories attendues : formes juridiques, secteurs, activités, produits, marchés, types de documents, types d'alertes, types d'échéances, décisions, motifs de retour et niveaux de risque.

#### Normes

`standards(id PK, code UNIQUE, name, description, issuing_authority, version_label, effective_from, effective_to, is_active)`.

Les normes méritent une table explicite car elles sont directement liées aux certifications, accréditations et critères de contrôle.

### 8.3 Entreprises

#### `enterprises`

`id PK`, `code UNIQUE`, `legal_name`, `trade_name`, `legal_form_id FK`, `rccm UNIQUE NULL`, `nif UNIQUE NULL`, `creation_date`, `sector_id FK`, `main_activity_id FK`, `address`, `region_id FK`, `prefecture_id FK`, `commune_id FK`, `latitude`, `longitude`, `phone`, `email`, `website`, `employee_count`, `annual_turnover NULL`, `status`, `risk_level`, `observations`, colonnes d'audit.

#### Tables enfants

- `enterprise_contacts(id PK, enterprise_id FK, full_name, job_title, phone, email, is_primary)`.
- `enterprise_sites(id PK, enterprise_id FK, name, site_type, address, region_id FK, prefecture_id FK, commune_id FK, latitude, longitude, is_active)`.
- `enterprise_products(id PK, enterprise_id FK, product_id FK NULL, product_name, annual_volume, unit_id FK, production_capacity, is_active)`.
- `enterprise_markets(enterprise_id FK, market_reference_id FK, details, PK composite)`.

Relations : une entreprise possède plusieurs contacts, sites, produits, certifications, collectes, contrôles, alertes et échéances.

### 8.4 Organismes certificateurs et accréditations

#### `certification_bodies`

`id PK`, `code UNIQUE`, `name`, `acronym`, `body_type`, `country_code`, `registration_number`, `address`, `has_togo_representation`, `website`, `email`, `phone`, `contact_name`, `contact_job_title`, `status`, `last_verified_at`, `observations`, colonnes d'audit.

#### `accreditations`

`id PK`, `body_id FK`, `standard_id FK`, `accreditor_name`, `accreditation_number`, `scope`, `issued_at`, `expires_at`, `status`, `verification_reference`, `document_id FK NULL`.

Relations : un organisme délivre plusieurs certifications et possède plusieurs accréditations ; une accréditation cible une norme.

### 8.5 Certifications

#### `certifications`

`id PK`, `code UNIQUE`, `enterprise_id FK`, `body_id FK`, `standard_id FK`, `certificate_number`, `scope`, `issue_date`, `effective_date`, `expiry_date`, `status`, `verification_status`, `authenticity_status`, `last_verified_at`, `verified_by FK users NULL`, `notes`, colonnes d'audit.

Contrainte unique à étudier : `(body_id, certificate_number)`.

#### Tables associatives et événements

- `certification_products(certification_id FK, enterprise_product_id FK, PK composite)`.
- `certification_sites(certification_id FK, enterprise_site_id FK, PK composite)`.
- `certification_audits(id PK, certification_id FK, audit_type, planned_date, performed_date, result, report_document_id FK NULL, next_audit_date, observations)`.
- `certification_status_history(id PK, certification_id FK, old_status, new_status, changed_by FK, reason, changed_at)`.

### 8.6 Documents et preuves

#### `documents`

`id PK`, `document_type_id FK`, `file_name`, `storage_key UNIQUE`, `mime_type`, `size_bytes`, `checksum`, `version`, `is_current`, `status`, `uploaded_by FK`, `uploaded_at`, `verified_by FK NULL`, `verified_at NULL`, `observations`.

Pour garantir l'intégrité référentielle, privilégier des tables de liaison explicites plutôt qu'un unique couple polymorphe `resource_type/resource_id` :

- `enterprise_documents(enterprise_id, document_id)` ;
- `certification_documents(certification_id, document_id)` ;
- `collection_documents(collection_form_id, document_id)` ;
- `control_documents(control_id, document_id)` ;
- `accreditation_documents(accreditation_id, document_id)`.

### 8.7 Campagnes, missions et fiches de collecte

#### `campaigns`

`id PK`, `code UNIQUE`, `name`, `description`, `start_date`, `end_date`, `status`, `target_count`, `created_by FK`.

#### `collection_missions`

`id PK`, `code UNIQUE`, `campaign_id FK NULL`, `enterprise_id FK`, `assigned_agent_id FK users`, `planned_date`, `started_at`, `submitted_at`, `status`, `progress_percent`, `priority`, `purpose`, `created_by FK`, colonnes d'audit.

#### `collection_forms`

`id PK`, `mission_id FK`, `form_version`, `revision_number`, `is_current`, `status`, `consent_obtained`, `declarant_name`, `declarant_job_title`, `signature_status`, `general_observations`, `saved_at`, `submitted_at`.

La charge utile API doit être organisée en objets `mission`, `enterprise`, `contacts[]`, `products[]`, `markets[]`, `certifications[]`, `documents[]` et `consent`. Ne pas aplatir les éléments multiples dans des colonnes numérotées.

Contrainte : une seule révision courante par mission.

#### Tables de contenu de collecte

- `collection_products(id PK, form_id FK, product_id FK NULL, declared_name, volume, unit_id FK, capacity, target_markets)`.
- `collection_certifications(id PK, form_id FK, certification_id FK NULL, declared_standard, declared_number, declared_body, issue_date, expiry_date, authenticity_status, traceability_note)`.
- `collection_form_answers(id PK, form_id FK, field_code, value_jsonb)` uniquement pour les champs réellement dynamiques ; les champs majeurs doivent rester structurés.
- `collection_status_history(id PK, mission_id FK, old_status, new_status, actor_id FK, comment, created_at)`.

Les valeurs déclarées doivent rester dans la révision de collecte même lorsque la fiche officielle de l'entreprise est ensuite corrigée : cela assure la preuve historique.

### 8.8 Affectations et validations

#### `validation_assignments`

`id PK`, `mission_id FK`, `validator_id FK users`, `assigned_by FK users`, `assigned_at`, `due_at`, `status`, `reassigned_from_id FK NULL`, `assignment_note`.

Une seule affectation active par mission, mais toutes les anciennes affectations sont conservées.

#### `validations`

`id PK`, `mission_id FK`, `assignment_id FK`, `validator_id FK`, `status`, `decision`, `completeness_score`, `internal_note`, `started_at`, `completed_at`.

#### `validation_checks`

`id PK`, `validation_id FK`, `check_code`, `label_snapshot`, `result`, `comment`, `evidence_document_id FK NULL`.

#### `correction_requests`

`id PK`, `validation_id FK`, `reason_code`, `comment`, `requested_by FK`, `requested_at`, `due_at`, `resubmitted_at`, `status`.

Relations : une mission peut avoir plusieurs affectations et cycles de validation ; une validation comporte plusieurs contrôles de complétude et demandes de correction.

### 8.9 Grille de contrôle, scoring et actions correctives

#### Référentiel de contrôle

- `control_domains(id PK, code UNIQUE, label, description, sort_order, is_active)`.
- `control_criteria(id PK, domain_id FK, code, label, description, max_score DEFAULT 2, sort_order, rule_version_id FK, is_active)`.

La grille FUCCS documentée comporte 28 critères répartis en quatre rubriques. Toute autre organisation par domaines doit être versionnée et validée avant utilisation.

#### `controls`

`id PK`, `code UNIQUE`, `mission_id FK`, `enterprise_id FK`, `validation_id FK`, `controller_id FK users`, `status`, `started_at`, `completed_at`, `raw_score`, `max_raw_score`, `normalized_score`, `decision_code`, `decision_reason`, `rule_version_id FK`, `formula_snapshot jsonb`.

#### `control_scores`

`id PK`, `control_id FK`, `criterion_id FK`, `criterion_label_snapshot`, `score`, `comment`, `evidence_document_id FK NULL`, `updated_by`, `updated_at`.

Contraintes : `score >= 0`, `score <= max_score`, et unicité `(control_id, criterion_id)`.

#### Constatations et suivi

- `control_findings(id PK, control_id FK, finding_type, severity, title, description, status, detected_at)`.
- `score_snapshots(id PK, control_id FK, raw_score, normalized_score, formula_version, calculation_details jsonb, calculated_at)`.
- `corrective_actions(id PK, control_id FK, finding_id FK NULL, enterprise_id FK, title, description, responsible_user_id FK NULL, responsible_contact_id FK NULL, due_date, priority, status, completed_at, verified_by FK NULL, verified_at NULL)`.

Le snapshot des critères et de la formule est indispensable : un ancien contrôle doit rester reproductible même après modification des règles.

#### Vérification documentaire

- `verification_cases(id PK, mission_id FK, certification_id FK, assigned_to FK, status, opinion, started_at, completed_at, source_count, summary, created_at)`.
- `verification_checks(id PK, case_id FK, check_code, result, observation, evidence_document_id FK NULL, checked_at, checked_by FK)`.
- `verification_anomalies(id PK, case_id FK, category, severity, description, status, resolution, escalated_at NULL, resolved_at NULL)`.
- `verification_requests(id PK, case_id FK, body_id FK NULL, enterprise_id FK NULL, channel, subject, sent_at, expected_by, response_received_at NULL, status, response_document_id FK NULL)`.

Avis normalisés : `verified_compliant`, `verified_with_reservation`, `not_verified`, `suspect`, `rejected`.

#### Intégration BNEC

- `integration_jobs(id PK, validation_id FK, status, assigned_admin_id FK, precheck_result, started_at, completed_at, postcheck_result, backup_reference, notification_sent_at)`.
- `integration_items(id PK, job_id FK, entity_type, source_revision_id, target_id NULL, action, generated_code NULL, status, error_message NULL)`.

L'intégration doit être impossible sans validation formelle. Les contrôles préalables et postérieurs, les codes générés et les erreurs doivent rester historisés.

#### INFC et SNCC

- `infc_formula_versions(id PK, version_label UNIQUE, status, effective_from, approved_by, approved_at, calculation_spec jsonb)`.
- `infc_domain_scores(id PK, control_id FK, formula_version_id FK, domain_code, raw_value, weighted_value, evidence_summary)`.
- `infc_results(id PK, certification_id FK, control_id FK, formula_version_id FK, score, level, calculated_at, validated_by NULL, validated_at NULL)`.
- `sncc_classifications(id PK, certification_id FK, infc_result_id FK NULL, class_code, administrative_status, risk_level, proposed_by, verified_by NULL, validated_by NULL, reason, effective_at)`.
- `sncc_history(id PK, classification_id FK, old_values jsonb, new_values jsonb, changed_by, changed_at, reason)`.

Ne jamais calculer silencieusement l'INFC en appliquant une simple règle de trois au score FUCCS sur 56. La formule officielle doit être explicite, versionnée et reproductible.

### 8.10 Échéances, alertes et affectation

#### `deadlines`

`id PK`, `code UNIQUE`, `enterprise_id FK NULL`, `certification_id FK NULL`, `control_id FK NULL`, `corrective_action_id FK NULL`, `deadline_type`, `title`, `description`, `due_date`, `owner_user_id FK`, `priority`, `status`, `completed_at`, `created_by FK`, colonnes d'audit.

Une règle doit imposer qu'au moins une ressource métier soit associée.

#### `alerts`

`id PK`, `code UNIQUE`, `alert_type`, `severity`, `title`, `message`, `enterprise_id FK NULL`, `deadline_id FK NULL`, `resource_type`, `resource_id`, `status`, `assigned_to FK users NULL`, `assigned_by FK users NULL`, `assigned_at`, `due_at`, `created_at`, `acknowledged_at`, `resolved_at`, `resolution_note`.

#### `alert_history`

`id PK`, `alert_id FK`, `action`, `actor_id FK`, `old_values jsonb`, `new_values jsonb`, `comment`, `created_at`.

#### Notifications email

- `alert_notification_rules(id PK, alert_type, enabled, first_notice_days, repeat_every_days, sender_email, reply_to_email, rule_version_id FK, updated_by FK)`.
- `alert_rule_recipients(rule_id FK, user_id FK NULL, external_email NULL, recipient_type, is_active)` avec contrainte imposant un utilisateur ou une adresse externe.
- `notification_deliveries(id PK, alert_id FK, recipient_email, subject, template_code, status, provider_message_id, queued_at, sent_at, failed_at, error_message, retry_count)`.

Les envois doivent être exécutés en arrière-plan, dédupliqués, retentés en cas d'échec et enregistrés dans le journal d'audit. Les adresses externes doivent être validées et les secrets SMTP/API conservés hors de la base métier.

Les liens polymorphes `resource_type/resource_id` servent à la navigation, mais les ressources critiques doivent également disposer d'une FK explicite quand elle existe.

#### Cellule de veille, relances et rapports

- `watch_cases(id PK, certification_id FK, event_type, priority, status, opened_at, owner_user_id, last_reviewed_at, next_action_at, closed_at NULL)`.
- `follow_ups(id PK, watch_case_id FK, recipient_type, recipient_id NULL, channel, subject, sent_at, due_at, response_at NULL, outcome, document_id FK NULL)`.
- `watch_reports(id PK, report_type, period_start, period_end, status, prepared_by, validated_by NULL, document_id NULL, created_at)` avec types `monthly_note` et `quarterly_report`.
- `watch_kpi_snapshots(id PK, period, certificates_monitored, alerts_on_time_rate, renewals_followed_rate, average_update_delay, data_reliability_rate)`.

#### Décisions et plans d'action

- `decision_notes(id PK, period, context, findings, major_risks, options jsonb, recommendation, status, prepared_by, approved_by NULL, approved_at NULL)`.
- `institutional_decisions(id PK, note_id FK NULL, code UNIQUE, title, decision_text, authority_user_id, decided_at, priority, status)`.
- `decision_actions(id PK, decision_id FK, title, owner_user_id, resources, due_date, indicator, target, status, progress_percent, completed_at NULL)`.
- `decision_reviews(id PK, decision_id FK, reviewed_at, result, impact_summary, adjustments, reviewed_by)`.

### 8.11 Rapports et exports

- `report_templates(id PK, code UNIQUE, name, category, allowed_formats, configuration_schema jsonb, is_active)`.
- `saved_report_configs(id PK, user_id FK, template_id FK, name, filters jsonb, sections jsonb, default_format, created_at)`.
- `report_jobs(id PK, template_id FK, requested_by FK, status, filters_snapshot jsonb, format, storage_key NULL, file_size NULL, started_at, completed_at, error_message NULL)`.

Les gros exports doivent être produits par une tâche asynchrone et non dans la requête HTTP principale.

### 8.12 Règles métier, codification et séquences

#### `rule_versions`

`id PK`, `version_label UNIQUE`, `status`, `effective_from`, `effective_to`, `approval_reference`, `change_reason`, `created_by`, `published_by NULL`, `published_at NULL`.

#### `business_rules`

`id PK`, `rule_version_id FK`, `family`, `rule_key`, `value jsonb`, `data_type`, `description` ; unicité `(rule_version_id, rule_key)`.

#### `code_models`

`id PK`, `rule_version_id FK`, `entity_type`, `pattern`, `separator`, `reset_frequency`, `is_active`.

#### `sequences`

`id PK`, `entity_type`, `scope_key`, `year NULL`, `current_value`, `updated_at` ; unicité `(entity_type, scope_key, year)`.

La génération d'un code doit être transactionnelle avec verrouillage afin d'éviter les doublons. Le format officiel, notamment les références de type `COTAG TGN/COTAG/XXX/DG/2025`, reste à confirmer.

### 8.13 Journal d'audit

#### `audit_events`

`id PK`, `occurred_at`, `actor_user_id FK NULL`, `action`, `category`, `resource_type`, `resource_id`, `result`, `ip_address`, `user_agent`, `correlation_id`, `before_values jsonb`, `after_values jsonb`, `metadata jsonb`, `previous_hash NULL`, `event_hash NULL`.

Le journal doit être en écriture seule pour l'application : pas de modification ni de suppression par les utilisateurs ordinaires. Les champs sensibles tels que mots de passe, jetons ou secrets ne doivent jamais y être enregistrés.

## 9. Relations essentielles résumées

```text
Entreprise 1 ── N Sites / Contacts / Produits
Entreprise 1 ── N Certifications N ── 1 Organisme certificateur
Certification N ── 1 Norme
Certification N ── N Produits et Sites
Organisme 1 ── N Accréditations N ── 1 Norme

Campagne 1 ── N Missions
Entreprise 1 ── N Missions
Agent 1 ── N Missions affectées
Mission 1 ── N Révisions de fiche de collecte
Mission 1 ── N Affectations de validation
Validation 1 ── N Vérifications / Demandes de correction
Validation recevable 1 ── 0..N Contrôles

Contrôle 1 ── N Notes de critères
Contrôle 1 ── N Constatations
Contrôle 1 ── N Actions correctives
Contrôle N ── 1 Version de règles

Entreprise / Certification / Contrôle / Action corrective ── N Échéances
Échéance ou règle métier 1 ── 0..N Alertes
Utilisateur 1 ── N Affectations / Notifications / Actions auditées
```

## 10. Statuts provisoires à normaliser

| Objet | Statuts proposés |
|---|---|
| Utilisateur | `pending`, `active`, `inactive`, `blocked` |
| Entreprise | `active`, `inactive`, `at_risk`, `archived` |
| Organisme | `to_verify`, `recognized`, `suspended`, `withdrawn`, `inactive` |
| Certification | `draft`, `valid`, `expiring`, `expired`, `suspended`, `revoked` |
| Campagne | `draft`, `planned`, `active`, `closed`, `cancelled` |
| Mission/collecte | `planned`, `in_progress`, `draft`, `submitted`, `assigned`, `under_review`, `correction_requested`, `resubmitted`, `receivable`, `control_in_progress`, `completed`, `validated`, `rejected` |
| Affectation | `active`, `completed`, `reassigned`, `cancelled` |
| Vérification | `assigned`, `in_progress`, `awaiting_information`, `verified_compliant`, `verified_with_reservation`, `not_verified`, `suspect`, `rejected` |
| Validation | `pending`, `in_review`, `validated`, `validated_with_reservation`, `deferred`, `rejected` |
| Intégration | `queued`, `precheck`, `integrating`, `postcheck`, `completed`, `failed`, `returned` |
| Contrôle | `draft`, `in_progress`, `finalized`, `cancelled` |
| Classement SNCC | classes `A+`, `A`, `B`, `C`, `D` ; statuts `VA`, `RE`, `SU`, `RT`, `EX`, `VE` ; risques `R1` à `R5` |
| Action corrective | `open`, `in_progress`, `completed`, `verified`, `overdue`, `cancelled` |
| Échéance | `planned`, `due`, `late`, `completed`, `cancelled` |
| Alerte | `new`, `assigned`, `in_progress`, `resolved`, `dismissed` |
| Export | `queued`, `running`, `completed`, `failed`, `expired` |
| Version de règle | `draft`, `published`, `archived` |

Éviter de disperser les valeurs sous forme de chaînes libres. Employer des enums applicatifs contrôlés ou des tables de statut lorsque l'administration doit être dynamique.

## 11. API FastAPI proposée

Préfixe recommandé : `/api/v1`.

```text
/auth/login, /auth/refresh, /auth/logout, /auth/password-reset
/users, /roles, /permissions, /me, /notifications
/references, /regions, /prefectures, /communes, /standards
/enterprises, /enterprises/{id}/contacts|sites|products|documents
/certification-bodies, /accreditations
/certifications, /certifications/{id}/audits|documents|history
/campaigns, /missions, /collections, /collections/{id}/submit
/verification-cases, /verification-requests, /verification-anomalies
/validation-assignments, /validations, /correction-requests, /integration-jobs
/control-domains, /control-criteria, /controls, /scores, /findings
/infc/formulas, /infc/results, /sncc/classifications
/corrective-actions, /deadlines, /alerts, /alerts/{id}/assign
/watch-cases, /follow-ups, /watch-reports
/decision-notes, /decisions, /decision-actions
/report-templates, /reports, /report-jobs
/rule-versions, /business-rules, /code-models
/audit-events
```

Principes : pagination, recherche, filtres, tri, validation Pydantic, réponses normalisées, contrôle d'accès au niveau de chaque objet et gestion des conflits par numéro de version.

## 12. Sécurité et exigences non fonctionnelles

- Hachage des mots de passe avec Argon2id ou bcrypt correctement configuré.
- Jetons courts + renouvellement sécurisé, idéalement cookies `HttpOnly`, `Secure`, `SameSite`, avec protection CSRF si cookies.
- RBAC fondé sur les permissions et contrôle d'accès sur chaque dossier.
- MFA au minimum pour administrateurs et superviseurs si possible.
- Limitation des tentatives de connexion et verrouillage temporaire.
- Verrouillage après inactivité avec reprise par code privé secondaire ou déconnexion. Minimum actuel : cinq caractères ; six ou plus sont recommandés en production.
- Ne jamais conserver ce code en clair ni dans `localStorage` en production : utiliser `session_pin_hash`, Argon2id/bcrypt et une vérification FastAPI. Après cinq erreurs, révoquer la session.
- Validation stricte des données et protection contre injections/XSS.
- Documents : liste de MIME autorisés, taille maximale, checksum, antivirus si disponible et stockage hors répertoire public.
- Journal d'audit des connexions, lectures sensibles, créations, modifications, décisions, affectations et exports.
- Migrations avec Alembic ; aucune création manuelle non versionnée en production.
- Sauvegardes PostgreSQL chiffrées, test de restauration et politique de rétention.
- Index sur codes, statuts, dates d'échéance, entreprises, certifications, responsables et clés étrangères.
- Tests unitaires, intégration API, permissions et parcours métier critiques.
- Environnements séparés : développement, recette et production.
- Documentation d'installation, d'exploitation, dictionnaire de données et guide utilisateur remis à la HAUQE.

## 13. Points à confirmer impérativement avec la HAUQE

1. La fiche officielle de collecte et tous les champs envoyés par M. Nyanuste.
2. Les champs obligatoires, conditionnels, répétables et justificatifs exigés.
3. La confirmation des 28 critères FUCCS, de leurs quatre rubriques, des commentaires obligatoires et des décisions associées au score sur 56.
4. La formule officielle de l'INFC sur 100, ses six domaines, les données sources, les arrondis et le traitement des données manquantes.
5. La matrice SNCC : classes, statuts, risques, règles de reclassement et circuit de validation.
6. Les rôles, permissions, délégations et niveaux de confidentialité réels, notamment ceux de la CVC.
7. Les statuts et transitions autorisées de la collecte jusqu'à l'intégration, au classement et à la veille.
8. Les formats officiels de codification et les règles de remise à zéro des séquences.
9. Les modalités complémentaires des alertes. Les seuils métier principaux sont désormais validés à 180/90/30 jours puis expiration ; l'éventuel maintien d'une information à 12 mois reste à confirmer.
10. Les pièces obligatoires pour entreprises, organismes, certifications, vérifications, contrôles et mises à jour.
11. Les rapports officiels, leurs en-têtes, signatures, logos, fréquences et autorités de validation.
12. Les cinq tableaux de bord, leurs indicateurs, leurs destinataires et le périmètre exact des données publiques.
13. Le niveau géographique exact attendu : région, préfecture, commune, localité et coordonnées GPS.
14. La durée de conservation, l'archivage et les règles de protection des données.
15. Les délais et canaux officiels d'échange avec les organismes certificateurs et les entreprises.
16. Les éventuelles intégrations externes et les sources de vérification des certificats/accréditations.
17. L'hébergement, le domaine, HTTPS, les sauvegardes et les responsabilités après transfert.

## 14. Ordre recommandé pour la suite

1. Faire une recette écran par écran avec les représentants HAUQE.
2. Appliquer les règles RM validées et ne soumettre à arbitrage que les sujets encore ouverts : codification nationale, détails des statuts/transitions, formule opérationnelle INFC et visas de validation.
3. Intégrer définitivement les champs de la fiche FUCCS et des fiches spécialisées dans les écrans concernés.
4. Corriger le workflow frontend pour distinguer vérification, contrôle, validation et intégration.
5. Refondre le scoring pour séparer FUCCS, INFC et SNCC.
6. Ajouter la CVC, les cinq tableaux de bord, les échanges avec les OC, les décisions et la gestion documentaire.
7. Valider les parcours, rôles, statuts, critères, calculs, codifications et rapports.
8. Geler un dictionnaire de données et un catalogue de règles versionnés.
9. Produire et valider le diagramme entité-relation PostgreSQL.
10. Créer SQLAlchemy, Alembic et les modèles Pydantic.
11. Implémenter l'authentification, les utilisateurs, rôles et permissions.
12. Développer les API des référentiels, entreprises, organismes et certifications.
13. Développer collecte, vérification, contrôle, validation, intégration, INFC, SNCC et veille.
14. Développer échéances, alertes, notifications, décisions, rapports et audit.
15. Remplacer progressivement les simulations JavaScript par les appels de `api.js`.
16. Tester les permissions, calculs, exports, pièces jointes et parcours complets.
17. Préparer déploiement, sauvegarde, transfert, formation et maintenance.
18. Finaliser `GUIDE_UTILISATION.md` sans omettre les boutons, menus, fenêtres, erreurs et profils.

## 15. Référentiel normatif des règles métiers validées

Le fichier **Règles métier validation GFA — version améliorée** contient le référentiel autorisé RM-01 à RM-51 : 17 règles validées, 23 règles modifiées et retenues et 11 nouvelles règles. Trois règles supplémentaires seront communiquées en cours de projet ; aucun contenu ne doit leur être attribué avant réception.

### 15.1 Hiérarchie documentaire

En cas de divergence, appliquer :

1. les règles RM validées ;
2. les procédures opérationnelles ;
3. les documents INFC et SNCC ;
4. le guide méthodologique ;
5. les anciennes propositions et simulations.

Les règles fixent notamment les seuils d'alerte 180/90/30 jours puis expiration. Les valeurs 12/6/3/1 mois restent historiques ou complémentaires. La classification globale de l'entreprise, confirmée par le maître d'ouvrage, est différente de l'INFC d'une certification et du classement SNCC.

### 15.2 Impacts métier obligatoires

#### Certifications

- obtention obligatoire et expiration conditionnelle au référentiel ;
- contrôles chronologiques bloquants ;
- justificatif officiel obligatoire, sinon statut **À vérifier** ;
- unicité entreprise-organisme-référentiel-périmètre ;
- preuve officielle et pondération transitoire de renouvellement ;
- statut **Non renouvelée** six mois après expiration hors procédure justifiée ;
- versions et historique de tous les événements de certification.

#### Alertes et échéances

- niveau 1 Information à 180 jours ;
- niveau 2 Surveillance à 90 jours ;
- niveau 3 Urgence à 30 jours ;
- niveau 4 Critique à l'expiration, maintenu jusqu'à régularisation ou clôture ;
- relances, notifications, réponses, escalades et clôtures historisées.

#### Entreprises

- RCCM unique, mais entreprise sans RCCM autorisée au statut **En attente de régularisation** ;
- minimum requis : nom, localité, région et téléphone ou courriel ;
- statut actif calculé depuis les certifications ;
- risque automatique sous 90 jours pour une certification stratégique ;
- non-conformité uniquement sans certification valide ni renouvellement officiel ;
- doublons multicritères, identifiant national permanent, versions et historique administratif.

#### Organismes certificateurs

- organisme non accrédité enregistrable ;
- certificats correspondants **À vérifier** ;
- accréditations structurées par référentiel, domaine, périmètre et validité ;
- reclassement **Sous vérification** après suspension ou perte d'accréditation ;
- décision HAUQE avant invalidation ;
- contrôle des doublons et historique des versions.

#### Trois résultats séparés

- classification entreprise : Conforme 85-100, À surveiller 60-84, Non conforme sous 60 ;
- INFC : indice propre à la certification sur 100 avec six domaines et niveaux propres ;
- SNCC : classes A+ à D, statuts VA/RE/SU/RT/EX/VE et risques R1 à R5.

Chaque calcul doit conserver modèle, version, date, données sources et historique.

#### Collecte et workflow

Le parcours devient :

**Brouillon → Soumise → Vérification → Contrôle → Validation définitive → Intégration BNEC → Classification entreprise/INFC → SNCC → Veille**

Un brouillon incomplet est autorisé, mais la soumission est bloquée si les champs obligatoires manquent. Une fiche papier doit être saisie sous cinq jours ouvrables. Après validation, toute modification exige une autorisation, une nouvelle version et un audit.

#### Utilisateurs, sécurité et exports

- permissions configurables et moindre privilège ;
- lecture seule par défaut des intervenants externes ;
- export soumis à permission, motif et audit détaillé ;
- désactivation après 180 jours d'inactivité et préavis de 30 jours ;
- verrouillage après cinq échecs, durée paramétrable et notifications ;
- séparation entre verrouillage de reprise de session et verrouillage du compte.

#### Audit, archivage et conservation

- audit non modifiable des créations, consultations, modifications, validations, archivages, exports et authentifications ;
- adresse IP si disponible ;
- aucune suppression physique des données métier ;
- archivage motivé et accès restreint ;
- versions avant/après des entreprises, certifications et organismes ;
- conservation minimale de dix ans après expiration ou retrait de la dernière certification.

#### Sauvegardes et continuité

- sauvegardes quotidiennes, hebdomadaires et mensuelles ;
- rétention configurable ;
- historique, statut et incidents ;
- demandes de restauration ;
- tests périodiques de restauration et preuve d'intégrité ;
- écran de supervision réservé à l'administrateur système.

#### Qualité et plans d'action

Une revue annuelle couvre exactitude, complétude, cohérence, unicité, traçabilité et conformité. Les anomalies donnent lieu à des constats, responsables, délais, preuves, actions correctives, suivi de l'effet et clôture.

#### Publication

Toute publication de données, statistiques, indicateurs ou rapports suit :

**Brouillon → Soumis → Approuvé → Publié → Retiré**

La Direction Générale ou l'autorité compétente valide la publication. Les données publiques sont agrégées et séparées des données internes confidentielles.

#### Administration des règles

L'interface sécurisée administre pondérations, modèles de scoring, seuils, alertes, délais, référentiels, nomenclatures, catégories, permissions, codifications et règles de complétude. Chaque changement possède auteur, motif, valeurs avant/après, date d'effet, version, état de publication et audit, sans changement du code source.

### 15.3 Compléments PostgreSQL obligatoires

Ajouter ou confirmer :

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

Toutes les suppressions métier sont logiques et aucun identifiant national n'est réattribué.

### 15.4 Compléments FastAPI obligatoires

Prévoir :

- `/api/v1/business-rules` et les versions ;
- `/api/v1/scoring-models` ;
- `/api/v1/enterprises/{id}/score` et `/completeness` ;
- `/api/v1/certifications/{id}/renewal` et `/history` ;
- `/api/v1/certification-bodies/{id}/accreditations` ;
- `/api/v1/duplicates/check` ;
- `/api/v1/archives` et `/api/v1/security-events` ;
- `/api/v1/backups` et `/api/v1/restore-tests` ;
- `/api/v1/data-quality-reviews` et `/api/v1/action-plans` ;
- `/api/v1/publications` et `/api/v1/public/indicators`.

Les calculs et transitions sont exécutés côté FastAPI/PostgreSQL et non uniquement dans JavaScript.

### 15.5 Traçabilité et priorités

Maintenir une matrice :

**règle RM → écran → permission → table → route API → événement d'audit → test**

Priorités :

- P0 : dates, pièces, doublons, alertes, séparation des trois résultats, workflow, permissions et audit ;
- P1 : versions, renouvellements, qualité, décisions, publications et paramètres ;
- P2 : sauvegardes, restauration, revue annuelle et diffusion publique.

Mettre à jour `FEUILLE_DE_ROUTE_FRONTEND.md`, `GUIDE_UTILISATION.md`, le dictionnaire de données, le catalogue des statuts, la matrice rôles/permissions et le catalogue versionné des règles.

## 16. Règle de continuité documentaire

Après chaque modification importante :

- mettre à jour la page concernée dans `FEUILLE_DE_ROUTE_FRONTEND.md` ;
- documenter son utilisation dans `GUIDE_UTILISATION.md` ;
- modifier ce fichier si l'architecture, la base, les rôles ou le workflow changent ;
- noter séparément ce qui est **validé par la HAUQE**, **proposé**, **simulé** ou **implémenté**.

Cette distinction est essentielle : une belle interface ne constitue pas encore une règle métier approuvée ni une fonctionnalité backend opérationnelle.

## 17. État du frontend après intégration des règles métier — 23 juillet 2026

Les écrans suivants disposent désormais d'une **maquette fonctionnelle navigable**, alimentée par des données de démonstration : vérifications, intégrations BNEC, calcul INFC, classement SNCC, Cellule de Veille, décisions et plans d'action, mises à jour, gestion documentaire, incidents, amélioration continue, qualité des données, sauvegardes, publications, échanges avec les organismes, tableaux de bord tactique/stratégique/annuel, baromètre et espace public.

Le composant commun de ces écrans fournit recherche, filtres, priorités, vues personnelles, tableau, panneau de détail, création simulée, avancement d'état et retour utilisateur. Les routes sont déclarées dans le routeur de la SPA et les accès principaux sont présents dans la navigation.

Les adaptations suivantes sont également visibles :

- RCCM non bloquant lors de la création d'une entreprise, avec statut de régularisation ;
- règles de dates et d'expiration, preuve principale et option sans date d'expiration pour une certification ;
- conservation des organismes non accrédités avec mise sous vérification de leurs certificats ;
- séparation explicite entre classification entreprise, FUCCS, INFC sur 100 et classement SNCC ;
- seuils d'alerte à 180, 90 et 30 jours, puis expiration ;
- rappel du workflow Collecte → Vérification → Contrôle → Validation → Intégration → Classement → Veille ;
- rôles institutionnels enrichis dans l'administration.

Ces fonctions restent **frontend uniquement** : les créations, transitions, calculs, exports et journaux affichés sont simulés. Le backend FastAPI devra les remplacer par les API, permissions, transactions, validations et événements d'audit prévus dans les sections précédentes.
