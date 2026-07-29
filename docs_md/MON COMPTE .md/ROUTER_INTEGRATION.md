# Intégration des routes Mon compte

Dans `app/routes/api/v1/router.py` :

```python
from app.routes.api.v1.account import (
    account_router,
    account_auth_router,
)

api_router.include_router(account_router)
api_router.include_router(account_auth_router)
```

Les routes finales seront donc sous le préfixe global `/api/v1`.

## Important

Ce lot ne crée **aucune permission RBAC supplémentaire** pour `/me/*`.

Un utilisateur authentifié doit pouvoir :
- consulter son propre profil ;
- modifier les champs personnels autorisés ;
- gérer son mot de passe ;
- gérer son MFA ;
- consulter/révoquer ses propres sessions ;
- gérer ses préférences ;
- gérer son propre verrou de reprise.

Les contrôles portent sur l'identité de la session, pas sur une permission
administrative.

## Routes publiques ajoutées

```text
POST /api/v1/auth/password/forgot
POST /api/v1/auth/password/reset
POST /api/v1/auth/mfa/verify
```

`/auth/mfa/verify` est la seconde étape du login MFA et n'accepte qu'un
challenge opaque temporaire.
