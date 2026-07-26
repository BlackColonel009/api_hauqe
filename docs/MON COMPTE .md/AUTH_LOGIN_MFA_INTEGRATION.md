# Intégration obligatoire avec l'authentification existante

Ce fichier décrit deux hooks indispensables.

---

## 1. MFA après mot de passe

L'actuel `POST /api/v1/auth/login` valide déjà :
- email ;
- mot de passe Argon2 ;
- statut ACTIF ;
- anti-bruteforce.

**Juste après ces validations et AVANT la création de
`sessions_utilisateur`**, appeler :

```python
from app.services.mfa_service import MfaService

mfa_challenge = await MfaService.post_password_authentication(
    db,
    user=user,
    request=request,
)

if mfa_challenge is not None:
    return mfa_challenge
```

Dans ce cas, le login renvoie par exemple :

```json
{
  "mfa_required": true,
  "challenge_token": "...",
  "expires_at": "..."
}
```

et **aucun Bearer token définitif n'est encore créé**.

Le frontend envoie ensuite :

```text
POST /api/v1/auth/mfa/verify
```

avec le challenge + le code TOTP ou un code de récupération.

Cette seconde route crée alors la vraie session opaque.

### Response model de `/auth/login`

Le schéma de réponse doit accepter :
- la réponse login existante ;
- ou `MfaChallengeResponse`.

Exemple FastAPI/Pydantic :

```python
response_model=LoginResponse | MfaChallengeResponse
```

Ne jamais laisser l'ancien `/auth/login` créer une session lorsque
`utilisateurs.mfa_active == true`, sinon le MFA serait contournable.

---

## 2. Connexion réussie et RM-33

Sur toute connexion réussie sans MFA, après création de la session :

```python
security = await AccountRepository.get_or_create_security(
    db,
    user.id,
)
security.inactivite_warning_sent_at = None
```

`user.derniere_connexion_at` doit continuer à être mis à jour comme
actuellement.

Pour une connexion MFA, cette remise à zéro est déjà faite par
`MfaService.verify_login_challenge()`.
