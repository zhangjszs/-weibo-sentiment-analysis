#!/usr/bin/env python3
"""#12 回归：统一错误契约（JSON 非 HTML）、大屏无静默伪造、空表/方言/静默注册修复。"""

import pytest

pytestmark = pytest.mark.api


class TestDataApiDbErrorIsJson:
    """data_api DB 异常 → 统一 error JSON（code 500），而非 Flask 500 HTML。"""

    def test_home_db_error_returns_json(self, authed_client, monkeypatch):
        from sqlalchemy.exc import SQLAlchemyError

        import views.data.data_api as data_api

        def _boom():
            raise SQLAlchemyError("db gone")

        monkeypatch.setattr(data_api.getHomeData, "getHomeTopLikeCommentsData", _boom)
        monkeypatch.setattr(data_api, "get_cached_data", lambda k, t: None)

        resp = authed_client.get("/api/getHomeData")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data is not None, "必须返回 JSON 而非 HTML"
        assert data.get("code") == 500


class TestBigscreenNoSilentFake:
    """缺失返回空；仅 ?demo=true 显式请求才给模拟数据。"""

    def test_region_empty_without_demo(self, authed_client, monkeypatch):
        import views.api.bigscreen_api as m

        monkeypatch.setattr(m, "_article_repo", lambda: type("R", (), {"get_region_distribution": lambda self: []})())
        resp = authed_client.get("/api/bigscreen/region")
        assert resp.status_code == 200
        body = resp.get_json()["data"]
        assert body["data"] == []
        assert body["demo_mode"] is False

    def test_region_demo_when_requested(self, authed_client, monkeypatch):
        import views.api.bigscreen_api as m

        monkeypatch.setattr(m, "_article_repo", lambda: type("R", (), {"get_region_distribution": lambda self: []})())
        resp = authed_client.get("/api/bigscreen/region?demo=true")
        assert resp.status_code == 200
        body = resp.get_json()["data"]
        assert body["data"], "显式 demo 应返回模拟数据"
        assert body["demo_mode"] is True
        assert any(r["name"] == "北京" for r in body["data"])

    def test_hot_topics_and_alerts_empty(self, authed_client, monkeypatch):
        import views.api.bigscreen_api as m

        monkeypatch.setattr(m, "_get_hot_topics", lambda limit=10: [])
        monkeypatch.setattr(m, "_get_recent_alerts", lambda limit=5: [])
        resp = authed_client.get("/api/bigscreen/hot-topics")
        assert resp.get_json()["data"]["topics"] == []
        resp = authed_client.get("/api/bigscreen/alerts")
        assert resp.get_json()["data"]["alerts"] == []
        # 未显式 demo 时不得出现硬编码伪造
        flat = resp.get_data(as_text=True)
        assert "科技创新" not in flat and "负面舆情激增" not in flat

    def test_sentiment_failure_returns_zeros(self, monkeypatch):
        import views.api.bigscreen_api as m

        def _boom():
            raise RuntimeError("db down")

        monkeypatch.setattr(
            m, "_comment_repo", lambda: type("R", (), {"get_recent_texts": lambda self, **k: _boom()})()
        )
        dist = m._get_sentiment_distribution()
        assert dist == {"positive": 0, "neutral": 0, "negative": 0}


class TestApiInitLoudFailure:
    def test_register_api_does_not_silently_skip(self):
        import pathlib

        src = pathlib.Path("src/views/api/__init__.py").read_text(encoding="utf-8")
        block = src.split("from views.data.data_api import db as data_bp")[1].split(
            "blueprints = ["
        )[0]
        assert "except Exception" not in block, "数据蓝图导入失败禁止裸 except 静默跳过"
        assert "except ImportError" in block
