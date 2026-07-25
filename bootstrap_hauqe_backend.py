# bootstrap_hauqe_backend.py

from pathlib import Path
import secrets
import subprocess
import sys


ROOT = Path(__file__).resolve().parent


# ============================================================
# 1. DOSSIERS À CRÉER
# ============================================================

DIRECTORIES = [
    "app/config",
    "app/database",

    "app/models",
    "app/schemas",
    "app/repositories",
    "app/services",
    "app/rules",
    "app/permissions",
    "app/audit",
    "app/middleware",
    "app/tasks",
    "app/utils",

    "app/routes",
    "app/routes/api",
    "app/routes/api/v1",

    "tests",
    "tests/unit",
    "tests/integration",
    "tests/api",

    "uploads",
    "uploads/avatars",
    "uploads/produits",
    "uploads/documents",
    "uploads/rapports",
    "uploads/temporaires",
]


# ============================================================
# 2. FICHIERS PYTHON VIDES / STRUCTURELS
# ============================================================

EMPTY_FILES = [
    # CONFIG
    "app/config/__init__.py",
    "app/config/security.py",
    "app/config/logging.py",

    # DATABASE
    "app/database/__init__.py",
    "app/database/types.py",

    # MODELS
    "app/models/__init__.py",
    "app/models/utilisateur.py",
    "app/models/role.py",
    "app/models/permission.py",
    "app/models/referentiel.py",
    "app/models/entreprise.py",
    "app/models/organisme.py",
    "app/models/accreditation.py",
    "app/models/certification.py",
    "app/models/document.py",
    "app/models/collecte.py",
    "app/models/verification.py",
    "app/models/controle.py",
    "app/models/validation.py",
    "app/models/integration.py",
    "app/models/scoring.py",
    "app/models/alerte.py",
    "app/models/veille.py",
    "app/models/regle_metier.py",
    "app/models/audit.py",

    # SCHEMAS
    "app/schemas/__init__.py",
    "app/schemas/auth.py",
    "app/schemas/utilisateur.py",
    "app/schemas/referentiel.py",
    "app/schemas/entreprise.py",
    "app/schemas/organisme.py",
    "app/schemas/certification.py",
    "app/schemas/document.py",
    "app/schemas/collecte.py",
    "app/schemas/verification.py",
    "app/schemas/controle.py",
    "app/schemas/validation.py",
    "app/schemas/integration.py",
    "app/schemas/scoring.py",
    "app/schemas/alerte.py",
    "app/schemas/audit.py",

    # REPOSITORIES
    "app/repositories/__init__.py",
    "app/repositories/base.py",
    "app/repositories/utilisateur_repository.py",
    "app/repositories/referentiel_repository.py",
    "app/repositories/entreprise_repository.py",
    "app/repositories/organisme_repository.py",
    "app/repositories/certification_repository.py",
    "app/repositories/document_repository.py",
    "app/repositories/collecte_repository.py",
    "app/repositories/verification_repository.py",
    "app/repositories/controle_repository.py",
    "app/repositories/validation_repository.py",
    "app/repositories/integration_repository.py",
    "app/repositories/scoring_repository.py",
    "app/repositories/alerte_repository.py",
    "app/repositories/audit_repository.py",

    # SERVICES
    "app/services/__init__.py",
    "app/services/auth_service.py",
    "app/services/utilisateur_service.py",
    "app/services/referentiel_service.py",
    "app/services/entreprise_service.py",
    "app/services/organisme_service.py",
    "app/services/certification_service.py",
    "app/services/document_service.py",
    "app/services/collecte_service.py",
    "app/services/verification_service.py",
    "app/services/controle_service.py",
    "app/services/validation_service.py",
    "app/services/integration_service.py",
    "app/services/scoring_service.py",
    "app/services/alerte_service.py",
    "app/services/audit_service.py",

    # RULES
    "app/rules/__init__.py",
    "app/rules/entreprises.py",
    "app/rules/certifications.py",
    "app/rules/completeness.py",
    "app/rules/duplicates.py",
    "app/rules/transitions.py",
    "app/rules/alerts.py",
    "app/rules/fuccs.py",
    "app/rules/infc.py",
    "app/rules/sncc.py",

    # PERMISSIONS
    "app/permissions/__init__.py",
    "app/permissions/dependencies.py",
    "app/permissions/policies.py",

    # AUDIT
    "app/audit/__init__.py",
    "app/audit/context.py",
    "app/audit/service.py",

    # MIDDLEWARE
    "app/middleware/__init__.py",
    "app/middleware/security.py",
    "app/middleware/request_context.py",

    # TASKS
    "app/tasks/__init__.py",
    "app/tasks/alerts.py",
    "app/tasks/notifications.py",

    # UTILS
    "app/utils/__init__.py",
    "app/utils/dates.py",
    "app/utils/files.py",
    "app/utils/pagination.py",

    # ROUTES
    "app/routes/__init__.py",
    "app/routes/web.py",
    "app/routes/api/__init__.py",
    "app/routes/api/v1/__init__.py",
    "app/routes/api/v1/router.py",
    "app/routes/api/v1/health.py",
    "app/routes/api/v1/auth.py",
    "app/routes/api/v1/users.py",
    "app/routes/api/v1/referentials.py",
    "app/routes/api/v1/enterprises.py",
    "app/routes/api/v1/certification_bodies.py",
    "app/routes/api/v1/certifications.py",
    "app/routes/api/v1/documents.py",
    "app/routes/api/v1/collections.py",
    "app/routes/api/v1/verifications.py",
    "app/routes/api/v1/controls.py",
    "app/routes/api/v1/validations.py",
    "app/routes/api/v1/integrations.py",
    "app/routes/api/v1/scoring.py",
    "app/routes/api/v1/alerts.py",
    "app/routes/api/v1/audit.py",

    # TESTS
    "tests/__init__.py",
    "tests/conftest.py",
    "tests/unit/__init__.py",
    "tests/integration/__init__.py",
    "tests/api/__init__.py",
]


