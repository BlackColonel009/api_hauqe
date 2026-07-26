# Intégration des routers Veille

Dans `app/routes/api/v1/router.py` :

```python
from app.routes.api.v1.veille import (
    deadline_router,
    alert_router,
    notification_router,
    watch_router,
)

api_router.include_router(deadline_router)
api_router.include_router(alert_router)
api_router.include_router(notification_router)
api_router.include_router(watch_router)
```

Aucune migration Alembic n'est requise.
