"""Seed idempotent des permissions Vérification + FUCCS.

Aucune modification de schéma.
Les droits restent ensuite administrables via l'API RBAC existante.
"""
from __future__ import annotations
import asyncio, sys
from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission

PERMISSIONS = [
    ("VERIFICATION.LIRE","VERIFICATION","LIRE","Consulter les dossiers de vérification."),
    ("VERIFICATION.OUVRIR","VERIFICATION","OUVRIR","Ouvrir un dossier depuis une fiche soumise."),
    ("VERIFICATION.AFFECTER","VERIFICATION","AFFECTER","Affecter/réaffecter les vérificateurs."),
    ("VERIFICATION.VERIFIER","VERIFICATION","VERIFIER","Enregistrer les points de vérification."),
    ("VERIFICATION.SIGNALER_ANOMALIE","VERIFICATION","SIGNALER_ANOMALIE","Gérer les anomalies."),
    ("VERIFICATION.CONFIRMER","VERIFICATION","CONFIRMER","Gérer les confirmations externes."),
    ("VERIFICATION.CLOTURER","VERIFICATION","CLOTURER","Prononcer l'avis de vérification."),
    ("FUCCS.LIRE","FUCCS","LIRE","Consulter grilles et contrôles FUCCS."),
    ("FUCCS.ADMINISTRER_GRILLE","FUCCS","ADMINISTRER_GRILLE","Versionner les grilles FUCCS."),
    ("FUCCS.CONTROLER","FUCCS","CONTROLER","Réaliser un contrôle FUCCS."),
    ("FUCCS.FINALISER","FUCCS","FINALISER","Finaliser un contrôle FUCCS."),
    ("FUCCS.REOUVRIR","FUCCS","REOUVRIR","Réouvrir un contrôle finalisé."),
]

ROLE_MATRIX = {
    "DIRECTION_TECHNIQUE": {
        "VERIFICATION.LIRE","VERIFICATION.OUVRIR","VERIFICATION.AFFECTER",
        "VERIFICATION.VERIFIER","VERIFICATION.SIGNALER_ANOMALIE",
        "VERIFICATION.CONFIRMER","VERIFICATION.CLOTURER",
        "FUCCS.LIRE","FUCCS.ADMINISTRER_GRILLE","FUCCS.REOUVRIR",
    },
    "POINT_FOCAL_BNEC": {
        "VERIFICATION.LIRE","VERIFICATION.OUVRIR","VERIFICATION.AFFECTER","FUCCS.LIRE",
    },
    "VERIFICATEUR": {
        "VERIFICATION.LIRE","VERIFICATION.VERIFIER","VERIFICATION.SIGNALER_ANOMALIE",
        "VERIFICATION.CONFIRMER","VERIFICATION.CLOTURER",
    },
    "CONTROLEUR_FUCCS": {"VERIFICATION.LIRE","FUCCS.LIRE","FUCCS.CONTROLER","FUCCS.FINALISER"},
    "ADMIN_BNEC": {"VERIFICATION.LIRE","FUCCS.LIRE"},
    "LECTEUR": {"VERIFICATION.LIRE","FUCCS.LIRE"},
}

async def ensure_link(db, role_id, permission_id):
    r=await db.execute(select(RolePermission).where(
        RolePermission.role_id==role_id,RolePermission.permission_id==permission_id))
    if r.scalar_one_or_none() is None:
        db.add(RolePermission(role_id=role_id,permission_id=permission_id))

async def seed():
    async with AsyncSessionLocal() as db:
        try:
            by_code={}
            for code,domaine,action,description in PERMISSIONS:
                r=await db.execute(select(Permission).where(Permission.code==code))
                p=r.scalar_one_or_none()
                if p is None:
                    p=Permission(code=code,domaine=domaine,action=action,description=description)
                    db.add(p); await db.flush()
                by_code[code]=p

            r=await db.execute(select(Role).where(Role.code=="ADMIN_HAUQE"))
            admin=r.scalar_one_or_none()
            if admin is None: raise RuntimeError("ADMIN_HAUQE absent.")

            allp=await db.execute(select(Permission))
            for p in allp.scalars().all():
                await ensure_link(db,admin.id,p.id)

            for role_code,codes in ROLE_MATRIX.items():
                rr=await db.execute(select(Role).where(Role.code==role_code))
                role=rr.scalar_one_or_none()
                if role is None:
                    print("Rôle absent, ignoré :",role_code); continue
                for code in codes:
                    await ensure_link(db,role.id,by_code[code].id)

            await db.commit()
            print("Permissions Vérification/FUCCS synchronisées.")
        except Exception:
            await db.rollback(); raise

if __name__=="__main__":
    if sys.platform=="win32":
        asyncio.run(seed(),loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(seed())
