"""
Tâche hebdomadaire — résumé utilisateur.

À planifier chaque lundi.

Le résumé reste volontairement factuel :
- notifications non lues ;
- alertes actives affectées à l'utilisateur ;
- échéances actives dont il est responsable.

Il ne produit aucune décision métier.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import date, timedelta

from sqlalchemy import func, select

from app.database.session import AsyncSessionLocal
from app.models.alerte import Alerte
from app.models.echeance import Echeance
from app.models.notification import Notification
from app.models.preference_utilisateur import PreferenceUtilisateur
from app.models.utilisateur import Utilisateur
from app.repositories.account_repository import AccountRepository


async def run() -> None:
    async with AsyncSessionLocal() as db:
        users_result = await db.execute(
            select(Utilisateur)
            .join(
                PreferenceUtilisateur,
                PreferenceUtilisateur.utilisateur_id == Utilisateur.id,
            )
            .where(
                func.upper(Utilisateur.statut) == "ACTIF",
                PreferenceUtilisateur.notifications_resume_hebdomadaire.is_(True),
            )
        )
        users = list(users_result.scalars().all())

        queued = 0
        today = date.today()
        next_week = today + timedelta(days=7)

        for user in users:
            unread_result = await db.execute(
                select(func.count(Notification.id)).where(
                    Notification.destinataire_utilisateur_id == user.id,
                    Notification.date_lecture.is_(None),
                )
            )
            alerts_result = await db.execute(
                select(func.count(Alerte.id)).where(
                    Alerte.responsable_id == user.id,
                    Alerte.statut.in_(["NOUVELLE", "AFFECTEE", "EN_COURS"]),
                )
            )
            deadlines_result = await db.execute(
                select(func.count(Echeance.id)).where(
                    Echeance.responsable_id == user.id,
                    Echeance.statut.in_(["PLANIFIEE", "EN_COURS"]),
                    Echeance.date_echeance >= today,
                    Echeance.date_echeance <= next_week,
                )
            )

            unread = int(unread_result.scalar_one())
            alerts = int(alerts_result.scalar_one())
            deadlines = int(deadlines_result.scalar_one())

            body = (
                "Résumé hebdomadaire HAUQE Certif : "
                f"{unread} notification(s) non lue(s), "
                f"{alerts} alerte(s) active(s) affectée(s), "
                f"{deadlines} échéance(s) dans les 7 prochains jours."
            )

            await AccountRepository.create_notification(
                db,
                user_id=user.id,
                channel="IN_APP",
                subject="Votre résumé hebdomadaire HAUQE Certif",
                body=body,
                immediate=True,
            )
            await AccountRepository.create_notification(
                db,
                user_id=user.id,
                channel="EMAIL",
                subject="Votre résumé hebdomadaire HAUQE Certif",
                body=body,
                immediate=False,
            )
            queued += 1

        await db.commit()
        print(f"Résumés hebdomadaires préparés : {queued}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(run(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(run())
