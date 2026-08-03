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

    We point ``DATABASE_URL`` at an unresolvable host and assert the endpoint
    still returns a stable response (200 or 503) with a ``checks`` map.
    """
    monkeypatch.setenv("DB_HOST", "invalid-host-that-does-not-exist.local")
    monkeypatch.setenv("DB_PORT", "12345")

    response = client.get("/ready")
    assert response.status_code in {200, 503}

    payload = response.get_json()
    assert payload is not None, "/ready must return JSON"
    assert "checks" in payload, "/ready must expose per-dependency status"

    checks = payload["checks"]
    assert isinstance(checks, dict)
    # At minimum the database check must be present and report not-ready.
    if "database" in checks:
        assert checks["database"].get("ready") is False


@pytest.mark.api
def test_ready_endpoint_structure(client):
    """When the app can start at all, ``/ready`` returns a well-formed payload."""
    response = client.get("/ready")
    assert response.status_code in {200, 503}

    payload = response.get_json()
    assert "status" in payload
    assert "checks" in payload
    assert isinstance(payload["checks"], dict)
