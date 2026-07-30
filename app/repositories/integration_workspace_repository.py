from __future__ import annotations
from uuid import UUID
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from app.models.campagne import Campagne
from app.models.controle_fuccs import ControleFuccs
from app.models.entreprise import Entreprise
from app.models.fiche_collecte import FicheCollecte
from app.models.integration_bnec import IntegrationBnec
from app.models.mission_collecte import MissionCollecte
from app.models.utilisateur import Utilisateur
from app.models.validation import Validation
from app.models.zone_administrative import ZoneAdministrative

class IntegrationWorkspaceRepository:
    @staticmethod
    async def statuses(db: AsyncSession) -> list[str]:
        result = await db.execute(select(IntegrationBnec.statut).where(IntegrationBnec.statut.is_not(None), func.trim(IntegrationBnec.statut) != '').distinct().order_by(IntegrationBnec.statut))
        return [str(v).strip() for v in result.scalars().all() if v]

    @staticmethod
    def registry_base_query():
        admin = aliased(Utilisateur)
        validator = aliased(Utilisateur)
        return (select(
            IntegrationBnec,
            Validation.id.label('validation_id'), Validation.decision.label('validation_decision'), Validation.date_validation.label('validation_date'), Validation.validateur_id.label('validator_id'),
            validator.prenoms.label('validator_first_names'), validator.nom.label('validator_last_name'), validator.email.label('validator_email'),
            FicheCollecte.id.label('fiche_id'), FicheCollecte.numero_revision.label('fiche_revision'), FicheCollecte.entreprise_id.label('entreprise_id'),
            MissionCollecte.id.label('mission_id'), MissionCollecte.code.label('mission_code'),
            Campagne.code.label('campaign_code'), Campagne.nom.label('campaign_name'), ZoneAdministrative.nom.label('zone_name'),
            Entreprise.identifiant_national.label('entreprise_identifiant'), Entreprise.raison_sociale.label('entreprise_name'), Entreprise.nom_commercial.label('entreprise_trade_name'),
            ControleFuccs.id.label('control_id'), ControleFuccs.score_brut.label('control_score'), ControleFuccs.score_maximal.label('control_maximum'), ControleFuccs.taux.label('control_rate'), ControleFuccs.date_fin.label('control_ended_on'),
            admin.prenoms.label('administrator_first_names'), admin.nom.label('administrator_last_name'), admin.email.label('administrator_email'),
        ).select_from(IntegrationBnec)
          .join(Validation, Validation.id == IntegrationBnec.validation_id)
          .join(FicheCollecte, FicheCollecte.id == Validation.fiche_collecte_id)
          .join(MissionCollecte, MissionCollecte.id == FicheCollecte.mission_id)
          .join(Campagne, Campagne.id == MissionCollecte.campagne_id)
          .join(ZoneAdministrative, ZoneAdministrative.id == MissionCollecte.zone_id)
          .outerjoin(Entreprise, Entreprise.id == FicheCollecte.entreprise_id)
          .outerjoin(ControleFuccs, ControleFuccs.id == Validation.controle_fuccs_id)
          .join(admin, admin.id == IntegrationBnec.administrateur_id)
          .outerjoin(validator, validator.id == Validation.validateur_id))

    @staticmethod
    def registry_filters(*, search: str | None, statut: str | None):
        filters=[]
        if statut: filters.append(func.upper(IntegrationBnec.statut) == statut.strip().upper())
        if search and search.strip():
            p=f'%{search.strip()}%'
            filters.append(or_(MissionCollecte.code.ilike(p),Campagne.code.ilike(p),Campagne.nom.ilike(p),ZoneAdministrative.nom.ilike(p),Entreprise.identifiant_national.ilike(p),Entreprise.raison_sociale.ilike(p),Entreprise.nom_commercial.ilike(p),IntegrationBnec.resume.ilike(p),IntegrationBnec.sauvegarde_reference.ilike(p)))
        return filters

    @staticmethod
    async def registry(db: AsyncSession, *, search, statut, sort, limit, offset):
        filters=IntegrationWorkspaceRepository.registry_filters(search=search,statut=statut)
        order={'oldest':IntegrationBnec.created_at.asc(),'company':Entreprise.raison_sociale.asc().nullslast(),'status':IntegrationBnec.statut.asc().nullslast()}.get(sort,IntegrationBnec.created_at.desc())
        result=await db.execute(IntegrationWorkspaceRepository.registry_base_query().where(*filters).order_by(order,IntegrationBnec.created_at.desc()).limit(limit).offset(offset))
        count=await db.execute(select(func.count(IntegrationBnec.id)).select_from(IntegrationBnec).join(Validation,Validation.id==IntegrationBnec.validation_id).join(FicheCollecte,FicheCollecte.id==Validation.fiche_collecte_id).join(MissionCollecte,MissionCollecte.id==FicheCollecte.mission_id).join(Campagne,Campagne.id==MissionCollecte.campagne_id).join(ZoneAdministrative,ZoneAdministrative.id==MissionCollecte.zone_id).outerjoin(Entreprise,Entreprise.id==FicheCollecte.entreprise_id).where(*filters))
        return result.all(), int(count.scalar_one() or 0)

    @staticmethod
    async def context(db: AsyncSession, integration_id: UUID):
        result=await db.execute(IntegrationWorkspaceRepository.registry_base_query().where(IntegrationBnec.id==integration_id).limit(1))
        return result.one_or_none()

    @staticmethod
    async def summary(db: AsyncSession, *, search, statut):
        filters=IntegrationWorkspaceRepository.registry_filters(search=search,statut=statut)
        base=(select(IntegrationBnec.id,IntegrationBnec.statut).select_from(IntegrationBnec).join(Validation,Validation.id==IntegrationBnec.validation_id).join(FicheCollecte,FicheCollecte.id==Validation.fiche_collecte_id).join(MissionCollecte,MissionCollecte.id==FicheCollecte.mission_id).join(Campagne,Campagne.id==MissionCollecte.campagne_id).join(ZoneAdministrative,ZoneAdministrative.id==MissionCollecte.zone_id).outerjoin(Entreprise,Entreprise.id==FicheCollecte.entreprise_id).where(*filters).subquery())
        out={}
        out['total']=int((await db.execute(select(func.count(base.c.id)))).scalar_one() or 0)
        for status in ('EN_ATTENTE','BLOQUE','PRECONTROLE','INTEGRATION_EN_COURS','POSTCONTROLE','INTEGREE','ECHEC'):
            out[status]=int((await db.execute(select(func.count(base.c.id)).where(func.upper(func.coalesce(base.c.statut,''))==status))).scalar_one() or 0)
        return out

    @staticmethod
    def latest_integration_id():
        return select(IntegrationBnec.id).where(IntegrationBnec.validation_id==Validation.id).order_by(IntegrationBnec.created_at.desc()).limit(1).correlate(Validation).scalar_subquery()

    @staticmethod
    async def queue(db: AsyncSession, *, search, limit, offset):
        latest_id=IntegrationWorkspaceRepository.latest_integration_id()
        latest_status=select(IntegrationBnec.statut).where(IntegrationBnec.id==latest_id).correlate(Validation).scalar_subquery()
        latest_ended=select(IntegrationBnec.date_fin).where(IntegrationBnec.id==latest_id).correlate(Validation).scalar_subquery()
        validator=aliased(Utilisateur)
        filters=[Validation.niveau_validation=='NIVEAU_2',Validation.decision.in_(['VALIDE','VALIDE_SOUS_RESERVE']),Validation.statut=='TERMINE']
        if search and search.strip():
            p=f'%{search.strip()}%'
            filters.append(or_(MissionCollecte.code.ilike(p),Campagne.code.ilike(p),Campagne.nom.ilike(p),ZoneAdministrative.nom.ilike(p),Entreprise.identifiant_national.ilike(p),Entreprise.raison_sociale.ilike(p),Entreprise.nom_commercial.ilike(p)))
        query=(select(
            Validation.id.label('validation_id'),Validation.decision.label('validation_decision'),Validation.date_validation.label('validation_date'),
            validator.prenoms.label('validator_first_names'),validator.nom.label('validator_last_name'),validator.email.label('validator_email'),
            FicheCollecte.id.label('fiche_id'),FicheCollecte.numero_revision.label('fiche_revision'),
            MissionCollecte.id.label('mission_id'),MissionCollecte.code.label('mission_code'),Campagne.code.label('campaign_code'),Campagne.nom.label('campaign_name'),ZoneAdministrative.nom.label('zone_name'),
            Entreprise.id.label('entreprise_id'),Entreprise.identifiant_national.label('entreprise_identifiant'),Entreprise.raison_sociale.label('entreprise_name'),Entreprise.nom_commercial.label('entreprise_trade_name'),
            ControleFuccs.id.label('control_id'),ControleFuccs.taux.label('control_rate'),
            latest_id.label('existing_integration_id'),latest_status.label('existing_integration_status'),latest_ended.label('existing_integration_ended_on')
        ).select_from(Validation).join(FicheCollecte,FicheCollecte.id==Validation.fiche_collecte_id).join(MissionCollecte,MissionCollecte.id==FicheCollecte.mission_id).join(Campagne,Campagne.id==MissionCollecte.campagne_id).join(ZoneAdministrative,ZoneAdministrative.id==MissionCollecte.zone_id).outerjoin(Entreprise,Entreprise.id==FicheCollecte.entreprise_id).outerjoin(ControleFuccs,ControleFuccs.id==Validation.controle_fuccs_id).outerjoin(validator,validator.id==Validation.validateur_id).where(*filters).order_by(Validation.date_validation.desc().nullslast(),Validation.created_at.desc()))
        result=await db.execute(query.limit(limit).offset(offset))
        count=await db.execute(select(func.count(Validation.id)).select_from(Validation).join(FicheCollecte,FicheCollecte.id==Validation.fiche_collecte_id).join(MissionCollecte,MissionCollecte.id==FicheCollecte.mission_id).join(Campagne,Campagne.id==MissionCollecte.campagne_id).join(ZoneAdministrative,ZoneAdministrative.id==MissionCollecte.zone_id).outerjoin(Entreprise,Entreprise.id==FicheCollecte.entreprise_id).where(*filters))
        return result.all(), int(count.scalar_one() or 0)
