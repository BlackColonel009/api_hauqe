from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import UniqueConstraint


ROOT = Path(__file__).resolve().parent


# ============================================================
# MODELES DE DONNEES POUR L'AUDIT
# ============================================================

@dataclass
class ExpectedColumn:
    name: str
    pg_type: str
    constraints_raw: str
    primary_key: bool
    nullable: bool
    unique: bool
    foreign_key: str | None
    default: str | None


@dataclass
class Difference:
    severity: str
    table: str
    column: str | None
    property_name: str
    expected: Any
    actual: Any


# ============================================================
# LOCALISATION DU DICTIONNAIRE
# ============================================================

def find_dictionary(explicit_path: str | None = None) -> Path:
    if explicit_path:
        path = Path(explicit_path)

        if not path.is_absolute():
            path = ROOT / path

        if not path.exists():
            raise FileNotFoundError(
                f"Dictionnaire introuvable : {path}"
            )

        return path

    candidates = [
        ROOT / "DICTIONNAIRE_DONNEES_66_TABLES.md",
        ROOT / "docs" / "DICTIONNAIRE_DONNEES_66_TABLES.md",
        ROOT / "documentation" / "DICTIONNAIRE_DONNEES_66_TABLES.md",
        ROOT / "sources" / "DICTIONNAIRE_DONNEES_66_TABLES.md",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "\nImpossible de trouver DICTIONNAIRE_DONNEES_66_TABLES.md.\n"
        "Utilise par exemple :\n\n"
        "python audit_sqlalchemy_vs_dictionary.py "
        "--dictionary chemin/DICTIONNAIRE_DONNEES_66_TABLES.md\n"
    )


# ============================================================
# PARSING DU DICTIONNAIRE MARKDOWN
# ============================================================

TABLE_HEADING_RE = re.compile(
    r"^##\s+\d+\.\s+`([^`]+)`\s*$",
    re.MULTILINE,
)

COLUMN_ROW_RE = re.compile(
    r"^\|\s*`([^`]+)`\s*"
    r"\|\s*`([^`]+)`\s*"
    r"\|\s*(.*?)\s*\|\s*$",
    re.MULTILINE,
)

FK_RE = re.compile(
    r"FK\s*→\s*`([^`]+)`"
)


def parse_constraints(
    raw: str,
) -> tuple[bool, bool, bool, str | None, str | None]:

    primary_key = bool(
        re.search(r"\bPK\b", raw)
    )

    unique = bool(
        re.search(r"\bUQ\b", raw)
    )

    # NN = NOT NULL.
    # Tout ce qui n'est pas NN est nullable dans le dictionnaire.
    nullable = not bool(
        re.search(r"\bNN\b", raw)
    )

    fk_match = FK_RE.search(raw)

    foreign_key = (
        fk_match.group(1)
        if fk_match
        else None
    )

    default = None

    if "gen_random_uuid()" in raw:
        default = "gen_random_uuid()"

    elif "now()" in raw:
        default = "now()"

    return (
        primary_key,
        nullable,
        unique,
        foreign_key,
        default,
    )


def parse_dictionary(
    path: Path,
) -> dict[str, dict[str, ExpectedColumn]]:

    text = path.read_text(
        encoding="utf-8"
    )

    headings = list(
        TABLE_HEADING_RE.finditer(text)
    )

    expected: dict[
        str,
        dict[str, ExpectedColumn]
    ] = {}

    for index, heading in enumerate(headings):

        table_name = heading.group(1)

        start = heading.end()

        end = (
            headings[index + 1].start()
            if index + 1 < len(headings)
            else len(text)
        )

        section = text[start:end]

        columns: dict[
            str,
            ExpectedColumn
        ] = {}

        for match in COLUMN_ROW_RE.finditer(section):

            column_name = match.group(1)
            pg_type = match.group(2)
            constraints = match.group(3)

            (
                primary_key,
                nullable,
                unique,
                foreign_key,
                default,
            ) = parse_constraints(
                constraints
            )

            columns[column_name] = ExpectedColumn(
                name=column_name,
                pg_type=normalize_type_name(pg_type),
                constraints_raw=constraints,
                primary_key=primary_key,
                nullable=nullable,
                unique=unique,
                foreign_key=foreign_key,
                default=default,
            )

        expected[table_name] = columns

    return expected


# ============================================================
# NORMALISATION TYPES POSTGRESQL
# ============================================================

