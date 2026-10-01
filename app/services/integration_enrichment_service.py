"""Compléments prudents des anciennes collectes au passage BNEC.

Les valeurs déjà présentes dans les registres restent prioritaires. Cette
étape ne déduit ni identité juridique, ni accréditation, ni reconnaissance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.contact_entreprise import ContactEntreprise
from app.models.entreprise import Entreprise
from app.models.fiche_collecte import FicheCollecte
from app.models.offre_declaree import OffreDeclaree
from app.models.organisme import Organisme
from app.models.certification_declaree import CertificationDeclaree
from app.repositories.validation_bnec_repository import ValidationBnecRepository


def _text(value: str | None) -> str | None:
    return value.strip() or None if value else None


@dataclass(slots=True)
class EnterpriseComplements:
    activity: str | None = None
    activity_offer_id: UUID | None = None
    contact: ContactEntreprise | None = None
    contact_values: dict[str, str] = field(default_factory=dict)
    create_contact: bool = False

    def descriptions(self) -> list[str]:
        result = []
        if self.activity:
            result.append("Entreprise : activité principale renseignée depuis l'offre déclarée")
        if self.create_contact:
            result.append("Entreprise : contact du déclarant créé depuis la fiche")
        elif self.contact_values:
            result.append("Entreprise : contact du déclarant complété depuis la fiche")
        return result


class IntegrationEnrichmentService:
    @staticmethod
    def _activity_candidate(offers: list[OffreDeclaree]) -> tuple[str | None, UUID | None]:
        descriptions: dict[str, tuple[str, UUID]] = {}
        for offer in offers:
            if (offer.statut or "ACTIF").upper() not in {"ACTIF", "ACTIVE"}:
                continue
            description = _text(offer.description)
            if description:
                descriptions.setdefault(description.casefold(), (description[:255], offer.id))
        # Plusieurs descriptions distinctes ne permettent pas de déduire une
        # activité principale sans décision humaine.
        return next(iter(descriptions.values())) if len(descriptions) == 1 else (None, None)

    @staticmethod
    async def plan_enterprise(
        db: AsyncSession, *, fiche: FicheCollecte, entreprise: Entreprise
    ) -> EnterpriseComplements:
        plan = EnterpriseComplements()
        if not _text(entreprise.activite_principale):
            offers = await ValidationBnecRepository.list_declared_offers(db, fiche.id)
            plan.activity, plan.activity_offer_id = IntegrationEnrichmentService._activity_candidate(offers)

        values = {
            "nom": _text(fiche.nom_declarant),
            "fonction": _text(fiche.fonction_declarant),
            "telephone": _text(fiche.telephone_declarant),
            "email": _text(fiche.email_declarant),
        }
        if not values["nom"] and not values["email"]:
            return plan

        contacts = list((await db.execute(
            select(ContactEntreprise).where(ContactEntreprise.entreprise_id == entreprise.id)
        )).scalars().all())
        email = values["email"]
        nom = values["nom"]
        if any(
            email and _text(item.email) and item.email.casefold() == email.casefold()
            and nom and _text(item.nom) and item.nom.casefold() != nom.casefold()
            for item in contacts
        ):
            return plan
        if any(
            nom and _text(item.nom) and item.nom.casefold() == nom.casefold()
            and (item.type_contact or "").upper() == "DECLARANT_COLLECTE"
            and email and _text(item.email) and item.email.casefold() != email.casefold()
            for item in contacts
        ):
            return plan
        matching = [
            item for item in contacts
            if email and _text(item.email) and item.email.casefold() == email.casefold()
            and (not nom or not _text(item.nom) or item.nom.casefold() == nom.casefold())
        ]
        if not matching and nom:
            matching = [
                item for item in contacts
                if (item.type_contact or "").upper() == "DECLARANT_COLLECTE"
                and _text(item.nom) and item.nom.casefold() == nom.casefold()
                and (not email or not _text(item.email) or item.email.casefold() == email.casefold())
            ]
        if len(matching) > 1:
            # Une identité ambiguë doit être rapprochée manuellement.
            return plan
        plan.contact = matching[0] if matching else None
        if plan.contact is None:
            plan.create_contact = True
            plan.contact_values = {key: value for key, value in values.items() if value}
        else:
            plan.contact_values = {
                key: value for key, value in values.items()
                if value and not _text(getattr(plan.contact, key))
            }
        return plan

    @staticmethod
    async def apply_enterprise(
        db: AsyncSession, *, fiche: FicheCollecte, entreprise: Entreprise,
        actor_id: UUID, integration_id: UUID,
    ) -> list[str]:
        plan = await IntegrationEnrichmentService.plan_enterprise(
            db, fiche=fiche, entreprise=entreprise
        )
        if plan.activity:
            entreprise.activite_principale = plan.activity
            await write_audit_event(
                db, action="BNEC_ENTREPRISE_COMPLEMENT", categorie="INTEGRATION_BNEC",
                resultat="SUCCES", utilisateur_id=actor_id,
                ressource_type="entreprise", ressource_id=entreprise.id,
                valeurs_avant={"activite_principale": None},
                valeurs_apres={"activite_principale": plan.activity},
                contexte={"integration_id": str(integration_id),
                          "fiche_collecte_id": str(fiche.id),
                          "offre_declaree_id": str(plan.activity_offer_id)},
            )
        if plan.create_contact:
            contact = ContactEntreprise(
                entreprise_id=entreprise.id, **plan.contact_values,
                type_contact="DECLARANT_COLLECTE", contact_principal=False,
                statut="ACTIF",
            )
            db.add(contact)
            await db.flush()
            before = None
        elif plan.contact_values and plan.contact is not None:
            contact = plan.contact
            before = {key: getattr(contact, key) for key in plan.contact_values}
            for key, value in plan.contact_values.items():
                setattr(contact, key, value)
        else:
            contact = None
            before = None
        if contact is not None:
            await write_audit_event(
                db, action="BNEC_DECLARANT_CONTACT_COMPLEMENT",
                categorie="INTEGRATION_BNEC", resultat="SUCCES",
                utilisateur_id=actor_id, ressource_type="contact_entreprise",
                ressource_id=contact.id, valeurs_avant=before,
                valeurs_apres=plan.contact_values,
                contexte={"integration_id": str(integration_id),
                          "fiche_collecte_id": str(fiche.id)},
            )
        return plan.descriptions()

    @staticmethod
    def organism_name_complement(
        source: CertificationDeclaree, organisme: Organisme
    ) -> str | None:
        return _text(source.organisme_declare) if not _text(organisme.nom_officiel) else None

    @staticmethod
    async def apply_organism_name(
        db: AsyncSession, *, source: CertificationDeclaree, organisme: Organisme,
        actor_id: UUID, integration_id: UUID,
    ) -> bool:
        name = IntegrationEnrichmentService.organism_name_complement(source, organisme)
        if not name:
            return False
        organisme.nom_officiel = name
        await write_audit_event(
            db, action="BNEC_ORGANISME_COMPLEMENT", categorie="INTEGRATION_BNEC",
            resultat="SUCCES", utilisateur_id=actor_id,
            ressource_type="organisme", ressource_id=organisme.id,
            valeurs_avant={"nom_officiel": None},
            valeurs_apres={"nom_officiel": name},
            contexte={"integration_id": str(integration_id),
                      "certification_declaree_id": str(source.id)},
        )
        return True
