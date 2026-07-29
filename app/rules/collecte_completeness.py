from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certification_declaree import CertificationDeclaree
from app.models.document import Document
from app.models.fiche_collecte import FicheCollecte
from app.models.offre_declaree import OffreDeclaree


SYSTEM_FIELDS = {
    "id",
    "mission_id",
    "numero_revision",
    "statut",
    "taux_completude",
    "collecte_par_id",
    "collecte_at",
    "soumise_at",
    "created_at",
    "updated_at",
}

FIELD_LABELS = {
    "entreprise_id": "Entreprise liée",
    "version_formulaire": "Version du formulaire",
    "consentement_obtenu": "Consentement obtenu",
    "nom_declarant": "Nom du déclarant",
    "fonction_declarant": "Fonction du déclarant",
    "telephone_declarant": "Téléphone du déclarant",
    "email_declarant": "Courriel du déclarant",
    "signature_declarant": "Signature du déclarant",
    "observations": "Observations",
}

COUNT_RESOURCES = {
    "DOCUMENTS": {
        "label": "Documents rattachés à la fiche",
        "description": "Documents actifs dont la ressource est FICHE_COLLECTE.",
    },
    "OFFRES_DECLAREES": {
        "label": "Offres déclarées",
        "description": "Nombre d'offres déclarées liées à la fiche.",
    },
    "CERTIFICATIONS_DECLAREES": {
        "label": "Certifications déclarées",
        "description": "Nombre de certifications déclarées liées à la fiche.",
    },
}


@dataclass
class CompletenessValidation:
    normalized: dict[str, Any]
    errors: list[str]
    warnings: list[str]


def selectable_fields() -> list[dict[str, Any]]:
    result = []
    for column in FicheCollecte.__table__.columns:
        name = column.name
        if name in SYSTEM_FIELDS:
            continue
        result.append(
            {
                "name": name,
                "label": FIELD_LABELS.get(
                    name,
                    name.replace("_", " ").strip().capitalize(),
                ),
                "nullable": bool(column.nullable),
                "type": column.type.__class__.__name__,
            }
        )
    return result


def _legacy_requirements(params: dict[str, Any]) -> list[dict[str, Any]]:
    requirements = []
    required = params.get("required_fields") or []
    if not isinstance(required, list):
        return requirements

    for expression in required:
        if not isinstance(expression, str) or not expression.strip():
            continue
        fields = [value.strip() for value in expression.split("|") if value.strip()]
        if not fields:
            continue
        requirements.append(
            {
                "type": "FIELD",
                "label": " / ".join(fields),
                "fields": fields,
                "match": "ANY" if len(fields) > 1 else "ALL",
            }
        )
    return requirements


