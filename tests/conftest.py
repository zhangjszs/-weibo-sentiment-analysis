from __future__ import annotations

import importlib
import os
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SANDBOX_TEMP_DIR = PROJECT_ROOT / ".pytest_tmp" / "temp"

sys.path.insert(0, str(PROJECT_ROOT / "src"))

os.environ["TEST_DATABASE_URL"] = "sqlite:///:memory:"


def sandbox_mkdtemp(
    suffix: str | None = None,
    prefix: str | None = None,
    dir: str | os.PathLike[str] | None = None,
) -> str:
    target_dir = Path(dir or SANDBOX_TEMP_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)

    prefix = prefix or "tmp"
    suffix = suffix or ""
    for _ in range(1000):
        candidate = target_dir / f"{prefix}{uuid.uuid4().hex}{suffix}"
        try:
            candidate.mkdir()
            return str(candidate)
        except FileExistsError:
            continue

    raise FileExistsError("无法创建唯一的临时目录")


def configure_sandbox_temp_dir() -> None:
    SANDBOX_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    sandbox_temp_path = str(SANDBOX_TEMP_DIR)

    os.environ["TMP"] = sandbox_temp_path
    os.environ["TEMP"] = sandbox_temp_path
    os.environ["TMPDIR"] = sandbox_temp_path

    tempfile.mkdtemp = sandbox_mkdtemp
    tempfile.tempdir = sandbox_temp_path


configure_sandbox_temp_dir()


@pytest.fixture(scope="session", autouse=True)
def apply_sandbox_temp_dir() -> None:
    configure_sandbox_temp_dir()


@pytest.fixture
def app(monkeypatch):
    """Flask应用fixture — 使用 SQLite 内存数据库。"""
    monkeypatch.setenv("AUTO_CREATE_DEMO_ADMIN", "False")
    monkeypatch.setenv("DEMO_ADMIN_RESET_PASSWORD", "False")

    import database

    database.reset()

    for mod in list(sys.modules.keys()):
        if mod.startswith("app") or mod.startswith("config") or mod.startswith("services.startup_service"):
            del sys.modules[mod]

    app_module = importlib.import_module("app")
    flask_app = app_module.create_app()
    flask_app.config["TESTING"] = True

    # Celery result backend 默认 redis://localhost:6379，Redis 不可用时
    # AsyncResult.state 会因 redis-py 8.0 默认 retry=10 阻塞 ~20s。测试中
    # 改用 memory backend，避免任何 Redis 连接尝试。
    try:
        from tasks.celery_config import celery_app

        # Celery Settings 的 broker_url/result_backend 属性优先读环境变量
        # （见 celery/app/utils.py:Settings.broker_url），仅改 conf 字典不足以覆盖
        # .env 中的 CELERY_BROKER_URL，故需同步覆盖环境变量。
        monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
        monkeypatch.setenv("CELERY_RESULT_BACKEND", "cache+memory://")
        monkeypatch.setitem(celery_app.conf, "result_backend", "cache+memory://")
        monkeypatch.setitem(celery_app.conf, "broker_url", "memory://")
        monkeypatch.setitem(celery_app.conf, "task_always_eager", True)
    except Exception:
        pass

    return flask_app


@pytest.fixture
def client(app):
    """Flask测试客户端fixture"""
    return app.test_client()


def set_auth_cookie(client, token):
    """兼容 Werkzeug 2.x 和 3.x 的 Cookie 设置辅助函数"""
    import inspect

    sig = inspect.signature(client.set_cookie)
    if "server_name" in sig.parameters:
        # Werkzeug 2.x: set_cookie(server_name, key, value, ...)
        client.set_cookie("localhost", "weibo_access_token", token)
    else:
        # Werkzeug 3.x: set_cookie(key, value, *, domain="localhost", ...)
        client.set_cookie("weibo_access_token", token)


@pytest.fixture
def authed_client(client):
    """带认证的Flask测试客户端fixture"""
    from utils.jwt_handler import create_token

    token = create_token(1, "tester")
    set_auth_cookie(client, token)
    return client


# ---------------------------------------------------------------------------
# 预警子系统 DB fixture（P0 #5）
# ---------------------------------------------------------------------------


@pytest.fixture
def alert_db(monkeypatch):
    """in-memory SQLite + scoped_session，monkeypatch 到 ``database.db_session``。

    供预警子系统测试：``alert_service`` / ``notification_service`` 方法内部
    ``from database import db_session`` 调用时读取 ``database.db_session`` 模块
    属性，故 patch 该属性即可让引擎/服务写入测试 SQLite。``StaticPool`` 保证所有
    连接共享同一 :memory: 库（否则每连接各持独立 :memory:）。``expire_on_commit=False``
    使提交后对象属性仍可直接访问（_fire_alert 返回的 alert/rule 无需 reload）。
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker
    from sqlalchemy.pool import StaticPool

    import database
    from database import Base

    test_engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    TestSession = scoped_session(
        sessionmaker(bind=test_engine, expire_on_commit=False)
    )
    monkeypatch.setattr(database, "db_session", TestSession)
    Base.metadata.create_all(test_engine)
    yield TestSession
    TestSession.remove()
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture
def alert_engine(alert_db):
    """DB-backed 预警引擎，已 seed 5 条默认规则。"""
    from services.alert_service import AlertRuleEngine

    eng = AlertRuleEngine()
    eng._ensure_defaults_seeded()
    return eng
