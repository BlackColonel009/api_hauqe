import asyncio
from types import SimpleNamespace as Obj
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from app.services.collection_transfer_service import transfer, archive, ensure_manager
from app.services.collection_transfer_service import unarchive
from app.repositories.collecte_workspace_repository import CollecteWorkspaceRepository
from app.routes.api.v1.missions_collecte import TransferDossiersRequest


def test_transfer_permissions_and_reason():
    for role in ['ADMIN_HAUQE', 'POINT_FOCAL_BNEC']:
        ensure_manager(Obj(roles=[role]))
    with pytest.raises(HTTPException):
        ensure_manager(Obj(roles=['COLLECTEUR']))
    with pytest.raises(ValueError):
        TransferDossiersRequest(destination_id=uuid4(), fiche_ids=[uuid4()], motif='   ')


def test_full_revision_transfer_keeps_identity():
    source, destination, company, user, root, revision = [uuid4() for _ in range(6)]
    missions=[Obj(id=source,campagne_id=uuid4()),Obj(id=destination,campagne_id=uuid4(),statut='EN_COURS')]
    fiches=[Obj(id=root,dossier_id=root,entreprise_id=company,responsable_id=user,mission_id=source),
            Obj(id=revision,dossier_id=root,entreprise_id=company,responsable_id=user,mission_id=source)]
    responses=[Obj(scalars=lambda:Obj(all=lambda:missions)),Obj(scalars=lambda:Obj(all=lambda:fiches)),
               Obj(first=lambda:None),Obj(scalars=lambda:Obj(all=lambda:[user]))]
    db=Obj(execute=AsyncMock(side_effect=responses),get=AsyncMock(return_value=Obj(statut='ACTIVE')),commit=AsyncMock())
    payload=TransferDossiersRequest(destination_id=destination,fiche_ids=[revision],motif='Regroupement')
    with patch('app.services.collection_transfer_service.write_audit_event',new=AsyncMock()) as audit:
        result=asyncio.run(transfer(db,source,payload,Obj(roles=['ADMIN_HAUQE'],user=Obj(id=user)),Obj(client=None)))
        assert result=={'dossiers_deplaces':1,'revisions_deplacees':2}
        assert all(f.mission_id==destination for f in fiches)
        assert fiches[0].id==root and fiches[1].id==revision
        assert all(f.responsable_id==user for f in fiches)
        audit.assert_awaited_once()
        db.commit.assert_awaited_once()


def test_archive_nonempty_is_refused_without_commit():
    mission=Obj(id=uuid4(),statut='EN_COURS')
    db=Obj(execute=AsyncMock(side_effect=[Obj(scalar_one_or_none=lambda:mission),Obj(first=lambda:(uuid4(),))]),commit=AsyncMock())
    with pytest.raises(HTTPException) as error:
        asyncio.run(archive(db,mission.id,'Mission vide',Obj(roles=['ADMIN_HAUQE']),Obj(client=None)))
    assert error.value.status_code==409
    db.commit.assert_not_awaited()


def test_unarchive_restarts_as_planned_with_audit():
    mission=Obj(id=uuid4(),statut='ARCHIVEE',campagne_id=uuid4())
    db=Obj(execute=AsyncMock(return_value=Obj(scalar_one_or_none=lambda:mission)),
           get=AsyncMock(return_value=Obj(statut='ACTIVE')),commit=AsyncMock())
    with patch('app.services.collection_transfer_service.write_audit_event',new=AsyncMock()) as audit:
        asyncio.run(unarchive(db,mission.id,'Reprise terrain',Obj(roles=['POINT_FOCAL_BNEC'],user=Obj(id=uuid4())),Obj(client=None)))
        assert mission.statut=='PLANIFIEE'
        audit.assert_awaited_once()


def test_field_registry_excludes_inactive_campaigns_even_without_filters():
    filters=CollecteWorkspaceRepository.build_filters(search=None,campagne_id=None,zone_id=None,
        assigned_user_id=None,mission_statut=None,fiche_statut=None)
    assert len(filters)>0
    assert 'campagnes.statut' in str(filters[0])
