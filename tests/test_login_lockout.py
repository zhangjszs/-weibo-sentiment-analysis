#!/usr/bin/env python3
"""
登录失败锁定测试（#15）
"""

import pytest

pytestmark = pytest.mark.api


import pytest  # noqa: E402

from services.auth_service import AuthService  # noqa: E402
from utils import login_lockout  # noqa: E402
from utils.cache import memory_cache  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_lockout_cache():
    yield
    for username, ip in (
        ("locked-user", "1.2.3.4"),
        ("locked-user", "other-ip"),
        ("ghost", "9.9.9.9"),
    ):
        memory_cache.delete(login_lockout._fail_key(username, ip))
        memory_cache.delete(login_lockout._lock_key(username, ip))


def _seed_failures(username="locked-user", ip="1.2.3.4", n=login_lockout.MAX_FAILURES):
    for _ in range(n):
        login_lockout.record_failure(username, ip)


def test_lockout_triggers_after_max_failures():
    _seed_failures()
    assert login_lockout.is_locked("locked-user", "1.2.3.4") is True


def test_lockout_isolated_by_username_and_ip():
    _seed_failures()
    assert login_lockout.is_locked("locked-user", "5.6.7.8") is False
    assert login_lockout.is_locked("other-user", "1.2.3.4") is False


def test_service_login_rejects_when_locked(monkeypatch):
    service = AuthService()
    _seed_failures()

    called = {"repo": False}

    def _fail_repo(username):
        called["repo"] = True
        return None

    monkeypatch.setattr(service.user_repo, "find_by_username", _fail_repo)
    success, msg, _ = service.login("locked-user", "whatever", "1.2.3.4")
    assert success is False
    assert "锁定" in msg
    # 锁定期间不应触达仓储层
    assert called["repo"] is False


def test_service_login_records_failure_and_clears_on_success(monkeypatch):
    service = AuthService()
    user = {"id": 3, "username": "locked-user", "password": "stored-hash", "create_time": ""}

    monkeypatch.setattr(
        service.user_repo,
        "find_by_username",
        lambda username: user if username == "locked-user" else None,
    )
    # 密码正确与否由提交的口令决定（right 才算对）
    monkeypatch.setattr("services.auth_service.verify_password", lambda pwd, h: pwd == "right")

    # 失败 5 次：前 4 次未达阈值；第 5 次失败后锁定生效（该次返回仍是
    # 通用失败文案——锁定检查在入口，随后才计数）
    for _ in range(4):
        success, msg, _ = service.login("locked-user", "wrong", "1.2.3.4")
        assert success is False
        assert msg == "用户名或密码错误"
    success, msg, _ = service.login("locked-user", "wrong", "1.2.3.4")
    assert success is False
    assert login_lockout.is_locked("locked-user", "1.2.3.4") is True

    # 第 6 次（锁定后）返回锁定文案，且不触达仓储层
    repo_called = {"hit": False}

    def _spy(username):
        repo_called["hit"] = True
        return user

    monkeypatch.setattr(service.user_repo, "find_by_username", _spy)
    success, msg, _ = service.login("locked-user", "right", "1.2.3.4")
    assert success is False and "锁定" in msg
    assert repo_called["hit"] is False

    # 换 IP 不受影响：成功登录返回 token
    success, _, payload = service.login("locked-user", "right", "other-ip")
    assert success is True
    assert payload["token"]


def test_unknown_username_failures_also_counted(monkeypatch):
    """不存在的用户名也计数（撞库者无法通过换用户名绕过锁定语义）。"""
    service = AuthService()
    monkeypatch.setattr(service.user_repo, "find_by_username", lambda username: None)
    for _ in range(login_lockout.MAX_FAILURES):
        service.login("ghost", "x", "9.9.9.9")
    assert login_lockout.is_locked("ghost", "9.9.9.9") is True
