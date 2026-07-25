from __future__ import annotations

import re
import unicodedata
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "MODELE_TABLES_VARIABLES_V2.md"
OUTPUT = ROOT / "output" / "sql" / "HAUQE_CERTIF_POWERDESIGNER.sql"


def ascii_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()


def infer_type(name: str) -> str:
    json_names = {
        "secteurs_secondaires", "marches_cibles", "destinations", "criteres_concordants",
        "preuves", "valeurs_avant", "valeurs_apres", "parametres", "sources",
        "scores_domaines", "indicateurs", "filtres", "sections", "constats",
    }
    boolean_names = {
        "mfa_active", "is_active", "contact_principal", "authenticite_verifiee",
        "certification_strategique", "consentement_obtenu", "copie_disponible",
        "commentaire_obligatoire", "preuve_obligatoire", "escalade",
        "integrite_validee",
    }
    integer_names = {
        "niveau", "ordre_affichage", "effectif", "nombre_tentatives",
        "nombre_certifications_suivies", "nombre_alertes", "nombre_renouvellements",
        "progression", "numero_revision",
    }
    numeric_names = {
        "capital_social", "chiffre_affaires", "volume_annuel", "capacite_production",
        "volume", "capacite", "score_similarite", "score_rapprochement",
        "taux_completude", "score_maximal", "score_brut", "score", "poids",
        "valeur", "score_global", "delai_moyen_traitement", "latitude", "longitude",
    }
    if name == "id" or name.endswith("_id"):
        return "UUID"
    if name in json_names:
        return "JSONB"
    if name in boolean_names or name.startswith("est_"):
        return "BOOLEAN"
    if name in integer_names or name.startswith("nombre_"):
        return "INTEGER"
    if name in numeric_names:
        return "NUMERIC(18,4)"
    if name == "taille_octets":
        return "BIGINT"
    if name.endswith("_at") or name in {"date_evenement", "date_depot", "date_archivage"}:
        return "TIMESTAMPTZ"
    if name.startswith("date_") or name.endswith("_date"):
        return "DATE"
    if name in {
        "description", "observations", "observation", "commentaire", "commentaires",
        "message", "contenu", "contenu_reponse", "synthese", "justification",
        "motif", "resolution", "reponse", "resultat", "resume", "regle_calcul",
        "perimetre", "portee", "adresse", "contexte", "instructions",
    }:
        return "TEXT"
    return "VARCHAR(255)"


def parse_model() -> tuple[list[dict], list[tuple[str, str, str, str]], list[tuple[str, str]]]:
    tables: list[dict] = []
    foreign_keys: list[tuple[str, str, str, str]] = []
    unique_keys: list[tuple[str, str]] = []
    current = None

    for raw in SOURCE.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^###\s+\d+\.\s+(.+)$", raw)
        if heading:
            current = {"name": ascii_name(heading.group(1)), "columns": []}
            tables.append(current)
            continue
        column = re.match(r"^-\s+`([^`]+)`(?:\s+—\s+(.+))?$", raw)
        if not column or current is None:
            continue
        original_name, annotation = column.groups()
        annotation = annotation or ""
        name = ascii_name(original_name)
        current["columns"].append((name, infer_type(name), annotation))
        if "UQ" in annotation:
            unique_keys.append((current["name"], name))
        target = re.search(r"vers\s+`([^`]+)\.id`", annotation)
        if target:
            foreign_keys.append((current["name"], name, ascii_name(target.group(1)), "id"))
        elif "FK récursive" in annotation or "FK recursive" in annotation:
            foreign_keys.append((current["name"], name, current["name"], "id"))
    return tables, foreign_keys, unique_keys


def sql_identifier(name: str) -> str:
    return f'"{name}"'


def qualified_table(name: str) -> str:
    # PowerDesigner's script reverse-engineering parser resolves references more
    # reliably when table names are unqualified. PostgreSQL still creates the
    # objects in hauqe_certif because SET search_path is emitted before the DDL.
    return sql_identifier(name)


def short_code(prefix: str, *parts: str, max_length: int = 31) -> str:
    raw = "_".join((prefix, *parts))
    if len(raw) <= max_length:
        return raw
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:6]
    available = max_length - len(prefix) - len(digest) - 2
    stem = "_".join(parts)[:available].rstrip("_")
    return f"{prefix}_{stem}_{digest}"


