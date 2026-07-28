from __future__ import annotations
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.integration_workspace_repository import IntegrationWorkspaceRepository
from app.schemas.integration_workspace import IntegrationQueueWorkspaceItem,IntegrationQueueWorkspaceResponse,IntegrationWorkspaceFiltersResponse,IntegrationWorkspaceItem,IntegrationWorkspaceRegistryResponse,IntegrationWorkspaceSummary
from app.services.validation_bnec_service import ValidationBnecService

class IntegrationWorkspaceService:
    @staticmethod
    def display_name(first_names,last_name,email):
        name=' '.join(part for part in (first_names,last_name) if part).strip()
        return name or email

    @staticmethod
    async def item_from_row(db: AsyncSession,row) -> IntegrationWorkspaceItem:
        item=row[0]
        counts=await ValidationBnecService.integration_response(db,item)
        return IntegrationWorkspaceItem(
            integration_id=item.id,integration_status=item.statut,started_on=item.date_debut,ended_on=item.date_fin,precontrol=item.precontrole,postcontrol=item.postcontrole,backup_reference=item.sauvegarde_reference,summary_text=item.resume,
            administrator_id=item.administrateur_id,administrator_name=IntegrationWorkspaceService.display_name(row.administrator_first_names,row.administrator_last_name,row.administrator_email),
            validation_id=row.validation_id,validation_decision=row.validation_decision,validation_date=row.validation_date,validator_id=row.validator_id,validator_name=IntegrationWorkspaceService.display_name(row.validator_first_names,row.validator_last_name,row.validator_email),
            fiche_id=row.fiche_id,fiche_revision=row.fiche_revision,mission_id=row.mission_id,mission_code=row.mission_code,campaign_code=row.campaign_code,campaign_name=row.campaign_name,zone_name=row.zone_name,
            entreprise_id=row.entreprise_id,entreprise_name=row.entreprise_name or row.entreprise_trade_name,entreprise_identifiant=row.entreprise_identifiant,
            control_id=row.control_id,control_score=str(row.control_score) if row.control_score is not None else None,control_maximum=str(row.control_maximum) if row.control_maximum is not None else None,control_rate=row.control_rate,control_ended_on=row.control_ended_on,
            elements_count=counts.elements_count,elements_success_count=counts.elements_success_count,elements_error_count=counts.elements_error_count)

    @staticmethod
    async def filters(db: AsyncSession):
        return IntegrationWorkspaceFiltersResponse(statuses=await IntegrationWorkspaceRepository.statuses(db))

    @staticmethod
    async def registry(db: AsyncSession, *, search, statut, sort, limit, offset):
        rows,total=await IntegrationWorkspaceRepository.registry(db,search=search,statut=statut,sort=sort,limit=limit,offset=offset)
        raw=await IntegrationWorkspaceRepository.summary(db,search=search,statut=statut)
        return IntegrationWorkspaceRegistryResponse(total=total,limit=limit,offset=offset,summary=IntegrationWorkspaceSummary(total=raw['total'],waiting=raw['EN_ATTENTE'],precontrolled=raw['PRECONTROLE'],in_progress=raw['INTEGRATION_EN_COURS'],postcontrolled=raw['POSTCONTROLE'],integrated=raw['INTEGREE'],failed=raw['ECHEC']),items=[await IntegrationWorkspaceService.item_from_row(db,row) for row in rows])

    @staticmethod
    async def context(db: AsyncSession,integration_id):
        row=await IntegrationWorkspaceRepository.context(db,integration_id)
        if row is None: raise HTTPException(404,'Intégration BNEC introuvable.')
        return await IntegrationWorkspaceService.item_from_row(db,row)

    @staticmethod
    async def queue(db: AsyncSession, *, search, limit, offset):
        rows,total=await IntegrationWorkspaceRepository.queue(db,search=search,limit=limit,offset=offset)
        items=[]
        for row in rows:
            status=row.existing_integration_status
            items.append(IntegrationQueueWorkspaceItem(validation_id=row.validation_id,validation_decision=row.validation_decision,validation_date=row.validation_date,validator_name=IntegrationWorkspaceService.display_name(row.validator_first_names,row.validator_last_name,row.validator_email),fiche_id=row.fiche_id,fiche_revision=row.fiche_revision,mission_id=row.mission_id,mission_code=row.mission_code,campaign_code=row.campaign_code,campaign_name=row.campaign_name,zone_name=row.zone_name,entreprise_id=row.entreprise_id,entreprise_name=row.entreprise_name or row.entreprise_trade_name,entreprise_identifiant=row.entreprise_identifiant,control_id=row.control_id,control_rate=row.control_rate,existing_integration_id=row.existing_integration_id,existing_integration_status=status,existing_integration_closed=bool(row.existing_integration_ended_on),eligible=status!='INTEGREE'))
        return IntegrationQueueWorkspaceResponse(total=total,items=items)
