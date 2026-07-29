from __future__ import annotations

import json
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.scoring_repository import ScoringRepository
from app.rules.business_rule_resolver import resolve_business_rule
from app.rules.collecte_completeness import (
    COUNT_RESOURCES,
    selectable_fields,
    validate_parameters,
)
from app.schemas.institutional_setup import (
    CompletenessCatalogResponse,
    CompletenessValidateResponse,
    InstitutionalCountOption,
    InstitutionalFieldOption,
    InstitutionalReadinessResponse,
    ReadinessModel,
    ReadinessRule,
)


class InstitutionalSetupService:
    @staticmethod
    def _model_rule(model) -> dict:
        if not model or not model.regle_calcul:
            return {}
        try:
            data = json.loads(model.regle_calcul)
        except (TypeError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    async def _model_readiness(
        db: AsyncSession,
        object_type: str,
    ) -> ReadinessModel:
        model = await ScoringRepository.active_model(
            db,
            object_type,
        )
        if model is None:
            return ReadinessModel(
                ready=False,
                object_type=object_type,
            )

        weights = await ScoringRepository.list_weights(
            db,
            model.id,
            active_only=True,
        )
        total = sum(
            (Decimal(str(weight.valeur or 0)) for weight in weights),
            Decimal("0"),
        )
        rule = InstitutionalSetupService._model_rule(model)

        return ReadinessModel(
            ready=True,
            id=model.id,
            code=model.code,
            version=model.version,
            object_type=object_type,
            calculation_mode=rule.get("calculation_mode"),
            active_weights=len(weights),
            total_weight=float(total),
            approval_reference=model.reference_approbation,
            status=model.statut,
        )

    @staticmethod
    async def readiness(
        db: AsyncSession,
    ) -> InstitutionalReadinessResponse:
        rule = await resolve_business_rule(
            db,
            "COLLECTE_COMPLETUDE",
        )

        collecte = ReadinessRule(
            ready=rule is not None,
            id=rule.id if rule else None,
            version=rule.version if rule else None,
            effective_from=rule.date_debut_effet if rule else None,
            approval_reference=rule.reference_approbation if rule else None,
            status=rule.statut if rule else None,
        )

        classification = await InstitutionalSetupService._model_readiness(
            db,
            "CLASSIFICATION_ENTREPRISE",
        )
        infc = await InstitutionalSetupService._model_readiness(
            db,
            "INFC",
        )

        blockers = []
        if not collecte.ready:
            blockers.append("Aucune version publiée active de COLLECTE_COMPLETUDE.")
        if not classification.ready:
            blockers.append("Aucun modèle publié actif CLASSIFICATION_ENTREPRISE.")
        if not infc.ready:
            blockers.append("Aucun modèle publié actif INFC.")

        return InstitutionalReadinessResponse(
            collecte_completude=collecte,
            classification_entreprise=classification,
            infc=infc,
            ready_for_collecte_submission=collecte.ready,
            ready_for_classification_tests=classification.ready,
            ready_for_infc_score_tests=infc.ready,
            blockers=blockers,
        )

    @staticmethod
    def completeness_catalog() -> CompletenessCatalogResponse:
        return CompletenessCatalogResponse(
            fields=[
                InstitutionalFieldOption(**row)
                for row in selectable_fields()
            ],
            count_resources=[
                InstitutionalCountOption(
                    code=code,
                    label=meta["label"],
                    description=meta["description"],
                )
                for code, meta in COUNT_RESOURCES.items()
            ],
        )

    @staticmethod
    def validate_completeness(
        params: dict,
    ) -> CompletenessValidateResponse:
        result = validate_parameters(params)
        return CompletenessValidateResponse(
            valid=not result.errors,
            normalized=result.normalized,
            errors=result.errors,
            warnings=result.warnings,
        )
