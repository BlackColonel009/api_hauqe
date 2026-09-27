"""Validation de la matrice de classement SNCC publiée."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from app.rules.sncc_reference import (
    SNCC_ADMIN_STATUSES,
    SNCC_CLASSES,
    SNCC_RISK_LEVELS,
)


def _decimal(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def validate_sncc_matrix_parameters(
    parameters: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Normalise la matrice et retourne les erreurs de publication.

    Chaque classe doit être définie une seule fois et couvrir la plage 0–100.
    Les seuils restent institutionnels : aucun n'est défini par le backend.
    """
    source = parameters.get("rows", parameters.get("matrice", []))
    errors: list[str] = []
    normalized_rows: list[dict[str, Any]] = []
    if not isinstance(source, list) or not source:
        return {}, ["La matrice SNCC doit contenir au moins une ligne."]

    for position, item in enumerate(source, start=1):
        if not isinstance(item, dict):
            errors.append(f"Ligne SNCC {position} invalide.")
            continue
        minimum = _decimal(item.get("min", item.get("score_min")))
        maximum = _decimal(item.get("max", item.get("score_max")))
        classe = str(item.get("classe", item.get("class_code", ""))).strip().upper()
        statut = str(item.get("statut_administratif", item.get("statut", ""))).strip().upper()
        risque = str(item.get("niveau_risque", item.get("risque", ""))).strip().upper()
        if minimum is None or maximum is None:
            errors.append(f"Ligne SNCC {position} : bornes min et max obligatoires.")
            continue
        if minimum < 0 or maximum > 100 or minimum > maximum:
            errors.append(f"Ligne SNCC {position} : plage de score incohérente.")
        if classe not in SNCC_CLASSES:
            errors.append(f"Ligne SNCC {position} : classe invalide ({classe or 'vide'}).")
        if statut not in SNCC_ADMIN_STATUSES:
            errors.append(f"Ligne SNCC {position} : statut invalide ({statut or 'vide'}).")
        if risque not in SNCC_RISK_LEVELS:
            errors.append(f"Ligne SNCC {position} : risque invalide ({risque or 'vide'}).")
        normalized_rows.append(
            {
                "min": float(minimum),
                "max": float(maximum),
                "classe": classe,
                "statut_administratif": statut,
                "niveau_risque": risque,
            }
        )

    if errors:
        return {}, errors
    classes = [item["classe"] for item in normalized_rows]
    if set(classes) != set(SNCC_CLASSES) or len(classes) != len(SNCC_CLASSES):
        errors.append("La matrice doit définir une ligne unique pour A+, A, B, C et D.")

    ordered = sorted(normalized_rows, key=lambda item: item["min"])
    if ordered and ordered[0]["min"] != 0:
        errors.append("La première plage SNCC doit commencer à 0.")
    if ordered and ordered[-1]["max"] != 100:
        errors.append("La dernière plage SNCC doit se terminer à 100.")
    tolerance = Decimal("0.01")
    for previous, current in zip(ordered, ordered[1:]):
        previous_maximum = Decimal(str(previous["max"]))
        current_minimum = Decimal(str(current["min"]))
        if current_minimum <= previous_maximum:
            errors.append("Les plages SNCC se chevauchent.")
        elif current_minimum - previous_maximum > tolerance:
            errors.append("Les plages SNCC présentent un intervalle non couvert.")

    return {"rows": ordered}, errors
