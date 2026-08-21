#!/usr/bin/env python3
"""
工厂守卫测试：import 无副作用，急切构造仅发生在组合根。
"""

import importlib
import sys

import pytest

pytestmark = pytest.mark.unit


def _reload_app_module(monkeypatch):
    monkeypatch.setenv("AUTO_CREATE_DEMO_ADMIN", "False")
    monkeypatch.setenv("DEMO_ADMIN_RESET_PASSWORD", "False")
    for mod in list(sys.modules.keys()):
        if mod.startswith("app") or mod.startswith("config") or mod.startswith("services.startup_service"):
            del sys.modules[mod]
    return importlib.import_module("app")


def test_import_has_no_side_effects(monkeypatch):
    """import app 不应创建 Flask 实例或配置日志。"""
    mod = _reload_app_module(monkeypatch)
    # 工厂存在，全局 app 不存在
    assert hasattr(mod, "create_app")
    assert callable(mod.create_app)
    assert not hasattr(mod, "app") or not getattr(mod, "app", None)  # 无模块级 app 实例
    # 日志幂等守卫：import 时不应已配置
    # 首次 import 后 _LOGGING_CONFIGURED 仍为 False（仅 create_app 时才置 True）
    assert mod._LOGGING_CONFIGURED is False


def test_create_app_returns_isolated_instances(monkeypatch):
    """每次 create_app() 返回全新 Flask 实例。"""
    mod = _reload_app_module(monkeypatch)
    app1 = mod.create_app()
    app1.config["TESTING"] = True
    app2 = mod.create_app()
    app2.config["TESTING"] = True
    assert app1 is not app2
    assert app1.name == app2.name == "app"


def test_create_app_is_idempotent_logging(monkeypatch):
    """多次 create_app 不应重复添加日志 handler（幂等）。"""
    mod = _reload_app_module(monkeypatch)
    mod.create_app()
    assert mod._LOGGING_CONFIGURED is True
    # 第二次调用不应抛错且守卫仍为 True
    mod.create_app()
    assert mod._LOGGING_CONFIGURED is True


def test_run_is_composition_root():
    """组合根 run:app 仍可用（gunicorn 入口）。"""
    import run as run_module

    assert hasattr(run_module, "app")
    # run.app 应是 Flask 实例
    from flask import Flask

    assert isinstance(run_module.app, Flask)
