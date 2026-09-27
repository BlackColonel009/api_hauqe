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
from sqlalchemy import delete, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.certification_declaree import CertificationDeclaree
from app.models.contact_entreprise import ContactEntreprise
from app.models.document import Document
from app.models.evenement_collecte import EvenementCollecte
from app.models.fiche_collecte import FicheCollecte
from app.models.offre_entreprise import OffreEntreprise
from app.models.offre_declaree import OffreDeclaree
from app.models.organisme import Organisme
from app.repositories.fiche_collecte_repository import (
    FicheCollecteRepository,
)
from app.repositories.mission_collecte_repository import (
    MissionCollecteRepository,
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
        dossier_id=item.dossier_id,
        responsable_id=item.responsable_id,
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
    "EXPIREE",
    "AUDIT_INITIAL",
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
        organisme_id=item.organisme_id,
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
    async def resolve_declared_organisme(db: AsyncSession, organisme_id, libelle):
        """Garantit la liaison registre d'une certification déclarée.

        Une saisie libre est normalisée en organisme du registre marqué « À
        vérifier ». Ainsi, une collecte ne peut plus laisser une certification
        sans organisme rapprochable lors du parcours BNEC.
        """
        label = clean_text(libelle)
        if organisme_id is not None:
            organisme = await FicheCollecteRepository.get_organisme(db, organisme_id)
            if organisme is None:
                raise HTTPException(status_code=404, detail="Organisme certificateur introuvable.")
            return (
                organisme.id,
                clean_text(organisme.nom_officiel)
                or clean_text(organisme.sigle)
                or label,
            )

        if not label:
            return None, None

        organisme = await FicheCollecteRepository.find_organisme_by_label(db, label)
        if organisme is None:
            organisme = Organisme(
                nom_officiel=label,
                type_organisme="CERTIFICATION",
                statut="A_VERIFIER",
            )
            db.add(organisme)
            await db.flush()
        return organisme.id, clean_text(organisme.nom_officiel) or label

    @staticmethod
    async def synchronize_declarant_contact(
        db: AsyncSession,
        *,
        fiche: FicheCollecte,
        actor: AuthContext,
        request: Request,
    ) -> None:
        """Expose le déclarant de la collecte dans les contacts de l'entreprise."""
        if fiche.entreprise_id is None:
            return
        values = {
            "nom": clean_text(fiche.nom_declarant),
            "fonction": clean_text(fiche.fonction_declarant),
            "telephone": clean_text(fiche.telephone_declarant),
            "email": clean_text(fiche.email_declarant),
        }
        if not any(values.values()):
            return

        filters = [ContactEntreprise.entreprise_id == fiche.entreprise_id]
        if values["email"]:
            filters.append(ContactEntreprise.email == values["email"])
        else:
            filters.append(ContactEntreprise.type_contact == "DECLARANT_COLLECTE")
        result = await db.execute(
            select(ContactEntreprise)
            .where(*filters)
            .order_by(ContactEntreprise.created_at.desc())
            .limit(1)
        )
        contact = result.scalar_one_or_none()
        if contact is None:
            contact = ContactEntreprise(
                entreprise_id=fiche.entreprise_id,
                nom=values["nom"],
                prenoms=None,
                fonction=values["fonction"],
                telephone=values["telephone"],
                email=values["email"],
                type_contact="DECLARANT_COLLECTE",
                contact_principal=False,
                statut="ACTIF",
            )
            db.add(contact)
            await db.flush()
            action = "COLLECTE_DECLARANT_CONTACT_CREATE"
            before = None
        else:
            before = {
                "nom": contact.nom,
                "fonction": contact.fonction,
                "telephone": contact.telephone,
                "email": contact.email,
            }
            for field, value in values.items():
                if value is not None:
                    setattr(contact, field, value)
            contact.type_contact = contact.type_contact or "DECLARANT_COLLECTE"
            contact.statut = "ACTIF"
            action = "COLLECTE_DECLARANT_CONTACT_UPDATE"

        await write_audit_event(
            db,
            action=action,
            categorie="COLLECTE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="contact_entreprise",
            ressource_id=contact.id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
            valeurs_apres={**values, "fiche_collecte_id": str(fiche.id)},
        )

    @staticmethod
    async def initialize_enterprise_activity_from_offer(
        db: AsyncSession,
        *,
        fiche: FicheCollecte,
        offer: OffreDeclaree,
        actor: AuthContext,
        request: Request,
    ) -> None:
        """Initialise une activité principale encore vide, sans l'écraser."""
        description = clean_text(offer.description)
        if fiche.entreprise_id is None or not description:
            return
        enterprise = await FicheCollecteRepository.get_entreprise(
            db,
            fiche.entreprise_id,
        )
        if enterprise is None or clean_text(enterprise.activite_principale):
            return
        enterprise.activite_principale = description[:255]
        await write_audit_event(
            db,
            action="COLLECTE_ENTERPRISE_ACTIVITY_INITIALIZE",
            categorie="COLLECTE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="entreprise",
            ressource_id=enterprise.id,
            adresse_ip=client_ip(request),
            valeurs_avant={"activite_principale": None},
            valeurs_apres={
                "activite_principale": enterprise.activite_principale,
                "offre_declaree_id": str(offer.id),
                "fiche_collecte_id": str(fiche.id),
            },
        )

    @staticmethod
    def collection_market_values(value: str | None) -> list[str]:
        """Transforme la saisie libre de marchés en valeurs réutilisables."""
        values: list[str] = []
        for part in (value or "").replace(";", ",").split(","):
            cleaned = clean_text(part)
            if cleaned and cleaned not in values:
                values.append(cleaned)
        return values

    @staticmethod
    def enterprise_offer_key(item) -> tuple[str, str, str]:
        """Clé métier stable pour éviter un produit dupliqué dans l'entreprise."""
        return tuple(
            (clean_text(value) or "").casefold()
            for value in (item.type_offre, item.nom, item.categorie)
        )

    @staticmethod
    async def synchronize_enterprise_offers(
        db: AsyncSession,
        *,
        fiche: FicheCollecte,
        actor: AuthContext | None,
        request: Request | None,
    ) -> dict[str, int]:
        """Copie les offres d'une fiche soumise dans le dossier entreprise.

        Les produits sont rapprochés par type, nom et catégorie. Les marchés
        déclarés alimentent à la fois les marchés cibles et les destinations
        de l'offre entreprise, afin de rester visibles dans sa vue d'ensemble.
        """
        summary = {"created": 0, "updated": 0, "skipped": 0}
        if fiche.entreprise_id is None:
            return summary

        enterprise = await FicheCollecteRepository.get_entreprise(
            db,
            fiche.entreprise_id,
        )
        if enterprise is None:
            return summary

        sources = await FicheCollecteRepository.list_offres(db, fiche.id)
        result = await db.execute(
            select(OffreEntreprise).where(
                OffreEntreprise.entreprise_id == enterprise.id
            )
        )
        targets = list(result.scalars().all())
        targets_by_key = {
            FicheCollecteService.enterprise_offer_key(item): item
            for item in targets
        }
        processed_source_keys: set[tuple[str, str, str]] = set()

        for source in sources:
            if not clean_text(source.nom):
                # Une offre sans nom reste dans la collecte pour correction,
                # mais ne doit pas créer une ligne incompréhensible du registre.
                summary["skipped"] += 1
                continue

            key = FicheCollecteService.enterprise_offer_key(source)
            if key in processed_source_keys:
                # La fiche peut contenir une ligne répétée par une ancienne
                # saisie. La première ligne est la référence de migration ;
                # une seconde ne doit ni créer ni écraser l'offre entreprise.
                summary["skipped"] += 1
                continue
            processed_source_keys.add(key)
            target = targets_by_key.get(key)
            markets = FicheCollecteService.collection_market_values(
                source.marches_vises
            )
            before = None

            if target is None:
                target = OffreEntreprise(entreprise_id=enterprise.id)
                db.add(target)
                await db.flush()
                targets_by_key[key] = target
                summary["created"] += 1
                action = "COLLECTE_ENTERPRISE_OFFER_CREATE"
            else:
                before = {
                    "type_offre": target.type_offre,
                    "nom": target.nom,
                    "categorie": target.categorie,
                    "description": target.description,
                    "marches_cibles": target.marches_cibles,
                    "destinations": target.destinations,
                }
                summary["updated"] += 1
                action = "COLLECTE_ENTERPRISE_OFFER_UPDATE"

            target.type_offre = clean_text(source.type_offre)
            target.nom = clean_text(source.nom)
            target.description = clean_text(source.description)
            target.categorie = clean_text(source.categorie)
            target.volume_annuel = source.volume
            target.unite = clean_text(source.unite)
            target.capacite_production = source.capacite
            target.marches_cibles = markets
            target.destinations = markets
            target.statut = clean_text(source.statut) or "ACTIF"

            await write_audit_event(
                db,
                action=action,
                categorie="COLLECTE",
                resultat="SUCCES",
                utilisateur_id=actor.user.id if actor else None,
                ressource_type="offre_entreprise",
                ressource_id=target.id,
                adresse_ip=client_ip(request) if request else None,
                valeurs_avant=before,
                valeurs_apres={
                    "entreprise_id": str(enterprise.id),
                    "fiche_collecte_id": str(fiche.id),
                    "offre_declaree_id": str(source.id),
                    "type_offre": target.type_offre,
                    "nom": target.nom,
                    "categorie": target.categorie,
                    "marches_cibles": markets,
                    "destinations": markets,
                },
            )

        return summary


    @staticmethod
    async def ensure_actor_can_write_mission(
        db: AsyncSession,
        *,
        mission_id: UUID,
        actor: AuthContext,
    ) -> None:
        """Autorise l'écriture seulement à un agent affecté à la mission.

        Le détenteur de ``COLLECTE.AFFECTER`` est le responsable de la
        collecte (administrateur ou point focal) : il peut intervenir sur
        toutes les missions. Les autres profils de collecte doivent disposer
        d'une affectation dont le statut est actif.
        """
        await MissionCollecteService.get(db, mission_id)

        if "COLLECTE.AFFECTER" in actor.permissions:
            return

        assignment = (
            await MissionCollecteRepository
            .get_active_assignment_for_user(
                db,
                mission_id=mission_id,
                utilisateur_id=actor.user.id,
            )
        )
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Vous ne pouvez pas saisir dans cette mission : "
                    "une affectation active par un administrateur HAUQE "
                    "est requise."
                ),
            )

    @staticmethod
    def ensure_actor_can_write_fiche(
        fiche: FicheCollecte,
        actor: AuthContext,
    ) -> None:
        """Une fiche appartient à son collecteur jusqu'à une intervention admin."""
        if "COLLECTE.AFFECTER" in actor.permissions:
            return
        if fiche.responsable_id != actor.user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Cette fiche est déjà prise en charge par un autre agent. "
                    "Elle reste consultable, mais seule son ou sa responsable "
                    "ou un administrateur HAUQE peut la modifier."
                ),
            )

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
        item = await FicheCollecteService.get(
            db, mission_id=mission_id, fiche_id=fiche_id
        )
        current = await FicheCollecteRepository.get_current(
            db,
            mission_id,
            dossier_id=item.dossier_id or item.id,
        )
        if current is None or current.id != fiche_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cette fiche n'est pas la révision courante "
                    "de ce dossier de collecte."
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
        await FicheCollecteService.ensure_actor_can_write_mission(
            db,
            mission_id=mission_id,
            actor=actor,
        )

        current = await FicheCollecteRepository.get_current(
            db,
            mission_id,
            entreprise_id=payload.entreprise_id,
        ) if payload.entreprise_id is not None else None
        if current is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Cette entreprise possède déjà une fiche dans cette mission. "
                    "Utilisez sa révision courante ou créez une nouvelle "
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
            dossier_id=None,  # renseigné après génération de l'UUID
            responsable_id=actor.user.id,
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
        item.dossier_id = item.id

        await FicheCollecteService.synchronize_declarant_contact(
            db,
            fiche=item,
            actor=actor,
            request=request,
        )

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
        await FicheCollecteService.ensure_actor_can_write_mission(
            db,
            mission_id=mission_id,
            actor=actor,
        )
        item = await FicheCollecteService.ensure_draft_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )
        FicheCollecteService.ensure_actor_can_write_fiche(item, actor)

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
            duplicate = await FicheCollecteRepository.get_current(
                db,
                mission_id,
                entreprise_id=changes["entreprise_id"],
            )
            if (
                duplicate is not None
                and (duplicate.dossier_id or duplicate.id)
                != (item.dossier_id or item.id)
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Cette entreprise possède déjà une collecte dans cette mission. "
                        "Ouvrez sa fiche existante au lieu de créer un doublon."
                    ),
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

        # `collecte_par_id` conserve le dernier intervenant historique ; le
        # responsable métier reste stable sur la fiche.
        item.collecte_par_id = actor.user.id
        item.collecte_at = datetime.now(timezone.utc)

        await FicheCollecteService.synchronize_declarant_contact(
            db,
            fiche=item,
            actor=actor,
            request=request,
        )

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
    async def reset_draft(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
        actor: AuthContext,
        request: Request,
    ) -> FicheCollecteResponse:
        """
        Réinitialise une fiche courante en BROUILLON sans supprimer la mission.

        La mission (campagne, zone, période et agents affectés) n'est jamais
        modifiée : elle peut contenir d'autres collectes d'entreprises. Les
        documents déjà déposés sont désactivés, jamais supprimés physiquement.
        """
        await FicheCollecteService.ensure_actor_can_write_mission(
            db,
            mission_id=mission_id,
            actor=actor,
        )
        item = await FicheCollecteService.ensure_draft_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )
        FicheCollecteService.ensure_actor_can_write_fiche(item, actor)
        offers = await FicheCollecteRepository.list_offres(db, item.id)
        certifications = await FicheCollecteRepository.list_certifications(
            db,
            item.id,
        )
        document_rows = list((await db.execute(
            select(Document)
            .where(
                Document.ressource_type == "FICHE_COLLECTE",
                Document.ressource_id == item.id,
                or_(
                    Document.statut.is_(None),
                    Document.statut != "INACTIF",
                ),
            )
            .with_for_update()
        )).scalars().all())

        before = {
            "entreprise_id": str(item.entreprise_id) if item.entreprise_id else None,
            "offres": len(offers),
            "certifications_declarees": len(certifications),
            "documents_desactives": len(document_rows),
        }

        # Ne vider que les données de cette fiche. Une mission peut accueillir
        # plusieurs entreprises : ses informations communes ne doivent jamais
        # être effacées par la réinitialisation d'un seul brouillon.
        item.entreprise_id = None
        item.version_formulaire = "HAUQE-COLLECTE-SIMPLIFIEE-V1"
        item.consentement_obtenu = False
        item.nom_declarant = None
        item.fonction_declarant = None
        item.telephone_declarant = None
        item.email_declarant = None
        item.signature_declarant = None
        item.observations = None
        item.collecte_par_id = actor.user.id
        item.collecte_at = datetime.now(timezone.utc)

        if offers:
            await db.execute(
                delete(OffreDeclaree).where(
                    OffreDeclaree.fiche_collecte_id == item.id
                )
            )
        if certifications:
            await db.execute(
                delete(CertificationDeclaree).where(
                    CertificationDeclaree.fiche_collecte_id == item.id
                )
            )
        for document in document_rows:
            document.statut = "INACTIF"

        await FicheCollecteService.calculate_completeness(db, item)
        await FicheCollecteService.record_event(
            db,
            fiche_id=item.id,
            type_evenement="REINITIALISATION_BROUILLON",
            ancien_statut=item.statut,
            nouveau_statut=item.statut,
            commentaire="Saisie de cette fiche réinitialisée ; mission inchangée.",
            acteur_id=actor.user.id,
        )
        await write_audit_event(
            db,
            action="COLLECTE_FORM_RESET",
            categorie="COLLECTE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="fiche_collecte",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
            valeurs_apres={
                "entreprise_id": None,
                "offres": 0,
                "certifications_declarees": 0,
                "documents_actifs": 0,
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
        await FicheCollecteService.ensure_actor_can_write_mission(
            db,
            mission_id=mission_id,
            actor=actor,
        )
        item = await FicheCollecteService.ensure_draft_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )
        FicheCollecteService.ensure_actor_can_write_fiche(item, actor)

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
        offers_sync = await FicheCollecteService.synchronize_enterprise_offers(
            db,
            fiche=item,
            actor=actor,
            request=request,
        )
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
                "offres_entreprise": offers_sync,
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
        await FicheCollecteService.ensure_actor_can_write_mission(
            db,
            mission_id=mission_id,
            actor=actor,
        )
        current = await FicheCollecteService.ensure_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )
        FicheCollecteService.ensure_actor_can_write_fiche(current, actor)

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
            dossier_id=current.dossier_id or current.id,
            responsable_id=current.responsable_id,
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
                    organisme_id=old.organisme_id,
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
        await FicheCollecteService.ensure_actor_can_write_mission(
            db,
            mission_id=mission_id,
            actor=actor,
        )
        fiche = await FicheCollecteService.ensure_draft_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )
        FicheCollecteService.ensure_actor_can_write_fiche(fiche, actor)

        type_offre = clean_text(payload.type_offre)
        nom = clean_text(payload.nom)
        categorie = clean_text(payload.categorie)
        if nom:
            duplicate = await FicheCollecteRepository.find_equivalent_offre(
                db,
                fiche_id=fiche.id,
                type_offre=type_offre,
                nom=nom,
                categorie=categorie,
            )
            if duplicate is not None:
                # Une seconde requête identique (double clic, latence, reprise
                # réseau) reçoit l'offre déjà créée au lieu d'en créer une autre.
                return offre_response(duplicate)

        item = OffreDeclaree(
            fiche_collecte_id=fiche.id,
            type_offre=type_offre,
            nom=nom,
            description=clean_text(payload.description),
            categorie=categorie,
            volume=payload.volume,
            unite=clean_text(payload.unite),
            capacite=payload.capacite,
            marches_vises=clean_text(payload.marches_vises),
            statut=clean_text(payload.statut) or "ACTIF",
        )

        db.add(item)
        try:
            await db.flush()
        except IntegrityError:
            # La contrainte PostgreSQL couvre deux requêtes concurrentes qui
            # auraient franchi le contrôle applicatif au même instant.
            await db.rollback()
            duplicate = await FicheCollecteRepository.find_equivalent_offre(
                db,
                fiche_id=fiche_id,
                type_offre=type_offre,
                nom=nom or "",
                categorie=categorie,
            )
            if duplicate is not None:
                return offre_response(duplicate)
            raise

        await FicheCollecteService.initialize_enterprise_activity_from_offer(
            db,
            fiche=fiche,
            offer=item,
            actor=actor,
            request=request,
        )

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
        await FicheCollecteService.ensure_actor_can_write_mission(
            db,
            mission_id=mission_id,
            actor=actor,
        )
        fiche = await FicheCollecteService.ensure_draft_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )
        FicheCollecteService.ensure_actor_can_write_fiche(fiche, actor)

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

        prospective_type = clean_text(
            changes.get("type_offre", item.type_offre)
        )
        prospective_nom = clean_text(changes.get("nom", item.nom))
        prospective_categorie = clean_text(
            changes.get("categorie", item.categorie)
        )
        if prospective_nom:
            duplicate = await FicheCollecteRepository.find_equivalent_offre(
                db,
                fiche_id=fiche.id,
                type_offre=prospective_type,
                nom=prospective_nom,
                categorie=prospective_categorie,
                exclude_offre_id=item.id,
            )
            if duplicate is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Une offre identique existe déjà dans cette collecte. "
                        "Modifiez son nom, son type ou sa catégorie."
                    ),
                )

        for field, value in changes.items():
            if field in text_fields:
                value = clean_text(value)
            setattr(item, field, value)

        await FicheCollecteService.initialize_enterprise_activity_from_offer(
            db,
            fiche=fiche,
            offer=item,
            actor=actor,
            request=request,
        )

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
    async def delete_offre(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
        offre_id: UUID,
        actor: AuthContext,
        request: Request,
    ) -> None:
        await FicheCollecteService.ensure_actor_can_write_mission(
            db, mission_id=mission_id, actor=actor,
        )
        fiche = await FicheCollecteService.ensure_draft_current(
            db, mission_id=mission_id, fiche_id=fiche_id,
        )
        FicheCollecteService.ensure_actor_can_write_fiche(fiche, actor)
        item = await FicheCollecteRepository.get_offre(
            db, fiche_id=fiche_id, offre_id=offre_id,
        )
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offre déclarée introuvable.")
        await write_audit_event(
            db, action="COLLECTE_DECLARED_OFFER_DELETE", categorie="COLLECTE",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="offre_declaree", ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant={"fiche_collecte_id": str(fiche.id), "nom": item.nom, "type_offre": item.type_offre},
        )
        await db.delete(item)
        await db.commit()

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
        await FicheCollecteService.ensure_actor_can_write_mission(
            db,
            mission_id=mission_id,
            actor=actor,
        )
        fiche = await FicheCollecteService.ensure_draft_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )
        FicheCollecteService.ensure_actor_can_write_fiche(fiche, actor)

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

        organisme_id, organisme_declare = await FicheCollecteService.resolve_declared_organisme(
            db, payload.organisme_id, payload.organisme_declare
        )
        item = CertificationDeclaree(
            fiche_collecte_id=fiche.id,
            nom_certification=clean_text(payload.nom_certification),
            numero=clean_text(payload.numero),
            organisme_declare=organisme_declare,
            organisme_id=organisme_id,
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
                "organisme_id": str(item.organisme_id) if item.organisme_id else None,
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
        await FicheCollecteService.ensure_actor_can_write_mission(
            db,
            mission_id=mission_id,
            actor=actor,
        )
        fiche = await FicheCollecteService.ensure_draft_current(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )
        FicheCollecteService.ensure_actor_can_write_fiche(fiche, actor)

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
            "organisme_id": str(item.organisme_id) if item.organisme_id else None,
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

        if "organisme_id" in changes or "organisme_declare" in changes:
            organisme_id, organisme_declare = await FicheCollecteService.resolve_declared_organisme(
                db,
                changes.get("organisme_id"),
                changes.get("organisme_declare", item.organisme_declare),
            )
            changes["organisme_id"] = organisme_id
            changes["organisme_declare"] = organisme_declare

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
                "organisme_id": str(item.organisme_id) if item.organisme_id else None,
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
    async def delete_certification(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
        certification_declaree_id: UUID,
        actor: AuthContext,
        request: Request,
    ) -> None:
        await FicheCollecteService.ensure_actor_can_write_mission(
            db, mission_id=mission_id, actor=actor,
        )
        fiche = await FicheCollecteService.ensure_draft_current(
            db, mission_id=mission_id, fiche_id=fiche_id,
        )
        FicheCollecteService.ensure_actor_can_write_fiche(fiche, actor)
        item = await FicheCollecteRepository.get_certification(
            db, fiche_id=fiche_id, certification_declaree_id=certification_declaree_id,
        )
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification déclarée introuvable.")
        await write_audit_event(
            db, action="COLLECTE_DECLARED_CERT_DELETE", categorie="COLLECTE",
            resultat="SUCCES", utilisateur_id=actor.user.id,
            ressource_type="certification_declaree", ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant={"fiche_collecte_id": str(fiche.id), "nom_certification": item.nom_certification, "numero": item.numero},
        )
        await db.delete(item)
        await db.commit()

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
