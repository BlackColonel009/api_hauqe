# FEUILLE DE ROUTE BACKEND — HAUQE CERTIF

**Projet :** HAUQE Certif / BNEC  
**Backend :** FastAPI + PostgreSQL + SQLAlchemy 2 async + Psycopg 3 + Alembic  
**Dernière mise à jour :** 2026-07-26  
**Statut global :** backend métier principal implémenté ; verrou de reprise/session intégré côté authentification et interaction avec le timeout d’inactivité ajustée ; MFA-login, réactivation RM-33 et validation runtime globale restent à finaliser pendant la recette API ↔ frontend. SMTP e-mail volontairement différé.

---

## 1. Règle de continuité du projet

Ce document est la **source de reprise rapide du backend**.

À chaque avancée significative du backend, il doit être mis à jour avec :

- ce qui vient d’être réalisé ;
- ce qui a été testé et validé ;
- les fichiers ajoutés ou modifiés ;
- les endpoints disponibles ;
- les décisions techniques prises ;
- les paramètres `.env` importants ;
- les points de vigilance ;
- la prochaine étape exacte.

**Ne jamais repartir de zéro dans une nouvelle discussion.**  
Le travail doit reprendre à partir de la dernière section « Prochaine étape ».

---

# 2. Décisions structurantes à ne pas changer sans validation explicite

## 2.1 Base de données

La structure actuelle de la base est conservée.

Aucune refonte arbitraire du MPD/MCD/MLD ne doit être faite.

