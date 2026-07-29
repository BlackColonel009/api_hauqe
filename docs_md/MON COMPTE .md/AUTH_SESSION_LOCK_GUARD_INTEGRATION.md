# Intégration obligatoire du verrou de reprise dans `get_current_auth`

Le verrouillage de session ne doit pas être seulement visuel.

Dans `app/permissions/auth.py`, une fois la session courante résolue et
validée, mais **avant d'autoriser la route métier**, appeler :

```python
from app.services.account_session_lock_guard import (
    ensure_session_not_screen_locked,
)

await ensure_session_not_screen_locked(
    db,
    session=session,
    request=request,
)
```

Routes exemptées par le garde :

```text
POST /api/v1/me/security-lock/verify
POST /api/v1/auth/logout
```

Comportement :

```text
session non verrouillée
    → requête normale

session verrouillée
    → HTTP 423 SESSION_SCREEN_LOCKED

POST /me/security-lock/verify + bon code
    → déverrouillage

5 codes erronés
    → session révoquée
    → HTTP 401
```

## Ordre conseillé dans `get_current_auth`

```text
Bearer token
→ hash SHA-256
→ session existe ?
→ session révoquée ?
→ expiration absolue ?
→ compte ACTIF ?
→ verrou de reprise ?
→ timeout d'inactivité serveur ?
→ rôles / permissions
→ requête autorisée
```

Le timeout serveur de 30 minutes et le verrou d'écran personnel 5/10/15/30
minutes restent deux mécanismes distincts.
