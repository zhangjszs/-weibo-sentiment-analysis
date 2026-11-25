import pytest

from models.user import User
from services import admin_provisioning
from utils.password_hasher import verify_password

pytestmark = pytest.mark.unit


def test_operator_can_create_only_the_configured_identity_once(monkeypatch, alert_db):
    monkeypatch.setattr(admin_provisioning.Config, "ADMIN_USERS", {"operator"})
    with pytest.raises(ValueError, match="ADMIN_USERS"):
        admin_provisioning.create_admin_account("other", "fixture-First-2002@")

    assert admin_provisioning.create_admin_account("operator", "fixture-First-2002@")
    assert not admin_provisioning.create_admin_account("operator", "fixture-Second-2003@")
    account = alert_db.query(User).filter_by(username="operator").one()
    assert verify_password("fixture-First-2002@", account.password)


@pytest.mark.parametrize("password", ["", "too-short"])
def test_operator_cannot_provision_weak_credentials(monkeypatch, alert_db, password):
    monkeypatch.setattr(admin_provisioning.Config, "ADMIN_USERS", {"operator"})
    with pytest.raises(ValueError, match="15"):
        admin_provisioning.create_admin_account("operator", password)
    assert alert_db.query(User).filter_by(username="operator").first() is None
