# Intégration des routers

Dans `app/routes/api/v1/router.py` :

```python
from app.routes.api.v1.validations import (
    router as validations_router,
)
from app.routes.api.v1.integrations_bnec import (
    router as integrations_bnec_router,
    validation_integration_router,
)

api_router.include_router(validations_router)
api_router.include_router(integrations_bnec_router)
api_router.include_router(validation_integration_router)
```

Aucune migration Alembic n'est nécessaire.
