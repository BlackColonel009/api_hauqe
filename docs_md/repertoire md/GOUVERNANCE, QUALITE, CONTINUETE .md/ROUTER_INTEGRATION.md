# Intégration du router Gouvernance

Dans `app/routes/api/v1/router.py` :

```python
from app.routes.api.v1.governance import (
    governance_router,
    quality_router,
    decision_router,
    publication_router,
    report_router,
    audit_router,
    archive_router,
    backup_router,
    incident_router,
)

api_router.include_router(governance_router)
api_router.include_router(quality_router)
api_router.include_router(decision_router)
api_router.include_router(publication_router)
api_router.include_router(report_router)
api_router.include_router(audit_router)
api_router.include_router(archive_router)
api_router.include_router(backup_router)
api_router.include_router(incident_router)
```

Puis exécuter impérativement :

```powershell
.\.venv\Scripts\python.exe -m app.scripts.seed_governance_permissions
```

Aucune migration Alembic n'est requise.
