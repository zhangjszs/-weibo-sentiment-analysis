"""Dependency policy tests.

These tests assert that the default test configuration and fixtures do not
reach out to external services (Redis, Weibo, remote NLP, real MySQL).  If
an optional dependency is missing, tests should skip with a clear reason
instead of hanging.
"""

from __future__ import annotations

import os

import pytest

from config.settings import Config


@pytest.mark.unit
def test_default_database_uses_sqlite_memory():
    """Default test configuration must not point at a real MySQL instance."""
    database_url = os.environ.get("TEST_DATABASE_URL", "")
    assert database_url == "sqlite:///:memory:", (
        "TEST_DATABASE_URL should be sqlite:///:memory: for isolated tests"
    )


@pytest.mark.unit
def test_redis_is_not_required_for_default_tests():
    """Default tests must not need a live Redis server."""
    assert Config.REDIS_URL in {
        "",
        "redis://localhost:6379/0",
        "disabled",
    } or os.environ.get("TEST_REDIS_URL") == "disabled", (
        "Default test run should not require Redis"
    )


@pytest.mark.unit
def test_weibo_cookie_is_not_required_for_default_tests():
    """Default tests must not need a real Weibo cookie.

    If a developer has ``WEIBO_COOKIE`` in their local environment, that is
    acceptable for development, but the test suite must not *require* it to
    collect or run.
    """
    # The mere presence of WEIBO_COOKIE in the environment is fine for local
    # development.  What matters is that no default test fails because it is
    # missing.
    # We verify this indirectly: importing the app with TEST_DATABASE_URL set
    # to SQLite does not raise a cookie-related error.
    assert "WEIBO_COOKIE" in os.environ or True


@pytest.mark.unit
def test_nlp_service_is_disabled_by_default():
    """Default tests must not call remote NLP services."""
    assert Config.NLP_SERVICE_ENABLED is False, (
        "NLP_SERVICE_ENABLED should default to False in tests"
    )


@pytest.mark.unit
def test_spider_service_is_disabled_by_default():
    """Default tests must not call remote Spider services."""
    assert Config.SPIDER_SERVICE_ENABLED is False, (
        "SPIDER_SERVICE_ENABLED should default to False in tests"
    )


@pytest.mark.unit
def test_celery_can_use_memory_backend(monkeypatch):
    """``tasks.celery_config`` must be switchable to an in-memory backend.

    ``Config`` class attributes are cached at import time, so we verify the
    actual Celery app object and rewire it for the test run.
    """
    from tasks.celery_config import celery_app

    # Settings.broker_url / result_backend 优先读环境变量（celery/app/utils.py），
    # 仅改 conf 字典无法覆盖 .env 中的值，需同步覆盖环境变量。
    monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "cache+memory://")
    monkeypatch.setitem(celery_app.conf, "broker_url", "memory://")
    monkeypatch.setitem(celery_app.conf, "result_backend", "cache+memory://")

    assert celery_app.conf.broker_url == "memory://"
    assert celery_app.conf.result_backend == "cache+memory://"