def validate_parameters(params: dict[str, Any]) -> CompletenessValidation:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(params, dict):
        return CompletenessValidation(
            normalized={},
            errors=["Les paramètres doivent être un objet JSON."],
            warnings=[],
        )

    allowed_fields = {row["name"] for row in selectable_fields()}
    raw_requirements = params.get("requirements")
    if raw_requirements is None:
        raw_requirements = _legacy_requirements(params)

    if not isinstance(raw_requirements, list):
        errors.append("requirements doit être une liste.")
        raw_requirements = []

    normalized_requirements: list[dict[str, Any]] = []

    for index, raw in enumerate(raw_requirements, start=1):
        if not isinstance(raw, dict):
            errors.append(f"Exigence {index} : un objet est attendu.")
            continue

        kind = str(raw.get("type", "")).strip().upper()
        label = str(raw.get("label", "")).strip() or f"Exigence {index}"

        if kind == "FIELD":
            fields = raw.get("fields") or []
            if isinstance(fields, str):
                fields = [fields]
            fields = [str(value).strip() for value in fields if str(value).strip()]
            unknown = [field for field in fields if field not in allowed_fields]

            if not fields:
                errors.append(f"{label} : au moins un champ est requis.")
                continue
            if unknown:
                errors.append(f"{label} : champ(s) inconnu(s) : {', '.join(unknown)}.")
                continue

            match = str(raw.get("match", "ALL")).strip().upper()
            if match not in {"ANY", "ALL"}:
                errors.append(f"{label} : match doit être ANY ou ALL.")
                continue

            normalized_requirements.append(
                {
                    "type": "FIELD",
                    "label": label,
                    "fields": fields,
                    "match": match,
                }
            )
            continue

        if kind == "COUNT":
            resource = str(raw.get("resource", "")).strip().upper()
            if resource not in COUNT_RESOURCES:
                errors.append(f"{label} : ressource de comptage inconnue.")
                continue

            try:
                minimum = int(raw.get("minimum", 1))
            except (TypeError, ValueError):
                errors.append(f"{label} : minimum doit être un entier.")
                continue

            if minimum < 1:
                errors.append(f"{label} : minimum doit être supérieur ou égal à 1.")
                continue

            normalized_requirements.append(
                {
                    "type": "COUNT",
                    "label": label,
                    "resource": resource,
                    "minimum": minimum,
                }
            )
            continue

        errors.append(f"{label} : type d'exigence non supporté ({kind or 'vide'}).")

    try:
        minimum_rate = Decimal(str(params.get("minimum_submission_rate", 100)))
    except Exception:
        errors.append("minimum_submission_rate doit être un nombre.")
        minimum_rate = Decimal("100")

    if minimum_rate < 0 or minimum_rate > 100:
        errors.append("minimum_submission_rate doit être compris entre 0 et 100.")

    if not normalized_requirements:
        errors.append("Au moins une exigence de complétude doit être définie.")

    if minimum_rate < 100:
        warnings.append(
            "Un minimum inférieur à 100 % autorise la soumission avec certaines exigences non satisfaites."
        )

    normalized = dict(params)
    normalized["requirements"] = normalized_requirements
    normalized["minimum_submission_rate"] = float(minimum_rate)
    normalized.pop("required_fields", None)

    return CompletenessValidation(
        normalized=normalized,
        errors=errors,
        warnings=warnings,
    )


def _field_is_fulfilled(fiche: FicheCollecte, field: str) -> bool:
    if not hasattr(fiche, field):
        return False

    value = getattr(fiche, field)

    if isinstance(value, bool):
        if field == "consentement_obtenu":
            return value is True
        return value is not None

    return value is not None and bool(str(value).strip())


async def _count_resource(db: AsyncSession, fiche: FicheCollecte, resource: str) -> int:
    resource = resource.upper()

    if resource == "OFFRES_DECLAREES":
        value = await db.scalar(
            select(func.count(OffreDeclaree.id)).where(
                OffreDeclaree.fiche_collecte_id == fiche.id
            )
        )
        return int(value or 0)

    if resource == "CERTIFICATIONS_DECLAREES":
        value = await db.scalar(
            select(func.count(CertificationDeclaree.id)).where(
                CertificationDeclaree.fiche_collecte_id == fiche.id
            )
        )
        return int(value or 0)

    if resource == "DOCUMENTS":
        value = await db.scalar(
            select(func.count(Document.id)).where(
                Document.ressource_type == "FICHE_COLLECTE",
                Document.ressource_id == fiche.id,
                or_(Document.statut.is_(None), Document.statut == "ACTIF"),
            )
        )
        return int(value or 0)

    return 0


async def evaluate(
    db: AsyncSession,
    fiche: FicheCollecte,
    params: dict[str, Any],
) -> dict[str, Any]:
    validation = validate_parameters(params)

    if validation.errors:
        raise ValueError(" | ".join(validation.errors))

    details = []
    fulfilled = 0

    for requirement in validation.normalized["requirements"]:
        kind = requirement["type"]
        ok = False
        actual: Any = None

        if kind == "FIELD":
            values = [
                _field_is_fulfilled(fiche, field)
                for field in requirement["fields"]
            ]
            ok = any(values) if requirement["match"] == "ANY" else all(values)
            actual = dict(zip(requirement["fields"], values))

        elif kind == "COUNT":
            count = await _count_resource(db, fiche, requirement["resource"])
            ok = count >= requirement["minimum"]
            actual = count

        if ok:
            fulfilled += 1

        details.append(
            {
                "label": requirement["label"],
                "type": kind,
                "fulfilled": ok,
                "actual": actual,
            }
        )

    total = len(details)
    rate = (
        Decimal(fulfilled * 100) / Decimal(total)
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "rate": rate,
        "fulfilled": fulfilled,
        "total": total,
        "details": details,
        "normalized": validation.normalized,
    }
