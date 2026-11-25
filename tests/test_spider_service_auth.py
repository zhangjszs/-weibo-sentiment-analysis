"""Exercise the Spider and NLP Flask auth hooks without Celery side effects."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

pytestmark = pytest.mark.unit
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(params=["spider", "nlp"])
def service(request, monkeypatch):
    name = request.param
    app_dir = PROJECT_ROOT / f"{name}_service" / "app"
    tasks_spec = importlib.util.spec_from_file_location(
        f"_{name}_tasks", app_dir / "tasks.py"
    )
    tasks = importlib.util.module_from_spec(tasks_spec)
    tasks_spec.loader.exec_module(tasks)

    spec = importlib.util.spec_from_file_location(f"_{name}_main", app_dir / "main.py")
    module = importlib.util.module_from_spec(spec)
    # Each standalone image imports app.tasks; don't replace the main backend's app.
    with monkeypatch.context() as imports:
        imports.setitem(sys.modules, "app.tasks", tasks)
        spec.loader.exec_module(module)
    module.app.config["TESTING"] = True

    if name == "spider":
        path, body = "/api/spider/tasks", {"type": "hot"}
        handler = Mock(return_value=Mock(id="task-auth-001"))
        monkeypatch.setattr(module.spider_hot_task, "delay", handler)
        result = {"task_id": "task-auth-001"}
    else:
        path, body = "/api/nlp/analyze", {"text": "example"}
        result = {"label": "neutral"}
        handler = Mock(return_value=result)
        monkeypatch.setattr(module, "analyze_text_sync", handler)
    return (
        module.app.test_client(),
        f"{name.upper()}_SERVICE_TOKEN",
        path,
        body,
        handler,
        result,
    )


@pytest.mark.parametrize("token", [None, "", "   "])
def test_missing_configuration_rejects_protected_requests(service, monkeypatch, token):
    client, env_name, path, body, handler, _ = service
    if token is None:
        monkeypatch.delenv(env_name, raising=False)
    else:
        monkeypatch.setenv(env_name, token)

    response = client.post(path, json=body)

    assert response.status_code == 503
    assert response.get_json()["msg"] == "service token not configured"
    handler.assert_not_called()


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer wrong-token"}])
def test_configured_service_rejects_missing_or_invalid_credentials(
    service, monkeypatch, headers
):
    client, env_name, path, body, handler, _ = service
    monkeypatch.setenv(env_name, "test-service-token")

    response = client.post(path, json=body, headers=headers)

    assert response.status_code == 401
    assert response.get_json()["msg"] == "unauthorized"
    handler.assert_not_called()


def test_configured_service_accepts_valid_token(service, monkeypatch):
    client, env_name, path, body, handler, result = service
    monkeypatch.setenv(env_name, "test-service-token")

    response = client.post(
        path, json=body, headers={"Authorization": "Bearer test-service-token"}
    )

    assert response.status_code == 200
    assert result.items() <= response.get_json()["data"].items()
    handler.assert_called_once()


@pytest.mark.parametrize("token", ["", "test-service-token"])
def test_health_remains_public(service, monkeypatch, token):
    client, env_name, _, _, _, _ = service
    monkeypatch.setenv(env_name, token)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "ok"
