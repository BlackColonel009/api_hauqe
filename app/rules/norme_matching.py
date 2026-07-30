"""Rapprochement déterministe des normes déclarées.

Le module ne dépend ni de SQLAlchemy ni de FastAPI afin de pouvoir être testé
isolément. Il normalise les variantes courantes comme ``ISO 9001:2015``,
``ISO-9001-2015`` et ``ISO9001 2015`` sans effectuer de rapprochement flou
silencieux lorsqu'une version reste ambiguë.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


_STANDARD_CODE_RE = re.compile(
    r"(?<![A-Z0-9])"
    r"((?:[A-Z]{2,12}\s*/\s*)*[A-Z]{2,12})"
    r"[\s\-_/]*"
    r"([0-9]{2,6}(?:[\-_/][0-9]{1,6})*)",
    re.IGNORECASE,
)
_VERSION_AFTER_CODE_RE = re.compile(
    r"^\s*(?:(?::|;|,|/|\-|–|—)\s*|\s+)"
    r"((?:19|20)\d{2}|V?\d+(?:\.\d+)*)\b",
    re.IGNORECASE,
)
_SIMPLE_CODE_RE = re.compile(r"^[A-Z][A-Z0-9./_-]{1,63}$", re.IGNORECASE)


@dataclass(slots=True, frozen=True)
class ParsedNormeLabel:
    raw: str
    code: str
    version: str | None
    code_key: str
    full_key: str

    @property
    def creatable(self) -> bool:
        """Indique si le libellé permet une création contrôlée du référentiel."""

        return (
            2 <= len(self.code) <= 255
            and any(character.isalpha() for character in self.code)
            and len(self.raw) <= 255
        )


@dataclass(slots=True, frozen=True)
class NormeCandidateScore:
    score: int
    code_key: str
    version_key: str | None


def ascii_upper(value: str | None) -> str:
    """Supprime les accents et normalise une valeur en majuscules."""

    if not value:
        return ""
    decomposed = unicodedata.normalize("NFKD", str(value))
    without_marks = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return without_marks.upper().strip()


def compact_key(value: str | None) -> str:
    """Clé de comparaison insensible aux espaces et à la ponctuation."""

    return re.sub(r"[^A-Z0-9]+", "", ascii_upper(value))


def normalize_version(value: str | None) -> str | None:
    normalized = compact_key(value)
    if not normalized:
        return None
    return normalized[1:] if normalized.startswith("V") else normalized


def _pretty_prefix(value: str) -> str:
    parts = [part.strip() for part in re.split(r"\s*/\s*", ascii_upper(value))]
    return "/".join(part for part in parts if part)


def _pretty_number(value: str) -> str:
    return re.sub(r"[\s_/]+", "-", ascii_upper(value)).strip("-")


def parse_norme_label(value: str | None) -> ParsedNormeLabel:
    """Extrait un code et une éventuelle version depuis un libellé déclaré."""

    raw = " ".join(str(value or "").strip().split())
    normalized = ascii_upper(raw).replace("–", "-").replace("—", "-")
    match = _STANDARD_CODE_RE.search(normalized)

    version: str | None = None
    if match:
        prefix = _pretty_prefix(match.group(1))
        number = _pretty_number(match.group(2))
        embedded_year = re.fullmatch(r"(.+?)-((?:19|20)\d{2})", number)
        if embedded_year:
            number = embedded_year.group(1)
            version = embedded_year.group(2)
        code = f"{prefix} {number}".strip()
        suffix = normalized[match.end() :]
        version_match = _VERSION_AFTER_CODE_RE.match(suffix)
        if version_match:
            version = version_match.group(1).upper().lstrip("V")
    else:
        cleaned = re.sub(
            r"^(?:NORME|STANDARD|REFERENTIEL)\s*[:\-]?\s*",
            "",
            normalized,
        ).strip()
        if _SIMPLE_CODE_RE.fullmatch(cleaned):
            code = cleaned.replace("_", "-")
        else:
            code = cleaned[:255]

    code = " ".join(code.split()).strip(" -/:;")
    code_key = compact_key(code)
    full_key = compact_key(f"{code}{version or ''}")
    return ParsedNormeLabel(
        raw=raw,
        code=code,
        version=version,
        code_key=code_key,
        full_key=full_key,
    )


def score_norme_candidate(
    declared: ParsedNormeLabel,
    *,
    candidate_code: str | None,
    candidate_name: str | None,
    candidate_version: str | None,
    candidate_status: str | None = None,
) -> NormeCandidateScore:
    """Attribue un score déterministe à une norme du référentiel.

    Un conflit explicite de version annule le rapprochement. Lorsqu'aucune
    version n'est déclarée, plusieurs versions d'un même code conservent le
    même score et seront donc signalées comme ambiguës par le service.
    """

    code_parsed = parse_norme_label(candidate_code)
    name_parsed = parse_norme_label(candidate_name)
    code_key = code_parsed.code_key or name_parsed.code_key
    name_key = compact_key(candidate_name)
    raw_code_key = compact_key(candidate_code)
    version_key = (
        normalize_version(candidate_version)
        or normalize_version(code_parsed.version)
        or normalize_version(name_parsed.version)
    )

    if not declared.code_key:
        return NormeCandidateScore(0, code_key, version_key)

    score = 0
    if declared.code_key == raw_code_key:
        score = max(score, 110)
    if declared.code_key == code_key:
        score = max(score, 105)
    if declared.code_key == name_parsed.code_key:
        score = max(score, 100)
    if declared.full_key and declared.full_key in {
        compact_key(candidate_code),
        compact_key(candidate_name),
        compact_key(f"{candidate_code or ''}{candidate_version or ''}"),
        compact_key(f"{candidate_name or ''}{candidate_version or ''}"),
    }:
        score = max(score, 130)
    if declared.full_key == name_key:
        score = max(score, 125)

    if score == 0:
        return NormeCandidateScore(0, code_key, version_key)

    declared_version = normalize_version(declared.version)
    if declared_version:
        if version_key and version_key != declared_version:
            return NormeCandidateScore(0, code_key, version_key)
        score += 30 if version_key == declared_version else 5

    if ascii_upper(candidate_status) in {"ACTIF", "ACTIVE", "PUBLIE", "VALIDE"}:
        score += 1

    return NormeCandidateScore(score, code_key, version_key)