def normalize_type_name(value: str) -> str:
    value = value.strip().upper()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    value = value.replace(
        "NUMERIC(18, 4)",
        "NUMERIC(18,4)",
    )

    aliases = {
        "TIMESTAMP WITH TIME ZONE": "TIMESTAMPTZ",
        "TIMESTAMP WITHOUT TIME ZONE": "TIMESTAMP",
        "CHARACTER VARYING(255)": "VARCHAR(255)",
        "DOUBLE PRECISION": "FLOAT8",
    }

    return aliases.get(
        value,
        value,
    )


def sqlalchemy_type_name(column) -> str:
    dialect = postgresql.dialect()

    compiled = column.type.compile(
        dialect=dialect
    )

    return normalize_type_name(
        str(compiled)
    )


# ============================================================
# SQLALCHEMY METADATA
# ============================================================

def load_sqlalchemy_metadata():
    """
    L'import app.models doit charger les 66 modèles.
    """

    try:
        import app.models  # noqa: F401
        from app.database.base import Base

    except Exception as exc:
        print(
            "\nERREUR pendant le chargement "
            "des modèles SQLAlchemy :\n"
        )

        print(exc)

        raise

    # Force la configuration de toutes les relations ORM.
    from sqlalchemy.orm import configure_mappers

    configure_mappers()

    return Base.metadata


def get_unique_columns(table) -> set[str]:
    unique_columns: set[str] = set()

    # unique=True directement sur Column
    for column in table.columns:
        if column.unique is True:
            unique_columns.add(
                column.name
            )

    # UniqueConstraint SQLAlchemy
    for constraint in table.constraints:
        if isinstance(
            constraint,
            UniqueConstraint,
        ):
            for column in constraint.columns:
                unique_columns.add(
                    column.name
                )

    return unique_columns


def get_foreign_key(column) -> str | None:
    foreign_keys = list(
        column.foreign_keys
    )

    if not foreign_keys:
        return None

    if len(foreign_keys) > 1:
        return " | ".join(
            sorted(
                fk.target_fullname
                for fk in foreign_keys
            )
        )

    return foreign_keys[
        0
    ].target_fullname


def normalize_default(
    value: Any,
) -> str | None:

    if value is None:
        return None

    text = str(
        getattr(
            value,
            "arg",
            value,
        )
    )

    text = text.strip().lower()

    text = (
        text
        .replace("'", "")
        .replace('"', "")
    )

    if "gen_random_uuid()" in text:
        return "gen_random_uuid()"

    if "now()" in text:
        return "now()"

    if "current_timestamp" in text:
        return "now()"

    return text


# ============================================================
# COMPARAISON
# ============================================================

def add_difference(
    differences: list[Difference],
    *,
    severity: str,
    table: str,
    column: str | None,
    property_name: str,
    expected: Any,
    actual: Any,
) -> None:

    differences.append(
        Difference(
            severity=severity,
            table=table,
            column=column,
            property_name=property_name,
            expected=expected,
            actual=actual,
        )
    )


