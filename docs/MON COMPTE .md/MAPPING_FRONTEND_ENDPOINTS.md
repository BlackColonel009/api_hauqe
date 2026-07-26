# Mapping frontend ↔ API — Mon compte

La page inspectée contient quatre onglets :
- Informations personnelles
- Sécurité
- Notifications
- Sessions et connexions

Elle contient aussi le verrouillage local `hauqe-session-lock-settings` qui
doit disparaître : le code privé ne doit plus être stocké dans localStorage.

---

## `profil.html` — en-tête / informations personnelles

```text
GET /api/v1/me/profile
```

Alimente :
- prénom ;
- nom ;
- email professionnel ;
- téléphone ;
- fonction ;
- statut ;
- dernière connexion ;
- date de création ;
- MFA actif ;
- langue ;
- fuseau horaire ;
- avatar ;
- rôles / permissions pour affichage informatif.

```text
PATCH /api/v1/me/profile
```

Modifiable par l'utilisateur :
- prénom(s) ;
- nom ;
- téléphone ;
- langue ;
- fuseau ;
- avatar_document_id.

Non modifiable depuis Mon compte :
- email professionnel ;
- fonction ;
- région d'affectation ;
- statut ;
- rôles ;
- permissions.

### Avatar

1. uploader l'image via le module Documents privé ;
2. récupérer `document_id` ;
3. envoyer cet UUID dans `PATCH /me/profile`.

---

## Onglet Sécurité — mot de passe

```text
POST /api/v1/me/password/change
```

Formulaire :
- mot de passe actuel ;
- nouveau mot de passe ;
- confirmation.

Après succès :
- hash Argon2 remplacé ;
- autres sessions révoquées ;
- notification de sécurité ;
- audit.

---

## Onglet Sécurité — MFA

```text
GET  /api/v1/me/mfa
POST /api/v1/me/mfa/enable
POST /api/v1/me/mfa/verify
POST /api/v1/me/mfa/disable
```

Activation frontend :
1. `enable` ;
2. afficher QR à partir de `otpauth_uri` ou clé manuelle ;
3. saisir code 6 chiffres ;
4. `verify` ;
5. afficher les codes de récupération une seule fois.

Connexion lorsque MFA actif :
1. `POST /auth/login` ;
2. si `mfa_required=true`, afficher étape code MFA ;
3. `POST /auth/mfa/verify` ;
4. stocker le Bearer token final.

---

## Onglet Sécurité — verrouillage automatique

```text
GET   /api/v1/me/security-lock
PATCH /api/v1/me/security-lock
POST  /api/v1/me/security-lock/lock
POST  /api/v1/me/security-lock/verify
```

Valeurs exactes du select frontend :

```text
5 minutes
10 minutes
15 minutes
30 minutes
```

Code privé :
- minimum 5 caractères ;
- jamais stocké dans localStorage ;
- jamais renvoyé par l'API ;
- hash Argon2 uniquement.

### Remplacement de `session-lock.js`

Le timer peut rester côté navigateur pour détecter l'inactivité UI.

À expiration :

```text
POST /me/security-lock/lock
```

Puis afficher l'écran bloquant.

Pour déverrouiller :

```text
POST /me/security-lock/verify
```

Après cinq erreurs, l'API révoque la session.

Le frontend doit traiter :

```text
HTTP 423 + code SESSION_SCREEN_LOCKED
```

en ouvrant immédiatement l'écran global de déverrouillage.

---

## Onglet Notifications

```text
GET   /api/v1/me/notification-preferences
PATCH /api/v1/me/notification-preferences
```

Correspondance exacte avec la maquette :

```text
Alertes critiques       → alertes_critiques
Affectations             → affectations
Corrections              → corrections
Rapports planifiés       → rapports_planifies
Résumé hebdomadaire      → resume_hebdomadaire
```

Le helper serveur :

```text
app/services/account_notification_policy.py
```

doit être utilisé par les domaines qui génèrent ces événements.

Les notifications de sécurité du compte ne sont jamais désactivées par ces
préférences.

---

## Onglet Sessions et connexions

```text
GET  /api/v1/me/sessions
POST /api/v1/me/sessions/{session_id}/revoke
POST /api/v1/me/sessions/revoke-others
```

Chaque ligne reçoit :
- appareil / user-agent ;
- IP ;
- début ;
- dernière activité ;
- expiration ;
- révocation ;
- session actuelle ;
- état verrouillé.

Le bouton de la session actuelle peut afficher `Actuelle`.
Les autres lignes utilisent `Déconnecter`.

---

## `mot-de-passe-oublie.html`

```text
POST /api/v1/auth/password/forgot
```

Le message frontend reste neutre, même si le compte n'existe pas.

Expiration :

```text
30 minutes
usage unique
```

Le lien reçu doit ouvrir le même écran en mode nouveau mot de passe ou une
route frontend dédiée, puis appeler :

```text
POST /api/v1/auth/password/reset
```

---

## Tâches serveur

Quotidien :

```text
python -m app.tasks.account_inactivity_scan
```

Hebdomadaire, lundi :

```text
python -m app.tasks.account_weekly_digest
```

Le premier couvre RM-33.
Le second matérialise la préférence « Résumé hebdomadaire ».
