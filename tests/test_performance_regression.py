#!/usr/bin/env python3
"""#14 回归：SQL LIMIT、情感 memo 复用、限流/LRU 有界、读缓存命中。"""

import pytest

pytestmark = pytest.mark.unit


class TestExportSqlLimit:
    def test_comment_export_bounded(self, alert_db, monkeypatch):
        import repositories.base_repository as _base_repo

        monkeypatch.setattr(_base_repo, "db_session", alert_db)
        from models.comment import Comment
        from repositories.comment_repository import CommentRepository

        for i in range(5):
            alert_db.add(Comment(comment_id=f"c{i}", articleId=f"a{i}", content=f"c{i}"))
        alert_db.commit()
        rows = CommentRepository().get_all_for_export(limit=2)
        assert len(rows) == 2

    def test_user_export_bounded(self, alert_db, monkeypatch):
        import repositories.base_repository as _base_repo

        monkeypatch.setattr(_base_repo, "db_session", alert_db)
        from models.user import User
        from repositories.user_repository import UserRepository

        for i in range(4):
            alert_db.add(User(username=f"u{i}", password="x"))
        alert_db.commit()
        rows = UserRepository().get_all_for_export(limit=3)
        assert len(rows) == 3


class TestSentimentMemo:
    def test_same_input_computes_once(self, monkeypatch):
        from services.sentiment_service import service as svc

        svc._memo_clear()
        calls = []

        def _fake_batch(texts, mode="simple"):
            calls.append((tuple(texts), mode))
            return [{"label": "neutral"} for _ in texts]

        monkeypatch.setattr(
            svc.SentimentService, "analyze_batch", staticmethod(_fake_batch)
        )
        texts = ["今天不错", "有点糟"]
        r1 = svc.SentimentService.analyze_batch_cached(texts, "simple")
        r2 = svc.SentimentService.analyze_batch_cached(texts, "simple")
        assert r1 == r2
        assert len(calls) == 1

    def test_memo_bounded(self, monkeypatch):
        from services.sentiment_service import service as svc

        svc._memo_clear()
        monkeypatch.setattr(
            svc.SentimentService,
            "analyze_batch",
            staticmethod(lambda texts, mode="simple": []),
        )
        for i in range(svc._LOCAL_MEMO_MAX + 20):
            svc.SentimentService.analyze_batch_cached([f"text-{i}"], "simple")
        assert len(svc._LOCAL_MEMO) <= svc._LOCAL_MEMO_MAX


class TestRateLimiterBounded:
    def test_idle_keys_evicted(self):
        import time

        from utils.rate_limiter import RateLimiter

        limiter = RateLimiter()
        limiter._MAX_KEYS = 10
        for i in range(11):
            limiter.is_allowed(f"key-{i}", 100, 60)
        # 全部最近访问，无空闲可驱逐，但数量仍受新 key 触发的上限保护逻辑约束
        assert len(limiter.requests) <= 11
        # 将旧 key 标为空闲后再次触发 → 被驱逐
        old = time.time() - 7200
        for key in list(limiter.requests.keys())[:5]:
            limiter._last_seen[key] = old
        limiter.is_allowed("fresh-key", 100, 60)
        assert "fresh-key" in limiter.requests
        assert len(limiter.requests) <= 11 - 5 + 1 + 1


class TestLruAmortized:
    def test_expired_visible_on_access_and_sweep_amortized(self):
        from utils.cache import LRUCache

        cache = LRUCache(max_size=10, default_ttl=100)
        for i in range(5):
            cache.set(f"k{i}", i)
        for _ in range(10):
            assert cache.get("k0") == 0
        # 未达 64 次扫描阈值且未超容：扫描计数器累积但未触发全量扫描
        assert cache._ops_since_sweep == 10
        assert cache.get("missing") is None


class TestAlertRulesCache:
    def test_get_rules_cached_and_invalidated(self, alert_engine):
        from services import alert_service as mod

        engine = mod.alert_engine
        engine._invalidate_rules_cache()
        first = engine.get_rules()
        second = engine.get_rules()
        assert first is second
        engine._invalidate_rules_cache()
        third = engine.get_rules()
        assert third is not first
        assert third == first


class TestPropagationRepostsCache:
    def test_load_reposts_cached(self, monkeypatch):
        import views.api.propagation_api as m

        m._REPOSTS_CACHE.clear()
        m._REPOSTS_TABLE_MISSING = False
        calls = []

        def _fake_find(self, article_id, limit=100):
            calls.append((article_id, limit))
            return [
                {
                    "id": "r1",
                    "user_id": "u1",
                    "user_name": "n",
                    "content": "c",
                    "post_time": "2026-01-01 10:00:00",
                    "repost_count": 1,
                    "comment_count": 0,
                    "like_count": 0,
                    "depth": 0,
                    "parent_id": None,
                }
            ]

        monkeypatch.setattr(
            m, "_repost_repo", lambda: type("R", (), {"find_with_users": _fake_find})()
        )
        r1 = m._load_reposts("abc123", 100, False)
        r2 = m._load_reposts("abc123", 100, False)
        assert r1 == r2
        assert len(calls) == 1
        m._REPOSTS_CACHE.clear()
        m._REPOSTS_TABLE_MISSING = False
