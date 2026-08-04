"""Project health endpoint tests.

These tests cover the ``/health`` and ``/ready`` endpoints that the quality
gate (``scripts/verify_project.ps1``) and CI rely on.  They must pass in
the default ``unit``/``api`` test run without any external service.
"""

from __future__ import annotations

import json

import pytest


@pytest.mark.api
def test_health_endpoint_is_dependency_free(client):
    """``/health`` must always return 200 and never touch Redis/MySQL."""
    response = client.get("/health")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload is not None, "/health must return JSON"
    assert payload.get("status") == "ok"
    # The endpoint must not perform I/O, so it should not include
    # dependency check results — that is what ``/ready`` is for.
    assert "checks" not in payload, "/health must be a pure liveness probe"


@pytest.mark.api
def test_health_endpoint_is_json(client):
    """Response content type must be application/json."""
    response = client.get("/health")
    assert "application/json" in response.content_type


@pytest.mark.api
def test_ready_endpoint_reports_missing_dependencies(client, monkeypatch):
    """``/ready`` must report per-check status when a dependency is unreachable.

    We monkeypatch the ``db_session`` that the Flask app imported at module
    load time, so the readiness probe sees a hard failure without relying on
    ``Config`` class attribute caching, which would ignore runtime
    ``os.environ`` changes.
    """
    import app as app_module

    class _FailingSession:
        def execute(self, *args, **kwargs):
            raise Exception("simulated database failure")

        def remove(self):
            pass

    monkeypatch.setattr(app_module, "db_session", _FailingSession())

    response = client.get("/ready")
    assert response.status_code in {200, 503}

    payload = response.get_json()
    assert payload is not None, "/ready must return JSON"
    assert "checks" in payload, "/ready must expose per-dependency status"

    checks = payload["checks"]
    assert isinstance(checks, dict)
    assert "database" in checks
    assert checks["database"].get("ready") is False


@pytest.mark.api
def test_ready_endpoint_structure(client, monkeypatch):
    """When the app can start at all, ``/ready`` returns a well-formed payload."""
    import redis as redis_lib

    class _FakeRedis:
        def ping(self):
            pass

    monkeypatch.setattr(redis_lib, "Redis", _FakeRedis)

    response = client.get("/ready")
    assert response.status_code in {200, 503}

    payload = response.get_json()
    assert "status" in payload
    assert "checks" in payload
    assert isinstance(payload["checks"], dict)
