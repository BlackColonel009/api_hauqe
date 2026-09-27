"""Calculs automatiques explicables pour Scoring, INFC et SNCC.

Le service ne définit ni seuil de classement ni niveau de risque : ces valeurs
proviennent exclusivement des modèles et règles publiés. Il transforme les
données réelles du parcours Collecte → Vérification → FUCCS → N1/N2 → BNEC
en entrées de calcul, puis produit un rapport lisible avant toute écriture.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.anomalie_verification import AnomalieVerification
from app.models.certification import Certification
from app.models.certification_declaree import CertificationDeclaree
from app.models.classement_sncc import ClassementSncc
from app.models.constat_controle import ConstatControle
from app.models.controle_fuccs import ControleFuccs
from app.models.dossier_verification import DossierVerification
from app.models.element_integration import ElementIntegration
from app.models.fiche_collecte import FicheCollecte
from app.models.integration_bnec import IntegrationBnec
from app.models.regle_metier import RegleMetier
from app.models.validation import Validation
from app.rules.business_rule_resolver import resolve_business_rule
from app.schemas.scoring import (
    AutomaticEvaluationFinding,
    AutomaticEvaluationReport,
    AutomaticEvaluationResponse,
    ScoreEvaluationInput,
    SnccCreateRequest,
)
from app.services.auth_service import AuthContext
from app.services.scoring_service import (
    MODEL_OBJECT_ENTERPRISE,
    MODEL_OBJECT_INFC,
    ScoringService,
    client_ip,
    find_class,
    json_rule_load,
    validated_sncc_values,
)


FAVORABLE_DECISIONS = {"VALIDE", "VALIDE_SOUS_RESERVE"}
COMPLETED_INTEGRATION = {"INTEGREE", "INTEGRE"}
COMPLETED_FUCCS = {"FINALISE", "TERMINE"}
CLOSED_ANOMALIES = {"RESOLUE", "RESOLU", "CLOTUREE", "CLOTURE"}
CRITICAL_SEVERITIES = {"CRITIQUE", "MAJEURE", "ELEVEE", "ÉLEVÉE"}

# Les aliases couvrent les modèles déjà préremplis. Toute pondération
# différente doit être reliée explicitement dans automatic_mapping de la règle.
DOMAIN_ALIASES = {
    "COLLECTE": "COLLECTE_COMPLETUDE",
    "COMPLETUDE": "COLLECTE_COMPLETUDE",
    "COLLECTE_COMPLETUDE": "COLLECTE_COMPLETUDE",
    "VERIFICATION": "VERIFICATION_DOCUMENTAIRE",
    "VERIFICATION_DOCUMENTAIRE": "VERIFICATION_DOCUMENTAIRE",
    "FUCCS": "FUCCS",
    "VALIDATION_N1": "VALIDATION_N1",
    "VALIDATION_N2": "VALIDATION_N2",
    "INTEGRATION": "INTEGRATION_BNEC",
    "INTEGRATION_BNEC": "INTEGRATION_BNEC",
    "AUTHENTICITE": "AUTHENTICITE",
    "VALIDITE": "VALIDITE",
    "MAINTIEN": "MAINTIEN",
    "MAITRISE_DOCUMENTAIRE": "MAITRISE_DOCUMENTAIRE",
    "TRACABILITE_MAITRISE_OPERATIONNELLE": "TRACABILITE_MAITRISE_OPERATIONNELLE",
    "SUIVI_RENOUVELLEMENT": "SUIVI_RENOUVELLEMENT",
    "ANOMALIES": "ANOMALIES",
}

DEFAULT_ENTERPRISE_METRICS = [
    "COLLECTE_COMPLETUDE",
    "VERIFICATION_DOCUMENTAIRE",
    "FUCCS",
    "VALIDATION_N1",
    "VALIDATION_N2",
    "INTEGRATION_BNEC",
]
DEFAULT_INFC_METRICS = [
    "AUTHENTICITE",
    "VALIDITE",
    "MAINTIEN",
    "MAITRISE_DOCUMENTAIRE",
    "TRACABILITE_MAITRISE_OPERATIONNELLE",
    "SUIVI_RENOUVELLEMENT",
]


def _key(value: str | None) -> str:
    return str(value or "").strip().upper().replace(" ", "_").replace("-", "_")


def _percent(value: Any) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")
    return min(Decimal("100"), max(Decimal("0"), number))


def _done_validation(item: Validation | None) -> bool:
    return bool(
        item
        and _key(item.decision) in FAVORABLE_DECISIONS
        and _key(item.statut) in {"TERMINE", "TERMINEE", "VALIDE"}
    )


def _finding(
    code: str,
    libelle: str,
    statut: str,
    detail: str,
    valeur: Decimal | None = None,
) -> AutomaticEvaluationFinding:
    return AutomaticEvaluationFinding(
        code=code,
        libelle=libelle,
        statut=statut,
        detail=detail,
        valeur=valeur,
    )


class AutomaticScoringService:
    """Orchestrateur sans seuil métier codé en dur."""

    @staticmethod
    async def _pipeline(
        db: AsyncSession,
        certification: Certification,
    ) -> dict[str, Any]:
        """Retrouve le parcours source d'une certification intégrée."""
        element = await db.scalar(
            select(ElementIntegration)
            .join(IntegrationBnec, IntegrationBnec.id == ElementIntegration.integration_bnec_id)
            .where(
                ElementIntegration.type_objet == "CERTIFICATION",
                ElementIntegration.ressource_cible_id == certification.id,
            )
            .order_by(IntegrationBnec.updated_at.desc(), ElementIntegration.updated_at.desc())
            .limit(1)
        )
        integration = await db.get(IntegrationBnec, element.integration_bnec_id) if element else None
        validation = await db.get(Validation, integration.validation_id) if integration else None
        fiche = await db.get(FicheCollecte, validation.fiche_collecte_id) if validation else None

        # Une certification déjà créée peut posséder une source déclarée même
        # si l'élément BNEC n'est plus disponible : cela permet un rapport de
        # manquements plutôt qu'une erreur opaque.
        if fiche is None:
            declared = await db.scalar(
                select(CertificationDeclaree)
                .where(CertificationDeclaree.certification_officielle_id == certification.id)
                .order_by(CertificationDeclaree.updated_at.desc())
                .limit(1)
            )
            fiche = await db.get(FicheCollecte, declared.fiche_collecte_id) if declared else None

        verification = None
        control = None
        n1 = None
        n2 = None
        anomalies: list[AnomalieVerification] = []
        constats: list[ConstatControle] = []
        if fiche is not None:
            verification = await db.scalar(
                select(DossierVerification)
                .where(DossierVerification.fiche_collecte_id == fiche.id)
                .order_by(DossierVerification.updated_at.desc())
                .limit(1)
            )
            if verification is not None:
                control = await db.scalar(
                    select(ControleFuccs)
                    .where(ControleFuccs.dossier_verification_id == verification.id)
                    .order_by(ControleFuccs.updated_at.desc())
                    .limit(1)
                )
                anomalies = list(
                    (await db.scalars(
                        select(AnomalieVerification).where(
                            AnomalieVerification.dossier_verification_id == verification.id
                        )
                    )).all()
                )
            if control is not None:
                constats = list(
                    (await db.scalars(
                        select(ConstatControle).where(
                            ConstatControle.controle_fuccs_id == control.id
                        )
                    )).all()
                )
            n1 = await db.scalar(
                select(Validation)
                .where(
                    Validation.fiche_collecte_id == fiche.id,
                    Validation.niveau_validation == "NIVEAU_1",
                )
                .order_by(Validation.updated_at.desc())
                .limit(1)
            )
            n2 = await db.scalar(
                select(Validation)
                .where(
                    Validation.fiche_collecte_id == fiche.id,
                    Validation.niveau_validation == "NIVEAU_2",
                )
                .order_by(Validation.updated_at.desc())
                .limit(1)
            )

        return {
            "fiche": fiche,
            "verification": verification,
            "control": control,
            "n1": n1,
            "n2": n2,
            "integration": integration,
            "anomalies": anomalies,
            "constats": constats,
        }

    @staticmethod
    def _metrics(
        certification: Certification,
        pipeline: dict[str, Any],
        *,
        prefix: str = "",
    ) -> tuple[dict[str, Decimal], list[AutomaticEvaluationFinding], list[str], list[str]]:
        """Convertit le parcours en indicateurs sur 100 et constats lisibles."""
        fiche: FicheCollecte | None = pipeline["fiche"]
        verification: DossierVerification | None = pipeline["verification"]
        control: ControleFuccs | None = pipeline["control"]
        n1: Validation | None = pipeline["n1"]
        n2: Validation | None = pipeline["n2"]
        integration: IntegrationBnec | None = pipeline["integration"]

        findings: list[AutomaticEvaluationFinding] = []
        blockers: list[str] = []
        alerts: list[str] = []
        marker = f"{prefix} — " if prefix else ""

        collection = _percent(fiche.taux_completude if fiche else None)
        collection_done = bool(fiche and (fiche.soumise_at or _key(fiche.statut) == "SOUMISE"))
        if not fiche:
            blockers.append(f"{marker}aucune fiche de collecte source n'a été retrouvée.")
            findings.append(_finding("COLLECTE_COMPLETUDE", "Complétude de la collecte", "BLOQUANT", "Aucune fiche source rattachée à la certification.", collection))
        elif not collection_done:
            blockers.append(f"{marker}la fiche de collecte n'est pas soumise.")
            findings.append(_finding("COLLECTE_COMPLETUDE", "Complétude de la collecte", "BLOQUANT", "La fiche doit être complétée puis soumise.", collection))
        elif collection < 100:
            alerts.append(f"{marker}complétude de collecte : {collection}%.")
            findings.append(_finding("COLLECTE_COMPLETUDE", "Complétude de la collecte", "ALERTE", "La fiche est soumise mais comporte des informations non renseignées.", collection))
        else:
            findings.append(_finding("COLLECTE_COMPLETUDE", "Complétude de la collecte", "CONFORME", "Fiche soumise et complète.", collection))

        verification_done = bool(verification and verification.date_fin and _key(verification.avis) not in {"REJETE", "DEFAVORABLE"})
        if not verification:
            blockers.append(f"{marker}vérification documentaire non ouverte.")
            findings.append(_finding("VERIFICATION_DOCUMENTAIRE", "Vérification documentaire", "BLOQUANT", "Le dossier de vérification n'existe pas."))
        elif not verification_done:
            blockers.append(f"{marker}vérification documentaire non clôturée ou défavorable.")
            findings.append(_finding("VERIFICATION_DOCUMENTAIRE", "Vérification documentaire", "BLOQUANT", "La vérification doit être clôturée avec un avis favorable."))
        else:
            findings.append(_finding("VERIFICATION_DOCUMENTAIRE", "Vérification documentaire", "CONFORME", "Vérification documentaire clôturée." , Decimal("100")))

        fuccs_done = bool(control and _key(control.statut) in COMPLETED_FUCCS)
        fuccs = _percent(control.taux if control else None)
        if not control:
            blockers.append(f"{marker}contrôle FUCCS absent.")
            findings.append(_finding("FUCCS", "Contrôle FUCCS", "BLOQUANT", "Aucun contrôle FUCCS n'est rattaché au dossier.", fuccs))
        elif not fuccs_done:
            blockers.append(f"{marker}contrôle FUCCS non finalisé.")
            findings.append(_finding("FUCCS", "Contrôle FUCCS", "BLOQUANT", "Le contrôle FUCCS doit être finalisé.", fuccs))
        else:
            findings.append(_finding("FUCCS", "Contrôle FUCCS", "CONFORME" if fuccs >= 100 else "ALERTE", "Taux issu du contrôle FUCCS finalisé.", fuccs))
            if fuccs < 100:
                alerts.append(f"{marker}score FUCCS finalisé : {fuccs}%.")

        for level, item, code in (("N1", n1, "VALIDATION_N1"), ("N2", n2, "VALIDATION_N2")):
            if not _done_validation(item):
                blockers.append(f"{marker}validation {level} favorable non prononcée.")
                findings.append(_finding(code, f"Validation {level}", "BLOQUANT", f"La validation {level} favorable est requise."))
            else:
                findings.append(_finding(code, f"Validation {level}", "CONFORME", f"Décision {level} favorable enregistrée.", Decimal("100")))

        integrated = bool(integration and _key(integration.statut) in COMPLETED_INTEGRATION)
        if not integration:
            blockers.append(f"{marker}intégration BNEC non ouverte.")
            findings.append(_finding("INTEGRATION_BNEC", "Intégration BNEC", "BLOQUANT", "Aucune intégration BNEC n'est rattachée au dossier."))
        elif not integrated:
            blockers.append(f"{marker}intégration BNEC non terminée.")
            findings.append(_finding("INTEGRATION_BNEC", "Intégration BNEC", "BLOQUANT", "L'intégration BNEC doit être terminée.", Decimal("0")))
        else:
            findings.append(_finding("INTEGRATION_BNEC", "Intégration BNEC", "CONFORME", "Intégration BNEC terminée.", Decimal("100")))

        unresolved = [x for x in pipeline["anomalies"] if _key(x.statut) not in CLOSED_ANOMALIES]
        severe = [x for x in unresolved if _key(x.gravite) in CRITICAL_SEVERITIES]
        if severe:
            blockers.append(f"{marker}{len(severe)} anomalie(s) majeure(s) ou critique(s) non résolue(s).")
        elif unresolved:
            alerts.append(f"{marker}{len(unresolved)} anomalie(s) de vérification non résolue(s).")
        if unresolved:
            findings.append(_finding("ANOMALIES", "Anomalies de vérification", "BLOQUANT" if severe else "ALERTE", f"{len(unresolved)} anomalie(s) non résolue(s), dont {len(severe)} majeure(s) ou critique(s).", Decimal("0")))
        else:
            findings.append(_finding("ANOMALIES", "Anomalies de vérification", "CONFORME", "Aucune anomalie ouverte.", Decimal("100")))

        valid_dates = bool(certification.date_obtention and certification.date_expiration)
        not_expired = bool(valid_dates and certification.date_expiration >= date.today())
        if not valid_dates:
            alerts.append(f"{marker}date d'obtention ou d'expiration du certificat manquante.")
            findings.append(_finding("VALIDITE", "Validité du certificat", "ALERTE", "Les deux dates de validité du certificat sont nécessaires.", Decimal("0")))
        elif not not_expired:
            alerts.append(f"{marker}certificat expiré.")
            findings.append(_finding("VALIDITE", "Validité du certificat", "ALERTE", "La date d'expiration est dépassée.", Decimal("0")))
        else:
            findings.append(_finding("VALIDITE", "Validité du certificat", "CONFORME", "Dates de validité renseignées et certificat non expiré.", Decimal("100")))

        authenticity = Decimal("100") if certification.authenticite_verifiee or verification_done else Decimal("0")
        traceability = (Decimal("100") if _done_validation(n1) else Decimal("0"))
        traceability += Decimal("100") if _done_validation(n2) else Decimal("0")
        traceability += Decimal("100") if integrated else Decimal("0")
        traceability = traceability / Decimal("3")
        metrics = {
            "COLLECTE_COMPLETUDE": collection,
            "VERIFICATION_DOCUMENTAIRE": Decimal("100") if verification_done else Decimal("0"),
            "FUCCS": fuccs if fuccs_done else Decimal("0"),
            "VALIDATION_N1": Decimal("100") if _done_validation(n1) else Decimal("0"),
            "VALIDATION_N2": Decimal("100") if _done_validation(n2) else Decimal("0"),
            "INTEGRATION_BNEC": Decimal("100") if integrated else Decimal("0"),
            "AUTHENTICITE": authenticity,
            "VALIDITE": Decimal("100") if not_expired else Decimal("0"),
            "MAINTIEN": fuccs if fuccs_done else Decimal("0"),
            "MAITRISE_DOCUMENTAIRE": Decimal("100") if verification_done else Decimal("0"),
            "TRACABILITE_MAITRISE_OPERATIONNELLE": traceability,
            "SUIVI_RENOUVELLEMENT": Decimal("100") if not_expired else Decimal("0"),
            "ANOMALIES": Decimal("0") if unresolved else Decimal("100"),
        }
        return metrics, findings, blockers, alerts

    @staticmethod
    def _input_for_model(
        model,
        metrics: dict[str, Decimal],
        *,
        object_type: str,
        source_snapshot: dict[str, Any],
        blockers: list[str],
    ) -> ScoreEvaluationInput:
        rule = json_rule_load(model.regle_calcul)
        mode = _key(rule.get("calculation_mode"))
        configured_mapping = {
            _key(domain): _key(metric)
            for domain, metric in (rule.get("automatic_mapping") or {}).items()
            if isinstance(domain, str) and isinstance(metric, str)
        }
        if mode == "DIRECT_SCORE":
            defaults = DEFAULT_ENTERPRISE_METRICS if object_type == MODEL_OBJECT_ENTERPRISE else DEFAULT_INFC_METRICS
            selected = [_key(x) for x in (rule.get("automatic_sources") or defaults)]
            unknown = [key for key in selected if key not in metrics]
            if unknown:
                blockers.append("La règle publiée référence des sources automatiques inconnues : " + ", ".join(unknown) + ".")
            values = [metrics[key] for key in selected if key in metrics]
            score = sum(values, Decimal("0")) / Decimal(len(values)) if values else Decimal("0")
            return ScoreEvaluationInput(score_direct=score, sources=source_snapshot)

        expected: dict[str, Decimal] = {}
        # Les pondérations actives sont traitées par ScoringService.compute ;
        # il suffit de fournir les mêmes domaines résolus ci-dessous.
        source_snapshot["automatic_mapping"] = configured_mapping
        for domain, metric in configured_mapping.items():
            if metric not in metrics:
                blockers.append(f"Le mapping publié {domain} → {metric} est inconnu.")
            else:
                expected[domain] = metrics[metric]

        # Sans mapping explicite, les domaines documentés sont résolus par
        # leur code. Les autres seront signalés avant toute écriture par
        # compute() si une pondération active les attend.
        for domain, metric in DOMAIN_ALIASES.items():
            expected.setdefault(domain, metrics.get(metric, Decimal("0")))
        return ScoreEvaluationInput(scores_domaines=expected, sources=source_snapshot)

    @staticmethod
    def _risk_from_model(model, score: Decimal | None) -> tuple[str | None, str | None]:
        if score is None:
            return None, None
        rule = json_rule_load(model.regle_calcul)
        for row in rule.get("risk_levels") or []:
            if not isinstance(row, dict):
                continue
            try:
                minimum = Decimal(str(row["min"])) if row.get("min") is not None else None
                maximum = Decimal(str(row["max"])) if row.get("max") is not None else None
            except (InvalidOperation, KeyError, TypeError, ValueError):
                continue
            if (minimum is None or score >= minimum) and (maximum is None or score <= maximum):
                return str(row.get("code") or row.get("niveau_risque") or "").strip() or None, str(model.code or "")
        return None, None

    @staticmethod
    def _report(
        *,
        operation: str,
        findings: list[AutomaticEvaluationFinding],
        blockers: list[str],
        alerts: list[str],
        model=None,
        result=None,
        classe: str | None = None,
        risk: str | None = None,
        statut_administratif: str | None = None,
        risk_rule_code: str | None = None,
        risk_rule_version: str | None = None,
    ) -> AutomaticEvaluationReport:
        return AutomaticEvaluationReport(
            operation=operation,
            pret=not blockers,
            modele_code=getattr(model, "code", None),
            modele_version=getattr(model, "version", None),
            regle_risque_code=risk_rule_code,
            regle_risque_version=risk_rule_version,
            score=getattr(result, "score", None),
            classe=classe or getattr(result, "classe", None),
            statut_administratif=statut_administratif,
            niveau=getattr(result, "niveau", None),
            niveau_risque=risk,
            constats=findings,
            blocages=blockers,
            alertes=alerts,
        )

    @staticmethod
    async def _automatic_preview(
        db: AsyncSession,
        *,
        certification: Certification,
        object_type: str,
        prefix: str = "",
    ) -> tuple[Any | None, ScoreEvaluationInput | None, list[AutomaticEvaluationFinding], list[str], list[str]]:
        pipeline = await AutomaticScoringService._pipeline(db, certification)
        metrics, findings, blockers, alerts = AutomaticScoringService._metrics(certification, pipeline, prefix=prefix)
        try:
            model = await ScoringService.resolve_model(db, object_type=object_type, model_id=None)
        except HTTPException as exc:
            blockers.append(str(exc.detail))
            return None, None, findings, blockers, alerts
        snapshot = {
            "origine": "PARCOURS_AUTOMATIQUE",
            "certification_id": str(certification.id),
            "fiche_collecte_id": str(pipeline["fiche"].id) if pipeline["fiche"] else None,
            "dossier_verification_id": str(pipeline["verification"].id) if pipeline["verification"] else None,
            "controle_fuccs_id": str(pipeline["control"].id) if pipeline["control"] else None,
            "validation_n1_id": str(pipeline["n1"].id) if pipeline["n1"] else None,
            "validation_n2_id": str(pipeline["n2"].id) if pipeline["n2"] else None,
            "integration_bnec_id": str(pipeline["integration"].id) if pipeline["integration"] else None,
            "indicateurs": {key: str(value) for key, value in metrics.items()},
        }
        payload = AutomaticScoringService._input_for_model(
            model, metrics, object_type=object_type, source_snapshot=snapshot, blockers=blockers
        )
        try:
            preview = await ScoringService.compute(db, model=model, payload=payload)
        except HTTPException as exc:
            blockers.append(str(exc.detail))
            return model, None, findings, blockers, alerts
        risk, _ = AutomaticScoringService._risk_from_model(model, preview.score)
        if risk:
            findings.append(_finding("NIVEAU_RISQUE", "Niveau de risque", "INFORMATION", "Niveau déterminé par la règle publiée du modèle.", preview.score))
        return (model, payload, findings, blockers, alerts)

    @staticmethod
    async def evaluate_enterprise(
        db: AsyncSession,
        *,
        enterprise_id: UUID,
        actor: AuthContext,
        request,
    ) -> AutomaticEvaluationResponse:
        from app.repositories.scoring_repository import ScoringRepository
        enterprise_item = await ScoringRepository.get_enterprise(db, enterprise_id)
        if enterprise_item is None:
            raise HTTPException(404, "Entreprise introuvable.")
        certifications = list((await db.scalars(select(Certification).where(Certification.entreprise_id == enterprise_id))).all())
        findings: list[AutomaticEvaluationFinding] = []
        blockers: list[str] = []
        alerts: list[str] = []
        if not certifications:
            blockers.append("Aucune certification n'est rattachée à cette entreprise.")
        aggregate: dict[str, list[Decimal]] = {}
        for certification in certifications:
            pipeline = await AutomaticScoringService._pipeline(db, certification)
            metrics, local_findings, local_blockers, local_alerts = AutomaticScoringService._metrics(
                certification, pipeline, prefix=certification.identifiant_national
            )
            findings.extend(local_findings)
            blockers.extend(local_blockers)
            alerts.extend(local_alerts)
            for code, value in metrics.items():
                aggregate.setdefault(code, []).append(value)
        metrics = {
            code: sum(values, Decimal("0")) / Decimal(len(values))
            for code, values in aggregate.items()
            if values
        }
        try:
            model = await ScoringService.resolve_model(db, object_type=MODEL_OBJECT_ENTERPRISE, model_id=None)
        except HTTPException as exc:
            blockers.append(str(exc.detail))
            report = AutomaticScoringService._report(operation="CLASSIFICATION_ENTREPRISE", findings=findings, blockers=blockers, alerts=alerts)
            return AutomaticEvaluationResponse(execute=False, resultat=None, rapport=report)
        payload = AutomaticScoringService._input_for_model(
            model,
            metrics,
            object_type=MODEL_OBJECT_ENTERPRISE,
            source_snapshot={
                "origine": "PARCOURS_AUTOMATIQUE",
                "entreprise_id": str(enterprise_id),
                "certifications_prises_en_compte": [str(item.id) for item in certifications],
                "indicateurs_moyens": {key: str(value) for key, value in metrics.items()},
            },
            blockers=blockers,
        )
        try:
            preview = await ScoringService.compute(db, model=model, payload=payload)
        except HTTPException as exc:
            blockers.append(str(exc.detail))
            preview = None
        risk, risk_rule = AutomaticScoringService._risk_from_model(model, preview.score if preview else None)
        report = AutomaticScoringService._report(operation="CLASSIFICATION_ENTREPRISE", findings=findings, blockers=blockers, alerts=alerts, model=model, result=preview, risk=risk, risk_rule_code=risk_rule, risk_rule_version=model.version if risk_rule else None)
        if blockers or preview is None:
            return AutomaticEvaluationResponse(execute=False, resultat=None, rapport=report)
        result = await ScoringService.evaluate_enterprise(db, enterprise_id=enterprise_id, payload=payload, actor=actor, request=request)
        return AutomaticEvaluationResponse(execute=True, resultat=result.model_dump(mode="json"), rapport=report)

    @staticmethod
    async def calculate_infc(
        db: AsyncSession,
        *,
        certification_id: UUID,
        actor: AuthContext,
        request,
    ) -> AutomaticEvaluationResponse:
        certification = await db.get(Certification, certification_id)
        if certification is None:
            raise HTTPException(404, "Certification introuvable.")
        model, payload, findings, blockers, alerts = await AutomaticScoringService._automatic_preview(
            db, certification=certification, object_type=MODEL_OBJECT_INFC
        )
        preview = None
        if model and payload:
            try:
                preview = await ScoringService.compute(db, model=model, payload=payload)
            except HTTPException as exc:
                blockers.append(str(exc.detail))
        risk, risk_rule = AutomaticScoringService._risk_from_model(model, preview.score if model and preview else None)
        report = AutomaticScoringService._report(operation="INFC", findings=findings, blockers=blockers, alerts=alerts, model=model, result=preview, risk=risk, risk_rule_code=risk_rule, risk_rule_version=model.version if model and risk_rule else None)
        if blockers or payload is None:
            return AutomaticEvaluationResponse(execute=False, resultat=None, rapport=report)
        result = await ScoringService.calculate_infc(db, certification_id=certification_id, payload=payload, actor=actor, request=request)
        return AutomaticEvaluationResponse(execute=True, resultat=result.model_dump(mode="json"), rapport=report)

    @staticmethod
    async def _sncc_rule(db: AsyncSession) -> RegleMetier | None:
        # `regles_metier.code` contient le code physique versionné, par
        # exemple SNCC_CLASSIFICATION_MATRIX__V1_0. La résolution doit donc
        # utiliser le code logique stocké dans les paramètres.
        return await resolve_business_rule(
            db,
            "SNCC_CLASSIFICATION_MATRIX",
        )

    @staticmethod
    def _sncc_row(rule: RegleMetier, score: Decimal) -> dict[str, Any] | None:
        params = rule.parametres if isinstance(rule.parametres, dict) else {}
        for row in params.get("rows", params.get("matrice", [])) or []:
            if not isinstance(row, dict):
                continue
            try:
                minimum_value = row.get("min", row.get("score_min"))
                maximum_value = row.get("max", row.get("score_max"))
                minimum = Decimal(str(minimum_value)) if minimum_value is not None else None
                maximum = Decimal(str(maximum_value)) if maximum_value is not None else None
            except (InvalidOperation, TypeError, ValueError):
                continue
            if (minimum is None or score >= minimum) and (maximum is None or score <= maximum):
                return row
        return None

    @staticmethod
    def _sncc_value(row: dict[str, Any] | None, *keys: str) -> str | None:
        if not row:
            return None
        for key in keys:
            value = row.get(key)
            if value is not None and str(value).strip():
                return str(value).strip().upper()
        return None

    @staticmethod
    def _sncc_priority_status(
        certification: Certification,
    ) -> tuple[str | None, str | None]:
        """Applique les statuts SNCC imposés par la situation du certificat.

        La matrice reste la source de la classe et du risque. Ses statuts VA
        et RE décrivent un classement normal par score ; ils ne peuvent pas
        masquer une expiration, un retrait, une suspension ou une preuve
        documentaire non vérifiée.
        """
        current_status = _key(certification.statut)

        # L'expiration est un fait objectif et reste prioritaire lorsqu'une
        # copie doit aussi être vérifiée. Les deux raisons restent visibles
        # séparément dans la fiche du certificat.
        if (
            certification.date_expiration is not None
            and certification.date_expiration < date.today()
        ) or current_status in {"EXPIRE", "EXPIREE"}:
            return "EX", "Statut EX appliqué : la date d'expiration est dépassée."
        if current_status in {"RETIRE", "RETIREE", "RETIRED"}:
            return "RT", "Statut RT appliqué : le certificat est retiré."
        if current_status in {"SUSPENDU", "SUSPENDUE", "SUSPENSION"}:
            return "SU", "Statut SU appliqué : le certificat est suspendu."
        if current_status in {"A_VERIFIER", "A_VERIFIE", "EN_VERIFICATION"} or (
            certification.authenticite_verifiee is not True
        ):
            return (
                "VE",
                "Statut VE appliqué : l'authenticité documentaire reste à vérifier.",
            )
        return None, None

    @staticmethod
    async def classify_sncc(
        db: AsyncSession,
        *,
        certification_id: UUID,
        actor: AuthContext,
        request,
    ) -> AutomaticEvaluationResponse:
        certification = await db.get(Certification, certification_id)
        if certification is None:
            raise HTTPException(404, "Certification introuvable.")
        model, payload, findings, blockers, alerts = await AutomaticScoringService._automatic_preview(
            db, certification=certification, object_type=MODEL_OBJECT_INFC
        )
        preview = None
        if model and payload:
            try:
                preview = await ScoringService.compute(db, model=model, payload=payload)
            except HTTPException as exc:
                blockers.append(str(exc.detail))
        rule = await AutomaticScoringService._sncc_rule(db)
        row = AutomaticScoringService._sncc_row(rule, preview.score) if rule and preview else None
        if rule is None:
            blockers.append("Aucune matrice SNCC publiée active (SNCC_CLASSIFICATION_MATRIX) n'est disponible.")
        elif row is None:
            blockers.append("Le score automatique ne correspond à aucune ligne de la matrice SNCC publiée.")
        classe = AutomaticScoringService._sncc_value(row, "classe", "class_code")
        matrix_status = AutomaticScoringService._sncc_value(
            row, "statut_administratif", "statut", "administrative_status"
        )
        if matrix_status and matrix_status not in {"VA", "RE"}:
            # Compatibilité : une ancienne matrice pouvait associer SU ou RT à
            # une tranche de score. Ces statuts ne doivent plus être produits
            # par le score seul ; ils relèvent d'un fait métier prioritaire.
            findings.append(
                _finding(
                    "SNCC_STATUT_MATRICE_NORMALISE",
                    "Statut normal de la matrice",
                    "NORMALISE",
                    f"Le statut {matrix_status} de la matrice est traité comme RE : les statuts SU, RT, EX et VE sont réservés aux situations métier.",
                )
            )
            matrix_status = "RE"
        admin_status = matrix_status
        risk = AutomaticScoringService._sncc_value(
            row, "niveau_risque", "risque", "risk_level"
        )
        if row and not classe:
            blockers.append("La ligne applicable de la matrice SNCC ne précise pas la classe.")
        if row and not matrix_status:
            blockers.append("La ligne applicable de la matrice SNCC ne précise pas le statut administratif.")
        if row and not risk:
            blockers.append("La ligne applicable de la matrice SNCC ne précise pas le niveau de risque.")
        priority_status, priority_reason = AutomaticScoringService._sncc_priority_status(
            certification
        )
        if priority_status:
            admin_status = priority_status
            findings.append(
                _finding(
                    "SNCC_STATUT_PRIORITAIRE",
                    "Statut administratif prioritaire",
                    "APPLIQUE",
                    priority_reason or "Situation métier prioritaire appliquée.",
                )
            )
            alerts.append(
                f"Le statut SNCC normal {matrix_status or 'non renseigné'} est remplacé par {priority_status}."
            )
        report = AutomaticScoringService._report(
            operation="SNCC", findings=findings, blockers=blockers, alerts=alerts,
            model=model, result=preview, classe=classe, risk=risk, statut_administratif=admin_status,
            risk_rule_code=rule.code if rule else None,
            risk_rule_version=rule.version if rule else None,
        )
        if blockers or preview is None or row is None:
            return AutomaticEvaluationResponse(execute=False, resultat=None, rapport=report)

        payload_sncc = SnccCreateRequest(
            classe=classe or "",
            statut_administratif=admin_status or "",
            niveau_risque=risk or "",
            justification=(
                f"Classement automatique issu du modèle INFC publié {model.code} v{model.version} "
                f"(score {preview.score}) et de la matrice SNCC publiée {rule.code} v{rule.version}. "
                + (
                    f"Statut administratif prioritaire {admin_status} : {priority_reason}"
                    if priority_status
                    else f"Statut administratif normal {admin_status} issu de la matrice."
                )
            ),
            date_effet=date.today(),
        )
        classe, admin_status, risk_level = validated_sncc_values(payload_sncc)
        from app.repositories.scoring_repository import ScoringRepository
        current = await ScoringRepository.current_sncc(db, certification_id)
        if current and current.date_effet and current.date_effet > date.today():
            report.blocages.append("Le classement SNCC courant possède une date d'effet future.")
            report.pret = False
            return AutomaticEvaluationResponse(execute=False, resultat=None, rapport=report)
        if current and current.date_effet == date.today():
            current.classe = classe
            current.statut_administratif = admin_status
            current.niveau_risque = risk_level
            current.justification = payload_sncc.justification
            current.valide_par_id = actor.user.id
            item = current
            action = "SNCC_AUTOMATIC_UPDATE"
        else:
            if current:
                current.date_fin = date.today() - timedelta(days=1)
            item = ClassementSncc(
                certification_id=certification_id,
                classe=classe,
                statut_administratif=admin_status,
                niveau_risque=risk_level,
                justification=payload_sncc.justification,
                date_effet=date.today(),
                date_fin=None,
                valide_par_id=actor.user.id,
                statut="VALIDE",
            )
            db.add(item)
            action = "SNCC_AUTOMATIC_CLASSIFY"
        await db.flush()
        await write_audit_event(
            db, action=action, categorie="SCORING", resultat="SUCCES",
            utilisateur_id=actor.user.id, ressource_type="classement_sncc",
            ressource_id=item.id, adresse_ip=client_ip(request),
            valeurs_apres={"classe": classe, "statut_administratif": admin_status, "niveau_risque": risk_level},
            contexte={
                "modele_infc": f"{model.code}:{model.version}",
                "matrice_sncc": f"{rule.code}:{rule.version}",
                "statut_matrice": matrix_status,
                "statut_prioritaire": priority_status,
            },
        )
        await db.commit()
        await db.refresh(item)
        return AutomaticEvaluationResponse(
            execute=True,
            resultat={
                "id": str(item.id), "certification_id": str(certification_id),
                "classe": item.classe, "statut_administratif": item.statut_administratif,
                "niveau_risque": item.niveau_risque, "date_effet": item.date_effet.isoformat(),
            },
            rapport=report,
        )
