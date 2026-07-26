"""
Résolveur commun des règles métier publiées.

Pourquoi ce composant existe
----------------------------
Le MPD impose `regles_metier.code` UNIQUE alors que le même concept métier
doit être versionné. Pour respecter le MPD sans migration :

- `code` reste un identifiant physique unique de version ;
- `parametres["_logical_code"]` contient le code fonctionnel stable ;
- `version` contient la version métier ;
- le résolveur sélectionne la version publiée applicable à la date donnée.

Exemple :
    code physique : VEILLE_SEUILS_EXPIRATION__V1_0
    logical_code : VEILLE_SEUILS_EXPIRATION
    version       : 1.0

Les anciens consommateurs qui cherchent `RegleMetier.code == ...` doivent
être migrés vers `resolve_business_rule`.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.regle_metier import RegleMetier


def rule_logical_code(rule: RegleMetier) -> str:
    if isinstance(rule.parametres, dict):
        logical = str(rule.parametres.get("_logical_code", "")).strip()
        if logical:
            return logical.upper()
    return (rule.code or "").strip().upper()


async def resolve_business_rule(
    db: AsyncSession,
    logical_code: str,
    *,
    effective_date: date | None = None,
) -> RegleMetier | None:
    logical_code = logical_code.strip().upper()
    effective_date = effective_date or date.today()

    result = await db.execute(
        select(RegleMetier)
        .where(RegleMetier.statut == "PUBLIE")
        .order_by(
            RegleMetier.date_debut_effet.desc().nullslast(),
            RegleMetier.created_at.desc(),
        )
    )

    for rule in result.scalars().all():
        if rule_logical_code(rule) != logical_code:
            continue
        if rule.date_debut_effet and rule.date_debut_effet > effective_date:
            continue
        if rule.date_fin_effet and rule.date_fin_effet < effective_date:
            continue
        return rule

    return None
