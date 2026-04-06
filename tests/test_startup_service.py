#!/usr/bin/env python3
"""
启动服务测试
"""

import os
import sys
import importlib
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.settings import Config
from services import startup_service


def test_ensure_demo_admin_creates_user(monkeypatch):
    monkeypatch.setattr(Config, "IS_DEVELOPMENT", True)
    monkeypatch.setattr(Config, "AUTO_CREATE_DEMO_ADMIN", True)
    monkeypatch.setattr(Config, "DEMO_ADMIN_USERNAME", "admin")
    monkeypatch.setattr(Config, "DEMO_ADMIN_PASSWORD", "Admin123!")
    monkeypatch.setattr(Config, "DEMO_ADMIN_RESET_PASSWORD", True)
    monkeypatch.setattr(Config, "ADMIN_USERS", set())

    calls = []

    def fake_querys(sql, params=None, type="no_select"):
        calls.append((sql, params, type))
        if "SELECT id, password FROM user" in sql:
            return []
        return "数据库语句执行成功"

    monkeypatch.setattr(startup_service, "querys", fake_querys)
    monkeypatch.setattr(startup_service, "hash_password", lambda raw: f"hashed:{raw}")

    result = startup_service.ensure_demo_admin()

    assert result["enabled"] is True
    assert result["action"] == "created"
    assert "admin" in Config.ADMIN_USERS
    assert any("INSERT INTO user" in sql for sql, _, _ in calls)


def test_ensure_demo_admin_resets_legacy_password(monkeypatch):
    monkeypatch.setattr(Config, "IS_DEVELOPMENT", True)
    monkeypatch.setattr(Config, "AUTO_CREATE_DEMO_ADMIN", True)
    monkeypatch.setattr(Config, "DEMO_ADMIN_USERNAME", "admin")
    monkeypatch.setattr(Config, "DEMO_ADMIN_PASSWORD", "Admin123!")
    monkeypatch.setattr(Config, "DEMO_ADMIN_RESET_PASSWORD", True)
    monkeypatch.setattr(Config, "ADMIN_USERS", {"admin"})

    calls = []

    def fake_querys(sql, params=None, type="no_select"):
        calls.append((sql, params, type))
        if "SELECT id, password FROM user" in sql:
            return [{"id": 1, "password": "123123"}]
        return "数据库语句执行成功"

    monkeypatch.setattr(startup_service, "querys", fake_querys)
    monkeypatch.setattr(startup_service, "hash_password", lambda raw: f"hashed:{raw}")

    result = startup_service.ensure_demo_admin()

    assert result["enabled"] is True
    assert result["action"] == "reset_password"
    assert any("UPDATE user SET password" in sql for sql, _, _ in calls)


def test_development_defaults_do_not_auto_create_or_reset_demo_admin(monkeypatch):
    original_auto = os.environ.get("AUTO_CREATE_DEMO_ADMIN")
    original_reset = os.environ.get("DEMO_ADMIN_RESET_PASSWORD")
    original_env = os.environ.get("FLASK_ENV")

    monkeypatch.delenv("AUTO_CREATE_DEMO_ADMIN", raising=False)
    monkeypatch.delenv("DEMO_ADMIN_RESET_PASSWORD", raising=False)
    monkeypatch.setenv("FLASK_ENV", "development")

    import config.settings as settings_module

    reloaded = importlib.reload(settings_module)
    try:
        assert reloaded.Config.AUTO_CREATE_DEMO_ADMIN is False
        assert reloaded.Config.DEMO_ADMIN_RESET_PASSWORD is False
    finally:
        if original_auto is None:
            os.environ.pop("AUTO_CREATE_DEMO_ADMIN", None)
        else:
            os.environ["AUTO_CREATE_DEMO_ADMIN"] = original_auto
        if original_reset is None:
            os.environ.pop("DEMO_ADMIN_RESET_PASSWORD", None)
        else:
            os.environ["DEMO_ADMIN_RESET_PASSWORD"] = original_reset
        if original_env is None:
            os.environ.pop("FLASK_ENV", None)
        else:
            os.environ["FLASK_ENV"] = original_env
        importlib.reload(settings_module)


def test_schedule_startup_warmup_disabled(monkeypatch):
    monkeypatch.setattr(Config, "ENABLE_STARTUP_WARMUP", False)
    started = startup_service.schedule_startup_warmup(app=None)
    assert started is False


def test_schedule_startup_warmup_records_status(monkeypatch):
    monkeypatch.setattr(Config, "ENABLE_STARTUP_WARMUP", True)
    monkeypatch.setattr(Config, "STARTUP_WARMUP_DELAY", 0.0)
    monkeypatch.setattr(Config, "DEMO_ADMIN_USERNAME", "admin")
    monkeypatch.setattr(startup_service, "create_token", lambda *args, **kwargs: "token")

    class ImmediateThread:
        def __init__(self, target=None, name=None, daemon=None):
            self._target = target

        def start(self):
            if self._target:
                self._target()

    monkeypatch.setattr(startup_service.threading, "Thread", ImmediateThread)

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, path, headers=None):
            return SimpleNamespace(status_code=200)

    class FakeApp:
        @staticmethod
        def test_client():
            return FakeClient()

    started = startup_service.schedule_startup_warmup(FakeApp())
    assert started is True

    status = startup_service.get_startup_status()
    warmup = status["warmup"]
    assert warmup["enabled"] is True
    assert warmup["running"] is False
    assert warmup["paths_total"] == 4
    assert warmup["paths_done"] == 4
    assert len(warmup["results"]) == 4
    assert all(item["status_code"] == 200 for item in warmup["results"])
