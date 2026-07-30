"""
Service métier — Gouvernance / Qualité / Continuité.

RÈGLES DIRECTRICES
------------------
- journal d'audit en lecture seule ;
- aucune suppression physique ;
- règles métier versionnées et immuables après publication ;
- publications soumises à approbation avant diffusion ;
- rapports sensibles restent des demandes historisées et produisent un
  document privé ;
- archives motivées avec conservation minimale par défaut de 10 ans ;
- sauvegardes : l'API supervise et trace, mais n'exécute pas de commande
  système ou de shell ;
- incidents : déclaration -> affectation -> résolution -> clôture ;
- séparation entre préparation et décision lorsque le modèle le permet.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import re
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.archive import Archive
from app.models.decision_institutionnelle import DecisionInstitutionnelle
from app.models.notification import Notification
from app.models.incident import Incident
from app.models.plan_action import PlanAction
from app.models.publication import Publication
from app.models.rapport_genere import RapportGenere
from app.models.regle_metier import RegleMetier
from app.models.revue_qualite import RevueQualite
from app.models.sauvegarde import Sauvegarde
from app.repositories.governance_repository import GovernanceRepository
from app.rules.business_rule_resolver import rule_logical_code
from app.rules.collecte_completeness import (
    validate_parameters as validate_collecte_completeness_parameters,
)
from app.rules.codification import (
    CODIFICATION_PREFIX,
    validate_codification_parameters,
)
from app.schemas.governance import *
from app.services.auth_service import AuthContext


def ip(request: Request | None) -> str | None:
    return request.client.host if request and request.client else None


def txt(value):
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def parse_iso(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            422,
            f"{field} doit être au format YYYY-MM-DD.",
        ) from exc


def plus_years(start: date, years: int) -> date:
    try:
        return start.replace(year=start.year + years)
    except ValueError:
        return start.replace(
            month=2,
            day=28,
            year=start.year + years,
        )


def normalize_rule_version(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_")
    if not value:
        raise HTTPException(422, "Version de règle invalide.")
    return value.upper()


def build_physical_rule_code(logical_code: str, version: str) -> str:
    logical = re.sub(
        r"[^A-Za-z0-9_]+",
        "_",
        logical_code.strip().upper(),
    ).strip("_")
    if not logical:
        raise HTTPException(422, "Code logique de règle invalide.")
    physical = f"{logical}__V{normalize_rule_version(version)}"
    if len(physical) > 255:
        raise HTTPException(422, "Code physique de règle trop long.")
    return physical


def audit_response(item):
    user = item.utilisateur
    user_name = None
    if user is not None:
        user_name = " ".join(
            value for value in (user.prenoms, user.nom) if value
        ).strip() or user.email
    return AuditEventResponse(
        id=item.id,
        utilisateur_id=item.utilisateur_id,
        utilisateur_nom=user_name,
        utilisateur_email=user.email if user is not None else None,
        action=item.action,
        categorie=item.categorie,
        ressource_type=item.ressource_type,
        ressource_id=item.ressource_id,
        adresse_ip=item.adresse_ip,
        contexte=item.contexte,
        valeurs_avant=item.valeurs_avant,
        valeurs_apres=item.valeurs_apres,
        empreinte=item.empreinte,
        resultat=item.resultat,
        date_evenement=item.date_evenement,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


class GovernanceService:

    # ========================================================
    # COMMUN
    # ========================================================

    @staticmethod
    async def require_active_user(db, user_id: UUID):
        user = await GovernanceRepository.get_user(db, user_id)
        if user is None:
            raise HTTPException(404, "Utilisateur introuvable.")
        if (user.statut or "").upper() != "ACTIF":
            raise HTTPException(409, "Utilisateur non actif.")
        return user

    # ========================================================
    # RÈGLES MÉTIER
    # ========================================================

    @staticmethod
    async def require_rule(db, rule_id: UUID):
        item = await GovernanceRepository.get_rule(db, rule_id)
        if item is None:
            raise HTTPException(404, "Règle métier introuvable.")
        return item

    @staticmethod
    def require_rule_draft(item):
        if (item.statut or "").upper() != "BROUILLON":
            raise HTTPException(
                409,
                "Une règle publiée/retirée est immuable. Clonez-la.",
            )

    @staticmethod
    def rule_response(item):
        return BusinessRuleResponse(
            id=item.id,
            code=item.code,
            logical_code=rule_logical_code(item),
            famille=item.famille,
            libelle=item.libelle,
            description=item.description,
            version=item.version,
            parametres=item.parametres,
            date_debut_effet=item.date_debut_effet,
            date_fin_effet=item.date_fin_effet,
            reference_approbation=item.reference_approbation,
            approuve_par_id=item.approuve_par_id,
            statut=item.statut,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    async def list_rules(db, *, logical_code, famille, statut_filter):
        rows = await GovernanceRepository.list_rules(
            db,
            logical_code=logical_code,
            famille=famille,
            statut=statut_filter,
        )
        return [GovernanceService.rule_response(x) for x in rows]

    @staticmethod
    async def active_rule(db, logical_code: str):
        today = date.today()
        rows = await GovernanceRepository.published_rules(db)
        logical_code = logical_code.strip().upper()
        for row in rows:
            if rule_logical_code(row) != logical_code:
                continue
            if row.date_debut_effet and row.date_debut_effet > today:
                continue
            if row.date_fin_effet and row.date_fin_effet < today:
                continue
            return GovernanceService.rule_response(row)
        raise HTTPException(404, "Aucune version publiée active.")

    @staticmethod
    async def create_rule(db, *, payload, actor, request):
        physical_code = build_physical_rule_code(
            payload.logical_code,
            payload.version,
        )
        if await GovernanceRepository.find_physical_rule_code(
            db,
            physical_code,
        ):
            raise HTTPException(409, "Cette version de règle existe déjà.")

        params = dict(payload.parametres)
        params["_logical_code"] = payload.logical_code.strip().upper()

        item = RegleMetier(
            code=physical_code,
            famille=txt(payload.famille.upper() if payload.famille else None),
            libelle=payload.libelle.strip(),
            description=txt(payload.description),
            version=payload.version.strip(),
            parametres=params,
            date_debut_effet=payload.date_debut_effet,
            date_fin_effet=None,
            reference_approbation=None,
            approuve_par_id=None,
            statut="BROUILLON",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="GOV_RULE_CREATE",
            categorie="GOUVERNANCE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="regle_metier",
            ressource_id=item.id,
            adresse_ip=ip(request),
            valeurs_apres={
                "logical_code": rule_logical_code(item),
                "code": item.code,
                "version": item.version,
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.rule_response(item)

    @staticmethod
    async def update_rule(db, *, rule_id, payload, actor, request):
        item = await GovernanceService.require_rule(db, rule_id)
        GovernanceService.require_rule_draft(item)

        for key, value in payload.model_dump(exclude_unset=True).items():
            if key == "parametres" and value is not None:
                params = dict(value)
                params["_logical_code"] = rule_logical_code(item)
                value = params
            elif key == "famille" and value:
                value = value.strip().upper()
            else:
                value = txt(value)
            setattr(item, key, value)

        await write_audit_event(
            db,
            action="GOV_RULE_UPDATE",
            categorie="GOUVERNANCE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="regle_metier",
            ressource_id=item.id,
            adresse_ip=ip(request),
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.rule_response(item)

    @staticmethod
    async def clone_rule(db, *, rule_id, payload, actor, request):
        source = await GovernanceService.require_rule(db, rule_id)
        logical_code = rule_logical_code(source)
        physical_code = build_physical_rule_code(
            logical_code,
            payload.version,
        )
        if await GovernanceRepository.find_physical_rule_code(
            db,
            physical_code,
        ):
            raise HTTPException(409, "La version cible existe déjà.")

        params = dict(source.parametres or {})
        params["_logical_code"] = logical_code

        item = RegleMetier(
            code=physical_code,
            famille=source.famille,
            libelle=txt(payload.libelle) or source.libelle,
            description=source.description,
            version=payload.version.strip(),
            parametres=params,
            date_debut_effet=payload.date_debut_effet,
            date_fin_effet=None,
            reference_approbation=None,
            approuve_par_id=None,
            statut="BROUILLON",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="GOV_RULE_CLONE",
            categorie="GOUVERNANCE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="regle_metier",
            ressource_id=item.id,
            adresse_ip=ip(request),
            contexte={"source_rule_id": str(source.id)},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.rule_response(item)

    @staticmethod
    async def publish_rule(db, *, rule_id, payload, actor, request):
        item = await GovernanceService.require_rule(db, rule_id)
        GovernanceService.require_rule_draft(item)

        logical = rule_logical_code(item)

        if logical == "COLLECTE_COMPLETUDE":
            validation = validate_collecte_completeness_parameters(
                item.parametres or {},
            )
            if validation.errors:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "COLLECTE_COMPLETUDE ne peut pas être publiée : "
                        + " | ".join(validation.errors)
                    ),
                )

            params = dict(validation.normalized)
            params["_logical_code"] = logical
            item.parametres = params

        if logical.startswith(CODIFICATION_PREFIX):
            validation = validate_codification_parameters(
                logical,
                item.parametres or {},
            )
            if validation.errors:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Le modèle de codification ne peut pas être publié : "
                        + " | ".join(validation.errors)
                    ),
                )

            params = dict(validation.normalized)
            params["_logical_code"] = logical
            if validation.warnings:
                params["_publication_warnings"] = validation.warnings
            item.parametres = params

        # Clôture automatiquement une version publiée qui chevaucherait
        # la nouvelle date d'effet.
        replaced = []
        for previous in await GovernanceRepository.published_rules(db):
            if previous.id == item.id:
                continue
            if rule_logical_code(previous) != logical:
                continue
            if (
                previous.date_fin_effet is None
                or previous.date_fin_effet >= payload.date_debut_effet
            ):
                previous.date_fin_effet = (
                    payload.date_debut_effet
                    - __import__("datetime").timedelta(days=1)
                )
                previous.statut = "RETIRE"
                replaced.append(str(previous.id))

        item.date_debut_effet = payload.date_debut_effet
        item.reference_approbation = payload.reference_approbation.strip()
        item.approuve_par_id = actor.user.id
        item.statut = "PUBLIE"

        await write_audit_event(
            db,
            action="GOV_RULE_PUBLISH",
            categorie="GOUVERNANCE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="regle_metier",
            ressource_id=item.id,
            adresse_ip=ip(request),
            valeurs_apres={
                "logical_code": logical,
                "version": item.version,
                "date_debut_effet": item.date_debut_effet.isoformat(),
                "reference_approbation": item.reference_approbation,
                "statut": item.statut,
            },
            contexte={
                "versions_retirees": replaced,
                "commentaire": txt(payload.commentaire),
            },
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.rule_response(item)

    @staticmethod
    async def retire_rule(db, *, rule_id, payload, actor, request):
        item = await GovernanceService.require_rule(db, rule_id)
        if (item.statut or "").upper() != "PUBLIE":
            raise HTTPException(409, "Seule une règle publiée peut être retirée.")
        if item.date_debut_effet and payload.date_fin_effet < item.date_debut_effet:
            raise HTTPException(422, "Date de retrait incohérente.")

        item.date_fin_effet = payload.date_fin_effet
        item.statut = "RETIRE"

        await write_audit_event(
            db,
            action="GOV_RULE_RETIRE",
            categorie="GOUVERNANCE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="regle_metier",
            ressource_id=item.id,
            adresse_ip=ip(request),
            contexte={"motif": payload.motif.strip()},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.rule_response(item)

    # ========================================================
    # QUALITÉ / PLANS D'ACTION
    # ========================================================

    @staticmethod
    async def require_review(db, review_id):
        item = await GovernanceRepository.get_quality_review(db, review_id)
        if item is None:
            raise HTTPException(404, "Revue qualité introuvable.")
        return item

    @staticmethod
    async def review_response(db, item):
        return QualityReviewResponse(
            id=item.id,
            periode_debut=item.periode_debut,
            periode_fin=item.periode_fin,
            perimetre=item.perimetre,
            resultat_global=item.resultat_global,
            constats=item.constats,
            preuves=item.preuves,
            responsable_id=item.responsable_id,
            date_validation=item.date_validation,
            statut=item.statut,
            plans_action_count=(
                await GovernanceRepository.action_plan_count_for_review(
                    db,
                    item.id,
                )
            ),
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    async def list_reviews(db, **filters):
        rows, total = await GovernanceRepository.list_quality_reviews(
            db,
            **filters,
        )
        return {
            "total": total,
            "limit": filters["limit"],
            "offset": filters["offset"],
            "items": [
                await GovernanceService.review_response(db, x)
                for x in rows
            ],
        }

    @staticmethod
    async def create_review(db, *, payload, actor, request):
        start = parse_iso(payload.periode_debut, "periode_debut")
        end = parse_iso(payload.periode_fin, "periode_fin")
        if end < start:
            raise HTTPException(422, "Période de revue incohérente.")

        await GovernanceService.require_active_user(
            db,
            payload.responsable_id,
        )

        item = RevueQualite(
            periode_debut=start.isoformat(),
            periode_fin=end.isoformat(),
            perimetre=payload.perimetre.strip(),
            resultat_global=txt(payload.resultat_global),
            constats=payload.constats,
            preuves=payload.preuves,
            responsable_id=payload.responsable_id,
            date_validation=None,
            statut="BROUILLON",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="QUALITY_REVIEW_CREATE",
            categorie="QUALITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="revue_qualite",
            ressource_id=item.id,
            adresse_ip=ip(request),
        )
        await db.commit()
        await db.refresh(item)
        return await GovernanceService.review_response(db, item)

    @staticmethod
    async def update_review(db, *, review_id, payload, actor, request):
        item = await GovernanceService.require_review(db, review_id)
        if item.date_validation is not None:
            raise HTTPException(409, "Une revue validée est verrouillée.")

        changes = payload.model_dump(exclude_unset=True)
        if changes.get("responsable_id"):
            await GovernanceService.require_active_user(
                db,
                changes["responsable_id"],
            )

        start = parse_iso(
            changes.get("periode_debut", item.periode_debut),
            "periode_debut",
        )
        end = parse_iso(
            changes.get("periode_fin", item.periode_fin),
            "periode_fin",
        )
        if end < start:
            raise HTTPException(422, "Période de revue incohérente.")
        changes["periode_debut"] = start.isoformat()
        changes["periode_fin"] = end.isoformat()

        for key, value in changes.items():
            setattr(item, key, txt(value))

        await write_audit_event(
            db,
            action="QUALITY_REVIEW_UPDATE",
            categorie="QUALITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="revue_qualite",
            ressource_id=item.id,
            adresse_ip=ip(request),
        )
        await db.commit()
        await db.refresh(item)
        return await GovernanceService.review_response(db, item)

    @staticmethod
    async def validate_review(db, *, review_id, payload, actor, request):
        item = await GovernanceService.require_review(db, review_id)
        if item.date_validation is not None:
            return await GovernanceService.review_response(db, item)

        item.resultat_global = payload.resultat_global.strip()
        item.date_validation = date.today()
        item.statut = "VALIDEE"

        await write_audit_event(
            db,
            action="QUALITY_REVIEW_VALIDATE",
            categorie="QUALITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="revue_qualite",
            ressource_id=item.id,
            adresse_ip=ip(request),
            contexte={"commentaire": txt(payload.commentaire)},
        )
        await db.commit()
        await db.refresh(item)
        return await GovernanceService.review_response(db, item)

    @staticmethod
    async def require_action_plan(db, plan_id):
        item = await GovernanceRepository.get_action_plan(db, plan_id)
        if item is None:
            raise HTTPException(404, "Plan d'action introuvable.")
        return item

    @staticmethod
    def plan_response(item):
        return ActionPlanResponse(
            id=item.id,
            revue_qualite_id=item.revue_qualite_id,
            titre=item.titre,
            objectif=item.objectif,
            responsable_id=item.responsable_id,
            date_debut=item.date_debut,
            date_echeance=item.date_echeance,
            priorite=item.priorite,
            indicateur=item.indicateur,
            progression=item.progression,
            date_cloture=item.date_cloture,
            statut=item.statut,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    async def list_action_plans(db, **filters):
        rows, total = await GovernanceRepository.list_action_plans(
            db,
            **filters,
        )
        return {
            "total": total,
            "limit": filters["limit"],
            "offset": filters["offset"],
            "items": [GovernanceService.plan_response(x) for x in rows],
        }

    @staticmethod
    async def create_action_plan(db, *, payload, actor, request):
        if payload.revue_qualite_id:
            await GovernanceService.require_review(
                db,
                payload.revue_qualite_id,
            )
        await GovernanceService.require_active_user(
            db,
            payload.responsable_id,
        )
        start = payload.date_debut or date.today()
        if payload.date_echeance < start:
            raise HTTPException(422, "Échéance antérieure au début.")

        item = PlanAction(
            revue_qualite_id=payload.revue_qualite_id,
            titre=payload.titre.strip(),
            objectif=payload.objectif.strip(),
            responsable_id=payload.responsable_id,
            date_debut=start,
            date_echeance=payload.date_echeance,
            priorite=txt(payload.priorite),
            indicateur=payload.indicateur.strip(),
            progression=0,
            date_cloture=None,
            statut="OUVERT",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="ACTION_PLAN_CREATE",
            categorie="QUALITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="plan_action",
            ressource_id=item.id,
            adresse_ip=ip(request),
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.plan_response(item)

    @staticmethod
    async def update_action_plan(db, *, plan_id, payload, actor, request):
        item = await GovernanceService.require_action_plan(db, plan_id)
        if item.date_cloture:
            raise HTTPException(409, "Plan clôturé.")

        changes = payload.model_dump(exclude_unset=True)
        if changes.get("responsable_id"):
            await GovernanceService.require_active_user(
                db,
                changes["responsable_id"],
            )

        start = changes.get("date_debut", item.date_debut)
        due = changes.get("date_echeance", item.date_echeance)
        if start and due and due < start:
            raise HTTPException(422, "Période du plan incohérente.")

        for key, value in changes.items():
            setattr(item, key, txt(value))

        await write_audit_event(
            db,
            action="ACTION_PLAN_UPDATE",
            categorie="QUALITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="plan_action",
            ressource_id=item.id,
            adresse_ip=ip(request),
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.plan_response(item)

    @staticmethod
    async def progress_action_plan(db, *, plan_id, payload, actor, request):
        item = await GovernanceService.require_action_plan(db, plan_id)
        if item.date_cloture:
            raise HTTPException(409, "Plan clôturé.")
        item.progression = payload.progression
        item.statut = (
            "TERMINE"
            if payload.progression == 100
            else "EN_COURS"
        )

        await write_audit_event(
            db,
            action="ACTION_PLAN_PROGRESS",
            categorie="QUALITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="plan_action",
            ressource_id=item.id,
            adresse_ip=ip(request),
            valeurs_apres={
                "progression": item.progression,
                "statut": item.statut,
            },
            contexte={"commentaire": txt(payload.commentaire)},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.plan_response(item)

    @staticmethod
    async def close_action_plan(db, *, plan_id, payload, actor, request):
        item = await GovernanceService.require_action_plan(db, plan_id)
        if item.date_cloture:
            return GovernanceService.plan_response(item)

        item.progression = 100
        item.date_cloture = date.today()
        item.statut = "CLOTURE"

        await write_audit_event(
            db,
            action="ACTION_PLAN_CLOSE",
            categorie="QUALITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="plan_action",
            ressource_id=item.id,
            adresse_ip=ip(request),
            contexte={"resultat": payload.resultat.strip()},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.plan_response(item)

    # ========================================================
    # DÉCISIONS INSTITUTIONNELLES
    # ========================================================

    @staticmethod
    async def require_decision(db, decision_id):
        item = await GovernanceRepository.get_decision(db, decision_id)
        if item is None:
            raise HTTPException(404, "Décision institutionnelle introuvable.")
        return item

    @staticmethod
    def decision_response(item):
        return InstitutionalDecisionResponse(
            id=item.id,
            ressource_type=item.ressource_type,
            ressource_id=item.ressource_id,
            type_decision=item.type_decision,
            titre=item.titre,
            contexte=item.contexte,
            constats=item.constats,
            risques=item.risques,
            options=item.options,
            decision=item.decision,
            recommandation=item.recommandation,
            autorite=item.autorite,
            decide_par_id=item.decide_par_id,
            date_decision=item.date_decision,
            priorite=item.priorite,
            statut=item.statut,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    async def list_decisions(db, **filters):
        rows, total = await GovernanceRepository.list_decisions(
            db,
            **filters,
        )
        return {
            "total": total,
            "limit": filters["limit"],
            "offset": filters["offset"],
            "items": [GovernanceService.decision_response(x) for x in rows],
        }

    @staticmethod
    async def create_decision(db, *, payload, actor, request):
        item = DecisionInstitutionnelle(
            ressource_type=payload.ressource_type.strip().upper(),
            ressource_id=payload.ressource_id,
            type_decision=payload.type_decision.strip().upper(),
            titre=payload.titre.strip(),
            contexte=payload.contexte.strip(),
            constats=payload.constats,
            risques=txt(payload.risques),
            options=txt(payload.options),
            decision=None,
            recommandation=txt(payload.recommandation),
            autorite=txt(payload.autorite),
            decide_par_id=None,
            date_decision=None,
            priorite=txt(payload.priorite),
            statut="BROUILLON",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="INSTITUTIONAL_DECISION_CREATE",
            categorie="GOUVERNANCE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="decision_institutionnelle",
            ressource_id=item.id,
            adresse_ip=ip(request),
        )
        for recipient in await GovernanceRepository.list_active_users(db):
            db.add(Notification(
                destinataire_utilisateur_id=recipient.id,
                canal="IN_APP",
                objet="Nouvelle décision institutionnelle",
                contenu=f"{item.titre} - priorité {item.priorite or 'NORMALE'}.",
                date_envoi=date.today(),
                nombre_tentatives=0,
                resultat="Disponible dans l'application",
                statut="ENVOYEE",
            ))
        await db.commit()
        await db.refresh(item)
        return GovernanceService.decision_response(item)

    @staticmethod
    async def update_decision(db, *, decision_id, payload, actor, request):
        item = await GovernanceService.require_decision(db, decision_id)
        if item.statut != "BROUILLON":
            raise HTTPException(409, "Seul un brouillon est modifiable.")

        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, key, txt(value))

        await write_audit_event(
            db,
            action="INSTITUTIONAL_DECISION_UPDATE",
            categorie="GOUVERNANCE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="decision_institutionnelle",
            ressource_id=item.id,
            adresse_ip=ip(request),
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.decision_response(item)

    @staticmethod
    async def submit_decision(db, *, decision_id, payload, actor, request):
        item = await GovernanceService.require_decision(db, decision_id)
        if item.statut != "BROUILLON":
            raise HTTPException(409, "Décision non soumissible.")
        item.statut = "SOUMISE"

        await write_audit_event(
            db,
            action="INSTITUTIONAL_DECISION_SUBMIT",
            categorie="GOUVERNANCE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="decision_institutionnelle",
            ressource_id=item.id,
            adresse_ip=ip(request),
            contexte={"commentaire": txt(payload.commentaire)},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.decision_response(item)

    @staticmethod
    async def pronounce_decision(db, *, decision_id, payload, actor, request):
        item = await GovernanceService.require_decision(db, decision_id)
        if item.statut != "SOUMISE":
            raise HTTPException(409, "La note doit être soumise avant décision.")

        item.decision = payload.decision.strip()
        item.decide_par_id = actor.user.id
        item.date_decision = date.today()
        item.statut = "DECIDEE"

        await write_audit_event(
            db,
            action="INSTITUTIONAL_DECISION_PRONOUNCE",
            categorie="GOUVERNANCE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="decision_institutionnelle",
            ressource_id=item.id,
            adresse_ip=ip(request),
            valeurs_apres={
                "decision": item.decision,
                "decide_par_id": str(item.decide_par_id),
                "date_decision": item.date_decision.isoformat(),
            },
            contexte={"justification": payload.justification.strip()},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.decision_response(item)

    # ========================================================
    # PUBLICATIONS
    # ========================================================

    @staticmethod
    async def require_publication(db, publication_id):
        item = await GovernanceRepository.get_publication(db, publication_id)
        if item is None:
            raise HTTPException(404, "Publication introuvable.")
        return item

    @staticmethod
    def publication_response(item):
        return PublicationResponse(
            id=item.id,
            ressource_type=item.ressource_type,
            ressource_id=item.ressource_id,
            objet=item.objet,
            perimetre=item.perimetre,
            niveau_confidentialite=item.niveau_confidentialite,
            demande_par_id=item.demande_par_id,
            date_demande=item.date_demande,
            decision=item.decision,
            autorite_approbation=item.autorite_approbation,
            approuve_par_id=item.approuve_par_id,
            date_approbation=item.date_approbation,
            reserve=item.reserve,
            date_publication=item.date_publication,
            statut=item.statut,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    async def list_publications(db, **filters):
        rows, total = await GovernanceRepository.list_publications(
            db,
            **filters,
        )
        return {
            "total": total,
            "limit": filters["limit"],
            "offset": filters["offset"],
            "items": [GovernanceService.publication_response(x) for x in rows],
        }

    @staticmethod
    async def create_publication(db, *, payload, actor, request):
        item = Publication(
            ressource_type=payload.ressource_type.strip().upper(),
            ressource_id=payload.ressource_id,
            objet=payload.objet.strip(),
            perimetre=payload.perimetre.strip(),
            niveau_confidentialite=payload.niveau_confidentialite.strip().upper(),
            demande_par_id=actor.user.id,
            date_demande=date.today(),
            decision=None,
            autorite_approbation=None,
            approuve_par_id=None,
            date_approbation=None,
            reserve=None,
            date_publication=None,
            statut="BROUILLON",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="PUBLICATION_CREATE",
            categorie="GOUVERNANCE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="publication",
            ressource_id=item.id,
            adresse_ip=ip(request),
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.publication_response(item)

    @staticmethod
    async def submit_publication(db, *, publication_id, payload, actor, request):
        item = await GovernanceService.require_publication(db, publication_id)
        if item.statut != "BROUILLON":
            raise HTTPException(409, "Publication non soumissible.")
        item.statut = "SOUMISE"

        await write_audit_event(
            db,
            action="PUBLICATION_SUBMIT",
            categorie="GOUVERNANCE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="publication",
            ressource_id=item.id,
            adresse_ip=ip(request),
            contexte={"commentaire": txt(payload.commentaire)},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.publication_response(item)

    @staticmethod
    async def approve_publication(db, *, publication_id, payload, actor, request):
        item = await GovernanceService.require_publication(db, publication_id)
        if item.statut != "SOUMISE":
            raise HTTPException(409, "Publication non soumise.")

        item.decision = payload.decision
        item.autorite_approbation = payload.autorite_approbation.strip()
        item.approuve_par_id = actor.user.id
        item.date_approbation = date.today()
        item.reserve = txt(payload.reserve)
        item.statut = (
            "APPROUVEE"
            if payload.decision == "APPROUVE"
            else "REJETEE"
        )

        await write_audit_event(
            db,
            action="PUBLICATION_APPROVAL",
            categorie="GOUVERNANCE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="publication",
            ressource_id=item.id,
            adresse_ip=ip(request),
            valeurs_apres={
                "decision": item.decision,
                "autorite_approbation": item.autorite_approbation,
                "date_approbation": item.date_approbation.isoformat(),
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.publication_response(item)

    @staticmethod
    async def publish_publication(db, *, publication_id, payload, actor, request):
        item = await GovernanceService.require_publication(db, publication_id)
        if item.statut != "APPROUVEE":
            raise HTTPException(409, "Publication non approuvée.")
        item.date_publication = payload.date_publication or date.today()
        item.statut = "PUBLIEE"

        await write_audit_event(
            db,
            action="PUBLICATION_PUBLISH",
            categorie="GOUVERNANCE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="publication",
            ressource_id=item.id,
            adresse_ip=ip(request),
            valeurs_apres={
                "date_publication": item.date_publication.isoformat(),
                "statut": item.statut,
            },
            contexte={"commentaire": txt(payload.commentaire)},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.publication_response(item)

    @staticmethod
    async def retire_publication(db, *, publication_id, payload, actor, request):
        item = await GovernanceService.require_publication(db, publication_id)
        if item.statut != "PUBLIEE":
            raise HTTPException(409, "Seule une publication publiée peut être retirée.")
        item.statut = "RETIREE"

        await write_audit_event(
            db,
            action="PUBLICATION_RETIRE",
            categorie="GOUVERNANCE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="publication",
            ressource_id=item.id,
            adresse_ip=ip(request),
            contexte={"motif": payload.motif.strip()},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.publication_response(item)

    # ========================================================
    # RAPPORTS
    # ========================================================

    @staticmethod
    async def require_report(db, report_id):
        item = await GovernanceRepository.get_generated_report(db, report_id)
        if item is None:
            raise HTTPException(404, "Rapport introuvable.")
        return item

    @staticmethod
    def report_response(item):
        return GeneratedReportResponse(
            id=item.id,
            code_modele=item.code_modele,
            nom_modele=item.nom_modele,
            categorie=item.categorie,
            demandeur_id=item.demandeur_id,
            filtres=item.filtres,
            sections=item.sections,
            format=item.format,
            periode_debut=item.periode_debut,
            periode_fin=item.periode_fin,
            date_demande=item.date_demande,
            date_generation=item.date_generation,
            document_id=item.document_id,
            resultat=item.resultat,
            statut=item.statut,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    async def list_reports(db, **filters):
        rows, total = await GovernanceRepository.list_generated_reports(
            db,
            **filters,
        )
        return {
            "total": total,
            "limit": filters["limit"],
            "offset": filters["offset"],
            "items": [GovernanceService.report_response(x) for x in rows],
        }

    @staticmethod
    async def create_report_request(db, *, payload, actor, request):
        if payload.periode_debut:
            start = parse_iso(payload.periode_debut, "periode_debut")
        else:
            start = None
        if payload.periode_fin:
            end = parse_iso(payload.periode_fin, "periode_fin")
        else:
            end = None
        if start and end and end < start:
            raise HTTPException(422, "Période de rapport incohérente.")

        item = RapportGenere(
            code_modele=payload.code_modele.strip().upper(),
            nom_modele=payload.nom_modele.strip(),
            categorie=payload.categorie.strip().upper(),
            demandeur_id=actor.user.id,
            filtres=payload.filtres,
            sections=payload.sections,
            format=payload.format,
            periode_debut=start.isoformat() if start else None,
            periode_fin=end.isoformat() if end else None,
            date_demande=date.today(),
            date_generation=None,
            document_id=None,
            resultat=None,
            statut="DEMANDE",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="REPORT_REQUEST_CREATE",
            categorie="REPORTING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="rapport_genere",
            ressource_id=item.id,
            adresse_ip=ip(request),
            valeurs_apres={
                "code_modele": item.code_modele,
                "format": item.format,
                "categorie": item.categorie,
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.report_response(item)

    @staticmethod
    async def start_report(db, *, report_id, payload, actor, request):
        item = await GovernanceService.require_report(db, report_id)
        if item.statut != "DEMANDE":
            raise HTTPException(409, "Rapport non démarrable.")
        item.statut = "EN_GENERATION"

        await write_audit_event(
            db,
            action="REPORT_GENERATION_START",
            categorie="REPORTING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="rapport_genere",
            ressource_id=item.id,
            adresse_ip=ip(request),
            contexte={"commentaire": txt(payload.commentaire)},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.report_response(item)

    @staticmethod
    async def complete_report(db, *, report_id, payload, actor, request):
        item = await GovernanceService.require_report(db, report_id)
        if item.statut not in {"DEMANDE", "EN_GENERATION"}:
            raise HTTPException(409, "Rapport non finalisable.")

        document = await GovernanceRepository.get_active_document(
            db,
            payload.document_id,
        )
        if document is None:
            raise HTTPException(404, "Document de rapport introuvable ou inactif.")

        item.document_id = payload.document_id
        item.resultat = txt(payload.resultat) or "Génération terminée."
        item.date_generation = date.today()
        item.statut = "GENERE"

        await write_audit_event(
            db,
            action="REPORT_GENERATION_COMPLETE",
            categorie="REPORTING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="rapport_genere",
            ressource_id=item.id,
            adresse_ip=ip(request),
            valeurs_apres={
                "document_id": str(item.document_id),
                "date_generation": item.date_generation.isoformat(),
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.report_response(item)

    @staticmethod
    async def fail_report(db, *, report_id, payload, actor, request):
        item = await GovernanceService.require_report(db, report_id)
        if item.statut == "GENERE":
            raise HTTPException(409, "Un rapport généré ne peut pas être passé en échec.")
        item.resultat = payload.resultat.strip()
        item.statut = "ECHEC"

        await write_audit_event(
            db,
            action="REPORT_GENERATION_FAIL",
            categorie="REPORTING",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="rapport_genere",
            ressource_id=item.id,
            adresse_ip=ip(request),
            contexte={"erreur": item.resultat},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.report_response(item)

    # ========================================================
    # AUDIT — LECTURE SEULE
    # ========================================================

    @staticmethod
    async def list_audit_events(db, **filters):
        rows, total = await GovernanceRepository.list_audit_events(
            db,
            **filters,
        )
        return AuditEventListResponse(
            total=total,
            limit=filters["limit"],
            offset=filters["offset"],
            items=[audit_response(x) for x in rows],
        )

    @staticmethod
    async def get_audit_event(db, event_id):
        item = await GovernanceRepository.get_audit_event(db, event_id)
        if item is None:
            raise HTTPException(404, "Événement d'audit introuvable.")
        return audit_response(item)

    # ========================================================
    # ARCHIVES
    # ========================================================

    @staticmethod
    async def require_archive(db, archive_id):
        item = await GovernanceRepository.get_archive(db, archive_id)
        if item is None:
            raise HTTPException(404, "Archive introuvable.")
        return item

    @staticmethod
    def archive_response(item):
        return ArchiveResponse(
            id=item.id,
            ressource_type=item.ressource_type,
            ressource_id=item.ressource_id,
            categorie_donnees=item.categorie_donnees,
            date_archivage=item.date_archivage,
            motif=item.motif,
            auteur_id=item.auteur_id,
            duree_conservation=item.duree_conservation,
            date_suppression_prevue=item.date_suppression_prevue,
            emplacement=item.emplacement,
            statut=item.statut,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    async def list_archives(db, **filters):
        rows, total = await GovernanceRepository.list_archives(db, **filters)
        return {
            "total": total,
            "limit": filters["limit"],
            "offset": filters["offset"],
            "items": [GovernanceService.archive_response(x) for x in rows],
        }

    @staticmethod
    async def create_archive(db, *, payload, actor, request):
        resource_type = payload.ressource_type.strip().upper()
        if await GovernanceRepository.active_archive_for_resource(
            db,
            ressource_type=resource_type,
            ressource_id=payload.ressource_id,
        ):
            raise HTTPException(409, "Cette ressource possède déjà une archive active.")

        archived_at = datetime.now(timezone.utc)
        planned = payload.date_suppression_prevue
        # RM-47 : minimum 10 ans. En l'absence d'un ancrage métier plus précis,
        # le registre d'archive applique une conservation conservatrice de
        # dix ans à compter de l'archivage.
        min_planned = plus_years(archived_at.date(), 10)
        if planned and planned < min_planned:
            raise HTTPException(
                422,
                "La date de suppression prévue est inférieure au minimum de 10 ans.",
            )

        item = Archive(
            ressource_type=resource_type,
            ressource_id=payload.ressource_id,
            categorie_donnees=payload.categorie_donnees.strip().upper(),
            date_archivage=archived_at,
            motif=payload.motif.strip(),
            auteur_id=actor.user.id,
            duree_conservation=(
                txt(payload.duree_conservation)
                or "10 ANS MINIMUM"
            ),
            date_suppression_prevue=planned or min_planned,
            emplacement=txt(payload.emplacement) or "ARCHIVE_LOGIQUE_BNEC",
            statut="ARCHIVE",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="ARCHIVE_CREATE",
            categorie="GOUVERNANCE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="archive",
            ressource_id=item.id,
            adresse_ip=ip(request),
            valeurs_apres={
                "ressource_type": item.ressource_type,
                "ressource_id": str(item.ressource_id),
                "date_suppression_prevue": item.date_suppression_prevue.isoformat(),
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.archive_response(item)

    # ========================================================
    # SAUVEGARDES
    # ========================================================

    @staticmethod
    async def require_backup(db, backup_id):
        item = await GovernanceRepository.get_backup(db, backup_id)
        if item is None:
            raise HTTPException(404, "Enregistrement de sauvegarde introuvable.")
        return item

    @staticmethod
    def backup_response(item):
        return BackupResponse(
            id=item.id,
            type_enregistrement=item.type_enregistrement,
            parent_id=item.parent_id,
            frequence=item.frequence,
            retention=item.retention,
            perimetre=item.perimetre,
            emplacement_stockage=item.emplacement_stockage,
            date_debut=item.date_debut,
            date_fin=item.date_fin,
            taille_octets=item.taille_octets,
            integrite_validee=item.integrite_validee,
            resultat=item.resultat,
            preuve_document_id=item.preuve_document_id,
            message_erreur=item.message_erreur,
            statut=item.statut,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    async def list_backups(db, **filters):
        rows, total = await GovernanceRepository.list_backups(db, **filters)
        return {
            "total": total,
            "limit": filters["limit"],
            "offset": filters["offset"],
            "items": [GovernanceService.backup_response(x) for x in rows],
        }

    @staticmethod
    async def create_backup_policy(db, *, payload, actor, request):
        item = Sauvegarde(
            type_enregistrement="POLITIQUE",
            parent_id=None,
            frequence=payload.frequence.strip().upper(),
            retention=payload.retention.strip(),
            perimetre=payload.perimetre.strip(),
            emplacement_stockage=payload.emplacement_stockage.strip(),
            date_debut=None,
            date_fin=None,
            taille_octets=None,
            integrite_validee=None,
            resultat=None,
            preuve_document_id=None,
            message_erreur=None,
            statut="ACTIVE",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="BACKUP_POLICY_CREATE",
            categorie="CONTINUITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="sauvegarde",
            ressource_id=item.id,
            adresse_ip=ip(request),
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.backup_response(item)

    @staticmethod
    async def update_backup_policy(db, *, backup_id, payload, actor, request):
        item = await GovernanceService.require_backup(db, backup_id)
        if item.type_enregistrement != "POLITIQUE":
            raise HTTPException(409, "Cet enregistrement n'est pas une politique.")

        for key, value in payload.model_dump(exclude_unset=True).items():
            if key == "frequence" and value:
                value = value.strip().upper()
            else:
                value = txt(value)
            setattr(item, key, value)

        await write_audit_event(
            db,
            action="BACKUP_POLICY_UPDATE",
            categorie="CONTINUITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="sauvegarde",
            ressource_id=item.id,
            adresse_ip=ip(request),
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.backup_response(item)

    @staticmethod
    async def create_backup_run(db, *, policy_id, payload, actor, request):
        policy = await GovernanceService.require_backup(db, policy_id)
        if policy.type_enregistrement != "POLITIQUE":
            raise HTTPException(409, "Parent non politique.")
        if policy.statut != "ACTIVE":
            raise HTTPException(409, "Politique inactive.")

        item = Sauvegarde(
            type_enregistrement="EXECUTION",
            parent_id=policy.id,
            frequence=policy.frequence,
            retention=policy.retention,
            perimetre=policy.perimetre,
            emplacement_stockage=policy.emplacement_stockage,
            date_debut=payload.date_debut or date.today(),
            date_fin=None,
            taille_octets=None,
            integrite_validee=None,
            resultat=None,
            preuve_document_id=None,
            message_erreur=None,
            statut="EN_COURS",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="BACKUP_RUN_START",
            categorie="CONTINUITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="sauvegarde",
            ressource_id=item.id,
            adresse_ip=ip(request),
            contexte={"policy_id": str(policy.id)},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.backup_response(item)

    @staticmethod
    async def complete_backup_run(db, *, backup_id, payload, actor, request):
        item = await GovernanceService.require_backup(db, backup_id)
        if item.type_enregistrement not in {"EXECUTION", "TEST_RESTAURATION"}:
            raise HTTPException(409, "Enregistrement non finalisable.")
        if item.statut != "EN_COURS":
            raise HTTPException(409, "Exécution non en cours.")

        if payload.preuve_document_id:
            if not await GovernanceRepository.get_active_document(
                db,
                payload.preuve_document_id,
            ):
                raise HTTPException(404, "Preuve documentaire introuvable.")

        item.date_fin = payload.date_fin or date.today()
        item.taille_octets = payload.taille_octets
        item.integrite_validee = payload.integrite_validee
        item.resultat = payload.resultat.strip()
        item.preuve_document_id = payload.preuve_document_id
        item.message_erreur = None
        item.statut = (
            "TERMINE"
            if payload.integrite_validee
            else "ECHEC_INTEGRITE"
        )

        await write_audit_event(
            db,
            action=(
                "BACKUP_RESTORE_TEST_COMPLETE"
                if item.type_enregistrement == "TEST_RESTAURATION"
                else "BACKUP_RUN_COMPLETE"
            ),
            categorie="CONTINUITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="sauvegarde",
            ressource_id=item.id,
            adresse_ip=ip(request),
            valeurs_apres={
                "integrite_validee": item.integrite_validee,
                "taille_octets": item.taille_octets,
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.backup_response(item)

    @staticmethod
    async def fail_backup_run(db, *, backup_id, payload, actor, request):
        item = await GovernanceService.require_backup(db, backup_id)
        if item.type_enregistrement not in {"EXECUTION", "TEST_RESTAURATION"}:
            raise HTTPException(409, "Enregistrement non exécutable.")
        item.date_fin = payload.date_fin or date.today()
        item.message_erreur = payload.message_erreur.strip()
        item.resultat = txt(payload.resultat)
        item.integrite_validee = False
        item.statut = "ECHEC"

        await write_audit_event(
            db,
            action="BACKUP_RUN_FAIL",
            categorie="CONTINUITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="sauvegarde",
            ressource_id=item.id,
            adresse_ip=ip(request),
            contexte={"message_erreur": item.message_erreur},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.backup_response(item)

    @staticmethod
    async def create_restore_test(db, *, backup_id, payload, actor, request):
        source = await GovernanceService.require_backup(db, backup_id)
        if source.type_enregistrement != "EXECUTION":
            raise HTTPException(409, "Le test doit partir d'une exécution de sauvegarde.")
        if source.statut != "TERMINE":
            raise HTTPException(409, "La sauvegarde source n'est pas valide.")

        item = Sauvegarde(
            type_enregistrement="TEST_RESTAURATION",
            parent_id=source.id,
            frequence=None,
            retention=source.retention,
            perimetre=txt(payload.perimetre) or source.perimetre,
            emplacement_stockage=source.emplacement_stockage,
            date_debut=date.today(),
            date_fin=None,
            taille_octets=None,
            integrite_validee=None,
            resultat=None,
            preuve_document_id=None,
            message_erreur=None,
            statut="EN_COURS",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="BACKUP_RESTORE_TEST_START",
            categorie="CONTINUITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="sauvegarde",
            ressource_id=item.id,
            adresse_ip=ip(request),
            contexte={"source_backup_id": str(source.id)},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.backup_response(item)

    # ========================================================
    # INCIDENTS
    # ========================================================

    @staticmethod
    async def require_incident(db, incident_id):
        item = await GovernanceRepository.get_incident(db, incident_id)
        if item is None:
            raise HTTPException(404, "Incident introuvable.")
        return item

    @staticmethod
    def incident_response(item):
        return IncidentResponse(
            id=item.id,
            code=item.code,
            categorie=item.categorie,
            gravite=item.gravite,
            titre=item.titre,
            description=item.description,
            date_declaration=item.date_declaration,
            declare_par_id=item.declare_par_id,
            responsable_id=item.responsable_id,
            ressource_type=item.ressource_type,
            ressource_id=item.ressource_id,
            preuves=item.preuves,
            resolution=item.resolution,
            date_resolution=item.date_resolution,
            date_cloture=item.date_cloture,
            statut=item.statut,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    async def generate_incident_code(db):
        for _ in range(10):
            code = (
                f"INC-{date.today().strftime('%Y%m%d')}-"
                f"{uuid4().hex[:8].upper()}"
            )
            if not await GovernanceRepository.incident_code_exists(db, code):
                return code
        raise HTTPException(500, "Impossible de générer un code incident unique.")

    @staticmethod
    async def list_incidents(db, **filters):
        rows, total = await GovernanceRepository.list_incidents(db, **filters)
        return {
            "total": total,
            "limit": filters["limit"],
            "offset": filters["offset"],
            "items": [GovernanceService.incident_response(x) for x in rows],
        }

    @staticmethod
    async def create_incident(db, *, payload, actor, request):
        if payload.responsable_id:
            await GovernanceService.require_active_user(
                db,
                payload.responsable_id,
            )

        item = Incident(
            code=await GovernanceService.generate_incident_code(db),
            categorie=payload.categorie.strip().upper(),
            gravite=payload.gravite.strip().upper(),
            titre=payload.titre.strip(),
            description=payload.description.strip(),
            date_declaration=date.today(),
            declare_par_id=actor.user.id,
            responsable_id=payload.responsable_id,
            ressource_type=(
                payload.ressource_type.strip().upper()
                if payload.ressource_type else None
            ),
            ressource_id=payload.ressource_id,
            preuves=payload.preuves,
            resolution=None,
            date_resolution=None,
            date_cloture=None,
            statut="OUVERT",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="INCIDENT_CREATE",
            categorie="CONTINUITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="incident",
            ressource_id=item.id,
            adresse_ip=ip(request),
            valeurs_apres={
                "code": item.code,
                "categorie": item.categorie,
                "gravite": item.gravite,
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.incident_response(item)

    @staticmethod
    async def update_incident(db, *, incident_id, payload, actor, request):
        item = await GovernanceService.require_incident(db, incident_id)
        if item.date_cloture:
            raise HTTPException(409, "Incident clôturé.")

        changes = payload.model_dump(exclude_unset=True)
        if changes.get("responsable_id"):
            await GovernanceService.require_active_user(
                db,
                changes["responsable_id"],
            )
        for key, value in changes.items():
            if key in {"categorie", "gravite"} and value:
                value = value.strip().upper()
            else:
                value = txt(value)
            setattr(item, key, value)

        await write_audit_event(
            db,
            action="INCIDENT_UPDATE",
            categorie="CONTINUITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="incident",
            ressource_id=item.id,
            adresse_ip=ip(request),
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.incident_response(item)

    @staticmethod
    async def assign_incident(db, *, incident_id, payload, actor, request):
        item = await GovernanceService.require_incident(db, incident_id)
        if item.date_cloture:
            raise HTTPException(409, "Incident clôturé.")
        await GovernanceService.require_active_user(
            db,
            payload.responsable_id,
        )
        item.responsable_id = payload.responsable_id
        item.statut = "EN_COURS"

        await write_audit_event(
            db,
            action="INCIDENT_ASSIGN",
            categorie="CONTINUITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="incident",
            ressource_id=item.id,
            adresse_ip=ip(request),
            valeurs_apres={
                "responsable_id": str(item.responsable_id),
                "statut": item.statut,
            },
            contexte={"commentaire": txt(payload.commentaire)},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.incident_response(item)

    @staticmethod
    async def resolve_incident(db, *, incident_id, payload, actor, request):
        item = await GovernanceService.require_incident(db, incident_id)
        if item.date_cloture:
            raise HTTPException(409, "Incident clôturé.")
        item.resolution = payload.resolution.strip()
        item.date_resolution = date.today()
        item.statut = "RESOLU"

        await write_audit_event(
            db,
            action="INCIDENT_RESOLVE",
            categorie="CONTINUITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="incident",
            ressource_id=item.id,
            adresse_ip=ip(request),
            valeurs_apres={
                "date_resolution": item.date_resolution.isoformat(),
                "statut": item.statut,
            },
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.incident_response(item)

    @staticmethod
    async def close_incident(db, *, incident_id, payload, actor, request):
        item = await GovernanceService.require_incident(db, incident_id)
        if item.date_cloture:
            return GovernanceService.incident_response(item)
        if item.date_resolution is None:
            raise HTTPException(409, "L'incident doit être résolu avant clôture.")
        item.date_cloture = date.today()
        item.statut = "CLOTURE"

        await write_audit_event(
            db,
            action="INCIDENT_CLOSE",
            categorie="CONTINUITE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="incident",
            ressource_id=item.id,
            adresse_ip=ip(request),
            contexte={"commentaire": txt(payload.commentaire)},
        )
        await db.commit()
        await db.refresh(item)
        return GovernanceService.incident_response(item)

    # ========================================================
    # DASHBOARD
    # ========================================================

    @staticmethod
    async def dashboard(db):
        (
            draft_rules,
            open_plans,
            open_incidents,
            pending_publications,
            pending_reports,
            failed_backups,
        ) = await GovernanceRepository.dashboard_counts(db)

        return GovernanceDashboardResponse(
            draft_rules=draft_rules,
            open_action_plans=open_plans,
            open_incidents=open_incidents,
            pending_publications=pending_publications,
            pending_reports=pending_reports,
            failed_backups=failed_backups,
        )
