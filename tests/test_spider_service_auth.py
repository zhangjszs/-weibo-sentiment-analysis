from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

import importlib
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class _FakeAsyncResult:
    id = "task-auth-001"


class _FakeTask:
    def delay(self, *args, **kwargs):
        return _FakeAsyncResult()


@pytest.fixture
def spider_service_module(monkeypatch):
    monkeypatch.syspath_prepend(str(PROJECT_ROOT / "spider_service"))
    for module_name in [
        "app",
        "app.main",
        "app.tasks",
        "celery_app",
        "spider_service.app.main",
    ]:
        sys.modules.pop(module_name, None)

    module = importlib.import_module("app.main")
    monkeypatch.setattr(module, "spider_hot_task", _FakeTask())
    monkeypatch.setattr(module, "spider_search_task", _FakeTask())
    monkeypatch.setattr(module, "spider_comments_task", _FakeTask())
    module.app.config["TESTING"] = True
    return module


@pytest.fixture
def client(spider_service_module):
    return spider_service_module.app.test_client()


def test_spider_service_allows_tasks_when_token_is_not_configured(
    client, monkeypatch
):
    monkeypatch.delenv("SPIDER_SERVICE_TOKEN", raising=False)

    response = client.post("/api/spider/tasks", json={"type": "hot"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data"]["task_id"] == "task-auth-001"


def test_spider_service_rejects_missing_token_when_configured(client, monkeypatch):
    monkeypatch.setenv("SPIDER_SERVICE_TOKEN", "secret-token")

    response = client.post("/api/spider/tasks", json={"type": "hot"})

    assert response.status_code == 401
    assert response.get_json()["msg"] == "unauthorized"


def test_spider_service_rejects_invalid_token_when_configured(client, monkeypatch):
    monkeypatch.setenv("SPIDER_SERVICE_TOKEN", "secret-token")

    response = client.post(
        "/api/spider/tasks",
        json={"type": "hot"},
        headers={"Authorization": "Bearer wrong-token"},
    )

    assert response.status_code == 401
    assert response.get_json()["msg"] == "unauthorized"


def test_spider_service_accepts_valid_token_when_configured(client, monkeypatch):
    monkeypatch.setenv("SPIDER_SERVICE_TOKEN", "secret-token")

    response = client.post(
        "/api/spider/tasks",
        json={"type": "hot"},
        headers={"Authorization": "Bearer secret-token"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data"]["task_id"] == "task-auth-001"


def test_spider_service_health_remains_public(client, monkeypatch):
    monkeypatch.setenv("SPIDER_SERVICE_TOKEN", "secret-token")

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "ok"
