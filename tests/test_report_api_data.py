#!/usr/bin/env python3
"""
报告数据 API 测试
"""

import os
import sys
import importlib

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utils.jwt_handler import create_token


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("AUTO_CREATE_DEMO_ADMIN", "False")
    monkeypatch.setenv("DEMO_ADMIN_RESET_PASSWORD", "False")

    sys.modules.pop("app", None)
    sys.modules.pop("config.settings", None)
    sys.modules.pop("services.startup_service", None)
    app_module = importlib.import_module("app")
    app = app_module.app

    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def _auth_headers():
    token = create_token(1, "report_tester")
    return {"Authorization": f"Bearer {token}"}


def test_report_data_returns_core_fields(client):
    response = client.get("/api/report/data", headers=_auth_headers())

    assert response.status_code == 200
    body = response.get_json()
    assert body is not None
    assert body.get("code") == 200

    payload = body.get("data", {})
    for key in [
        "summary",
        "hot_topics",
        "alerts",
        "trend",
        "demo_mode",
        "data_source",
    ]:
        assert key in payload


def test_report_data_demo_mode_explicit(client):
    response = client.get("/api/report/data?demo=true", headers=_auth_headers())

    assert response.status_code == 200
    body = response.get_json()
    assert body is not None
    assert body.get("code") == 200

    payload = body.get("data", {})
    assert payload.get("demo_mode") is True
    assert payload.get("data_source") == "demo"
    assert payload.get("summary", {}).get("total_articles", 0) > 0


def test_report_data_does_not_silent_demo_fallback(client, monkeypatch):
    import views.api.report_api as report_api

    def fake_querys(sql, params=None, type=None):
        raise RuntimeError("db offline")

    monkeypatch.setattr(report_api, "querys", fake_querys)

    response = client.get("/api/report/data", headers=_auth_headers())

    assert response.status_code == 200
    body = response.get_json()
    payload = body.get("data", {})
    assert payload.get("demo_mode") is False
    assert payload.get("data_source") == "real_error"
    assert payload.get("summary", {}).get("total_articles") == 0
    assert payload.get("trend") == []


def test_report_data_uses_real_sentiment_distribution(client, monkeypatch):
    import views.api.report_api as report_api

    query_results = {
        "SELECT COUNT(*) AS count FROM article": [{"count": 5}],
        "SELECT COUNT(*) AS count FROM comments": [{"count": 3}],
        "FROM comments": [
            {"date": "2026-03-18", "count": 1},
            {"date": "2026-03-19", "count": 2},
        ],
    }

    def fake_querys(sql, params=None, type=None):
        for key, value in query_results.items():
            if key in sql:
                return value
        return []

    monkeypatch.setattr(report_api, "querys", fake_querys)

    import services.sentiment_service as sentiment_service

    monkeypatch.setattr(
        report_api,
        "_load_recent_comment_texts",
        lambda limit=200: ["很好", "一般", "很差"],
    )
    monkeypatch.setattr(
        sentiment_service.SentimentService,
        "analyze_distribution",
        lambda texts, mode="simple", sample_size=100: {"正面": 1, "中性": 1, "负面": 1},
    )

    response = client.get("/api/report/data", headers=_auth_headers())

    assert response.status_code == 200
    payload = response.get_json()["data"]
    summary = payload["summary"]
    assert summary["positive_count"] == 1
    assert summary["neutral_count"] == 1
    assert summary["negative_count"] == 1
    assert payload["sentiment_analysis"]["正面情感占比"] == "33.3%"
