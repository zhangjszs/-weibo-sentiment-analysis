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

# 添加 src 到路径
sys.path.insert(0, str(PROJECT_ROOT / "src"))


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
    """Flask应用fixture"""
    monkeypatch.setenv("AUTO_CREATE_DEMO_ADMIN", "False")
    monkeypatch.setenv("DEMO_ADMIN_RESET_PASSWORD", "False")
    
    # 清除已导入的模块，确保使用新的环境变量
    for mod in list(sys.modules.keys()):
        if mod.startswith("app") or mod.startswith("config") or mod.startswith("services.startup_service"):
            del sys.modules[mod]
    
    app_module = importlib.import_module("app")
    flask_app = app_module.app
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    """Flask测试客户端fixture"""
    return app.test_client()


@pytest.fixture
def authed_client(client):
    """带认证的Flask测试客户端fixture"""
    from utils.jwt_handler import create_token

    token = create_token(1, "tester")
    client.set_cookie("weibo_access_token", token)
    return client
