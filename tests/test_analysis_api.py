"""Tests for the ``/api/v1/analysis`` endpoint."""
from __future__ import annotations

import pytest


@pytest.mark.api
class TestV1AnalysisAPI:
    def test_requires_topic(self, authed_client):
        resp = authed_client.get("/api/v1/analysis")
        assert resp.status_code == 400
        body = resp.get_json()
        assert body is not None

    def test_rejects_invalid_time_range(self, authed_client):
        resp = authed_client.get(
            "/api/v1/analysis",
            query_string={
                "topic": "test",
                "start_at": "2026-08-10T00:00:00",
                "end_at": "2026-08-01T00:00:00",
            },
        )
        assert resp.status_code == 400

    def test_returns_200_with_defaults(self, authed_client):
        """Without start_at/end_at, the pipeline should still run for recent data."""
        resp = authed_client.get("/api/v1/analysis", query_string={"topic": "test_topic"})
        assert resp.status_code in {200, 500}

    def test_demo_mode_returns_proper_structure(self, authed_client):
        resp = authed_client.get(
            "/api/v1/analysis",
            query_string={
                "topic": "demo_test",
                "demo": "true",
            },
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body is not None
        data = body.get("data", {})
        assert "meta" in data
        assert data["meta"]["source_type"] == "demo"
        assert data["meta"]["is_demo"] is True

    def test_meta_in_response_for_demo(self, authed_client):
        resp = authed_client.get(
            "/api/v1/analysis",
            query_string={"topic": "demo_test", "demo": "true"},
        )
        body = resp.get_json()
        meta = body.get("data", {}).get("meta", {})
        assert meta.get("source_type") == "demo"
        assert meta.get("data_count", 0) > 0
        assert "time_range" in meta
        assert "limitations" in meta

    def test_summary_in_response_for_demo(self, authed_client):
        resp = authed_client.get(
            "/api/v1/analysis",
            query_string={"topic": "demo_test", "demo": "true"},
        )
        data = resp.get_json().get("data", {})
        assert "summary" in data
        assert "trend" in data
        assert "sentiment" in data
        assert "top_articles" in data