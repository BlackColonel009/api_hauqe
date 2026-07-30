"""Exécution persistante des sauvegardes HAUQE côté backend."""
from __future__ import annotations
import asyncio, hashlib, os, shutil, subprocess, zipfile
from datetime import date, datetime
from pathlib import Path
from urllib.parse import unquote, urlparse
from uuid import UUID
from app.audit.service import write_audit_event
from app.config.settings import settings
from app.database.session import AsyncSessionLocal
from app.models.sauvegarde import Sauvegarde

ROOT = Path(__file__).resolve().parents[2]
BACKUP_ROOT, UPLOAD_ROOT = ROOT / "backups", ROOT / "uploads"

def pg_dump_path():
    for candidate in (os.getenv("HAUQE_PG_DUMP"), shutil.which("pg_dump"), r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"):
        if candidate and Path(candidate).is_file(): return str(candidate)
    raise RuntimeError("pg_dump est introuvable sur le serveur.")

def dump_database(target):
    parsed=urlparse(settings.database_url.replace("+asyncpg","")); env=os.environ.copy(); env["PGPASSWORD"]=unquote(parsed.password or "")
    command=[pg_dump_path(),"--format=custom","--no-owner","--no-privileges","--host",parsed.hostname or "localhost","--port",str(parsed.port or 5432),"--username",unquote(parsed.username or ""),"--file",str(target),parsed.path.lstrip("/")]
    result=subprocess.run(command,env=env,capture_output=True,text=True,timeout=3600,check=False,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    if result.returncode: raise RuntimeError((result.stderr or "Échec pg_dump")[-1000:])

def archive_documents(target):
    with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,allowZip64=True) as out:
        if UPLOAD_ROOT.exists():
            for path in UPLOAD_ROOT.rglob("*"):
                if path.is_file(): out.write(path,path.relative_to(ROOT))

def checksum(path):
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""): digest.update(block)
    return digest.hexdigest()

async def progress(run_id,message):
    async with AsyncSessionLocal() as db:
        item=await db.get(Sauvegarde,run_id)
        if not item: raise RuntimeError("Exécution introuvable.")
        item.resultat=message; await db.commit(); return item

async def execute_backup_run(run_id: UUID):
    BACKUP_ROOT.mkdir(parents=True,exist_ok=True); stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
    try:
        item=await progress(run_id,"15|Préparation de la sauvegarde"); scope=(item.perimetre or "COMPLETE").strip().upper()
        dbdump=BACKUP_ROOT/f"hauqe-systeme-{stamp}.dump"; doczip=BACKUP_ROOT/f"hauqe-documents-{stamp}.zip"
        if scope in {"SYSTEME","COMPLETE"}: await progress(run_id,"26|Sauvegarde de la base"); await asyncio.to_thread(dump_database,dbdump)
        if scope in {"DOCUMENTS","COMPLETE"}: await progress(run_id,"55|Archivage des documents"); await asyncio.to_thread(archive_documents,doczip)
        if scope=="SYSTEME": final=dbdump
        elif scope=="DOCUMENTS": final=doczip
        else:
            await progress(run_id,"81|Assemblage de la sauvegarde complète"); final=BACKUP_ROOT/f"hauqe-complete-{stamp}.zip"
            with zipfile.ZipFile(final,"w",zipfile.ZIP_DEFLATED,allowZip64=True) as out: out.write(dbdump,dbdump.name); out.write(doczip,doczip.name)
            dbdump.unlink(missing_ok=True); doczip.unlink(missing_ok=True)
        proof=await asyncio.to_thread(checksum,final)
        async with AsyncSessionLocal() as db:
            run=await db.get(Sauvegarde,run_id); run.date_fin=date.today(); run.taille_octets=final.stat().st_size; run.integrite_validee=True; run.resultat=f"100|Archive créée : {final.name} · SHA-256 {proof}"; run.emplacement_stockage=str(final); run.statut="TERMINE"
            await write_audit_event(db,action="BACKUP_RUN_COMPLETE",categorie="CONTINUITE",resultat="SUCCES",utilisateur_id=None,ressource_type="sauvegarde",ressource_id=run.id,valeurs_apres={"archive":final.name,"sha256":proof}); await db.commit()
    except Exception as exc:
        async with AsyncSessionLocal() as db:
            run=await db.get(Sauvegarde,run_id)
            if run:
                run.date_fin=date.today(); run.integrite_validee=False; run.message_erreur=str(exc)[:255]; run.resultat="0|Échec de la sauvegarde"; run.statut="ECHEC"
                await write_audit_event(db,action="BACKUP_RUN_FAIL",categorie="CONTINUITE",resultat="ECHEC",utilisateur_id=None,ressource_type="sauvegarde",ressource_id=run.id,contexte={"erreur":str(exc)[:255]}); await db.commit()
