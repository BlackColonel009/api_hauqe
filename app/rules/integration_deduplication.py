"""Clés déterministes pour regrouper les déclarations identiques.

Le module reste indépendant de SQLAlchemy : il travaille sur tout objet exposant
les attributs attendus. Il sert uniquement à éviter la création de plusieurs
ressources officielles à partir de lignes strictement équivalentes dans une même
fiche validée.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import date, datetime
from decimal import Decimal
import re
import unicodedata
from typing import Any, TypeVar


T = TypeVar("T")


def normalized_text(value: Any) -> str:
    """Normalise une valeur textuelle pour les comparaisons exactes métier."""

    if value is None:
        return ""
    decomposed = unicodedata.normalize("NFKD", str(value))
    without_marks = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", without_marks).strip().upper()


def normalized_scalar(value: Any) -> str:
    """Produit une représentation stable des valeurs non textuelles."""

    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    return normalized_text(value)


def offer_declaration_key(item: Any) -> tuple[str, ...]:
    """Clé d'identité stricte d'une offre déclarée."""

    return (
        normalized_text(getattr(item, "type_offre", None)),
        normalized_text(getattr(item, "nom", None)),
        normalized_text(getattr(item, "description", None)),
        normalized_text(getattr(item, "categorie", None)),
        normalized_scalar(getattr(item, "volume", None)),
        normalized_text(getattr(item, "unite", None)),
        normalized_scalar(getattr(item, "capacite", None)),
        normalized_text(getattr(item, "marches_vises", None)),
        normalized_text(getattr(item, "statut", None)),
    )


def certification_declaration_key(item: Any) -> tuple[str, ...]:
    """Clé d'identité stricte d'une certification déclarée."""

    return (
        normalized_text(getattr(item, "nom_certification", None)),
        normalized_text(getattr(item, "numero", None)),
        normalized_text(getattr(item, "organisme_declare", None)),
        normalized_text(getattr(item, "norme_declaree", None)),
        normalized_text(getattr(item, "portee", None)),
        normalized_scalar(getattr(item, "date_obtention", None)),
        normalized_scalar(getattr(item, "date_expiration", None)),
        normalized_scalar(getattr(item, "copie_disponible", None)),
        normalized_text(getattr(item, "situation_declaree", None)),
    )


def group_identical(
    items: Iterable[T],
    key: Callable[[T], tuple[str, ...]],
) -> list[tuple[T, list[T]]]:
    """Regroupe les éléments strictement identiques en conservant l'ordre.

    Le premier élément du groupe devient la source principale du plan. Les
    suivants sont conservés dans la liste afin que le service puisse les relier
    à la même ressource officielle au moment de l'intégration.
    """

    groups: dict[tuple[str, ...], list[T]] = {}
    order: list[tuple[str, ...]] = []
    for item in items:
        item_key = key(item)
        if item_key not in groups:
            groups[item_key] = []
            order.append(item_key)
        groups[item_key].append(item)
    return [(groups[item_key][0], groups[item_key]) for item_key in order]
