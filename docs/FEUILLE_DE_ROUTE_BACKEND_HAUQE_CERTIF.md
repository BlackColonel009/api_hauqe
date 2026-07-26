# FEUILLE DE ROUTE BACKEND — HAUQE CERTIF

**Projet :** HAUQE Certif / BNEC  
**Backend :** FastAPI + PostgreSQL + SQLAlchemy 2 async + Psycopg 3 + Alembic  
**Dernière mise à jour :** 2026-07-25  
**Statut global :** Socle base de données et sécurité opérationnels — RBAC utilisateur fonctionnel — prochaine étape : matrice rôle → permissions puis premier vertical métier Entreprises.

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

Référence validée :

- **66 tables métier**
- **843 colonnes**
- **107 clés étrangères**
- **9 contraintes UNIQUE**
- **66 clés primaires**
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
🟡 EN COURS

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