def build() -> None:
    tables, foreign_keys, unique_keys = parse_model()
    lines = [
        "-- HAUQE Certif - Schéma PostgreSQL destiné à la rétroconception PowerDesigner",
        "-- Généré depuis MODELE_TABLES_VARIABLES_V2.md",
        "-- PostgreSQL 14+",
        "",
        "CREATE EXTENSION IF NOT EXISTS pgcrypto;",
        "CREATE SCHEMA IF NOT EXISTS hauqe_certif;",
        "SET search_path TO hauqe_certif, public;",
        "",
    ]

    for table in tables:
        columns = list(table["columns"])
        existing = {name for name, _, _ in columns}
        if "id" not in existing:
            columns.insert(0, ("id", "UUID", "PK"))
        if "created_at" not in existing:
            columns.append(("created_at", "TIMESTAMPTZ", ""))
        if "updated_at" not in existing:
            columns.append(("updated_at", "TIMESTAMPTZ", ""))

        lines.append(f"CREATE TABLE {qualified_table(table['name'])} (")
        definitions = []
        for name, data_type, annotation in columns:
            if name == "id":
                definition = f"    {sql_identifier(name)} UUID PRIMARY KEY DEFAULT gen_random_uuid()"
            elif name == "created_at":
                definition = f"    {sql_identifier(name)} TIMESTAMPTZ NOT NULL DEFAULT now()"
            elif name == "updated_at":
                definition = f"    {sql_identifier(name)} TIMESTAMPTZ NOT NULL DEFAULT now()"
            else:
                definition = f"    {sql_identifier(name)} {data_type}"
                is_required_fk = "FK" in annotation and "facult" not in annotation.lower()
                if "UQ" in annotation or is_required_fk:
                    definition += " NOT NULL"
            definitions.append(definition)
        lines.append(",\n".join(definitions))
        lines.append(");")
        lines.append(f"COMMENT ON TABLE {qualified_table(table['name'])} IS 'Table métier HAUQE Certif';")
        lines.append("")

    for table, column in unique_keys:
        constraint = short_code("uq", table, column)
        lines.append(
            f"ALTER TABLE {qualified_table(table)} ADD CONSTRAINT {sql_identifier(constraint)} "
            f"UNIQUE ({sql_identifier(column)});"
        )
    lines.append("")

    valid_tables = {table["name"] for table in tables}
    for table, column, target_table, target_column in foreign_keys:
        if target_table not in valid_tables:
            continue
        constraint = short_code("fk", table, column)
        lines.append(
            f"ALTER TABLE {qualified_table(table)} ADD CONSTRAINT {sql_identifier(constraint)} "
            f"FOREIGN KEY ({sql_identifier(column)}) REFERENCES "
            f"{qualified_table(target_table)} ({sql_identifier(target_column)}) "
            "ON UPDATE CASCADE ON DELETE RESTRICT;"
        )
        index = short_code("ix", table, column)
        lines.append(
            f"CREATE INDEX {sql_identifier(index)} ON {qualified_table(table)} ({sql_identifier(column)});"
        )

    indexed_tables = {table for table, _, _, _ in foreign_keys}
    for table in tables:
        table_name = table["name"]
        if table_name in indexed_tables:
            continue
        column_names = [column[0] for column in table["columns"]]
        index_column = "code" if "code" in column_names else "created_at"
        index = short_code("ix", table_name, index_column)
        lines.append(
            f"CREATE INDEX {sql_identifier(index)} ON {qualified_table(table_name)} "
            f"({sql_identifier(index_column)});"
        )

    lines.extend([
        "",
        "-- Mise à jour automatique de updated_at",
        "CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$",
        "BEGIN",
        "    NEW.updated_at = now();",
        "    RETURN NEW;",
        "END;",
        "$$ LANGUAGE plpgsql;",
        "",
    ])
    for table in tables:
        # Some PowerDesigner DBMS profiles enforce a trigger code shorter than
        # the nominal 31-character object-name limit.
        trigger = short_code("trg", table["name"], "upd", max_length=28)
        lines.append(
            f"CREATE TRIGGER {sql_identifier(trigger)} BEFORE UPDATE ON {qualified_table(table['name'])} "
            "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"tables={len(tables)} foreign_keys={len(foreign_keys)} unique_keys={len(unique_keys)}")
    print(OUTPUT)


if __name__ == "__main__":
    build()
