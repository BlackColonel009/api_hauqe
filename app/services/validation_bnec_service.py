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
- l'intégration suit précontrôle -> exécution -> postcontrôle -> intégrée ;
- chaque élément d'intégration est tracé séparément ;
- aucun format de code national n'est inventé ici : `code_genere` reste fourni
  par le mécanisme de codification qui sera paramétré/branché ultérieurement.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.correction import Correction
from app.models.element_integration import ElementIntegration
from app.models.integration_bnec import IntegrationBnec
from app.models.validation import Validation
from app.repositories.validation_bnec_repository import ValidationBnecRepository
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
    IntegrationQueueItem,
    IntegrationResponse,
    IntegrationStartRequest,
    ValidationDecisionRequest,
    ValidationListResponse,
    ValidationQueueItem,
    ValidationResponse,
)
from app.services.auth_service import AuthContext


FAVORABLE = {"VALIDE", "VALIDE_SOUS_RESERVE"}
CORRECTABLE = {"AJOURNE", "VALIDE_SOUS_RESERVE"}


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


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

        fiche = await ValidationBnecRepository.get_fiche(db, fiche_id)
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
    # INTEGRATION BNEC
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
                    eligible=not bool(
                        current
                        and current.statut == "INTEGREE"
                    ),
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
                await ValidationBnecService.integration_response(db, x)
                for x in items
            ],
        )

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
                detail="Seule une validation définitive NIVEAU_2 favorable autorise l'intégration.",
            )

        if await ValidationBnecRepository.active_integration_for_validation(
            db, validation_id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Une intégration active existe déjà pour cette validation.",
            )

        previous = await ValidationBnecRepository.latest_integration_for_validation(
            db, validation_id
        )
        if previous and previous.statut == "INTEGREE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cette validation a déjà été intégrée avec succès.",
            )

        item = IntegrationBnec(
            validation_id=validation_id,
            administrateur_id=actor.user.id,
            date_debut=None,
            date_fin=None,
            statut="EN_ATTENTE",
            precontrole=None,
            postcontrole=None,
            sauvegarde_reference=None,
            resume=clean_text(payload.resume),
        )
        db.add(item)
        await db.flush()

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
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return await ValidationBnecService.integration_response(db, item)

    @staticmethod
    async def precontrol(
        db: AsyncSession,
        *,
        integration_id: UUID,
        payload: IntegrationCheckRequest,
        actor: AuthContext,
        request: Request,
    ) -> IntegrationResponse:
        item = await ValidationBnecService.get_integration(db, integration_id)

        if item.statut not in {"EN_ATTENTE", "PRECONTROLE"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Le précontrôle n'est plus autorisé à ce stade.",
            )

        item.precontrole = payload.resultat
        item.resume = payload.resume.strip()
        if payload.sauvegarde_reference is not None:
            item.sauvegarde_reference = clean_text(payload.sauvegarde_reference)

        if payload.resultat == "OK":
            item.statut = "PRECONTROLE"
        else:
            item.statut = "ECHEC"
            item.date_fin = date.today()

        await write_audit_event(
            db,
            action="BNEC_PRECONTROL",
            categorie="INTEGRATION_BNEC",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="integration_bnec",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "precontrole": item.precontrole,
                "statut": item.statut,
                "sauvegarde_reference": item.sauvegarde_reference,
            },
        )

        await db.commit()
        await db.refresh(item)
        return await ValidationBnecService.integration_response(db, item)

    @staticmethod
    async def start(
        db: AsyncSession,
        *,
        integration_id: UUID,
        payload: IntegrationStartRequest,
        actor: AuthContext,
        request: Request,
    ) -> IntegrationResponse:
        item = await ValidationBnecService.get_integration(db, integration_id)

        if item.precontrole != "OK":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Un précontrôle OK est requis avant l'intégration.",
            )
        if item.statut != "PRECONTROLE":
            raise HTTPException(409, "L'intégration ne peut pas démarrer dans cet état.")

        item.date_debut = date.today()
        item.statut = "INTEGRATION_EN_COURS"
        if clean_text(payload.resume):
            item.resume = clean_text(payload.resume)

        await write_audit_event(
            db,
            action="BNEC_INTEGRATION_START",
            categorie="INTEGRATION_BNEC",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="integration_bnec",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "date_debut": item.date_debut.isoformat(),
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return await ValidationBnecService.integration_response(db, item)

    @staticmethod
    async def list_elements(
        db: AsyncSession,
        integration_id: UUID,
    ) -> list[IntegrationElementResponse]:
        await ValidationBnecService.get_integration(db, integration_id)
        items = await ValidationBnecRepository.list_elements(db, integration_id)
        return [element_response(x) for x in items]

    @staticmethod
    async def create_element(
        db: AsyncSession,
        *,
        integration_id: UUID,
        payload: IntegrationElementCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> IntegrationElementResponse:
        integration = await ValidationBnecService.get_integration(db, integration_id)

        if integration.statut not in {"PRECONTROLE", "INTEGRATION_EN_COURS"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Les éléments ne peuvent être préparés qu'avant le postcontrôle.",
            )

        item = ElementIntegration(
            integration_bnec_id=integration_id,
            type_objet=payload.type_objet.strip().upper(),
            ressource_source_id=payload.ressource_source_id,
            ressource_cible_id=payload.ressource_cible_id,
            revision_source=clean_text(payload.revision_source),
            action=payload.action.strip().upper(),
            code_genere=clean_text(payload.code_genere),
            statut="A_TRAITER",
            message_erreur=None,
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="BNEC_INTEGRATION_ELEMENT_CREATE",
            categorie="INTEGRATION_BNEC",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="element_integration",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "integration_bnec_id": str(integration_id),
                "type_objet": item.type_objet,
                "action": item.action,
                "revision_source": item.revision_source,
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return element_response(item)

    @staticmethod
    async def update_element(
        db: AsyncSession,
        *,
        integration_id: UUID,
        element_id: UUID,
        payload: IntegrationElementUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> IntegrationElementResponse:
        integration = await ValidationBnecService.get_integration(db, integration_id)
        if integration.statut not in {"PRECONTROLE", "INTEGRATION_EN_COURS"}:
            raise HTTPException(409, "Élément verrouillé à ce stade.")

        item = await ValidationBnecRepository.get_element(
            db,
            integration_id=integration_id,
            element_id=element_id,
        )
        if item is None:
            raise HTTPException(404, "Élément d'intégration introuvable.")

        if item.statut == "INTEGRE":
            raise HTTPException(409, "Un élément déjà intégré ne peut pas être réécrit.")

        for field, value in payload.model_dump(exclude_unset=True).items():
            if isinstance(value, str):
                value = clean_text(value)
                if field == "action" and value:
                    value = value.upper()
            setattr(item, field, value)

        await write_audit_event(
            db,
            action="BNEC_INTEGRATION_ELEMENT_UPDATE",
            categorie="INTEGRATION_BNEC",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="element_integration",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
        )

        await db.commit()
        await db.refresh(item)
        return element_response(item)

    @staticmethod
    async def element_result(
        db: AsyncSession,
        *,
        integration_id: UUID,
        element_id: UUID,
        payload: IntegrationElementResultRequest,
        actor: AuthContext,
        request: Request,
    ) -> IntegrationElementResponse:
        integration = await ValidationBnecService.get_integration(db, integration_id)

        if integration.statut != "INTEGRATION_EN_COURS":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Les résultats d'élément exigent une intégration en cours.",
            )

        item = await ValidationBnecRepository.get_element(
            db,
            integration_id=integration_id,
            element_id=element_id,
        )
        if item is None:
            raise HTTPException(404, "Élément d'intégration introuvable.")

        if payload.resultat == "INTEGRE":
            item.statut = "INTEGRE"
            item.ressource_cible_id = (
                payload.ressource_cible_id or item.ressource_cible_id
            )
            item.code_genere = clean_text(payload.code_genere) or item.code_genere
            item.message_erreur = None
        else:
            item.statut = "ECHEC"
            item.message_erreur = clean_text(payload.message_erreur) or (
                "Échec d'intégration sans message détaillé."
            )

        await write_audit_event(
            db,
            action="BNEC_INTEGRATION_ELEMENT_RESULT",
            categorie="INTEGRATION_BNEC",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="element_integration",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "statut": item.statut,
                "ressource_cible_id": (
                    str(item.ressource_cible_id)
                    if item.ressource_cible_id else None
                ),
                "code_genere": item.code_genere,
                "message_erreur": item.message_erreur,
            },
        )

        await db.commit()
        await db.refresh(item)
        return element_response(item)

    @staticmethod
    async def postcontrol(
        db: AsyncSession,
        *,
        integration_id: UUID,
        payload: IntegrationCheckRequest,
        actor: AuthContext,
        request: Request,
    ) -> IntegrationResponse:
        item = await ValidationBnecService.get_integration(db, integration_id)

        if item.statut != "INTEGRATION_EN_COURS":
            raise HTTPException(409, "Le postcontrôle exige une intégration en cours.")

        total, success, error = await ValidationBnecRepository.integration_counts(
            db, integration_id
        )

        if total == 0:
            raise HTTPException(409, "Aucun élément d'intégration n'a été enregistré.")

        if payload.resultat == "OK":
            if error > 0 or success != total:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Tous les éléments doivent être intégrés avec succès avant un postcontrôle OK.",
                )

        item.postcontrole = payload.resultat
        item.resume = payload.resume.strip()
        if payload.sauvegarde_reference is not None:
            item.sauvegarde_reference = clean_text(payload.sauvegarde_reference)

        if payload.resultat == "OK":
            item.statut = "POSTCONTROLE"
        else:
            item.statut = "ECHEC"
            item.date_fin = date.today()

        await write_audit_event(
            db,
            action="BNEC_POSTCONTROL",
            categorie="INTEGRATION_BNEC",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="integration_bnec",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "postcontrole": item.postcontrole,
                "statut": item.statut,
                "sauvegarde_reference": item.sauvegarde_reference,
                "elements_count": total,
            },
        )

        await db.commit()
        await db.refresh(item)
        return await ValidationBnecService.integration_response(db, item)

    @staticmethod
    async def complete(
        db: AsyncSession,
        *,
        integration_id: UUID,
        actor: AuthContext,
        request: Request,
    ) -> IntegrationResponse:
        item = await ValidationBnecService.get_integration(db, integration_id)

        if item.statut != "POSTCONTROLE" or item.postcontrole != "OK":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Un postcontrôle OK est requis avant clôture.",
            )

        if not clean_text(item.sauvegarde_reference):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Une référence de sauvegarde est requise avant clôture.",
            )

        total, success, error = await ValidationBnecRepository.integration_counts(
            db, integration_id
        )
        if total == 0 or error > 0 or success != total:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tous les éléments doivent être intégrés avec succès.",
            )

        item.statut = "INTEGREE"
        item.date_fin = date.today()

        await write_audit_event(
            db,
            action="BNEC_INTEGRATION_COMPLETE",
            categorie="INTEGRATION_BNEC",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="integration_bnec",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "statut": item.statut,
                "date_fin": item.date_fin.isoformat(),
                "sauvegarde_reference": item.sauvegarde_reference,
                "elements_count": total,
            },
        )

        await db.commit()
        await db.refresh(item)
        return await ValidationBnecService.integration_response(db, item)