def audit_schema(
    expected_schema,
    metadata,
) -> list[Difference]:

    differences: list[Difference] = []

    expected_tables = set(
        expected_schema.keys()
    )

    actual_tables = set(
        metadata.tables.keys()
    )

    # --------------------------------------------------------
    # TABLES MANQUANTES
    # --------------------------------------------------------

    for table_name in sorted(
        expected_tables - actual_tables
    ):

        add_difference(
            differences,
            severity="ERROR",
            table=table_name,
            column=None,
            property_name="table",
            expected="présente",
            actual="absente",
        )

    # --------------------------------------------------------
    # TABLES EN TROP
    # --------------------------------------------------------

    for table_name in sorted(
        actual_tables - expected_tables
    ):

        add_difference(
            differences,
            severity="ERROR",
            table=table_name,
            column=None,
            property_name="table",
            expected="absente",
            actual="présente dans SQLAlchemy",
        )

    # --------------------------------------------------------
    # TABLES COMMUNES
    # --------------------------------------------------------

    for table_name in sorted(
        expected_tables & actual_tables
    ):

        expected_columns = expected_schema[
            table_name
        ]

        table = metadata.tables[
            table_name
        ]

        actual_columns = {
            column.name: column
            for column in table.columns
        }

        expected_column_names = set(
            expected_columns.keys()
        )

        actual_column_names = set(
            actual_columns.keys()
        )

        # Colonnes manquantes
        for column_name in sorted(
            expected_column_names
            - actual_column_names
        ):

            add_difference(
                differences,
                severity="ERROR",
                table=table_name,
                column=column_name,
                property_name="colonne",
                expected="présente",
                actual="absente",
            )

        # Colonnes en trop
        for column_name in sorted(
            actual_column_names
            - expected_column_names
        ):

            add_difference(
                differences,
                severity="ERROR",
                table=table_name,
                column=column_name,
                property_name="colonne",
                expected="absente",
                actual="présente",
            )

        unique_columns = get_unique_columns(
            table
        )

        for column_name in sorted(
            expected_column_names
            & actual_column_names
        ):

            expected = expected_columns[
                column_name
            ]

            actual = actual_columns[
                column_name
            ]

            # --------------------------------------------
            # TYPE
            # --------------------------------------------

            expected_type = normalize_type_name(
                expected.pg_type
            )

            actual_type = sqlalchemy_type_name(
                actual
            )

            if expected_type != actual_type:

                add_difference(
                    differences,
                    severity="ERROR",
                    table=table_name,
                    column=column_name,
                    property_name="type",
                    expected=expected_type,
                    actual=actual_type,
                )

            # --------------------------------------------
            # PRIMARY KEY
            # --------------------------------------------

            if (
                expected.primary_key
                != actual.primary_key
            ):

                add_difference(
                    differences,
                    severity="ERROR",
                    table=table_name,
                    column=column_name,
                    property_name="primary_key",
                    expected=expected.primary_key,
                    actual=actual.primary_key,
                )

            # --------------------------------------------
            # NULLABLE
            # --------------------------------------------

            # SQLAlchemy considère toujours une PK
            # comme non nullable.
            actual_nullable = bool(
                actual.nullable
            )

            if (
                expected.nullable
                != actual_nullable
            ):

                add_difference(
                    differences,
                    severity="ERROR",
                    table=table_name,
                    column=column_name,
                    property_name="nullable",
                    expected=expected.nullable,
                    actual=actual_nullable,
                )

            # --------------------------------------------
            # UNIQUE
            # --------------------------------------------

            actual_unique = (
                column_name
                in unique_columns
            )

            if (
                expected.unique
                != actual_unique
            ):

                add_difference(
                    differences,
                    severity="ERROR",
                    table=table_name,
                    column=column_name,
                    property_name="unique",
                    expected=expected.unique,
                    actual=actual_unique,
                )

            # --------------------------------------------
            # FOREIGN KEY
            # --------------------------------------------

            actual_fk = get_foreign_key(
                actual
            )

            if (
                expected.foreign_key
                != actual_fk
            ):

                add_difference(
                    differences,
                    severity="ERROR",
                    table=table_name,
                    column=column_name,
                    property_name="foreign_key",
                    expected=expected.foreign_key,
                    actual=actual_fk,
                )

            # --------------------------------------------
            # SERVER DEFAULT
            # --------------------------------------------

            expected_default = (
                expected.default
            )

            actual_default = normalize_default(
                actual.server_default
            )

            if (
                expected_default
                != actual_default
            ):

                add_difference(
                    differences,
                    severity="ERROR",
                    table=table_name,
                    column=column_name,
                    property_name="server_default",
                    expected=expected_default,
                    actual=actual_default,
                )

    return differences


# ============================================================
# STATISTIQUES
# ============================================================

def calculate_expected_stats(
    schema,
) -> dict[str, int]:

    table_count = len(schema)

    column_count = sum(
        len(columns)
        for columns in schema.values()
    )

    fk_count = sum(
        1
        for columns in schema.values()
        for column in columns.values()
        if column.foreign_key
    )

    unique_count = sum(
        1
        for columns in schema.values()
        for column in columns.values()
        if column.unique
    )

    return {
        "tables": table_count,
        "columns": column_count,
        "foreign_keys": fk_count,
        "unique_columns": unique_count,
    }


def calculate_actual_stats(
    metadata,
) -> dict[str, int]:

    tables = list(
        metadata.tables.values()
    )

    column_count = sum(
        len(table.columns)
        for table in tables
    )

    foreign_key_count = sum(
        len(column.foreign_keys)
        for table in tables
        for column in table.columns
    )

    unique_count = 0

    for table in tables:
        unique_count += len(
            get_unique_columns(table)
        )

    return {
        "tables": len(tables),
        "columns": column_count,
        "foreign_keys": foreign_key_count,
        "unique_columns": unique_count,
    }


# ============================================================
# RAPPORT MARKDOWN
# ============================================================

def md_value(value: Any) -> str:
    if value is None:
        return "`None`"

    value = str(value)

    value = value.replace(
        "|",
        "\\|",
    )

    return f"`{value}`"


