"""
Service métier — Validation hiérarchisée + Intégration BNEC.

RÈGLES GARANTIES
----------------
- le FUCCS doit être finalisé avant validation ;
- N1 précède N2 ;
- N1 et N2 ne peuvent pas être prononcés par la même personne ;
- une réserve doit être explicitée ;
- un ajournement/rejet exige une justification ;
- une correction ne détruit jamais la décision d'origine ;
- seule une validation N2 favorable ouvre l'intégration BNEC ;
- précontrôle, codification, exécution et postcontrôle sont automatiques ;
- toute erreur provoque un rollback complet de l'intégration ;
- les codes officiels proviennent des modèles publiés dans Règles & codification ;
- aucun UUID, code ou résultat technique n'est saisi par l'utilisateur.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.certification import Certification
from app.models.certification_declaree import CertificationDeclaree
from app.models.correction import Correction
from app.models.element_integration import ElementIntegration
from app.models.evenement_certification import EvenementCertification
from app.models.integration_bnec import IntegrationBnec
from app.models.norme import Norme
from app.models.offre_declaree import OffreDeclaree
from app.models.offre_entreprise import OffreEntreprise
from app.models.organisme import Organisme
from app.models.validation import Validation
from app.repositories.validation_bnec_repository import ValidationBnecRepository
from app.rules.integration_deduplication import (
    certification_declaration_key,
    group_identical,
    offer_declaration_key,
)
from app.rules.norme_matching import (
    ParsedNormeLabel,
    parse_norme_label,
    score_norme_candidate,
)
from app.schemas.validation_bnec import (
    CorrectionCreateRequest,
    CorrectionResponse,
    CorrectionResubmitRequest,
    CorrectionUpdateRequest,
    IntegrationCheckRequest,
    IntegrationElementCreateRequest,
    IntegrationElementResponse,
    IntegrationElementResultRequest,
    IntegrationElementUpdateRequest,
    IntegrationListResponse,
    IntegrationOpenRequest,
    IntegrationPlanItem,
    IntegrationPlanResponse,
    IntegrationQueueItem,
    IntegrationResponse,
    IntegrationStartRequest,
    ValidationDecisionRequest,
    ValidationListResponse,
    ValidationQueueItem,
    ValidationResponse,
)
from app.services.auth_service import AuthContext
from app.services.codification_service import CodificationService
from app.services.veille_service import WatchService


FAVORABLE = {"VALIDE", "VALIDE_SOUS_RESERVE"}
CORRECTABLE = {"AJOURNE", "VALIDE_SOUS_RESERVE"}


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


@dataclass(slots=True)
class NormResolution:
    status: str
    parsed: ParsedNormeLabel
    norme: Norme | None = None
    candidates: list[Norme] | None = None
    created: bool = False


def validation_response(item: Validation) -> ValidationResponse:
    return ValidationResponse(
        id=item.id,
        fiche_collecte_id=item.fiche_collecte_id,
        controle_fuccs_id=item.controle_fuccs_id,
        niveau_validation=item.niveau_validation,
        validateur_id=item.validateur_id,
        decision=item.decision,
        date_validation=item.date_validation,
        reserves=item.reserves,
        justification=item.justification,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def correction_response(item: Correction) -> CorrectionResponse:
    return CorrectionResponse(
        id=item.id,
        validation_id=item.validation_id,
        motif=item.motif,
        instructions=item.instructions,
        date_demande=item.date_demande,
        date_echeance=item.date_echeance,
        date_resoumission=item.date_resoumission,
        reponse=item.reponse,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def element_response(item: ElementIntegration) -> IntegrationElementResponse:
    return IntegrationElementResponse(
        id=item.id,
        integration_bnec_id=item.integration_bnec_id,
        type_objet=item.type_objet,
        ressource_source_id=item.ressource_source_id,
        ressource_cible_id=item.ressource_cible_id,
        revision_source=item.revision_source,
        action=item.action,
        code_genere=item.code_genere,
        codification_regle_id=item.codification_regle_id,
        codification_logical_code=item.codification_logical_code,
        codification_version=item.codification_version,
        codification_format=item.codification_format,
        codification_scope_key=item.codification_scope_key,
        codification_sequence=item.codification_sequence,
        codification_segments=item.codification_segments,
        statut=item.statut,
        message_erreur=item.message_erreur,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


class ValidationBnecService:

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    async def get_validation(db: AsyncSession, validation_id: UUID) -> Validation:
        item = await ValidationBnecRepository.get_validation(db, validation_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation introuvable.",
            )
        return item

    @staticmethod
    async def list_validations(
        db: AsyncSession,
        *,
        fiche_id: UUID | None,
        niveau: str | None,
        decision: str | None,
        limit: int,
        offset: int,
    ) -> ValidationListResponse:
        items, total = await ValidationBnecRepository.list_validations(
            db,
            fiche_id=fiche_id,
            niveau=niveau,
            decision=decision,
            limit=limit,
            offset=offset,
        )
        return ValidationListResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=[validation_response(x) for x in items],
        )

    @staticmethod
    async def queue(db: AsyncSession) -> list[ValidationQueueItem]:
        rows = await ValidationBnecRepository.validation_queue_rows(db)
        output: list[ValidationQueueItem] = []
        seen_fiches: set[UUID] = set()

        for control, dossier in rows:
            fiche_id = dossier.fiche_collecte_id
            if fiche_id in seen_fiches:
                continue
            seen_fiches.add(fiche_id)

            n1 = await ValidationBnecRepository.latest_validation_for_level(
                db, fiche_id=fiche_id, level="NIVEAU_1"
            )
            n2 = await ValidationBnecRepository.latest_validation_for_level(
                db, fiche_id=fiche_id, level="NIVEAU_2"
            )

            integration_possible = bool(
                n1
                and n1.decision in FAVORABLE
                and n2
                and n2.decision in FAVORABLE
            )

            output.append(
                ValidationQueueItem(
                    fiche_collecte_id=fiche_id,
                    controle_fuccs_id=control.id,
                    controle_statut=control.statut,
                    score_brut=str(control.score_brut) if control.score_brut is not None else None,
                    score_maximal=str(control.score_maximal) if control.score_maximal is not None else None,
                    taux=control.taux,
                    niveau_1_decision=n1.decision if n1 else None,
                    niveau_1_validation_id=n1.id if n1 else None,
                    niveau_2_decision=n2.decision if n2 else None,
                    niveau_2_validation_id=n2.id if n2 else None,
                    integration_possible=integration_possible,
                )
            )

        return output

    @staticmethod
    def validate_decision_payload(payload: ValidationDecisionRequest) -> None:
        if payload.decision == "VALIDE_SOUS_RESERVE" and not clean_text(payload.reserves):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Les réserves sont obligatoires pour une validation sous réserve.",
            )

    @staticmethod
    async def create_level_decision(
        db: AsyncSession,
        *,
        fiche_id: UUID,
        level: str,
        payload: ValidationDecisionRequest,
        actor: AuthContext,
        request: Request,
    ) -> ValidationResponse:
        ValidationBnecService.validate_decision_payload(payload)

        # Évite deux décisions concurrentes du même niveau sur la même fiche.
        fiche = await ValidationBnecRepository.get_fiche_for_update(db, fiche_id)
        if fiche is None:
            raise HTTPException(404, "Fiche de collecte introuvable.")

        control = await ValidationBnecRepository.latest_finalized_control_for_fiche(
            db, fiche_id
        )
        if control is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Un contrôle FUCCS finalisé est requis avant validation.",
            )

        latest_same = await ValidationBnecRepository.latest_validation_for_level(
            db, fiche_id=fiche_id, level=level
        )

        if latest_same and latest_same.decision in FAVORABLE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Le {level} possède déjà une décision favorable active.",
            )

        if latest_same and latest_same.decision == "AJOURNE":
            if await ValidationBnecRepository.has_pending_correction(db, latest_same.id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Une correction demandée doit être resoumise avant nouvelle décision.",
                )

        n1 = await ValidationBnecRepository.latest_validation_for_level(
            db, fiche_id=fiche_id, level="NIVEAU_1"
        )

        if level == "NIVEAU_2":
            if n1 is None or n1.decision not in FAVORABLE:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Une revue NIVEAU_1 favorable est requise avant NIVEAU_2.",
                )
            if n1.validateur_id == actor.user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Le même utilisateur ne peut pas prononcer les deux niveaux de validation.",
                )

        item = Validation(
            fiche_collecte_id=fiche_id,
            controle_fuccs_id=control.id,
            niveau_validation=level,
            validateur_id=actor.user.id,
            decision=payload.decision,
            date_validation=date.today(),
            reserves=clean_text(payload.reserves),
            justification=payload.justification.strip(),
            statut="TERMINE",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action=(
                "VALIDATION_LEVEL1_DECISION"
                if level == "NIVEAU_1"
                else "VALIDATION_LEVEL2_DECISION"
            ),
            categorie="VALIDATION",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="validation",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "fiche_collecte_id": str(fiche_id),
                "controle_fuccs_id": str(control.id),
                "niveau_validation": level,
                "decision": item.decision,
                "reserves": item.reserves,
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return validation_response(item)

    # ========================================================
    # CORRECTIONS
    # ========================================================

    @staticmethod
    async def list_corrections(
        db: AsyncSession,
        validation_id: UUID,
    ) -> list[CorrectionResponse]:
        await ValidationBnecService.get_validation(db, validation_id)
        items = await ValidationBnecRepository.list_corrections(db, validation_id)
        return [correction_response(x) for x in items]

    @staticmethod
    async def create_correction(
        db: AsyncSession,
        *,
        validation_id: UUID,
        payload: CorrectionCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> CorrectionResponse:
        validation = await ValidationBnecService.get_validation(db, validation_id)

        if validation.decision not in CORRECTABLE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Une correction n'est permise que pour AJOURNE ou VALIDE_SOUS_RESERVE.",
            )

        item = Correction(
            validation_id=validation_id,
            motif=payload.motif.strip(),
            instructions=payload.instructions.strip(),
            date_demande=date.today(),
            date_echeance=payload.date_echeance,
            date_resoumission=None,
            reponse=None,
            statut="DEMANDEE",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="VALIDATION_CORRECTION_REQUEST",
            categorie="VALIDATION",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="correction",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "validation_id": str(validation_id),
                "date_echeance": (
                    item.date_echeance.isoformat() if item.date_echeance else None
                ),
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return correction_response(item)

    @staticmethod
    async def update_correction(
        db: AsyncSession,
        *,
        validation_id: UUID,
        correction_id: UUID,
        payload: CorrectionUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> CorrectionResponse:
        item = await ValidationBnecRepository.get_correction(
            db,
            validation_id=validation_id,
            correction_id=correction_id,
        )
        if item is None:
            raise HTTPException(404, "Correction introuvable.")

        if item.date_resoumission is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Une correction déjà resoumise n'est plus modifiable.",
            )

        changes = payload.model_dump(exclude_unset=True)
        before = {
            "motif": item.motif,
            "instructions": item.instructions,
            "date_echeance": (
                item.date_echeance.isoformat() if item.date_echeance else None
            ),
        }

        for field, value in changes.items():
            if isinstance(value, str):
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db,
            action="VALIDATION_CORRECTION_UPDATE",
            categorie="VALIDATION",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="correction",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
            valeurs_apres={
                "motif": item.motif,
                "instructions": item.instructions,
                "date_echeance": (
                    item.date_echeance.isoformat() if item.date_echeance else None
                ),
            },
        )

        await db.commit()
        await db.refresh(item)
        return correction_response(item)

    @staticmethod
    async def resubmit_correction(
        db: AsyncSession,
        *,
        validation_id: UUID,
        correction_id: UUID,
        payload: CorrectionResubmitRequest,
        actor: AuthContext,
        request: Request,
    ) -> CorrectionResponse:
        item = await ValidationBnecRepository.get_correction(
            db,
            validation_id=validation_id,
            correction_id=correction_id,
        )
        if item is None:
            raise HTTPException(404, "Correction introuvable.")

        if item.date_resoumission is not None:
            raise HTTPException(409, "Cette correction a déjà été resoumise.")

        item.date_resoumission = payload.date_resoumission or date.today()
        item.reponse = payload.reponse.strip()
        item.statut = "RESOUMISE"

        await write_audit_event(
            db,
            action="VALIDATION_CORRECTION_RESUBMIT",
            categorie="VALIDATION",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="correction",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "date_resoumission": item.date_resoumission.isoformat(),
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return correction_response(item)


    # ========================================================
    # INTÉGRATION BNEC — V4 AUTOMATIQUE + CODIFICATION
    # ========================================================

    @staticmethod
    async def get_integration(
        db: AsyncSession,
        integration_id: UUID,
    ) -> IntegrationBnec:
        item = await ValidationBnecRepository.get_integration(db, integration_id)
        if item is None:
            raise HTTPException(404, "Intégration BNEC introuvable.")
        return item

    @staticmethod
    async def integration_response(
        db: AsyncSession,
        item: IntegrationBnec,
    ) -> IntegrationResponse:
        total, success, error = await ValidationBnecRepository.integration_counts(
            db, item.id
        )
        return IntegrationResponse(
            id=item.id,
            validation_id=item.validation_id,
            administrateur_id=item.administrateur_id,
            date_debut=item.date_debut,
            date_fin=item.date_fin,
            statut=item.statut,
            precontrole=item.precontrole,
            postcontrole=item.postcontrole,
            sauvegarde_reference=item.sauvegarde_reference,
            resume=item.resume,
            elements_count=total,
            elements_success_count=success,
            elements_error_count=error,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    async def integration_queue(
        db: AsyncSession,
    ) -> list[IntegrationQueueItem]:
        validations = await ValidationBnecRepository.favorable_level2_validations(db)
        output: list[IntegrationQueueItem] = []
        for validation in validations:
            current = await ValidationBnecRepository.latest_integration_for_validation(
                db, validation.id
            )
            output.append(
                IntegrationQueueItem(
                    validation_id=validation.id,
                    fiche_collecte_id=validation.fiche_collecte_id,
                    controle_fuccs_id=validation.controle_fuccs_id,
                    decision=validation.decision,
                    date_validation=validation.date_validation,
                    existing_integration_id=current.id if current else None,
                    existing_integration_status=current.statut if current else None,
                    eligible=not bool(current and current.statut == "INTEGREE"),
                )
            )
        return output

    @staticmethod
    async def list_integrations(
        db: AsyncSession,
        *,
        statut: str | None,
        validation_id: UUID | None,
        administrateur_id: UUID | None,
        limit: int,
        offset: int,
    ) -> IntegrationListResponse:
        items, total = await ValidationBnecRepository.list_integrations(
            db,
            statut=statut,
            validation_id=validation_id,
            administrateur_id=administrateur_id,
            limit=limit,
            offset=offset,
        )
        return IntegrationListResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=[
                await ValidationBnecService.integration_response(db, item)
                for item in items
            ],
        )

    @staticmethod
    async def _source_context(db: AsyncSession, integration_id: UUID):
        row = await ValidationBnecRepository.integration_source_context(
            db, integration_id
        )
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La source validée de cette intégration est introuvable.",
            )
        return row

    @staticmethod
    def _enterprise_needs_codification(entreprise) -> bool:
        """Distingue un identifiant provisoire d'un code BNEC officiel.

        Une simple valeur courte comme ``TG`` ne suffit pas à prouver qu'une
        entreprise a déjà été codifiée. Les dossiers précréés pendant la
        collecte, sans statut officiel ou portant un identifiant temporaire,
        doivent recevoir le code issu du modèle ENTREPRISE publié.
        """

        if entreprise is None:
            return True
        identifier = (entreprise.identifiant_national or "").strip().upper()
        source = (entreprise.source_donnee or "").strip().upper()
        statut = (entreprise.statut or "").strip().upper()
        compact_identifier = "".join(
            character for character in identifier if character.isalnum()
        )

        if not identifier or identifier.startswith("TMP-"):
            return True
        if source in {
            "COLLECTE_TERRAIN",
            "COLLECTE",
            "SAISIE_RAPIDE",
            "PRECREATION_COLLECTE",
        }:
            return True
        if statut in {
            "",
            "INCOMPLET_COLLECTE",
            "BROUILLON",
            "A_COMPLETER",
            "EN_SAISIE",
        }:
            return True
        if len(compact_identifier) <= 3:
            return True
        return False

    @staticmethod
    async def _region_for_enterprise(db: AsyncSession, entreprise):
        zone = await ValidationBnecRepository.get_zone(
            db, entreprise.zone_siege_id if entreprise else None
        )
        current = zone
        region = None
        for _ in range(8):
            if current is None:
                break
            if (current.type_zone or "").upper() == "REGION":
                region = current
                break
            current = await ValidationBnecRepository.get_zone(db, current.parent_id)
        return zone, region or zone

    @staticmethod
    async def _enterprise_code_context(db: AsyncSession, entreprise) -> dict[str, str]:
        zone, region = await ValidationBnecService._region_for_enterprise(
            db, entreprise
        )
        return {
            "REGION": (
                (region.code or region.nom) if region else ""
            ),
            "ZONE": ((zone.code or zone.nom) if zone else ""),
            "ENTREPRISE": (
                entreprise.raison_sociale
                or entreprise.nom_commercial
                or "ENTREPRISE"
            ),
            "ENTREPRISE_ID": str(entreprise.id),
            "SECTEUR": entreprise.activite_principale or "",
        }

    @staticmethod
    async def _certification_code_context(
        db: AsyncSession,
        *,
        entreprise,
        source: CertificationDeclaree,
        organisme: Organisme,
        norme: Norme,
    ) -> dict[str, str]:
        context = await ValidationBnecService._enterprise_code_context(db, entreprise)
        context.update(
            {
                "CODE_ENTREPRISE": entreprise.identifiant_national,
                "ORGANISME": organisme.sigle or organisme.nom_officiel or "OC",
                "NORME": norme.code or norme.nom or source.norme_declaree or "NORME",
            }
        )
        return context

    @staticmethod
    async def _codification_preview(
        db: AsyncSession,
        *,
        object_type: str,
        context: dict[str, str],
        excluded_codes: set[str] | None = None,
    ):
        try:
            return await CodificationService.preview(
                db,
                object_type=object_type,
                context=context,
                excluded_codes=excluded_codes,
            ), None
        except ValueError as exc:
            return None, str(exc)

    @staticmethod
    def _rank_norm_candidates(
        parsed: ParsedNormeLabel,
        norms: list[Norme],
    ) -> list[tuple[int, Norme]]:
        ranked: list[tuple[int, Norme]] = []
        for norme in norms:
            result = score_norme_candidate(
                parsed,
                candidate_code=norme.code,
                candidate_name=norme.nom,
                candidate_version=norme.version,
                candidate_status=norme.statut,
            )
            if result.score >= 85:
                ranked.append((result.score, norme))
        ranked.sort(
            key=lambda item: (
                item[0],
                item[1].updated_at or datetime.min.replace(tzinfo=timezone.utc),
            ),
            reverse=True,
        )
        return ranked

    @staticmethod
    def _norm_candidate_label(norme: Norme) -> str:
        label = norme.code or norme.nom or "Norme sans libellé"
        return f"{label} — version {norme.version}" if norme.version else label

    @staticmethod
    def _norm_resolution_error(resolution: NormResolution) -> str | None:
        if resolution.status == "INVALID":
            return "norme déclarée inexploitable"
        if resolution.status == "AMBIGUOUS":
            labels = [
                ValidationBnecService._norm_candidate_label(item)
                for item in (resolution.candidates or [])[:3]
            ]
            suffix = f" ({'; '.join(labels)})" if labels else ""
            return "norme ambiguë dans le référentiel" + suffix
        return None

    @staticmethod
    async def _resolve_norm_reference(
        db: AsyncSession,
        label: str | None,
        *,
        create_missing: bool = False,
    ) -> NormResolution:
        """Rapproche ou prépare la création d'une norme validée N2.

        Une correspondance unique est réutilisée. Une absence réelle produit
        une norme officielle pendant la transaction d'intégration. Plusieurs
        versions de score identique restent bloquantes afin d'éviter un choix
        silencieux et irréversible.
        """

        parsed = parse_norme_label(label)
        if not parsed.creatable:
            return NormResolution(status="INVALID", parsed=parsed)

        norms = await ValidationBnecRepository.list_norms_for_matching(db)
        ranked = ValidationBnecService._rank_norm_candidates(parsed, norms)
        if ranked:
            best_score = ranked[0][0]
            best = [item for score, item in ranked if score == best_score]
            if len(best) == 1:
                return NormResolution(
                    status="MATCHED",
                    parsed=parsed,
                    norme=best[0],
                    candidates=best,
                )
            return NormResolution(
                status="AMBIGUOUS",
                parsed=parsed,
                candidates=best,
            )

        preview = Norme(
            code=parsed.code,
            nom=parsed.code,
            version=parsed.version,
            statut="ACTIF",
        )
        if not create_missing:
            return NormResolution(
                status="TO_CREATE",
                parsed=parsed,
                norme=preview,
            )

        # Le verrou évite que deux intégrations concurrentes créent la même
        # norme absente. Après acquisition, le référentiel est relu.
        await ValidationBnecRepository.lock_codification_scope(
            db,
            "HAUQE:BNEC:NORME:"
            f"{parsed.code_key}:{parsed.version or 'SANS_VERSION'}",
        )
        norms = await ValidationBnecRepository.list_norms_for_matching(db)
        ranked = ValidationBnecService._rank_norm_candidates(parsed, norms)
        if ranked:
            best_score = ranked[0][0]
            best = [item for score, item in ranked if score == best_score]
            if len(best) == 1:
                return NormResolution(
                    status="MATCHED",
                    parsed=parsed,
                    norme=best[0],
                    candidates=best,
                )
            return NormResolution(
                status="AMBIGUOUS",
                parsed=parsed,
                candidates=best,
            )

        db.add(preview)
        await db.flush()
        return NormResolution(
            status="CREATED",
            parsed=parsed,
            norme=preview,
            created=True,
        )

    @staticmethod
    async def _seed_integration_elements(
        db: AsyncSession,
        *,
        integration: IntegrationBnec,
        rebuild: bool = False,
    ) -> list[ElementIntegration]:
        """Construit le plan sans exposer d'identifiant technique à saisir."""

        _, validation, fiche, entreprise = await ValidationBnecService._source_context(
            db, integration.id
        )
        existing = await ValidationBnecRepository.list_elements(db, integration.id)
        if rebuild:
            if any(item.statut == "INTEGRE" for item in existing):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Une intégration terminée ne peut pas être reconstruite.",
                )
            for item in existing:
                await db.delete(item)
            await db.flush()
        elif existing:
            return existing

        revision = str(fiche.numero_revision or 1)
        elements: list[ElementIntegration] = []

        if entreprise is None:
            elements.append(
                ElementIntegration(
                    integration_bnec_id=integration.id,
                    type_objet="ENTREPRISE",
                    revision_source=revision,
                    action="CONFIRMER",
                    statut="BLOQUE",
                    message_erreur=(
                        "La fiche validée n'est reliée à aucune entreprise."
                    ),
                )
            )
        else:
            blocker = None
            if ValidationBnecService._enterprise_needs_codification(entreprise):
                context = await ValidationBnecService._enterprise_code_context(
                    db, entreprise
                )
                _, blocker = await ValidationBnecService._codification_preview(
                    db,
                    object_type="ENTREPRISE",
                    context=context,
                )
            elements.append(
                ElementIntegration(
                    integration_bnec_id=integration.id,
                    type_objet="ENTREPRISE",
                    ressource_source_id=entreprise.id,
                    ressource_cible_id=entreprise.id,
                    revision_source=revision,
                    action="CONFIRMER",
                    code_genere=(
                        None
                        if ValidationBnecService._enterprise_needs_codification(entreprise)
                        else entreprise.identifiant_national
                    ),
                    statut="BLOQUE" if blocker else "PRET",
                    message_erreur=blocker,
                )
            )

        declared_offers = await ValidationBnecRepository.list_declared_offers(
            db, fiche.id
        )
        for declared, _duplicates in group_identical(
            declared_offers,
            offer_declaration_key,
        ):
            blocker = None
            target = None
            if not clean_text(declared.nom):
                blocker = "Le nom de l'offre déclarée est obligatoire."
            elif entreprise is not None:
                target = await ValidationBnecRepository.find_official_offer(
                    db,
                    enterprise_id=entreprise.id,
                    name=declared.nom,
                    offer_type=declared.type_offre,
                    category=declared.categorie,
                )
            elements.append(
                ElementIntegration(
                    integration_bnec_id=integration.id,
                    type_objet="OFFRE",
                    ressource_source_id=declared.id,
                    ressource_cible_id=target.id if target else None,
                    revision_source=revision,
                    action="RAPPROCHER" if target else "CREER",
                    statut="BLOQUE" if blocker else "PRET",
                    message_erreur=blocker,
                )
            )

        declared_certifications = (
            await ValidationBnecRepository.list_declared_certifications(
                db, fiche.id
            )
        )
        for declared, _duplicates in group_identical(
            declared_certifications,
            certification_declaration_key,
        ):
            blockers: list[str] = []
            if entreprise is None:
                blockers.append("entreprise source absente")
            if not clean_text(declared.organisme_declare):
                blockers.append("organisme certificateur non renseigné")
            if not clean_text(declared.norme_declaree):
                blockers.append("norme ou référentiel non renseigné")
            if declared.date_obtention is None:
                blockers.append("date d'obtention non renseignée")
            if (
                declared.date_obtention
                and declared.date_expiration
                and declared.date_expiration <= declared.date_obtention
            ):
                blockers.append("date d'expiration incohérente")

            organisme = None
            norme = None
            if clean_text(declared.organisme_declare):
                organisme = await ValidationBnecRepository.find_organism_by_label(
                    db, declared.organisme_declare
                )
                if organisme is None:
                    blockers.append(
                        "organisme certificateur non rapproché dans le registre"
                    )
            if clean_text(declared.norme_declaree):
                norm_resolution = (
                    await ValidationBnecService._resolve_norm_reference(
                        db,
                        declared.norme_declaree,
                    )
                )
                norme = norm_resolution.norme
                norm_error = ValidationBnecService._norm_resolution_error(
                    norm_resolution
                )
                if norm_error:
                    blockers.append(norm_error)

            target = None
            if declared.certification_officielle_id:
                target = await ValidationBnecRepository.get_official_certification(
                    db, declared.certification_officielle_id
                )
            if target is None and entreprise is not None and clean_text(declared.numero):
                target = await ValidationBnecRepository.find_certification_by_number(
                    db,
                    enterprise_id=entreprise.id,
                    number=declared.numero,
                )
            if (
                target is None
                and entreprise is not None
                and organisme is not None
                and norme is not None
                and getattr(norme, "id", None) is not None
            ):
                target = await ValidationBnecRepository.find_certification_candidate(
                    db,
                    enterprise_id=entreprise.id,
                    organisme_id=organisme.id,
                    norme_id=norme.id,
                    scope=declared.portee,
                )

            if (
                target is None
                and entreprise is not None
                and organisme is not None
                and norme is not None
                and not blockers
            ):
                company_code = entreprise.identifiant_national
                if ValidationBnecService._enterprise_needs_codification(entreprise):
                    company_preview, company_error = (
                        await ValidationBnecService._codification_preview(
                            db,
                            object_type="ENTREPRISE",
                            context=(
                                await ValidationBnecService._enterprise_code_context(
                                    db, entreprise
                                )
                            ),
                        )
                    )
                    if company_error:
                        blockers.append(company_error)
                    elif company_preview:
                        company_code = company_preview.code
                if not blockers:
                    context = await ValidationBnecService._certification_code_context(
                        db,
                        entreprise=entreprise,
                        source=declared,
                        organisme=organisme,
                        norme=norme,
                    )
                    context["CODE_ENTREPRISE"] = company_code
                    _, code_error = await ValidationBnecService._codification_preview(
                        db,
                        object_type="CERTIFICATION",
                        context=context,
                    )
                    if code_error:
                        blockers.append(code_error)

            elements.append(
                ElementIntegration(
                    integration_bnec_id=integration.id,
                    type_objet="CERTIFICATION",
                    ressource_source_id=declared.id,
                    ressource_cible_id=target.id if target else None,
                    revision_source=revision,
                    action="RAPPROCHER" if target else "CREER",
                    code_genere=target.identifiant_national if target else None,
                    statut="BLOQUE" if blockers else "PRET",
                    message_erreur=(
                        "Certification bloquée : " + ", ".join(blockers) + "."
                        if blockers
                        else None
                    ),
                )
            )

        db.add_all(elements)
        await db.flush()
        return elements

    @staticmethod
    async def open_integration(
        db: AsyncSession,
        *,
        validation_id: UUID,
        payload: IntegrationOpenRequest,
        actor: AuthContext,
        request: Request,
    ) -> IntegrationResponse:
        validation = await ValidationBnecService.get_validation(db, validation_id)
        if (
            validation.niveau_validation != "NIVEAU_2"
            or validation.decision not in FAVORABLE
            or validation.statut != "TERMINE"
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Seule une validation définitive NIVEAU_2 favorable "
                    "autorise l'intégration."
                ),
            )
        current = await ValidationBnecRepository.active_integration_for_validation(
            db, validation_id
        )
        if current:
            return await ValidationBnecService.integration_response(db, current)
        previous = await ValidationBnecRepository.latest_integration_for_validation(
            db, validation_id
        )
        if previous and previous.statut == "INTEGREE":
            raise HTTPException(409, "Cette validation a déjà été intégrée.")

        item = IntegrationBnec(
            validation_id=validation_id,
            administrateur_id=actor.user.id,
            statut="EN_ATTENTE",
            resume=clean_text(payload.resume),
        )
        db.add(item)
        await db.flush()
        await ValidationBnecService._seed_integration_elements(
            db, integration=item
        )
        await write_audit_event(
            db,
            action="BNEC_INTEGRATION_OPEN",
            categorie="INTEGRATION_BNEC",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="integration_bnec",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "validation_id": str(validation_id),
                "plan_automatique": True,
                "codification_configurable": True,
            },
        )
        await db.commit()
        await db.refresh(item)
        return await ValidationBnecService.integration_response(db, item)

    @staticmethod
    async def prepare_plan(
        db: AsyncSession,
        *,
        integration_id: UUID,
        actor: AuthContext,
        request: Request,
    ) -> IntegrationPlanResponse:
        integration = await ValidationBnecService.get_integration(db, integration_id)
        if integration.statut == "INTEGREE":
            raise HTTPException(409, "Cette intégration est déjà terminée.")
        await ValidationBnecService._seed_integration_elements(
            db,
            integration=integration,
            rebuild=True,
        )
        integration.precontrole = None
        integration.postcontrole = None
        integration.date_debut = None
        integration.date_fin = None
        integration.statut = "EN_ATTENTE"
        await write_audit_event(
            db,
            action="BNEC_INTEGRATION_ANALYSIS_REFRESH",
            categorie="INTEGRATION_BNEC",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="integration_bnec",
            ressource_id=integration.id,
            adresse_ip=client_ip(request),
        )
        await db.commit()
        return await ValidationBnecService.integration_plan(db, integration.id)

    @staticmethod
    async def _plan_item(
        db: AsyncSession,
        element: ElementIntegration,
        *,
        entreprise,
        reserved_preview_codes: set[str],
    ) -> IntegrationPlanItem:
        """Construit une carte métier depuis l'état actuel des référentiels.

        Les blocages sont recalculés à chaque lecture. Un ancien message stocké
        dans ``elements_integration`` ne peut donc plus contredire une norme
        désormais rapprochée ou marquée pour création automatique.
        """

        kind = (element.type_objet or "OBJET").upper()
        action = (element.action or "A_DEFINIR").upper()
        labels = {
            "ENTREPRISE": "Entreprise",
            "OFFRE": "Produit ou service",
            "CERTIFICATION": "Certification déclarée",
        }
        action_labels = {
            "CONFIRMER": "Confirmer dans la BNEC",
            "CREER": "Créer la ressource officielle",
            "RAPPROCHER": "Rapprocher de l'existant",
            "METTRE_A_JOUR": "Mettre à jour l'existant",
        }
        source_title = "Source introuvable"
        source_details: list[str] = []
        target_title = None
        target_details: list[str] = []
        code_propose = element.code_genere
        codification_required = False
        model = None
        model_info = None
        code_error = None
        current_blockers: list[str] = []

        if kind == "ENTREPRISE" and entreprise is not None:
            source_title = (
                entreprise.raison_sociale
                or entreprise.nom_commercial
                or "Entreprise"
            )
            needs_code = ValidationBnecService._enterprise_needs_codification(
                entreprise
            )
            source_details = [
                (
                    f"Identifiant provisoire : {entreprise.identifiant_national}"
                    if needs_code and entreprise.identifiant_national
                    else f"Code BNEC : {entreprise.identifiant_national}"
                    if entreprise.identifiant_national
                    else "Identifiant non renseigné"
                ),
                entreprise.rccm or "RCCM non renseigné",
                entreprise.statut or "Statut non renseigné",
            ]
            target_title = source_title
            target_details = ["Dossier précréé pendant la collecte"]
            codification_required = element.statut != "INTEGRE" and needs_code
            if codification_required:
                model, code_error = await ValidationBnecService._codification_preview(
                    db,
                    object_type="ENTREPRISE",
                    context=await ValidationBnecService._enterprise_code_context(
                        db, entreprise
                    ),
                    excluded_codes=reserved_preview_codes,
                )
                if model:
                    code_propose = model.code
                    reserved_preview_codes.add(model.code)
            elif element.statut != "INTEGRE":
                code_propose = entreprise.identifiant_national

        elif kind == "OFFRE" and element.ressource_source_id:
            source = await ValidationBnecRepository.get_declared_offer(
                db, element.ressource_source_id
            )
            if source:
                source_title = source.nom or "Offre sans nom"
                source_details = [
                    value
                    for value in [source.type_offre, source.categorie]
                    if value
                ]
                if not clean_text(source.nom):
                    current_blockers.append("nom de l'offre non renseigné")
                declarations = await ValidationBnecRepository.list_declared_offers(
                    db, source.fiche_collecte_id
                )
                duplicate_count = sum(
                    1
                    for item in declarations
                    if offer_declaration_key(item) == offer_declaration_key(source)
                )
                if duplicate_count > 1:
                    target_details.append(
                        f"{duplicate_count} déclarations identiques regroupées en une seule offre officielle"
                    )
            target_title = (
                "Offre existante rapprochée"
                if element.ressource_cible_id
                else "Nouvelle offre officielle"
            )

        elif kind == "CERTIFICATION" and element.ressource_source_id:
            source = await ValidationBnecRepository.get_declared_certification(
                db, element.ressource_source_id
            )
            if source:
                source_title = (
                    source.nom_certification
                    or source.norme_declaree
                    or "Certification"
                )
                source_details = [
                    value
                    for value in [
                        f"N° {source.numero}" if source.numero else None,
                        (
                            f"Organisme : {source.organisme_declare}"
                            if source.organisme_declare
                            else None
                        ),
                        (
                            f"Norme : {source.norme_declaree}"
                            if source.norme_declaree
                            else None
                        ),
                    ]
                    if value
                ]

                if entreprise is None:
                    current_blockers.append("entreprise source absente")
                if not clean_text(source.organisme_declare):
                    current_blockers.append("organisme certificateur non renseigné")
                if not clean_text(source.norme_declaree):
                    current_blockers.append("norme ou référentiel non renseigné")
                if source.date_obtention is None:
                    current_blockers.append("date d'obtention non renseignée")
                if (
                    source.date_obtention
                    and source.date_expiration
                    and source.date_expiration <= source.date_obtention
                ):
                    current_blockers.append("date d'expiration incohérente")

                declarations = (
                    await ValidationBnecRepository.list_declared_certifications(
                        db, source.fiche_collecte_id
                    )
                )
                duplicate_count = sum(
                    1
                    for item in declarations
                    if certification_declaration_key(item)
                    == certification_declaration_key(source)
                )
                if duplicate_count > 1:
                    target_details.append(
                        f"{duplicate_count} déclarations identiques regroupées en une seule certification officielle"
                    )

                organisme = (
                    await ValidationBnecRepository.find_organism_by_label(
                        db, source.organisme_declare
                    )
                    if clean_text(source.organisme_declare)
                    else None
                )
                if clean_text(source.organisme_declare) and organisme is None:
                    current_blockers.append(
                        "organisme certificateur non rapproché dans le registre"
                    )

                norm_resolution = (
                    await ValidationBnecService._resolve_norm_reference(
                        db,
                        source.norme_declaree,
                    )
                    if clean_text(source.norme_declaree)
                    else None
                )
                norme = norm_resolution.norme if norm_resolution else None
                if norm_resolution:
                    norm_error = ValidationBnecService._norm_resolution_error(
                        norm_resolution
                    )
                    if norm_error:
                        current_blockers.append(norm_error)
                    elif norm_resolution.status == "MATCHED" and norme:
                        target_details.append(
                            "Norme rapprochée : "
                            + ValidationBnecService._norm_candidate_label(norme)
                        )
                    elif norm_resolution.status == "TO_CREATE" and norme:
                        target_details.append(
                            "Norme à créer automatiquement : "
                            + ValidationBnecService._norm_candidate_label(norme)
                        )

                target = None
                if element.ressource_cible_id:
                    target = await ValidationBnecRepository.get_official_certification(
                        db, element.ressource_cible_id
                    )
                if target:
                    target_title = target.identifiant_national
                    code_propose = target.identifiant_national
                else:
                    target_title = "Nouvelle certification officielle"
                    codification_required = element.statut != "INTEGRE"

                if (
                    codification_required
                    and entreprise is not None
                    and organisme is not None
                    and norme is not None
                    and not current_blockers
                ):
                    company_code = entreprise.identifiant_national
                    if ValidationBnecService._enterprise_needs_codification(
                        entreprise
                    ):
                        company_preview, company_error = (
                            await ValidationBnecService._codification_preview(
                                db,
                                object_type="ENTREPRISE",
                                context=(
                                    await ValidationBnecService._enterprise_code_context(
                                        db, entreprise
                                    )
                                ),
                            )
                        )
                        if company_preview:
                            company_code = company_preview.code
                        elif company_error:
                            code_error = company_error
                    if code_error is None:
                        context = (
                            await ValidationBnecService._certification_code_context(
                                db,
                                entreprise=entreprise,
                                source=source,
                                organisme=organisme,
                                norme=norme,
                            )
                        )
                        context["CODE_ENTREPRISE"] = company_code
                        model, code_error = (
                            await ValidationBnecService._codification_preview(
                                db,
                                object_type="CERTIFICATION",
                                context=context,
                                excluded_codes=reserved_preview_codes,
                            )
                        )
                        if model:
                            code_propose = model.code
                            reserved_preview_codes.add(model.code)

        if codification_required and model is None:
            try:
                model_info = await CodificationService.describe_active_rule(
                    db,
                    kind,
                )
            except ValueError as exc:
                if code_error is None:
                    code_error = str(exc)

        if element.codification_regle_id:
            model_label = element.codification_logical_code
            model_version = element.codification_version
            model_format = element.codification_format
            model_scope = element.codification_scope_key
            model_approval = None
            model_logical_code = element.codification_logical_code
        else:
            described_model = model or model_info
            model_label = described_model.model_label if described_model else None
            model_version = described_model.version if described_model else None
            model_format = described_model.format_code if described_model else None
            model_scope = described_model.sequence_scope if described_model else None
            model_approval = (
                described_model.approval_reference if described_model else None
            )
            model_logical_code = (
                described_model.logical_code if described_model else None
            )

        # Une erreur d'exécution reste visible. Pour les plans PRET/BLOQUE, le
        # diagnostic frais remplace entièrement l'ancien message enregistré.
        if element.statut == "ECHEC":
            blocker = element.message_erreur or code_error
        elif element.statut == "INTEGRE":
            blocker = None
        else:
            if code_error:
                current_blockers.append(code_error)
            blocker = (
                "Certification bloquée : " + ", ".join(current_blockers) + "."
                if kind == "CERTIFICATION" and current_blockers
                else ", ".join(current_blockers) if current_blockers else None
            )

        return IntegrationPlanItem(
            element_id=element.id,
            type_objet=kind,
            type_libelle=labels.get(kind, kind.title()),
            source_titre=source_title,
            source_details=source_details,
            action=action,
            action_libelle=action_labels.get(action, action.replace("_", " ").title()),
            cible_titre=target_title,
            cible_details=target_details,
            statut=(
                "INTEGRE"
                if element.statut == "INTEGRE"
                else "ECHEC"
                if element.statut == "ECHEC"
                else "BLOQUE"
                if blocker
                else "PRET"
            ),
            blocage=blocker,
            ressource_source_id=element.ressource_source_id,
            ressource_cible_id=element.ressource_cible_id,
            revision_source=element.revision_source,
            code_genere=element.code_genere,
            code_propose=code_propose,
            codification_requise=codification_required,
            codification_modele=model_label,
            codification_logical_code=(
                element.codification_logical_code or model_logical_code
            ),
            codification_version=model_version,
            codification_format=model_format,
            codification_portee=model_scope,
            codification_reference_approbation=model_approval,
        )

    @staticmethod
    async def _deduplicated_plan_elements(
        db: AsyncSession,
        elements: list[ElementIntegration],
    ) -> list[ElementIntegration]:
        """Masque immédiatement les anciens doublons de plan.

        Après déploiement, une tentative déjà préparée peut encore contenir
        plusieurs éléments techniques issus des versions antérieures. La vue
        métier les regroupe dès le chargement, puis ``Actualiser l'analyse``
        reconstruit définitivement la liste persistée.
        """

        visible: list[ElementIntegration] = []
        seen: set[tuple[object, ...]] = set()
        for element in elements:
            kind = (element.type_objet or "").upper()
            key: tuple[object, ...]
            if kind == "OFFRE" and element.ressource_source_id:
                source = await ValidationBnecRepository.get_declared_offer(
                    db, element.ressource_source_id
                )
                key = (
                    kind,
                    offer_declaration_key(source) if source else element.id,
                )
            elif kind == "CERTIFICATION" and element.ressource_source_id:
                source = await ValidationBnecRepository.get_declared_certification(
                    db, element.ressource_source_id
                )
                key = (
                    kind,
                    certification_declaration_key(source)
                    if source
                    else element.id,
                )
            else:
                key = (kind, element.id)
            if key in seen:
                continue
            seen.add(key)
            visible.append(element)
        return visible

    @staticmethod
    async def integration_plan(
        db: AsyncSession,
        integration_id: UUID,
    ) -> IntegrationPlanResponse:
        integration, validation, fiche, entreprise = (
            await ValidationBnecService._source_context(db, integration_id)
        )
        elements = await ValidationBnecRepository.list_elements(db, integration_id)
        elements = await ValidationBnecService._deduplicated_plan_elements(
            db, elements
        )
        reserved_preview_codes: set[str] = set()
        items = []
        for element in elements:
            items.append(
                await ValidationBnecService._plan_item(
                    db,
                    element,
                    entreprise=entreprise,
                    reserved_preview_codes=reserved_preview_codes,
                )
            )
        blocked = sum(1 for item in items if item.statut == "BLOQUE")
        errors = sum(1 for item in items if item.statut == "ECHEC")
        integrated = sum(1 for item in items if item.statut == "INTEGRE")
        ready_count = sum(1 for item in items if item.statut == "PRET")
        required_models = sorted(
            {
                item.type_objet
                for item in items
                if item.codification_requise
            }
        )
        missing = []
        for object_type in required_models:
            if await CodificationService.active_rule(db, object_type) is None:
                missing.append(object_type)
        codification_ready = not missing and all(
            (not item.codification_requise) or bool(item.codification_modele)
            for item in items
        )
        return IntegrationPlanResponse(
            integration_id=integration.id,
            validation_id=validation.id,
            fiche_collecte_id=fiche.id,
            fiche_revision=fiche.numero_revision,
            entreprise_id=entreprise.id if entreprise else None,
            entreprise_nom=(
                entreprise.raison_sociale or entreprise.nom_commercial
                if entreprise
                else None
            ),
            entreprise_identifiant=(
                entreprise.identifiant_national if entreprise else None
            ),
            validation_decision=validation.decision,
            prepared=bool(items),
            ready=bool(items) and blocked == 0 and errors == 0 and not missing,
            total=len(items),
            ready_count=ready_count,
            integrated_count=integrated,
            error_count=errors,
            blocked_count=blocked,
            codification_ready=codification_ready,
            missing_codification_models=missing,
            items=items,
        )

    @staticmethod
    async def _automatic_precontrol(
        db: AsyncSession,
        *,
        integration: IntegrationBnec,
    ) -> IntegrationPlanResponse:
        _, validation, fiche, _ = await ValidationBnecService._source_context(
            db, integration.id
        )
        n1 = await ValidationBnecRepository.latest_validation_for_level(
            db,
            fiche_id=fiche.id,
            level="NIVEAU_1",
        )
        if n1 is None or n1.decision not in FAVORABLE:
            raise ValueError("La décision N1 favorable est introuvable.")
        if n1.validateur_id == validation.validateur_id:
            raise ValueError("Les validateurs N1 et N2 doivent être distincts.")
        plan = await ValidationBnecService.integration_plan(db, integration.id)
        if not plan.prepared:
            raise ValueError("Aucun élément métier n'a été détecté.")
        if not plan.ready:
            details = [
                item.blocage
                for item in plan.items
                if item.blocage
            ][:4]
            if plan.missing_codification_models:
                details.append(
                    "Modèles de codification manquants : "
                    + ", ".join(plan.missing_codification_models)
                )
            raise ValueError(" | ".join(details) or "Le dossier est bloqué.")
        integration.precontrole = "OK"
        integration.statut = "PRECONTROLE"
        return plan

    @staticmethod
    async def precontrol(
        db: AsyncSession,
        *,
        integration_id: UUID,
        payload: IntegrationCheckRequest,
        actor: AuthContext,
        request: Request,
    ) -> IntegrationResponse:
        # Compatibilité API : le résultat n'est plus saisi manuellement.
        integration = await ValidationBnecService.get_integration(db, integration_id)
        try:
            plan = await ValidationBnecService._automatic_precontrol(
                db,
                integration=integration,
            )
            integration.resume = (
                f"Précontrôle automatique réussi : {plan.total} ressource(s)."
            )
        except ValueError as exc:
            integration.precontrole = "ECHEC"
            integration.statut = "BLOQUE"
            integration.resume = str(exc)
            await db.commit()
            raise HTTPException(409, str(exc)) from exc
        await db.commit()
        await db.refresh(integration)
        return await ValidationBnecService.integration_response(db, integration)

    @staticmethod
    def _markets(value: str | None) -> list[str] | None:
        if not clean_text(value):
            return None
        return [
            part.strip()
            for part in value.replace(";", ",").split(",")
            if part.strip()
        ] or None

    @staticmethod
    def _certification_status(source: CertificationDeclaree) -> str:
        today = date.today()
        if source.copie_disponible is not True or source.date_expiration is None:
            return "A_VERIFIER"
        if source.date_expiration < today:
            return "EXPIREE"
        if (source.situation_declaree or "").upper() == "ABSENTE":
            return "A_VERIFIER"
        return "ACTIVE"

    @staticmethod
    async def _execute_enterprise(
        db: AsyncSession,
        *,
        element: ElementIntegration,
        fiche,
        entreprise,
    ) -> None:
        if entreprise is None:
            raise ValueError("Aucune entreprise n'est rattachée à la fiche.")
        if ValidationBnecService._enterprise_needs_codification(entreprise):
            assignment = await CodificationService.reserve(
                db,
                object_type="ENTREPRISE",
                context=await ValidationBnecService._enterprise_code_context(
                    db, entreprise
                ),
                element=element,
            )
            entreprise.identifiant_national = assignment.code
        else:
            element.code_genere = entreprise.identifiant_national
        entreprise.date_derniere_verification = date.today()
        entreprise.source_donnee = "COLLECTE_VALIDEE"
        if (entreprise.statut or "").upper() in {
            "",
            "INCOMPLET_COLLECTE",
            "BROUILLON",
            "A_COMPLETER",
            "EN_SAISIE",
        }:
            entreprise.statut = (
                "EN_ATTENTE_REGULARISATION" if not entreprise.rccm else "A_VERIFIER"
            )
        element.ressource_source_id = entreprise.id
        element.ressource_cible_id = entreprise.id
        element.action = "CONFIRMER"

    @staticmethod
    async def _execute_offer(
        db: AsyncSession,
        *,
        element: ElementIntegration,
        fiche,
        entreprise,
    ) -> None:
        if entreprise is None or element.ressource_source_id is None:
            raise ValueError("Entreprise ou offre déclarée absente.")
        source = await ValidationBnecRepository.get_declared_offer(
            db, element.ressource_source_id
        )
        if source is None or source.fiche_collecte_id != fiche.id:
            raise ValueError("Offre source incohérente.")
        if not clean_text(source.nom):
            raise ValueError("Le nom de l'offre est obligatoire.")
        target = None
        if element.ressource_cible_id:
            target = await ValidationBnecRepository.get_official_offer(
                db, element.ressource_cible_id
            )
        if target is None:
            target = await ValidationBnecRepository.find_official_offer(
                db,
                enterprise_id=entreprise.id,
                name=source.nom,
                offer_type=source.type_offre,
                category=source.categorie,
            )
        if target is None:
            target = OffreEntreprise(entreprise_id=entreprise.id)
            db.add(target)
            await db.flush()
            element.action = "CREER"
        else:
            if target.entreprise_id != entreprise.id:
                raise ValueError("L'offre cible appartient à une autre entreprise.")
            element.action = "RAPPROCHER"
        target.type_offre = clean_text(source.type_offre)
        target.nom = source.nom.strip()
        target.description = clean_text(source.description)
        target.categorie = clean_text(source.categorie)
        target.volume_annuel = source.volume
        target.unite = clean_text(source.unite)
        target.capacite_production = source.capacite
        target.marches_cibles = ValidationBnecService._markets(source.marches_vises)
        target.statut = "ACTIF"
        element.ressource_cible_id = target.id

    @staticmethod
    async def _execute_certification(
        db: AsyncSession,
        *,
        element: ElementIntegration,
        fiche,
        entreprise,
        actor: AuthContext,
    ) -> None:
        if entreprise is None or element.ressource_source_id is None:
            raise ValueError("Entreprise ou certification déclarée absente.")
        source = await ValidationBnecRepository.get_declared_certification(
            db, element.ressource_source_id
        )
        if source is None or source.fiche_collecte_id != fiche.id:
            raise ValueError("Certification source incohérente.")
        if source.date_obtention is None:
            raise ValueError("La date d'obtention est obligatoire.")
        if source.date_expiration and source.date_expiration <= source.date_obtention:
            raise ValueError("Les dates de certification sont incohérentes.")
        organisme = await ValidationBnecRepository.find_organism_by_label(
            db, source.organisme_declare or ""
        )
        if organisme is None:
            raise ValueError(
                "L'organisme déclaré doit être rapproché avant l'intégration."
            )
        norm_resolution = await ValidationBnecService._resolve_norm_reference(
            db,
            source.norme_declaree,
            create_missing=True,
        )
        norm_error = ValidationBnecService._norm_resolution_error(norm_resolution)
        if norm_error:
            raise ValueError(
                "La norme déclarée ne peut pas être intégrée : " + norm_error + "."
            )
        norme = norm_resolution.norme
        if norme is None:
            raise ValueError("La norme déclarée ne peut pas être résolue.")
        if norm_resolution.created:
            await write_audit_event(
                db,
                action="BNEC_NORME_AUTO_CREATE",
                categorie="REFERENTIEL_NORME",
                resultat="SUCCES",
                utilisateur_id=actor.user.id,
                ressource_type="norme",
                ressource_id=norme.id,
                valeurs_apres={
                    "code": norme.code,
                    "nom": norme.nom,
                    "version": norme.version,
                    "statut": norme.statut,
                    "source": "CERTIFICATION_DECLAREE_VALIDEE_N2",
                    "certification_declaree_id": str(source.id),
                },
            )

        target = None
        if source.certification_officielle_id:
            target = await ValidationBnecRepository.get_official_certification(
                db, source.certification_officielle_id
            )
        if target is None and element.ressource_cible_id:
            target = await ValidationBnecRepository.get_official_certification(
                db, element.ressource_cible_id
            )
        if target is None and clean_text(source.numero):
            target = await ValidationBnecRepository.find_certification_by_number(
                db,
                enterprise_id=entreprise.id,
                number=source.numero,
            )
        if target is None:
            target = await ValidationBnecRepository.find_certification_candidate(
                db,
                enterprise_id=entreprise.id,
                organisme_id=organisme.id,
                norme_id=norme.id,
                scope=source.portee,
            )

        previous_status = target.statut if target else None
        created = target is None
        if created:
            context = await ValidationBnecService._certification_code_context(
                db,
                entreprise=entreprise,
                source=source,
                organisme=organisme,
                norme=norme,
            )
            assignment = await CodificationService.reserve(
                db,
                object_type="CERTIFICATION",
                context=context,
                element=element,
            )
            target = Certification(
                identifiant_national=assignment.code,
                entreprise_id=entreprise.id,
                organisme_id=organisme.id,
                accreditation_id=None,
                norme_id=norme.id,
            )
            db.add(target)
            await db.flush()
            element.action = "CREER"
        else:
            if target.entreprise_id != entreprise.id:
                raise ValueError(
                    "La certification cible appartient à une autre entreprise."
                )
            element.action = "RAPPROCHER"
            element.code_genere = target.identifiant_national

        target.organisme_id = organisme.id
        target.norme_id = norme.id
        target.numero_certificat = clean_text(source.numero)
        target.portee = clean_text(source.portee)
        target.date_obtention = source.date_obtention
        target.date_effet = source.date_obtention
        target.date_expiration = source.date_expiration
        target.statut = ValidationBnecService._certification_status(source)
        target.motif_statut = (
            f"Situation déclarée validée : {source.situation_declaree}"
            if source.situation_declaree
            else "Intégration d'une collecte validée N2"
        )
        target.authenticite_verifiee = source.copie_disponible is True
        target.source_donnee = "COLLECTE_VALIDEE"
        # Toutes les déclarations strictement identiques de la même fiche sont
        # reliées à l'unique certification officielle. Le plan ne crée ainsi
        # qu'une ressource BNEC tout en conservant la traçabilité des lignes
        # déclaratives d'origine.
        declaration_key = certification_declaration_key(source)
        for declaration in await ValidationBnecRepository.list_declared_certifications(
            db, fiche.id
        ):
            if certification_declaration_key(declaration) != declaration_key:
                continue
            declaration.certification_officielle_id = target.id
            declaration.score_rapprochement = 100
            declaration.statut_rapprochement = (
                "INTEGRE_BNEC" if created else "RAPPROCHE_AUTO"
            )
        element.ressource_cible_id = target.id
        db.add(
            EvenementCertification(
                certification_id=target.id,
                type_evenement="INTEGRATION_BNEC",
                ancien_statut=previous_status,
                nouveau_statut=target.statut,
                date_evenement=datetime.now(timezone.utc),
                motif="Intégration automatique depuis une validation N2.",
                source="SNGSC_INTEGRATION_BNEC",
                acteur_id=actor.user.id,
            )
        )
        await WatchService.synchronize_certification_schedule(
            db,
            certification=target,
            declared_situation=source.situation_declaree,
        )

    @staticmethod
    async def _execute_element(
        db: AsyncSession,
        *,
        element: ElementIntegration,
        fiche,
        entreprise,
        actor: AuthContext,
    ) -> None:
        kind = (element.type_objet or "").upper()
        if kind == "ENTREPRISE":
            await ValidationBnecService._execute_enterprise(
                db,
                element=element,
                fiche=fiche,
                entreprise=entreprise,
            )
        elif kind == "OFFRE":
            await ValidationBnecService._execute_offer(
                db,
                element=element,
                fiche=fiche,
                entreprise=entreprise,
            )
        elif kind == "CERTIFICATION":
            await ValidationBnecService._execute_certification(
                db,
                element=element,
                fiche=fiche,
                entreprise=entreprise,
                actor=actor,
            )
        else:
            raise ValueError(f"Type d'objet non pris en charge : {kind or 'vide'}.")

    @staticmethod
    async def _refresh_enterprise_status(
        db: AsyncSession,
        entreprise,
    ) -> None:
        if entreprise is None:
            return
        active = await ValidationBnecRepository.count_active_certifications(
            db, entreprise.id
        )
        if active > 0:
            entreprise.statut = "CERTIFIEE_ACTIVE"
        elif not entreprise.rccm:
            entreprise.statut = "EN_ATTENTE_REGULARISATION"
        else:
            entreprise.statut = "A_VERIFIER"
        entreprise.date_derniere_verification = date.today()
        entreprise.source_donnee = "COLLECTE_VALIDEE"

    @staticmethod
    async def _automatic_postcontrol(
        db: AsyncSession,
        *,
        integration: IntegrationBnec,
        fiche,
        entreprise,
        elements: list[ElementIntegration],
    ) -> None:
        if entreprise is None or ValidationBnecService._enterprise_needs_codification(
            entreprise
        ):
            raise ValueError("Le code BNEC définitif de l'entreprise est absent.")
        if any(item.statut != "INTEGRE" for item in elements):
            raise ValueError("Tous les éléments n'ont pas été intégrés.")
        declarations = await ValidationBnecRepository.list_declared_certifications(
            db, fiche.id
        )
        unlinked = [item for item in declarations if not item.certification_officielle_id]
        if unlinked:
            raise ValueError(
                f"{len(unlinked)} certification(s) déclarée(s) ne sont pas reliées."
            )
        for element in elements:
            if element.type_objet in {"ENTREPRISE", "CERTIFICATION"}:
                if not element.code_genere:
                    raise ValueError(
                        f"Code définitif absent pour {element.type_objet}."
                    )
        integration.postcontrole = "OK"

    @staticmethod
    async def start(
        db: AsyncSession,
        *,
        integration_id: UUID,
        payload: IntegrationStartRequest,
        actor: AuthContext,
        request: Request,
    ) -> IntegrationResponse:
        """Précontrôle, codification, intégration et postcontrôle en un clic.

        Toutes les ressources métier sont placées dans un même savepoint. Une
        erreur annule l'ensemble des créations/mises à jour afin d'éviter une
        intégration partielle silencieuse.
        """

        required_permissions = {
            "INTEGRATION.EXECUTER",
            "INTEGRATION.PRECONTROLER",
            "INTEGRATION.POSTCONTROLER",
            "INTEGRATION.CLOTURER",
        }
        missing_permissions = sorted(required_permissions - set(actor.permissions))
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "L’intégration automatique exige les habilitations complètes : "
                    + ", ".join(missing_permissions)
                    + "."
                ),
            )

        integration, validation, fiche, entreprise = (
            await ValidationBnecService._source_context(db, integration_id)
        )
        if integration.statut == "INTEGREE":
            return await ValidationBnecService.integration_response(db, integration)
        if integration.statut == "INTEGRATION_EN_COURS":
            raise HTTPException(409, "Une exécution est déjà en cours.")

        elements = await ValidationBnecService._seed_integration_elements(
            db,
            integration=integration,
        )
        try:
            plan = await ValidationBnecService._automatic_precontrol(
                db,
                integration=integration,
            )
        except ValueError as exc:
            integration.precontrole = "ECHEC"
            integration.statut = "BLOQUE"
            integration.resume = str(exc)
            await write_audit_event(
                db,
                action="BNEC_AUTOMATIC_PRECONTROL",
                categorie="INTEGRATION_BNEC",
                resultat="ECHEC",
                utilisateur_id=actor.user.id,
                ressource_type="integration_bnec",
                ressource_id=integration.id,
                adresse_ip=client_ip(request),
                contexte={"erreur": str(exc)},
            )
            await db.commit()
            raise HTTPException(409, str(exc)) from exc

        integration.administrateur_id = actor.user.id
        integration.date_debut = date.today()
        integration.date_fin = None
        integration.statut = "INTEGRATION_EN_COURS"
        if clean_text(payload.resume):
            integration.resume = clean_text(payload.resume)

        failing_element_id = None
        try:
            async with db.begin_nested():
                ordered = sorted(
                    elements,
                    key=lambda item: {
                        "ENTREPRISE": 0,
                        "OFFRE": 1,
                        "CERTIFICATION": 2,
                    }.get((item.type_objet or "").upper(), 99),
                )
                for element in ordered:
                    failing_element_id = element.id
                    await ValidationBnecService._execute_element(
                        db,
                        element=element,
                        fiche=fiche,
                        entreprise=entreprise,
                        actor=actor,
                    )
                    element.statut = "INTEGRE"
                    element.message_erreur = None
                    await db.flush()

                await ValidationBnecService._refresh_enterprise_status(
                    db, entreprise
                )
                await db.flush()
                await ValidationBnecService._automatic_postcontrol(
                    db,
                    integration=integration,
                    fiche=fiche,
                    entreprise=entreprise,
                    elements=ordered,
                )
        except Exception as exc:
            # Le savepoint a annulé toutes les ressources officielles. On
            # recharge les éléments pour enregistrer une erreur réessayable.
            integration = await ValidationBnecService.get_integration(
                db, integration_id
            )
            refreshed = await ValidationBnecRepository.list_elements(
                db, integration_id
            )
            for element in refreshed:
                element.statut = (
                    "ECHEC" if element.id == failing_element_id else "PRET"
                )
                element.message_erreur = (
                    (str(exc) or exc.__class__.__name__)[:255]
                    if element.id == failing_element_id
                    else None
                )
                if element.statut != "INTEGRE":
                    element.code_genere = None
                    element.codification_regle_id = None
                    element.codification_logical_code = None
                    element.codification_version = None
                    element.codification_format = None
                    element.codification_scope_key = None
                    element.codification_sequence = None
                    element.codification_segments = None
            integration.statut = "ECHEC"
            integration.postcontrole = "ECHEC"
            integration.date_fin = date.today()
            integration.resume = (str(exc) or exc.__class__.__name__)[:2000]
            await write_audit_event(
                db,
                action="BNEC_INTEGRATION_AUTOMATIC_EXECUTE",
                categorie="INTEGRATION_BNEC",
                resultat="ECHEC",
                utilisateur_id=actor.user.id,
                ressource_type="integration_bnec",
                ressource_id=integration.id,
                adresse_ip=client_ip(request),
                contexte={
                    "erreur": str(exc),
                    "rollback_complet": True,
                    "element_id": str(failing_element_id) if failing_element_id else None,
                },
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "L'intégration a été annulée intégralement : "
                    + (str(exc) or exc.__class__.__name__)
                ),
            ) from exc

        integration.statut = "INTEGREE"
        integration.precontrole = "OK"
        integration.postcontrole = "OK"
        integration.date_fin = date.today()
        integration.sauvegarde_reference = (
            integration.sauvegarde_reference
            or f"BNEC-TX-{date.today():%Y%m%d}-{str(integration.id)[:8].upper()}"
        )
        integration.resume = clean_text(payload.resume) or (
            f"Intégration automatique réussie : {plan.total} ressource(s)."
        )
        await write_audit_event(
            db,
            action="BNEC_INTEGRATION_AUTOMATIC_EXECUTE",
            categorie="INTEGRATION_BNEC",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="integration_bnec",
            ressource_id=integration.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "statut": integration.statut,
                "precontrole": "OK",
                "postcontrole": "OK",
                "elements": len(elements),
                "rollback_complet_si_erreur": True,
                "codes": [
                    {
                        "type_objet": item.type_objet,
                        "code": item.code_genere,
                        "modele": item.codification_logical_code,
                        "version": item.codification_version,
                        "format": item.codification_format,
                        "segments": item.codification_segments,
                    }
                    for item in elements
                    if item.code_genere
                ],
            },
        )
        await db.commit()
        await db.refresh(integration)
        return await ValidationBnecService.integration_response(db, integration)

    @staticmethod
    async def list_elements(
        db: AsyncSession,
        integration_id: UUID,
    ) -> list[IntegrationElementResponse]:
        await ValidationBnecService.get_integration(db, integration_id)
        items = await ValidationBnecRepository.list_elements(db, integration_id)
        return [element_response(item) for item in items]

    @staticmethod
    async def create_element(*args, **kwargs):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="La saisie manuelle des éléments d'intégration a été supprimée.",
        )

    @staticmethod
    async def update_element(*args, **kwargs):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Les UUID et codes d'intégration sont désormais calculés automatiquement.",
        )

    @staticmethod
    async def element_result(*args, **kwargs):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Le résultat de chaque élément est déterminé automatiquement.",
        )

    @staticmethod
    async def postcontrol(
        db: AsyncSession,
        *,
        integration_id: UUID,
        payload: IntegrationCheckRequest,
        actor: AuthContext,
        request: Request,
    ) -> IntegrationResponse:
        integration = await ValidationBnecService.get_integration(db, integration_id)
        if integration.statut != "INTEGREE":
            raise HTTPException(
                409,
                "Le postcontrôle est automatique pendant l'intégration.",
            )
        return await ValidationBnecService.integration_response(db, integration)

    @staticmethod
    async def complete(
        db: AsyncSession,
        *,
        integration_id: UUID,
        actor: AuthContext,
        request: Request,
    ) -> IntegrationResponse:
        integration = await ValidationBnecService.get_integration(db, integration_id)
        if integration.statut != "INTEGREE":
            raise HTTPException(
                409,
                "La clôture est automatique après un postcontrôle réussi.",
            )
        return await ValidationBnecService.integration_response(db, integration)
