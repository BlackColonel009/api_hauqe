"""
Service métier de contrôle des doublons d'entreprises.

DOCTRINE MÉTIER
---------------
La procédure de vérification HAUQE impose de rapprocher notamment :
- nom / sigle ;
- IFU / NIF ;
- téléphone ;
- courriel ;
- localisation.

Un doublon potentiel ne doit PAS être fusionné ou écarté automatiquement.
Il doit faire l'objet :
1. d'un enregistrement de candidat ;
2. d'un examen humain ;
3. d'une décision motivée ;
4. d'une trace d'audit.

Le service ne contient donc volontairement aucun endpoint "merge".
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.candidat_doublon import CandidatDoublon
from app.repositories.candidat_doublon_repository import (
    CandidatDoublonRepository,
)
from app.schemas.candidat_doublon import (
    CandidatDoublonCreateRequest,
    CandidatDoublonDecisionRequest,
    CandidatDoublonListResponse,
    CandidatDoublonResponse,
)
from app.services.auth_service import AuthContext


def client_ip(request: Request) -> str | None:
    if request.client is None:
        return None
    return request.client.host


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def build_response(
    candidat: CandidatDoublon,
) -> CandidatDoublonResponse:
    return CandidatDoublonResponse(
        id=candidat.id,
        entreprise_source_id=candidat.entreprise_source_id,
        entreprise_cible_id=candidat.entreprise_cible_id,
        criteres_concordants=candidat.criteres_concordants,
        score_similarite=candidat.score_similarite,
        statut_examen=candidat.statut_examen,
        decision=candidat.decision,
        motif_decision=candidat.motif_decision,
        examine_par_id=candidat.examine_par_id,
        examine_at=candidat.examine_at,
        created_at=candidat.created_at,
        updated_at=candidat.updated_at,
    )


class CandidatDoublonService:

    @staticmethod
    async def list_candidats(
        db: AsyncSession,
        *,
        entreprise_id: UUID | None,
        statut_examen: str | None,
        decision: str | None,
        limit: int,
        offset: int,
    ) -> CandidatDoublonListResponse:
        items, total = await CandidatDoublonRepository.list_candidats(
            db,
            entreprise_id=entreprise_id,
            statut_examen=statut_examen,
            decision=decision,
            limit=limit,
            offset=offset,
        )

        return CandidatDoublonListResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=[build_response(item) for item in items],
        )

    @staticmethod
    async def get_candidat(
        db: AsyncSession,
        *,
        candidat_id: UUID,
    ) -> CandidatDoublonResponse:
        candidat = await CandidatDoublonRepository.get_by_id(
            db,
            candidat_id,
        )

        if candidat is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidat de doublon introuvable.",
            )

        return build_response(candidat)

    @staticmethod
    async def create_candidat(
        db: AsyncSession,
        *,
        payload: CandidatDoublonCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> CandidatDoublonResponse:
        """
        Enregistre un rapprochement suspect.

        `examine_par_id` est NOT NULL dans le MPD actuel. L'utilisateur
        authentifié devient donc l'examinateur affecté à ce candidat.
        `examine_at` reste NULL tant qu'aucune décision n'a été prise.
        """

        if payload.entreprise_source_id == payload.entreprise_cible_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Une entreprise ne peut pas être comparée à elle-même."
                ),
            )

        source = await CandidatDoublonRepository.get_entreprise(
            db,
            payload.entreprise_source_id,
        )
        cible = await CandidatDoublonRepository.get_entreprise(
            db,
            payload.entreprise_cible_id,
        )

        if source is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entreprise source introuvable.",
            )

        if cible is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entreprise cible introuvable.",
            )

        candidat = CandidatDoublon(
            entreprise_source_id=payload.entreprise_source_id,
            entreprise_cible_id=payload.entreprise_cible_id,
            criteres_concordants=payload.criteres_concordants,
            score_similarite=payload.score_similarite,
            statut_examen=clean_text(payload.statut_examen),
            decision=None,
            motif_decision=None,

            # Le MPD impose cette FK en NOT NULL.
            examine_par_id=actor.user.id,

            # Pas encore examiné/décidé à la création.
            examine_at=None,
        )

        db.add(candidat)
        await db.flush()

        await write_audit_event(
            db,
            action="ENTREPRISE_DOUBLON_CREATE",
            categorie="QUALITE_DONNEES",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="candidat_doublon",
            ressource_id=candidat.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "entreprise_source_id":
                    str(candidat.entreprise_source_id),
                "entreprise_cible_id":
                    str(candidat.entreprise_cible_id),
                "criteres_concordants":
                    candidat.criteres_concordants,
                "score_similarite": (
                    str(candidat.score_similarite)
                    if candidat.score_similarite is not None
                    else None
                ),
                "statut_examen":
                    candidat.statut_examen,
                "examine_par_id":
                    str(candidat.examine_par_id),
            },
        )

        await db.commit()
        await db.refresh(candidat)
        return build_response(candidat)

    @staticmethod
    async def decide(
        db: AsyncSession,
        *,
        candidat_id: UUID,
        payload: CandidatDoublonDecisionRequest,
        actor: AuthContext,
        request: Request,
    ) -> CandidatDoublonResponse:
        """
        Enregistre une décision humaine motivée.

        Les valeurs possibles de `statut_examen` et `decision` ne sont pas
        figées dans le service afin de ne pas inventer un référentiel
        institutionnel non encore validé.
        """

        candidat = await CandidatDoublonRepository.get_by_id(
            db,
            candidat_id,
        )

        if candidat is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidat de doublon introuvable.",
            )

        before = {
            "statut_examen": candidat.statut_examen,
            "decision": candidat.decision,
            "motif_decision": candidat.motif_decision,
            "examine_par_id": str(candidat.examine_par_id),
            "examine_at": (
                candidat.examine_at.isoformat()
                if candidat.examine_at is not None
                else None
            ),
        }

        candidat.statut_examen = payload.statut_examen.strip()
        candidat.decision = payload.decision.strip()
        candidat.motif_decision = payload.motif_decision.strip()

        # La décision est toujours rattachée à l'utilisateur qui la prend.
        candidat.examine_par_id = actor.user.id
        candidat.examine_at = datetime.now(timezone.utc)

        await write_audit_event(
            db,
            action="ENTREPRISE_DOUBLON_DECISION",
            categorie="QUALITE_DONNEES",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="candidat_doublon",
            ressource_id=candidat.id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
            valeurs_apres={
                "statut_examen": candidat.statut_examen,
                "decision": candidat.decision,
                "motif_decision": candidat.motif_decision,
                "examine_par_id": str(candidat.examine_par_id),
                "examine_at": candidat.examine_at.isoformat(),
            },
        )

        await db.commit()
        await db.refresh(candidat)
        return build_response(candidat)
