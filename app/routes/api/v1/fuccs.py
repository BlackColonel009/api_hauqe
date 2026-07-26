"""Routes API FUCCS.

`controle.html` utilise les contrôles, notes et constats.
`referentiels.html` / `regles-codification.html` administrent les versions de grille.
"""
from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request, Response, status
from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.fuccs import *
from app.services.fuccs_service import FuccsService

router=APIRouter(prefix="/fuccs",tags=["FUCCS"])
verification_fuccs_router=APIRouter(prefix="/verifications/{dossier_id}/fuccs-controles",tags=["FUCCS - Contrôles"])

@router.get("/grilles",response_model=list[FuccsGridResponse])
async def grids(db=Depends(get_db),actor=Depends(require_permission("FUCCS.LIRE"))): return await FuccsService.list_grids(db)

@router.get("/grilles/active",response_model=FuccsGridResponse)
async def active(db=Depends(get_db),actor=Depends(require_permission("FUCCS.LIRE"))): return await FuccsService.active_grid(db)

@router.post("/grilles",response_model=FuccsGridResponse,status_code=201)
async def create_grid(payload:FuccsGridCreateRequest,request:Request,db=Depends(get_db),actor=Depends(require_permission("FUCCS.ADMINISTRER_GRILLE"))):
    return await FuccsService.create_grid(db,payload=payload,actor=actor,request=request)

@router.get("/grilles/{grid_id}",response_model=FuccsGridResponse)
async def get_grid(grid_id:UUID,db=Depends(get_db),actor=Depends(require_permission("FUCCS.LIRE"))):
    return await FuccsService.grid_response(db,await FuccsService.require_grid(db,grid_id))

@router.patch("/grilles/{grid_id}",response_model=FuccsGridResponse)
async def update_grid(grid_id:UUID,payload:FuccsGridUpdateRequest,request:Request,db=Depends(get_db),actor=Depends(require_permission("FUCCS.ADMINISTRER_GRILLE"))):
    return await FuccsService.update_grid(db,grid_id=grid_id,payload=payload,actor=actor,request=request)

@router.post("/grilles/{grid_id}/clone",response_model=FuccsGridResponse,status_code=201)
async def clone_grid(grid_id:UUID,payload:FuccsGridCloneRequest,request:Request,db=Depends(get_db),actor=Depends(require_permission("FUCCS.ADMINISTRER_GRILLE"))):
    return await FuccsService.clone_grid(db,grid_id=grid_id,payload=payload,actor=actor,request=request)

@router.post("/grilles/{grid_id}/publish",response_model=FuccsGridResponse)
async def publish_grid(grid_id:UUID,payload:FuccsGridPublishRequest,request:Request,db=Depends(get_db),actor=Depends(require_permission("FUCCS.ADMINISTRER_GRILLE"))):
    return await FuccsService.publish_grid(db,grid_id=grid_id,payload=payload,actor=actor,request=request)

@router.post("/grilles/{grid_id}/retire",response_model=FuccsGridResponse)
async def retire_grid(grid_id:UUID,payload:FuccsGridRetireRequest,request:Request,db=Depends(get_db),actor=Depends(require_permission("FUCCS.ADMINISTRER_GRILLE"))):
    return await FuccsService.retire_grid(db,grid_id=grid_id,payload=payload,actor=actor,request=request)

@router.get("/grilles/{grid_id}/rubriques",response_model=list[FuccsRubricResponse])
async def rubrics(grid_id:UUID,db=Depends(get_db),actor=Depends(require_permission("FUCCS.LIRE"))):
    return await FuccsService.list_rubrics(db,grid_id)

@router.post("/grilles/{grid_id}/rubriques",response_model=FuccsRubricResponse,status_code=201)
async def create_rubric(grid_id:UUID,payload:FuccsRubricCreateRequest,request:Request,db=Depends(get_db),actor=Depends(require_permission("FUCCS.ADMINISTRER_GRILLE"))):
    return await FuccsService.create_rubric(db,grid_id=grid_id,payload=payload,actor=actor,request=request)

@router.patch("/grilles/{grid_id}/rubriques/{rubric_id}",response_model=FuccsRubricResponse)
async def update_rubric(grid_id:UUID,rubric_id:UUID,payload:FuccsRubricUpdateRequest,request:Request,db=Depends(get_db),actor=Depends(require_permission("FUCCS.ADMINISTRER_GRILLE"))):
    return await FuccsService.update_rubric(db,grid_id=grid_id,rubric_id=rubric_id,payload=payload,actor=actor,request=request)

@router.delete("/grilles/{grid_id}/rubriques/{rubric_id}",status_code=204)
async def delete_rubric(grid_id:UUID,rubric_id:UUID,request:Request,db=Depends(get_db),actor=Depends(require_permission("FUCCS.ADMINISTRER_GRILLE"))):
    await FuccsService.delete_rubric(db,grid_id=grid_id,rubric_id=rubric_id,actor=actor,request=request); return Response(status_code=204)

