"""
Service métier — Scoring / Classification entreprise / INFC / SNCC.

MOTEUR DE CALCUL
----------------
Le service ne contient aucun seuil métier officiel en dur.

`modeles_scoring.regle_calcul` est un JSON sérialisé dans une colonne TEXT.
Le backend supporte trois modes techniques génériques :

1. DIRECT_SCORE
   - le score est fourni explicitement ;
   - utile lorsque le calcul officiel est externe ou pas encore codé ;
   - les classes/niveaux restent lus dans la règle versionnée.

2. WEIGHTED_AVERAGE_100
   - chaque domaine est exprimé de 0 à 100 ;
   - score = somme(score_domaine * poids) / somme(poids).

3. SUM_DOMAIN_POINTS
   - chaque pondération représente le maximum de points du domaine ;
   - chaque score de domaine doit être compris entre 0 et cette pondération ;
   - score global = somme des points.

Aucun de ces modes n'est proclamé "officiel" par le code.
Le modèle doit être publié avec une référence d'approbation.

Exemple de `regle_calcul` pour une classification :

{
  "calculation_mode": "DIRECT_SCORE",
  "rounding": 2,
  "classes": [
    {"code": "...", "min": 0, "max": 100}
  ]
}

Exemple générique INFC :

{
  "calculation_mode": "SUM_DOMAIN_POINTS",
  "rounding": 2,
  "missing_policy": "REJECT",
  "levels": [
    {"niveau": 1, "min": 0, "max": 100}
  ]
}

Les seuils réels restent à renseigner dans la base lorsque la règle HAUQE
correspondante est confirmée.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
from typing import Any
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.classement_sncc import ClassementSncc
from app.models.classification_entreprise import ClassificationEntreprise
from app.models.modele_scoring import ModeleScoring
from app.models.ponderation_scoring import PonderationScoring
from app.models.resultat_infc import ResultatInfc
from app.repositories.scoring_repository import ScoringRepository
from app.rules.sncc_reference import (
    SNCC_ADMIN_STATUSES,
    SNCC_CLASSES,
    SNCC_RISK_LEVELS,
)
from app.schemas.scoring import (
    EnterpriseClassificationListResponse,
    EnterpriseClassificationResponse,
    InfcResultListResponse,
    InfcResultResponse,
    InfcValidateRequest,
    ScoreComputationPreviewResponse,
    ScoreEvaluationInput,
    ScoringModelCloneRequest,
    ScoringModelCreateRequest,
    ScoringModelPublishRequest,
    ScoringModelResponse,
    ScoringModelRetireRequest,
    ScoringModelUpdateRequest,
    ScoringWeightCreateRequest,
    ScoringWeightResponse,
    ScoringWeightUpdateRequest,
    SnccCloseRequest,
    SnccCreateRequest,
    SnccListResponse,
    SnccReclassifyRequest,
    SnccResponse,
)
from app.services.auth_service import AuthContext


MODEL_OBJECT_ENTERPRISE = "CLASSIFICATION_ENTREPRISE"
MODEL_OBJECT_INFC = "INFC"

SUPPORTED_MODES = {
    "DIRECT_SCORE",
    "WEIGHTED_AVERAGE_100",
    "SUM_DOMAIN_POINTS",
}


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def validated_sncc_values(payload) -> tuple[str, str, str]:
    classe = payload.classe.strip().upper()
    admin_status = payload.statut_administratif.strip().upper()
    risk_level = payload.niveau_risque.strip().upper()
    errors = []
    if classe not in SNCC_CLASSES:
        errors.append(f"classe autorisée : {', '.join(SNCC_CLASSES)}")
    if admin_status not in SNCC_ADMIN_STATUSES:
        errors.append(
            "statut administratif autorisé : "
            + ", ".join(SNCC_ADMIN_STATUSES)
        )
    if risk_level not in SNCC_RISK_LEVELS:
        errors.append(
            "niveau de risque autorisé : "
            + ", ".join(SNCC_RISK_LEVELS)
        )
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Valeur SNCC hors référentiel — " + " ; ".join(errors) + ".",
        )
    return classe, admin_status, risk_level


def json_rule_dump(rule: dict[str, Any]) -> str:
    return json.dumps(
        rule,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def json_rule_load(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La règle de calcul du modèle est invalide.",
        ) from exc

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La règle de calcul doit être un objet JSON.",
        )
    return data


def quantize(value: Decimal, digits: int) -> Decimal:
    digits = max(0, min(int(digits), 6))
    quantum = Decimal("1") if digits == 0 else Decimal("1").scaleb(-digits)
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


def ensure_model_rule(rule: dict[str, Any]) -> str:
    mode = str(rule.get("calculation_mode", "")).strip().upper()
    if mode not in SUPPORTED_MODES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "calculation_mode doit être DIRECT_SCORE, "
                "WEIGHTED_AVERAGE_100 ou SUM_DOMAIN_POINTS."
            ),
        )

    try:
        rounding = int(rule.get("rounding", 2))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le paramètre rounding doit être un entier.",
        ) from exc

    if rounding < 0 or rounding > 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="rounding doit être compris entre 0 et 6.",
        )

    for key in ("classes", "levels"):
        if key in rule and not isinstance(rule[key], list):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{key} doit être une liste.",
            )

    return mode



def _score_in_interval(row: dict[str, Any], score: Decimal) -> bool:
    """Teste une plage dont la borne basse ou haute peut être absente."""
    try:
        min_value = (
            Decimal(str(row["min"]))
            if row.get("min") is not None
            else None
        )
        max_value = (
            Decimal(str(row["max"]))
            if row.get("max") is not None
            else None
        )
    except Exception:
        return False

    if min_value is not None and score < min_value:
        return False
    if max_value is not None and score > max_value:
        return False
    return min_value is not None or max_value is not None


def find_class(rule: dict[str, Any], score: Decimal) -> str | None:
    classes = rule.get("classes") or []
    default_code = None

    for row in classes:
        if not isinstance(row, dict):
            continue

        code = clean_text(str(row.get("code", "")))
        if not code:
            continue

        if row.get("default") is True:
            default_code = code
            continue

        if _score_in_interval(row, score):
            return code

    if default_code is not None:
        return default_code

    if classes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Le score calculé ne correspond à aucune classe dans "
                "la règle publiée."
            ),
        )
    return None

def find_level(rule: dict[str, Any], score: Decimal) -> int | None:
    levels = rule.get("levels") or []
    for row in levels:
        if not isinstance(row, dict):
            continue
        try:
            level = int(row.get("niveau"))
        except Exception:
            continue
        if _score_in_interval(row, score):
            return level

    if levels:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Le score calculé ne correspond à aucun niveau dans "
                "la règle publiée."
            ),
        )
    return None
def weight_response(item: PonderationScoring) -> ScoringWeightResponse:
    return ScoringWeightResponse(
        id=item.id,
        modele_scoring_id=item.modele_scoring_id,
        domaine=item.domaine,
        valeur=item.valeur,
        periode_debut=item.periode_debut,
        periode_fin=item.periode_fin,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def enterprise_classification_response(
    item: ClassificationEntreprise,
) -> EnterpriseClassificationResponse:
    return EnterpriseClassificationResponse(
        id=item.id,
        entreprise_id=item.entreprise_id,
        modele_scoring_id=item.modele_scoring_id,
        score=item.score,
        classe=item.classe,
        date_calcul=item.date_calcul,
        date_validation=item.date_validation,
        sources=item.sources,
        valide_par_id=item.valide_par_id,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def infc_response(item: ResultatInfc) -> InfcResultResponse:
    return InfcResultResponse(
        id=item.id,
        certification_id=item.certification_id,
        modele_scoring_id=item.modele_scoring_id,
        score_global=item.score_global,
        niveau=item.niveau,
        scores_domaines=item.scores_domaines,
        date_calcul=item.date_calcul,
        date_validation=item.date_validation,
        sources=item.sources,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def sncc_response(item: ClassementSncc) -> SnccResponse:
    return SnccResponse(
        id=item.id,
        certification_id=item.certification_id,
        classe=item.classe,
        statut_administratif=item.statut_administratif,
        niveau_risque=item.niveau_risque,
        justification=item.justification,
        date_effet=item.date_effet,
        date_fin=item.date_fin,
        valide_par_id=item.valide_par_id,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


class ScoringService:

    # ========================================================
    # MODÈLES / PONDÉRATIONS
    # ========================================================

    @staticmethod
    async def require_model(
        db: AsyncSession,
        model_id: UUID,
    ) -> ModeleScoring:
        item = await ScoringRepository.get_model(db, model_id)
        if item is None:
            raise HTTPException(404, "Modèle de scoring introuvable.")
        return item

    @staticmethod
    def require_draft(model: ModeleScoring) -> None:
        if (model.statut or "").strip().upper() != "BROUILLON":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Un modèle publié ou retiré est immuable. "
                    "Clonez-le pour créer une nouvelle version."
                ),
            )

    @staticmethod
    async def model_response(
        db: AsyncSession,
        model: ModeleScoring,
    ) -> ScoringModelResponse:
        weights = await ScoringRepository.list_weights(db, model.id)
        total = sum(
            (Decimal(str(x.valeur or 0)) for x in weights),
            Decimal("0"),
        )

        return ScoringModelResponse(
            id=model.id,
            code=model.code,
            libelle=model.libelle,
            version=model.version,
            objet_evalue=model.objet_evalue,
            description=model.description,
            date_debut_validite=model.date_debut_validite,
            date_fin_validite=model.date_fin_validite,
            regle_calcul=json_rule_load(model.regle_calcul),
            reference_approbation=model.reference_approbation,
            statut=model.statut,
            ponderations_count=len(weights),
            total_ponderation=total,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    async def list_models(
        db: AsyncSession,
        *,
        objet_evalue: str | None,
        statut: str | None,
    ) -> list[ScoringModelResponse]:
        items = await ScoringRepository.list_models(
            db,
            objet_evalue=objet_evalue,
            statut=statut,
        )
        return [
            await ScoringService.model_response(db, x)
            for x in items
        ]

    @staticmethod
    async def active_model_response(
        db: AsyncSession,
        objet_evalue: str,
    ) -> ScoringModelResponse:
        item = await ScoringRepository.active_model(
            db,
            objet_evalue.strip().upper(),
        )
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucun modèle publié actif pour cet objet.",
            )
        return await ScoringService.model_response(db, item)

    @staticmethod
    async def create_model(
        db: AsyncSession,
        *,
        payload: ScoringModelCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> ScoringModelResponse:
        code = payload.code.strip().upper()
        version = payload.version.strip()
        objet = payload.objet_evalue.strip().upper()

        ensure_model_rule(payload.regle_calcul)

        if (
            payload.date_debut_validite
            and payload.date_fin_validite
            and payload.date_fin_validite < payload.date_debut_validite
        ):
            raise HTTPException(422, "Période de validité incohérente.")

        if await ScoringRepository.find_model_version(
            db,
            code=code,
            version=version,
        ):
            raise HTTPException(409, "Cette version de modèle existe déjà.")

        item = ModeleScoring(
            code=code,
            libelle=payload.libelle.strip(),
            version=version,
            objet_evalue=objet,
            description=clean_text(payload.description),
            date_debut_validite=payload.date_debut_validite,
            date_fin_validite=payload.date_fin_validite,
            regle_calcul=json_rule_dump(payload.regle_calcul),
            reference_approbation=None,
            statut="BROUILLON",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="SCORING_MODEL_CREATE",
            categorie="SCORING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="modele_scoring",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "code": item.code,
                "version": item.version,
                "objet_evalue": item.objet_evalue,
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return await ScoringService.model_response(db, item)

    @staticmethod
    async def update_model(
        db: AsyncSession,
        *,
        model_id: UUID,
        payload: ScoringModelUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> ScoringModelResponse:
        item = await ScoringService.require_model(db, model_id)
        ScoringService.require_draft(item)

        changes = payload.model_dump(exclude_unset=True)

        if "regle_calcul" in changes and changes["regle_calcul"] is not None:
            ensure_model_rule(changes["regle_calcul"])
            changes["regle_calcul"] = json_rule_dump(changes["regle_calcul"])

        new_start = changes.get(
            "date_debut_validite",
            item.date_debut_validite,
        )
        new_end = changes.get(
            "date_fin_validite",
            item.date_fin_validite,
        )
        if new_start and new_end and new_end < new_start:
            raise HTTPException(422, "Période de validité incohérente.")

        for field, value in changes.items():
            if isinstance(value, str):
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db,
            action="SCORING_MODEL_UPDATE",
            categorie="SCORING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="modele_scoring",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
        )

        await db.commit()
        await db.refresh(item)
        return await ScoringService.model_response(db, item)

    @staticmethod
    async def clone_model(
        db: AsyncSession,
        *,
        model_id: UUID,
        payload: ScoringModelCloneRequest,
        actor: AuthContext,
        request: Request,
    ) -> ScoringModelResponse:
        source = await ScoringService.require_model(db, model_id)

        code = payload.code.strip().upper()
        version = payload.version.strip()

        if await ScoringRepository.find_model_version(
            db,
            code=code,
            version=version,
        ):
            raise HTTPException(409, "La version cible existe déjà.")

        target = ModeleScoring(
            code=code,
            libelle=payload.libelle.strip(),
            version=version,
            objet_evalue=source.objet_evalue,
            description=source.description,
            date_debut_validite=payload.date_debut_validite,
            date_fin_validite=None,
            regle_calcul=source.regle_calcul,
            reference_approbation=None,
            statut="BROUILLON",
        )
        db.add(target)
        await db.flush()

        for weight in await ScoringRepository.list_weights(db, source.id):
            db.add(
                PonderationScoring(
                    modele_scoring_id=target.id,
                    domaine=weight.domaine,
                    valeur=weight.valeur,
                    periode_debut=weight.periode_debut,
                    periode_fin=weight.periode_fin,
                    statut=weight.statut,
                )
            )

        await write_audit_event(
            db,
            action="SCORING_MODEL_CLONE",
            categorie="SCORING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="modele_scoring",
            ressource_id=target.id,
            adresse_ip=client_ip(request),
            contexte={"source_model_id": str(source.id)},
        )

        await db.commit()
        await db.refresh(target)
        return await ScoringService.model_response(db, target)

    @staticmethod
    async def publish_model(
        db: AsyncSession,
        *,
        model_id: UUID,
        payload: ScoringModelPublishRequest,
        actor: AuthContext,
        request: Request,
    ) -> ScoringModelResponse:
        item = await ScoringService.require_model(db, model_id)
        ScoringService.require_draft(item)

        rule = json_rule_load(item.regle_calcul)
        mode = ensure_model_rule(rule)

        if mode in {"WEIGHTED_AVERAGE_100", "SUM_DOMAIN_POINTS"}:
            weights = await ScoringRepository.list_weights(
                db,
                item.id,
                active_only=True,
            )
            if not weights:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Un modèle pondéré ne peut pas être publié "
                        "sans pondération active."
                    ),
                )

        item.reference_approbation = payload.reference_approbation.strip()
        item.date_debut_validite = payload.date_debut_validite
        item.statut = "PUBLIE"

        await write_audit_event(
            db,
            action="SCORING_MODEL_PUBLISH",
            categorie="SCORING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="modele_scoring",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "reference_approbation": item.reference_approbation,
                "date_debut_validite": item.date_debut_validite.isoformat(),
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return await ScoringService.model_response(db, item)

    @staticmethod
    async def retire_model(
        db: AsyncSession,
        *,
        model_id: UUID,
        payload: ScoringModelRetireRequest,
        actor: AuthContext,
        request: Request,
    ) -> ScoringModelResponse:
        item = await ScoringService.require_model(db, model_id)

        if (item.statut or "").strip().upper() != "PUBLIE":
            raise HTTPException(409, "Seul un modèle publié peut être retiré.")

        if (
            item.date_debut_validite
            and payload.date_fin_validite < item.date_debut_validite
        ):
            raise HTTPException(422, "Date de fin antérieure au début.")

        item.date_fin_validite = payload.date_fin_validite
        item.statut = "RETIRE"

        await write_audit_event(
            db,
            action="SCORING_MODEL_RETIRE",
            categorie="SCORING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="modele_scoring",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            contexte={"motif": payload.motif.strip()},
        )

        await db.commit()
        await db.refresh(item)
        return await ScoringService.model_response(db, item)

    @staticmethod
    async def list_weights(
        db: AsyncSession,
        model_id: UUID,
    ) -> list[ScoringWeightResponse]:
        await ScoringService.require_model(db, model_id)
        return [
            weight_response(x)
            for x in await ScoringRepository.list_weights(db, model_id)
        ]

    @staticmethod
    async def create_weight(
        db: AsyncSession,
        *,
        model_id: UUID,
        payload: ScoringWeightCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> ScoringWeightResponse:
        model = await ScoringService.require_model(db, model_id)
        ScoringService.require_draft(model)

        domain = payload.domaine.strip().upper()

        if await ScoringRepository.active_weight_by_domain(
            db,
            model_id=model_id,
            domain=domain,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Une pondération active existe déjà pour ce domaine.",
            )

        item = PonderationScoring(
            modele_scoring_id=model_id,
            domaine=domain,
            valeur=payload.valeur,
            periode_debut=clean_text(payload.periode_debut),
            periode_fin=clean_text(payload.periode_fin),
            statut=clean_text(payload.statut) or "ACTIF",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="SCORING_WEIGHT_CREATE",
            categorie="SCORING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="ponderation_scoring",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "modele_scoring_id": str(model_id),
                "domaine": item.domaine,
                "valeur": str(item.valeur),
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return weight_response(item)

    @staticmethod
    async def update_weight(
        db: AsyncSession,
        *,
        model_id: UUID,
        weight_id: UUID,
        payload: ScoringWeightUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> ScoringWeightResponse:
        model = await ScoringService.require_model(db, model_id)
        ScoringService.require_draft(model)

        item = await ScoringRepository.get_weight(
            db,
            model_id=model_id,
            weight_id=weight_id,
        )
        if item is None:
            raise HTTPException(404, "Pondération introuvable.")

        for field, value in payload.model_dump(exclude_unset=True).items():
            if field == "domaine" and value is not None:
                value = value.strip().upper()
            elif isinstance(value, str):
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db,
            action="SCORING_WEIGHT_UPDATE",
            categorie="SCORING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="ponderation_scoring",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
        )

        await db.commit()
        await db.refresh(item)
        return weight_response(item)

    @staticmethod
    async def deactivate_weight(
        db: AsyncSession,
        *,
        model_id: UUID,
        weight_id: UUID,
        actor: AuthContext,
        request: Request,
    ) -> ScoringWeightResponse:
        model = await ScoringService.require_model(db, model_id)
        ScoringService.require_draft(model)

        item = await ScoringRepository.get_weight(
            db,
            model_id=model_id,
            weight_id=weight_id,
        )
        if item is None:
            raise HTTPException(404, "Pondération introuvable.")

        item.statut = "INACTIF"

        await write_audit_event(
            db,
            action="SCORING_WEIGHT_DEACTIVATE",
            categorie="SCORING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="ponderation_scoring",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
        )

        await db.commit()
        await db.refresh(item)
        return weight_response(item)

    # ========================================================
    # MOTEUR DE CALCUL
    # ========================================================

    @staticmethod
    async def resolve_model(
        db: AsyncSession,
        *,
        object_type: str,
        model_id: UUID | None,
    ) -> ModeleScoring:
        if model_id is not None:
            model = await ScoringService.require_model(db, model_id)
            if (model.statut or "").strip().upper() != "PUBLIE":
                raise HTTPException(409, "Le modèle choisi n'est pas publié.")
            if (model.objet_evalue or "").strip().upper() != object_type:
                raise HTTPException(
                    409,
                    "Le modèle choisi ne correspond pas à l'objet évalué.",
                )
            return model

        model = await ScoringRepository.active_model(db, object_type)
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Aucun modèle publié actif pour {object_type}."
                ),
            )
        return model

    @staticmethod
    async def compute(
        db: AsyncSession,
        *,
        model: ModeleScoring,
        payload: ScoreEvaluationInput,
    ) -> ScoreComputationPreviewResponse:
        rule = json_rule_load(model.regle_calcul)
        mode = ensure_model_rule(rule)
        rounding = int(rule.get("rounding", 2))

        contributions: dict[str, Any] = {}
        score: Decimal

        if mode == "DIRECT_SCORE":
            if payload.score_direct is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "score_direct est requis pour le mode DIRECT_SCORE."
                    ),
                )
            score = payload.score_direct

            if "score_min" in rule and score < Decimal(str(rule["score_min"])):
                raise HTTPException(422, "Score inférieur au minimum du modèle.")
            if "score_max" in rule and score > Decimal(str(rule["score_max"])):
                raise HTTPException(422, "Score supérieur au maximum du modèle.")

        else:
            weights = await ScoringRepository.list_weights(
                db,
                model.id,
                active_only=True,
            )
            if not weights:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Aucune pondération active pour ce modèle.",
                )

            normalized_inputs = {
                str(key).strip().upper(): Decimal(str(value))
                for key, value in payload.scores_domaines.items()
            }

            expected = {
                (weight.domaine or "").strip().upper(): Decimal(
                    str(weight.valeur or 0)
                )
                for weight in weights
                if clean_text(weight.domaine)
            }

            missing = [
                domain
                for domain in expected
                if domain not in normalized_inputs
            ]

            missing_policy = str(
                rule.get("missing_policy", "REJECT")
            ).strip().upper()

            if missing and missing_policy == "REJECT":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Données insuffisantes pour calculer le score. "
                        f"Domaines manquants : {', '.join(missing)}"
                    ),
                )

            if mode == "WEIGHTED_AVERAGE_100":
                numerator = Decimal("0")
                denominator = Decimal("0")

                for domain, weight_value in expected.items():
                    if domain not in normalized_inputs:
                        continue

                    domain_score = normalized_inputs[domain]
                    if domain_score < 0 or domain_score > 100:
                        raise HTTPException(
                            422,
                            f"Le domaine {domain} doit être noté entre 0 et 100.",
                        )

                    contribution = domain_score * weight_value
                    numerator += contribution
                    denominator += weight_value
                    contributions[domain] = {
                        "score": str(domain_score),
                        "poids": str(weight_value),
                        "produit": str(contribution),
                    }

                if denominator <= 0:
                    raise HTTPException(409, "Somme des pondérations nulle.")

                score = numerator / denominator

            else:  # SUM_DOMAIN_POINTS
                score = Decimal("0")

                for domain, max_points in expected.items():
                    if domain not in normalized_inputs:
                        continue

                    domain_score = normalized_inputs[domain]
                    if domain_score < 0 or domain_score > max_points:
                        raise HTTPException(
                            422,
                            (
                                f"Le domaine {domain} doit être compris "
                                f"entre 0 et {max_points}."
                            ),
                        )

                    score += domain_score
                    contributions[domain] = {
                        "score": str(domain_score),
                        "maximum": str(max_points),
                    }

        score = quantize(score, rounding)

        classe = find_class(rule, score)
        niveau = find_level(rule, score)

        return ScoreComputationPreviewResponse(
            modele_scoring_id=model.id,
            modele_code=model.code or "",
            modele_version=model.version or "",
            objet_evalue=model.objet_evalue or "",
            mode_calcul=mode,
            score=score,
            contributions=contributions,
            classe=classe,
            niveau=niveau,
        )

    @staticmethod
    async def preview(
        db: AsyncSession,
        *,
        object_type: str,
        payload: ScoreEvaluationInput,
    ) -> ScoreComputationPreviewResponse:
        model = await ScoringService.resolve_model(
            db,
            object_type=object_type.strip().upper(),
            model_id=payload.modele_scoring_id,
        )
        return await ScoringService.compute(
            db,
            model=model,
            payload=payload,
        )

    # ========================================================
    # CLASSIFICATION ENTREPRISE
    # ========================================================

    @staticmethod
    async def list_enterprise_classifications(
        db: AsyncSession,
        enterprise_id: UUID,
    ) -> EnterpriseClassificationListResponse:
        if await ScoringRepository.get_enterprise(db, enterprise_id) is None:
            raise HTTPException(404, "Entreprise introuvable.")

        items = await ScoringRepository.list_enterprise_classifications(
            db, enterprise_id
        )
        return EnterpriseClassificationListResponse(
            total=len(items),
            items=[enterprise_classification_response(x) for x in items],
        )

    @staticmethod
    async def latest_enterprise_classification(
        db: AsyncSession,
        enterprise_id: UUID,
    ) -> EnterpriseClassificationResponse:
        if await ScoringRepository.get_enterprise(db, enterprise_id) is None:
            raise HTTPException(404, "Entreprise introuvable.")

        item = await ScoringRepository.latest_enterprise_classification(
            db, enterprise_id
        )
        if item is None:
            raise HTTPException(404, "Aucune classification pour cette entreprise.")
        return enterprise_classification_response(item)

    @staticmethod
    async def evaluate_enterprise(
        db: AsyncSession,
        *,
        enterprise_id: UUID,
        payload: ScoreEvaluationInput,
        actor: AuthContext,
        request: Request,
    ) -> EnterpriseClassificationResponse:
        enterprise = await ScoringRepository.get_enterprise(db, enterprise_id)
        if enterprise is None:
            raise HTTPException(404, "Entreprise introuvable.")

        model = await ScoringService.resolve_model(
            db,
            object_type=MODEL_OBJECT_ENTERPRISE,
            model_id=payload.modele_scoring_id,
        )
        result = await ScoringService.compute(
            db,
            model=model,
            payload=payload,
        )

        if not result.classe:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Le modèle de classification doit définir des classes."
                ),
            )

        sources = dict(payload.sources)
        sources["_calcul"] = {
            "modele_code": model.code,
            "modele_version": model.version,
            "mode_calcul": result.mode_calcul,
            "scores_domaines": {
                k: str(v) for k, v in payload.scores_domaines.items()
            },
            "score_direct": (
                str(payload.score_direct)
                if payload.score_direct is not None else None
            ),
            "contributions": result.contributions,
        }

        item = ClassificationEntreprise(
            entreprise_id=enterprise_id,
            modele_scoring_id=model.id,
            score=result.score,
            classe=result.classe,
            date_calcul=date.today(),
            date_validation=date.today(),
            sources=sources,
            valide_par_id=actor.user.id,
            statut="VALIDE",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="ENTERPRISE_CLASSIFICATION_CREATE",
            categorie="SCORING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="classification_entreprise",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "entreprise_id": str(enterprise_id),
                "modele_scoring_id": str(model.id),
                "score": str(item.score),
                "classe": item.classe,
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return enterprise_classification_response(item)

    # ========================================================
    # INFC
    # ========================================================

    @staticmethod
    async def list_infc(
        db: AsyncSession,
        *,
        certification_id: UUID | None,
        model_id: UUID | None,
        statut_filter: str | None,
        limit: int,
        offset: int,
    ) -> InfcResultListResponse:
        items, total = await ScoringRepository.list_infc_results(
            db,
            certification_id=certification_id,
            model_id=model_id,
            statut=statut_filter,
            limit=limit,
            offset=offset,
        )
        return InfcResultListResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=[infc_response(x) for x in items],
        )

    @staticmethod
    async def latest_infc(
        db: AsyncSession,
        certification_id: UUID,
    ) -> InfcResultResponse:
        if await ScoringRepository.get_certification(db, certification_id) is None:
            raise HTTPException(404, "Certification introuvable.")

        item = await ScoringRepository.latest_infc_result(
            db,
            certification_id,
        )
        if item is None:
            raise HTTPException(404, "Aucun résultat INFC pour cette certification.")
        return infc_response(item)

    @staticmethod
    async def calculate_infc(
        db: AsyncSession,
        *,
        certification_id: UUID,
        payload: ScoreEvaluationInput,
        actor: AuthContext,
        request: Request,
    ) -> InfcResultResponse:
        certification = await ScoringRepository.get_certification(
            db,
            certification_id,
        )
        if certification is None:
            raise HTTPException(404, "Certification introuvable.")

        model = await ScoringService.resolve_model(
            db,
            object_type=MODEL_OBJECT_INFC,
            model_id=payload.modele_scoring_id,
        )
        result = await ScoringService.compute(
            db,
            model=model,
            payload=payload,
        )

        sources = dict(payload.sources)
        sources["_calcul"] = {
            "modele_code": model.code,
            "modele_version": model.version,
            "mode_calcul": result.mode_calcul,
            "niveau_configure": result.niveau is not None,
        }

        domain_snapshot = {
            "entrees": {
                key: str(value)
                for key, value in payload.scores_domaines.items()
            },
            "contributions": result.contributions,
        }

        latest = await ScoringRepository.latest_infc_result(
            db,
            certification_id,
        )
        if (
            latest is not None
            and latest.modele_scoring_id == model.id
            and latest.score_global == result.score
            and latest.niveau == result.niveau
            and latest.scores_domaines == domain_snapshot
            and latest.sources == sources
        ):
            # Un double clic ou la répétition stricte du même calcul ne doit
            # pas polluer l'historique. Un changement d'entrée ou de modèle
            # créera en revanche un nouveau résultat traçable.
            return infc_response(latest)

        item = ResultatInfc(
            certification_id=certification_id,
            modele_scoring_id=model.id,
            score_global=result.score,
            niveau=result.niveau,
            scores_domaines=domain_snapshot,
            date_calcul=date.today(),
            date_validation=None,
            sources=sources,
            statut="CALCULE",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="INFC_CALCULATE",
            categorie="SCORING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="resultat_infc",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "certification_id": str(certification_id),
                "modele_scoring_id": str(model.id),
                "score_global": str(item.score_global),
                "niveau": item.niveau,
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return infc_response(item)

    @staticmethod
    async def validate_infc(
        db: AsyncSession,
        *,
        result_id: UUID,
        payload: InfcValidateRequest,
        actor: AuthContext,
        request: Request,
    ) -> InfcResultResponse:
        item = await ScoringRepository.get_infc_result(db, result_id)
        if item is None:
            raise HTTPException(404, "Résultat INFC introuvable.")

        if item.statut == "VALIDE":
            return infc_response(item)

        if item.niveau is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Le score INFC a bien été calculé, mais il ne peut pas "
                    "être validé tant que le modèle publié ne définit pas "
                    "ses niveaux dans la règle de calcul."
                ),
            )

        item.date_validation = date.today()
        item.statut = "VALIDE"

        await write_audit_event(
            db,
            action="INFC_VALIDATE",
            categorie="SCORING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="resultat_infc",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "date_validation": item.date_validation.isoformat(),
                "statut": item.statut,
            },
            contexte={
                "commentaire": clean_text(payload.commentaire)
            },
        )

        await db.commit()
        await db.refresh(item)
        return infc_response(item)

    # ========================================================
    # SNCC
    # ========================================================

    @staticmethod
    async def list_sncc(
        db: AsyncSession,
        *,
        certification_id: UUID | None,
        classe: str | None,
        statut_administratif: str | None,
        niveau_risque: str | None,
        limit: int,
        offset: int,
    ) -> SnccListResponse:
        items, total = await ScoringRepository.list_sncc(
            db,
            certification_id=certification_id,
            classe=classe,
            statut_administratif=statut_administratif,
            niveau_risque=niveau_risque,
            limit=limit,
            offset=offset,
        )
        return SnccListResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=[sncc_response(x) for x in items],
        )

    @staticmethod
    async def current_sncc(
        db: AsyncSession,
        certification_id: UUID,
    ) -> SnccResponse:
        if await ScoringRepository.get_certification(db, certification_id) is None:
            raise HTTPException(404, "Certification introuvable.")

        item = await ScoringRepository.current_sncc(
            db,
            certification_id,
        )
        if item is None:
            raise HTTPException(404, "Aucun classement SNCC courant.")
        return sncc_response(item)

    @staticmethod
    async def create_sncc(
        db: AsyncSession,
        *,
        certification_id: UUID,
        payload: SnccCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> SnccResponse:
        if await ScoringRepository.get_certification(db, certification_id) is None:
            raise HTTPException(404, "Certification introuvable.")

        latest_infc = await ScoringRepository.latest_infc_result(
            db,
            certification_id,
        )
        if (
            latest_infc is None
            or (latest_infc.statut or "").strip().upper() != "VALIDE"
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Le classement SNCC exige un résultat INFC validé. "
                    "Finalisez l’INFC après l’intégration BNEC avant "
                    "de classer la certification."
                ),
            )

        current = await ScoringRepository.current_sncc(
            db,
            certification_id,
        )
        if current is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Un classement SNCC courant existe déjà. "
                    "Utilisez l'endpoint de reclassement."
                ),
            )

        classe, admin_status, risk_level = validated_sncc_values(payload)
        item = ClassementSncc(
            certification_id=certification_id,
            classe=classe,
            statut_administratif=admin_status,
            niveau_risque=risk_level,
            justification=payload.justification.strip(),
            date_effet=payload.date_effet,
            date_fin=None,
            valide_par_id=actor.user.id,
            statut="VALIDE",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="SNCC_CREATE",
            categorie="SCORING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="classement_sncc",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "certification_id": str(certification_id),
                "classe": item.classe,
                "statut_administratif": item.statut_administratif,
                "niveau_risque": item.niveau_risque,
                "date_effet": item.date_effet.isoformat(),
            },
        )

        await db.commit()
        await db.refresh(item)
        return sncc_response(item)

    @staticmethod
    async def reclassify_sncc(
        db: AsyncSession,
        *,
        certification_id: UUID,
        payload: SnccReclassifyRequest,
        actor: AuthContext,
        request: Request,
    ) -> SnccResponse:
        if await ScoringRepository.get_certification(db, certification_id) is None:
            raise HTTPException(404, "Certification introuvable.")

        latest_infc = await ScoringRepository.latest_infc_result(
            db,
            certification_id,
        )
        if (
            latest_infc is None
            or (latest_infc.statut or "").strip().upper() != "VALIDE"
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Le classement SNCC exige un résultat INFC validé. "
                    "Finalisez l’INFC après l’intégration BNEC avant "
                    "de classer la certification."
                ),
            )

        current = await ScoringRepository.current_sncc(
            db,
            certification_id,
        )
        if current is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Aucun classement courant à remplacer.",
            )

        if current.date_effet and payload.date_effet <= current.date_effet:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "La date d'effet du reclassement doit être postérieure "
                    "au classement courant."
                ),
            )

        old_values = {
            "id": str(current.id),
            "classe": current.classe,
            "statut_administratif": current.statut_administratif,
            "niveau_risque": current.niveau_risque,
            "date_effet": (
                current.date_effet.isoformat()
                if current.date_effet else None
            ),
            "date_fin": None,
        }

        current.date_fin = payload.date_effet - timedelta(days=1)

        classe, admin_status, risk_level = validated_sncc_values(payload)
        item = ClassementSncc(
            certification_id=certification_id,
            classe=classe,
            statut_administratif=admin_status,
            niveau_risque=risk_level,
            justification=payload.justification.strip(),
            date_effet=payload.date_effet,
            date_fin=None,
            valide_par_id=actor.user.id,
            statut="VALIDE",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="SNCC_RECLASSIFY",
            categorie="SCORING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="classement_sncc",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant=old_values,
            valeurs_apres={
                "classe": item.classe,
                "statut_administratif": item.statut_administratif,
                "niveau_risque": item.niveau_risque,
                "date_effet": item.date_effet.isoformat(),
            },
            contexte={
                "classement_precedent_id": str(current.id),
                "motif_reclassement": payload.motif_reclassement.strip(),
            },
        )

        await db.commit()
        await db.refresh(item)
        return sncc_response(item)

    @staticmethod
    async def close_sncc(
        db: AsyncSession,
        *,
        sncc_id: UUID,
        payload: SnccCloseRequest,
        actor: AuthContext,
        request: Request,
    ) -> SnccResponse:
        item = await ScoringRepository.get_sncc(db, sncc_id)
        if item is None:
            raise HTTPException(404, "Classement SNCC introuvable.")

        if item.date_fin is not None:
            raise HTTPException(409, "Ce classement possède déjà une date de fin.")

        if item.date_effet and payload.date_fin < item.date_effet:
            raise HTTPException(422, "Date de fin antérieure à la date d'effet.")

        item.date_fin = payload.date_fin

        await write_audit_event(
            db,
            action="SNCC_CLOSE",
            categorie="SCORING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="classement_sncc",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={"date_fin": item.date_fin.isoformat()},
            contexte={"motif": payload.motif.strip()},
        )

        await db.commit()
        await db.refresh(item)
        return sncc_response(item)
