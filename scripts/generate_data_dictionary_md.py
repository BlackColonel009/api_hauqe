from __future__ import annotations

from pathlib import Path

from generate_powerdesigner_sql import ROOT, infer_type, parse_model


OUTPUT = ROOT / "DICTIONNAIRE_DONNEES_66_TABLES.md"


def build() -> None:
    tables, foreign_keys, unique_keys = parse_model()
    fk_map = {(table, column): target for table, column, target, _ in foreign_keys}
    uq_set = set(unique_keys)

    lines = [
        "# Dictionnaire de données — HAUQE Certif",
        "",
        "**Version :** 0.3  ",
        "**Cible :** PostgreSQL / FastAPI / PowerDesigner  ",
        f"**Nombre de tables :** {len(tables)}  ",
        f"**Nombre de clés étrangères :** {len(foreign_keys)}  ",
        "",
        "Ce document reprend exactement les tables et colonnes générées dans "
        "`output/sql/HAUQE_CERTIF_POWERDESIGNER.sql`.",
        "",
        "Abréviations : `PK` = clé primaire, `FK` = clé étrangère, "
        "`UQ` = contrainte d’unicité, `NN` = obligatoire.",
        "",
    ]

    total_columns = 0
    for number, table in enumerate(tables, start=1):
        table_name = table["name"]
        columns = list(table["columns"])
        existing = {name for name, _, _ in columns}
        if "id" not in existing:
            columns.insert(0, ("id", "UUID", "PK"))
        columns.extend([
            ("created_at", "TIMESTAMPTZ", "NN, valeur par défaut `now()`"),
            ("updated_at", "TIMESTAMPTZ", "NN, valeur par défaut `now()`"),
        ])
        total_columns += len(columns)

        lines.extend([
            f"## {number}. `{table_name}`",
            "",
            "| Colonne | Type PostgreSQL | Contraintes / relation |",
            "|---|---|---|",
        ])

        for name, data_type, annotation in columns:
            constraints = []
            if name == "id":
                constraints.extend(["PK", "NN", "`gen_random_uuid()`"])
            if (table_name, name) in uq_set:
                constraints.extend(["UQ", "NN"])
            target = fk_map.get((table_name, name))
            if target:
                constraints.append(f"FK → `{target}.id`")
                if "facult" not in annotation.lower():
                    constraints.append("NN")
                else:
                    constraints.append("facultatif")
            if name in {"created_at", "updated_at"}:
                constraints.extend(["NN", "`now()`"])
            detail = ", ".join(dict.fromkeys(constraints)) or "—"
            lines.append(f"| `{name}` | `{data_type}` | {detail} |")
        lines.append("")

    lines.extend([
        "## Synthèse",
        "",
        f"- Tables : **{len(tables)}**",
        f"- Colonnes totales : **{total_columns}**",
        f"- Clés étrangères : **{len(foreign_keys)}**",
        f"- Contraintes d’unicité : **{len(unique_keys)}**",
        "- Champs techniques automatiques : `created_at` et `updated_at` sur chaque table.",
        "",
    ])
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"tables={len(tables)} columns={total_columns} foreign_keys={len(foreign_keys)}")
    print(OUTPUT)


if __name__ == "__main__":
    build()
