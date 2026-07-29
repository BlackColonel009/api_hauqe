"""
Service métier principal de la collecte terrain.

INTERACTIONS
------------
mission_collecte
    -> fiches_collecte (révisions)
         -> offres_declarees
         -> certifications_declarees
         -> evenements_collecte

Les données déclarées restent séparées des données officielles de la BNEC.

COMPLÉTUDE
----------
Le backend ne code pas en dur les exigences institutionnelles de soumission.
Il résout la version publiée applicable du code logique
`COLLECTE_COMPLETUDE`.

La règle peut contenir des exigences FIELD (ALL / ANY) et COUNT
(documents, offres ou certifications déclarées). Le format historique
`required_fields` reste lisible pour compatibilité.

Si aucune règle publiée n'existe, le brouillon reste utilisable mais la
soumission est bloquée.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.certification_declaree import CertificationDeclaree
from app.models.evenement_collecte import EvenementCollecte
from app.models.fiche_collecte import FicheCollecte
from app.models.offre_declaree import OffreDeclaree
from app.repositories.fiche_collecte_repository import (
    FicheCollecteRepository,
)
from app.rules.collecte_completeness import (
    evaluate as evaluate_completeness_rule,
)
from app.schemas.declarations_collecte import (
    CertificationDeclareeCreateRequest,
    CertificationDeclareeResponse,
    CertificationDeclareeUpdateRequest,
    OffreDeclareeCreateRequest,
    OffreDeclareeResponse,
    OffreDeclareeUpdateRequest,
)
from app.schemas.fiche_collecte import (
    EvenementCollecteResponse,
    FicheCollecteCreateRequest,
    FicheCollecteResponse,
    FicheCollecteUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.mission_collecte_service import (
    MissionCollecteService,
)


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def fiche_response(item: FicheCollecte) -> FicheCollecteResponse:
    return FicheCollecteResponse(
        id=item.id,
        mission_id=item.mission_id,
        entreprise_id=item.entreprise_id,
        version_formulaire=item.version_formulaire,
        numero_revision=item.numero_revision,
        statut=item.statut,
        taux_completude=item.taux_completude,
        consentement_obtenu=item.consentement_obtenu,
        nom_declarant=item.nom_declarant,
        fonction_declarant=item.fonction_declarant,
        telephone_declarant=item.telephone_declarant,
        email_declarant=item.email_declarant,
        signature_declarant=item.signature_declarant,
        observations=item.observations,
        collecte_par_id=item.collecte_par_id,
        collecte_at=item.collecte_at,
        soumise_at=item.soumise_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def offre_response(item: OffreDeclaree) -> OffreDeclareeResponse:
    return OffreDeclareeResponse(
        id=item.id,
        fiche_collecte_id=item.fiche_collecte_id,
        type_offre=item.type_offre,
        nom=item.nom,
        description=item.description,
        categorie=item.categorie,
        volume=item.volume,
        unite=item.unite,
        capacite=item.capacite,
        marches_vises=item.marches_vises,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )



DECLARED_CERTIFICATION_SITUATIONS = {
    "PRESENTE",
    "ABSENTE",
    "AUDIT_SURVEILLANCE_1",
    "AUDIT_SURVEILLANCE_2",
    "AUDIT_SURVEILLANCE_3",
    "RENOUVELLEMENT",
}


def normalize_declared_situation(value: str | None) -> str | None:
    normalized = clean_text(value)
    if normalized is None:
        return None
    normalized = normalized.upper()
    if normalized not in DECLARED_CERTIFICATION_SITUATIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Situation déclarée de certification invalide.",
        )
    return normalized


def certification_response(
    item: CertificationDeclaree,
) -> CertificationDeclareeResponse:
    return CertificationDeclareeResponse(
        id=item.id,
        fiche_collecte_id=item.fiche_collecte_id,
        nom_certification=item.nom_certification,
        numero=item.numero,
        organisme_declare=item.organisme_declare,
        norme_declaree=item.norme_declaree,
        portee=item.portee,
        date_obtention=item.date_obtention,
        date_expiration=item.date_expiration,
        copie_disponible=item.copie_disponible,
        situation_declaree=item.situation_declaree,
        certification_officielle_id=item.certification_officielle_id,
        score_rapprochement=item.score_rapprochement,
        statut_rapprochement=item.statut_rapprochement,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def event_response(item: EvenementCollecte) -> EvenementCollecteResponse:
    return EvenementCollecteResponse(
        id=item.id,
        fiche_collecte_id=item.fiche_collecte_id,
        type_evenement=item.type_evenement,
        ancien_statut=item.ancien_statut,
        nouveau_statut=item.nouveau_statut,
        commentaire=item.commentaire,
        acteur_id=item.acteur_id,
        date_evenement=item.date_evenement,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


class FicheCollecteService:

    @staticmethod
    async def get(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
    ) -> FicheCollecte:
        await MissionCollecteService.get(db, mission_id)

        item = await FicheCollecteRepository.get_for_mission(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fiche de collecte introuvable.",
            )
        return item

    @staticmethod
    async def ensure_current(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
    ) -> FicheCollecte:
        current = await FicheCollecteRepository.get_current(
            db,
            mission_id,
        )
        if current is None or current.id != fiche_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cette fiche n'est pas la révision courante "
                    "de la mission."
                ),
            )
        return current

    @staticmethod
    async def ensure_draft_current(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
    ) -> FicheCollecte:
        item = await FicheCollecteService.ensure_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )

        if (item.statut or "").strip().upper() != "BROUILLON":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Seule la révision courante en BROUILLON "
                    "peut être modifiée."
                ),
            )
        return item

    @staticmethod
    async def record_event(
        db: AsyncSession,
        *,
        fiche_id: UUID,
        type_evenement: str,
        ancien_statut: str | None,
        nouveau_statut: str | None,
        commentaire: str | None,
        acteur_id: UUID,
    ) -> EvenementCollecte:
        event = EvenementCollecte(
            fiche_collecte_id=fiche_id,
            type_evenement=type_evenement,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            commentaire=clean_text(commentaire),
            acteur_id=acteur_id,
            date_evenement=datetime.now(timezone.utc),
        )
        db.add(event)
        await db.flush()
        return event



    @staticmethod
    async def calculate_completeness(
        db: AsyncSession,
        fiche: FicheCollecte,
    ) -> tuple[Decimal | None, dict | None]:
        """
        Calcule la complétude à partir de la version publiée applicable
        de COLLECTE_COMPLETUDE.

        La règle reste paramétrique : FIELD (ALL/ANY) et COUNT.
        """
        rule = await FicheCollecteRepository.get_completeness_rule(db)

        if rule is None:
            fiche.taux_completude = None
            return None, None

        params = rule.parametres or {}

        try:
            evaluation = await evaluate_completeness_rule(
                db,
                fiche,
                params,
            )
        except ValueError as exc:
            fiche.taux_completude = None
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "La règle COLLECTE_COMPLETUDE publiée est invalide : "
                    f"{exc}"
                ),
            ) from exc

        rate = evaluation["rate"]
        fiche.taux_completude = rate
        return rate, evaluation["normalized"]
    @staticmethod
    async def list_revisions(
        db: AsyncSession,
        mission_id: UUID,
    ) -> list[FicheCollecteResponse]:
        await MissionCollecteService.get(db, mission_id)
        items = await FicheCollecteRepository.list_revisions(
            db,
            mission_id,
        )
        return [fiche_response(x) for x in items]

    @staticmethod
    async def current(
        db: AsyncSession,
        mission_id: UUID,
    ) -> FicheCollecteResponse:
        await MissionCollecteService.get(db, mission_id)
        item = await FicheCollecteRepository.get_current(
            db,
            mission_id,
        )
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucune fiche n'existe pour cette mission.",
            )
        return fiche_response(item)

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        mission_id: UUID,
        payload: FicheCollecteCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> FicheCollecteResponse:
        await MissionCollecteService.get(db, mission_id)

        current = await FicheCollecteRepository.get_current(
            db,
            mission_id,
        )
        if current is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cette mission possède déjà une fiche. "
                    "Utilisez la révision courante ou créez une nouvelle "
                    "révision depuis celle-ci."
                ),
            )

        if payload.entreprise_id is not None:
            entreprise = await FicheCollecteRepository.get_entreprise(
                db,
                payload.entreprise_id,
            )
            if entreprise is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Entreprise introuvable.",
                )

        now = datetime.now(timezone.utc)

        item = FicheCollecte(
            mission_id=mission_id,
            entreprise_id=payload.entreprise_id,
            version_formulaire=clean_text(payload.version_formulaire),
            numero_revision=1,
            statut="BROUILLON",
            taux_completude=None,
            consentement_obtenu=payload.consentement_obtenu,
            nom_declarant=clean_text(payload.nom_declarant),
            fonction_declarant=clean_text(payload.fonction_declarant),
            telephone_declarant=clean_text(
                payload.telephone_declarant
            ),
            email_declarant=clean_text(payload.email_declarant),
            signature_declarant=clean_text(
                payload.signature_declarant
            ),
            observations=clean_text(payload.observations),
            collecte_par_id=actor.user.id,
            collecte_at=now,
            soumise_at=None,
        )

        db.add(item)
        await db.flush()

        await FicheCollecteService.calculate_completeness(db, item)

        await FicheCollecteService.record_event(
            db,
            fiche_id=item.id,
            type_evenement="CREATION_BROUILLON",
            ancien_statut=None,
            nouveau_statut="BROUILLON",
            commentaire=None,
            acteur_id=actor.user.id,
        )

        await write_audit_event(
            db,
            action="COLLECTE_FORM_CREATE",
            categorie="COLLECTE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="fiche_collecte",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "mission_id": str(mission_id),
                "entreprise_id": (
                    str(item.entreprise_id)
                    if item.entreprise_id else None
                ),
                "numero_revision": item.numero_revision,
                "statut": item.statut,
                "taux_completude": (
                    str(item.taux_completude)
                    if item.taux_completude is not None
                    else None
                ),
            },
        )

        await db.commit()
        await db.refresh(item)
        return fiche_response(item)

    @staticmethod
    async def update(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
        payload: FicheCollecteUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> FicheCollecteResponse:
        item = await FicheCollecteService.ensure_draft_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )

        changes = payload.model_dump(exclude_unset=True)

        if "entreprise_id" in changes and changes["entreprise_id"]:
            entreprise = await FicheCollecteRepository.get_entreprise(
                db,
                changes["entreprise_id"],
            )
            if entreprise is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Entreprise introuvable.",
                )

        before = {
            "entreprise_id": (
                str(item.entreprise_id)
                if item.entreprise_id else None
            ),
            "version_formulaire": item.version_formulaire,
            "consentement_obtenu": item.consentement_obtenu,
            "nom_declarant": item.nom_declarant,
            "fonction_declarant": item.fonction_declarant,
            "telephone_declarant": item.telephone_declarant,
            "email_declarant": item.email_declarant,
            "signature_declarant": item.signature_declarant,
            "observations": item.observations,
            "taux_completude": (
                str(item.taux_completude)
                if item.taux_completude is not None
                else None
            ),
        }

        text_fields = {
            "version_formulaire",
            "nom_declarant",
            "fonction_declarant",
            "telephone_declarant",
            "email_declarant",
            "signature_declarant",
            "observations",
        }

        for field, value in changes.items():
            if field == "situation_declaree":
                value = normalize_declared_situation(value)
            elif field in text_fields:
                value = clean_text(value)
            setattr(item, field, value)

        item.collecte_par_id = actor.user.id
        item.collecte_at = datetime.now(timezone.utc)

        await FicheCollecteService.calculate_completeness(db, item)

        await FicheCollecteService.record_event(
            db,
            fiche_id=item.id,
            type_evenement="MISE_A_JOUR_BROUILLON",
            ancien_statut=item.statut,
            nouveau_statut=item.statut,
            commentaire=None,
            acteur_id=actor.user.id,
        )

        await write_audit_event(
            db,
            action="COLLECTE_FORM_UPDATE",
            categorie="COLLECTE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="fiche_collecte",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
            valeurs_apres={
                "entreprise_id": (
                    str(item.entreprise_id)
                    if item.entreprise_id else None
                ),
                "version_formulaire": item.version_formulaire,
                "consentement_obtenu": item.consentement_obtenu,
                "nom_declarant": item.nom_declarant,
                "fonction_declarant": item.fonction_declarant,
                "telephone_declarant": item.telephone_declarant,
                "email_declarant": item.email_declarant,
                "signature_declarant": item.signature_declarant,
                "observations": item.observations,
                "taux_completude": (
                    str(item.taux_completude)
                    if item.taux_completude is not None
                    else None
                ),
            },
        )

        await db.commit()
        await db.refresh(item)
        return fiche_response(item)

    @staticmethod
    async def submit(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
        commentaire: str | None,
        actor: AuthContext,
        request: Request,
    ) -> FicheCollecteResponse:
        item = await FicheCollecteService.ensure_draft_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )

        rate, params = await FicheCollecteService.calculate_completeness(
            db,
            item,
        )

        if params is None or rate is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Aucune règle de complétude COLLECTE_COMPLETUDE "
                    "publiée/active n'est disponible. "
                    "La soumission est bloquée par sécurité."
                ),
            )

        minimum = Decimal(
            str(params.get("minimum_submission_rate", 100))
        )

        if rate < minimum:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Complétude insuffisante : {rate}% ; "
                    f"minimum requis : {minimum}%."
                ),
            )

        old_status = item.statut
        item.statut = "SOUMISE"
        item.soumise_at = datetime.now(timezone.utc)

        await FicheCollecteService.record_event(
            db,
            fiche_id=item.id,
            type_evenement="SOUMISSION",
            ancien_statut=old_status,
            nouveau_statut="SOUMISE",
            commentaire=commentaire,
            acteur_id=actor.user.id,
        )

        await write_audit_event(
            db,
            action="COLLECTE_FORM_SUBMIT",
            categorie="COLLECTE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="fiche_collecte",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant={"statut": old_status},
            valeurs_apres={
                "statut": "SOUMISE",
                "taux_completude": str(rate),
                "soumise_at": item.soumise_at.isoformat(),
            },
            contexte={"commentaire": clean_text(commentaire)},
        )

        await db.commit()
        await db.refresh(item)
        return fiche_response(item)

    @staticmethod
    async def create_revision(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
        commentaire: str,
        actor: AuthContext,
        request: Request,
    ) -> FicheCollecteResponse:
        current = await FicheCollecteService.ensure_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )

        if (current.statut or "").strip().upper() == "BROUILLON":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "La révision courante est déjà un BROUILLON. "
                    "Modifiez-la au lieu d'en créer une nouvelle."
                ),
            )

        old_revision = current.numero_revision or 0

        new_item = FicheCollecte(
            mission_id=current.mission_id,
            entreprise_id=current.entreprise_id,
            version_formulaire=current.version_formulaire,
            numero_revision=old_revision + 1,
            statut="BROUILLON",
            taux_completude=current.taux_completude,
            consentement_obtenu=current.consentement_obtenu,
            nom_declarant=current.nom_declarant,
            fonction_declarant=current.fonction_declarant,
            telephone_declarant=current.telephone_declarant,
            email_declarant=current.email_declarant,
            signature_declarant=current.signature_declarant,
            observations=current.observations,
            collecte_par_id=actor.user.id,
            collecte_at=datetime.now(timezone.utc),
            soumise_at=None,
        )

        db.add(new_item)
        await db.flush()

        # Les déclarations sont dupliquées afin que la nouvelle révision
        # reste autonome et que l'ancienne conserve exactement son état.
        old_offres = await FicheCollecteRepository.list_offres(
            db,
            current.id,
        )
        for old in old_offres:
            db.add(
                OffreDeclaree(
                    fiche_collecte_id=new_item.id,
                    type_offre=old.type_offre,
                    nom=old.nom,
                    description=old.description,
                    categorie=old.categorie,
                    volume=old.volume,
                    unite=old.unite,
                    capacite=old.capacite,
                    marches_vises=old.marches_vises,
                    statut=old.statut,
                )
            )

        old_certs = await FicheCollecteRepository.list_certifications(
            db,
            current.id,
        )
        for old in old_certs:
            db.add(
                CertificationDeclaree(
                    fiche_collecte_id=new_item.id,
                    nom_certification=old.nom_certification,
                    numero=old.numero,
                    organisme_declare=old.organisme_declare,
                    norme_declaree=old.norme_declaree,
                    portee=old.portee,
                    date_obtention=old.date_obtention,
                    date_expiration=old.date_expiration,
                    copie_disponible=old.copie_disponible,

                    # Le rapprochement officiel n'est pas propagé
                    # automatiquement à une nouvelle révision déclarative.
                    certification_officielle_id=None,
                    score_rapprochement=None,
                    statut_rapprochement=None,
                )
            )

        await FicheCollecteService.record_event(
            db,
            fiche_id=current.id,
            type_evenement="REVISION_SUIVANTE_CREEE",
            ancien_statut=current.statut,
            nouveau_statut=current.statut,
            commentaire=commentaire,
            acteur_id=actor.user.id,
        )

        await FicheCollecteService.record_event(
            db,
            fiche_id=new_item.id,
            type_evenement="NOUVELLE_REVISION",
            ancien_statut=None,
            nouveau_statut="BROUILLON",
            commentaire=commentaire,
            acteur_id=actor.user.id,
        )

        await write_audit_event(
            db,
            action="COLLECTE_FORM_REVISION_CREATE",
            categorie="COLLECTE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="fiche_collecte",
            ressource_id=new_item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "mission_id": str(mission_id),
                "revision_source_id": str(current.id),
                "numero_revision": new_item.numero_revision,
                "statut": new_item.statut,
            },
            contexte={"commentaire": commentaire.strip()},
        )

        await db.commit()
        await db.refresh(new_item)
        return fiche_response(new_item)

    @staticmethod
    async def list_offres(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
    ) -> list[OffreDeclareeResponse]:
        await FicheCollecteService.get(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )
        items = await FicheCollecteRepository.list_offres(db, fiche_id)
        return [offre_response(x) for x in items]

    @staticmethod
    async def create_offre(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
        payload: OffreDeclareeCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> OffreDeclareeResponse:
        fiche = await FicheCollecteService.ensure_draft_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )

        item = OffreDeclaree(
            fiche_collecte_id=fiche.id,
            type_offre=clean_text(payload.type_offre),
            nom=clean_text(payload.nom),
            description=clean_text(payload.description),
            categorie=clean_text(payload.categorie),
            volume=payload.volume,
            unite=clean_text(payload.unite),
            capacite=payload.capacite,
            marches_vises=clean_text(payload.marches_vises),
            statut=clean_text(payload.statut) or "ACTIF",
        )

        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="COLLECTE_DECLARED_OFFER_CREATE",
            categorie="COLLECTE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="offre_declaree",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "fiche_collecte_id": str(fiche.id),
                "type_offre": item.type_offre,
                "nom": item.nom,
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return offre_response(item)

    @staticmethod
    async def update_offre(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
        offre_id: UUID,
        payload: OffreDeclareeUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> OffreDeclareeResponse:
        await FicheCollecteService.ensure_draft_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )

        item = await FicheCollecteRepository.get_offre(
            db,
            fiche_id=fiche_id,
            offre_id=offre_id,
        )
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offre déclarée introuvable.",
            )

        before = {
            "type_offre": item.type_offre,
            "nom": item.nom,
            "description": item.description,
            "categorie": item.categorie,
            "volume": str(item.volume) if item.volume is not None else None,
            "unite": item.unite,
            "capacite": (
                str(item.capacite)
                if item.capacite is not None
                else None
            ),
            "marches_vises": item.marches_vises,
            "statut": item.statut,
        }

        changes = payload.model_dump(exclude_unset=True)
        text_fields = {
            "type_offre",
            "nom",
            "description",
            "categorie",
            "unite",
            "marches_vises",
            "statut",
        }

        for field, value in changes.items():
            if field in text_fields:
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db,
            action="COLLECTE_DECLARED_OFFER_UPDATE",
            categorie="COLLECTE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="offre_declaree",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
            valeurs_apres={
                "type_offre": item.type_offre,
                "nom": item.nom,
                "description": item.description,
                "categorie": item.categorie,
                "volume": (
                    str(item.volume)
                    if item.volume is not None
                    else None
                ),
                "unite": item.unite,
                "capacite": (
                    str(item.capacite)
                    if item.capacite is not None
                    else None
                ),
                "marches_vises": item.marches_vises,
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return offre_response(item)

    @staticmethod
    async def list_certifications(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
    ) -> list[CertificationDeclareeResponse]:
        await FicheCollecteService.get(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )
        items = await FicheCollecteRepository.list_certifications(
            db,
            fiche_id,
        )
        return [certification_response(x) for x in items]

    @staticmethod
    async def create_certification(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
        payload: CertificationDeclareeCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> CertificationDeclareeResponse:
        fiche = await FicheCollecteService.ensure_draft_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )

        if (
            payload.date_obtention is not None
            and payload.date_expiration is not None
            and payload.date_expiration < payload.date_obtention
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "La date d'expiration déclarée ne peut pas "
                    "précéder la date d'obtention."
                ),
            )

        item = CertificationDeclaree(
            fiche_collecte_id=fiche.id,
            nom_certification=clean_text(payload.nom_certification),
            numero=clean_text(payload.numero),
            organisme_declare=clean_text(payload.organisme_declare),
            norme_declaree=clean_text(payload.norme_declaree),
            portee=clean_text(payload.portee),
            date_obtention=payload.date_obtention,
            date_expiration=payload.date_expiration,
            copie_disponible=payload.copie_disponible,
            situation_declaree=normalize_declared_situation(payload.situation_declaree),
            certification_officielle_id=None,
            score_rapprochement=None,
            statut_rapprochement=None,
        )

        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="COLLECTE_DECLARED_CERT_CREATE",
            categorie="COLLECTE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="certification_declaree",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "fiche_collecte_id": str(fiche.id),
                "nom_certification": item.nom_certification,
                "numero": item.numero,
                "organisme_declare": item.organisme_declare,
                "norme_declaree": item.norme_declaree,
                "copie_disponible": item.copie_disponible,
                "situation_declaree": item.situation_declaree,
            },
        )

        await db.commit()
        await db.refresh(item)
        return certification_response(item)

    @staticmethod
    async def update_certification(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
        certification_declaree_id: UUID,
        payload: CertificationDeclareeUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> CertificationDeclareeResponse:
        await FicheCollecteService.ensure_draft_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )

        item = await FicheCollecteRepository.get_certification(
            db,
            fiche_id=fiche_id,
            certification_declaree_id=certification_declaree_id,
        )
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certification déclarée introuvable.",
            )

        changes = payload.model_dump(exclude_unset=True)

        new_obtention = changes.get("date_obtention", item.date_obtention)
        new_expiration = changes.get(
            "date_expiration",
            item.date_expiration,
        )
        if (
            new_obtention is not None
            and new_expiration is not None
            and new_expiration < new_obtention
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "La date d'expiration déclarée ne peut pas "
                    "précéder la date d'obtention."
                ),
            )

        before = {
            "nom_certification": item.nom_certification,
            "numero": item.numero,
            "organisme_declare": item.organisme_declare,
            "norme_declaree": item.norme_declaree,
            "portee": item.portee,
            "date_obtention": (
                item.date_obtention.isoformat()
                if item.date_obtention else None
            ),
            "date_expiration": (
                item.date_expiration.isoformat()
                if item.date_expiration else None
            ),
            "copie_disponible": item.copie_disponible,
            "situation_declaree": item.situation_declaree,
        }

        text_fields = {
            "nom_certification",
            "numero",
            "organisme_declare",
            "norme_declaree",
            "portee",
        }

        for field, value in changes.items():
            if field in text_fields:
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db,
            action="COLLECTE_DECLARED_CERT_UPDATE",
            categorie="COLLECTE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="certification_declaree",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
            valeurs_apres={
                "nom_certification": item.nom_certification,
                "numero": item.numero,
                "organisme_declare": item.organisme_declare,
                "norme_declaree": item.norme_declaree,
                "portee": item.portee,
                "date_obtention": (
                    item.date_obtention.isoformat()
                    if item.date_obtention else None
                ),
                "date_expiration": (
                    item.date_expiration.isoformat()
                    if item.date_expiration else None
                ),
                "copie_disponible": item.copie_disponible,
                "situation_declaree": item.situation_declaree,
            },
        )

        await db.commit()
        await db.refresh(item)
        return certification_response(item)

    @staticmethod
    async def history(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
    ) -> list[EvenementCollecteResponse]:
        await FicheCollecteService.get(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )
        items = await FicheCollecteRepository.list_events(db, fiche_id)
        return [event_response(x) for x in items]
