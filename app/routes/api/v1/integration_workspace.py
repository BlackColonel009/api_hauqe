from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.integration_workspace import IntegrationQueueWorkspaceResponse,IntegrationWorkspaceFiltersResponse,IntegrationWorkspaceItem,IntegrationWorkspaceRegistryResponse
from app.services.auth_service import AuthContext
from app.services.integration_workspace_service import IntegrationWorkspaceService

router=APIRouter(prefix='/integrations-bnec/workspace',tags=['Intégration BNEC - Espace de travail'])

@router.get('/filters',response_model=IntegrationWorkspaceFiltersResponse)
async def integration_workspace_filters(db: AsyncSession=Depends(get_db),actor: AuthContext=Depends(require_permission('INTEGRATION.LIRE'))):
    return await IntegrationWorkspaceService.filters(db)

@router.get('/registry',response_model=IntegrationWorkspaceRegistryResponse)
async def integration_workspace_registry(search: str|None=Query(default=None,max_length=255),statut: str|None=Query(default=None,max_length=255),sort: str=Query(default='recent',max_length=64),limit: int=Query(default=25,ge=1,le=100),offset: int=Query(default=0,ge=0),db: AsyncSession=Depends(get_db),actor: AuthContext=Depends(require_permission('INTEGRATION.LIRE'))):
    return await IntegrationWorkspaceService.registry(db,search=search,statut=statut,sort=sort,limit=limit,offset=offset)

@router.get('/queue',response_model=IntegrationQueueWorkspaceResponse)
async def integration_workspace_queue(search: str|None=Query(default=None,max_length=255),limit: int=Query(default=20,ge=1,le=100),offset: int=Query(default=0,ge=0),db: AsyncSession=Depends(get_db),actor: AuthContext=Depends(require_permission('INTEGRATION.LIRE'))):
    return await IntegrationWorkspaceService.queue(db,search=search,limit=limit,offset=offset)

@router.get('/{integration_id}',response_model=IntegrationWorkspaceItem)
async def integration_workspace_context(integration_id: UUID,db: AsyncSession=Depends(get_db),actor: AuthContext=Depends(require_permission('INTEGRATION.LIRE'))):
    return await IntegrationWorkspaceService.context(db,integration_id)
