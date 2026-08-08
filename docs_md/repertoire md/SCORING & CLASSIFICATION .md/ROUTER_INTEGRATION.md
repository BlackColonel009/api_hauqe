# Intégration du router Scoring

Dans `app/routes/api/v1/router.py` :

```python
from app.routes.api.v1.scoring import (
    scoring_router,
    enterprise_classification_router,
    infc_router,
    cert_infc_router,
    sncc_router,
    cert_sncc_router,
)

api_router.include_router(scoring_router)
api_router.include_router(enterprise_classification_router)
api_router.include_router(infc_router)
api_router.include_router(cert_infc_router)
api_router.include_router(sncc_router)
api_router.include_router(cert_sncc_router)
```

Aucune migration Alembic n'est requise.
