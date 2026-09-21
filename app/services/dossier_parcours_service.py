"""Lecture consolidée du parcours Collecte → BNEC d'une même fiche."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.controle_fuccs import ControleFuccs
from app.models.dossier_verification import DossierVerification
from app.models.fiche_collecte import FicheCollecte
from app.models.integration_bnec import IntegrationBnec
from app.models.validation import Validation
from app.schemas.dossier_parcours import (
    ParcoursDossierResponse,
    ParcoursEtapeResponse,
)


FAVORABLE = {"VALIDE", "VALIDE_SOUS_RESERVE"}
BLOCKING_DECISIONS = {"AJOURNE", "REJETE"}


class DossierParcoursService:
    """Construit un état de progression lisible, sans exposer d'identifiant technique."""

    @staticmethod
    async def _fiche_id_for_source(
        db: AsyncSession, *, source: str, resource_id: UUID
    ) -> UUID:
        source = source.strip().lower()
        if source == "fiche":
            fiche_id = await db.scalar(
                select(FicheCollecte.id).where(FicheCollecte.id == resource_id)
            )
        elif source == "verification":
            fiche_id = await db.scalar(
                select(DossierVerification.fiche_collecte_id).where(
                    DossierVerification.id == resource_id
                )
            )
        elif source == "controle":
            fiche_id = await db.scalar(
                select(DossierVerification.fiche_collecte_id)
                .join(
                    ControleFuccs,
                    ControleFuccs.dossier_verification_id == DossierVerification.id,
                )
                .where(ControleFuccs.id == resource_id)
            )
        elif source == "validation":
            fiche_id = await db.scalar(
                select(Validation.fiche_collecte_id).where(Validation.id == resource_id)
            )
        elif source == "integration":
            fiche_id = await db.scalar(
                select(Validation.fiche_collecte_id)
                .join(IntegrationBnec, IntegrationBnec.validation_id == Validation.id)
                .where(IntegrationBnec.id == resource_id)
            )
        else:
            raise HTTPException(404, "Type de dossier introuvable.")

        if fiche_id is None:
            raise HTTPException(404, "Dossier introuvable.")
        return fiche_id

    @staticmethod
    def _step(code: str, label: str, status: str, detail: str, resource_id=None):
        return ParcoursEtapeResponse(
            code=code,
            libelle=label,
            statut=status,
            detail=detail,
            ressource_id=resource_id,
        )

    @staticmethod
    async def for_source(
        db: AsyncSession, *, source: str, resource_id: UUID
    ) -> ParcoursDossierResponse:
        fiche_id = await DossierParcoursService._fiche_id_for_source(
            db, source=source, resource_id=resource_id
        )
        fiche = await db.scalar(select(FicheCollecte).where(FicheCollecte.id == fiche_id))
        verification = await db.scalar(
            select(DossierVerification)
            .where(DossierVerification.fiche_collecte_id == fiche_id)
            .order_by(DossierVerification.updated_at.desc())
        )
        controle = None
        if verification:
            controle = await db.scalar(
                select(ControleFuccs)
                .where(ControleFuccs.dossier_verification_id == verification.id)
                .order_by(ControleFuccs.updated_at.desc())
            )
        n1 = await db.scalar(
            select(Validation)
            .where(
                Validation.fiche_collecte_id == fiche_id,
                Validation.niveau_validation == "NIVEAU_1",
            )
            .order_by(Validation.created_at.desc())
        )
        n2 = await db.scalar(
            select(Validation)
            .where(
                Validation.fiche_collecte_id == fiche_id,
                Validation.niveau_validation == "NIVEAU_2",
            )
            .order_by(Validation.created_at.desc())
        )
        integration = await db.scalar(
            select(IntegrationBnec)
            .join(Validation, IntegrationBnec.validation_id == Validation.id)
            .where(Validation.fiche_collecte_id == fiche_id)
            .order_by(IntegrationBnec.updated_at.desc())
        )

        steps: list[ParcoursEtapeResponse] = []
        collecte_done = bool(fiche.soumise_at) or (fiche.statut or "").upper() == "SOUMISE"
        steps.append(DossierParcoursService._step(
            "COLLECTE", "Collecte", "TERMINE" if collecte_done else "EN_COURS",
            "Fiche soumise et prête pour vérification." if collecte_done else "Fiche à compléter puis à soumettre.",
            fiche.id,
        ))

        verification_done = bool(verification and verification.date_fin)
        if verification_done:
            verification_status, verification_detail = "TERMINE", "Vérification documentaire clôturée."
        elif verification:
            verification_status, verification_detail = "EN_COURS", "Vérification documentaire en cours."
        else:
            verification_status = "A_FAIRE"
            verification_detail = "À ouvrir après la soumission de la fiche." if collecte_done else "Disponible après la soumission de la fiche."
        steps.append(DossierParcoursService._step(
            "VERIFICATION", "Vérification documentaire", verification_status,
            verification_detail, verification.id if verification else None,
        ))

        controle_done = bool(controle and (controle.statut or "").upper() == "FINALISE")
        if controle_done:
            controle_status, controle_detail = "TERMINE", "Contrôle FUCCS finalisé."
        elif controle and (controle.statut or "").upper() in {"BLOQUE", "ECHEC"}:
            controle_status, controle_detail = "BLOQUE", "Contrôle FUCCS à corriger avant validation."
        elif controle:
            controle_status, controle_detail = "EN_COURS", "Contrôle FUCCS en cours de renseignement."
        else:
            controle_status = "A_FAIRE"
            controle_detail = "Disponible après la clôture de la vérification." if verification_done else "Disponible après la vérification documentaire."
        steps.append(DossierParcoursService._step(
            "FUCCS", "Contrôle FUCCS", controle_status, controle_detail,
            controle.id if controle else None,
        ))

        def validation_step(validation: Validation | None, level: str, predecessor_done: bool):
            if validation and validation.decision in FAVORABLE and validation.statut == "TERMINE":
                return "TERMINE", f"Décision {level} favorable prononcée."
            if validation and validation.decision in BLOCKING_DECISIONS:
                return "BLOQUE", f"Décision {level} {validation.decision.lower()} : action ou correction requise."
            if validation:
                return "EN_COURS", f"Décision {level} en cours de traitement."
            if predecessor_done:
                return "A_FAIRE", f"Décision {level} à prononcer."
            return "A_FAIRE", f"Disponible après l'étape précédente."

        n1_status, n1_detail = validation_step(n1, "N1", controle_done)
        steps.append(DossierParcoursService._step(
            "N1", "Validation N1", n1_status, n1_detail, n1.id if n1 else None
        ))
        n1_done = n1_status == "TERMINE"
        n2_status, n2_detail = validation_step(n2, "N2", n1_done)
        steps.append(DossierParcoursService._step(
            "N2", "Validation N2", n2_status, n2_detail, n2.id if n2 else None
        ))

        n2_done = n2_status == "TERMINE"
        integration_key = (integration.statut or "").upper() if integration else ""
        if integration_key == "INTEGREE":
            integration_status, integration_detail = "TERMINE", "Dossier intégré dans la BNEC."
        elif integration_key in {"BLOQUE", "ECHEC"}:
            integration_status, integration_detail = "BLOQUE", "Intégration BNEC bloquée : analyser les éléments signalés."
        elif integration:
            integration_status, integration_detail = "EN_COURS", "Précontrôle ou intégration BNEC en cours."
        elif n2_done:
            integration_status, integration_detail = "A_FAIRE", "Intégration BNEC à ouvrir."
        else:
            integration_status, integration_detail = "A_FAIRE", "Disponible après une décision N2 favorable."
        steps.append(DossierParcoursService._step(
            "BNEC", "Intégration BNEC", integration_status, integration_detail,
            integration.id if integration else None,
        ))

        active = next((step for step in steps if step.statut in {"BLOQUE", "EN_COURS"}), None)
        upcoming = next((step for step in steps if step.statut == "A_FAIRE"), None)
        target = active or upcoming
        next_action = (
            f"{target.libelle} — {target.detail}"
            if target else "Parcours terminé : le dossier est intégré dans la BNEC."
        )
        return ParcoursDossierResponse(
            fiche_collecte_id=fiche_id,
            etapes=steps,
            prochaine_action=next_action,
            etapes_restantes=sum(step.statut != "TERMINE" for step in steps),
            bloque=any(step.statut == "BLOQUE" for step in steps),
        )