# ============================================================
# 3. CONTENUS DE BASE
# ============================================================

SETTINGS_CONTENT = '''from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HAUQE Certif"
    environment: str = "development"
    debug: bool = True

    database_url: str

    secret_key: str
    access_token_expire_minutes: int = 30

    timezone: str = "Africa/Lome"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
'''


DATABASE_BASE_CONTENT = '''from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
'''


DATABASE_SESSION_CONTENT = '''from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import settings


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
'''


API_ROUTER_CONTENT = '''from fastapi import APIRouter

from app.routes.api.v1 import health


api_router = APIRouter()

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)

# Ajouter progressivement :
#
# api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(enterprises.router, prefix="/enterprises", tags=["Enterprises"])
# etc.
'''


HEALTH_CONTENT = '''from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.database.session import get_db


router = APIRouter()


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "application": "HAUQE Certif",
        "database": "connected",
    }
'''


REPOSITORY_BASE_CONTENT = '''from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase


ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class BaseRepository(Generic[ModelType]):

    def __init__(
        self,
        model: type[ModelType],
        session: AsyncSession,
    ):
        self.model = model
        self.session = session
'''


ENV_EXAMPLE_CONTENT = '''# ============================================================
# HAUQE CERTIF
# ============================================================

APP_NAME=HAUQE Certif
ENVIRONMENT=development
DEBUG=true

# PostgreSQL + Psycopg 3 async
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/hauqe_certif

# Sécurité
SECRET_KEY=CHANGE_ME
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Fuseau horaire
TIMEZONE=Africa/Lome
'''


GITIGNORE_CONTENT = '''# Python
__pycache__/
*.py[cod]
*.pyo

# Virtual environment
.venv/
venv/

# Environment
.env

# IDE
.vscode/
.idea/

# Tests
.pytest_cache/
.coverage
htmlcov/

# Uploads privés
uploads/documents/*
uploads/rapports/*
uploads/temporaires/*

# Conserver les dossiers
!uploads/documents/.gitkeep
!uploads/rapports/.gitkeep
!uploads/temporaires/.gitkeep
'''


ALEMBIC_ENV_CONTENT = '''from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.database.base import Base

# IMPORTANT :
# importer ici tous les modèles SQLAlchemy lorsque tu les créeras.
#
# Exemple :
# from app.models import entreprise
# from app.models import certification

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''


# ============================================================
# 4. FONCTIONS
# ============================================================

def create_directory(relative_path: str):
    path = ROOT / relative_path
    path.mkdir(parents=True, exist_ok=True)
    print(f"[DOSSIER] {relative_path}")


def create_file(relative_path: str, content: str = ""):
    path = ROOT / relative_path

    if path.exists():
        print(f"[EXISTE]  {relative_path}")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    print(f"[FICHIER] {relative_path}")


def create_env():
    env_path = ROOT / ".env"

    if env_path.exists():
        print("[EXISTE]  .env")
        return

    secret_key = secrets.token_urlsafe(64)

    content = f'''APP_NAME=HAUQE Certif
