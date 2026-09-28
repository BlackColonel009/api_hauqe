"""Communication interne lors des transitions réelles du parcours métier.

Les alertes et notifications sont créées dans la transaction de la transition.
Le worker SMTP transporte ensuite les courriels EN_ATTENTE ; il ne conditionne
jamais la réussite de l'opération métier à la disponibilité du relais.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.alerte import Alerte
from app.models.campagne import Campagne
from app.models.certification_declaree import CertificationDeclaree
from app.models.entreprise import Entreprise
from app.models.fiche_collecte import FicheCollecte
from app.models.mission_collecte import MissionCollecte
from app.models.notification import Notification
from app.models.role import Role
from app.models.utilisateur import Utilisateur
from app.models.utilisateur_role import UtilisateurRole


def application_link(route: str) -> str | None:
    value = (settings.lien_vers_sngsc or "").strip().rstrip("/")
    if not value:
        return None
    if not value.lower().startswith(("https://", "http://")):
        value = "https://" + value
    return value + route


class WorkflowCommunicationService:
    @staticmethod
    async def recipients_for_roles(db: AsyncSession, codes: set[str]) -> dict[UUID, Utilisateur]:
        if not codes:
            return {}
        today = date.today()
        rows = await db.execute(
            select(Utilisateur)
            .join(UtilisateurRole, UtilisateurRole.utilisateur_id == Utilisateur.id)
            .join(Role, Role.id == UtilisateurRole.role_id)
            .where(
                Role.code.in_(codes),
                or_(Role.statut.is_(None), func.upper(Role.statut) == "ACTIF"),
                func.upper(func.coalesce(Utilisateur.statut, "")) == "ACTIF",
                or_(UtilisateurRole.statut.is_(None), func.upper(UtilisateurRole.statut) == "ACTIF"),
                or_(UtilisateurRole.date_debut.is_(None), UtilisateurRole.date_debut <= today),
                or_(UtilisateurRole.date_fin.is_(None), UtilisateurRole.date_fin >= today),
            )
        )
        return {user.id: user for user in rows.scalars().all()}

    @staticmethod
    async def fiche_context(db: AsyncSession, fiche_id: UUID) -> tuple[str, str]:
        row = (await db.execute(
            select(FicheCollecte, MissionCollecte, Campagne, Entreprise)
            .join(MissionCollecte, MissionCollecte.id == FicheCollecte.mission_id)
            .join(Campagne, Campagne.id == MissionCollecte.campagne_id)
            .outerjoin(Entreprise, Entreprise.id == FicheCollecte.entreprise_id)
            .where(FicheCollecte.id == fiche_id)
        )).one_or_none()
        if row is None:
            return "Dossier de collecte", "Dossier de collecte concerné."
        fiche, mission, campagne, entreprise = row
        company = (entreprise.raison_sociale or entreprise.nom_commercial) if entreprise else None
        company = company or "Entreprise concernée"
        details = [
            f"Entreprise : {company}",
            f"Identifiant entreprise : {entreprise.identifiant_national}" if entreprise else None,
            f"Campagne : {campagne.nom or campagne.code}",
            f"Mission : {mission.code or mission.objet or 'Mission de collecte'}",
            f"Révision de la collecte : {fiche.numero_revision or 1}",
        ]
        certs = (await db.execute(
            select(CertificationDeclaree)
            .where(CertificationDeclaree.fiche_collecte_id == fiche_id)
            .order_by(CertificationDeclaree.created_at, CertificationDeclaree.id)
        )).scalars().all()
        for cert in certs:
            label = cert.nom_certification or cert.norme_declaree or "Certification déclarée"
            suffix = " · ".join(v for v in (cert.numero, cert.norme_declaree) if v)
            details.append(f"Certification : {label}" + (f" ({suffix})" if suffix else ""))
        return company, "\n".join(value for value in details if value)

    @staticmethod
    async def mission_context(db: AsyncSession, mission_id: UUID) -> tuple[str, str]:
        row = (await db.execute(
            select(MissionCollecte, Campagne)
            .join(Campagne, Campagne.id == MissionCollecte.campagne_id)
            .where(MissionCollecte.id == mission_id)
        )).one_or_none()
        if row is None:
            return "Mission de collecte", "Une mission de collecte vous a été attribuée."
        mission, campagne = row
        title = mission.code or mission.objet or "Mission de collecte"
        return title, "\n".join([
            f"Campagne : {campagne.nom or campagne.code}",
            f"Mission : {title}",
            f"Objet : {mission.objet or 'Non précisé'}",
            f"Période prévue : {mission.date_debut_prevue or 'À définir'} au {mission.date_fin_prevue or 'À définir'}",
        ])

    @staticmethod
    async def emit(
        db: AsyncSession,
        *,
        event: str,
        resource_type: str,
        resource_id: UUID,
        title: str,
        context: str,
        action: str,
        route: str,
        action_roles: set[str] | None = None,
        information_roles: set[str] | None = None,
        action_user_ids: set[UUID] | None = None,
    ) -> int:
        """Une alerte par transition ; un couple IN_APP/EMAIL par destinataire actif."""
        actionable = await WorkflowCommunicationService.recipients_for_roles(db, action_roles or set())
        informed = await WorkflowCommunicationService.recipients_for_roles(db, information_roles or set())
        for user_id in action_user_ids or set():
            user = await db.get(Utilisateur, user_id)
            if user and (user.statut or "").upper() == "ACTIF":
                actionable[user.id] = user
        recipients = {**informed, **actionable}
        if not recipients:
            return 0

        # Les mutations sources interdisent déjà la répétition d'une transition
        # terminée. Un nouvel épisode après réouverture obtient un nouveau numéro.
        previous = (await db.execute(
            select(func.count(Alerte.id)).where(
                Alerte.ressource_type == resource_type,
                Alerte.ressource_id == resource_id,
                Alerte.type_alerte == event,
            )
        )).scalar_one()
        alert = Alerte(
            type_alerte=event,
            niveau=2,
            titre=title[:255],
            message=context + "\nAction attendue : " + action,
            ressource_type=resource_type,
            ressource_id=resource_id,
            responsable_id=next(iter(actionable)) if len(actionable) == 1 else None,
            date_detection=date.today(),
            regle_notification=f"PARCOURS:{event}:{previous + 1}",
            statut="NOUVELLE",
        )
        db.add(alert)
        await db.flush()
        link = application_link(route)
        for user_id, user in recipients.items():
            is_action = user_id in actionable
            subject = f"HAUQE — {title}"[:255]
            greeting = (user.prenoms or user.nom or "collègue").strip()
            body = (
                f"Bonjour {greeting},\n\n{context}\n\n"
                + (f"Action attendue : {action}" if is_action else f"Pour information : {action}")
                + (f"\n\nOuvrir le dossier dans le SNGSC : {link}" if link else "")
            )
            db.add(Notification(
                alerte_id=alert.id,
                destinataire_utilisateur_id=user_id,
                canal="IN_APP",
                objet=subject,
                contenu=body,
                date_envoi=date.today(),
                resultat="Disponible dans l'application",
                nombre_tentatives=0,
                statut="ENVOYEE",
            ))
            if user.email:
                db.add(Notification(
                    alerte_id=alert.id,
                    destinataire_utilisateur_id=user_id,
                    canal="EMAIL",
                    objet=subject,
                    contenu=body,
                    nombre_tentatives=0,
                    statut="EN_ATTENTE",
                ))
        await db.flush()
        return len(recipients)