def generate_markdown_report(
    dictionary_path: Path,
    expected_stats: dict,
    actual_stats: dict,
    differences: list[Difference],
) -> str:

    lines: list[str] = []

    lines.append(
        "# Audit SQLAlchemy ↔ Dictionnaire HAUQE Certif"
    )

    lines.append("")
    lines.append(
        f"**Source :** `{dictionary_path}`"
    )

    lines.append("")
    lines.append("## 1. Synthèse")
    lines.append("")

    lines.append(
        "| Indicateur | Dictionnaire | SQLAlchemy |"
    )

    lines.append(
        "|---|---:|---:|"
    )

    labels = {
        "tables": "Tables",
        "columns": "Colonnes",
        "foreign_keys": "Clés étrangères",
        "unique_columns": "Colonnes uniques",
    }

    for key, label in labels.items():

        lines.append(
            f"| {label} | "
            f"{expected_stats[key]} | "
            f"{actual_stats[key]} |"
        )

    lines.append("")

    if not differences:

        lines.append(
            "## 2. Verdict"
        )

        lines.append("")

        lines.append(
            "**CONFORME — aucun écart structurel détecté.**"
        )

        lines.append("")

        lines.append(
            "Les métadonnées SQLAlchemy correspondent "
            "au dictionnaire sur les éléments contrôlés."
        )

        return "\n".join(lines)

    lines.append(
        "## 2. Verdict"
    )

    lines.append("")

    lines.append(
        f"**NON CONFORME — "
        f"{len(differences)} écart(s) détecté(s).**"
    )

    lines.append("")

    # --------------------------------------------------------
    # Regroupement
    # --------------------------------------------------------

    by_property: dict[str, int] = {}

    for diff in differences:

        by_property[
            diff.property_name
        ] = (
            by_property.get(
                diff.property_name,
                0,
            )
            + 1
        )

    lines.append(
        "### Répartition des écarts"
    )

    lines.append("")

    lines.append(
        "| Type d'écart | Nombre |"
    )

    lines.append(
        "|---|---:|"
    )

    for property_name, count in sorted(
        by_property.items()
    ):

        lines.append(
            f"| `{property_name}` | {count} |"
        )

    lines.append("")
    lines.append(
        "## 3. Détail des écarts"
    )

    lines.append("")

    lines.append(
        "| # | Table | Colonne | Propriété | "
        "Attendu | SQLAlchemy |"
    )

    lines.append(
        "|---:|---|---|---|---|---|"
    )

    for index, diff in enumerate(
        differences,
        start=1,
    ):

        column = (
            f"`{diff.column}`"
            if diff.column
            else "—"
        )

        lines.append(
            f"| {index} "
            f"| `{diff.table}` "
            f"| {column} "
            f"| `{diff.property_name}` "
            f"| {md_value(diff.expected)} "
            f"| {md_value(diff.actual)} |"
        )

    lines.append("")
    lines.append(
        "## 4. Décision"
    )

    lines.append("")

    lines.append(
        "Ne pas générer de migration Alembic "
        "tant que les écarts ERROR ne sont pas corrigés."
    )

    return "\n".join(lines)


# ============================================================
# JSON
# ============================================================

def generate_json_report(
    dictionary_path: Path,
    expected_stats: dict,
    actual_stats: dict,
    differences: list[Difference],
) -> dict:

    return {
        "dictionary": str(
            dictionary_path
        ),
        "expected": expected_stats,
        "actual": actual_stats,
        "conform": len(
            differences
        ) == 0,
        "difference_count": len(
            differences
        ),
        "differences": [
            {
                "severity": diff.severity,
                "table": diff.table,
                "column": diff.column,
                "property": diff.property_name,
                "expected": diff.expected,
                "actual": diff.actual,
            }
            for diff in differences
        ],
    }


# ============================================================
# CONTROLE DES VALEURS DE REFERENCE
# ============================================================

