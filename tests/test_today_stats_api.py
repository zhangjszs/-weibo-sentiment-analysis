#!/usr/bin/env python3
"""
/api/stats/today 接口测试
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utils.jwt_handler import create_token  # noqa: E402
from views.api import api as api_module  # noqa: E402


@pytest.fixture
def app():
    from app import app

    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_get_today_stats_success(client, monkeypatch):
    monkeypatch.setattr(
        api_module.article_service,
        "get_today_stats",
        lambda: {
            "today_articles": 12,
            "today_comments": 34,
            "latest_update": "2026-03-01 12:00:00",
        },
    )
    token = create_token(1, "tester")

    response = client.get(
        "/api/stats/today",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["code"] == 200
    assert payload["data"]["today_articles"] == 12
    assert payload["data"]["today_comments"] == 34


def test_get_today_stats_handles_service_error(client, monkeypatch):
    def _raise_error():
        raise RuntimeError("stats_failed")

    monkeypatch.setattr(api_module.article_service, "get_today_stats", _raise_error)
    token = create_token(1, "tester")

    response = client.get(
        "/api/stats/today",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 500
    payload = response.get_json()
    assert payload["code"] == 500
