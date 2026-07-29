# Tests — Mon compte / Sécurité

Statut du lot : **implémenté / non validé runtime**.

## Installation

```powershell
.\.venv\Scripts\python.exe -m pip install "cryptography>=42,<47"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m compileall app
```

Configurer `MFA_FERNET_KEY` et `PASSWORD_RESET_URL_TEMPLATE`.

## Profil

- GET `/me/profile`
- modifier prénom/téléphone/langue/fuseau
- vérifier email/fonction/rôles non modifiables
- avatar image valide
- avatar PDF -> 422

## Mot de passe

- mot actuel faux -> 401
- confirmation différente -> 422
- nouveau identique -> 422
- changement valide -> autres sessions révoquées
- notification IN_APP + EMAIL
- audit

## Forgot / reset

- email existant -> réponse neutre
- email inexistant -> même réponse
- token hashé uniquement en DB
- token expire à 30 min
- token réutilisé -> refus
- reset -> toutes sessions révoquées

## MFA

- enable sans `MFA_FERNET_KEY` -> 503
- enable -> secret + URI uniquement à l'enrôlement
- mauvais premier code -> 401
- bon code -> MFA actif + 8 recovery codes
- désactivation avec mauvais mot de passe -> 401
- désactivation avec TOTP/recovery valide
- login compte MFA : `/auth/login` ne doit PAS créer de session
- `/auth/mfa/verify` -> Bearer token final
- recovery code utilisé supprimé de la liste

## Sessions

- GET liste
- une session d'un autre utilisateur ne peut être révoquée
- revoke une session
- revoke-others conserve la courante

## Verrouillage

- activation sans code -> 422
- code < 5 -> 422
- délai hors 5/10/15/30 -> 422
- lock manuel -> état verrouillé
- route métier pendant lock -> 423 après intégration du guard
- bon code -> unlock
- 5 erreurs -> session révoquée

## Préférences

- defaults conformes à `profil.js`
- PATCH individuel
- helper `user_wants_notification()`
- résumé hebdomadaire seulement si preference true

## RM-33

Créer des utilisateurs de dates contrôlées :
- 149 jours -> rien
- 150 jours -> préavis
- second scan -> pas de double préavis
- 180 jours -> statut INACTIF + sessions révoquées
- réactivation admin -> `reactivation_at`
- le scan suivant ne doit pas redésactiver immédiatement

## Alembic

```powershell
.\.venv\Scripts\python.exe -m alembic current
```

Attendu :

```text
c5b7a8f2d901 (head)
```

Puis :

```powershell
.\.venv\Scripts\python.exe -m alembic check
```

Attendu après intégration correcte des modèles :

```text
No new upgrade operations detected.
```