ENVIRONMENT=development
DEBUG=true

DATABASE_URL=postgresql+psycopg://postgres:CHANGE_ME@localhost:5432/hauqe_certif

SECRET_KEY={secret_key}
ACCESS_TOKEN_EXPIRE_MINUTES=30

TIMEZONE=Africa/Lome
'''

    env_path.write_text(content, encoding="utf-8")

    print("[FICHIER] .env")


def initialize_alembic():
    alembic_ini = ROOT / "alembic.ini"
    alembic_dir = ROOT / "alembic"

    if alembic_ini.exists() or alembic_dir.exists():
        print("[EXISTE]  Alembic")
        return

    print("\nInitialisation Alembic...")

    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "alembic",
                "init",
                "alembic",
            ],
            cwd=ROOT,
            check=True,
        )

        print("[OK] Alembic initialisé")

    except Exception:
        print(
            "\n[ATTENTION] Alembic n'est probablement pas installé.\n"
            "Installe-le avec :\n\n"
            "    pip install alembic\n\n"
            "Puis exécute :\n\n"
            "    python -m alembic init alembic\n"
        )


def configure_alembic_env():
    path = ROOT / "alembic" / "env.py"

    if not path.exists():
        return

    path.write_text(
        ALEMBIC_ENV_CONTENT,
        encoding="utf-8",
    )

    print("[CONFIG]  alembic/env.py")


def create_gitkeep_files():
    folders = [
        "uploads/avatars",
        "uploads/produits",
        "uploads/documents",
        "uploads/rapports",
        "uploads/temporaires",
    ]

    for folder in folders:
        path = ROOT / folder / ".gitkeep"

        if not path.exists():
            path.touch()


# ============================================================
# 5. EXÉCUTION
# ============================================================

def main():

    print("=" * 70)
    print("INITIALISATION BACKEND — HAUQE CERTIF")
    print("=" * 70)

    app_path = ROOT / "app"

    if not app_path.exists():
        print(
            "\nERREUR : dossier app/ introuvable.\n"
            "Place ce script à la racine du projet HAUQE Certif."
        )
        return

    # --------------------------------------------------------
    # Dossiers
    # --------------------------------------------------------

    for directory in DIRECTORIES:
        create_directory(directory)

    # --------------------------------------------------------
    # Fichiers génériques
    # --------------------------------------------------------

    for file_path in EMPTY_FILES:
        create_file(file_path)

    # --------------------------------------------------------
    # Fichiers avec contenu initial
    # --------------------------------------------------------

    create_file(
        "app/config/settings.py",
        SETTINGS_CONTENT,
    )

    create_file(
        "app/database/base.py",
        DATABASE_BASE_CONTENT,
    )

    create_file(
        "app/database/session.py",
        DATABASE_SESSION_CONTENT,
    )

    create_file(
        "app/routes/api/v1/router.py",
        API_ROUTER_CONTENT,
    )

    create_file(
        "app/routes/api/v1/health.py",
        HEALTH_CONTENT,
    )

    create_file(
        "app/repositories/base.py",
        REPOSITORY_BASE_CONTENT,
    )

    # --------------------------------------------------------
    # ENV
    # --------------------------------------------------------

    create_env()

    create_file(
        ".env.example",
        ENV_EXAMPLE_CONTENT,
    )

    # --------------------------------------------------------
    # Gitignore
    # --------------------------------------------------------

    create_file(
        ".gitignore",
        GITIGNORE_CONTENT,
    )

    # --------------------------------------------------------
    # Uploads
    # --------------------------------------------------------

    create_gitkeep_files()

    # --------------------------------------------------------
    # Alembic
    # --------------------------------------------------------

    initialize_alembic()
    configure_alembic_env()

    print("\n" + "=" * 70)
    print("STRUCTURE CRÉÉE AVEC SUCCÈS")
    print("=" * 70)

    print(
        """
IMPORTANT :

1. Ton app/main.py existant n'a pas été modifié.
2. app/static/ n'a pas été modifié.
3. app/templates/ n'a pas été modifié.
4. Vérifie le DATABASE_URL dans .env.
5. Installe les dépendances nécessaires.
"""
    )


if __name__ == "__main__":
    main()