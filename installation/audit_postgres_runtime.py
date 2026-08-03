from __future__ import annotations

from sqlalchemy import create_engine, inspect, text

from app.config.settings import settings


EXPECTED = {
    "tables": 66,
    "columns": 843,
    "foreign_keys": 107,
    "unique_constraints": 9,
    "primary_keys": 66,
    "revision": "9f89b5d85b6a",
}


def ok(label: str, actual, expected) -> bool:
    status = "OK" if actual == expected else "ERREUR"

    print(
        f"[{status:<6}] "
        f"{label:<25} "
        f"{actual} / attendu {expected}"
    )

    return actual == expected


def main() -> None:
    print("=" * 72)
    print("HAUQE CERTIF — AUDIT POSTGRESQL APRES MIGRATION")
    print("=" * 72)

    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
    )

    inspector = inspect(engine)

    # ============================================================
    # TABLES
    # ============================================================

    all_tables = inspector.get_table_names(
        schema="public"
    )

    # alembic_version est une table technique Alembic,
    # elle ne fait pas partie des 66 tables métier.
    business_tables = [
        table
        for table in all_tables
        if table != "alembic_version"
    ]

    # ============================================================
    # COLONNES / FK / UNIQUE / PK
    # ============================================================

    column_count = 0
    fk_count = 0
    unique_count = 0
    pk_count = 0

    for table in business_tables:

        columns = inspector.get_columns(
            table,
            schema="public",
        )

        column_count += len(columns)

        foreign_keys = inspector.get_foreign_keys(
            table,
            schema="public",
        )

        fk_count += len(foreign_keys)

        unique_constraints = inspector.get_unique_constraints(
            table,
            schema="public",
        )

        unique_count += len(
            unique_constraints
        )

        pk = inspector.get_pk_constraint(
            table,
            schema="public",
        )

        if pk.get("constrained_columns"):
            pk_count += 1

    # ============================================================
    # REVISION ALEMBIC
    # ============================================================

    with engine.connect() as connection:

        revision = connection.execute(
            text(
                """
                SELECT version_num
                FROM alembic_version
                LIMIT 1
                """
            )
        ).scalar_one_or_none()

        # --------------------------------------------------------
        # PostgreSQL
        # --------------------------------------------------------

        pg_version = connection.execute(
            text("SELECT version()")
        ).scalar_one()

        # --------------------------------------------------------
        # GEN_RANDOM_UUID
        # --------------------------------------------------------

        uuid_test = connection.execute(
            text("SELECT gen_random_uuid()")
        ).scalar_one()

    # ============================================================
    # RESULTATS
    # ============================================================

    print()
    print("PostgreSQL :")
    print(pg_version)

    print()
    print("Test gen_random_uuid() :")
    print(uuid_test)

    print()
    print("=" * 72)
    print("CONFORMITE")
    print("=" * 72)

    results = []

    results.append(
        ok(
            "Tables métier",
            len(business_tables),
            EXPECTED["tables"],
        )
    )

    results.append(
        ok(
            "Colonnes",
            column_count,
            EXPECTED["columns"],
        )
    )

    results.append(
        ok(
            "Clés étrangères",
            fk_count,
            EXPECTED["foreign_keys"],
        )
    )

    results.append(
        ok(
            "Contraintes UNIQUE",
            unique_count,
            EXPECTED["unique_constraints"],
        )
    )

    results.append(
        ok(
            "Clés primaires",
            pk_count,
            EXPECTED["primary_keys"],
        )
    )

    results.append(
        ok(
            "Révision Alembic",
            revision,
            EXPECTED["revision"],
        )
    )

    # ============================================================
    # TABLE ALEMBIC
    # ============================================================

    print()

    if "alembic_version" in all_tables:
        print(
            "[OK    ] Table technique "
            "alembic_version présente"
        )
    else:
        print(
            "[ERREUR] Table alembic_version absente"
        )
        results.append(False)

    # ============================================================
    # VERDICT
    # ============================================================

    print()
    print("=" * 72)

    if all(results):
        print("VERDICT : POSTGRESQL CONFORME")
        print("=" * 72)

        print(
            """
La base physique est conforme au modèle attendu :

- 66 tables métier
- 843 colonnes
- 107 clés étrangères
- 9 contraintes UNIQUE
- 66 clés primaires
- révision Alembic correcte
- gen_random_uuid() opérationnel
"""
        )

    else:
        print("VERDICT : NON CONFORME")
        print("=" * 72)

        print(
            "Ne commence pas encore les données initiales "
            "ni l'API métier."
        )


if __name__ == "__main__":
    main()