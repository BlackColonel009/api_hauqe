"""Routes API Vérification — page frontend principale : `verifications.html`."""
from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.verification import *
from app.services.auth_service import AuthContext
from app.services.verification_service import VerificationService

router=APIRouter(prefix="/verifications",tags=["Vérification"])

@router.get("",response_model=VerificationDossierListResponse)
async def list_verifications(statut:str|None=Query(None),avis:str|None=Query(None),priorite:str|None=Query(None),
    verificateur_id:UUID|None=Query(None),limit:int=Query(50,ge=1,le=200),offset:int=Query(0,ge=0),
    db:AsyncSession=Depends(get_db),actor:AuthContext=Depends(require_permission("VERIFICATION.LIRE"))):
    return await VerificationService.list(db,statut=statut,avis=avis,priorite=priorite,
        verificateur_id=verificateur_id,limit=limit,offset=offset)


@router.get("/filters",response_model=VerificationWorkspaceFiltersResponse)
async def verification_workspace_filters(db:AsyncSession=Depends(get_db),actor:AuthContext=Depends(require_permission("VERIFICATION.LIRE"))):
    return await VerificationService.workspace_filters(db)

@router.get("/registry",response_model=VerificationRegistryResponse)
async def verification_workspace_registry(search:str|None=Query(None,max_length=255),statut:str|None=Query(None,max_length=255),avis:str|None=Query(None,max_length=255),priorite:str|None=Query(None,max_length=255),verificateur_id:UUID|None=Query(None),sort:str=Query("opened",max_length=64),limit:int=Query(25,ge=1,le=100),offset:int=Query(0,ge=0),db:AsyncSession=Depends(get_db),actor:AuthContext=Depends(require_permission("VERIFICATION.LIRE"))):
    return await VerificationService.workspace_registry(db,search=search,statut=statut,avis=avis,priorite=priorite,verificateur_id=verificateur_id,sort=sort,limit=limit,offset=offset)

@router.get("/eligible-fiches",response_model=VerificationEligibleFichesResponse)
async def verification_eligible_fiches(search:str|None=Query(None,max_length=255),limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0),db:AsyncSession=Depends(get_db),actor:AuthContext=Depends(require_permission("VERIFICATION.LIRE"))):
    return await VerificationService.eligible_fiches(db,search=search,limit=limit,offset=offset)

