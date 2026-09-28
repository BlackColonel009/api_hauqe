from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.account_service import AccountService
from app.tasks.process_notification_queue import (
    is_account_security_email,
    should_suppress_system_email,
)


def notification(*, subject="Nouvelle mission", result=None, user_id=None):
    return SimpleNamespace(
        alerte_id=None,
        destinataire_utilisateur_id=user_id,
        objet=subject,
        resultat=result,
    )


def test_only_admin_roles_manage_agent_email_policy():
    AccountService.require_email_policy_admin(SimpleNamespace(roles=["ADMIN_HAUQE"]))
    AccountService.require_email_policy_admin(SimpleNamespace(roles=["ADMIN_BNEC"]))
    with pytest.raises(HTTPException) as error:
        AccountService.require_email_policy_admin(SimpleNamespace(roles=["CELLULE_VEILLE"]))
    assert error.value.status_code == 403


def test_functional_email_can_be_suppressed_without_touching_security_or_external():
    user_id = uuid4()
    functional = notification(user_id=user_id)
    assert should_suppress_system_email(functional, enabled=False)
    assert not should_suppress_system_email(functional, enabled=True)

    security = notification(user_id=user_id, result="SECURITE_COMPTE")
    assert is_account_security_email(security)
    assert not should_suppress_system_email(security, enabled=False)

    prior_security = notification(
        user_id=user_id,
        subject="Réinitialisation de votre mot de passe HAUQE Certif",
    )
    assert not should_suppress_system_email(prior_security, enabled=False)
    assert not should_suppress_system_email(notification(), enabled=False)
