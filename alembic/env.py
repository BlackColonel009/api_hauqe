from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config.settings import settings
from app.database.base import Base

# IMPORTANT :
# cet import charge les 66 modèles dans Base.metadata
import app.models  # noqa: F401


config = context.config


# ============================================================
# DATABASE URL
# ============================================================

# On prend DATABASE_URL depuis .env au lieu de conserver
# le mot de passe dans alembic.ini.
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url.replace("%", "%%"),
)


# ============================================================
# LOGGING
# ============================================================

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ============================================================
# METADATA SQLALCHEMY
# ============================================================

target_metadata = Base.metadata


# ============================================================
# MODE OFFLINE
# ============================================================

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },

        # Comparaisons importantes
        compare_type=True,
        compare_server_default=True,

        # Génération déterministe
        render_as_batch=False,
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================
# MODE ONLINE
# ============================================================

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,

            # Vérification des types PostgreSQL
            compare_type=True,

            # Vérification des defaults
            compare_server_default=True,

            # Ne pas générer automatiquement des changements
            # sur les noms de schémas PostgreSQL.
            include_schemas=False,
        )

        with context.begin_transaction():
            context.run_migrations()


# ============================================================
# EXECUTION
# ============================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()