"""Moteur transactionnel de codification HAUQE / BNEC.

Les modèles sont des règles métier publiées dans ``regles_metier``. Le moteur
produit un aperçu sans réservation, puis réserve la séquence définitive dans la
transaction d'intégration grâce à un verrou consultatif PostgreSQL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.element_integration import ElementIntegration
from app.models.regle_metier import RegleMetier
from app.repositories.validation_bnec_repository import ValidationBnecRepository
from app.rules.codification import (
    build_scope_key,
    logical_code_for_object,
    render_code,
    spec_from_parameters,
    validate_codification_parameters,
)


@dataclass(slots=True, frozen=True)
class CodificationModelInfo:
    rule_id: UUID
    logical_code: str
    model_label: str
    version: str | None
    format_code: str
    approval_reference: str | None
    sequence_scope: str


@dataclass(slots=True, frozen=True)
class CodificationAssignment:
    rule_id: UUID
    logical_code: str
    model_label: str
    version: str | None
    format_code: str
    scope_key: str
    sequence: int
    segments: dict[str, str]
    code: str
    approval_reference: str | None
    sequence_scope: str


class CodificationService:
    @staticmethod
    def model_display_label(rule: RegleMetier, object_type: str) -> str:
        """Retourne un libellé métier cohérent avec l'objet codifié.

        Les versions déjà publiées restent immuables. Lorsqu'un brouillon a été
        créé en changeant l'objet sans modifier l'ancien libellé par défaut,
        l'intégration affiche néanmoins le bon type de modèle afin d'éviter une
        confusion entre ENTREPRISE et CERTIFICATION.
        """

        object_type = object_type.strip().upper()
        custom = (rule.libelle or "").strip()
        normalized = custom.upper()
        if object_type == "CERTIFICATION":
            if not custom or ("ENTREPRISE" in normalized and "CERTIF" not in normalized):
                return "Modèle de codification des certifications"
        elif object_type == "ENTREPRISE":
            if not custom or ("CERTIF" in normalized and "ENTREPRISE" not in normalized):
                return "Modèle de codification des entreprises BNEC"
        return custom or logical_code_for_object(object_type)

    @staticmethod
    async def active_rule(
        db: AsyncSession,
        object_type: str,
    ) -> RegleMetier | None:
        return await ValidationBnecRepository.active_codification_rule(
            db,
            logical_code_for_object(object_type),
        )

    @staticmethod
    async def require_active_rule(
        db: AsyncSession,
        object_type: str,
    ) -> RegleMetier:
        rule = await CodificationService.active_rule(db, object_type)
        if rule is None:
            raise ValueError(
                "Aucun modèle de codification publié pour l'objet "
                f"{object_type.strip().upper()}."
            )
        validation = validate_codification_parameters(
            logical_code_for_object(object_type),
            rule.parametres or {},
        )
        if validation.errors:
            raise ValueError(
                "Le modèle de codification publié est invalide : "
                + " | ".join(validation.errors)
            )
        return rule

    @staticmethod
    async def describe_active_rule(
        db: AsyncSession,
        object_type: str,
    ) -> CodificationModelInfo:
        """Décrit un modèle publié sans exiger la résolution de ses variables.

        Cette méthode permet à l'interface d'afficher correctement « modèle
        publié et actif » même lorsqu'un autre référentiel métier (par exemple
        une norme ambiguë) empêche encore le calcul de l'aperçu du code.
        """

        rule = await CodificationService.require_active_rule(db, object_type)
        spec = spec_from_parameters(rule.parametres or {})
        return CodificationModelInfo(
            rule_id=rule.id,
            logical_code=logical_code_for_object(spec.objet),
            model_label=CodificationService.model_display_label(rule, spec.objet),
            version=rule.version,
            format_code=spec.format_code,
            approval_reference=rule.reference_approbation,
            sequence_scope=spec.sequence_portee,
        )

    @staticmethod
    def _assignment(
        rule: RegleMetier,
        context: Mapping[str, Any],
        sequence: int,
    ) -> CodificationAssignment:
        spec = spec_from_parameters(rule.parametres or {})
        scope_key = build_scope_key(spec, context)
        code, segments = render_code(spec, context, sequence)
        logical_code = logical_code_for_object(spec.objet)
        return CodificationAssignment(
            rule_id=rule.id,
            logical_code=logical_code,
            model_label=CodificationService.model_display_label(rule, spec.objet),
            version=rule.version,
            format_code=spec.format_code,
            scope_key=scope_key,
            sequence=sequence,
            segments=segments,
            code=code,
            approval_reference=rule.reference_approbation,
            sequence_scope=spec.sequence_portee,
        )

    @staticmethod
    async def preview(
        db: AsyncSession,
        *,
        object_type: str,
        context: Mapping[str, Any],
        excluded_codes: set[str] | None = None,
    ) -> CodificationAssignment:
        rule = await CodificationService.require_active_rule(db, object_type)
        spec = spec_from_parameters(rule.parametres or {})
        scope_key = build_scope_key(spec, context)
        current = await ValidationBnecRepository.max_codification_sequence(
            db,
            rule_id=rule.id,
            scope_key=scope_key,
        )
        sequence = current + 1
        excluded_codes = excluded_codes or set()
        # L'aperçu n'est pas réservé : on évite les collisions déjà présentes
        # ainsi que les codes déjà proposés dans le même plan d'intégration.
        for _ in range(10000):
            assignment = CodificationService._assignment(rule, context, sequence)
            if assignment.code in excluded_codes:
                sequence += 1
                continue
            exists = await ValidationBnecRepository.generated_code_exists(
                db,
                object_type=object_type,
                code=assignment.code,
            )
            if not exists:
                return assignment
            sequence += 1
        raise ValueError("Impossible de calculer une séquence de codification disponible.")

    @staticmethod
    async def reserve(
        db: AsyncSession,
        *,
        object_type: str,
        context: Mapping[str, Any],
        element: ElementIntegration,
    ) -> CodificationAssignment:
        rule = await CodificationService.require_active_rule(db, object_type)
        spec = spec_from_parameters(rule.parametres or {})
        scope_key = build_scope_key(spec, context)
        lock_key = f"HAUQE:BNEC:CODIFICATION:{rule.id}:{scope_key}"
        await ValidationBnecRepository.lock_codification_scope(db, lock_key)
        current = await ValidationBnecRepository.max_codification_sequence(
            db,
            rule_id=rule.id,
            scope_key=scope_key,
        )
        sequence = current + 1
        for _ in range(10000):
            assignment = CodificationService._assignment(rule, context, sequence)
            exists = await ValidationBnecRepository.generated_code_exists(
                db,
                object_type=object_type,
                code=assignment.code,
                exclude_element_id=element.id,
            )
            if not exists:
                CodificationService.apply_snapshot(element, assignment)
                return assignment
            sequence += 1
        raise ValueError("Impossible de réserver une séquence de codification disponible.")

    @staticmethod
    def apply_snapshot(
        element: ElementIntegration,
        assignment: CodificationAssignment,
    ) -> None:
        element.code_genere = assignment.code
        element.codification_regle_id = assignment.rule_id
        element.codification_logical_code = assignment.logical_code
        element.codification_version = assignment.version
        element.codification_format = assignment.format_code
        element.codification_scope_key = assignment.scope_key
        element.codification_sequence = assignment.sequence
        element.codification_segments = assignment.segments
