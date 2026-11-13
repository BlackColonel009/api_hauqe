import asyncio
from types import SimpleNamespace as Obj
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from app.services.verification_service import ensure_verification_write


@pytest.mark.parametrize('assigned_to_me,assigned_count,role,allowed',[
    (False,0,'VERIFICATEUR',True),
    (True,1,'VERIFICATEUR',True),
    (False,1,'VERIFICATEUR',False),
    (False,1,'POINT_FOCAL_BNEC',True),
    (False,1,'ADMIN_HAUQE',True),
])
def test_assignment_exclusivity(assigned_to_me,assigned_count,role,allowed):
    user_id,dossier_id=uuid4(),uuid4()
    assigned=[] if not assigned_count else [user_id if assigned_to_me else uuid4()]
    db=Obj(execute=AsyncMock(side_effect=[Obj(scalar_one_or_none=lambda:dossier_id),
        Obj(scalars=lambda:Obj(all=lambda:assigned))]))
    actor=Obj(user=Obj(id=user_id),roles=[role])
    if allowed:
        asyncio.run(ensure_verification_write(db,dossier_id,actor))
    else:
        with pytest.raises(HTTPException) as error:
            asyncio.run(ensure_verification_write(db,dossier_id,actor))
        assert error.value.status_code==403
    query=db.execute.call_args_list[1].args[0]
    assert 'affectations_verification.statut' in str(query)
