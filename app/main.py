from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes.api.v1.router import api_router


BASE_DIR = Path(__file__).resolve().parent


app = FastAPI(
    title="HAUQE Certif",
    version="0.2.0",
    description="API BNEC / HAUQE Certif",
)


# ============================================================
# FRONTEND
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@app.get(
    "/",
    response_class=HTMLResponse,
    name="application",
    include_in_schema=False,
)
async def application(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@app.get(
    "/views/{page_name}",
    response_class=HTMLResponse,
    name="frontend_view",
    include_in_schema=False,
)
async def frontend_view(
    request: Request,
    page_name: str,
):
    allowed_pages = {
        "dashboard": "views/dashboard.html",
        "alertes": "views/alertes.html",
        "echeances": "views/echeances.html",
        "veille": "views/veille.html",
        "entreprises": "views/entreprises.html",

        "entreprise-detail": "views/entreprise-detail.html",
        "entreprise-form": "views/entreprise-form.html",

        "certifications": "views/certifications.html",
        "certification-detail": "views/certification-detail.html",
        "certification-form": "views/certification-form.html",

        "organismes": "views/organismes.html",
        "organisme-detail": "views/organisme-detail.html",
        "organisme-form": "views/organisme-form.html",

        "collectes": "views/collectes.html",
        "collecte-form": "views/collecte-form.html",

        "verifications": "views/verifications.html",
        "verification-detail": "views/verification-detail.html",
        
        "validations": "views/validations.html",
        "validation-detail": "views/validation-detail.html",
        
        "integrations": "views/integrations.html",
        "integration-detail": "views/integration-detail.html",
        
        "controle": "views/controle.html",
        "controle-detail": "views/controle-detail.html",
        
        "scoring": "views/scoring.html",
        "infc": "views/infc.html",
        "classement-sncc": "views/classement-sncc.html",

        "rapports": "views/rapports.html",
        "utilisateurs": "views/utilisateurs.html",
        "referentiels": "views/referentiels.html",
        "zones-administratives": "views/zones-administratives.html",

        "regles-codification": "views/regles-codification.html",
        "journal-audit": "views/journal-audit.html",

        "connexion": "views/connexion.html",
        "mot-de-passe-oublie": "views/mot-de-passe-oublie.html",
        "profil": "views/profil.html",

        "governance-module": "views/governance-module.html",
    }

    template_name = allowed_pages.get(
        page_name,
        "legacy/index.html",
    )

    return templates.TemplateResponse(
        request=request,
        name=template_name,
    )


@app.get(
    "/loader-demo",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def loader_demo(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="loader-demo.html",
    )


# ============================================================
# API VERSIONNÉE
# ============================================================

app.include_router(
    api_router,
    prefix="/api/v1",
)