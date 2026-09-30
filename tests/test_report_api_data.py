#!/usr/bin/env python3
"""
报告数据 API 测试
"""


import pytest

pytestmark = pytest.mark.api


from utils.jwt_handler import create_token


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

    def _db_offline():
        raise RuntimeError("db offline")

    monkeypatch.setattr(report_api, "_article_repo", _db_offline)

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

    class _FakeArticleRepo:
        def count_total(self):
            return 5

    class _FakeCommentRepo:
        def count_total(self):
            return 3

        def get_recent_texts(self, limit=200):
            return ["很好", "一般", "很差"]

        def get_recent_trend(self, days=7):
            return [
                {"date": "2026-03-18", "count": 1},
                {"date": "2026-03-19", "count": 2},
            ]

    monkeypatch.setattr(report_api, "_article_repo", lambda: _FakeArticleRepo())
    monkeypatch.setattr(report_api, "_comment_repo", lambda: _FakeCommentRepo())

    import services.sentiment_service as sentiment_service

    monkeypatch.setattr(
        sentiment_service.SentimentService,
        "analyze_distribution_cached",
        lambda texts, mode="simple", sample_size=200: {"正面": 1, "中性": 1, "负面": 1},
    )

    response = client.get("/api/report/data", headers=_auth_headers())

    assert response.status_code == 200
    payload = response.get_json()["data"]
    summary = payload["summary"]
    assert summary["positive_count"] == 1
    assert summary["neutral_count"] == 1
    assert summary["negative_count"] == 1
    assert payload["sentiment_analysis"]["正面情感占比"] == "33.3%"
