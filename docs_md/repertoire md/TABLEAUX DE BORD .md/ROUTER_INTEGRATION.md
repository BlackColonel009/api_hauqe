# Intégration du router Pilotage

Dans `app/routes/api/v1/router.py` :

```python
from app.routes.api.v1.dashboards import (
    dashboard_router,
    barometer_router,
    public_dashboard_router,
)

api_router.include_router(dashboard_router)
api_router.include_router(barometer_router)
api_router.include_router(public_dashboard_router)
```

Puis exécuter :

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_dashboard_permissions
```

Aucune migration Alembic n'est requise.
