# Intégration RM-33 avec la réactivation administrateur

Le scan quotidien désactive automatiquement un compte après 180 jours
d'inactivité.

L'endpoint administratif existant :

```text
PATCH /api/v1/users/{user_id}/status
```

reste l'autorité pour réactiver le compte.

Lors d'une transition :

```text
INACTIF → ACTIF
```

ajouter :

```python
from datetime import datetime, timezone
from app.repositories.account_repository import AccountRepository

security = await AccountRepository.get_or_create_security(
    db,
    user.id,
)
security.reactivation_at = datetime.now(timezone.utc)
security.inactivite_warning_sent_at = None
```

Pourquoi `reactivation_at` :
sans cette date de grâce, le scan quotidien verrait toujours l'ancienne
dernière connexion (>180 jours) et pourrait redésactiver immédiatement le
compte avant que l'utilisateur ait le temps de se reconnecter.

Une première connexion après réactivation reprend ensuite naturellement
comme nouvelle activité.
