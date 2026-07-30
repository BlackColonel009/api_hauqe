"""Repository PostgreSQL du domaine FUCCS."""
from __future__ import annotations
from datetime import date
from sqlalchemy import delete, func, or_, select
from app.models.constat_controle import ConstatControle
from app.models.controle_fuccs import ControleFuccs
from app.models.critere_fuccs import CritereFuccs
from app.models.document import Document
from app.models.dossier_verification import DossierVerification
from app.models.grille_fuccs import GrilleFuccs
from app.models.note_critere import NoteCritere
from app.models.rubrique_fuccs import RubriqueFuccs

class FuccsRepository:
    @staticmethod
    async def get_grid(db, grid_id):
        r=await db.execute(select(GrilleFuccs).where(GrilleFuccs.id==grid_id)); return r.scalar_one_or_none()

    @staticmethod
    async def find_grid_version(db, *, code, version):
        r=await db.execute(select(GrilleFuccs).where(GrilleFuccs.code==code,GrilleFuccs.version==version)); return r.scalar_one_or_none()

    @staticmethod
    async def list_grids(db):
        r=await db.execute(select(GrilleFuccs).order_by(GrilleFuccs.created_at.desc())); return list(r.scalars().all())

    @staticmethod
    async def active_grid(db):
        today=date.today()
        r=await db.execute(select(GrilleFuccs).where(
            GrilleFuccs.statut_publication=="PUBLIE",
            or_(GrilleFuccs.date_effet.is_(None),GrilleFuccs.date_effet<=today),
            or_(GrilleFuccs.date_fin.is_(None),GrilleFuccs.date_fin>=today)
        ).order_by(GrilleFuccs.date_effet.desc().nullslast(),GrilleFuccs.created_at.desc()).limit(1))
        return r.scalar_one_or_none()

    @staticmethod
    async def grid_counts(db, grid_id):
        rr=await db.execute(select(func.count(RubriqueFuccs.id)).where(RubriqueFuccs.grille_fuccs_id==grid_id))
        cr=await db.execute(select(func.count(CritereFuccs.id),func.coalesce(func.sum(CritereFuccs.score_maximal),0))
            .select_from(CritereFuccs).join(RubriqueFuccs,RubriqueFuccs.id==CritereFuccs.rubrique_fuccs_id)
            .where(RubriqueFuccs.grille_fuccs_id==grid_id))
        cc,score=cr.one()
        return int(rr.scalar_one()),int(cc),score

    @staticmethod
    async def list_rubrics(db, grid_id):
        r=await db.execute(select(RubriqueFuccs).where(RubriqueFuccs.grille_fuccs_id==grid_id)
            .order_by(RubriqueFuccs.ordre_affichage,RubriqueFuccs.code))
        return list(r.scalars().all())

    @staticmethod
    async def get_rubric(db, *, grid_id, rubric_id):
        r=await db.execute(select(RubriqueFuccs).where(RubriqueFuccs.id==rubric_id,RubriqueFuccs.grille_fuccs_id==grid_id))
        return r.scalar_one_or_none()

    @staticmethod
    async def list_criteria_for_grid(db, grid_id):
        r=await db.execute(select(CritereFuccs).join(RubriqueFuccs,RubriqueFuccs.id==CritereFuccs.rubrique_fuccs_id)
            .where(RubriqueFuccs.grille_fuccs_id==grid_id)
            .order_by(RubriqueFuccs.ordre_affichage,CritereFuccs.ordre_affichage,CritereFuccs.code))
        return list(r.scalars().all())

    @staticmethod
    async def list_criteria_for_rubric(db, rubric_id):
        r=await db.execute(select(CritereFuccs).where(CritereFuccs.rubrique_fuccs_id==rubric_id)
            .order_by(CritereFuccs.ordre_affichage,CritereFuccs.code))
        return list(r.scalars().all())

    @staticmethod
    async def get_criterion_for_grid(db, *, grid_id, criterion_id):
        r=await db.execute(select(CritereFuccs).join(RubriqueFuccs,RubriqueFuccs.id==CritereFuccs.rubrique_fuccs_id)
            .where(CritereFuccs.id==criterion_id,RubriqueFuccs.grille_fuccs_id==grid_id))
        return r.scalar_one_or_none()

    @staticmethod
    async def get_criterion_for_rubric(db, *, rubric_id, criterion_id):
        r=await db.execute(select(CritereFuccs).where(CritereFuccs.id==criterion_id,CritereFuccs.rubrique_fuccs_id==rubric_id))
        return r.scalar_one_or_none()

    @staticmethod
    async def delete_criterion(db, criterion_id):
        await db.execute(delete(CritereFuccs).where(CritereFuccs.id==criterion_id))

    @staticmethod
    async def delete_rubric_with_criteria(db, rubric_id):
        await db.execute(delete(CritereFuccs).where(CritereFuccs.rubrique_fuccs_id==rubric_id))
        await db.execute(delete(RubriqueFuccs).where(RubriqueFuccs.id==rubric_id))

    @staticmethod
    async def get_dossier(db, dossier_id):
        r=await db.execute(select(DossierVerification).where(DossierVerification.id==dossier_id)); return r.scalar_one_or_none()

    @staticmethod
    async def get_dossier_for_update(db, dossier_id):
        r=await db.execute(
            select(DossierVerification)
            .where(DossierVerification.id==dossier_id)
            .with_for_update()
        )
        return r.scalar_one_or_none()

    @staticmethod
    async def get_control(db, control_id):
        r=await db.execute(select(ControleFuccs).where(ControleFuccs.id==control_id)); return r.scalar_one_or_none()

    @staticmethod
    async def latest_control_for_dossier(db, dossier_id):
        r=await db.execute(
            select(ControleFuccs)
            .where(ControleFuccs.dossier_verification_id==dossier_id)
            .order_by(ControleFuccs.created_at.desc())
            .limit(1)
        )
        return r.scalar_one_or_none()

    @staticmethod
    async def list_controls(db, *, dossier_id, statut, limit, offset):
        f=[]
        if dossier_id: f.append(ControleFuccs.dossier_verification_id==dossier_id)
        if statut: f.append(ControleFuccs.statut==statut.strip())
        r=await db.execute(select(ControleFuccs).where(*f).order_by(ControleFuccs.created_at.desc()).limit(limit).offset(offset))
        c=await db.execute(select(func.count(ControleFuccs.id)).where(*f))
        return list(r.scalars().all()),int(c.scalar_one())

    @staticmethod
    async def control_counts(db, control_id, grid_id):
        n=await db.execute(select(func.count(NoteCritere.id)).where(NoteCritere.controle_fuccs_id==control_id))
        c=await db.execute(select(func.count(CritereFuccs.id)).select_from(CritereFuccs)
            .join(RubriqueFuccs,RubriqueFuccs.id==CritereFuccs.rubrique_fuccs_id).where(RubriqueFuccs.grille_fuccs_id==grid_id))
        f=await db.execute(select(func.count(ConstatControle.id)).where(ConstatControle.controle_fuccs_id==control_id))
        return int(n.scalar_one()),int(c.scalar_one()),int(f.scalar_one())

    @staticmethod
    async def list_notes(db, control_id):
        r=await db.execute(select(NoteCritere).where(NoteCritere.controle_fuccs_id==control_id).order_by(NoteCritere.created_at))
        return list(r.scalars().all())

    @staticmethod
    async def get_note(db, *, control_id, criterion_id):
        r=await db.execute(select(NoteCritere).where(NoteCritere.controle_fuccs_id==control_id,NoteCritere.critere_fuccs_id==criterion_id))
        return r.scalar_one_or_none()

    @staticmethod
    async def list_findings(db, control_id):
        r=await db.execute(select(ConstatControle).where(ConstatControle.controle_fuccs_id==control_id).order_by(ConstatControle.created_at.desc()))
        return list(r.scalars().all())

    @staticmethod
    async def get_finding(db, *, control_id, finding_id):
        r=await db.execute(select(ConstatControle).where(ConstatControle.id==finding_id,ConstatControle.controle_fuccs_id==control_id))
        return r.scalar_one_or_none()

    @staticmethod
    async def get_active_document(db, document_id):
        r=await db.execute(select(Document).where(Document.id==document_id,
            or_(Document.statut.is_(None),Document.statut=="ACTIF")))
        return r.scalar_one_or_none()
