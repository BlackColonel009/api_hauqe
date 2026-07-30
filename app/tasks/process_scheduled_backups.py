"""Planificateur serveur des politiques de sauvegarde actives."""
from __future__ import annotations
import asyncio
import logging
from datetime import date
from sqlalchemy import select
from app.config.logging import configure_logging
from app.database.session import AsyncSessionLocal
from app.models.sauvegarde import Sauvegarde
from app.tasks.process_backup import execute_backup_run

logger = logging.getLogger(__name__)
configure_logging()

def due_today(frequency: str | None) -> bool:
    code=(frequency or "").upper(); today=date.today()
    return code=="QUOTIDIENNE" or (code=="HEBDOMADAIRE" and today.weekday()==6) or (code=="MENSUELLE" and today.day==1)

async def run():
    ids=[]
    async with AsyncSessionLocal() as db:
        policies=list((await db.scalars(select(Sauvegarde).where(Sauvegarde.type_enregistrement=="POLITIQUE",Sauvegarde.statut=="ACTIVE"))).all())
        for policy in policies:
            if not due_today(policy.frequence): continue
            existing=await db.scalar(select(Sauvegarde.id).where(Sauvegarde.parent_id==policy.id,Sauvegarde.date_debut==date.today(),Sauvegarde.type_enregistrement=="EXECUTION"))
            if existing: continue
            item=Sauvegarde(type_enregistrement="EXECUTION",parent_id=policy.id,frequence=policy.frequence,retention=policy.retention,perimetre=policy.perimetre,emplacement_stockage=policy.emplacement_stockage,date_debut=date.today(),statut="EN_COURS",resultat="0|Planification automatique")
            db.add(item); await db.flush(); ids.append(item.id)
        await db.commit()
    for run_id in ids: await execute_backup_run(run_id)
    logger.info("Sauvegardes automatiques exécutées : %s", len(ids))

if __name__=="__main__": asyncio.run(run())
