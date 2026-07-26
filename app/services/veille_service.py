"""
Service métier — Échéances / Alertes / Notifications / Veille.

Ce service couvre le cycle :
    échéance -> alerte -> notification -> traitement -> veille -> rapport.

SEUILS VALIDÉS
--------------
Le corpus fonctionnel valide les seuils :
- 180 jours : information ;
- 90 jours : surveillance ;
- 30 jours : urgence ;
- expiration : critique.

Le champ `alertes.niveau` étant INTEGER, le mapping technique utilisé est :
1 = Information
2 = Surveillance
3 = Urgence
4 = Critique

Le moteur tente d'abord de charger une règle publiée
`VEILLE_SEUILS_EXPIRATION` depuis `regles_metier.parametres`.
En son absence, il utilise les quatre seuils validés ci-dessus.

Ainsi, la future administration des règles n'exigera pas de réécriture
du moteur.

NOTIFICATIONS
-------------
- IN_APP : considérée disponible immédiatement dans la cloche utilisateur ;
- EMAIL/SMS/autre : créée en `EN_ATTENTE` pour un worker de transport ;
- les comptes utilisateur non ACTIF ne reçoivent pas de notification ;
- les secrets SMTP ne sont jamais stockés dans les tables métier.

Les transports externes sont séparés du domaine métier.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import re
from typing import Any
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.alerte import Alerte
from app.models.dossier_veille import DossierVeille
from app.models.echeance import Echeance
from app.models.notification import Notification
from app.models.rapport_veille import RapportVeille
from app.models.relance_veille import RelanceVeille
from app.repositories.veille_repository import WatchRepository
from app.schemas.veille import (
    AlertAssignRequest,
    AlertCreateRequest,
    AlertListResponse,
    AlertNotifyRequest,
    AlertResolveRequest,
    AlertResponse,
    AlertUpdateRequest,
    DailyScanResponse,
    DeadlineCloseRequest,
    DeadlineCreateRequest,
    DeadlineListResponse,
    DeadlineResponse,
    DeadlineUpdateRequest,
    FollowUpCreateRequest,
    FollowUpResponse,
    FollowUpResponseRequest,
    FollowUpUpdateRequest,
    NotificationListResponse,
    NotificationResponse,
    NotificationResultRequest,
    WatchCaseCloseRequest,
    WatchCaseCreateRequest,
    WatchCaseListResponse,
    WatchCaseResponse,
    WatchCaseUpdateRequest,
    WatchDashboardResponse,
    WatchReportGenerateRequest,
    WatchReportListResponse,
    WatchReportResponse,
    WatchReportValidateRequest,
)
from app.services.auth_service import AuthContext


RULE_CODE_EXPIRATION = "VEILLE_SEUILS_EXPIRATION"

DEFAULT_THRESHOLDS = [
    {
        "days": 180,
        "niveau": 1,
        "code": "INFO_180",
        "label": "Information",
    },
    {
        "days": 90,
        "niveau": 2,
        "code": "SURVEILLANCE_90",
        "label": "Surveillance",
    },
    {
        "days": 30,
        "niveau": 3,
        "code": "URGENCE_30",
        "label": "Urgence",
    },
    {
        "days": 0,
        "niveau": 4,
        "code": "CRITIQUE_EXPIRATION",
        "label": "Critique",
    },
]


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def normalize_code(value: str) -> str:
    return value.strip().upper()


def parse_iso_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} doit être au format YYYY-MM-DD.",
        ) from exc


def basic_email_is_valid(value: str) -> bool:
    """
    Validation volontairement simple pour éviter une dépendance externe.

    Le transport SMTP doit effectuer sa propre validation complémentaire.
    """
    return bool(
        re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            value.strip(),
        )
    )


def notification_response(item: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=item.id,
        alerte_id=item.alerte_id,
        destinataire_utilisateur_id=item.destinataire_utilisateur_id,
        adresse_externe=item.adresse_externe,
        canal=item.canal,
        objet=item.objet,
        contenu=item.contenu,
        date_envoi=item.date_envoi,
        date_lecture=item.date_lecture,
        resultat=item.resultat,
        nombre_tentatives=item.nombre_tentatives,
        message_erreur=item.message_erreur,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def followup_response(item: RelanceVeille) -> FollowUpResponse:
    return FollowUpResponse(
        id=item.id,
        dossier_veille_id=item.dossier_veille_id,
        destinataire=item.destinataire,
        canal=item.canal,
        objet=item.objet,
        date_envoi=item.date_envoi,
        date_echeance=item.date_echeance,
        date_reponse=item.date_reponse,
        reponse=item.reponse,
        resultat=item.resultat,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def report_response(item: RapportVeille) -> WatchReportResponse:
    return WatchReportResponse(
        id=item.id,
        type_rapport=item.type_rapport,
        periode_debut=item.periode_debut,
        periode_fin=item.periode_fin,
        nombre_certifications_suivies=item.nombre_certifications_suivies,
        nombre_alertes=item.nombre_alertes,
        nombre_renouvellements=item.nombre_renouvellements,
        delai_moyen_traitement=item.delai_moyen_traitement,
        indicateurs=item.indicateurs,
        prepare_par_id=item.prepare_par_id,
        valide_par_id=item.valide_par_id,
        date_validation=item.date_validation,
        statut=item.statut,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


class WatchService:

    # ========================================================
    # UTILITAIRES
    # ========================================================

    @staticmethod
    async def require_active_user(
        db: AsyncSession,
        user_id: UUID,
    ):
        user = await WatchRepository.get_user(db, user_id)
        if user is None:
            raise HTTPException(404, "Utilisateur introuvable.")
        if (user.statut or "").strip().upper() != "ACTIF":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="L'utilisateur destinataire/responsable n'est pas actif.",
            )
        return user

    @staticmethod
    async def get_thresholds(
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        rule = await WatchRepository.active_alert_rule(
            db,
            RULE_CODE_EXPIRATION,
        )
        if rule is None or not isinstance(rule.parametres, dict):
            return DEFAULT_THRESHOLDS

        raw = rule.parametres.get("thresholds")
        if not isinstance(raw, list):
            return DEFAULT_THRESHOLDS

        cleaned = []
        for row in raw:
            if not isinstance(row, dict):
                continue
            try:
                days = int(row["days"])
                niveau = int(row["niveau"])
                code = str(row["code"]).strip().upper()
                label = str(row.get("label") or code).strip()
            except (KeyError, TypeError, ValueError):
                continue

            if days < 0 or niveau < 1 or niveau > 4 or not code:
                continue

            cleaned.append(
                {
                    "days": days,
                    "niveau": niveau,
                    "code": code,
                    "label": label,
                }
            )

        if not cleaned:
            return DEFAULT_THRESHOLDS

        # Plus grand délai vers le plus petit pour une lecture stable.
        return sorted(cleaned, key=lambda x: x["days"], reverse=True)

    @staticmethod
    def due_threshold(
        thresholds: list[dict[str, Any]],
        days_remaining: int,
    ) -> dict[str, Any] | None:
        """
        Retourne le niveau le plus sévère atteint.

        Exemple :
        - J-170 -> seuil 180 ;
        - J-80 -> seuil 90 ;
        - J-20 -> seuil 30 ;
        - J0/J+ -> critique.
        """
        applicable = [
            row
            for row in thresholds
            if days_remaining <= int(row["days"])
        ]
        if not applicable:
            return None
        return min(applicable, key=lambda x: x["days"])

    # ========================================================
    # ÉCHÉANCES
    # ========================================================

    @staticmethod
    async def require_deadline(
        db: AsyncSession,
        deadline_id: UUID,
    ) -> Echeance:
        item = await WatchRepository.get_deadline(db, deadline_id)
        if item is None:
            raise HTTPException(404, "Échéance introuvable.")
        return item

    @staticmethod
    async def deadline_response(
        db: AsyncSession,
        item: Echeance,
    ) -> DeadlineResponse:
        alert_count = await WatchRepository.deadline_alert_count(
            db,
            item.id,
        )

        days_remaining = None
        if item.date_echeance:
            days_remaining = (item.date_echeance - date.today()).days

        return DeadlineResponse(
            id=item.id,
            ressource_type=item.ressource_type,
            ressource_id=item.ressource_id,
            type_echeance=item.type_echeance,
            titre=item.titre,
            description=item.description,
            date_echeance=item.date_echeance,
            responsable_id=item.responsable_id,
            priorite=item.priorite,
            statut=item.statut,
            jours_restants=days_remaining,
            alertes_actives_count=alert_count,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    async def list_deadlines(
        db: AsyncSession,
        **filters,
    ) -> DeadlineListResponse:
        items, total = await WatchRepository.list_deadlines(
            db,
            **filters,
        )
        return DeadlineListResponse(
            total=total,
            limit=filters["limit"],
            offset=filters["offset"],
            items=[
                await WatchService.deadline_response(db, item)
                for item in items
            ],
        )

    @staticmethod
    async def create_deadline(
        db: AsyncSession,
        *,
        payload: DeadlineCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> DeadlineResponse:
        if payload.responsable_id:
            await WatchService.require_active_user(
                db,
                payload.responsable_id,
            )

        resource_type = normalize_code(payload.ressource_type)
        deadline_type = normalize_code(payload.type_echeance)

        duplicate = await WatchRepository.find_active_deadline(
            db,
            ressource_type=resource_type,
            ressource_id=payload.ressource_id,
            type_echeance=deadline_type,
            due_date=payload.date_echeance,
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Une échéance active identique existe déjà.",
            )

        item = Echeance(
            ressource_type=resource_type,
            ressource_id=payload.ressource_id,
            type_echeance=deadline_type,
            titre=payload.titre.strip(),
            description=clean_text(payload.description),
            date_echeance=payload.date_echeance,
            responsable_id=payload.responsable_id,
            priorite=clean_text(payload.priorite),
            statut="PLANIFIEE",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="WATCH_DEADLINE_CREATE",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="echeance",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "ressource_type": item.ressource_type,
                "ressource_id": str(item.ressource_id),
                "type_echeance": item.type_echeance,
                "date_echeance": item.date_echeance.isoformat(),
                "responsable_id": (
                    str(item.responsable_id)
                    if item.responsable_id else None
                ),
            },
        )

        await db.commit()
        await db.refresh(item)
        return await WatchService.deadline_response(db, item)

    @staticmethod
    async def update_deadline(
        db: AsyncSession,
        *,
        deadline_id: UUID,
        payload: DeadlineUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> DeadlineResponse:
        item = await WatchService.require_deadline(db, deadline_id)

        if item.statut in {"TERMINEE", "ANNULEE"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Une échéance terminée/annulée est verrouillée.",
            )

        changes = payload.model_dump(exclude_unset=True)

        if changes.get("responsable_id"):
            await WatchService.require_active_user(
                db,
                changes["responsable_id"],
            )

        before = {
            "titre": item.titre,
            "date_echeance": (
                item.date_echeance.isoformat()
                if item.date_echeance else None
            ),
            "responsable_id": (
                str(item.responsable_id)
                if item.responsable_id else None
            ),
            "priorite": item.priorite,
        }

        for field, value in changes.items():
            if isinstance(value, str):
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db,
            action="WATCH_DEADLINE_UPDATE",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="echeance",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant=before,
            valeurs_apres={
                "titre": item.titre,
                "date_echeance": (
                    item.date_echeance.isoformat()
                    if item.date_echeance else None
                ),
                "responsable_id": (
                    str(item.responsable_id)
                    if item.responsable_id else None
                ),
                "priorite": item.priorite,
            },
        )

        await db.commit()
        await db.refresh(item)
        return await WatchService.deadline_response(db, item)

    @staticmethod
    async def close_deadline(
        db: AsyncSession,
        *,
        deadline_id: UUID,
        target_status: str,
        payload: DeadlineCloseRequest,
        actor: AuthContext,
        request: Request,
    ) -> DeadlineResponse:
        item = await WatchService.require_deadline(db, deadline_id)

        if item.statut in {"TERMINEE", "ANNULEE"}:
            return await WatchService.deadline_response(db, item)

        item.statut = target_status

        await write_audit_event(
            db,
            action=(
                "WATCH_DEADLINE_COMPLETE"
                if target_status == "TERMINEE"
                else "WATCH_DEADLINE_CANCEL"
            ),
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="echeance",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={"statut": item.statut},
            contexte={"motif": payload.motif.strip()},
        )

        await db.commit()
        await db.refresh(item)
        return await WatchService.deadline_response(db, item)

    # ========================================================
    # ALERTES
    # ========================================================

    @staticmethod
    async def require_alert(
        db: AsyncSession,
        alert_id: UUID,
    ) -> Alerte:
        item = await WatchRepository.get_alert(db, alert_id)
        if item is None:
            raise HTTPException(404, "Alerte introuvable.")
        return item

    @staticmethod
    async def alert_response(
        db: AsyncSession,
        item: Alerte,
    ) -> AlertResponse:
        total, unread = await WatchRepository.alert_notification_counts(
            db,
            item.id,
        )
        return AlertResponse(
            id=item.id,
            echeance_id=item.echeance_id,
            type_alerte=item.type_alerte,
            niveau=item.niveau,
            titre=item.titre,
            message=item.message,
            ressource_type=item.ressource_type,
            ressource_id=item.ressource_id,
            responsable_id=item.responsable_id,
            date_detection=item.date_detection,
            date_resolution=item.date_resolution,
            regle_notification=item.regle_notification,
            statut=item.statut,
            notifications_count=total,
            notifications_non_lues_count=unread,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    async def list_alerts(
        db: AsyncSession,
        **filters,
    ) -> AlertListResponse:
        items, total = await WatchRepository.list_alerts(
            db,
            **filters,
        )
        return AlertListResponse(
            total=total,
            limit=filters["limit"],
            offset=filters["offset"],
            items=[
                await WatchService.alert_response(db, item)
                for item in items
            ],
        )

    @staticmethod
    async def create_alert(
        db: AsyncSession,
        *,
        payload: AlertCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> AlertResponse:
        if payload.responsable_id:
            await WatchService.require_active_user(
                db,
                payload.responsable_id,
            )

        if payload.echeance_id:
            deadline = await WatchService.require_deadline(
                db,
                payload.echeance_id,
            )
            if (
                deadline.ressource_type != normalize_code(payload.ressource_type)
                or deadline.ressource_id != payload.ressource_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "L'échéance ne correspond pas à la ressource "
                        "de l'alerte."
                    ),
                )

        rule_code = (
            normalize_code(payload.regle_notification)
            if payload.regle_notification else None
        )

        if payload.echeance_id and rule_code:
            duplicate = await WatchRepository.find_active_alert_for_rule(
                db,
                deadline_id=payload.echeance_id,
                rule_code=rule_code,
            )
            if duplicate:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Une alerte active existe déjà pour cette règle "
                        "et cette échéance."
                    ),
                )

        item = Alerte(
            echeance_id=payload.echeance_id,
            type_alerte=normalize_code(payload.type_alerte),
            niveau=payload.niveau,
            titre=payload.titre.strip(),
            message=payload.message.strip(),
            ressource_type=normalize_code(payload.ressource_type),
            ressource_id=payload.ressource_id,
            responsable_id=payload.responsable_id,
            date_detection=date.today(),
            date_resolution=None,
            regle_notification=rule_code,
            statut="NOUVELLE",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="WATCH_ALERT_CREATE",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="alerte",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "type_alerte": item.type_alerte,
                "niveau": item.niveau,
                "ressource_type": item.ressource_type,
                "ressource_id": str(item.ressource_id),
                "regle_notification": item.regle_notification,
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return await WatchService.alert_response(db, item)

    @staticmethod
    async def assign_alert(
        db: AsyncSession,
        *,
        alert_id: UUID,
        payload: AlertAssignRequest,
        actor: AuthContext,
        request: Request,
    ) -> AlertResponse:
        item = await WatchService.require_alert(db, alert_id)

        if item.statut in {"RESOLUE", "CLOTUREE"}:
            raise HTTPException(409, "Une alerte clôturée ne peut pas être affectée.")

        await WatchService.require_active_user(
            db,
            payload.responsable_id,
        )

        old_responsible = item.responsable_id
        item.responsable_id = payload.responsable_id
        item.statut = "AFFECTEE"

        await write_audit_event(
            db,
            action="WATCH_ALERT_ASSIGN",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="alerte",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_avant={
                "responsable_id": (
                    str(old_responsible)
                    if old_responsible else None
                )
            },
            valeurs_apres={
                "responsable_id": str(item.responsable_id),
                "statut": item.statut,
            },
            contexte={"commentaire": clean_text(payload.commentaire)},
        )

        await db.commit()
        await db.refresh(item)
        return await WatchService.alert_response(db, item)

    @staticmethod
    async def update_alert(
        db: AsyncSession,
        *,
        alert_id: UUID,
        payload: AlertUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> AlertResponse:
        item = await WatchService.require_alert(db, alert_id)

        if item.statut in {"RESOLUE", "CLOTUREE"}:
            raise HTTPException(409, "Une alerte résolue/clôturée est verrouillée.")

        changes = payload.model_dump(exclude_unset=True)

        if changes.get("responsable_id"):
            await WatchService.require_active_user(
                db,
                changes["responsable_id"],
            )

        for field, value in changes.items():
            if isinstance(value, str):
                value = clean_text(value)
            setattr(item, field, value)

        if item.statut == "NOUVELLE":
            item.statut = "EN_COURS"

        await write_audit_event(
            db,
            action="WATCH_ALERT_UPDATE",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="alerte",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "niveau": item.niveau,
                "responsable_id": (
                    str(item.responsable_id)
                    if item.responsable_id else None
                ),
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return await WatchService.alert_response(db, item)

    @staticmethod
    async def resolve_alert(
        db: AsyncSession,
        *,
        alert_id: UUID,
        payload: AlertResolveRequest,
        actor: AuthContext,
        request: Request,
    ) -> AlertResponse:
        item = await WatchService.require_alert(db, alert_id)

        if item.date_resolution is not None:
            return await WatchService.alert_response(db, item)

        item.date_resolution = date.today()
        item.statut = "CLOTUREE" if payload.cloturer else "RESOLUE"

        await write_audit_event(
            db,
            action="WATCH_ALERT_RESOLVE",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="alerte",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "date_resolution": item.date_resolution.isoformat(),
                "statut": item.statut,
            },
            contexte={"resolution": payload.resolution.strip()},
        )

        await db.commit()
        await db.refresh(item)
        return await WatchService.alert_response(db, item)

    # ========================================================
    # NOTIFICATIONS
    # ========================================================

    @staticmethod
    async def queue_alert_notifications(
        db: AsyncSession,
        *,
        alert_id: UUID,
        payload: AlertNotifyRequest,
        actor: AuthContext,
        request: Request,
    ) -> list[NotificationResponse]:
        alert = await WatchService.require_alert(db, alert_id)
        created: list[Notification] = []

        for recipient in payload.destinataires:
            user_id = recipient.destinataire_utilisateur_id
            external = clean_text(recipient.adresse_externe)
            channel = normalize_code(recipient.canal)

            if bool(user_id) == bool(external):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Chaque destinataire doit avoir soit un utilisateur, "
                        "soit une adresse externe, mais pas les deux."
                    ),
                )

            user = None
            if user_id:
                user = await WatchService.require_active_user(db, user_id)

            if channel == "IN_APP" and user_id is None:
                raise HTTPException(
                    422,
                    "Une notification IN_APP exige un utilisateur interne.",
                )

            if external and channel == "EMAIL" and not basic_email_is_valid(external):
                raise HTTPException(
                    422,
                    f"Adresse email externe invalide : {external}",
                )

            # Pour EMAIL vers utilisateur interne, le worker utilisera user.email.
            immediate = channel == "IN_APP"

            item = Notification(
                alerte_id=alert.id,
                destinataire_utilisateur_id=user_id,
                adresse_externe=external,
                canal=channel,
                objet=payload.objet.strip(),
                contenu=payload.contenu.strip(),
                date_envoi=date.today() if immediate else None,
                date_lecture=None,
                resultat=(
                    "Disponible dans l'application"
                    if immediate else None
                ),
                nombre_tentatives=0,
                message_erreur=None,
                statut="ENVOYEE" if immediate else "EN_ATTENTE",
            )
            db.add(item)
            await db.flush()
            created.append(item)

        await write_audit_event(
            db,
            action="WATCH_NOTIFICATION_QUEUE",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="alerte",
            ressource_id=alert.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "notifications_creees": len(created),
                "destinataires": [
                    {
                        "utilisateur_id": (
                            str(x.destinataire_utilisateur_id)
                            if x.destinataire_utilisateur_id else None
                        ),
                        "adresse_externe": x.adresse_externe,
                        "canal": x.canal,
                        "statut": x.statut,
                    }
                    for x in created
                ],
            },
        )

        await db.commit()
        for item in created:
            await db.refresh(item)

        return [notification_response(x) for x in created]

    @staticmethod
    async def list_my_notifications(
        db: AsyncSession,
        *,
        actor: AuthContext,
        statut_filter: str | None,
        unread_only: bool,
        limit: int,
        offset: int,
    ) -> NotificationListResponse:
        items, total, unread_count = await WatchRepository.list_notifications(
            db,
            current_user_id=actor.user.id,
            statut=statut_filter,
            unread_only=unread_only,
            limit=limit,
            offset=offset,
        )
        return NotificationListResponse(
            total=total,
            unread_count=unread_count,
            limit=limit,
            offset=offset,
            items=[notification_response(x) for x in items],
        )

    @staticmethod
    async def mark_notification_read(
        db: AsyncSession,
        *,
        notification_id: UUID,
        actor: AuthContext,
        request: Request,
    ) -> NotificationResponse:
        item = await WatchRepository.get_notification(
            db,
            notification_id,
        )
        if item is None:
            raise HTTPException(404, "Notification introuvable.")

        if item.destinataire_utilisateur_id != actor.user.id:
            raise HTTPException(403, "Cette notification ne vous appartient pas.")

        if item.date_lecture is None:
            item.date_lecture = date.today()

            await write_audit_event(
                db,
                action="WATCH_NOTIFICATION_READ",
                categorie="VEILLE",
                resultat="SUCCES",
                utilisateur_id=actor.user.id,
                ressource_type="notification",
                ressource_id=item.id,
                adresse_ip=client_ip(request),
            )

            await db.commit()
            await db.refresh(item)

        return notification_response(item)

    @staticmethod
    async def mark_all_notifications_read(
        db: AsyncSession,
        *,
        actor: AuthContext,
        request: Request,
    ) -> int:
        rows = await WatchRepository.unread_notification_rows(
            db,
            actor.user.id,
        )
        today = date.today()
        for item in rows:
            item.date_lecture = today

        if rows:
            await write_audit_event(
                db,
                action="WATCH_NOTIFICATION_READ_ALL",
                categorie="VEILLE",
                resultat="SUCCES",
                utilisateur_id=actor.user.id,
                ressource_type="notification",
                adresse_ip=client_ip(request),
                valeurs_apres={"nombre": len(rows)},
            )
            await db.commit()

        return len(rows)

    @staticmethod
    async def retry_notification(
        db: AsyncSession,
        *,
        notification_id: UUID,
        actor: AuthContext,
        request: Request,
    ) -> NotificationResponse:
        item = await WatchRepository.get_notification(
            db,
            notification_id,
        )
        if item is None:
            raise HTTPException(404, "Notification introuvable.")

        if normalize_code(item.canal or "") == "IN_APP":
            raise HTTPException(409, "Une notification IN_APP n'a pas de transport à retenter.")

        if item.statut == "ENVOYEE":
            raise HTTPException(409, "Notification déjà envoyée.")

        item.statut = "EN_ATTENTE"
        item.message_erreur = None

        await write_audit_event(
            db,
            action="WATCH_NOTIFICATION_RETRY",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="notification",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
        )

        await db.commit()
        await db.refresh(item)
        return notification_response(item)

    @staticmethod
    async def record_notification_delivery(
        db: AsyncSession,
        *,
        notification_id: UUID,
        payload: NotificationResultRequest,
        actor: AuthContext | None,
        request: Request | None,
    ) -> NotificationResponse:
        """
        Utilisé par un worker/administrateur de transport.

        `nombre_tentatives` est incrémenté ici, quelle que soit l'issue.
        """
        item = await WatchRepository.get_notification(
            db,
            notification_id,
        )
        if item is None:
            raise HTTPException(404, "Notification introuvable.")

        item.nombre_tentatives = int(item.nombre_tentatives or 0) + 1

        if payload.success:
            item.date_envoi = date.today()
            item.resultat = clean_text(payload.resultat) or "ENVOYEE"
            item.message_erreur = None
            item.statut = "ENVOYEE"
        else:
            item.resultat = clean_text(payload.resultat) or "ECHEC"
            item.message_erreur = (
                clean_text(payload.message_erreur)
                or "Échec de transport sans détail."
            )
            item.statut = "ECHEC"

        await write_audit_event(
            db,
            action="WATCH_NOTIFICATION_DELIVERY_RESULT",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id if actor else None,
            ressource_type="notification",
            ressource_id=item.id,
            adresse_ip=client_ip(request) if request else None,
            valeurs_apres={
                "statut": item.statut,
                "nombre_tentatives": item.nombre_tentatives,
                "message_erreur": item.message_erreur,
            },
        )

        await db.commit()
        await db.refresh(item)
        return notification_response(item)

    # ========================================================
    # SCAN QUOTIDIEN
    # ========================================================

    @staticmethod
    async def ensure_generated_deadline(
        db: AsyncSession,
        *,
        resource_type: str,
        resource_id: UUID,
        deadline_type: str,
        title: str,
        due_date: date,
    ) -> tuple[Echeance, bool]:
        existing = await WatchRepository.find_active_deadline(
            db,
            ressource_type=resource_type,
            ressource_id=resource_id,
            type_echeance=deadline_type,
            due_date=due_date,
        )
        if existing:
            return existing, False

        item = Echeance(
            ressource_type=resource_type,
            ressource_id=resource_id,
            type_echeance=deadline_type,
            titre=title,
            description="Échéance générée par le moteur de veille.",
            date_echeance=due_date,
            responsable_id=None,
            priorite=None,
            statut="PLANIFIEE",
        )
        db.add(item)
        await db.flush()
        return item, True

    @staticmethod
    async def ensure_threshold_alert(
        db: AsyncSession,
        *,
        deadline: Echeance,
        threshold: dict[str, Any],
    ) -> bool:
        rule_code = (
            f"{RULE_CODE_EXPIRATION}:"
            f"{deadline.type_echeance}:"
            f"{threshold['code']}"
        )

        existing = await WatchRepository.find_active_alert_for_rule(
            db,
            deadline_id=deadline.id,
            rule_code=rule_code,
        )
        if existing:
            return False

        days_remaining = (
            deadline.date_echeance - date.today()
        ).days

        item = Alerte(
            echeance_id=deadline.id,
            type_alerte="ECHEANCE",
            niveau=int(threshold["niveau"]),
            titre=f"{threshold['label']} — {deadline.titre}",
            message=(
                f"Échéance {deadline.type_echeance} au "
                f"{deadline.date_echeance.isoformat()} "
                f"({days_remaining} jour(s))."
            ),
            ressource_type=deadline.ressource_type,
            ressource_id=deadline.ressource_id,
            responsable_id=deadline.responsable_id,
            date_detection=date.today(),
            date_resolution=None,
            regle_notification=rule_code,
            statut="NOUVELLE",
        )
        db.add(item)
        await db.flush()
        return True

    @staticmethod
    async def run_daily_scan(
        db: AsyncSession,
        *,
        actor: AuthContext | None,
        request: Request | None,
    ) -> DailyScanResponse:
        thresholds = await WatchService.get_thresholds(db)

        created_deadlines = 0
        created_alerts = 0

        certifications = await WatchRepository.certifications_with_expiration(db)
        audits = await WatchRepository.audits_with_due_date(db)
        renewals = await WatchRepository.renewals_with_due_date(db)

        sources: list[tuple[str, UUID, str, str, date]] = []

        for cert in certifications:
            sources.append(
                (
                    "CERTIFICATION",
                    cert.id,
                    "EXPIRATION_CERTIFICATION",
                    (
                        f"Expiration certification "
                        f"{cert.identifiant_national or cert.numero_certificat or cert.id}"
                    ),
                    cert.date_expiration,
                )
            )

        for audit in audits:
            sources.append(
                (
                    "AUDIT_CERTIFICATION",
                    audit.id,
                    "AUDIT_CERTIFICATION",
                    f"Audit de certification {audit.type_audit or audit.id}",
                    audit.date_prevue,
                )
            )

        for renewal in renewals:
            sources.append(
                (
                    "RENOUVELLEMENT_CERTIFICATION",
                    renewal.id,
                    "RENOUVELLEMENT_CERTIFICATION",
                    f"Renouvellement de certification {renewal.certification_id}",
                    renewal.date_limite,
                )
            )

        for (
            resource_type,
            resource_id,
            deadline_type,
            title,
            due_date,
        ) in sources:
            deadline, was_created = (
                await WatchService.ensure_generated_deadline(
                    db,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    deadline_type=deadline_type,
                    title=title,
                    due_date=due_date,
                )
            )
            if was_created:
                created_deadlines += 1

            days_remaining = (due_date - date.today()).days
            threshold = WatchService.due_threshold(
                thresholds,
                days_remaining,
            )
            if threshold:
                if await WatchService.ensure_threshold_alert(
                    db,
                    deadline=deadline,
                    threshold=threshold,
                ):
                    created_alerts += 1

        await write_audit_event(
            db,
            action="WATCH_DAILY_SCAN",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id if actor else None,
            ressource_type="veille_scan",
            adresse_ip=client_ip(request) if request else None,
            valeurs_apres={
                "date": date.today().isoformat(),
                "deadlines_created": created_deadlines,
                "alerts_created": created_alerts,
                "certifications_seen": len(certifications),
                "audits_seen": len(audits),
                "renewals_seen": len(renewals),
            },
        )

        await db.commit()

        return DailyScanResponse(
            scan_date=date.today(),
            deadlines_created=created_deadlines,
            alerts_created=created_alerts,
            certification_deadlines_seen=len(certifications),
            audit_deadlines_seen=len(audits),
            renewal_deadlines_seen=len(renewals),
        )

    # ========================================================
    # DOSSIERS DE VEILLE
    # ========================================================

    @staticmethod
    async def require_watch_case(
        db: AsyncSession,
        case_id: UUID,
    ) -> DossierVeille:
        item = await WatchRepository.get_watch_case(db, case_id)
        if item is None:
            raise HTTPException(404, "Dossier de veille introuvable.")
        return item

    @staticmethod
    async def watch_case_response(
        db: AsyncSession,
        item: DossierVeille,
    ) -> WatchCaseResponse:
        total, pending = await WatchRepository.watch_case_followup_counts(
            db,
            item.id,
        )
        return WatchCaseResponse(
            id=item.id,
            certification_id=item.certification_id,
            type_evenement=item.type_evenement,
            priorite=item.priorite,
            date_ouverture=item.date_ouverture,
            responsable_id=item.responsable_id,
            prochaine_action_at=item.prochaine_action_at,
            date_cloture=item.date_cloture,
            statut=item.statut,
            relances_count=total,
            relances_en_attente_count=pending,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    async def list_watch_cases(
        db: AsyncSession,
        **filters,
    ) -> WatchCaseListResponse:
        items, total = await WatchRepository.list_watch_cases(
            db,
            **filters,
        )
        return WatchCaseListResponse(
            total=total,
            limit=filters["limit"],
            offset=filters["offset"],
            items=[
                await WatchService.watch_case_response(db, item)
                for item in items
            ],
        )

    @staticmethod
    async def create_watch_case(
        db: AsyncSession,
        *,
        payload: WatchCaseCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> WatchCaseResponse:
        certification = await WatchRepository.get_certification(
            db,
            payload.certification_id,
        )
        if certification is None:
            raise HTTPException(404, "Certification introuvable.")

        await WatchService.require_active_user(
            db,
            payload.responsable_id,
        )

        event_type = normalize_code(payload.type_evenement)
        duplicate = await WatchRepository.active_watch_case(
            db,
            certification_id=payload.certification_id,
            event_type=event_type,
        )
        if duplicate:
            raise HTTPException(
                409,
                "Un dossier de veille actif existe déjà pour cet événement.",
            )

        item = DossierVeille(
            certification_id=payload.certification_id,
            type_evenement=event_type,
            priorite=clean_text(payload.priorite),
            date_ouverture=date.today(),
            responsable_id=payload.responsable_id,
            prochaine_action_at=payload.prochaine_action_at,
            date_cloture=None,
            statut="OUVERT",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="WATCH_CASE_OPEN",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="dossier_veille",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "certification_id": str(item.certification_id),
                "type_evenement": item.type_evenement,
                "responsable_id": str(item.responsable_id),
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return await WatchService.watch_case_response(db, item)

    @staticmethod
    async def update_watch_case(
        db: AsyncSession,
        *,
        case_id: UUID,
        payload: WatchCaseUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> WatchCaseResponse:
        item = await WatchService.require_watch_case(db, case_id)

        if item.date_cloture is not None:
            raise HTTPException(409, "Dossier de veille clôturé.")

        changes = payload.model_dump(exclude_unset=True)

        if changes.get("responsable_id"):
            await WatchService.require_active_user(
                db,
                changes["responsable_id"],
            )

        for field, value in changes.items():
            if field == "type_evenement" and value:
                value = normalize_code(value)
            elif isinstance(value, str):
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db,
            action="WATCH_CASE_UPDATE",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="dossier_veille",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "priorite": item.priorite,
                "responsable_id": str(item.responsable_id),
                "prochaine_action_at": (
                    item.prochaine_action_at.isoformat()
                    if item.prochaine_action_at else None
                ),
            },
        )

        await db.commit()
        await db.refresh(item)
        return await WatchService.watch_case_response(db, item)

    @staticmethod
    async def close_watch_case(
        db: AsyncSession,
        *,
        case_id: UUID,
        payload: WatchCaseCloseRequest,
        actor: AuthContext,
        request: Request,
    ) -> WatchCaseResponse:
        item = await WatchService.require_watch_case(db, case_id)

        if item.date_cloture is not None:
            return await WatchService.watch_case_response(db, item)

        item.date_cloture = date.today()
        item.statut = "CLOTURE"

        await write_audit_event(
            db,
            action="WATCH_CASE_CLOSE",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="dossier_veille",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "date_cloture": item.date_cloture.isoformat(),
                "statut": item.statut,
            },
            contexte={"motif": payload.motif.strip()},
        )

        await db.commit()
        await db.refresh(item)
        return await WatchService.watch_case_response(db, item)

    # ========================================================
    # RELANCES
    # ========================================================

    @staticmethod
    async def list_followups(
        db: AsyncSession,
        case_id: UUID,
    ) -> list[FollowUpResponse]:
        await WatchService.require_watch_case(db, case_id)
        return [
            followup_response(x)
            for x in await WatchRepository.list_followups(db, case_id)
        ]

    @staticmethod
    async def create_followup(
        db: AsyncSession,
        *,
        case_id: UUID,
        payload: FollowUpCreateRequest,
        actor: AuthContext,
        request: Request,
    ) -> FollowUpResponse:
        case = await WatchService.require_watch_case(db, case_id)
        if case.date_cloture is not None:
            raise HTTPException(409, "Dossier de veille clôturé.")

        sent = payload.date_envoi or date.today()
        if payload.date_echeance and payload.date_echeance < sent:
            raise HTTPException(
                422,
                "La date d'échéance de relance précède la date d'envoi.",
            )

        item = RelanceVeille(
            dossier_veille_id=case_id,
            destinataire=payload.destinataire.strip(),
            canal=normalize_code(payload.canal),
            objet=payload.objet.strip(),
            date_envoi=sent,
            date_echeance=payload.date_echeance,
            date_reponse=None,
            reponse=None,
            resultat=None,
            statut="EN_ATTENTE",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="WATCH_FOLLOWUP_CREATE",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="relance_veille",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "dossier_veille_id": str(case_id),
                "destinataire": item.destinataire,
                "canal": item.canal,
                "date_echeance": (
                    item.date_echeance.isoformat()
                    if item.date_echeance else None
                ),
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return followup_response(item)

    @staticmethod
    async def update_followup(
        db: AsyncSession,
        *,
        case_id: UUID,
        followup_id: UUID,
        payload: FollowUpUpdateRequest,
        actor: AuthContext,
        request: Request,
    ) -> FollowUpResponse:
        item = await WatchRepository.get_followup(
            db,
            case_id=case_id,
            followup_id=followup_id,
        )
        if item is None:
            raise HTTPException(404, "Relance introuvable.")

        if item.date_reponse is not None:
            raise HTTPException(409, "Une relance ayant reçu une réponse est verrouillée.")

        changes = payload.model_dump(exclude_unset=True)
        sent = changes.get("date_envoi", item.date_envoi)
        due = changes.get("date_echeance", item.date_echeance)
        if sent and due and due < sent:
            raise HTTPException(422, "Période de relance incohérente.")

        for field, value in changes.items():
            if field == "canal" and value:
                value = normalize_code(value)
            elif isinstance(value, str):
                value = clean_text(value)
            setattr(item, field, value)

        await write_audit_event(
            db,
            action="WATCH_FOLLOWUP_UPDATE",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="relance_veille",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
        )

        await db.commit()
        await db.refresh(item)
        return followup_response(item)

    @staticmethod
    async def record_followup_response(
        db: AsyncSession,
        *,
        case_id: UUID,
        followup_id: UUID,
        payload: FollowUpResponseRequest,
        actor: AuthContext,
        request: Request,
    ) -> FollowUpResponse:
        item = await WatchRepository.get_followup(
            db,
            case_id=case_id,
            followup_id=followup_id,
        )
        if item is None:
            raise HTTPException(404, "Relance introuvable.")

        item.date_reponse = payload.date_reponse or date.today()
        item.reponse = payload.reponse.strip()
        item.resultat = clean_text(payload.resultat)
        item.statut = "REPONDU"

        await write_audit_event(
            db,
            action="WATCH_FOLLOWUP_RESPONSE",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="relance_veille",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "date_reponse": item.date_reponse.isoformat(),
                "resultat": item.resultat,
                "statut": item.statut,
            },
        )

        await db.commit()
        await db.refresh(item)
        return followup_response(item)

    # ========================================================
    # RAPPORTS DE VEILLE
    # ========================================================

    @staticmethod
    async def require_watch_report(
        db: AsyncSession,
        report_id: UUID,
    ) -> RapportVeille:
        item = await WatchRepository.get_watch_report(db, report_id)
        if item is None:
            raise HTTPException(404, "Rapport de veille introuvable.")
        return item

    @staticmethod
    async def list_reports(
        db: AsyncSession,
        *,
        type_rapport: str | None,
        statut_filter: str | None,
        limit: int,
        offset: int,
    ) -> WatchReportListResponse:
        items, total = await WatchRepository.list_watch_reports(
            db,
            type_rapport=type_rapport,
            statut=statut_filter,
            limit=limit,
            offset=offset,
        )
        return WatchReportListResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=[report_response(x) for x in items],
        )

    @staticmethod
    async def generate_report(
        db: AsyncSession,
        *,
        payload: WatchReportGenerateRequest,
        actor: AuthContext,
        request: Request,
    ) -> WatchReportResponse:
        start = parse_iso_date(
            payload.periode_debut,
            "periode_debut",
        )
        end = parse_iso_date(
            payload.periode_fin,
            "periode_fin",
        )
        if end < start:
            raise HTTPException(422, "Période de rapport incohérente.")

        cases = await WatchRepository.watch_cases_in_period(
            db,
            start,
            end,
        )
        alerts = await WatchRepository.alerts_in_period(
            db,
            start,
            end,
        )
        renewals = await WatchRepository.renewals_in_period(
            db,
            start,
            end,
        )

        certification_ids = {
            case.certification_id
            for case in cases
        }

        treatment_delays = []
        for alert in alerts:
            if alert.date_detection and alert.date_resolution:
                treatment_delays.append(
                    Decimal(
                        (alert.date_resolution - alert.date_detection).days
                    )
                )

        average_delay = None
        if treatment_delays:
            average_delay = (
                sum(treatment_delays, Decimal("0"))
                / Decimal(len(treatment_delays))
            ).quantize(Decimal("0.0001"))

        active_alerts = sum(
            1
            for alert in alerts
            if alert.statut in {"NOUVELLE", "AFFECTEE", "EN_COURS"}
        )
        critical_alerts = sum(
            1
            for alert in alerts
            if alert.niveau == 4
        )
        resolved_alerts = sum(
            1
            for alert in alerts
            if alert.date_resolution is not None
        )
        pending_cases = sum(
            1
            for case in cases
            if case.date_cloture is None
        )

        indicators = {
            "periode": {
                "debut": start.isoformat(),
                "fin": end.isoformat(),
            },
            "alertes_actives": active_alerts,
            "alertes_critiques": critical_alerts,
            "alertes_resolues": resolved_alerts,
            "dossiers_veille_ouverts": pending_cases,
            "certifications_distinctes_suivies": len(certification_ids),
        }

        item = RapportVeille(
            type_rapport=normalize_code(payload.type_rapport),
            periode_debut=start.isoformat(),
            periode_fin=end.isoformat(),
            nombre_certifications_suivies=len(certification_ids),
            nombre_alertes=len(alerts),
            nombre_renouvellements=len(renewals),
            delai_moyen_traitement=average_delay,
            indicateurs=indicators,
            prepare_par_id=actor.user.id,
            valide_par_id=None,
            date_validation=None,
            statut="BROUILLON",
        )
        db.add(item)
        await db.flush()

        await write_audit_event(
            db,
            action="WATCH_REPORT_GENERATE",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="rapport_veille",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "type_rapport": item.type_rapport,
                "periode_debut": item.periode_debut,
                "periode_fin": item.periode_fin,
                "nombre_certifications_suivies": (
                    item.nombre_certifications_suivies
                ),
                "nombre_alertes": item.nombre_alertes,
                "nombre_renouvellements": item.nombre_renouvellements,
            },
        )

        await db.commit()
        await db.refresh(item)
        return report_response(item)

    @staticmethod
    async def validate_report(
        db: AsyncSession,
        *,
        report_id: UUID,
        payload: WatchReportValidateRequest,
        actor: AuthContext,
        request: Request,
    ) -> WatchReportResponse:
        item = await WatchService.require_watch_report(
            db,
            report_id,
        )

        if item.statut == "VALIDE":
            return report_response(item)

        item.valide_par_id = actor.user.id
        item.date_validation = date.today()
        item.statut = "VALIDE"

        await write_audit_event(
            db,
            action="WATCH_REPORT_VALIDATE",
            categorie="VEILLE",
            resultat="SUCCES",
            utilisateur_id=actor.user.id,
            ressource_type="rapport_veille",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            valeurs_apres={
                "valide_par_id": str(item.valide_par_id),
                "date_validation": item.date_validation.isoformat(),
                "statut": item.statut,
            },
            contexte={
                "commentaire": clean_text(payload.commentaire)
            },
        )

        await db.commit()
        await db.refresh(item)
        return report_response(item)

    # ========================================================
    # DASHBOARD
    # ========================================================

    @staticmethod
    async def dashboard(
        db: AsyncSession,
        actor: AuthContext,
    ) -> WatchDashboardResponse:
        (
            open_cases,
            overdue,
            active_alerts,
            critical,
            pending_followups,
            unread,
        ) = await WatchRepository.dashboard_counts(
            db,
            actor.user.id,
        )

        return WatchDashboardResponse(
            open_watch_cases=open_cases,
            overdue_deadlines=overdue,
            active_alerts=active_alerts,
            critical_alerts=critical,
            pending_followups=pending_followups,
            unread_notifications=unread,
        )