@router.post("/from-fiche/{fiche_id}",response_model=VerificationDossierResponse,status_code=201)
async def open_from_fiche(fiche_id:UUID,payload:VerificationOpenRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.OUVRIR"))):
    return await VerificationService.open_from_fiche(db,fiche_id=fiche_id,payload=payload,actor=actor,request=request)

@router.get("/{dossier_id}",response_model=VerificationDossierResponse)
async def get_verification(dossier_id:UUID,db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.LIRE"))):
    return await VerificationService.response(db,await VerificationService.get(db,dossier_id))


@router.get("/{dossier_id}/context",response_model=VerificationRegistryItem)
async def verification_context(dossier_id:UUID,db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.LIRE"))):
    return await VerificationService.workspace_item(db,dossier_id)

@router.patch("/{dossier_id}",response_model=VerificationDossierResponse)
async def update_verification(dossier_id:UUID,payload:VerificationUpdateRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.VERIFIER"))):
    return await VerificationService.update(db,dossier_id=dossier_id,payload=payload,actor=actor,request=request)

@router.post("/{dossier_id}/close",response_model=VerificationDossierResponse)
async def close_verification(dossier_id:UUID,payload:VerificationCloseRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.CLOTURER"))):
    return await VerificationService.close(db,dossier_id=dossier_id,payload=payload,actor=actor,request=request)

@router.post("/{dossier_id}/reopen",response_model=VerificationDossierResponse)
async def reopen_verification(dossier_id:UUID,payload:VerificationReopenRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.AFFECTER"))):
    return await VerificationService.reopen(db,dossier_id=dossier_id,payload=payload,actor=actor,request=request)

@router.get("/{dossier_id}/affectations",response_model=list[VerificationAssignmentResponse])
async def list_assignments(dossier_id:UUID,db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.LIRE"))):
    return await VerificationService.list_assignments(db,dossier_id)

@router.post("/{dossier_id}/affectations",response_model=VerificationAssignmentResponse,status_code=201)
async def assign(dossier_id:UUID,payload:VerificationAssignmentCreateRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.AFFECTER"))):
    return await VerificationService.assign(db,dossier_id=dossier_id,payload=payload,actor=actor,request=request)

@router.patch("/{dossier_id}/affectations/{assignment_id}",response_model=VerificationAssignmentResponse)
async def update_assignment(dossier_id:UUID,assignment_id:UUID,payload:VerificationAssignmentUpdateRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.AFFECTER"))):
    return await VerificationService.update_assignment(db,dossier_id=dossier_id,assignment_id=assignment_id,
        payload=payload,actor=actor,request=request)

@router.get("/{dossier_id}/points",response_model=list[VerificationPointResponse])
async def list_points(dossier_id:UUID,db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.LIRE"))):
    return await VerificationService.list_points(db,dossier_id)

@router.post("/{dossier_id}/points",response_model=VerificationPointResponse,status_code=201)
async def create_point(dossier_id:UUID,payload:VerificationPointCreateRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.VERIFIER"))):
    return await VerificationService.save_point(db,dossier_id=dossier_id,payload=payload,actor=actor,request=request)

@router.patch("/{dossier_id}/points/{point_id}",response_model=VerificationPointResponse)
async def update_point(dossier_id:UUID,point_id:UUID,payload:VerificationPointUpdateRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.VERIFIER"))):
    return await VerificationService.update_point(db,dossier_id=dossier_id,point_id=point_id,payload=payload,actor=actor,request=request)

@router.get("/{dossier_id}/anomalies",response_model=list[VerificationAnomalyResponse])
async def list_anomalies(dossier_id:UUID,db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.LIRE"))):
    return await VerificationService.list_anomalies(db,dossier_id)

@router.post("/{dossier_id}/anomalies",response_model=VerificationAnomalyResponse,status_code=201)
async def create_anomaly(dossier_id:UUID,payload:VerificationAnomalyCreateRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.SIGNALER_ANOMALIE"))):
    return await VerificationService.create_anomaly(db,dossier_id=dossier_id,payload=payload,actor=actor,request=request)

@router.patch("/{dossier_id}/anomalies/{anomaly_id}",response_model=VerificationAnomalyResponse)
async def update_anomaly(dossier_id:UUID,anomaly_id:UUID,payload:VerificationAnomalyUpdateRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.SIGNALER_ANOMALIE"))):
    return await VerificationService.update_anomaly(db,dossier_id=dossier_id,anomaly_id=anomaly_id,payload=payload,actor=actor,request=request)

@router.post("/{dossier_id}/anomalies/{anomaly_id}/resolve",response_model=VerificationAnomalyResponse)
async def resolve_anomaly(dossier_id:UUID,anomaly_id:UUID,payload:VerificationAnomalyResolveRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.VERIFIER"))):
    return await VerificationService.resolve_anomaly(db,dossier_id=dossier_id,anomaly_id=anomaly_id,payload=payload,actor=actor,request=request)

@router.post("/{dossier_id}/anomalies/{anomaly_id}/escalate",response_model=VerificationAnomalyResponse)
async def escalate_anomaly(dossier_id:UUID,anomaly_id:UUID,payload:VerificationAnomalyEscalateRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.SIGNALER_ANOMALIE"))):
    return await VerificationService.escalate_anomaly(db,dossier_id=dossier_id,anomaly_id=anomaly_id,payload=payload,actor=actor,request=request)

@router.get("/{dossier_id}/confirmations",response_model=list[ExternalConfirmationResponse])
async def list_confirmations(dossier_id:UUID,db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.LIRE"))):
    return await VerificationService.list_confirmations(db,dossier_id)

@router.post("/{dossier_id}/confirmations",response_model=ExternalConfirmationResponse,status_code=201)
async def create_confirmation(dossier_id:UUID,payload:ExternalConfirmationCreateRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.CONFIRMER"))):
    return await VerificationService.create_confirmation(db,dossier_id=dossier_id,payload=payload,actor=actor,request=request)

@router.patch("/{dossier_id}/confirmations/{confirmation_id}",response_model=ExternalConfirmationResponse)
async def update_confirmation(dossier_id:UUID,confirmation_id:UUID,payload:ExternalConfirmationUpdateRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.CONFIRMER"))):
    return await VerificationService.update_confirmation(db,dossier_id=dossier_id,confirmation_id=confirmation_id,
        payload=payload,actor=actor,request=request)

@router.post("/{dossier_id}/confirmations/{confirmation_id}/response",response_model=ExternalConfirmationResponse)
async def response_confirmation(dossier_id:UUID,confirmation_id:UUID,payload:ExternalConfirmationResponseRequest,request:Request,
    db=Depends(get_db),actor=Depends(require_permission("VERIFICATION.CONFIRMER"))):
    return await VerificationService.record_confirmation_response(db,dossier_id=dossier_id,confirmation_id=confirmation_id,
        payload=payload,actor=actor,request=request)