@router.get("/grilles/{grid_id}/criteres",response_model=list[FuccsCriterionResponse])
async def criteria(grid_id:UUID,db=Depends(get_db),actor=Depends(require_permission("FUCCS.LIRE"))):
    return await FuccsService.list_criteria(db,grid_id)

@router.post("/grilles/{grid_id}/rubriques/{rubric_id}/criteres",response_model=FuccsCriterionResponse,status_code=201)
async def create_criterion(grid_id:UUID,rubric_id:UUID,payload:FuccsCriterionCreateRequest,request:Request,db=Depends(get_db),actor=Depends(require_permission("FUCCS.ADMINISTRER_GRILLE"))):
    return await FuccsService.create_criterion(db,grid_id=grid_id,rubric_id=rubric_id,payload=payload,actor=actor,request=request)

@router.patch("/grilles/{grid_id}/rubriques/{rubric_id}/criteres/{criterion_id}",response_model=FuccsCriterionResponse)
async def update_criterion(grid_id:UUID,rubric_id:UUID,criterion_id:UUID,payload:FuccsCriterionUpdateRequest,request:Request,db=Depends(get_db),actor=Depends(require_permission("FUCCS.ADMINISTRER_GRILLE"))):
    return await FuccsService.update_criterion(db,grid_id=grid_id,rubric_id=rubric_id,criterion_id=criterion_id,payload=payload,actor=actor,request=request)

@router.delete("/grilles/{grid_id}/rubriques/{rubric_id}/criteres/{criterion_id}",status_code=204)
async def delete_criterion(grid_id:UUID,rubric_id:UUID,criterion_id:UUID,request:Request,db=Depends(get_db),actor=Depends(require_permission("FUCCS.ADMINISTRER_GRILLE"))):
    await FuccsService.delete_criterion(db,grid_id=grid_id,rubric_id=rubric_id,criterion_id=criterion_id,actor=actor,request=request); return Response(status_code=204)

@router.get("/controles",response_model=FuccsControlListResponse)
async def controls(dossier_id:UUID|None=Query(None),statut:str|None=Query(None),limit:int=Query(50,ge=1,le=200),offset:int=Query(0,ge=0),
    db=Depends(get_db),actor=Depends(require_permission("FUCCS.LIRE"))):
    return await FuccsService.list_controls(db,dossier_id=dossier_id,statut=statut,limit=limit,offset=offset)

@verification_fuccs_router.post("",response_model=FuccsControlResponse,status_code=201)
async def create_control(dossier_id:UUID,payload:FuccsControlCreateRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("FUCCS.CONTROLER"))):
    return await FuccsService.create_control(db,dossier_id=dossier_id,payload=payload,actor=actor,request=request)

@router.get("/controles/{control_id}",response_model=FuccsControlResponse)
async def get_control(control_id:UUID,db=Depends(get_db),actor=Depends(require_permission("FUCCS.LIRE"))):
    return await FuccsService.control_response(db,await FuccsService.require_control(db,control_id))

@router.get("/controles/{control_id}/notes",response_model=list[FuccsNoteResponse])
async def notes(control_id:UUID,db=Depends(get_db),actor=Depends(require_permission("FUCCS.LIRE"))):
    return await FuccsService.list_notes(db,control_id)

@router.put("/controles/{control_id}/notes/{criterion_id}",response_model=FuccsNoteResponse)
async def upsert_note(control_id:UUID,criterion_id:UUID,payload:FuccsNoteUpsertRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("FUCCS.CONTROLER"))):
    return await FuccsService.upsert_note(db,control_id=control_id,criterion_id=criterion_id,payload=payload,actor=actor,request=request)

@router.get("/controles/{control_id}/constats",response_model=list[FuccsFindingResponse])
async def findings(control_id:UUID,db=Depends(get_db),actor=Depends(require_permission("FUCCS.LIRE"))):
    return await FuccsService.list_findings(db,control_id)

@router.post("/controles/{control_id}/constats",response_model=FuccsFindingResponse,status_code=201)
async def create_finding(control_id:UUID,payload:FuccsFindingCreateRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("FUCCS.CONTROLER"))):
    return await FuccsService.create_finding(db,control_id=control_id,payload=payload,actor=actor,request=request)

@router.patch("/controles/{control_id}/constats/{finding_id}",response_model=FuccsFindingResponse)
async def update_finding(control_id:UUID,finding_id:UUID,payload:FuccsFindingUpdateRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("FUCCS.CONTROLER"))):
    return await FuccsService.update_finding(db,control_id=control_id,finding_id=finding_id,payload=payload,actor=actor,request=request)

@router.post("/controles/{control_id}/finalize",response_model=FuccsControlResponse)
async def finalize(control_id:UUID,payload:FuccsFinalizeRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("FUCCS.FINALISER"))):
    return await FuccsService.finalize(db,control_id=control_id,payload=payload,actor=actor,request=request)

@router.post("/controles/{control_id}/reopen",response_model=FuccsControlResponse)
async def reopen(control_id:UUID,payload:FuccsReopenRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("FUCCS.REOUVRIR"))):
    return await FuccsService.reopen(db,control_id=control_id,payload=payload,actor=actor,request=request)
