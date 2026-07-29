from fastapi import APIRouter

from app.routes.api.v1 import  health

from app.routes.api.v1.auth import (
    router as auth_router,
)
from app.routes.api.v1.me import (
    router as me_router,
)

from app.routes.api.v1.users import (
    router as users_router,
)

from app.routes.api.v1.roles import (
    router as roles_router,
)

from app.routes.api.v1.zones_administratives import (
    router as zones_administratives_router,
)

# ============================================================
# MODULE ENTREPRISES
# ============================================================

from app.routes.api.v1.enterprises import (
    router as enterprises_router,
)

# ============================================================
# SOUS-MODULE CONTACTS ENTREPRISE
# ============================================================

from app.routes.api.v1.contacts_entreprise import (
    router as contacts_entreprise_router,
)

from app.routes.api.v1.sites_entreprise import (
    router as sites_entreprise_router,
)


from app.routes.api.v1.offres_entreprise import (
    router as offres_entreprise_router,
)
from app.routes.api.v1.candidats_doublon import (
    router as candidats_doublon_router,
)

# ============================================================
# MODULE ORGANISMES DE CERTIFICATION
# ============================================================

from app.routes.api.v1.organismes_certifications import (
    router as organismes_certifications_router,
)
from app.routes.api.v1.documents import router as documents_router

# ============================================================
# MODULE CERTIFICATION REGISTRY
# ============================================================


from app.routes.api.v1.certification_registry import (
    router as certification_registry_router,
)

# ============================================================
# MODULE MISSIONS DE COLLECTE
# ============================================================
from app.routes.api.v1.collecte_workspace import (
    router as collecte_workspace_router,
)
from app.routes.api.v1.campagnes import router as campagnes_router
from app.routes.api.v1.missions_collecte import (
    global_router as missions_collecte_router,
    campaign_router as campagnes_missions_router,
)
from app.routes.api.v1.fiches_collecte import (
    router as fiches_collecte_router,
)

# ============================================================
# MODULE VERIFICATIONS
# ============================================================

from app.routes.api.v1.verifications import router as verifications_router
from app.routes.api.v1.fuccs_workspace import (
    router as fuccs_workspace_router,
)
from app.routes.api.v1.fuccs import (
    router as fuccs_router,
    verification_fuccs_router,
)
# ============================================================
# MODULE VALIDATIONS
# ============================================================

from app.routes.api.v1.validation_workspace import (
    router as validation_workspace_router,
)
from app.routes.api.v1.validations import (
    router as validations_router,
)
from app.routes.api.v1.integration_workspace import (
    router as integration_workspace_router,
)
from app.routes.api.v1.integrations_bnec import (
    router as integrations_bnec_router,
    validation_integration_router,
)
# ============================================================
# MODULE SCORING
# ============================================================

from app.routes.api.v1.scoring_workspace import (
    router as scoring_workspace_router,
)
from app.routes.api.v1.scoring import (
    scoring_router,
    enterprise_classification_router,
    infc_router,
    cert_infc_router,
    sncc_router,
    cert_sncc_router,
)


# ============================================================
# MODULE VEILLE, ALERTES ET NOTIFICATIONS
# ============================================================


from app.routes.api.v1.watch_workspace import (
    router as watch_workspace_router,
)
from app.routes.api.v1.veille import (
    deadline_router,
    alert_router,
    notification_router,
    watch_router,
)

# ============================================================
# MODULE GOUVERNANCE, QUALITE ET AUDIT
# ============================================================

from app.routes.api.v1.institutional_setup import (
    router as institutional_setup_router,
)
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

# ============================================================
# MODULE DASHBOARDS
# ============================================================

from app.routes.api.v1.dashboards import (
    dashboard_router,
    barometer_router,
    public_dashboard_router,
)

# ============================================================
# MODULE COMPTE UTILISATEUR
# ============================================================

from app.routes.api.v1.account import (
    account_router,
    account_auth_router,
)

from app.routes.api.v1.account_avatar import (
    avatar_router as account_avatar_router,
)

from app.routes.api.v1.presence import (
    router as presence_router,
)



api_router = APIRouter()


api_router.include_router(
    health.router,
    prefix="/health",
    tags=["System"],
)

api_router.include_router(
    auth_router
)

api_router.include_router(
    account_router
)

api_router.include_router(
    presence_router
)

api_router.include_router(
    account_avatar_router
)

api_router.include_router(
    account_auth_router
)

api_router.include_router(
    me_router
)

api_router.include_router(
    users_router
)

api_router.include_router(
    roles_router
)

api_router.include_router(
    zones_administratives_router
)

api_router.include_router(
    enterprises_router
)

api_router.include_router(
    contacts_entreprise_router
)

api_router.include_router(
    sites_entreprise_router
)

api_router.include_router(
    offres_entreprise_router
)

api_router.include_router(
    candidats_doublon_router
)


api_router.include_router(
    organismes_certifications_router
)

api_router.include_router(
    certification_registry_router
)

api_router.include_router(
    documents_router
)

api_router.include_router(
    collecte_workspace_router
)

api_router.include_router(
    campagnes_router
)

api_router.include_router(
    missions_collecte_router
)

api_router.include_router(
    campagnes_missions_router
)

api_router.include_router(
    fiches_collecte_router
)

api_router.include_router(
    verifications_router
)

api_router.include_router(
    fuccs_workspace_router
)

api_router.include_router(
    fuccs_router
)

api_router.include_router(
    verification_fuccs_router
)

api_router.include_router(
    validation_workspace_router
)

api_router.include_router(
    validations_router
)

api_router.include_router(
    integration_workspace_router
)

api_router.include_router(
    integrations_bnec_router
)

api_router.include_router(
    validation_integration_router
)

api_router.include_router(
    scoring_workspace_router
)

api_router.include_router(
    scoring_router
)

api_router.include_router(
    enterprise_classification_router
)

api_router.include_router(
    infc_router
)

api_router.include_router(
    cert_infc_router
)

api_router.include_router(
    sncc_router
)

api_router.include_router(
    cert_sncc_router
)

api_router.include_router(
    deadline_router
)

api_router.include_router(
    alert_router
)

api_router.include_router(
    notification_router
)

api_router.include_router(
    watch_workspace_router
)

api_router.include_router(
    institutional_setup_router
)

api_router.include_router(
    watch_router
)

api_router.include_router(
    governance_router
)

api_router.include_router(
    quality_router
)

api_router.include_router(
    decision_router
)

api_router.include_router(
    publication_router
)

api_router.include_router(
    report_router
)

api_router.include_router(
    audit_router
)

api_router.include_router(
    archive_router
)

api_router.include_router(
    backup_router
)

api_router.include_router(
    incident_router
)

api_router.include_router(
    dashboard_router
)

api_router.include_router(
    barometer_router
)

api_router.include_router(
    public_dashboard_router
)

