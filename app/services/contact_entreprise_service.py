"""
Service métier des contacts entreprise.

RÔLE DU FICHIER
---------------
Appliquer la logique métier avant modification de PostgreSQL.

Règles actuelles :
- l'entreprise doit exister ;
- une entreprise archivée ne reçoit plus de nouveau contact ;
- un contact doit appartenir à l'entreprise de l'URL ;
- pas de DELETE physique ;
- les changements sont journalisés.

Le champ contact_principal est conservé tel quel.

Nous n'imposons pas encore une règle "un seul contact principal"
tant que cette règle métier n'a pas été explicitement validée.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import (
    HTTPException,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.contact_entreprise import (
    ContactEntreprise,
)
from app.repositories.contact_entreprise_repository import (
    ContactEntrepriseRepository,
)
from app.schemas.contact_entreprise import (
    ContactEntrepriseCreateRequest,
    ContactEntrepriseResponse,
    ContactEntrepriseUpdateRequest,
)
from app.services.auth_service import AuthContext


# ============================================================
# OUTILS
# ============================================================

def client_ip(
    request: Request,
) -> str | None:

    if request.client is None:
        return None

    return request.client.host


def clean_text(
    value: str | None,
) -> str | None:
    """
    Convertit une chaîne vide en NULL.
    """

    if value is None:
        return None

    value = value.strip()

    return value or None


def build_response(
    contact: ContactEntreprise,
) -> ContactEntrepriseResponse:

    return ContactEntrepriseResponse(
        id=contact.id,
        entreprise_id=contact.entreprise_id,

        nom=contact.nom,
        prenoms=contact.prenoms,
        fonction=contact.fonction,

        telephone=contact.telephone,
        email=contact.email,

        type_contact=contact.type_contact,

        contact_principal=(
            contact.contact_principal
        ),

        statut=contact.statut,

        created_at=contact.created_at,
        updated_at=contact.updated_at,
    )


# ============================================================
# SERVICE
# ============================================================

class ContactEntrepriseService:

    # ========================================================
    # VÉRIFICATION ENTREPRISE
    # ========================================================

    @staticmethod
    async def require_entreprise(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
    ):
        """
        Centralise le contrôle d'existence de l'entreprise.
        """

        entreprise = (
            await ContactEntrepriseRepository
            .get_entreprise(
                db,
                entreprise_id,
            )
        )

        if entreprise is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entreprise introuvable.",
            )

        return entreprise


    # ========================================================
    # LISTE
    # ========================================================

    @staticmethod
    async def list_contacts(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        include_inactive: bool,
    ) -> list[ContactEntrepriseResponse]:

        await ContactEntrepriseService.require_entreprise(
            db,
            entreprise_id=entreprise_id,
        )

        contacts = (
            await ContactEntrepriseRepository
            .list_contacts(
                db,
                entreprise_id=entreprise_id,
                include_inactive=include_inactive,
            )
        )

        return [
            build_response(contact)
            for contact in contacts
        ]


    # ========================================================
    # CRÉATION
    # ========================================================

    @staticmethod
    async def create_contact(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        payload: ContactEntrepriseCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> ContactEntrepriseResponse:

        entreprise = (
            await ContactEntrepriseService
            .require_entreprise(
                db,
                entreprise_id=entreprise_id,
            )
        )

        # ----------------------------------------------------
        # Une entreprise archivée reste consultable mais
        # n'est plus alimentée par des données opérationnelles.
        # ----------------------------------------------------

        if (
            entreprise.statut or ""
        ).strip().upper() == "ARCHIVE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Impossible d'ajouter un contact "
                    "à une entreprise archivée."
                ),
            )

        contact = ContactEntreprise(
            entreprise_id=entreprise_id,

            nom=clean_text(payload.nom),
            prenoms=clean_text(payload.prenoms),
            fonction=clean_text(payload.fonction),

            telephone=clean_text(payload.telephone),
            email=clean_text(payload.email),

            type_contact=clean_text(
                payload.type_contact
            ),

            contact_principal=(
                payload.contact_principal
            ),

            statut="ACTIF",
        )

        db.add(contact)

        await db.flush()

        # ----------------------------------------------------
        # Audit métier
        # ----------------------------------------------------

        await write_audit_event(
            db,
            action="ENTREPRISE_CONTACT_CREATE",
            categorie="DONNEES_METIER",
            resultat="SUCCES",

            utilisateur_id=actor.user.id,

            ressource_type="contact_entreprise",
            ressource_id=contact.id,

            adresse_ip=client_ip(request),

            valeurs_apres={
                "entreprise_id":
                    str(entreprise_id),
                "nom":
                    contact.nom,
                "prenoms":
                    contact.prenoms,
                "fonction":
                    contact.fonction,
                "email":
                    contact.email,
                "telephone":
                    contact.telephone,
                "contact_principal":
                    contact.contact_principal,
                "statut":
                    contact.statut,
            },
        )

        await db.commit()

        await db.refresh(contact)

        return build_response(contact)


    # ========================================================
    # MODIFICATION
    # ========================================================

    @staticmethod
    async def update_contact(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        contact_id: UUID,
        payload: ContactEntrepriseUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> ContactEntrepriseResponse:

        await ContactEntrepriseService.require_entreprise(
            db,
            entreprise_id=entreprise_id,
        )

        contact = (
            await ContactEntrepriseRepository
            .get_contact(
                db,
                entreprise_id=entreprise_id,
                contact_id=contact_id,
            )
        )

        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact introuvable.",
            )

        if (
            contact.statut or ""
        ).strip().upper() == "INACTIF":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Un contact désactivé ne peut pas "
                    "être modifié."
                ),
            )

        before = {
            "nom": contact.nom,
            "prenoms": contact.prenoms,
            "fonction": contact.fonction,
            "telephone": contact.telephone,
            "email": contact.email,
            "type_contact": contact.type_contact,
            "contact_principal":
                contact.contact_principal,
        }

        changes = payload.model_dump(
            exclude_unset=True
        )

        text_fields = {
            "nom",
            "prenoms",
            "fonction",
            "telephone",
            "email",
            "type_contact",
        }

        for field, value in changes.items():

            if field in text_fields:
                value = clean_text(value)

            setattr(
                contact,
                field,
                value,
            )

        await write_audit_event(
            db,
            action="ENTREPRISE_CONTACT_UPDATE",
            categorie="DONNEES_METIER",
            resultat="SUCCES",

            utilisateur_id=actor.user.id,

            ressource_type="contact_entreprise",
            ressource_id=contact.id,

            adresse_ip=client_ip(request),

            valeurs_avant=before,

            valeurs_apres={
                "nom": contact.nom,
                "prenoms": contact.prenoms,
                "fonction": contact.fonction,
                "telephone": contact.telephone,
                "email": contact.email,
                "type_contact":
                    contact.type_contact,
                "contact_principal":
                    contact.contact_principal,
            },
        )

        await db.commit()

        await db.refresh(contact)

        return build_response(contact)


    # ========================================================
    # DÉSACTIVATION
    # ========================================================

    @staticmethod
    async def deactivate_contact(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        contact_id: UUID,
        motif: str | None,
        actor: AuthContext,
        request: Request,
    ) -> ContactEntrepriseResponse:
        """
        Désactivation logique uniquement.

        Aucun DELETE SQL n'est exécuté.
        """

        contact = (
            await ContactEntrepriseRepository
            .get_contact(
                db,
                entreprise_id=entreprise_id,
                contact_id=contact_id,
            )
        )

        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact introuvable.",
            )

        if (
            contact.statut or ""
        ).strip().upper() == "INACTIF":
            return build_response(contact)

        previous_status = contact.statut

        contact.statut = "INACTIF"

        await write_audit_event(
            db,
            action="ENTREPRISE_CONTACT_DEACTIVATE",
            categorie="DONNEES_METIER",
            resultat="SUCCES",

            utilisateur_id=actor.user.id,

            ressource_type="contact_entreprise",
            ressource_id=contact.id,

            adresse_ip=client_ip(request),

            valeurs_avant={
                "statut": previous_status,
            },

            valeurs_apres={
                "statut": "INACTIF",
            },

            contexte={
                "motif": clean_text(motif),
            },
        )

        await db.commit()

        await db.refresh(contact)

        return build_response(contact)


    # ========================================================
    # RESTAURATION
    # ========================================================

    @staticmethod
    async def restore_contact(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        contact_id: UUID,
        motif: str | None,
        actor: AuthContext,
        request: Request,
    ) -> ContactEntrepriseResponse:

        contact = (
            await ContactEntrepriseRepository
            .get_contact(
                db,
                entreprise_id=entreprise_id,
                contact_id=contact_id,
            )
        )

        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact introuvable.",
            )

        if (
            contact.statut or ""
        ).strip().upper() != "INACTIF":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Ce contact n'est pas désactivé."
                ),
            )

        contact.statut = "ACTIF"

        await write_audit_event(
            db,
            action="ENTREPRISE_CONTACT_RESTORE",
            categorie="DONNEES_METIER",
            resultat="SUCCES",

            utilisateur_id=actor.user.id,

            ressource_type="contact_entreprise",
            ressource_id=contact.id,

            adresse_ip=client_ip(request),

            valeurs_avant={
                "statut": "INACTIF",
            },

            valeurs_apres={
                "statut": "ACTIF",
            },

            contexte={
                "motif": clean_text(motif),
            },
        )

        await db.commit()

        await db.refresh(contact)

        return build_response(contact)