def print_stats(
    expected_stats,
    actual_stats,
):

    print()
    print("=" * 72)
    print("STATISTIQUES")
    print("=" * 72)

    print(
        f"Tables          : "
        f"{expected_stats['tables']} attendu / "
        f"{actual_stats['tables']} SQLAlchemy"
    )

    print(
        f"Colonnes        : "
        f"{expected_stats['columns']} attendu / "
        f"{actual_stats['columns']} SQLAlchemy"
    )

    print(
        f"FK              : "
        f"{expected_stats['foreign_keys']} attendu / "
        f"{actual_stats['foreign_keys']} SQLAlchemy"
    )

    print(
        f"UNIQUE          : "
        f"{expected_stats['unique_columns']} attendu / "
        f"{actual_stats['unique_columns']} SQLAlchemy"
    )


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Audit structurel des modèles SQLAlchemy "
            "HAUQE Certif par rapport au dictionnaire officiel."
        )
    )

    parser.add_argument(
        "--dictionary",
        help=(
            "Chemin vers "
            "DICTIONNAIRE_DONNEES_66_TABLES.md"
        ),
        default=None,
    )

    parser.add_argument(
        "--report-dir",
        default="reports",
        help="Répertoire des rapports.",
    )

    args = parser.parse_args()

    print("=" * 72)
    print("HAUQE CERTIF — AUDIT SQLALCHEMY / DICTIONNAIRE")
    print("=" * 72)

    try:
        dictionary_path = find_dictionary(
            args.dictionary
        )

    except FileNotFoundError as exc:
        print(exc)
        return 2

    print(
        f"Dictionnaire : {dictionary_path}"
    )

    # --------------------------------------------------------
    # 1. DICTIONNAIRE
    # --------------------------------------------------------

    expected_schema = parse_dictionary(
        dictionary_path
    )

    expected_stats = calculate_expected_stats(
        expected_schema
    )

    # --------------------------------------------------------
    # Contrôle de cohérence interne du fichier de référence
    # --------------------------------------------------------

    if expected_stats["tables"] != 66:

        print(
            "\nERREUR : le dictionnaire parsé "
            f"contient {expected_stats['tables']} tables "
            "au lieu de 66."
        )

        return 3

    if expected_stats["columns"] != 843:

        print(
            "\nERREUR : le dictionnaire parsé "
            f"contient {expected_stats['columns']} colonnes "
            "au lieu de 843."
        )

        return 3

    if expected_stats["foreign_keys"] != 107:

        print(
            "\nERREUR : le dictionnaire parsé "
            f"contient {expected_stats['foreign_keys']} FK "
            "au lieu de 107."
        )

        return 3

    if expected_stats["unique_columns"] != 9:

        print(
            "\nERREUR : le dictionnaire parsé "
            f"contient {expected_stats['unique_columns']} "
            "contraintes uniques au lieu de 9."
        )

        return 3

    print(
        "Dictionnaire validé : "
        "66 tables / 843 colonnes / 107 FK / 9 UNIQUE"
    )

    # --------------------------------------------------------
    # 2. SQLALCHEMY
    # --------------------------------------------------------

    try:
        metadata = load_sqlalchemy_metadata()

    except Exception:
        return 4

    actual_stats = calculate_actual_stats(
        metadata
    )

    print_stats(
        expected_stats,
        actual_stats,
    )

    # --------------------------------------------------------
    # 3. COMPARAISON
    # --------------------------------------------------------

    differences = audit_schema(
        expected_schema,
        metadata,
    )

    # --------------------------------------------------------
    # 4. RAPPORTS
    # --------------------------------------------------------

    report_dir = ROOT / args.report_dir

    report_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    markdown_path = (
        report_dir
        / "AUDIT_SQLALCHEMY_VS_DICTIONNAIRE.md"
    )

    json_path = (
        report_dir
        / "AUDIT_SQLALCHEMY_VS_DICTIONNAIRE.json"
    )

    markdown_report = generate_markdown_report(
        dictionary_path,
        expected_stats,
        actual_stats,
        differences,
    )

    markdown_path.write_text(
        markdown_report,
        encoding="utf-8",
    )

    json_report = generate_json_report(
        dictionary_path,
        expected_stats,
        actual_stats,
        differences,
    )

    json_path.write_text(
        json.dumps(
            json_report,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # 5. VERDICT
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("VERDICT")
    print("=" * 72)

    if differences:

        print(
            f"NON CONFORME : "
            f"{len(differences)} écart(s) détecté(s)."
        )

        print()
        print(
            "NE LANCE PAS ENCORE ALEMBIC."
        )

        print()
        print(
            f"Rapport : {markdown_path}"
        )

        print(
            f"JSON    : {json_path}"
        )

        return 1

    print(
        "CONFORME : aucun écart structurel détecté."
    )

    print()
    print(
        f"Rapport : {markdown_path}"
    )

    print(
        f"JSON    : {json_path}"
    )

    print()
    print(
        "Les modèles peuvent passer à "
        "l'étape suivante de préparation Alembic."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())