Référence initiale validée (MPD/MCD/MLD d'origine) :

- **66 tables métier**
- **843 colonnes**
- **107 clés étrangères**
- **9 contraintes UNIQUE**
- **66 clés primaires**

Extension runtime explicitement décidée pour **Mon compte / Sécurité utilisateur** :

- `preferences_utilisateur`
- `securite_compte_utilisateur`
- `verrous_session_utilisateur`
- `jetons_securite_utilisateur`

**État physique cible après migration `c5b7a8f2d901` : 70 tables métier.**

Les documents PowerDesigner historiques restent la référence de la version initiale 66 tables ; cette extension doit être reportée dans le prochain cycle documentaire MCD/MLD/MPD.
- UUID comme identifiants techniques
- PostgreSQL
- `gen_random_uuid()` pour les UUID
- `TIMESTAMPTZ` pour les événements techniques concernés
- `created_at` / `updated_at` sur les tables prévues par le modèle

La table technique Alembic :

- `alembic_version`

ne fait pas partie des 66 tables métier.

## 2.2 Frontend / API / base

Les attributs déjà présents dans la base restent dans la base.

Le frontend et les schémas API n’exposent que les attributs nécessaires au besoin courant.

Exemple :

- `entreprises.chiffre_affaires` reste physiquement dans PostgreSQL ;
- il peut rester masqué du formulaire frontend actuel ;
- aucune suppression physique n’est faite uniquement parce qu’un champ n’est pas encore utilisé.

## 2.3 Grille FUCCS

La grille est versionnée en base.

La version frontend active utilise actuellement **24 critères**.

Ne pas coder « 24 » comme une contrainte structurelle permanente dans PostgreSQL.

Les critères restent des lignes de données versionnées.

Une version publiée doit être considérée comme immuable ; toute évolution doit conduire à une nouvelle version.

## 2.4 Journal d’audit

Le journal d’audit est conservé et fait partie du socle obligatoire.

Table :

- `evenements_audit`

Les opérations sensibles doivent être journalisées côté serveur.

Ne jamais mettre dans l’audit :

- mot de passe en clair ;
- hash du mot de passe ;
- token Bearer brut ;
- secrets applicatifs.

---

# 3. Architecture backend retenue

Structure générale :

```text
HAUQE_CERTIF/
├── app/
│   ├── main.py
│   ├── config/
│   ├── database/
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── rules/
│   ├── permissions/
│   ├── audit/
│   ├── middleware/
│   ├── tasks/
│   ├── utils/
│   ├── scripts/
│   ├── routes/
│   │   ├── web.py
│   │   └── api/
│   │       └── v1/
│   ├── static/
│   └── templates/
├── alembic/
├── tests/
├── uploads/
├── requirements.txt
├── alembic.ini
├── .env
├── .env.example
└── README.md
```

Architecture métier :

```text
Route FastAPI
      ↓
Service
      ↓
Repository
      ↓
SQLAlchemy
      ↓
PostgreSQL
```

Les permissions, règles métier et audits sont contrôlés côté serveur.

Le frontend ne constitue jamais une source d’autorité.

---

# 4. État de réalisation

## PHASE 0 — Audit du frontend existant

### Statut
✅ Réalisé

### Constat principal

Le frontend existant fonctionnait principalement avec :

- données simulées ;
- `localStorage` ;
- logique côté navigateur ;
- absence de backend métier réel ;
- absence de permissions serveur ;
- audit visuel uniquement.

Décision :

- conserver l’interface existante ;
- remplacer progressivement les données simulées par l’API FastAPI réelle.

---

# 5. PHASE 1 — Modèles SQLAlchemy

## Statut
✅ TERMINÉ ET AUDITÉ

Les **66 tables** du dictionnaire ont été modélisées en SQLAlchemy.

Familles couvertes :

### Sécurité / audit
- `zones_administratives`
- `utilisateurs`
- `roles`
- `permissions`
- `utilisateur_role`
- `role_permission`
- `sessions_utilisateur`
- `evenements_audit`

### Référentiels
- `referentiels`
- `valeurs_referentiel`
- `normes`

### Entreprises
- `entreprises`
- `contacts_entreprise`
- `sites_entreprise`
- `offres_entreprise`
- `candidats_doublon`

### Certification
- `organismes`
- `accreditations`
- `certifications`
- `couvertures_certification`
- `audits_certification`
- `evenements_certification`
- `renouvellements_certification`
- `documents`

### Collecte
- `campagnes`
- `missions_collecte`
- `affectations_mission`
- `fiches_collecte`
- `offres_declarees`
- `certifications_declarees`
- `evenements_collecte`

### Vérification
- `dossiers_verification`
- `affectations_verification`
- `points_verification`
- `anomalies_verification`
- `confirmations_externes`

### FUCCS
- `grilles_fuccs`
- `rubriques_fuccs`
- `criteres_fuccs`
- `controles_fuccs`
- `notes_criteres`
- `constats_controle`

### Validation / intégration
- `validations`
- `corrections`
- `integrations_bnec`
- `elements_integration`

### Scoring
- `modeles_scoring`
- `ponderations_scoring`
- `classifications_entreprise`
- `resultats_infc`
- `classements_sncc`

### Alertes / veille
- `echeances`
- `alertes`
- `notifications`
- `dossiers_veille`
- `relances_veille`
- `rapports_veille`

### Gouvernance
- `regles_metier`
- `revues_qualite`
- `plans_action`
- `decisions_institutionnelles`
- `publications`
- `rapports_generes`
- `archives`
- `sauvegardes`
- `incidents`

---

# 6. Audit SQLAlchemy ↔ dictionnaire

## Statut
✅ CONFORME

Résultat final :

```text
Tables SQLAlchemy        : 66 / 66
Colonnes                 : 843 / 843
Clés étrangères          : 107 / 107
Contraintes UNIQUE       : 9 / 9
```

Deux écarts avaient été détectés puis corrigés :

### `candidats_doublon.examine_par_id`
Corrigé en :

```text
nullable=False
```

### `utilisateurs.derniere_connexion_at`
Corrigé en :

```python
DateTime(timezone=True)
```

pour correspondre à `TIMESTAMPTZ`.

---

# 7. PHASE 1B — Alembic

## Statut
✅ TERMINÉ ET VALIDÉ

Alembic a été installé et configuré.

Migration initiale :

```text
Revision ID : 9f89b5d85b6a
Nom         : initial_schema_66_tables
```

La migration a été auditée avant exécution.

Elle contient correctement :

- 66 créations de tables ;
- 843 colonnes ;
- 107 FK ;
- 9 UNIQUE ;
- 66 PK ;
- types PostgreSQL corrects ;
- `gen_random_uuid()` ;
- `TIMESTAMPTZ` ;
- `JSONB` ;
- `NUMERIC(18,4)` ;
- ordre FK compatible ;
- `downgrade()` cohérent.

Commandes de contrôle :

```powershell
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Révision attendue :

```text
9f89b5d85b6a (head)
```

Résultat attendu de `alembic check` :

```text
No new upgrade operations detected.
```

---

# 8. Audit PostgreSQL réel

## Statut
✅ CONFORME

PostgreSQL réel a été vérifié après migration.

Résultat :

```text
66 tables métier
843 colonnes
107 clés étrangères
9 contraintes UNIQUE
66 clés primaires
révision Alembic correcte
gen_random_uuid() opérationnel
```

Avec la table technique Alembic :

```text
67 tables physiques dans public
=
66 métier
+
1 alembic_version
```

---

# 9. PHASE 2 — Bootstrap sécurité

## Statut
✅ TERMINÉ

Premier compte administrateur créé avec Argon2.

Rôle bootstrap :

```text
ADMIN_HAUQE
```

Le rôle reçoit le catalogue initial de permissions.

Le mot de passe n’est jamais stocké en clair.

Dépendance installée :

```text
argon2-cffi
```

Le script Windows utilise un `SelectorEventLoop` pour Psycopg async.

---

# 10. Authentification API

## Statut
✅ OPÉRATIONNEL ET TESTÉ

Endpoints :

```text
POST /api/v1/auth/login
GET  /api/v1/me
POST /api/v1/auth/logout
```

Chaîne de connexion :

```text
email / mot de passe
        ↓
Argon2
        ↓
utilisateur ACTIF
        ↓
rôles
        ↓
permissions
        ↓
création sessions_utilisateur
        ↓
Bearer token opaque
        ↓
hash SHA-256 stocké en base
        ↓
journal d’audit
```

Décision technique : **token opaque**.

Le client reçoit le token brut ; PostgreSQL ne conserve que `SHA-256(token)`.

---

# 11. Sécurité des sessions

## Statut
✅ OPÉRATIONNEL ET TESTÉ

Paramètres actuels :

```env
AUTH_SESSION_MINUTES=480
AUTH_IDLE_TIMEOUT_MINUTES=30
```

Règles :

```text
Durée absolue maximale : 8 heures
Inactivité maximale     : 30 minutes
Logout                  : révocation immédiate
Compte INACTIF          : accès refusé
```

Événement d’audit associé au verrouillage d’inactivité :

```text
AUTH_SESSION_IDLE_TIMEOUT
```

Important : les valeurs `.env` doivent être lues via `settings`, pas via `os.getenv()` dans les services.

---

# 12. Anti-bruteforce

## Statut
✅ IMPLÉMENTÉ

Politique courante :

```env
AUTH_MAX_FAILED_ATTEMPTS=5
AUTH_FAILURE_WINDOW_MINUTES=15
AUTH_LOCKOUT_MINUTES=15
```

Protection :

- par utilisateur ;
- par adresse IP.

Événements utilisés :

```text
AUTH_LOGIN
AUTH_LOGIN_BLOCKED
```

Code HTTP attendu lors du blocage :

```text
429 Too Many Requests
```

avec `Retry-After`.

Le mécanisme repose sur `evenements_audit`, sans ajouter de colonnes au MPD.

---

# 13. RBAC — utilisateurs / rôles / permissions

## Statut
✅ NOYAU OPÉRATIONNEL

Endpoints utilisateurs :

```text
GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/{user_id}
PATCH  /api/v1/users/{user_id}
PATCH  /api/v1/users/{user_id}/status
POST   /api/v1/users/{user_id}/roles
DELETE /api/v1/users/{user_id}/roles/{role_id}
```

Endpoints habilitations :

```text
GET /api/v1/roles
GET /api/v1/permissions
```

Fonctions validées :

- création utilisateur ;
- consultation ;
- modification ;
- activation ;
- désactivation ;
- attribution de rôle ;
- retrait de rôle ;
- journalisation ;
- révocation des sessions lors d’une désactivation ;
- non-exposition du hash de mot de passe ;
- permissions contrôlées côté serveur.

---

# 14. Rôles métier initialisés

## Statut
✅ CRÉÉS

Rôles présents :

```text
ADMIN_HAUQE
DIRECTION_TECHNIQUE
POINT_FOCAL_BNEC
VERIFICATEUR
CONTROLEUR_FUCCS
ADMIN_BNEC
AGENT_COLLECTE
CELLULE_VEILLE
LECTEUR
```

Le CRUD d’attribution / désactivation / retrait des rôles a été testé avec succès.

Important : les rôles existent en base, mais leur **matrice rôle → permissions métier définitive** doit encore être construite proprement.

Ne pas attribuer arbitrairement toutes les permissions aux rôles métier.

---

# 15. Fichiers backend importants déjà introduits

## Configuration

```text
app/config/settings.py
app/database/base.py
app/database/session.py
```

## Authentification / sécurité

```text
app/utils/security.py
app/services/auth_service.py
app/services/session_security_service.py
app/services/login_guard_service.py
app/permissions/auth.py
```

## Audit

```text
app/audit/service.py
```

## Repositories

```text
app/repositories/auth_repository.py
app/repositories/user_repository.py
```

## Schemas

```text
app/schemas/auth.py
app/schemas/user.py
app/schemas/role.py
```

## Routes

```text
app/routes/api/v1/auth.py
app/routes/api/v1/me.py
app/routes/api/v1/users.py
app/routes/api/v1/roles.py
app/routes/api/v1/router.py
```

## Scripts

```text
app/scripts/bootstrap_security.py
app/scripts/seed_business_roles.py
```

## Audits techniques

```text
audit_sqlalchemy_vs_dictionary.py
audit_postgres_runtime.py
```

---

# 16. Convention de commentaires dans le code

À partir de maintenant, chaque nouveau fichier backend doit contenir des commentaires utiles.

Commentaires attendus :

- rôle du fichier ;
- responsabilité de la classe/service/repository ;
- sections principales ;
- logique métier importante ;
- règle de sécurité ;
- raison d’un contrôle sensible ;
- transaction ou rollback significatif ;
- donnée qui ne doit jamais être exposée ;
- rappel si une décision dépend d’un paramètre `.env`.

Éviter les commentaires inutiles qui répètent simplement le code.

---

# 17. Contrôles techniques systématiques après chaque bloc

Après toute modification backend :

```powershell
.\.venv\Scripts\python.exe -m compileall app
```

Puis :

```powershell
.\.venv\Scripts\python.exe -m alembic check
```

Tant qu’aucune modification structurelle n’est prévue :

```text
No new upgrade operations detected.
```

doit rester le résultat attendu.

Lancement développement :

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

Swagger :

```text
http://127.0.0.1:8001/docs
```

---

# 18. Journalisation déjà attendue

Événements sécurité :

```text
AUTH_LOGIN
AUTH_LOGOUT
AUTH_LOGIN_BLOCKED
AUTH_SESSION_EXPIRED
AUTH_SESSION_IDLE_TIMEOUT
AUTH_SESSION_ACCOUNT_DISABLED
```

Événements administration :

```text
USER_CREATE
USER_UPDATE
USER_STATUS_CHANGE
USER_ROLE_ASSIGN
USER_ROLE_REMOVE
```

La liste continuera à évoluer avec les modules métier.

---

# 19. PHASE 2B — Matrice rôle → permissions

## Statut
✅ TERMINÉ ET VALIDÉ

Fonctionnalités validées :

```text
GET    /api/v1/roles/{role_id}/permissions
POST   /api/v1/roles/{role_id}/permissions
DELETE /api/v1/roles/{role_id}/permissions/{permission_id}
```

Décisions techniques conservées :

- `role_permission` est utilisé sans modification du MPD ;
- aucune migration Alembic n’a été nécessaire ;
- les permissions sont rechargées à chaque requête authentifiée ;
- les changements prennent effet immédiatement ;
- `ADMIN_HAUQE` conserve toutes les permissions ;
- le retrait d’une permission de `ADMIN_HAUQE` est bloqué ;
- le retrait sur un autre rôle supprime l’association `role_permission` ;
- l’historique reste conservé dans `evenements_audit` ;
- la matrice métier initiale a été seedée puis reste administrable.

Fichiers principaux :

```text
app/schemas/role.py
app/repositories/role_repository.py
app/services/role_permission_service.py
app/routes/api/v1/roles.py
app/scripts/seed_role_permission_matrix.py
```

Événements d’audit :

```text
ROLE_PERMISSION_ASSIGN
ROLE_PERMISSION_REMOVE
RBAC_MATRIX_SEED
```

---

# 20. PHASE 3 — Premier vertical métier : ENTREPRISES

## Statut
🟠 IMPLÉMENTATION COMPLÈTE FOURNIE — TESTS GROUPÉS À EFFECTUER

Objectif immédiat : remplacer les données simulées Entreprises par une API PostgreSQL réelle, sans modifier le schéma physique.

Périmètre du premier bloc :

```text
GET    /api/v1/entreprises
POST   /api/v1/entreprises
GET    /api/v1/entreprises/{id}
PATCH  /api/v1/entreprises/{id}
POST   /api/v1/entreprises/{id}/archive
```

Principes :

- `identifiant_national` reste l’identifiant métier unique ;
- `zone_siege_id` est contrôlé avant insertion/mise à jour ;
- `chiffre_affaires` reste dans PostgreSQL mais n’est pas exposé dans le premier schéma API courant ;
- `niveau_risque` et `date_derniere_verification` restent pilotés par les futurs services métier ;
- l’archivage est logique via `statut`, sans suppression physique ;
- toute création, modification et archive est auditée ;
- permissions utilisées : `ENTREPRISES.LIRE`, `ENTREPRISES.CREER`, `ENTREPRISES.MODIFIER`, `ENTREPRISES.ARCHIVER`.

Fichiers à ajouter / compléter :

```text
app/schemas/entreprise.py
app/repositories/entreprise_repository.py
app/services/entreprise_service.py
app/routes/api/v1/entreprises.py
app/routes/api/v1/router.py
```

Étapes suivantes après ce premier bloc :

```text
contacts_entreprise
sites_entreprise
offres_entreprise
candidats_doublon
connexion du frontend Entreprises à l’API réelle
```

---

# 21. Roadmap métier après Entreprises

Ordre recommandé :

```text
1. Entreprises
2. Organismes
3. Certifications
4. Documents
5. Campagnes / missions
6. Collecte
7. Vérification
8. Confirmations externes / anomalies
9. Grille FUCCS
10. Validation
11. Corrections
12. Intégration BNEC
13. Scoring entreprise
14. INFC
15. Classement
16. Échéances
17. Alertes
18. Veille
19. Rapports
20. Règles métier / gouvernance
21. Publications
22. Qualité / plans d’action
23. Incidents
24. Sauvegardes / archives
```

---

# 22. Points à traiter plus tard dans la sécurité

Non encore finalisés :

```text
MFA réel
récupération de mot de passe
changement de mot de passe
réinitialisation administrative
rotation de session
politique de mot de passe complète
rate limiting distribué
proxy de confiance / X-Forwarded-For
CSRF si cookies auth introduits
headers de sécurité
CSP
SRI pour ressources externes
tests automatisés sécurité
```

---

# 23. État résumé pour reprise rapide

```text
BASE DE DONNÉES
66 tables / 843 colonnes / 107 FK / 9 UNIQUE          ✅

SQLALCHEMY
66 modèles conformes                                  ✅

ALEMBIC
migration initiale 9f89b5d85b6a                      ✅

POSTGRESQL RÉEL
audit physique conforme                               ✅

ADMINISTRATEUR
ADMIN_HAUQE bootstrap                                 ✅

AUTH
login / me / logout                                   ✅

ARGON2
opérationnel                                           ✅

SESSIONS
Bearer opaque + hash SHA-256                          ✅

VERROUILLAGE SESSION
8 h absolues / 30 min inactivité                      ✅

AUDIT SÉCURITÉ
opérationnel                                           ✅

ANTI-BRUTEFORCE
5 échecs / 15 min / blocage 15 min                    ✅

UTILISATEURS
CRUD d’administration de base                         ✅

RÔLES
création / attribution / retrait                      ✅

RÔLES MÉTIER
9 rôles présents                                      ✅

MATRICE RÔLE → PERMISSIONS
opérationnelle                                         ✅

ENTREPRISES API RÉELLE
premier vertical en cours                              🟡
```

---

# 24. Instruction de reprise pour une nouvelle discussion

Si ce fichier est fourni dans une nouvelle discussion, reprendre immédiatement à :

> **PHASE 3 — Premier vertical métier : ENTREPRISES**

Ne pas recréer les modèles, ne pas refaire Alembic, ne pas refaire le bootstrap sécurité et ne pas repartir du frontend simulé.

Avant toute nouvelle étape :

1. lire cette feuille de route ;
2. vérifier la section « Prochaine étape exacte » ;
3. respecter les décisions structurantes ;
4. mettre à jour ce fichier après chaque avancée significative.

---

# 25. Historique de mise à jour

## 2026-07-25

- 66 modèles SQLAlchemy terminés.
- Audit SQLAlchemy ↔ dictionnaire conforme.
- Migration Alembic initiale générée et validée.
- PostgreSQL réel audité et conforme.
- Bootstrap sécurité réalisé.
- ADMIN_HAUQE créé.
- Catalogue de permissions créé.
- Login / me / logout opérationnels.
- Sessions opaques révoquables opérationnelles.
- Timeout absolu et inactivité opérationnels.
- Audit sécurité opérationnel.
- Anti-bruteforce ajouté.
- Administration utilisateurs ajoutée.
- Attribution et retrait de rôles validés.
- 8 rôles métier ajoutés en plus de ADMIN_HAUQE.
- Prochaine étape fixée : matrice rôle → permissions.
- Phase 2B démarrée : endpoints et service d’administration rôle → permissions définis.
- Matrice RBAC initiale des rôles métier préparée pour seed et validation.
- Phase 2B validée : attribution/retrait de permissions par rôle opérationnels.
- Phase 3 démarrée : premier vertical métier Entreprises.

## Mise à jour — Module Entreprises

Le vertical Entreprises comprend désormais également le cycle de vie suivant :

```text
POST /api/v1/entreprises/{id}/archive
POST /api/v1/entreprises/{id}/restore
GET  /api/v1/entreprises/archives
```

Règles :
- archivage logique via `statut = ARCHIVE` ;
- restauration via `statut = ACTIF` ;
- aucune suppression physique de l'entreprise ;
- consultation dédiée des archives ;
- les actions d'archivage/restauration restent auditées ;
- la route statique `/entreprises/archives` doit être déclarée avant `/entreprises/{entreprise_id}` pour éviter un conflit de résolution de route.

## Mise à jour — Sous-module Contacts entreprise

La Phase 3 Entreprises se poursuit avec `contacts_entreprise`.

Endpoints ajoutés / prévus :

```text
GET   /api/v1/entreprises/{entreprise_id}/contacts
POST  /api/v1/entreprises/{entreprise_id}/contacts
PATCH /api/v1/entreprises/{entreprise_id}/contacts/{contact_id}
POST  /api/v1/entreprises/{entreprise_id}/contacts/{contact_id}/deactivate
POST  /api/v1/entreprises/{entreprise_id}/contacts/{contact_id}/restore
```

Décisions :
- aucune suppression physique ;
- `statut = INACTIF` pour désactiver un contact ;
- restauration avec `statut = ACTIF` ;
- contrôle que le contact appartient bien à l’entreprise de l’URL ;
- audit des créations, modifications, désactivations et restaurations ;
- aucune migration Alembic ;
- les permissions du domaine Entreprises sont réutilisées pour ce sous-module.

## Mise à jour — Sous-module Sites entreprise

La Phase 3 Entreprises se poursuit avec `sites_entreprise`.

Endpoints ajoutés / prévus :

```text
GET   /api/v1/entreprises/{entreprise_id}/sites
POST  /api/v1/entreprises/{entreprise_id}/sites
PATCH /api/v1/entreprises/{entreprise_id}/sites/{site_id}
POST  /api/v1/entreprises/{entreprise_id}/sites/{site_id}/deactivate
POST  /api/v1/entreprises/{entreprise_id}/sites/{site_id}/restore
```

Décisions :
- aucune suppression physique ;
- `statut = INACTIF` pour désactiver un site ;
- restauration avec `statut = ACTIF` ;
- contrôle strict que le site appartient à l’entreprise de l’URL ;
- contrôle de l’existence de `zone_id` avant insertion/modification ;
- une entreprise archivée ne peut pas recevoir de nouveau site ;
- un site inactif ne peut pas être modifié tant qu’il n’est pas restauré ;
- audit des créations, modifications, désactivations et restaurations ;
- aucune migration Alembic ;
- les permissions `ENTREPRISES.*` existantes sont réutilisées ;
- aucune règle supplémentaire sur la relation future avec `couvertures_certification` n’est imposée à ce stade.

# REGISTRE GLOBAL DES ENDPOINTS API

Cette section doit être mise à jour à chaque création, suppression ou modification d'un endpoint.

## Authentification / session

```text
POST /api/v1/auth/login
GET  /api/v1/me
POST /api/v1/auth/logout
```

Fonctions :
- authentification Argon2 ;
- création d'une session serveur ;
- émission d'un Bearer token opaque ;
- consultation de l'utilisateur courant ;
- révocation immédiate de la session au logout ;
- contrôle de l'expiration absolue et de l'inactivité ;
- journalisation des événements de sécurité.

## Utilisateurs

```text
GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/{user_id}
PATCH  /api/v1/users/{user_id}
PATCH  /api/v1/users/{user_id}/status
POST   /api/v1/users/{user_id}/roles
DELETE /api/v1/users/{user_id}/roles/{role_id}
```

Fonctions :
- création et consultation des comptes ;
- modification ;
- activation / désactivation ;
- attribution et retrait de rôles ;
- révocation des sessions lors de la désactivation ;
- audit des opérations sensibles.

## Rôles / permissions

```text
GET    /api/v1/roles
GET    /api/v1/permissions
GET    /api/v1/roles/{role_id}/permissions
POST   /api/v1/roles/{role_id}/permissions
DELETE /api/v1/roles/{role_id}/permissions/{permission_id}
```

Fonctions :
- consultation du catalogue RBAC ;
- consultation des permissions d'un rôle ;
- attribution d'une permission ;
- retrait d'une permission ;
- protection de `ADMIN_HAUQE` contre le retrait de permissions critiques ;
- prise d'effet immédiate des changements grâce au rechargement des permissions à chaque requête authentifiée.

## Entreprises

```text
GET   /api/v1/entreprises
GET   /api/v1/entreprises/archives
POST  /api/v1/entreprises
GET   /api/v1/entreprises/{entreprise_id}
PATCH /api/v1/entreprises/{entreprise_id}
POST  /api/v1/entreprises/{entreprise_id}/archive
POST  /api/v1/entreprises/{entreprise_id}/restore
```

Fonctions :
- liste paginée et recherche ;
- consultation des archives ;
- création ;
- modification ;
- archivage logique ;
- restauration ;
- aucune suppression physique.

## Contacts entreprise

```text
GET   /api/v1/entreprises/{entreprise_id}/contacts
POST  /api/v1/entreprises/{entreprise_id}/contacts
PATCH /api/v1/entreprises/{entreprise_id}/contacts/{contact_id}
POST  /api/v1/entreprises/{entreprise_id}/contacts/{contact_id}/deactivate
POST  /api/v1/entreprises/{entreprise_id}/contacts/{contact_id}/restore
```

Fonctions :
- liste des contacts d'une entreprise ;
- ajout ;
- modification ;
- désactivation logique ;
- restauration ;
- contrôle strict de l'appartenance du contact à l'entreprise de l'URL.

## Sites entreprise

```text
GET   /api/v1/entreprises/{entreprise_id}/sites
POST  /api/v1/entreprises/{entreprise_id}/sites
PATCH /api/v1/entreprises/{entreprise_id}/sites/{site_id}
POST  /api/v1/entreprises/{entreprise_id}/sites/{site_id}/deactivate
POST  /api/v1/entreprises/{entreprise_id}/sites/{site_id}/restore
```

Fonctions :
- liste des sites d'une entreprise ;
- ajout ;
- modification ;
- désactivation logique ;
- restauration ;
- contrôle de `zone_id` ;
- contrôle strict de l'appartenance du site à l'entreprise de l'URL.

---

# INTERACTIONS ENTRE MODULES PRINCIPAUX ET SOUS-MODULES

Cette section est obligatoire et doit être enrichie à chaque nouveau module.

## 1. Sécurité / Authentification / RBAC

```text
utilisateurs
    ↓ utilisateur_role
roles
    ↓ role_permission
permissions
```

Interaction :
- `utilisateurs` représente les comptes ;
- `utilisateur_role` associe un utilisateur à un ou plusieurs rôles ;
- `roles` porte les profils fonctionnels ;
- `role_permission` associe un rôle à des permissions ;
- `permissions` représente les actions réellement contrôlées côté API ;
- `get_current_auth()` recharge les rôles et permissions depuis PostgreSQL à chaque requête protégée ;
- une modification RBAC prend donc effet sans attendre une nouvelle connexion.

Les sessions sont reliées par :

```text
utilisateurs
    ↓
sessions_utilisateur
```

Effets :
- logout → `revoquee_at` ;
- compte désactivé → révocation des sessions actives ;
- expiration absolue → session refusée ;
- inactivité prolongée → session verrouillée/révoquée ;
- les événements sont consignés dans `evenements_audit`.

## 2. Module principal Entreprises

```text
entreprises
   ├── contacts_entreprise
   ├── sites_entreprise
   ├── offres_entreprise
   └── candidats_doublon
```

`entreprises` constitue la racine du domaine entreprise.

### 2.1 Entreprises ↔ Contacts entreprise

Clé de liaison :

```text
contacts_entreprise.entreprise_id
    →
entreprises.id
```

Règles :
- un contact appartient à une seule entreprise ;
- l'API ne permet pas de changer `entreprise_id` depuis le JSON ;
- l'entreprise est déterminée par l'URL ;
- une requête utilisant le `contact_id` d'une autre entreprise retourne 404 ;
- une entreprise archivée ne doit plus recevoir de nouveaux contacts ;
- un contact peut être désactivé sans être supprimé physiquement ;
- le contact reste disponible pour la traçabilité et l'historique métier.

### 2.2 Entreprises ↔ Sites entreprise

Clé de liaison :

```text
sites_entreprise.entreprise_id
    →
entreprises.id
```

Le site dépend également de :

```text
sites_entreprise.zone_id
    →
zones_administratives.id
```

Règles :
- un site appartient à une seule entreprise ;
- l'entreprise est déterminée par l'URL ;
- `zone_id` doit exister avant création/modification ;
- une entreprise archivée ne reçoit plus de nouveau site ;
- un site inactif doit être restauré avant modification ;
- aucune suppression physique ;
- les coordonnées et données du site restent liées à son entreprise.

Relation future importante :

```text
sites_entreprise
    ↓
couvertures_certification
    ↓
certifications
```

Cela permettra à une certification de préciser quels sites de l'entreprise sont effectivement couverts.

### 2.3 Entreprises ↔ Offres entreprise

Sous-module encore à implémenter.

Clé prévue :

```text
offres_entreprise.entreprise_id
    →
entreprises.id
```

Rôle métier futur :
- décrire les biens/services/offres d'une entreprise ;
- stocker volumes, capacités, marchés cibles et destinations ;
- fournir une base de rapprochement avec les couvertures de certification.

Relation future :

```text
offres_entreprise
    ↓
couvertures_certification
    ↓
certifications
```

Une certification pourra donc couvrir une offre précise, un site précis ou une combinaison du périmètre défini.

### 2.4 Entreprises ↔ Candidats doublon

Sous-module encore à implémenter.

Relations :

```text
candidats_doublon.entreprise_source_id
    →
entreprises.id

candidats_doublon.entreprise_cible_id
    →
entreprises.id
```

Rôle :
- détecter les entreprises potentiellement dupliquées ;
- conserver le score de similarité ;
- conserver les critères concordants ;
- permettre une décision humaine documentée ;
- éviter les fusions automatiques dangereuses.

### 2.5 Effet de l'archivage d'une entreprise

```text
entreprise ACTIF
    ↓
utilisation opérationnelle normale

entreprise ARCHIVE
    ↓
consultable
mais non alimentée par de nouvelles données opérationnelles
```

L'archivage ne doit jamais supprimer automatiquement :
- ses contacts ;
- ses sites ;
- ses offres ;
- ses certifications ;
- ses contrôles ;
- ses audits ;
- ses pièces ;
- son historique.

Ces sous-données restent nécessaires à la traçabilité.

## 3. Entreprises ↔ Certifications — interaction future

```text
entreprises
    ↓
certifications
        ↓
couvertures_certification
             ├── sites_entreprise
             └── offres_entreprise
```

Cela permettra de distinguer :
- l'entreprise titulaire ;
- la certification ;
- le site réellement couvert ;
- l'offre ou activité réellement couverte ;
- le périmètre exact du certificat.

Cette séparation doit être conservée : une certification d'entreprise ne signifie pas nécessairement que tous ses sites et toutes ses offres sont certifiés.

---

# RÈGLE DE MAINTENANCE DE CETTE FEUILLE DE ROUTE

Après chaque avancée backend significative, mettre obligatoirement à jour :

1. le statut de la phase ;
2. les fichiers créés/modifiés ;
3. tous les endpoints ajoutés ou modifiés ;
4. les permissions associées ;
5. les événements d'audit associés ;
6. les interactions entre le module et ses sous-modules ;
7. les clés étrangères / dépendances importantes ;
8. les règles de cycle de vie (ACTIF, INACTIF, ARCHIVE, restauration, etc.) ;
9. les contrôles testés ;
10. la prochaine étape exacte.

# MISE À JOUR — LIVRAISON COMPLÈTE DU DOMAINE ENTREPRISES

## Mode de livraison adopté

À partir de cette étape, les domaines métier seront livrés autant que possible en **blocs complets** :

```text
module principal
    +
ses sous-modules directement dépendants
    +
routes
    +
services
    +
repositories
    +
schemas
    +
permissions
    +
audit
    +
documentation des interactions
```

L'utilisateur pourra ensuite intégrer le bloc puis tester l'ensemble de ses endpoints en une seule campagne.

## Domaine Entreprises — état

```text
entreprises              ✅ créé
├── contacts_entreprise  ✅ créé
├── sites_entreprise     ✅ créé
├── offres_entreprise    🟡 livré / à intégrer et tester
└── candidats_doublon    🟡 livré / à intégrer et tester
```

Le domaine Entreprises pourra être marqué **TERMINÉ ET VALIDÉ** après la campagne de tests globale.

## Endpoints Entreprises — registre complet

### Entreprise principale

```text
GET   /api/v1/entreprises
GET   /api/v1/entreprises/archives
POST  /api/v1/entreprises
GET   /api/v1/entreprises/{entreprise_id}
PATCH /api/v1/entreprises/{entreprise_id}
POST  /api/v1/entreprises/{entreprise_id}/archive
POST  /api/v1/entreprises/{entreprise_id}/restore
```

### Contacts

```text
GET   /api/v1/entreprises/{entreprise_id}/contacts
POST  /api/v1/entreprises/{entreprise_id}/contacts
PATCH /api/v1/entreprises/{entreprise_id}/contacts/{contact_id}
POST  /api/v1/entreprises/{entreprise_id}/contacts/{contact_id}/deactivate
POST  /api/v1/entreprises/{entreprise_id}/contacts/{contact_id}/restore
```

### Sites

```text
GET   /api/v1/entreprises/{entreprise_id}/sites
POST  /api/v1/entreprises/{entreprise_id}/sites
PATCH /api/v1/entreprises/{entreprise_id}/sites/{site_id}
POST  /api/v1/entreprises/{entreprise_id}/sites/{site_id}/deactivate
POST  /api/v1/entreprises/{entreprise_id}/sites/{site_id}/restore
```

### Offres

```text
GET   /api/v1/entreprises/{entreprise_id}/offres
GET   /api/v1/entreprises/{entreprise_id}/offres/{offre_id}
POST  /api/v1/entreprises/{entreprise_id}/offres
PATCH /api/v1/entreprises/{entreprise_id}/offres/{offre_id}
POST  /api/v1/entreprises/{entreprise_id}/offres/{offre_id}/deactivate
POST  /api/v1/entreprises/{entreprise_id}/offres/{offre_id}/restore
```

### Contrôle des doublons

```text
GET  /api/v1/doublons-entreprises
POST /api/v1/doublons-entreprises
GET  /api/v1/doublons-entreprises/{candidat_id}
POST /api/v1/doublons-entreprises/{candidat_id}/decision
```

IMPORTANT : les routes statiques `/entreprises/archives` et `/doublons-entreprises`
doivent être enregistrées de manière à ne pas être absorbées par
`/entreprises/{entreprise_id}`.

## Interactions du domaine Entreprises

```text
zones_administratives
        ↑
        │ zone_siege_id
entreprises
   │
   ├── contacts_entreprise
   │      FK entreprise_id
   │
   ├── sites_entreprise
   │      FK entreprise_id
   │      FK zone_id → zones_administratives
   │
   ├── offres_entreprise
   │      FK entreprise_id
   │
   └── candidats_doublon
          FK entreprise_source_id → entreprises
          FK entreprise_cible_id  → entreprises
          FK examine_par_id       → utilisateurs
```

### Entreprises ↔ Offres

`offres_entreprise` décrit les produits ou services proposés par l'entreprise.

Colonnes métier principales :

```text
type_offre
nom
description
categorie
volume_annuel
unite
capacite_production
marches_cibles JSONB
destinations JSONB
statut
```

Une offre ne peut pas être rattachée arbitrairement à une autre entreprise :
l'entreprise est imposée par l'URL.

Une entreprise archivée reste consultable mais ne reçoit pas de nouvelle offre.

Une offre est désactivée logiquement (`INACTIF`) et peut être restaurée (`ACTIF`).

Relation future :

```text
offres_entreprise
      ↓ offre_entreprise_id
couvertures_certification
      ↓ certification_id
certifications
```

Cette relation permettra de représenter le fait qu'une certification peut
couvrir une offre précise sans couvrir nécessairement toutes les activités
de l'entreprise.

### Entreprises ↔ Candidats doublon

`candidats_doublon` n'est pas une seconde fiche entreprise. C'est un
**résultat de contrôle** reliant deux entreprises déjà enregistrées.

```text
entreprise_source_id ─┐
                      ├→ candidats_doublon
entreprise_cible_id ──┘
```

Il conserve :

```text
criteres_concordants JSONB
score_similarite
statut_examen
decision
motif_decision
examine_par_id
examine_at
```

Règles :
- une entreprise ne peut pas être comparée avec elle-même ;
- un candidat doublon ne doit jamais provoquer une fusion automatique ;
- l'examen produit une décision humaine motivée ;
- l'examinateur est l'utilisateur authentifié ;
- la décision et son motif sont audités ;
- le moteur automatique de détection RM-36 sera branché ultérieurement sur ce sous-module, sans inventer aujourd'hui un seuil de similarité non validé.

La procédure institutionnelle exige justement qu'un doublon potentiel soit examiné,
motivé et audité avant toute décision ; il ne doit pas être fusionné ou écarté automatiquement.

## Permissions Entreprises

```text
ENTREPRISES.LIRE
ENTREPRISES.CREER
ENTREPRISES.MODIFIER
ENTREPRISES.ARCHIVER
VERIFICATION.SIGNALER_ANOMALIE
VERIFICATION.VERIFIER
```

Usage :

```text
lecture Entreprises / contacts / sites / offres / doublons
    → ENTREPRISES.LIRE

création Entreprise / contact / site / offre
    → ENTREPRISES.CREER

modification / désactivation / restauration des sous-modules
    → ENTREPRISES.MODIFIER

archive / restore entreprise
    → ENTREPRISES.ARCHIVER

création d'un candidat doublon
    → VERIFICATION.VERIFIER

décision sur un candidat doublon
    → VERIFICATION.VERIFIER
```

## Événements d'audit du domaine

```text
ENTREPRISE_CREATE
ENTREPRISE_UPDATE
ENTREPRISE_ARCHIVE
ENTREPRISE_RESTORE

ENTREPRISE_CONTACT_CREATE
ENTREPRISE_CONTACT_UPDATE
ENTREPRISE_CONTACT_DEACTIVATE
ENTREPRISE_CONTACT_RESTORE

ENTREPRISE_SITE_CREATE
ENTREPRISE_SITE_UPDATE
ENTREPRISE_SITE_DEACTIVATE
ENTREPRISE_SITE_RESTORE

ENTREPRISE_OFFRE_CREATE
ENTREPRISE_OFFRE_UPDATE
ENTREPRISE_OFFRE_DEACTIVATE
ENTREPRISE_OFFRE_RESTORE

ENTREPRISE_DOUBLON_CREATE
ENTREPRISE_DOUBLON_DECISION
```

## Prochaine campagne de validation

Après intégration du bloc :

```text
python -m compileall app
python -m alembic check
```

Puis tester tous les endpoints Entreprises, sous-modules inclus.

Après validation globale :

```text
PHASE 3 — ENTREPRISES = ✅ TERMINÉE
```

Étape suivante : livrer le prochain domaine principal avec ses sous-modules en bloc complet.


# CONSOLIDATION ACTUELLE — DOMAINE ENTREPRISES COMPLET

## Statut

🟠 **Implémentation complète fournie — validation groupée à effectuer**

Le domaine principal `entreprises` et ses quatre sous-modules sont maintenant couverts :

```text
entreprises
   ├── contacts_entreprise
   ├── sites_entreprise
   ├── offres_entreprise
   └── candidats_doublon
```

Le dictionnaire confirme les relations suivantes :
- `contacts_entreprise.entreprise_id → entreprises.id`
- `sites_entreprise.entreprise_id → entreprises.id`
- `sites_entreprise.zone_id → zones_administratives.id`
- `offres_entreprise.entreprise_id → entreprises.id`
- `candidats_doublon.entreprise_source_id → entreprises.id`
- `candidats_doublon.entreprise_cible_id → entreprises.id`
- `candidats_doublon.examine_par_id → utilisateurs.id`

## Registre exhaustif des endpoints Entreprises

### Entreprise

```text
GET   /api/v1/entreprises
GET   /api/v1/entreprises/archives
POST  /api/v1/entreprises
GET   /api/v1/entreprises/{entreprise_id}
PATCH /api/v1/entreprises/{entreprise_id}
POST  /api/v1/entreprises/{entreprise_id}/archive
POST  /api/v1/entreprises/{entreprise_id}/restore
```

### Contacts

```text
GET   /api/v1/entreprises/{entreprise_id}/contacts
POST  /api/v1/entreprises/{entreprise_id}/contacts
PATCH /api/v1/entreprises/{entreprise_id}/contacts/{contact_id}
POST  /api/v1/entreprises/{entreprise_id}/contacts/{contact_id}/deactivate
POST  /api/v1/entreprises/{entreprise_id}/contacts/{contact_id}/restore
```

### Sites

```text
GET   /api/v1/entreprises/{entreprise_id}/sites
POST  /api/v1/entreprises/{entreprise_id}/sites
PATCH /api/v1/entreprises/{entreprise_id}/sites/{site_id}
POST  /api/v1/entreprises/{entreprise_id}/sites/{site_id}/deactivate
POST  /api/v1/entreprises/{entreprise_id}/sites/{site_id}/restore
```

### Offres

```text
GET   /api/v1/entreprises/{entreprise_id}/offres
GET   /api/v1/entreprises/{entreprise_id}/offres/{offre_id}
POST  /api/v1/entreprises/{entreprise_id}/offres
PATCH /api/v1/entreprises/{entreprise_id}/offres/{offre_id}
POST  /api/v1/entreprises/{entreprise_id}/offres/{offre_id}/deactivate
POST  /api/v1/entreprises/{entreprise_id}/offres/{offre_id}/restore
```

### Contrôle des doublons

Le contrôle relie deux entreprises ; il possède donc une racine globale distincte :

```text
GET  /api/v1/doublons-entreprises
GET  /api/v1/doublons-entreprises/{candidat_id}
POST /api/v1/doublons-entreprises
POST /api/v1/doublons-entreprises/{candidat_id}/decision
```

Le GET global accepte notamment :
- `entreprise_id`
- `statut_examen`
- `decision`
- `limit`
- `offset`

## Interaction complète du domaine

```text
zones_administratives
    ↑                    ↑
    │ zone_siege_id      │ zone_id
    │                    │
entreprises ───────── sites_entreprise
    │
    ├──────── contacts_entreprise
    │
    ├──────── offres_entreprise
    │             │
    │             └──── future couverture de certification
    │
    └──── candidats_doublon
             ├─ entreprise_source_id
             ├─ entreprise_cible_id
             └─ examine_par_id → utilisateurs
```

### Cycle de vie parent / enfants

- `entreprises.ARCHIVE` : l'entreprise reste consultable et historique ; elle ne reçoit plus de nouveau contact/site/offre.
- Contacts/sites/offres : désactivation logique `INACTIF`, restauration `ACTIF`, aucune suppression physique.
- L'archivage de l'entreprise ne supprime jamais ses sous-données.
- Les offres et sites doivent rester disponibles historiquement car `couvertures_certification` pourra les référencer.
- `candidats_doublon` est un résultat de contrôle et non une fiche entreprise ; aucune fusion automatique n'est proposée.

### Contrôle doublon

La procédure HAUQE prévoit un rapprochement sur plusieurs critères et exige qu'un doublon potentiel soit examiné, motivé et audité avant toute décision. Le backend enregistre donc :
- les deux entreprises comparées ;
- les critères concordants ;
- le score de similarité sans imposer un seuil non validé ;
- l'examinateur ;
- la décision ;
- le motif ;
- la date d'examen.

Le MPD impose `examine_par_id` en NOT NULL. À la création manuelle d'un candidat, l'utilisateur authentifié est donc affecté comme examinateur ; `examine_at` reste vide jusqu'à la décision.

## Permissions utilisées

```text
ENTREPRISES.LIRE
ENTREPRISES.CREER
ENTREPRISES.MODIFIER
ENTREPRISES.ARCHIVER
VERIFICATION.VERIFIER
```

- consultation des entreprises et sous-modules : `ENTREPRISES.LIRE`
- création entreprise/contact/site/offre : `ENTREPRISES.CREER`
- modification/désactivation/restauration contact/site/offre : `ENTREPRISES.MODIFIER`
- archivage/restauration entreprise : `ENTREPRISES.ARCHIVER`
- création et décision sur candidat doublon : `VERIFICATION.VERIFIER`

## Audit attendu

```text
ENTREPRISE_CREATE
ENTREPRISE_UPDATE
ENTREPRISE_ARCHIVE
ENTREPRISE_RESTORE

ENTREPRISE_CONTACT_CREATE
ENTREPRISE_CONTACT_UPDATE
ENTREPRISE_CONTACT_DEACTIVATE
ENTREPRISE_CONTACT_RESTORE

ENTREPRISE_SITE_CREATE
ENTREPRISE_SITE_UPDATE
ENTREPRISE_SITE_DEACTIVATE
ENTREPRISE_SITE_RESTORE

ENTREPRISE_OFFRE_CREATE
ENTREPRISE_OFFRE_UPDATE
ENTREPRISE_OFFRE_DEACTIVATE
ENTREPRISE_OFFRE_RESTORE

ENTREPRISE_DOUBLON_CREATE
ENTREPRISE_DOUBLON_DECISION
```

## Validation groupée à réaliser

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m alembic check
```

Puis tester l'ensemble des endpoints ci-dessus dans Swagger.

Résultat Alembic attendu :

```text
No new upgrade operations detected.
```

Quand ces tests passent, marquer :

```text
PHASE 3 — ENTREPRISES = ✅ TERMINÉE ET VALIDÉE
```

## Nouvelle méthode de livraison

À partir du prochain domaine, livrer le **module principal et tous ses sous-modules dans le même bloc**, puis effectuer une campagne de tests groupée.

Bloc livré pour intégration et tests groupés :

```text
ORGANISMES / CERTIFICATIONS
├── organismes
├── accreditations
├── certifications
├── couvertures_certification
├── audits_certification
├── evenements_certification
├── renouvellements_certification
└── documents
```

Cette famille sera documentée avec tous ses endpoints, permissions, audits, clés de liaison et interactions avant les tests groupés.

# DOMAINE ORGANISMES / CERTIFICATIONS / DOCUMENTS

## Statut

✅ **TERMINÉ ET VALIDÉ — intégration et tests groupés confirmés**

Le domaine est livré en un seul lot conformément à la méthode de travail retenue :

```text
ORGANISMES / CERTIFICATIONS
├── normes (lecture minimale nécessaire)
├── organismes
├── accreditations
├── certifications
├── couvertures_certification
├── audits_certification
├── evenements_certification
├── renouvellements_certification
└── documents
```

Aucune modification du MPD n'est introduite par ce lot.

## Fichiers livrés

```text
app/schemas/organismes_certifications.py
app/schemas/document.py

app/repositories/organismes_certifications_repository.py
app/repositories/document_repository.py

app/services/organismes_certifications_service.py
app/services/document_service.py

app/routes/api/v1/organismes_certifications.py
app/routes/api/v1/documents.py

app/scripts/seed_certification_domain_permissions.py
```

Documentation d'intégration :

```text
ROUTER_INTEGRATION.md
DEPENDANCES_ET_CONFIGURATION.md
INTERACTIONS_DOMAINE.md
TESTS_ENDPOINTS_ORGANISMES_CERTIFICATIONS.md
```

## Registre exhaustif des endpoints du domaine

### Normes

```text
GET /api/v1/normes
GET /api/v1/normes/{norme_id}
```

État : **créés dans le lot / tests à effectuer**

Ces deux routes constituent uniquement la lecture minimale nécessaire à la création d'une certification. Le CRUD complet des référentiels sera traité dans son domaine propre.

### Organismes

```text
GET   /api/v1/organismes
POST  /api/v1/organismes
GET   /api/v1/organismes/{organisme_id}
PATCH /api/v1/organismes/{organisme_id}
POST  /api/v1/organismes/{organisme_id}/verification
```

État : **créés dans le lot / tests à effectuer**

### Accréditations

```text
GET   /api/v1/organismes/{organisme_id}/accreditations
GET   /api/v1/organismes/{organisme_id}/accreditations/{accreditation_id}
POST  /api/v1/organismes/{organisme_id}/accreditations
PATCH /api/v1/organismes/{organisme_id}/accreditations/{accreditation_id}
POST  /api/v1/organismes/{organisme_id}/accreditations/{accreditation_id}/decision
```

État : **créés dans le lot / tests à effectuer**

### Certifications

```text
GET   /api/v1/certifications
POST  /api/v1/certifications
GET   /api/v1/certifications/{certification_id}
PATCH /api/v1/certifications/{certification_id}
POST  /api/v1/certifications/{certification_id}/status
POST  /api/v1/certifications/{certification_id}/verification
GET   /api/v1/certifications/{certification_id}/history
```

État : **créés dans le lot / tests à effectuer**

### Couvertures de certification

```text
GET   /api/v1/certifications/{certification_id}/couvertures
POST  /api/v1/certifications/{certification_id}/couvertures
PATCH /api/v1/certifications/{certification_id}/couvertures/{couverture_id}
```

État : **créés dans le lot / tests à effectuer**

### Audits de certification

```text
GET   /api/v1/certifications/{certification_id}/audits
POST  /api/v1/certifications/{certification_id}/audits
PATCH /api/v1/certifications/{certification_id}/audits/{audit_id}
```

État : **créés dans le lot / tests à effectuer**

### Renouvellements

```text
GET   /api/v1/certifications/{certification_id}/renewals
POST  /api/v1/certifications/{certification_id}/renewals
PATCH /api/v1/certifications/{certification_id}/renewals/{renouvellement_id}
POST  /api/v1/certifications/{certification_id}/renewals/{renouvellement_id}/decision
```

État : **créés dans le lot / tests à effectuer**

### Documents

```text
GET  /api/v1/documents
POST /api/v1/documents/upload
GET  /api/v1/documents/{document_id}
GET  /api/v1/documents/{document_id}/download
POST /api/v1/documents/{document_id}/verification
POST /api/v1/documents/{document_id}/deactivate
POST /api/v1/documents/{document_id}/restore
```

État : **créés dans le lot / tests à effectuer**

## Interaction complète des modules

```text
zones_administratives
        ↑
        │ zone_id facultatif
    organismes
        │
        ├──────── accreditations
        │
        └──────── certifications ───────── normes
                      ↑
                      │
                  entreprises
                      │
                      ├──────── sites_entreprise
                      │              ↑
                      │              │
                      │      couvertures_certification
                      │              │
                      └──────── offres_entreprise
                                     ↑
                                     │
                             couvertures_certification

certifications
    ├── audits_certification
    ├── evenements_certification
    ├── renouvellements_certification
    └── documents via ressource_type + ressource_id
```

### Organismes ↔ Accréditations

Clé :

```text
accreditations.organisme_id
    →
organismes.id
```

Un organisme peut être enregistré même sans accréditation.

L'accéditation reste donc un sous-module facultatif et ne conditionne pas l'existence de l'organisme.

Le backend vérifie qu'une accréditation manipulée via :

```text
/organismes/{organisme_id}/accreditations/{accreditation_id}
```

appartient réellement à l'organisme présent dans l'URL.

### Limite MPD importante

Le MCD fonctionnel prévoit :

```text
ACCREDITATION → NORME
```

mais le MPD actuel ne possède pas `norme_id` dans `accreditations`.

Décision :

- aucune migration n'est créée ;
- aucune FK fictive n'est inventée ;
- le backend ne prétend donc pas encore vérifier qu'une accréditation couvre la même norme que le certificat.

### Certifications ↔ Entreprise / Organisme / Norme

Clés :

```text
certifications.entreprise_id
    → entreprises.id

certifications.organisme_id
    → organismes.id

certifications.accreditation_id
    → accreditations.id   (facultatif)

certifications.norme_id
    → normes.id
```

Contrôles :

- l'entreprise doit exister ;
- une entreprise archivée ne reçoit pas de nouvelle certification ;
- l'organisme doit exister ;
- la norme doit exister ;
- si une accréditation est fournie, elle doit appartenir au même organisme ;
- l'identifiant national de certification reste unique ;
- contrôle applicatif du doublon exact entreprise + organisme + norme + portée ;
- contrôles chronologiques obtention / effet / expiration.

### Certifications ↔ Documents

Une vérification d'authenticité positive :

```text
authenticite_verifiee = true
```

exige au moins un document actif lié à :

```text
ressource_type = CERTIFICATION
ressource_id   = certifications.id
```

La création du certificat reste possible sans preuve immédiate, mais son statut par défaut est :

```text
A_VERIFIER
```

### Certifications ↔ Couvertures

```text
certifications
    ↓
couvertures_certification
      ├── offre_entreprise_id
      └── site_entreprise_id
```

Règles :

- `PRODUIT` ou `SERVICE` exige une offre ;
- `SITE` exige un site ;
- `ACTIVITE` est actuellement décrite textuellement car le MPD ne possède pas d'entité activité dédiée ;
- le site ou l'offre doit appartenir à la même entreprise que la certification ;
- une offre ou un site inactif ne peut pas être ajouté comme nouvelle couverture.

Cette relation empêche de conclure qu'un certificat couvre automatiquement toute l'entreprise.

### Certification ↔ Historique

Deux historiques différents sont maintenus :

```text
evenements_certification
    = historique métier du certificat

evenements_audit
    = journal technique de l'action utilisateur/API
```

Un changement de statut ou une vérification crée l'événement métier correspondant.

Aucun endpoint de création libre d'un `evenement_certification` n'est exposé : le backend produit lui-même l'historique.

### Certification ↔ Audits

```text
audits_certification.certification_id
    →
certifications.id
```

Les audits de certification sont des objets métier de suivi du certificat.

Ils ne sont pas le même objet que le journal technique `evenements_audit`.

### Certification ↔ Renouvellements

```text
renouvellements_certification.certification_id
    →
certifications.id
```

Une certification peut posséder plusieurs procédures de renouvellement.

La décision de renouvellement n'altère pas silencieusement le statut principal du certificat. Si le statut de certification doit changer, la route :

```text
POST /api/v1/certifications/{certification_id}/status
```

doit être utilisée afin de générer un événement métier explicite.

### Documents

Le MPD utilise :

```text
documents.ressource_type
documents.ressource_id
```

sans FK générique.

Le backend valide actuellement les ressources suivantes avant dépôt :

```text
ENTREPRISE
ORGANISME
ACCREDITATION
CERTIFICATION
SITE_ENTREPRISE
OFFRE_ENTREPRISE
AUDIT_CERTIFICATION
RENOUVELLEMENT_CERTIFICATION
```

Sécurité documentaire :

- stockage sous `uploads/private` par défaut ;
- aucun stockage dans `app/static` ;
- nom physique généré côté serveur ;
- téléchargement via endpoint authentifié ;
- chemin physique non exposé ;
- checksum SHA-256 ;
- taille maximale par défaut : 10 MiB ;
- formats initiaux : PDF, PNG, JPG/JPEG ;
- désactivation logique sans suppression physique.

## Permissions nécessaires

Permissions déjà utilisées auparavant :

```text
REFERENTIELS.LIRE
ORGANISMES.LIRE
CERTIFICATIONS.LIRE
CERTIFICATIONS.VERIFIER
DOCUMENTS.LIRE
DOCUMENTS.DEPOSER
DOCUMENTS.TELECHARGER
```

Permissions complémentaires du nouveau lot :

```text
ORGANISMES.CREER
ORGANISMES.MODIFIER
CERTIFICATIONS.CREER
CERTIFICATIONS.MODIFIER
DOCUMENTS.VERIFIER
```

Le script :

```text
app/scripts/seed_certification_domain_permissions.py
```

crée uniquement les permissions absentes et garantit qu'`ADMIN_HAUQE` conserve tout le catalogue. Il n'impose pas encore ces nouvelles permissions aux autres rôles métier.

## Événements d'audit attendus

```text
ORGANISME_CREATE
ORGANISME_UPDATE
ORGANISME_VERIFY

ACCREDITATION_CREATE
ACCREDITATION_UPDATE
ACCREDITATION_DECISION

CERTIFICATION_CREATE
CERTIFICATION_UPDATE
CERTIFICATION_STATUS_CHANGE
CERTIFICATION_VERIFY

CERTIFICATION_COVERAGE_CREATE
CERTIFICATION_COVERAGE_UPDATE

CERTIFICATION_AUDIT_CREATE
CERTIFICATION_AUDIT_UPDATE

CERTIFICATION_RENEWAL_CREATE
CERTIFICATION_RENEWAL_UPDATE
CERTIFICATION_RENEWAL_DECISION

DOCUMENT_UPLOAD
DOCUMENT_VERIFY
DOCUMENT_DEACTIVATE
DOCUMENT_RESTORE
```

## Dépendance supplémentaire

Pour `UploadFile` / `Form` :

```text
python-multipart
```

Le lot prévoit :

```powershell
.\.venv\Scripts\python.exe -m pip install python-multipart
```

## Validation groupée à effectuer

Après intégration :

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_certification_domain_permissions
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m alembic check
```

Attendu :

```text
No new upgrade operations detected.
```

Puis exécuter la campagne Swagger décrite dans :

```text
TESTS_ENDPOINTS_ORGANISMES_CERTIFICATIONS.md
```

Lorsque tous les tests passent, marquer :

```text
DOMAINE ORGANISMES / CERTIFICATIONS / DOCUMENTS
= ✅ TERMINÉ ET VALIDÉ
```

## Prochaine famille après validation

```text
COLLECTE
├── campagnes
├── missions_collecte
├── affectations_mission
├── fiches_collecte
├── offres_declarees
├── certifications_declarees
└── evenements_collecte
```

Le domaine Collecte sera lui aussi livré intégralement avec tous ses sous-modules, endpoints, interactions, permissions, audits et tests groupés.

# DOMAINE COLLECTE

## Statut

🟠 **Implémentation complète fournie — intégration et tests groupés à effectuer**

Le lot couvre simultanément :

```text
COLLECTE
├── campagnes
├── missions_collecte
├── affectations_mission
├── fiches_collecte
├── offres_declarees
├── certifications_declarees
└── evenements_collecte
```

Aucune modification du MPD n'est réalisée.

Le dictionnaire physique utilisé pour ce domaine comprend :
- `campagnes` ;
- `missions_collecte` ;
- `affectations_mission` ;
- `fiches_collecte` ;
- `offres_declarees` ;
- `certifications_declarees` ;
- `evenements_collecte`.

## Registre exhaustif des endpoints Collecte

### Campagnes

```text
GET   /api/v1/campagnes
POST  /api/v1/campagnes
GET   /api/v1/campagnes/{campagne_id}
PATCH /api/v1/campagnes/{campagne_id}
```

État : **créés dans le lot / tests à effectuer**

### Missions — vue globale

```text
GET /api/v1/missions
GET /api/v1/missions/{mission_id}
```

Filtres disponibles sur la liste :

```text
campagne_id
zone_id
statut
assigned_user_id
limit
offset
```

État : **créés dans le lot / tests à effectuer**

### Missions — vue par campagne

```text
GET   /api/v1/campagnes/{campagne_id}/missions
POST  /api/v1/campagnes/{campagne_id}/missions
PATCH /api/v1/campagnes/{campagne_id}/missions/{mission_id}
```

État : **créés dans le lot / tests à effectuer**

### Affectations de mission

```text
GET   /api/v1/missions/{mission_id}/affectations
POST  /api/v1/missions/{mission_id}/affectations
PATCH /api/v1/missions/{mission_id}/affectations/{affectation_id}
```

État : **créés dans le lot / tests à effectuer**

### Fiches de collecte / révisions

```text
GET   /api/v1/missions/{mission_id}/fiches
GET   /api/v1/missions/{mission_id}/fiches/current
POST  /api/v1/missions/{mission_id}/fiches
GET   /api/v1/missions/{mission_id}/fiches/{fiche_id}
PATCH /api/v1/missions/{mission_id}/fiches/{fiche_id}
POST  /api/v1/missions/{mission_id}/fiches/{fiche_id}/submit
POST  /api/v1/missions/{mission_id}/fiches/{fiche_id}/revision
GET   /api/v1/missions/{mission_id}/fiches/{fiche_id}/history
```

État : **créés dans le lot / tests à effectuer**

### Offres déclarées

```text
GET   /api/v1/missions/{mission_id}/fiches/{fiche_id}/offres
POST  /api/v1/missions/{mission_id}/fiches/{fiche_id}/offres
PATCH /api/v1/missions/{mission_id}/fiches/{fiche_id}/offres/{offre_id}
```

État : **créés dans le lot / tests à effectuer**

### Certifications déclarées

```text
GET   /api/v1/missions/{mission_id}/fiches/{fiche_id}/certifications
POST  /api/v1/missions/{mission_id}/fiches/{fiche_id}/certifications
PATCH /api/v1/missions/{mission_id}/fiches/{fiche_id}/certifications/{certification_declaree_id}
```

État : **créés dans le lot / tests à effectuer**

## Interaction complète du domaine Collecte

```text
campagnes
    │
    └── missions_collecte ───────── zones_administratives
             │
             ├── affectations_mission ───── utilisateurs
             │
             └── fiches_collecte
                    │
                    ├── entreprise_id ───── entreprises
                    ├── offres_declarees
                    ├── certifications_declarees
                    │       └── certification_officielle_id
                    │             ↓
                    │        certifications
                    │        (rapprochement futur)
                    │
                    └── evenements_collecte
```

### Campagne ↔ Missions

Clé physique :

```text
missions_collecte.campagne_id
    →
campagnes.id
```

Le MCD conceptuel mentionnait qu'une mission pouvait relever de zéro ou une campagne, mais le MPD actuellement déployé impose `campagne_id NOT NULL`.

Le backend suit donc le MPD réel :
- toute mission créée doit appartenir à une campagne ;
- une mission ne peut pas être déplacée silencieusement vers une autre campagne ;
- la route parent/enfant contrôle l'appartenance réelle de la mission.

### Mission ↔ Zone administrative

```text
missions_collecte.zone_id
    →
zones_administratives.id
```

La zone doit exister avant création ou modification d'une mission.

### Mission ↔ Affectations

```text
affectations_mission.mission_id
    →
missions_collecte.id

affectations_mission.utilisateur_id
    →
utilisateurs.id

affectations_mission.attribue_par_id
    →
utilisateurs.id
```

Règles :
- l'utilisateur affecté doit exister et être ACTIF ;
- l'auteur d'une affectation est toujours l'utilisateur authentifié ;
- `attribue_par_id` n'est jamais accepté depuis le JSON ;
- une seconde affectation active identique utilisateur/mission est refusée ;
- la période, le motif, le rôle dans la mission et le statut sont conservés.

### Mission ↔ Entreprise : écart MCD / MPD

Le MCD indique :

```text
MISSION_COLLECTE → ENTREPRISE
```

mais le MPD physique ne contient pas `entreprise_id` dans `missions_collecte`.

La relation disponible est :

```text
fiches_collecte.entreprise_id
    →
entreprises.id
```

Décision :
- aucune migration n'est inventée ;
- le backend ne prétend pas que la mission possède directement une entreprise ;
- l'entreprise collectée est portée par la fiche.

### Mission ↔ Fiches / révisions

```text
fiches_collecte.mission_id
    →
missions_collecte.id
```

La règle métier RG-012 exige une seule révision courante par mission.

Le MPD ne possède pas de colonne `est_courante`.

Implémentation actuelle :

```text
plus grand numero_revision = révision courante
```

Exemple :

```text
Mission
  ├── Révision 1  historique
  ├── Révision 2  historique
  └── Révision 3  COURANTE
```

Une nouvelle fiche directe est interdite lorsqu'une fiche existe déjà pour la mission.

Pour continuer après une fiche soumise, l'API utilise :

```text
POST /missions/{mission_id}/fiches/{fiche_id}/revision
```

La nouvelle révision :
- reçoit `numero_revision + 1` ;
- repart en `BROUILLON` ;
- copie les valeurs déclaratives de la révision précédente ;
- copie les offres et certifications déclarées ;
- ne recopie pas automatiquement le rapprochement d'une certification déclarée avec une certification officielle.

### Fiche ↔ Offres déclarées

```text
offres_declarees.fiche_collecte_id
    →
fiches_collecte.id
```

Les offres déclarées restent des **données de terrain**.

Elles ne remplacent jamais silencieusement :

```text
offres_entreprise
```

Elles seront exploitées plus tard par la Vérification puis l'intégration BNEC.

### Fiche ↔ Certifications déclarées

```text
certifications_declarees.fiche_collecte_id
    →
fiches_collecte.id
```

Une certification déclarée conserve :
- le nom déclaré ;
- le numéro déclaré ;
- l'organisme déclaré ;
- la norme déclarée ;
- la portée ;
- les dates ;
- la présence déclarée d'une copie.

Les champs :

```text
certification_officielle_id
score_rapprochement
statut_rapprochement
```

sont exposés en lecture mais ne sont pas modifiables par l'agent de collecte.

Ils appartiennent à la future étape de Vérification.

### Fiche ↔ Historique métier

```text
evenements_collecte.fiche_collecte_id
    →
fiches_collecte.id
```

Le backend génère lui-même l'historique.

Événements actuels :

```text
CREATION_BROUILLON
MISE_A_JOUR_BROUILLON
SOUMISSION
REVISION_SUIVANTE_CREEE
NOUVELLE_REVISION
```

`evenements_collecte` et `evenements_audit` restent distincts :
- le premier décrit l'histoire métier de la fiche ;
- le second décrit l'action technique/utilisateur dans le système.

### Complétude et soumission

La règle RG-013 impose :

```text
soumission interdite si la complétude obligatoire n'est pas atteinte
```

Les champs obligatoires officiels ne sont cependant pas encore définitivement validés.

Décision technique :
- aucune liste de champs obligatoires n'est codée en dur ;
- le backend cherche une règle `regles_metier` :

```text
code = COLLECTE_COMPLETUDE
statut = PUBLIE ou ACTIF
```

- le calcul du taux est effectué côté serveur ;
- si aucune règle publiée n'existe, le brouillon fonctionne mais la soumission retourne `409 Conflict` ;
- cela empêche une règle provisoire d'être présentée comme règle officielle.

Format technique prévu dans `parametres` :

```json
{
  "required_fields": [
    "entreprise_id",
    "version_formulaire",
    "nom_declarant",
    "telephone_declarant|email_declarant",
    "consentement_obtenu",
    "signature_declarant"
  ],
  "minimum_submission_rate": 100
}
```

Cette liste est un exemple de format uniquement et n'est pas considérée comme la règle institutionnelle officielle.

### Collecte ↔ Documents

Le module Documents doit reconnaître en plus :

```text
FICHE_COLLECTE
OFFRE_DECLAREE
CERTIFICATION_DECLAREE
```

Cela permet de déposer les pièces de terrain sans les rendre publiques.

Exemple :

```text
ressource_type = CERTIFICATION_DECLAREE
ressource_id   = certifications_declarees.id
```

### Collecte ↔ Vérification

La transition suivante du workflow est :

```text
FICHE_COLLECTE SOUMISE
        ↓
DOSSIER_VERIFICATION
```

Le domaine Collecte **ne crée pas encore automatiquement** le dossier de vérification.

Cette responsabilité sera ajoutée dans le domaine Vérification afin de maintenir la séparation officielle :

```text
Collecte
≠
Vérification
≠
Contrôle FUCCS
≠
Validation
≠
Intégration BNEC
```

## Permissions utilisées

Aucune nouvelle permission n'est nécessaire pour ce lot.

Permissions existantes :

```text
COLLECTE.LIRE
COLLECTE.AFFECTER
COLLECTE.CREER
COLLECTE.MODIFIER
COLLECTE.SOUMETTRE
```

Répartition :

```text
COLLECTE.LIRE
    → lecture campagnes / missions / affectations / fiches / déclarations

COLLECTE.AFFECTER
    → création/modification campagnes et missions
    → gestion des affectations

COLLECTE.CREER
    → création initiale d'une fiche

COLLECTE.MODIFIER
    → édition du brouillon courant
    → offres déclarées
    → certifications déclarées
    → création d'une nouvelle révision

COLLECTE.SOUMETTRE
    → soumission de la fiche courante
```

## Événements d'audit attendus

```text
COLLECTE_CAMPAIGN_CREATE
COLLECTE_CAMPAIGN_UPDATE

COLLECTE_MISSION_CREATE
COLLECTE_MISSION_UPDATE

COLLECTE_MISSION_ASSIGN
COLLECTE_MISSION_ASSIGN_UPDATE

COLLECTE_FORM_CREATE
COLLECTE_FORM_UPDATE
COLLECTE_FORM_SUBMIT
COLLECTE_FORM_REVISION_CREATE

COLLECTE_DECLARED_OFFER_CREATE
COLLECTE_DECLARED_OFFER_UPDATE

COLLECTE_DECLARED_CERT_CREATE
COLLECTE_DECLARED_CERT_UPDATE
```

## Fichiers livrés

```text
app/schemas/campagne.py
app/schemas/mission_collecte.py
app/schemas/fiche_collecte.py
app/schemas/declarations_collecte.py

app/repositories/campagne_repository.py
app/repositories/mission_collecte_repository.py
app/repositories/fiche_collecte_repository.py

app/services/campagne_service.py
app/services/mission_collecte_service.py
app/services/fiche_collecte_service.py

app/routes/api/v1/campagnes.py
app/routes/api/v1/missions_collecte.py
app/routes/api/v1/fiches_collecte.py
```

Documentation livrée :

```text
ROUTER_INTEGRATION.md
INTEGRATION_DOCUMENTS_COLLECTE.md
REGLE_COMPLETUDE.md
INTERACTIONS_DOMAINE.md
TESTS_ENDPOINTS_COLLECTE.md
```

## Validation groupée

Après intégration :

```powershell
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m alembic check
```

Attendu :

```text
No new upgrade operations detected.
```

Puis tester tous les endpoints Collecte.

Lorsque les tests passent :

```text
DOMAINE COLLECTE
= ✅ TERMINÉ ET VALIDÉ
```

## Prochaine famille

```text
VERIFICATION
├── dossiers_verification
├── affectations_verification
├── points_verification
├── anomalies_verification
└── confirmations_externes
```

Ce prochain lot devra notamment implémenter :
- ouverture depuis une fiche SOUMISE ;
- affectation des vérificateurs ;
- points de contrôle ;
- anomalies ;
- confirmations externes ;
- rapprochement certification déclarée ↔ certification officielle ;
- preuves documentaires ;
- historique/audit ;
- séparation stricte Vérification / Validation.

# AJUSTEMENT COLLECTE — SNAPSHOT COMPOSITE ABANDONNÉ

## Statut

⛔ **ABANDONNÉ — NE PAS INTÉGRER LE PATCH SNAPSHOT**

Ce correctif répond à une contrainte importante du formulaire HAUQE :
la fiche de collecte contient plus de données que les seules colonnes de
`fiches_collecte`.

Le formulaire terrain doit pouvoir couvrir en une seule saisie :
- identité de l'entreprise ;
- contacts ;
- sites ;
- offres / produits ;
- marchés ;
- certifications ;
- organismes certificateurs ;
- accréditations ;
- justificatifs ;
- consentement et signature.

Le MPD actuel ne possède cependant pas de tables déclaratives dédiées pour
tous ces objets.

Décision retenue : **ne pas modifier le MPD**.

Le payload complet est sauvegardé comme snapshot JSON privé et versionné via
`documents`.

## Nouveaux endpoints

```text
PUT /api/v1/missions/{mission_id}/fiches/{fiche_id}/intake
GET /api/v1/missions/{mission_id}/fiches/{fiche_id}/intake
GET /api/v1/missions/{mission_id}/fiches/{fiche_id}/intake/projection
```

État : **créés dans le patch / tests à effectuer**

### PUT intake

Sauvegarde une nouvelle version du formulaire composite.

Conditions :
- la fiche existe ;
- elle appartient à la mission indiquée ;
- elle est au statut `BROUILLON` ;
- chaque sauvegarde crée une nouvelle version de snapshot ;
- aucun ancien snapshot n'est écrasé.

Le document technique créé utilise :

```text
type_document  = SNAPSHOT_COLLECTE
ressource_type = FICHE_COLLECTE
ressource_id   = fiches_collecte.id
format         = JSON
confidentialite = INTERNE
source         = SYSTEME_COLLECTE
```

Les colonnes natives de `fiches_collecte` sont synchronisées :
- consentement ;
- déclarant ;
- fonction ;
- téléphone ;
- courriel ;
- signature ;
- observations ;
- collecteur ;
- date de collecte.

### GET intake

Retourne le dernier snapshot composite de la fiche.

Il sert notamment à reprendre un brouillon sans perte des informations qui ne
possèdent pas de colonne dédiée dans `fiches_collecte`.

### GET intake/projection

Retourne une projection structurée destinée au pré-remplissage des étapes
suivantes.

```text
Collecte
   ↓
projection
   ├── Entreprise
   ├── Contacts
   ├── Sites
   ├── Offres
   └── Certifications
          ├── Organisme
          └── Accréditation
```

La réponse porte explicitement :

```text
source = COLLECTE_DECLAREE
verification_requise = true
```

La projection n'est donc jamais considérée comme une donnée officielle.

## Interaction corrigée Collecte → Entreprise / Organisme / Certification

```text
FORMULAIRE TERRAIN COMPLET
           │
           ▼
 SNAPSHOT COLLECTE JSON
           │
           ├──────── informations entreprise
           ├──────── contacts
           ├──────── sites
           ├──────── offres
           └──────── certifications
                      ├── organisme déclaré
                      └── accréditation déclarée
           │
           ▼
       FICHE SOUMISE
           │
           ▼
      VÉRIFICATION
           │
           ├── rapprochement entreprise existante
           ├── contrôle doublons entreprise
           ├── rapprochement organisme
           ├── contrôle accréditation
           ├── rapprochement certification officielle
           ├── preuves
           └── confirmation externe si nécessaire
           │
           ▼
       VALIDATION
           │
           ▼
     INTÉGRATION BNEC
```

## Pourquoi les tables officielles ne sont pas remplies immédiatement

La procédure distingue :
- les données déclarées pendant la collecte ;
- les données vérifiées ;
- les données validées ;
- les données officiellement intégrées dans la BNEC.

Le snapshot permet donc de pré-remplir sans faire :

```text
déclaration terrain = vérité officielle
```

Les modules `entreprises`, `organismes` et `certifications` pourront être
pré-alimentés visuellement et techniquement à partir de la projection, mais
leur création/mise à jour officielle sera contrôlée par Vérification /
Validation / Intégration.

## Données conservées par le snapshot

### Entreprise

```text
raison_sociale
nom_commercial
forme_juridique
rccm
nif
ifu
date_creation
nationalite
effectif
email_principal
telephone_principal
site_web
adresse_siege
zone_siege_id
activite_principale
secteurs_secondaires
```

### Contacts

```text
nom
prenoms
fonction
telephone
email
type_contact
contact_principal
```

### Sites

```text
nom
type_site
adresse
zone_id
latitude
longitude
date_ouverture
effectif
```

### Offres

```text
type_offre
nom
description
categorie
volume
unite
capacite
marches_vises
```

### Certifications

```text
nom_certification
numero
norme_declaree
portee
date_obtention
date_effet
date_expiration
statut_declare
nature
copie_disponible
absence_preuve_justification
produits_couverts
```

Chaque certification peut contenir :

```text
organisme
    ├── nom_officiel
    ├── sigle
    ├── type_organisme
    ├── pays
    ├── numero_enregistrement
    ├── email
    ├── telephone
    ├── adresse
    ├── zone_id
    └── site_web

accreditation
    ├── numero
    ├── accrediteur
    ├── domaine_technique
    ├── perimetre
    ├── date_delivrance
    ├── date_expiration
    └── reference_officielle
```

Un champ `extras` reste disponible dans le snapshot pour conserver les
éléments de la fiche terrain qui ne disposent pas encore d'une projection
MPD directe.

## Sécurité et historique

Chaque sauvegarde :
- crée un nouveau fichier JSON ;
- génère un checksum SHA-256 ;
- conserve l'auteur ;
- conserve la date ;
- est stockée sous le répertoire documentaire privé ;
- ne supprime pas la version précédente ;
- génère l'événement d'audit :

```text
COLLECTE_INTAKE_SNAPSHOT_SAVE
```

Permission :

```text
COLLECTE.MODIFIER
    → sauvegarde du snapshot

COLLECTE.LIRE
    → lecture du snapshot et de sa projection
```

## Prochaine intégration dans Vérification

Le domaine Vérification devra consommer :

```text
GET /missions/{mission_id}/fiches/{fiche_id}/intake/projection
```

pour construire son dossier candidat.

Il devra ensuite produire trois décisions distinctes :

```text
1. MATCH_EXISTANT
   → rattacher la donnée déclarée à un objet BNEC existant

2. CREATION_CANDIDATE
   → préparer la création d'un nouvel objet

3. CONFLIT / DOUBLON / A_VERIFIER
   → ouvrir anomalie ou confirmation externe
```

Cette logique s'appliquera séparément à :
- entreprise ;
- organisme ;
- accréditation ;
- certification.

La Vérification ne devra jamais fusionner automatiquement deux entreprises,
deux organismes ou deux certifications.

## Décision métier définitive sur la fiche de collecte simplifiée

Après échange terrain avec HAUQE / point focal, la fiche de collecte reste volontairement simplifiée.

Principe :

```text
BASE DE DONNÉES LARGE ET COMPLÈTE
        ↓
FRONTEND SIMPLIFIÉ
        ↓
API N'EXPOSE QUE LES CHAMPS ACTUELS
        ↓
SEULES CES COLONNES SONT RENSEIGNÉES
        ↓
LES AUTRES RESTENT NULL / INUTILISÉES
```

Il n'est donc pas nécessaire de créer un mécanisme de snapshot déclaratif pour conserver des champs que le frontend ne demande pas encore.

Quand HAUQE décidera d'élargir la collecte :

```text
nouveaux champs frontend
        ↓
extension des schémas API
        ↓
utilisation des colonnes déjà présentes dans le MPD
```

Aucune modification du MCD/MLD/MPD ne sera nécessaire tant que les nouveaux besoins correspondent à des colonnes déjà prévues.

### Interaction simplifiée de la collecte avec les modules existants

La fiche de collecte peut directement renseigner les champs actuellement affichés de :

```text
FICHE DE COLLECTE
      ├──→ ENTREPRISE
      ├──→ CONTACTS / SITES / OFFRES si affichés
      ├──→ ORGANISME CERTIFICATEUR
      └──→ CERTIFICATION
```

Les données non demandées actuellement restent simplement non renseignées.

Les contrôles métier restent applicables :
- données partielles autorisées lorsque les champs sont facultatifs dans le modèle ;
- aucun champ invisible n'est exigé artificiellement par l'API ;
- les validations doivent porter uniquement sur les champs effectivement exposés et obligatoires dans le formulaire courant ;
- les statuts métier permettent de distinguer une donnée encore à vérifier d'une donnée validée.

### Endpoints snapshot supprimés du plan actif

Les routes suivantes ne font plus partie de l'architecture à intégrer :

```text
PUT /api/v1/missions/{mission_id}/fiches/{fiche_id}/intake
GET /api/v1/missions/{mission_id}/fiches/{fiche_id}/intake
GET /api/v1/missions/{mission_id}/fiches/{fiche_id}/intake/projection
```

Elles sont conservées uniquement dans l'historique de conception de cette feuille de route comme proposition abandonnée.

### Règle pour les prochains développements

Pour chaque module :

1. conserver toutes les colonnes existantes du MPD ;
2. n'exposer dans Pydantic que les champs réellement utilisés par le frontend courant ;
3. ne pas forcer les colonnes non utilisées ;
4. utiliser directement les tables métier existantes ;
5. élargir les schémas/endpoints plus tard lorsque HAUQE ajoute des champs au formulaire ;
6. ne modifier le modèle de données que si un besoin futur n'existe réellement pas dans le MPD.

# DOMAINES VÉRIFICATION + FUCCS — LOT GROUPÉ

## Statut

🟠 **Implémentation complète fournie — intégration et tests groupés à effectuer**

Sous-modules couverts :

```text
VÉRIFICATION
├── dossiers_verification
├── affectations_verification
├── points_verification
├── anomalies_verification
└── confirmations_externes

FUCCS
├── grilles_fuccs
├── rubriques_fuccs
├── criteres_fuccs
├── controles_fuccs
├── notes_criteres
└── constats_controle
```

Aucune migration Alembic n'est requise.

## Registre exhaustif des endpoints créés

```text
GET    /api/v1/verifications
POST   /api/v1/verifications/from-fiche/{fiche_id}
GET    /api/v1/verifications/{dossier_id}
PATCH  /api/v1/verifications/{dossier_id}
POST   /api/v1/verifications/{dossier_id}/close
POST   /api/v1/verifications/{dossier_id}/reopen
GET    /api/v1/verifications/{dossier_id}/affectations
POST   /api/v1/verifications/{dossier_id}/affectations
PATCH  /api/v1/verifications/{dossier_id}/affectations/{assignment_id}
GET    /api/v1/verifications/{dossier_id}/points
POST   /api/v1/verifications/{dossier_id}/points
PATCH  /api/v1/verifications/{dossier_id}/points/{point_id}
GET    /api/v1/verifications/{dossier_id}/anomalies
POST   /api/v1/verifications/{dossier_id}/anomalies
PATCH  /api/v1/verifications/{dossier_id}/anomalies/{anomaly_id}
POST   /api/v1/verifications/{dossier_id}/anomalies/{anomaly_id}/resolve
POST   /api/v1/verifications/{dossier_id}/anomalies/{anomaly_id}/escalate
GET    /api/v1/verifications/{dossier_id}/confirmations
POST   /api/v1/verifications/{dossier_id}/confirmations
PATCH  /api/v1/verifications/{dossier_id}/confirmations/{confirmation_id}
POST   /api/v1/verifications/{dossier_id}/confirmations/{confirmation_id}/response
GET    /api/v1/fuccs/grilles
GET    /api/v1/fuccs/grilles/active
POST   /api/v1/fuccs/grilles
GET    /api/v1/fuccs/grilles/{grid_id}
PATCH  /api/v1/fuccs/grilles/{grid_id}
POST   /api/v1/fuccs/grilles/{grid_id}/clone
POST   /api/v1/fuccs/grilles/{grid_id}/publish
POST   /api/v1/fuccs/grilles/{grid_id}/retire
GET    /api/v1/fuccs/grilles/{grid_id}/rubriques
POST   /api/v1/fuccs/grilles/{grid_id}/rubriques
PATCH  /api/v1/fuccs/grilles/{grid_id}/rubriques/{rubric_id}
DELETE /api/v1/fuccs/grilles/{grid_id}/rubriques/{rubric_id}
GET    /api/v1/fuccs/grilles/{grid_id}/criteres
POST   /api/v1/fuccs/grilles/{grid_id}/rubriques/{rubric_id}/criteres
PATCH  /api/v1/fuccs/grilles/{grid_id}/rubriques/{rubric_id}/criteres/{criterion_id}
DELETE /api/v1/fuccs/grilles/{grid_id}/rubriques/{rubric_id}/criteres/{criterion_id}
GET    /api/v1/fuccs/controles
POST   /api/v1/verifications/{dossier_id}/fuccs-controles
GET    /api/v1/fuccs/controles/{control_id}
GET    /api/v1/fuccs/controles/{control_id}/notes
PUT    /api/v1/fuccs/controles/{control_id}/notes/{criterion_id}
GET    /api/v1/fuccs/controles/{control_id}/constats
POST   /api/v1/fuccs/controles/{control_id}/constats
PATCH  /api/v1/fuccs/controles/{control_id}/constats/{finding_id}
POST   /api/v1/fuccs/controles/{control_id}/finalize
POST   /api/v1/fuccs/controles/{control_id}/reopen
```

Total du lot : **47 endpoints**.

## Pages frontend concernées

- `verifications.html` / `#/verifications` : tous les endpoints `/api/v1/verifications...` hors création de contrôle FUCCS ;
- `controle.html` / `#/controle` : grille active, contrôle, notes, constats, finalisation et réouverture ;
- `referentiels.html` et `regles-codification.html` : administration des versions de grille, rubriques et critères ;
- `validations.html` : ne modifie ni Vérification ni FUCCS ; elle consommera leurs résultats dans le prochain domaine.

## Permissions ajoutées / synchronisées

```text
VERIFICATION.LIRE
VERIFICATION.OUVRIR
VERIFICATION.AFFECTER
VERIFICATION.VERIFIER
VERIFICATION.SIGNALER_ANOMALIE
VERIFICATION.CONFIRMER
VERIFICATION.CLOTURER

FUCCS.LIRE
FUCCS.ADMINISTRER_GRILLE
FUCCS.CONTROLER
FUCCS.FINALISER
FUCCS.REOUVRIR
```

Script idempotent :

```text
app/scripts/seed_verification_fuccs_permissions.py
```

## Événements d'audit présents dans le lot

```text
FUCCS_CONTROL_CREATE
FUCCS_CONTROL_FINALIZE
FUCCS_CONTROL_REOPEN
FUCCS_CRITERION_CREATE
FUCCS_CRITERION_DELETE_DRAFT
FUCCS_CRITERION_UPDATE
FUCCS_FINDING_CREATE
FUCCS_FINDING_UPDATE
FUCCS_GRID_CLONE
FUCCS_GRID_CREATE
FUCCS_GRID_PUBLISH
FUCCS_GRID_RETIRE
FUCCS_GRID_UPDATE
FUCCS_NOTE_CREATE
FUCCS_NOTE_UPDATE
FUCCS_RUBRIC_CREATE
FUCCS_RUBRIC_DELETE_DRAFT
FUCCS_RUBRIC_UPDATE
VERIFICATION_ANOMALY_CREATE
VERIFICATION_ANOMALY_ESCALATE
VERIFICATION_ANOMALY_RESOLVE
VERIFICATION_ANOMALY_UPDATE
VERIFICATION_ASSIGN
VERIFICATION_ASSIGN_UPDATE
VERIFICATION_CONFIRMATION_CREATE
VERIFICATION_CONFIRMATION_RESPONSE
VERIFICATION_CONFIRMATION_UPDATE
VERIFICATION_DOSSIER_CLOSE
VERIFICATION_DOSSIER_OPEN
VERIFICATION_DOSSIER_REOPEN
VERIFICATION_DOSSIER_UPDATE
VERIFICATION_POINT_CREATE
VERIFICATION_POINT_UPDATE
```

## Règles structurantes

- seule une fiche `SOUMISE` peut ouvrir un dossier ;
- un seul dossier non clôturé est autorisé simultanément par fiche ;
- la Vérification reste distincte de la Validation ;
- `verified_compliant` exige aucune anomalie non résolue et aucune confirmation en attente ;
- le contrôle FUCCS ne s'ouvre qu'après clôture de la Vérification avec `verified_compliant` ou `verified_with_reservation` ;
- le nombre de critères FUCCS n'est jamais codé en dur ;
- la version frontend active comporte actuellement 24 critères visibles, mais le backend dérive toujours le nombre de critères et le score maximal depuis la grille publiée ;
- une grille publiée est immuable ;
- toute évolution de grille passe par clone → brouillon → publication ;
- le contrôle conserve `grille_fuccs_id`, donc les anciens résultats restent reproductibles ;
- commentaire et preuve sont contrôlés selon les propriétés de chaque critère ;
- un contrôle finalisé est verrouillé jusqu'à une réouverture explicitement autorisée et auditée.

# Interactions — Vérification + FUCCS

```text
FICHE_COLLECTE SOUMISE
        ↓
DOSSIER_VERIFICATION
        ├── AFFECTATIONS_VERIFICATION → UTILISATEURS
        ├── POINTS_VERIFICATION → DOCUMENTS
        ├── ANOMALIES_VERIFICATION
        └── CONFIRMATIONS_EXTERNES → ORGANISMES / DOCUMENTS
        ↓
AVIS DE VERIFICATION
        ↓
verified_compliant
ou verified_with_reservation
        ↓
CONTROLE_FUCCS
        ├── GRILLE_FUCCS publiée
        │      └── RUBRIQUES
        │              └── CRITERES
        ├── NOTES_CRITERES → DOCUMENTS
        └── CONSTATS_CONTROLE
        ↓
CONTROLE FINALISE
        ↓
VALIDATION (prochain domaine)
```

## Point important sur la collecte simplifiée

La Vérification porte sur les données réellement affichées/collectées par la version courante du frontend. Les colonnes prévues dans le MPD mais non affichées restent simplement non renseignées.

## Confirmation externe

Le MPD physique contient `organisme_id` mais pas `entreprise_id`.
Une confirmation à une entreprise ou un tiers reste possible grâce à
`destinataire`, sans modification du MPD.

## FUCCS

Le nombre de critères est fourni par la version de grille. Une grille publiée
est immuable ; toute évolution passe par clone -> brouillon -> publication.

Le contrôle garde `grille_fuccs_id`, donc les anciens contrôles restent
reproductibles après publication d'une nouvelle version.


## Validation groupée

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_verification_fuccs_permissions
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m alembic check
```

Attendu :

```text
No new upgrade operations detected.
```

## Prochaine famille

```text
VALIDATION / INTÉGRATION BNEC
├── validations
├── corrections
├── integrations_bnec
└── elements_integration
```

# DOMAINE VALIDATION / INTÉGRATION BNEC — LOT GROUPÉ

    ## Statut

    🟠 **Implémenté — non validé runtime**

    Les tests Swagger séparés sont volontairement différés. La recette sera
    faite lors du raccordement frontend, page par page.

    Sous-modules :

    ```text
    validations
    corrections
    integrations_bnec
    elements_integration
    ```

    Les champs et FK de ces quatre tables correspondent au MPD existant :
    `validations` relie la fiche, le contrôle FUCCS et le validateur ;
    `corrections` dépend d'une validation ; `integrations_bnec` dépend d'une
    validation et d'un administrateur ; `elements_integration` détaille chaque
    objet traité. fileciteturn39file1

    ## Chaîne métier

    ```text
    FUCCS FINALISE
        ↓
    REVUE NIVEAU 1
        ↓
    VALIDATION DEFINITIVE NIVEAU 2
        ├── AJOURNE → CORRECTION → RESOUMISSION
        ├── REJETE
        └── VALIDE / VALIDE SOUS RESERVE
                     ↓
               INTEGRATION BNEC
                     ↓
                PRECONTROLE
                     ↓
             INTEGRATION EN COURS
                     ↓
               POSTCONTROLE
                     ↓
                 INTEGREE
    ```

    La procédure prévoit bien une revue technique de premier niveau, une
    validation définitive de second niveau, puis seulement l'intégration BNEC.
    fileciteturn42file3turn42file5

    ## Registre exhaustif des endpoints du lot

    ```text
    GET    /api/v1/validations
GET    /api/v1/validations/queue
POST   /api/v1/validations/from-fiche/{fiche_id}/level-1
POST   /api/v1/validations/from-fiche/{fiche_id}/level-2
GET    /api/v1/validations/{validation_id}
GET    /api/v1/validations/{validation_id}/corrections
POST   /api/v1/validations/{validation_id}/corrections
PATCH  /api/v1/validations/{validation_id}/corrections/{correction_id}
POST   /api/v1/validations/{validation_id}/corrections/{correction_id}/resubmit
GET    /api/v1/integrations-bnec
GET    /api/v1/integrations-bnec/queue
POST   /api/v1/validations/{validation_id}/integration-bnec
GET    /api/v1/integrations-bnec/{integration_id}
POST   /api/v1/integrations-bnec/{integration_id}/precontrol
POST   /api/v1/integrations-bnec/{integration_id}/start
GET    /api/v1/integrations-bnec/{integration_id}/elements
POST   /api/v1/integrations-bnec/{integration_id}/elements
PATCH  /api/v1/integrations-bnec/{integration_id}/elements/{element_id}
POST   /api/v1/integrations-bnec/{integration_id}/elements/{element_id}/result
POST   /api/v1/integrations-bnec/{integration_id}/postcontrol
POST   /api/v1/integrations-bnec/{integration_id}/complete
    ```

    **Total : 21 endpoints.**

    ## Rôle frontend — `validations.html` / `#/validations`

    | Endpoint | Rôle sur la page |
    |---|---|
    | `GET /api/v1/validations/queue` | File des dossiers FUCCS finalisés à valider |
    | `GET /api/v1/validations` | Historique et filtres |
    | `GET /api/v1/validations/{validation_id}` | Détail d'une décision |
    | `POST /api/v1/validations/from-fiche/{fiche_id}/level-1` | Bouton **Revue technique N1** |
    | `POST /api/v1/validations/from-fiche/{fiche_id}/level-2` | Bouton **Validation définitive N2** |
    | `GET /api/v1/validations/{validation_id}/corrections` | Onglet Corrections |
    | `POST /api/v1/validations/{validation_id}/corrections` | Demander une correction |
    | `PATCH /api/v1/validations/{validation_id}/corrections/{correction_id}` | Modifier une demande avant resoumission |
    | `POST /api/v1/validations/{validation_id}/corrections/{correction_id}/resubmit` | Enregistrer réponse et resoumission |

    Règles serveur :
    - contrôle FUCCS finalisé obligatoire ;
    - N1 favorable avant N2 ;
    - même utilisateur interdit pour N1 et N2 ;
    - `VALIDE_SOUS_RESERVE` exige une réserve ;
    - toute décision reste historisée ;
    - une correction ne détruit pas la validation source.

    Le frontend documente déjà la double validation et les décisions
    `validé`, `validé sous réserve`, `ajourné`, `rejeté`.
    fileciteturn42file0

    ## Rôle frontend — `#/integrations`

    La feuille frontend prévoit déjà `/integrations` comme file P0 des dossiers
    validés à intégrer, avec précontrôle, codification et postcontrôle.
    fileciteturn44file3

    | Endpoint | Rôle sur la page |
    |---|---|
    | `GET /api/v1/integrations-bnec/queue` | Onglet **À intégrer** |
    | `GET /api/v1/integrations-bnec` | Historique des intégrations |
    | `POST /api/v1/validations/{validation_id}/integration-bnec` | Ouvrir l'intégration |
    | `GET /api/v1/integrations-bnec/{integration_id}` | Panneau détail |
    | `POST /api/v1/integrations-bnec/{integration_id}/precontrol` | Étape Précontrôle |
    | `POST /api/v1/integrations-bnec/{integration_id}/start` | Démarrer l'intégration |
    | `GET /api/v1/integrations-bnec/{integration_id}/elements` | Tableau des objets source→cible |
    | `POST /api/v1/integrations-bnec/{integration_id}/elements` | Ajouter un élément |
    | `PATCH /api/v1/integrations-bnec/{integration_id}/elements/{element_id}` | Préparer/corriger l'élément |
    | `POST /api/v1/integrations-bnec/{integration_id}/elements/{element_id}/result` | Marquer intégré ou en échec |
    | `POST /api/v1/integrations-bnec/{integration_id}/postcontrol` | Étape Postcontrôle |
    | `POST /api/v1/integrations-bnec/{integration_id}/complete` | Clôturer en `INTEGREE` |

    États :

    ```text
    EN_ATTENTE
    → PRECONTROLE
    → INTEGRATION_EN_COURS
    → POSTCONTROLE
    → INTEGREE

    ECHEC
    ```

    Une intégration réussie exige :
    - validation N2 favorable ;
    - précontrôle `OK` ;
    - éléments d'intégration tracés ;
    - tous les éléments `INTEGRE` ;
    - postcontrôle `OK` ;
    - référence de sauvegarde.

    La procédure prévoit ce passage précontrôle → intégration → postcontrôle.
    fileciteturn42file4turn43file8

    ## Limite volontaire

    Aucun format de code national n'est inventé. `code_genere` est tracé dans
    `elements_integration`, mais le format de codification devra rester
    paramétré/validé. Le MCD prévoit justement que chaque élément relie une
    source déclarée à une ressource officielle créée ou mise à jour.
    fileciteturn42file13

    ## Permissions

    ```text
    VALIDATION.LIRE
    VALIDATION.REVUE_N1
    VALIDATION.DECIDER_N2
    VALIDATION.DEMANDER_CORRECTION
    VALIDATION.RESOUMETTRE_CORRECTION

    INTEGRATION.LIRE
    INTEGRATION.OUVRIR
    INTEGRATION.PRECONTROLER
    INTEGRATION.EXECUTER
    INTEGRATION.POSTCONTROLER
    INTEGRATION.CLOTURER
    ```

    ## Audit

    ```text
    BNEC_INTEGRATION_COMPLETE
BNEC_INTEGRATION_ELEMENT_CREATE
BNEC_INTEGRATION_ELEMENT_RESULT
BNEC_INTEGRATION_ELEMENT_UPDATE
BNEC_INTEGRATION_OPEN
BNEC_INTEGRATION_START
BNEC_POSTCONTROL
BNEC_PRECONTROL
VALIDATION_CORRECTION_REQUEST
VALIDATION_CORRECTION_RESUBMIT
VALIDATION_CORRECTION_UPDATE
    ```

    ## Fichiers du lot

    ```text
    app/schemas/validation_bnec.py
    app/repositories/validation_bnec_repository.py
    app/services/validation_bnec_service.py
    app/routes/api/v1/validations.py
    app/routes/api/v1/integrations_bnec.py
    app/scripts/seed_validation_integration_permissions.py
    ```

    ## État de recette

    ```text
    Syntaxe Python                  ✅
    Intégration dans le dépôt       ⏳
    Test runtime API                ⏳
    Raccordement validations.html   ⏳
    Raccordement #/integrations     ⏳
    Validation fonctionnelle        ⏳
    ```

    ## Prochaine famille

    ```text
    SCORING / CLASSIFICATION
    ├── modeles_scoring
    ├── ponderations_scoring
    ├── classifications_entreprise
    ├── resultats_infc
    └── classements_sncc
    ```

# DOMAINE SCORING / CLASSIFICATION / INFC / SNCC

## Statut

🟠 **Implémenté — non validé runtime**

La recette reste différée au raccordement frontend, page par page.

Sous-modules physiques :

```text
modeles_scoring
ponderations_scoring
classifications_entreprise
resultats_infc
classements_sncc
```

Le MPD utilise exactement ces cinq tables. La Classification entreprise,
l'INFC et le SNCC restent des résultats séparés.

## Doctrine

```text
FUCCS
≠
CLASSIFICATION ENTREPRISE
≠
INFC
≠
SNCC
```

Aucune conversion automatique FUCCS → INFC n'est implémentée.

Les modèles et pondérations sont versionnés. Le backend n'inscrit en dur
aucun seuil métier provisoire.

La règle calculée est stockée dans :

```text
modeles_scoring.regle_calcul
```

et les pondérations dans :

```text
ponderations_scoring
```

Une version publiée est immuable et doit être clonée pour évolution.

## Modes techniques génériques disponibles

```text
DIRECT_SCORE
WEIGHTED_AVERAGE_100
SUM_DOMAIN_POINTS
```

Ces modes sont des mécanismes techniques et non des règles institutionnelles
préchargées.

Le modèle publié doit contenir les seuils/classes/niveaux validés.

Politique par défaut pour les données manquantes :

```text
missing_policy = REJECT
```

afin d'empêcher un score trompeur.

## Registre exhaustif des endpoints

```text
GET    /api/v1/scoring/models
GET    /api/v1/scoring/models/active
POST   /api/v1/scoring/models
GET    /api/v1/scoring/models/{model_id}
PATCH  /api/v1/scoring/models/{model_id}
POST   /api/v1/scoring/models/{model_id}/clone
POST   /api/v1/scoring/models/{model_id}/publish
POST   /api/v1/scoring/models/{model_id}/retire
GET    /api/v1/scoring/models/{model_id}/weights
POST   /api/v1/scoring/models/{model_id}/weights
PATCH  /api/v1/scoring/models/{model_id}/weights/{weight_id}
POST   /api/v1/scoring/models/{model_id}/weights/{weight_id}/deactivate
POST   /api/v1/scoring/preview/{object_type}
GET    /api/v1/entreprises/{enterprise_id}/classifications
GET    /api/v1/entreprises/{enterprise_id}/classifications/latest
POST   /api/v1/entreprises/{enterprise_id}/classifications/evaluate
GET    /api/v1/infc/results
POST   /api/v1/infc/results/{result_id}/validate
GET    /api/v1/certifications/{certification_id}/infc
GET    /api/v1/certifications/{certification_id}/infc/latest
POST   /api/v1/certifications/{certification_id}/infc/calculate
GET    /api/v1/sncc
POST   /api/v1/sncc/{sncc_id}/close
GET    /api/v1/certifications/{certification_id}/sncc
GET    /api/v1/certifications/{certification_id}/sncc/current
POST   /api/v1/certifications/{certification_id}/sncc
POST   /api/v1/certifications/{certification_id}/sncc/reclassify
```

Total du lot : **27 endpoints**.

## Administration des modèles

Page principale :

```text
regles-codification.html
```

Endpoints :

```text
GET   /api/v1/scoring/models
GET   /api/v1/scoring/models/active
POST  /api/v1/scoring/models
GET   /api/v1/scoring/models/{model_id}
PATCH /api/v1/scoring/models/{model_id}
POST  /api/v1/scoring/models/{model_id}/clone
POST  /api/v1/scoring/models/{model_id}/publish
POST  /api/v1/scoring/models/{model_id}/retire

GET   /api/v1/scoring/models/{model_id}/weights
POST  /api/v1/scoring/models/{model_id}/weights
PATCH /api/v1/scoring/models/{model_id}/weights/{weight_id}
POST  /api/v1/scoring/models/{model_id}/weights/{weight_id}/deactivate

POST  /api/v1/scoring/preview/{object_type}
```

Le simulateur `/preview` n'enregistre aucun résultat.

## Classification entreprise

Relations :

```text
entreprises.id
    ↓
classifications_entreprise.entreprise_id

modeles_scoring.id
    ↓
classifications_entreprise.modele_scoring_id
```

Endpoints :

```text
GET  /api/v1/entreprises/{enterprise_id}/classifications
GET  /api/v1/entreprises/{enterprise_id}/classifications/latest
POST /api/v1/entreprises/{enterprise_id}/classifications/evaluate
```

Chaque calcul crée une nouvelle ligne historisée.

Le résultat conserve :
- modèle/version ;
- score ;
- classe ;
- sources JSONB ;
- auteur de validation ;
- dates de calcul/validation.

## INFC

Relations :

```text
certifications.id
    ↓
resultats_infc.certification_id

modeles_scoring.id
    ↓
resultats_infc.modele_scoring_id
```

Endpoints :

```text
GET  /api/v1/infc/results
POST /api/v1/infc/results/{result_id}/validate

GET  /api/v1/certifications/{certification_id}/infc
GET  /api/v1/certifications/{certification_id}/infc/latest
POST /api/v1/certifications/{certification_id}/infc/calculate
```

Le calcul produit d'abord :

```text
statut = CALCULE
```

puis la validation produit :

```text
statut = VALIDE
date_validation = date courante
```

`scores_domaines` conserve les entrées et contributions.

`sources` conserve les références métier utilisées.

Les domaines obligatoires proviennent du modèle publié ; ils ne sont pas
figés dans le code.

## SNCC

Relation :

```text
certifications.id
    ↓
classements_sncc.certification_id
```

Endpoints :

```text
GET  /api/v1/sncc
POST /api/v1/sncc/{sncc_id}/close

GET  /api/v1/certifications/{certification_id}/sncc
GET  /api/v1/certifications/{certification_id}/sncc/current
POST /api/v1/certifications/{certification_id}/sncc
POST /api/v1/certifications/{certification_id}/sncc/reclassify
```

Le MPD ne contient pas de FK directe :

```text
classements_sncc → resultats_infc
classements_sncc → modeles_scoring
```

Le backend ne fabrique donc aucune dépendance silencieuse.

Un reclassement :
1. ferme la période précédente à J-1 ;
2. crée une nouvelle ligne ;
3. conserve l'historique ;
4. audit le motif.

Les valeurs classe/statut/risque restent des chaînes contrôlées par le futur
référentiel institutionnel ; aucune matrice provisoire n'est imposée ici.

## Pages frontend

### `scoring.html` / `#/scoring`

Rôle :
- afficher séparément FUCCS, Classification entreprise, INFC et SNCC ;
- montrer les versions de modèle ;
- historique et évolution ;
- ne jamais recalculer lui-même la formule officielle.

### `#/infc`

Rôle :
- domaine par domaine ;
- simulation ;
- calcul ;
- détail des contributions ;
- validation ;
- historique.

### `#/classement-sncc`

Rôle :
- classement courant ;
- statut administratif ;
- niveau de risque ;
- justification ;
- période d'effet ;
- historique des reclassements.

### `regles-codification.html`

Rôle :
- modèles de scoring ;
- pondérations ;
- brouillons ;
- clonage ;
- publication ;
- retrait ;
- simulation.

## Permissions

```text
SCORING.LIRE
SCORING.ADMINISTRER_MODELE

CLASSIFICATION.LIRE
CLASSIFICATION.CALCULER_VALIDER

INFC.LIRE
INFC.CALCULER
INFC.VALIDER

SNCC.LIRE
SNCC.CLASSER
SNCC.RECLASSER
```

## Audit

```text
ENTERPRISE_CLASSIFICATION_CREATE
INFC_CALCULATE
INFC_VALIDATE
SCORING_MODEL_CLONE
SCORING_MODEL_CREATE
SCORING_MODEL_PUBLISH
SCORING_MODEL_RETIRE
SCORING_MODEL_UPDATE
SCORING_WEIGHT_CREATE
SCORING_WEIGHT_DEACTIVATE
SCORING_WEIGHT_UPDATE
SNCC_CLOSE
SNCC_CREATE
SNCC_RECLASSIFY
```

## Fichiers livrés

```text
app/schemas/scoring.py
app/repositories/scoring_repository.py
app/services/scoring_service.py
app/routes/api/v1/scoring.py
app/scripts/seed_scoring_permissions.py

ROUTER_INTEGRATION.md
REGLES_SCORING_VERSIONNEES.md
MAPPING_FRONTEND_ENDPOINTS.md
INTERACTIONS_SCORING.md
TESTS_SCORING_FRONTEND.md
```

## État de recette

```text
Syntaxe Python                    ✅
Bundle                            ✅
Registre endpoints                ✅
Mapping frontend                  ✅
Intégration dans dépôt            ⏳
Test runtime API                  ⏳
Raccordement scoring.html         ⏳
Raccordement #/infc               ⏳
Raccordement #/classement-sncc    ⏳
Validation fonctionnelle          ⏳
```

## Prochaine famille

```text
ÉCHÉANCES / ALERTES / VEILLE
├── echeances
├── alertes
├── notifications
├── dossiers_veille
├── relances_veille
└── rapports_veille
```

# DOMAINE ÉCHÉANCES / ALERTES / NOTIFICATIONS / VEILLE

## Statut

🟠 **Implémenté — non validé runtime**

Recette différée au raccordement frontend page par page.

Sous-modules physiques :

```text
echeances
alertes
notifications
dossiers_veille
relances_veille
rapports_veille
```

Aucune migration Alembic n'est requise.

## Chaîne métier

```text
CERTIFICATIONS / AUDITS / RENOUVELLEMENTS
                  ↓
            SCAN QUOTIDIEN
                  ↓
              ECHEANCES
                  ↓
               ALERTES
                  ├── NOTIFICATIONS IN_APP
                  ├── NOTIFICATIONS EMAIL
                  └── affectation / résolution
                            ↓
                      DOSSIERS VEILLE
                            ↓
                        RELANCES
                            ↓
                     RAPPORTS CVC
```

## Seuils d'alerte implémentés

Fallback métier validé :

```text
J-180  → niveau 1 → Information
J-90   → niveau 2 → Surveillance
J-30   → niveau 3 → Urgence
J0/J+  → niveau 4 → Critique
```

Le moteur cherche d'abord une règle publiée :

```text
VEILLE_SEUILS_EXPIRATION
```

dans `regles_metier.parametres`.

Ainsi le futur module de gouvernance pourra changer les seuils sans modifier
le code.

## Sources du scan quotidien

```text
certifications.date_expiration
audits_certification.date_prevue
renouvellements_certification.date_limite
```

Déduplication échéance :

```text
ressource_type
+ ressource_id
+ type_echeance
+ date_echeance
+ statut actif
```

Déduplication alerte :

```text
echeance_id
+ regle_notification
+ statut actif
```

Les alertes spéciales restent créables manuellement pour les événements
comme suspension, retrait, incohérence documentaire ou changement de portée,
tant que leurs règles automatiques spécifiques ne sont pas publiées.

## Registre exhaustif des endpoints

```text
GET    /api/v1/echeances
POST   /api/v1/echeances
GET    /api/v1/echeances/{deadline_id}
PATCH  /api/v1/echeances/{deadline_id}
POST   /api/v1/echeances/{deadline_id}/complete
POST   /api/v1/echeances/{deadline_id}/cancel
GET    /api/v1/echeances/{deadline_id}/alertes
GET    /api/v1/alertes
POST   /api/v1/alertes
GET    /api/v1/alertes/{alert_id}
PATCH  /api/v1/alertes/{alert_id}
POST   /api/v1/alertes/{alert_id}/assign
POST   /api/v1/alertes/{alert_id}/resolve
POST   /api/v1/alertes/{alert_id}/notifications
GET    /api/v1/notifications
GET    /api/v1/notifications/unread-count
POST   /api/v1/notifications/read-all
POST   /api/v1/notifications/{notification_id}/read
POST   /api/v1/notifications/{notification_id}/retry
POST   /api/v1/notifications/{notification_id}/delivery-result
GET    /api/v1/veille/dashboard
POST   /api/v1/veille/scans/daily
GET    /api/v1/veille/dossiers
POST   /api/v1/veille/dossiers
GET    /api/v1/veille/dossiers/{case_id}
PATCH  /api/v1/veille/dossiers/{case_id}
POST   /api/v1/veille/dossiers/{case_id}/close
GET    /api/v1/veille/dossiers/{case_id}/relances
POST   /api/v1/veille/dossiers/{case_id}/relances
PATCH  /api/v1/veille/dossiers/{case_id}/relances/{followup_id}
POST   /api/v1/veille/dossiers/{case_id}/relances/{followup_id}/response
GET    /api/v1/veille/rapports
POST   /api/v1/veille/rapports/generate
GET    /api/v1/veille/rapports/{report_id}
POST   /api/v1/veille/rapports/{report_id}/validate
```

Total du lot : **35 endpoints**.

## `echeances.html`

```text
GET   /api/v1/echeances
POST  /api/v1/echeances
GET   /api/v1/echeances/{deadline_id}
PATCH /api/v1/echeances/{deadline_id}
POST  /api/v1/echeances/{deadline_id}/complete
POST  /api/v1/echeances/{deadline_id}/cancel
GET   /api/v1/echeances/{deadline_id}/alertes
```

Rôle :
- calendrier/liste ;
- échéances en retard ;
- responsables ;
- priorités ;
- planification manuelle ;
- clôture/annulation ;
- navigation vers les alertes liées.

## `alertes.html`

```text
GET   /api/v1/alertes
POST  /api/v1/alertes
GET   /api/v1/alertes/{alert_id}
PATCH /api/v1/alertes/{alert_id}
POST  /api/v1/alertes/{alert_id}/assign
POST  /api/v1/alertes/{alert_id}/resolve
POST  /api/v1/alertes/{alert_id}/notifications
```

Rôle :
- file des alertes ;
- filtres par niveau/statut/responsable ;
- création d'alerte spéciale ;
- affectation ;
- traitement ;
- résolution motivée ;
- notification interne/externe.

Le MPD ne possède pas de champ `lu` dans `alertes`.

Le frontend doit donc dériver le lu/non-lu depuis
`notifications.date_lecture`.

## Cloche globale

```text
GET  /api/v1/notifications
GET  /api/v1/notifications/unread-count
POST /api/v1/notifications/read-all
POST /api/v1/notifications/{notification_id}/read
POST /api/v1/notifications/{notification_id}/retry
POST /api/v1/notifications/{notification_id}/delivery-result
```

Règles :
- IN_APP disponible immédiatement ;
- EMAIL mis en file ;
- utilisateur non ACTIF exclu ;
- chaque tentative est historisée ;
- succès/erreur/message transport sont conservés.

Worker EMAIL :

```text
app/tasks/process_notification_queue.py
```

Secrets attendus uniquement dans l'environnement :

```text
HAUQE_SMTP_HOST
HAUQE_SMTP_PORT
HAUQE_SMTP_USER
HAUQE_SMTP_PASSWORD
HAUQE_SMTP_FROM
HAUQE_SMTP_USE_TLS
```

## `#/veille`

Dashboard :

```text
GET  /api/v1/veille/dashboard
POST /api/v1/veille/scans/daily
```

Dossiers CVC :

```text
GET   /api/v1/veille/dossiers
POST  /api/v1/veille/dossiers
GET   /api/v1/veille/dossiers/{case_id}
PATCH /api/v1/veille/dossiers/{case_id}
POST  /api/v1/veille/dossiers/{case_id}/close
```

Relances :

```text
GET   /api/v1/veille/dossiers/{case_id}/relances
POST  /api/v1/veille/dossiers/{case_id}/relances
PATCH /api/v1/veille/dossiers/{case_id}/relances/{followup_id}
POST  /api/v1/veille/dossiers/{case_id}/relances/{followup_id}/response
```

Rapports :

```text
GET  /api/v1/veille/rapports
POST /api/v1/veille/rapports/generate
GET  /api/v1/veille/rapports/{report_id}
POST /api/v1/veille/rapports/{report_id}/validate
```

Le rapport calcule :
- certifications distinctes suivies ;
- nombre d'alertes ;
- nombre de renouvellements ;
- délai moyen de traitement des alertes résolues ;
- indicateurs complémentaires JSONB.

`periode_debut` et `periode_fin` restent VARCHAR dans le MPD, mais le service
impose le format ISO `YYYY-MM-DD`.

## Tâche quotidienne

```text
app/tasks/watch_daily_scan.py
```

Elle est idempotente et peut être exécutée par :
- Windows Task Scheduler ;
- cron/systemd ;
- ordonnanceur applicatif ultérieur.

Commande :

```powershell
.\.venv\Scripts\python.exe -m app.tasks.watch_daily_scan
```

## Permissions

```text
ECHEANCES.LIRE
ECHEANCES.GERER

ALERTES.LIRE
ALERTES.CREER
ALERTES.GERER
ALERTES.AFFECTER
ALERTES.RESOUDRE

NOTIFICATIONS.LIRE
NOTIFICATIONS.CREER
NOTIFICATIONS.TRANSPORT

VEILLE.LIRE
VEILLE.SCANNER
VEILLE.GERER
VEILLE.RELANCER
VEILLE.CLOTURER
VEILLE.RAPPORTER
VEILLE.VALIDER_RAPPORT
```

Rôle opérationnel principal :

```text
CELLULE_VEILLE
```

La Direction Technique conserve la supervision et la validation des rapports.

## Audit du lot

```text
WATCH_ALERT_ASSIGN
WATCH_ALERT_CREATE
WATCH_ALERT_RESOLVE
WATCH_ALERT_UPDATE
WATCH_CASE_CLOSE
WATCH_CASE_OPEN
WATCH_CASE_UPDATE
WATCH_DAILY_SCAN
WATCH_DEADLINE_CREATE
WATCH_DEADLINE_UPDATE
WATCH_FOLLOWUP_CREATE
WATCH_FOLLOWUP_RESPONSE
WATCH_FOLLOWUP_UPDATE
WATCH_NOTIFICATION_DELIVERY_RESULT
WATCH_NOTIFICATION_QUEUE
WATCH_NOTIFICATION_READ
WATCH_NOTIFICATION_READ_ALL
WATCH_NOTIFICATION_RETRY
WATCH_REPORT_GENERATE
WATCH_REPORT_VALIDATE
```

## Fichiers livrés

```text
app/schemas/veille.py
app/repositories/veille_repository.py
app/services/veille_service.py
app/routes/api/v1/veille.py

app/tasks/watch_daily_scan.py
app/tasks/process_notification_queue.py

app/scripts/seed_watch_permissions.py

ROUTER_INTEGRATION.md
REGLES_ALERTES_VEILLE.md
MAPPING_FRONTEND_ENDPOINTS.md
INTERACTIONS_VEILLE.md
TESTS_VEILLE_FRONTEND.md
```

## État de recette

```text
Syntaxe Python                ✅
Bundle                        ✅
35 endpoints                  ✅
Mapping frontend              ✅
Permissions                   ✅
Audit                         ✅
Scan quotidien                ✅ code
Worker EMAIL                  ✅ code
SMTP réel                     ⏳ configuration environnement
Intégration dans dépôt        ⏳
Test runtime API              ⏳
Raccordement alertes.html     ⏳
Raccordement echeances.html   ⏳
Raccordement #/veille         ⏳
Validation fonctionnelle      ⏳
```

## Prochaine famille

```text
GOUVERNANCE / QUALITÉ / CONTINUITÉ
├── regles_metier
├── revues_qualite
├── plans_action
├── decisions_institutionnelles
├── publications
├── rapports_generes
├── evenements_audit
├── archives
├── sauvegardes
└── incidents
```

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
- seed `app.scripts.seed_watch_permissions` exécuté par l'utilisateur ✅
- `GET /api/v1/notifications` : permission appliquée et appel réussi ✅
- le domaine Veille complet reste à valider page par page ⏳

# DOMAINE GOUVERNANCE / QUALITÉ / CONTINUITÉ

## Statut

🟠 **Implémenté — non validé runtime**

Le lot regroupe :

```text
regles_metier
revues_qualite
plans_action
decisions_institutionnelles
publications
rapports_generes
evenements_audit
archives
sauvegardes
incidents
```

Aucune migration Alembic n'est requise.

## Important avant test

Exécuter obligatoirement :

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_governance_permissions
```

avant de tester les nouveaux endpoints, afin d'éviter les `403 Permission insuffisante`.

## Règles structurantes couvertes

- règles métier administrables et auditées ;
- journal d'audit en lecture seule ;
- absence de suppression physique ;
- conservation minimale de dix ans pour le registre d'archive ;
- diffusion/publication soumise à approbation ;
- plans d'action et amélioration continue ;
- supervision des politiques/exécutions de sauvegarde ;
- tests de restauration tracés ;
- incidents historisés jusqu'à clôture.

## Contrainte `regles_metier.code`

Le MPD actuel impose `regles_metier.code` UNIQUE alors que les règles sont versionnées.

Le lot respecte le MPD sans migration :

```text
logical_code stable
        ↓
code physique unique par version
        ↓
parametres["_logical_code"]
```

Exemple :

```text
logical_code = VEILLE_SEUILS_EXPIRATION
version      = 1.0
code DB      = VEILLE_SEUILS_EXPIRATION__V1_0
```

Autorité commune :

```text
app/rules/business_rule_resolver.py
```

Les lookups existants de Collecte et Veille doivent être raccordés à ce résolveur.

## Registre exhaustif des endpoints

```text
GET    /api/v1/governance/dashboard
GET    /api/v1/governance/rules
GET    /api/v1/governance/rules/active/{logical_code}
POST   /api/v1/governance/rules
GET    /api/v1/governance/rules/{rule_id}
PATCH  /api/v1/governance/rules/{rule_id}
POST   /api/v1/governance/rules/{rule_id}/clone
POST   /api/v1/governance/rules/{rule_id}/publish
POST   /api/v1/governance/rules/{rule_id}/retire
GET    /api/v1/quality/reviews
POST   /api/v1/quality/reviews
GET    /api/v1/quality/reviews/{review_id}
PATCH  /api/v1/quality/reviews/{review_id}
POST   /api/v1/quality/reviews/{review_id}/validate
GET    /api/v1/quality/action-plans
POST   /api/v1/quality/action-plans
GET    /api/v1/quality/action-plans/{plan_id}
PATCH  /api/v1/quality/action-plans/{plan_id}
POST   /api/v1/quality/action-plans/{plan_id}/progress
POST   /api/v1/quality/action-plans/{plan_id}/close
GET    /api/v1/decisions
POST   /api/v1/decisions
GET    /api/v1/decisions/{decision_id}
PATCH  /api/v1/decisions/{decision_id}
POST   /api/v1/decisions/{decision_id}/submit
POST   /api/v1/decisions/{decision_id}/pronounce
GET    /api/v1/publications
POST   /api/v1/publications
GET    /api/v1/publications/{publication_id}
POST   /api/v1/publications/{publication_id}/submit
POST   /api/v1/publications/{publication_id}/approve
POST   /api/v1/publications/{publication_id}/publish
POST   /api/v1/publications/{publication_id}/retire
GET    /api/v1/reports
POST   /api/v1/reports
GET    /api/v1/reports/{report_id}
POST   /api/v1/reports/{report_id}/start
POST   /api/v1/reports/{report_id}/complete
POST   /api/v1/reports/{report_id}/fail
GET    /api/v1/audit/events
GET    /api/v1/audit/events/{event_id}
GET    /api/v1/archives
POST   /api/v1/archives
GET    /api/v1/archives/{archive_id}
GET    /api/v1/backups
POST   /api/v1/backups/policies
PATCH  /api/v1/backups/policies/{policy_id}
POST   /api/v1/backups/policies/{policy_id}/runs
GET    /api/v1/backups/{backup_id}
POST   /api/v1/backups/{backup_id}/complete
POST   /api/v1/backups/{backup_id}/fail
POST   /api/v1/backups/{backup_id}/restore-tests
GET    /api/v1/incidents
POST   /api/v1/incidents
GET    /api/v1/incidents/{incident_id}
PATCH  /api/v1/incidents/{incident_id}
POST   /api/v1/incidents/{incident_id}/assign
POST   /api/v1/incidents/{incident_id}/resolve
POST   /api/v1/incidents/{incident_id}/close
```

Total du lot : **59 endpoints**.

## Rôle frontend

### `regles-codification.html`

```text
/api/v1/governance/rules...
```

Rôle :
- brouillons ;
- versions ;
- paramètres ;
- approbation ;
- publication ;
- retrait ;
- version active.

### `#/amelioration-continue`

```text
/api/v1/quality/reviews...
/api/v1/quality/action-plans...
```

Rôle :
- revues qualité ;
- campagnes périodiques/annuelles ;
- constats et preuves ;
- plans d'action ;
- responsables ;
- échéances ;
- progression ;
- clôture.

### `#/decisions`

```text
/api/v1/decisions...
```

Workflow :

```text
BROUILLON → SOUMISE → DECIDEE
```

### `#/publications`

```text
/api/v1/publications...
```

Workflow :

```text
BROUILLON
→ SOUMISE
→ APPROUVEE / REJETEE
→ PUBLIEE
→ RETIREE
```

Aucun endpoint public anonyme n'est activé tant que le périmètre des données diffusables n'est pas arbitré.

### `rapports.html`

```text
/api/v1/reports...
```

Formats autorisés :

```text
PDF
XLSX
CSV
```

Le lot gère le workflow de demande/génération et lie le résultat à un document privé.
Les modèles officiels de rapport ne sont pas inventés.

### `journal-audit.html`

```text
GET /api/v1/audit/events
GET /api/v1/audit/events/{event_id}
```

Lecture seule stricte : aucune mutation n'est exposée.

### `#/archives`

```text
GET  /api/v1/archives
POST /api/v1/archives
GET  /api/v1/archives/{archive_id}
```

Le registre d'archive ne supprime pas la ressource métier.

### `#/sauvegardes`

```text
/api/v1/backups...
```

La BNEC supervise :
- politique ;
- exécution ;
- résultat ;
- intégrité ;
- preuve ;
- test de restauration.

Aucune commande système de sauvegarde n'est exécutée par l'API métier.

### `#/incidents`

```text
/api/v1/incidents...
```

Workflow :

```text
OUVERT → EN_COURS → RESOLU → CLOTURE
```

## Permissions

```text
GOUVERNANCE.LIRE
GOUVERNANCE.ADMINISTRER_REGLES

QUALITE.LIRE
QUALITE.GERER
QUALITE.VALIDER

DECISIONS.LIRE
DECISIONS.PREPARER
DECISIONS.PRONONCER

PUBLICATIONS.LIRE
PUBLICATIONS.DEMANDER
PUBLICATIONS.APPROUVER
PUBLICATIONS.PUBLIER

RAPPORTS.LIRE
RAPPORTS.DEMANDER
RAPPORTS.GENERER

AUDIT.LIRE

ARCHIVES.LIRE
ARCHIVES.CREER

SAUVEGARDES.LIRE
SAUVEGARDES.GERER

INCIDENTS.LIRE
INCIDENTS.DECLARER
INCIDENTS.GERER
INCIDENTS.CLOTURER
```

## Audit du lot

```text
ACTION_PLAN_CLOSE
ACTION_PLAN_CREATE
ACTION_PLAN_PROGRESS
ACTION_PLAN_UPDATE
ARCHIVE_CREATE
BACKUP_POLICY_CREATE
BACKUP_POLICY_UPDATE
BACKUP_RESTORE_TEST_START
BACKUP_RUN_FAIL
BACKUP_RUN_START
GOV_RULE_CLONE
GOV_RULE_CREATE
GOV_RULE_PUBLISH
GOV_RULE_RETIRE
GOV_RULE_UPDATE
INCIDENT_ASSIGN
INCIDENT_CLOSE
INCIDENT_CREATE
INCIDENT_RESOLVE
INCIDENT_UPDATE
INSTITUTIONAL_DECISION_CREATE
INSTITUTIONAL_DECISION_PRONOUNCE
INSTITUTIONAL_DECISION_SUBMIT
INSTITUTIONAL_DECISION_UPDATE
PUBLICATION_APPROVAL
PUBLICATION_CREATE
PUBLICATION_PUBLISH
PUBLICATION_RETIRE
PUBLICATION_SUBMIT
QUALITY_REVIEW_CREATE
QUALITY_REVIEW_UPDATE
QUALITY_REVIEW_VALIDATE
REPORT_GENERATION_COMPLETE
REPORT_GENERATION_FAIL
REPORT_GENERATION_START
REPORT_REQUEST_CREATE
```

## Fichiers livrés

```text
app/schemas/governance.py
app/repositories/governance_repository.py
app/services/governance_service.py
app/routes/api/v1/governance.py
app/rules/business_rule_resolver.py
app/scripts/seed_governance_permissions.py

ROUTER_INTEGRATION.md
INTEGRATION_REGLES_METIER_EXISTANTES.md
MAPPING_FRONTEND_ENDPOINTS.md
INTERACTIONS_GOUVERNANCE.md
TESTS_GOUVERNANCE_FRONTEND.md
```

## État de recette

```text
Syntaxe Python                         ✅
Bundle                                 ✅
59 endpoints                           ✅
Permissions                            ✅ code
Mapping frontend                       ✅
Règles/versionnement                   ✅ code
Journal audit lecture seule            ✅ code
Qualité/plans d'action                 ✅ code
Décisions                              ✅ code
Publications                           ✅ code
Rapports                               ✅ workflow
Archives                               ✅ code
Sauvegardes/restauration               ✅ registre
Incidents                              ✅ code

Seed permissions                       ⏳ à exécuter
Intégration dépôt                      ⏳
Tests runtime                          ⏳
Raccordement frontend                  ⏳
Validation fonctionnelle               ⏳
```

## Prochaine famille

Après ce lot, le backend métier principal est quasiment complet.

Le prochain lot fonctionnel recommandé est :

```text
PILOTAGE / TABLEAUX DE BORD
├── opérationnel
├── tactique
├── stratégique
├── annuel
├── baromètre
└── public agrégé autorisé
```

Puis :

```text
RACCORDEMENT FRONTEND / RECETTE PAGE PAR PAGE
```

# DOMAINE PILOTAGE / TABLEAUX DE BORD / BAROMÈTRE

    ## Statut

    🟠 **Implémenté — non validé runtime**

    Aucun changement de schéma et aucune migration Alembic.

    ```text
    PILOTAGE
    ├── opérationnel
    ├── tactique mensuel
    ├── stratégique trimestriel
    ├── annuel
    ├── baromètre national
    └── public agrégé autorisé
    ```

    ## Avant test

    ```powershell
    .\.venv\Scripts\python.exe -m app.scripts.seed_dashboard_permissions
    ```

    Puis reconnecter le compte si nécessaire.

    ## Endpoints

    ```text
    GET    /api/v1/dashboards/filters
GET    /api/v1/dashboards/indicator-definitions
GET    /api/v1/dashboards/operational
GET    /api/v1/dashboards/tactical
GET    /api/v1/dashboards/strategic
GET    /api/v1/dashboards/annual
GET    /api/v1/barometer
GET    /api/v1/public/indicators
    ```

    Total : **8 endpoints**.

    ## Rôle frontend

    ### `index.html`

    `GET /api/v1/dashboards/operational`

    Alimente :
    - entreprises et certifications ;
    - certifications actives ;
    - nouvelles certifications ;
    - vigilance stratégique ≤ 90 jours ;
    - contrôles FUCCS à planifier ;
    - alertes et échéances ;
    - répartition statuts ;
    - buckets 180/90/30/expiration ;
    - INFC moyen validé ;
    - actions prioritaires ;
    - certifications récentes ;
    - série d'activité.

    Filtres :
    `days`, `zone_id`, `sector`, `norm_id`, `organisme_id`.

    ### Filtres et définitions

    ```text
    GET /api/v1/dashboards/filters
    GET /api/v1/dashboards/indicator-definitions
    ```

    ### `/tableaux-de-bord/tactique`

    `GET /api/v1/dashboards/tactical?year=YYYY&month=MM`

    Pilotage mensuel : Collecte → Vérification → FUCCS → Validation →
    Intégration BNEC → Veille → Qualité, avec comparaison au mois précédent.

    ### `/tableaux-de-bord/strategique`

    `GET /api/v1/dashboards/strategic?year=YYYY&quarter=1..4`

    Pilotage trimestriel : chiffres nationaux, SNCC, régions, secteurs,
    normes, organismes, tendance INFC et synthèse décisionnelle déterministe.

    ### `/tableaux-de-bord/annuel`

    `GET /api/v1/dashboards/annual?year=YYYY`

    Bilan annuel N/N-1, séries trimestrielles, qualité, incidents et continuité.

    ### `/barometre`

    ```text
    GET /api/v1/barometer
    GET /api/v1/barometer?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    ```

    Le baromètre conserve les composantes séparées. Aucun indice composite
    supplémentaire n'est inventé.

    ### `/public`

    `GET /api/v1/public/indicators`

    Endpoint anonyme mais fermé par défaut. Il exige :
    1. une règle publiée `PUBLIC_DASHBOARD_INDICATORS` ;
    2. une allowlist d'indicateurs ;
    3. une période publiée ;
    4. une publication institutionnelle liée à la règle au statut `PUBLIEE`.

    Aucune donnée individuelle n'est exposée.

    ## Permissions

    ```text
    DASHBOARDS.LIRE_REFERENTIELS
    DASHBOARDS.OPERATIONNEL
    DASHBOARDS.TACTIQUE
    DASHBOARDS.STRATEGIQUE
    DASHBOARDS.ANNUEL
    BAROMETRE.LIRE
    ```

    Le catalogue actuel n'ayant pas de rôle `PRESIDENCE`, le stratégique et
    l'annuel sont attribués à `DIRECTION_TECHNIQUE` et à `ADMIN_HAUQE`.
    Un rôle institutionnel supplémentaire pourra être ajouté via le RBAC.

    ## Fichiers

    ```text
    app/schemas/dashboard.py
    app/repositories/dashboard_repository.py
    app/services/dashboard_service.py
    app/routes/api/v1/dashboards.py
    app/scripts/seed_dashboard_permissions.py

    ROUTER_INTEGRATION.md
    CONFIGURATION_TABLEAU_PUBLIC.md
    MAPPING_FRONTEND_ENDPOINTS.md
    TESTS_DASHBOARDS_FRONTEND.md
    INTERACTIONS_PILOTAGE.md
    ```

    ## État de recette

    ```text
    Syntaxe Python                  ✅
    Bundle                          ✅
    8 endpoints                     ✅
    Mapping frontend                ✅
    Permissions                     ✅ code
    Public agrégé sécurisé          ✅ code

    Seed permissions                ⏳
    Intégration dépôt               ⏳
    Tests runtime                   ⏳
    Raccordement frontend           ⏳
    Validation fonctionnelle        ⏳
    ```

    ## Suite

    ```text
    RACCORDEMENT FRONTEND / RECETTE PAGE PAR PAGE
    ```

    Ordre recommandé :
    1. Auth / shell / navigation / permissions
    2. Dashboard opérationnel
    3. Entreprises
    4. Organismes / Certifications / Documents
    5. Collecte
    6. Vérification
    7. FUCCS
    8. Validation / Intégration BNEC
    9. Scoring / INFC / SNCC
    10. Échéances / Alertes / Veille
    11. Gouvernance / Qualité / Continuité
    12. Tactique / Stratégique / Annuel / Baromètre / Public

# DOMAINE MON COMPTE / SÉCURITÉ UTILISATEUR AVANCÉE

## Statut

🟠 **Implémenté — non validé runtime**

Ce lot couvre `profil.html`, `connexion.html` et `mot-de-passe-oublie.html`
sur les fonctions compte/sécurité qui manquaient encore.

## Extension explicite du schéma

Nouvelles tables :

```text
preferences_utilisateur
securite_compte_utilisateur
verrous_session_utilisateur
jetons_securite_utilisateur
```

Le schéma métier passe de **66 à 70 tables**.

Migration :

```text
c5b7a8f2d901_account_security_extension.py
```

Chaîne Alembic :

```text
9f89b5d85b6a → c5b7a8f2d901
```

Cette extension devra être reportée dans le prochain cycle MCD/MLD/MPD.

## Avant test

```powershell
.\.venv\Scripts\python.exe -m pip install "cryptography>=42,<47"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m compileall app
```

Configuration requise :

```env
MFA_FERNET_KEY=...
PASSWORD_RESET_URL_TEMPLATE=https://.../#/mot-de-passe-oublie?token={token}
```

## Registre exhaustif des endpoints

```text
GET    /api/v1/me/profile
PATCH  /api/v1/me/profile
POST   /api/v1/me/password/change
POST   /api/v1/auth/password/forgot
POST   /api/v1/auth/password/reset
GET    /api/v1/me/sessions
POST   /api/v1/me/sessions/revoke-others
POST   /api/v1/me/sessions/{session_id}/revoke
GET    /api/v1/me/mfa
POST   /api/v1/me/mfa/enable
POST   /api/v1/me/mfa/verify
POST   /api/v1/me/mfa/disable
POST   /api/v1/auth/mfa/verify
GET    /api/v1/me/notification-preferences
PATCH  /api/v1/me/notification-preferences
GET    /api/v1/me/security-lock
PATCH  /api/v1/me/security-lock
POST   /api/v1/me/security-lock/lock
POST   /api/v1/me/security-lock/verify
```

Total du lot : **19 endpoints**.

## Profil / informations personnelles

```text
GET   /api/v1/me/profile
PATCH /api/v1/me/profile
```

Alimente le hero et l'onglet Informations personnelles.

Modifiable par l'utilisateur :
- prénom(s) ;
- nom ;
- téléphone ;
- langue ;
- fuseau horaire ;
- avatar.

Non modifiable depuis Mon compte :
- email professionnel ;
- fonction ;
- région ;
- statut ;
- rôles ;
- permissions.

## Mot de passe

```text
POST /api/v1/me/password/change
POST /api/v1/auth/password/forgot
POST /api/v1/auth/password/reset
```

Règles :
- Argon2 ;
- réponse forgot neutre ;
- token reset opaque, hash SHA-256 en base ;
- expiration 30 minutes ;
- usage unique ;
- reset → révocation de toutes les sessions ;
- changement depuis Mon compte → révocation des autres sessions ;
- notifications de sécurité + audit.

La politique institutionnelle peut être publiée via :

```text
ACCOUNT_PASSWORD_POLICY
```

En absence de règle publiée, seul un plancher technique minimal de 8
caractères est appliqué.

## MFA TOTP

```text
GET  /api/v1/me/mfa
POST /api/v1/me/mfa/enable
POST /api/v1/me/mfa/verify
POST /api/v1/me/mfa/disable
POST /api/v1/auth/mfa/verify
```

Technique :
- TOTP RFC 6238 ;
- secret chiffré avec Fernet ;
- 8 codes de récupération ;
- codes de récupération hashés Argon2 ;
- challenge de login MFA : 5 minutes.

### Hook obligatoire login

Après validation email/mot de passe et avant création de session :

```text
MfaService.post_password_authentication(...)
```

Si le MFA est actif, `/auth/login` ne doit pas créer de Bearer token avant
la validation du challenge MFA.

## Sessions

```text
GET  /api/v1/me/sessions
POST /api/v1/me/sessions/{session_id}/revoke
POST /api/v1/me/sessions/revoke-others
```

Un utilisateur ne peut agir que sur ses propres sessions.

## Préférences de notification

```text
GET   /api/v1/me/notification-preferences
PATCH /api/v1/me/notification-preferences
```

Préférences persistées :
- alertes critiques ;
- affectations ;
- corrections ;
- rapports planifiés ;
- résumé hebdomadaire.

Helper partagé :

```text
app/services/account_notification_policy.py
```

Résumé hebdomadaire :

```text
app/tasks/account_weekly_digest.py
```

## Verrouillage automatique / code privé

```text
GET   /api/v1/me/security-lock
PATCH /api/v1/me/security-lock
POST  /api/v1/me/security-lock/lock
POST  /api/v1/me/security-lock/verify
```

Règles :
- code privé ≥ 5 caractères ;
- délais 5 / 10 / 15 / 30 minutes ;
- hash Argon2 uniquement ;
- aucun code privé dans localStorage ;
- verrou par session ;
- 5 erreurs → révocation de la session.

Garde serveur :

```text
app/services/account_session_lock_guard.py
```

Session verrouillée :

```text
HTTP 423
SESSION_SCREEN_LOCKED
```

Routes exemptées :
- `/me/security-lock/verify`
- `/auth/logout`

## RM-33 — cycle d'inactivité

Tâche :

```text
app/tasks/account_inactivity_scan.py
```

Règles :
- préavis après 150 jours ;
- désactivation à 180 jours ;
- révocation des sessions ;
- aucune suppression du compte ;
- réactivation par l'endpoint admin existant.

Lors de `INACTIF → ACTIF`, le service admin doit renseigner :

```text
securite_compte_utilisateur.reactivation_at
```

pour éviter une redésactivation immédiate avant la prochaine connexion.

## Interactions

```text
utilisateurs
├── preferences_utilisateur
├── securite_compte_utilisateur
├── sessions_utilisateur
│      └── verrous_session_utilisateur
└── jetons_securite_utilisateur

documents
└── preferences_utilisateur.avatar_document_id

notifications
└── sécurité / reset / résumé hebdomadaire
```

## Fichiers livrés

```text
app/models/preference_utilisateur.py
app/models/securite_compte_utilisateur.py
app/models/verrou_session_utilisateur.py
app/models/jeton_securite_utilisateur.py

app/schemas/account.py
app/repositories/account_repository.py

app/services/account_service.py
app/services/password_service.py
app/services/mfa_service.py
app/services/account_inactivity_service.py
app/services/account_notification_policy.py
app/services/account_session_lock_guard.py

app/utils/account_security.py
app/routes/api/v1/account.py

app/tasks/account_inactivity_scan.py
app/tasks/account_weekly_digest.py

alembic/versions/c5b7a8f2d901_account_security_extension.py
```

## Documentation du lot

```text
ROUTER_INTEGRATION.md
MODELS_AND_MIGRATION_INTEGRATION.md
SETTINGS_AND_DEPENDENCIES.md
AUTH_LOGIN_MFA_INTEGRATION.md
AUTH_SESSION_LOCK_GUARD_INTEGRATION.md
USER_REACTIVATION_RM33_INTEGRATION.md
MAPPING_FRONTEND_ENDPOINTS.md
DICTIONNAIRE_EXTENSION_MON_COMPTE.md
TESTS_MON_COMPTE_SECURITE.md
```

## État de recette

```text
4 nouvelles tables                   ✅ code/migration
19 endpoints                         ✅ code
Profil                               ✅ code
Préférences                          ✅ code
Sessions                             ✅ code
Mot de passe                         ✅ code
Forgot/reset                         ✅ code
MFA TOTP                             ✅ code
Code privé / verrou session          ✅ code
RM-33                                ✅ code
Résumé hebdomadaire                  ✅ code
Audit                                ✅ code
Syntaxe Python                       ✅

cryptography environnement           ⏳
MFA_FERNET_KEY                       ⏳
migration Alembic appliquée          ⏳
hook MFA dans login                  ⏳ intégration
guard lock dans get_current_auth     ⏳ intégration
hook réactivation admin              ⏳ intégration
tests runtime                        ⏳
raccordement profil.html             ⏳
raccordement connexion.html          ⏳
raccordement mot-de-passe-oublie     ⏳
validation fonctionnelle             ⏳
```

## Suite

Après application de la migration et intégration des trois hooks de sécurité :

```text
RACCORDEMENT FRONTEND / RECETTE PAGE PAR PAGE
```

# CHECK-UP FINAL AVANT RACCORDEMENT API ↔ FRONTEND

## Résultat du check-up

**Décision : GO pour le raccordement API ↔ frontend, avec recette verticale page par page.**

Le check-up confirme :

```text
Socle Auth / RBAC                     ✅
Entreprises                            ✅ backend
Organismes / Certifications / Docs    ✅ backend
Collecte                               ✅ backend
Vérification                           ✅ backend
FUCCS                                  ✅ backend
Validation / Intégration BNEC         ✅ backend
Scoring / Classification / INFC / SNCC✅ backend
Échéances / Alertes / Veille          ✅ backend
Gouvernance / Qualité / Continuité    ✅ backend
Pilotage / Dashboards / Baromètre     ✅ backend
Mon compte / Sécurité                  ✅ code
Verrou session dans auth               ✅ intégré par l'utilisateur
Interaction verrou / idle timeout      ✅ ajustée

Runtime global de tous les lots        ⏳ recette au raccordement
MFA dans login                         ⏳ à confirmer pendant Sprint 1
Réactivation RM-33                     ⏳ à confirmer pendant Sprint 1/2
SMTP EMAIL                             ⏸ différé — non bloquant
```

### Point SMTP

Pour la phase de raccordement actuelle :

```text
IN_APP       → actif / à tester
EMAIL        → file EN_ATTENTE
SMTP réel    → différé volontairement
```

L'absence de SMTP ne doit pas bloquer la recette des écrans. Les tests d'envoi e-mail seront isolés dans une phase infrastructure ultérieure.

## Préflight obligatoire avant le premier écran

Ne commencer le frontend qu'après avoir vérifié dans le dépôt réel :

1. tous les routers des lots sont inclus dans `app/routes/api/v1/router.py` ;
2. les quatre modèles Mon compte sont importés par SQLAlchemy/Alembic si le projet utilise des imports explicites ;
3. migration `c5b7a8f2d901` appliquée ;
4. `python -m compileall app` sans erreur ;
5. `alembic current` sur la révision attendue ;
6. seeds nécessaires exécutés : Veille/Notifications, Gouvernance, Pilotage ;
7. Collecte et Veille utilisent `business_rule_resolver.py` ;
8. `get_current_auth()` contient le garde `ensure_session_not_screen_locked(...)` avec `db_session` ;
9. `AUTH_IDLE_TIMEOUT_MINUTES` est cohérent avec le verrou utilisateur 5/10/15/30 minutes ;
10. l'absence de SMTP est acceptée comme dette d'infrastructure non bloquante.

## Plan directeur de raccordement API ↔ frontend

### Principe de travail

**Une tranche verticale à la fois : page → API → permissions → erreurs → audit → validation.**

On ne raccorde pas 20 pages avant de tester. Une page devient la référence stable avant de passer à la suivante.

### SPRINT 0 — Socle d'intégration frontend

Objectif : construire une seule couche API commune utilisée par toutes les pages.

À finaliser dans `app/static/js/core/api.js` :

```text
apiRequest()
├── base URL /api/v1
├── Authorization: Bearer
├── JSON request/response
├── 401 → déconnexion / connexion
├── 403 → accès refusé
├── 409 → conflit métier
├── 422 → erreurs de formulaire
├── 423 → écran de verrouillage
├── 5xx → erreur serveur générique
└── timeout / réseau
```

Ajouter également :
- helper `getCurrentUser()` ;
- helper permissions ;
- loader commun ;
- toast/erreurs communs ;
- protection contre double soumission ;
- aucune donnée métier sensible comme source d'autorité dans `localStorage`.

### SPRINT 1 — Authentification / shell / sécurité de session

Pages :

```text
connexion.html
mot-de-passe-oublie.html
shell principal / navbar / sidebar
écran global de verrouillage
```

Endpoints prioritaires :

```text
POST /api/v1/auth/login
POST /api/v1/auth/mfa/verify
POST /api/v1/auth/logout
GET  /api/v1/me
POST /api/v1/auth/password/forgot
POST /api/v1/auth/password/reset
GET  /api/v1/me/security-lock
POST /api/v1/me/security-lock/lock
POST /api/v1/me/security-lock/verify
```

Critères de sortie Sprint 1 :
- login réel ;
- MFA non contournable si activé ;
- logout réel ;
- 401/403/423 gérés globalement ;
- verrou écran réel ;
- reprise par code privé ;
- timeout serveur distinct du verrou écran ;
- mot de passe oublié fonctionnel hors envoi SMTP réel si SMTP différé.

### SPRINT 2 — `profil.html` / Mon compte

Endpoints :

```text
GET/PATCH /api/v1/me/profile
POST      /api/v1/me/password/change
GET/POST  /api/v1/me/mfa...
GET/PATCH /api/v1/me/notification-preferences
GET/POST  /api/v1/me/sessions...
```

Remplacer toutes les valeurs simulées et tout stockage local du code privé.

### SPRINT 3 — Dashboard opérationnel `index.html`

```text
GET /api/v1/dashboards/operational
GET /api/v1/dashboards/filters
GET /api/v1/dashboards/indicator-definitions
```

Objectif : première page métier entièrement alimentée par PostgreSQL.

### SPRINT 4 — Entreprises

Ordre :

```text
entreprises.html
→ entreprise-detail.html
→ entreprise-form.html
→ contacts / sites / offres / doublons
```

### SPRINT 5 — Organismes / Certifications / Documents

Ordre :

```text
organismes.html
organisme-detail.html
organisme-form.html
certifications.html
certification-detail.html
certification-form.html
documents privés
```

### SPRINT 6 — Collecte

```text
collectes.html
collecte-form.html
campagnes / missions / affectations
offres déclarées
certifications déclarées
historique collecte
```

Rappel : **aucun snapshot composite** ; l'ancien patch reste abandonné.

### SPRINT 7 — Vérification

Raccorder la page de vérification distincte de la validation institutionnelle :
- dossiers ;
- affectations ;
- points ;
- anomalies ;
- confirmations externes.

### SPRINT 8 — FUCCS

`controle.html` : grille versionnée dynamique, aucun `24/28/48/56` structurel codé en dur.

### SPRINT 9 — Validation / Intégration BNEC

Séparer explicitement :

```text
validation institutionnelle
≠
intégration technique BNEC
```

### SPRINT 10 — Classification / INFC / SNCC

Raccorder séparément les trois résultats. Aucun calcul frontend souverain.

### SPRINT 11 — Échéances / Alertes / Notifications / Veille

Pages :

```text
echeances.html
alertes.html
cloche notifications
#/veille
```

SMTP reste hors critère de blocage ; IN_APP est la priorité de recette.

### SPRINT 12 — Gouvernance / Qualité / Continuité

```text
règles métier
qualité / plans d'action
décisions
publications
rapports
audit
archives
sauvegardes
incidents
```

### SPRINT 13 — Pilotage avancé / public

```text
tactique
stratégique
annuel
baromètre
public agrégé autorisé
```

Le public reste fermé tant que la règle + publication institutionnelle ne sont pas présentes.

## Définition de « page raccordée et validée »

Une page n'est déclarée raccordée que si les 10 points suivants sont vrais :

1. aucune donnée principale ne vient des mocks ;
2. aucun calcul métier souverain n'est dupliqué en JavaScript ;
3. chargement initial API réussi ;
4. actions CRUD/workflow réelles réussies ;
5. permissions testées au moins avec un rôle autorisé et un rôle refusé ;
6. états vides et chargement gérés ;
7. erreurs 401/403/409/422/423/5xx gérées ;
8. audit serveur vérifié pour les actions sensibles ;
9. responsive/ergonomie conservés ;
10. feuille backend + feuille frontend mises à jour avant de passer à la page suivante.

## Prochaine étape exacte

**Commencer par SPRINT 0 puis SPRINT 1.**

Premier travail de raccordement :

```text
app/static/js/core/api.js
+ connexion.html / connexion.js
+ gestion globale 401 / 403 / 423
+ /auth/login
+ /me
+ /auth/logout
+ MFA challenge si actif
```

## ÉTAPE 04 — CERTIFICATIONS

Statut : 🟡 projection registre ajoutée, recette runtime à confirmer.

Le CRUD métier Certifications existant n'a pas été remplacé.

Un sous-module de lecture/export a été ajouté afin de fournir au frontend
un registre joint et crédible sans multiplier les appels par ligne :

```text
GET /api/v1/certifications/filters
GET /api/v1/certifications/registry
GET /api/v1/certifications/{id}/context
GET /api/v1/certifications/export
GET /api/v1/certifications/{id}/export
```

Les opérations CRUD existantes restent souveraines :

```text
GET/POST/PATCH /api/v1/certifications...
/verification
/status
/history
/audits
/renewals
/couvertures
```

Permission ajoutée :

```text
CERTIFICATIONS.EXPORTER
```

Aucune migration et aucune nouvelle table.

## Correctif Étape 04 — 422 sur `/certifications/filters` et `/registry`

Symptômes :

```text
GET /api/v1/certifications/filters  -> 422
GET /api/v1/certifications/registry -> 422
```

Diagnostic :
les requêtes n'atteignaient pas la projection registre. FastAPI les faisait
correspondre à la route historique :

```text
GET /certifications/{certification_id}
```

et tentait donc de convertir `filters` ou `registry` en UUID, d'où le 422.

Correctif architectural :
les routes statiques du registre sont désormais déclarées directement dans
`organismes_certifications.py`, avant la route dynamique `{certification_id}`.

Ordre contrôlé :

```text
/certifications/filters
/certifications/registry
/certifications/export
/certifications/{uuid}/context
/certifications/{uuid}/export
/certifications
/certifications/{uuid}
...
```

Le router séparé `certification_registry_router` n'est plus inclus dans
`router.py`. Il n'y a donc plus deux routeurs concurrents pour le même préfixe.

Aucun changement frontend, repository, service, schéma ou base de données
n'est nécessaire pour ce correctif.

## ÉTAPE 05 — CAMPAGNES → MISSIONS → COLLECTE

Statut : 🟡 **raccordement produit — recette runtime utilisateur à faire**

Le backend métier déjà développé reste souverain pour toutes les écritures :

```text
/campagnes
/campagnes/{id}/missions
/missions
/missions/{id}/affectations
/missions/{id}/fiches
/missions/{id}/fiches/{fiche_id}
/offres
/certifications
/submit
/revision
/history
/documents
```

Aucune route d'écriture métier n'a été dupliquée.

Ajout uniquement d'une projection de lecture destinée à l'écran central :

```text
GET /api/v1/collectes/filters
GET /api/v1/collectes/registry
```

Cette projection joint :
- campagne ;
- mission ;
- zone administrative ;
- affectations actives ;
- révision courante de la fiche ;
- entreprise liée ;
- statut et taux de complétude.

La liste des agents proposée au coordonnateur n'est pas basée sur un rôle
codé en dur : elle expose les utilisateurs actifs possédant réellement
`COLLECTE.CREER` ou `COLLECTE.MODIFIER`.

Aucune migration Alembic.
Aucune nouvelle table.
Aucune nouvelle permission.


## ÉTAPE 06 — VÉRIFICATION DOCUMENTAIRE
Statut : 🟡 raccordement produit — recette runtime à confirmer.

Le backend Vérification existant reste souverain pour ouverture, affectations,
points, anomalies, confirmations externes, clôture/réouverture et audit.

Extensions de lecture :
- GET `/api/v1/verifications/filters`
- GET `/api/v1/verifications/registry`
- GET `/api/v1/verifications/eligible-fiches`
- GET `/api/v1/verifications/{dossier_id}/context`

Aucune migration, nouvelle table ou nouvelle permission.
`DOCUMENTS.VERIFIER` reste distinct de `VERIFICATION.VERIFIER`.

## ÉTAPE 07 — CONTRÔLE FUCCS

Statut : 🟡 **raccordement produit — recette runtime à confirmer**

Le moteur FUCCS existant n'est pas remplacé.

Conservés comme autorités métier :
- versions de grille ;
- rubriques et critères ;
- grille active publiée ;
- création du contrôle depuis un dossier de vérification clôturé ;
- notation des critères ;
- commentaires/preuves obligatoires ;
- recalcul score brut / score maximal / taux ;
- constats ;
- finalisation ;
- réouverture ;
- audit.

Ajout uniquement d'une projection de lecture :

```text
GET /api/v1/fuccs/workspace/filters
GET /api/v1/fuccs/workspace/registry
GET /api/v1/fuccs/workspace/eligible-verifications
GET /api/v1/fuccs/controles/{control_id}/context
```

Point important :
le frontend ne code plus en dur 28 critères, 24 critères, 7 domaines
ou un score maximal de 56. Il affiche exactement la grille publiée en base.
Ainsi une future mise à jour officielle de la grille ne nécessite pas
de réécrire l'écran de contrôle.

Aucune nouvelle table.
Aucune migration.
Aucune nouvelle permission.

## Mise à jour sécurité du compte — MFA TOTP (31/07/2026)

- `MFA_FERNET_KEY` est maintenant déclarée dans `app.config.settings` ;
- le service refuse explicitement une clé absente ou non conforme ;
- une clé Fernet URL-safe de 44 caractères est obligatoire dans chaque
  fichier `.env` d’exécution ;
- la clé ne doit jamais être versionnée, affichée dans les journaux ou placée
  dans l’historique du terminal ;
- la même clé doit être conservée lors d’une restauration de base contenant
  des comptes MFA actifs ;
- la procédure Windows → Linux, les permissions `root:sngsc` et les contrôles
  sans divulgation sont documentés dans
  `FEUILLE_DE_ROUTE_HEBERGEMENT_SNGSC.md`, section D.2.1 ;
- chiffrement/déchiffrement Fernet, TOTP, URI d’enrôlement et codes de
  récupération contrôlés avec succès.

## Correction du parcours « Mot de passe oublié » (31/07/2026)

- `PASSWORD_RESET_URL_TEMPLATE` est désormais déclaré dans les settings
  Python et chargé depuis `.env` ;
- `POST /api/v1/auth/password/forgot` crée un jeton à usage unique valable
  30 minutes et met le courriel en file sans révéler si le compte existe ;
- `POST /api/v1/auth/password/reset` applique le nouveau mot de passe et
  révoque les anciennes sessions ;
- le modèle d’URL doit contenir `{token}` ;
- SMTP et modèle d’URL détectés dans l’environnement Windows ;
- avant correction, aucun jeton `PASSWORD_RESET` n’avait été créé, confirmant
  que l’ancien formulaire n’appelait pas l’API.

## ÉTAPE 08 — VALIDATION + CORRECTIONS

Statut : 🟡 **raccordement produit — recette runtime à confirmer**

Le domaine métier existant reste souverain :
- `ValidationBnecService`;
- revue NIVEAU_1;
- validation NIVEAU_2;
- décisions historisées;
- corrections;
- resoumissions.

Aucune route d'écriture métier n'est remplacée.

Projection de lecture ajoutée :

```text
GET /api/v1/validations/workspace/filters
GET /api/v1/validations/workspace/registry
GET /api/v1/validations/workspace/{fiche_id}
```

Règles backend conservées :
- contrôle FUCCS finalisé obligatoire;
- N1 favorable avant N2;
- séparation de personne entre N1 et N2;
- réserves obligatoires pour `VALIDE_SOUS_RESERVE`;
- correction autorisée uniquement pour `AJOURNE` ou
  `VALIDE_SOUS_RESERVE`;
- une correction AJOURNE en attente doit être resoumise avant une
  nouvelle décision du même niveau;
- seule une N2 favorable ouvre l'étape d'intégration BNEC.

Aucune table, migration ou permission nouvelle.

## ÉTAPE 09 — INTÉGRATION BNEC

Statut : 🟡 **raccordement produit — recette runtime à confirmer**

Le moteur métier historique reste souverain pour ouverture, précontrôle, démarrage, éléments, résultats, postcontrôle et clôture.

Projection de lecture ajoutée :

```text
GET /api/v1/integrations-bnec/workspace/filters
GET /api/v1/integrations-bnec/workspace/registry
GET /api/v1/integrations-bnec/workspace/queue
GET /api/v1/integrations-bnec/workspace/{integration_id}
```

Règles conservées : N2 favorable terminée ; une intégration active par validation ; précontrôle OK avant démarrage ; au moins un élément ; tous les éléments intégrés avant postcontrôle OK ; sauvegarde + postcontrôle OK avant clôture. Un échec reste historisé et permet une nouvelle tentative.

Aucune table, migration ou permission nouvelle.

## ÉTAPE 10 — SCORING / CLASSIFICATION ENTREPRISE / INFC / SNCC

Statut : 🟡 **raccordement produit — recette runtime à confirmer**

Le moteur existant de scoring reste souverain : modèles versionnés, pondérations, prévisualisation, classification entreprise, calcul/validation INFC et classement/reclassement/clôture SNCC.

Ajout d'un read model relationnel sous `/api/v1/scoring/workspace/*` pour enrichir les résultats avec entreprise, certification, organisme, norme, modèle et validateur.

Aucune conversion automatique FUCCS → Classification, FUCCS → INFC, Classification → INFC ou INFC → SNCC.

Aucune table, migration ou permission nouvelle.

## ÉTAPE 11 — ÉCHÉANCES / ALERTES / NOTIFICATIONS / VEILLE

Statut : 🟡 **raccordement produit — recette runtime à confirmer**

Le domaine backend historique reste souverain. Aucune logique métier
d'écriture existante n'est remplacée.

### Échéances

```text
GET   /api/v1/echeances
POST  /api/v1/echeances
GET   /api/v1/echeances/{deadline_id}
PATCH /api/v1/echeances/{deadline_id}
POST  /api/v1/echeances/{deadline_id}/complete
POST  /api/v1/echeances/{deadline_id}/cancel
GET   /api/v1/echeances/{deadline_id}/alertes
```

### Alertes

```text
GET   /api/v1/alertes
POST  /api/v1/alertes
GET   /api/v1/alertes/{alert_id}
PATCH /api/v1/alertes/{alert_id}
POST  /api/v1/alertes/{alert_id}/assign
POST  /api/v1/alertes/{alert_id}/resolve
POST  /api/v1/alertes/{alert_id}/notifications
```

### Notifications

```text
GET  /api/v1/notifications
GET  /api/v1/notifications/unread-count
POST /api/v1/notifications/read-all
POST /api/v1/notifications/{notification_id}/read
POST /api/v1/notifications/{notification_id}/retry
POST /api/v1/notifications/{notification_id}/delivery-result
```

### Veille CVC

```text
GET  /api/v1/veille/dashboard
POST /api/v1/veille/scans/daily

GET/POST       /api/v1/veille/dossiers
GET/PATCH      /api/v1/veille/dossiers/{case_id}
POST           /api/v1/veille/dossiers/{case_id}/close
GET/POST       /api/v1/veille/dossiers/{case_id}/relances
PATCH          /api/v1/veille/dossiers/{case_id}/relances/{followup_id}
POST           /api/v1/veille/dossiers/{case_id}/relances/{followup_id}/response

GET            /api/v1/veille/rapports
POST           /api/v1/veille/rapports/generate
GET            /api/v1/veille/rapports/{report_id}
POST           /api/v1/veille/rapports/{report_id}/validate
```

### Read model ajouté

```text
GET /api/v1/veille/workspace/deadline-filters
GET /api/v1/veille/workspace/alert-filters
GET /api/v1/veille/workspace/filters
GET /api/v1/veille/workspace/deadline-options
GET /api/v1/veille/workspace/alert-options
GET /api/v1/veille/workspace/watch-options
GET /api/v1/veille/workspace/deadlines
GET /api/v1/veille/workspace/alerts
GET /api/v1/veille/workspace/cases
GET /api/v1/veille/workspace/reports
```

Le read model enrichit les UUID avec les informations nécessaires aux vues :
entreprise, certification, norme, organisme, responsable et route de navigation
vers la ressource source.

### Seuils de veille

Le moteur existant conserve :

```text
180 jours → niveau 1 / Information
90 jours  → niveau 2 / Surveillance
30 jours  → niveau 3 / Urgence
0 ou dépassé → niveau 4 / Critique
```

Le service tente d'abord de résoudre la règle publiée
`VEILLE_SEUILS_EXPIRATION`. Le socle ci-dessus reste le fallback technique
déjà présent dans le backend.

Aucune migration.
Aucune nouvelle permission.
