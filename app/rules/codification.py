"""Règles de codification institutionnelle HAUQE / BNEC.

Ce module ne dépend pas de FastAPI. Il normalise et valide les modèles
stockés dans ``regles_metier.parametres`` puis résout les variables lors de
l'intégration BNEC.

Un modèle est versionné par le moteur de gouvernance. Exemple :

    CODIFICATION_BNEC_ENTREPRISE
    {HAUQE}-{BNEC}-{PAYS}-{REGION}-{ANNEE4}-{SEQ4}

Les codes publiés sont immuables. Une nouvelle structure impose une nouvelle
version de règle, sans réécrire les identifiants déjà attribués.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import re
import unicodedata
from typing import Any, Mapping


CODIFICATION_PREFIX = "CODIFICATION_BNEC_"
SUPPORTED_OBJECTS = {
    "ENTREPRISE",
    "CERTIFICATION",
}

ALLOWED_TOKENS = {
    "HAUQE",
    "BNEC",
    "PAYS",
    "REGION",
    "ZONE",
    "ANNEE",
    "ANNEE2",
    "ANNEE4",
    "MOIS",
    "TYPE_OBJET",
    "CODE_ENTREPRISE",
    "ENTREPRISE",
    "CERTIF",
    "ORGANISME",
    "NORME",
    "SECTEUR",
    "SEQ3",
    "SEQ4",
    "SEQ5",
    "SEQUENCE",
}

SEQUENCE_TOKENS = {"SEQ3", "SEQ4", "SEQ5", "SEQUENCE"}
TOKEN_PATTERN = re.compile(r"\{([A-Z0-9_]+)\}")

SEQUENCE_SCOPES = {
    "GLOBALE",
    "ANNUELLE",
    "REGIONALE",
    "PAR_ENTREPRISE",
    "ANNUELLE_PAR_ENTREPRISE",
    "ANNUELLE_REGIONALE",
}

SEQUENCE_RESETS = {"JAMAIS", "ANNUELLE"}


@dataclass(slots=True)
class CodificationValidation:
    normalized: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class CodificationSpec:
    objet: str
    format_code: str
    separateur: str
    sequence_longueur: int
    sequence_portee: str
    sequence_reinitialisation: str
    constantes: dict[str, str]
    libelle_modele: str | None = None


def normalize_object(value: Any) -> str:
    return str(value or "").strip().upper().replace(" ", "_")


def logical_code_for_object(object_type: str) -> str:
    return f"{CODIFICATION_PREFIX}{normalize_object(object_type)}"


def object_from_logical_code(logical_code: str) -> str | None:
    logical = str(logical_code or "").strip().upper()
    if not logical.startswith(CODIFICATION_PREFIX):
        return None
    return logical.removeprefix(CODIFICATION_PREFIX) or None


def normalize_segment(value: Any, *, fallback: str = "") -> str:
    """Transforme une valeur métier en segment de code stable.

    - accents retirés ;
    - majuscules ;
    - caractères non alphanumériques supprimés ;
    - valeur vide remplacée par ``fallback``.
    """

    raw = str(value or "").strip()
    if not raw:
        raw = fallback
    ascii_value = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]+", "", ascii_value.upper())


def extract_tokens(pattern: str) -> list[str]:
    return TOKEN_PATTERN.findall(str(pattern or "").upper())


def sequence_token(pattern: str) -> str | None:
    tokens = extract_tokens(pattern)
    found = [token for token in tokens if token in SEQUENCE_TOKENS]
    return found[0] if len(found) == 1 else None


def sequence_length(spec_or_params: CodificationSpec | Mapping[str, Any]) -> int:
    if isinstance(spec_or_params, CodificationSpec):
        return spec_or_params.sequence_longueur
    try:
        return int(spec_or_params.get("sequence_longueur") or 4)
    except (TypeError, ValueError):
        return 4


def validate_codification_parameters(
    logical_code: str,
    parameters: Mapping[str, Any] | None,
) -> CodificationValidation:
    params = dict(parameters or {})
    result = CodificationValidation()

    object_from_code = object_from_logical_code(logical_code)
    object_type = normalize_object(params.get("objet") or object_from_code)
    if object_from_code and object_type and object_type != object_from_code:
        result.errors.append(
            "L'objet du modèle ne correspond pas à son code logique : "
            f"{object_from_code} attendu, {object_type} reçu."
        )
    if object_type not in SUPPORTED_OBJECTS:
        result.errors.append(
            "Objet codifié invalide. Valeurs prises en charge : "
            + ", ".join(sorted(SUPPORTED_OBJECTS))
            + "."
        )

    pattern = str(params.get("format") or params.get("format_code") or "").strip().upper()
    if not pattern:
        result.errors.append("Le format du code est obligatoire.")
    elif len(pattern) > 255:
        result.errors.append("Le format du code ne peut pas dépasser 255 caractères.")

    separator = str(params.get("separateur") or "-").strip()
    if separator not in {"-", "/", ".", "_"}:
        result.errors.append("Le séparateur doit être -, /, . ou _.")
        separator = "-"

    tokens = extract_tokens(pattern)
    unknown = sorted(set(tokens) - ALLOWED_TOKENS)
    if unknown:
        result.errors.append(
            "Variables inconnues : " + ", ".join(f"{{{token}}}" for token in unknown) + "."
        )

    sequence_tokens = [token for token in tokens if token in SEQUENCE_TOKENS]
    if not sequence_tokens:
        result.errors.append("Le modèle doit contenir une variable de séquence.")
    elif len(sequence_tokens) > 1:
        result.errors.append("Le modèle doit contenir une seule variable de séquence.")

    raw_length = params.get("sequence_longueur") or 4
    try:
        sequence_size = int(raw_length)
    except (TypeError, ValueError):
        sequence_size = 4
        result.errors.append("La longueur de séquence doit être un entier.")
    if sequence_size < 2 or sequence_size > 12:
        result.errors.append("La longueur de séquence doit être comprise entre 2 et 12.")

    if sequence_tokens:
        token = sequence_tokens[0]
        fixed = {"SEQ3": 3, "SEQ4": 4, "SEQ5": 5}.get(token)
        if fixed:
            sequence_size = fixed

    scope = str(params.get("sequence_portee") or "GLOBALE").strip().upper()
    if scope not in SEQUENCE_SCOPES:
        result.errors.append(
            "Portée de séquence invalide : " + ", ".join(sorted(SEQUENCE_SCOPES)) + "."
        )
        scope = "GLOBALE"

    reset = str(params.get("sequence_reinitialisation") or "JAMAIS").strip().upper()
    if reset not in SEQUENCE_RESETS:
        result.errors.append("Réinitialisation invalide : JAMAIS ou ANNUELLE.")
        reset = "JAMAIS"

    raw_constants = params.get("constantes")
    constants: dict[str, str] = {}
    if raw_constants is None:
        raw_constants = {}
    if not isinstance(raw_constants, Mapping):
        result.errors.append("Les constantes doivent être un objet JSON clé/valeur.")
        raw_constants = {}
    for key, value in raw_constants.items():
        normalized_key = normalize_object(key)
        if normalized_key not in ALLOWED_TOKENS:
            result.warnings.append(f"Constante ignorée : {normalized_key}.")
            continue
        constants[normalized_key] = normalize_segment(value)

    defaults = {
        "HAUQE": "HAUQE",
        "BNEC": "BNEC",
        "PAYS": "TG",
        "CERTIF": "CERT",
    }
    for key, value in defaults.items():
        constants.setdefault(key, value)

    if object_type == "CERTIFICATION" and "CODE_ENTREPRISE" not in tokens:
        result.warnings.append(
            "Le modèle CERTIFICATION ne contient pas {CODE_ENTREPRISE}; "
            "les codes ne seront pas directement rattachables à l'entreprise."
        )

    result.normalized = {
        "_logical_code": str(logical_code or "").strip().upper(),
        "objet": object_type,
        "format": pattern,
        "separateur": separator,
        "sequence_longueur": sequence_size,
        "sequence_portee": scope,
        "sequence_reinitialisation": reset,
        "constantes": constants,
        "modele_par_defaut": bool(params.get("modele_par_defaut", True)),
        "variables_autorisees": sorted(ALLOWED_TOKENS),
    }
    if params.get("libelle_modele"):
        result.normalized["libelle_modele"] = str(params["libelle_modele"]).strip()

    return result


def spec_from_parameters(parameters: Mapping[str, Any]) -> CodificationSpec:
    return CodificationSpec(
        objet=normalize_object(parameters.get("objet")),
        format_code=str(parameters.get("format") or "").strip().upper(),
        separateur=str(parameters.get("separateur") or "-"),
        sequence_longueur=sequence_length(parameters),
        sequence_portee=str(parameters.get("sequence_portee") or "GLOBALE").upper(),
        sequence_reinitialisation=str(
            parameters.get("sequence_reinitialisation") or "JAMAIS"
        ).upper(),
        constantes={
            normalize_object(key): normalize_segment(value)
            for key, value in dict(parameters.get("constantes") or {}).items()
        },
        libelle_modele=(
            str(parameters.get("libelle_modele")).strip()
            if parameters.get("libelle_modele")
            else None
        ),
    )


def build_scope_key(
    spec: CodificationSpec,
    context: Mapping[str, Any],
    *,
    today: date | None = None,
) -> str:
    today = today or date.today()
    region = normalize_segment(context.get("REGION"), fallback="SANSREGION")
    enterprise = normalize_segment(
        context.get("CODE_ENTREPRISE") or context.get("ENTREPRISE_ID"),
        fallback="SANSENTREPRISE",
    )

    if spec.sequence_portee == "GLOBALE":
        parts = [spec.objet, "GLOBAL"]
    elif spec.sequence_portee == "ANNUELLE":
        parts = [spec.objet, str(today.year)]
    elif spec.sequence_portee == "REGIONALE":
        parts = [spec.objet, region]
    elif spec.sequence_portee == "PAR_ENTREPRISE":
        parts = [spec.objet, enterprise]
    elif spec.sequence_portee == "ANNUELLE_PAR_ENTREPRISE":
        parts = [spec.objet, str(today.year), enterprise]
    elif spec.sequence_portee == "ANNUELLE_REGIONALE":
        parts = [spec.objet, str(today.year), region]
    else:
        parts = [spec.objet, "GLOBAL"]

    if spec.sequence_reinitialisation == "ANNUELLE" and str(today.year) not in parts:
        parts.append(str(today.year))
    return ":".join(parts)


def render_code(
    spec: CodificationSpec,
    context: Mapping[str, Any],
    sequence: int,
    *,
    today: date | None = None,
) -> tuple[str, dict[str, str]]:
    today = today or date.today()
    values: dict[str, str] = dict(spec.constantes)
    values.update(
        {
            "ANNEE": str(today.year),
            "ANNEE2": str(today.year)[-2:],
            "ANNEE4": str(today.year),
            "MOIS": str(today.month).zfill(2),
            "TYPE_OBJET": normalize_segment(spec.objet),
            "SEQUENCE": str(sequence).zfill(spec.sequence_longueur),
            "SEQ3": str(sequence).zfill(3),
            "SEQ4": str(sequence).zfill(4),
            "SEQ5": str(sequence).zfill(5),
        }
    )
    for key, value in context.items():
        values[normalize_object(key)] = normalize_segment(value)

    missing = [token for token in extract_tokens(spec.format_code) if not values.get(token)]
    if missing:
        raise ValueError(
            "Variables de codification non résolues : "
            + ", ".join(f"{{{token}}}" for token in sorted(set(missing)))
            + "."
        )

    rendered = spec.format_code
    for token in extract_tokens(spec.format_code):
        rendered = rendered.replace(f"{{{token}}}", values[token])

    # Le séparateur choisi devient la convention unique, y compris lorsque le
    # brouillon contenait un mélange de -, /, . ou _.
    rendered = re.sub(r"[-/._]+", spec.separateur, rendered)
    rendered = rendered.strip(spec.separateur)
    if len(rendered) > 255:
        raise ValueError("Le code généré dépasse la longueur maximale de 255 caractères.")
    return rendered, {token: values[token] for token in extract_tokens(spec.format_code)}
