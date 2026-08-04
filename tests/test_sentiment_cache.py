#!/usr/bin/env python3
"""
sentiment_service/cache.py 单元测试
覆盖范围：
- get_cache_key()（52-62，含 backend 维度 + 长文本截断）
- _build_sentiment_from_cache_data()（65-74）
- get_from_cache()（77-101）：
  * Redis 命中 / Redis 读取异常回退内存 / Redis 未命中回退内存
  * 内存命中 / 内存过期删除 / 内存未命中
  * REDIS_AVAILABLE=False 默认路径
- save_to_cache()（104-126）：
  * Redis 写入成功 / Redis 写入异常仅记录日志
  * 内存缓存超限触发 cleanup_memory_cache
  * 正常写入内存
- 模块导入期 Redis 连接成功（44-45，通过 importlib.reload 模拟）

注意：REDIS_AVAILABLE / redis_client 为模块级全局变量，运行时通过
monkeypatch 替换 cache_module.REDIS_AVAILABLE / redis_client 来覆盖 Redis 分支。
"""

import pytest

pytestmark = pytest.mark.unit

import json
import time
from unittest.mock import MagicMock

import pytest
import redis as redis_lib

from services.sentiment_service import cache as cache_module
from services.sentiment_service.cache import (
    _build_sentiment_from_cache_data,
    get_cache_key,
    get_from_cache,
    save_to_cache,
)
from services.sentiment_service.models import SentimentResult
from services.sentiment_service.monitoring import (
    MEMORY_CACHE_MAX_SIZE,
    MEMORY_CACHE_TTL,
    _stats,
)


@pytest.fixture(autouse=True)
def clear_memory_cache():
    """每个测试前后清空内存缓存，隔离测试"""
    _stats.memory_cache.clear()
    yield
    _stats.memory_cache.clear()


@pytest.fixture
def redis_enabled(monkeypatch):
    """模拟 Redis 可用：返回 fake_client，并设置 REDIS_AVAILABLE=True"""
    fake_client = MagicMock()
    monkeypatch.setattr(cache_module, "REDIS_AVAILABLE", True)
    monkeypatch.setattr(cache_module, "redis_client", fake_client)
    return fake_client


def _make_result(score=0.8, label="positive"):
    """构造 SentimentResult"""
    return SentimentResult(
        score=score,
        label=label,
        reasoning="测试推理",
        emotion="joy",
        keywords=["关键词"],
    )


# ----------------------------------------------------------------------
# get_cache_key
# ----------------------------------------------------------------------


class TestGetCacheKey:
    """测试 get_cache_key()（52-62）"""

    def test_deterministic(self):
        """相同输入应产生相同 key"""
        assert get_cache_key("text", "simple", "bert") == get_cache_key(
            "text", "simple", "bert"
        )

    def test_different_backend_different_key(self):
        """不同 backend 应产生不同 key（Phase 3 v4 设计）"""
        assert get_cache_key("text", "simple", "bert") != get_cache_key(
            "text", "simple", "sklearn"
        )

    def test_different_mode_different_key(self):
        assert get_cache_key("text", "simple") != get_cache_key("text", "detailed")

    def test_different_text_different_key(self):
        assert get_cache_key("text1", "simple") != get_cache_key("text2", "simple")

    def test_default_backend(self):
        """backend 默认为 'default'"""
        assert get_cache_key("text", "simple") == get_cache_key(
            "text", "simple", "default"
        )

    def test_long_text_truncation(self):
        """超过 1000 字符的文本应被截断，相同前缀产生相同 key"""
        short = "A" * 1000
        long_text = "A" * 1000 + "B" * 500
        assert get_cache_key(short, "simple") == get_cache_key(long_text, "simple")

    def test_returns_md5_hex(self):
        key = get_cache_key("text", "simple")
        assert len(key) == 32
        assert all(c in "0123456789abcdef" for c in key)


# ----------------------------------------------------------------------
# _build_sentiment_from_cache_data
# ----------------------------------------------------------------------


class TestBuildSentimentFromCacheData:
    """测试 _build_sentiment_from_cache_data()（65-74）"""

    def test_full_data(self):
        data = {
            "score": 0.9,
            "label": "positive",
            "reasoning": "推理",
            "emotion": "joy",
            "keywords": ["k1", "k2"],
        }
        result = _build_sentiment_from_cache_data(data, "cache_redis")
        assert result.score == 0.9
        assert result.label == "positive"
        assert result.reasoning == "推理"
        assert result.emotion == "joy"
        assert result.keywords == ["k1", "k2"]
        assert result.cached is True
        assert result.source == "cache_redis"

    def test_empty_dict_defaults(self):
        result = _build_sentiment_from_cache_data({}, "cache_memory")
        assert result.score == 0.5
        assert result.label == "neutral"
        assert result.reasoning is None
        assert result.emotion is None
        assert result.keywords == []
        assert result.cached is True
        assert result.source == "cache_memory"


# ----------------------------------------------------------------------
# get_from_cache
# ----------------------------------------------------------------------


class TestGetFromCache:
    """测试 get_from_cache()（77-101）"""

    def test_redis_hit(self, redis_enabled):
        """Redis 命中应返回 cache_redis 来源（84-88）"""
        data = {
            "score": 0.8,
            "label": "positive",
            "reasoning": "r",
            "emotion": "joy",
            "keywords": ["k"],
        }
        redis_enabled.get.return_value = json.dumps(data).encode()

        result = get_from_cache("text", "simple", "bert")
        assert result is not None
        assert result.source == "cache_redis"
        assert result.cached is True
        assert result.score == 0.8
        assert result.label == "positive"
        redis_enabled.get.assert_called_once_with(get_cache_key("text", "simple", "bert"))

    def test_redis_read_failure_falls_to_memory(self, monkeypatch):
        """Redis 读取异常应回退到内存缓存（89-90）"""
        # 先以 Redis 不可用方式写入内存
        save_to_cache("text1", "simple", _make_result(), "default")
        assert get_cache_key("text1", "simple", "default") in _stats.memory_cache

        # 启用 Redis 但 get 抛异常
        fake_client = MagicMock()
        fake_client.get.side_effect = redis_lib.RedisError("conn lost")
        monkeypatch.setattr(cache_module, "REDIS_AVAILABLE", True)
        monkeypatch.setattr(cache_module, "redis_client", fake_client)

        result = get_from_cache("text1", "simple", "default")
        assert result is not None
        assert result.source == "cache_memory"

    def test_redis_miss_falls_to_memory(self, redis_enabled):
        """Redis 未命中（返回 None）应回退到内存缓存"""
        redis_enabled.get.return_value = None

        # 存入内存（此时 REDIS_AVAILABLE=True，也会写 Redis，但 fake_client 接受）
        save_to_cache("text2", "simple", _make_result(), "default")

        result = get_from_cache("text2", "simple", "default")
        assert result is not None
        assert result.source == "cache_memory"

    def test_memory_hit(self):
        """内存缓存命中应返回 cache_memory 来源（93-97）"""
        save_to_cache("text3", "simple", _make_result(), "default")

        result = get_from_cache("text3", "simple", "default")
        assert result is not None
        assert result.source == "cache_memory"
        assert result.cached is True

    def test_memory_expired_deleted(self):
        """内存缓存过期应被删除并返回 None（98）"""
        save_to_cache("text4", "simple", _make_result(), "default")
        key = get_cache_key("text4", "simple", "default")
        # 手动将时间戳置为过期
        data, _ = _stats.memory_cache[key]
        _stats.memory_cache[key] = (data, time.time() - MEMORY_CACHE_TTL - 1)

        result = get_from_cache("text4", "simple", "default")
        assert result is None  # 未命中
        assert key not in _stats.memory_cache  # 已被删除

    def test_memory_miss(self):
        """内存与 Redis 均未命中应返回 None 并记录 miss（100）"""
        result = get_from_cache("nonexistent", "simple", "default")
        assert result is None

    def test_redis_hit_takes_precedence_over_memory(self, redis_enabled):
        """Redis 命中时不应再查内存"""
        # 同时存入内存
        save_to_cache("text5", "simple", _make_result(), "default")
        # Redis 返回不同的数据
        redis_data = {"score": 0.1, "label": "negative"}
        redis_enabled.get.return_value = json.dumps(redis_data).encode()

        result = get_from_cache("text5", "simple", "default")
        assert result.source == "cache_redis"
        assert result.score == 0.1


# ----------------------------------------------------------------------
# save_to_cache
# ----------------------------------------------------------------------


class TestSaveToCache:
    """测试 save_to_cache()（104-126）"""

    def test_redis_write_success(self, redis_enabled):
        """Redis 可用时应调用 setex 写入（118-119）"""
        save_to_cache("text1", "simple", _make_result(), "bert")
        redis_enabled.setex.assert_called_once()
        args = redis_enabled.setex.call_args[0]
        assert args[0] == get_cache_key("text1", "simple", "bert")
        assert args[1] == cache_module.Config.LLM_CACHE_TTL
        # 同时写入内存
        assert get_cache_key("text1", "simple", "bert") in _stats.memory_cache

    def test_redis_write_failure_logged(self, monkeypatch):
        """Redis 写入异常应仅记录日志，不影响内存写入（120-121）"""
        fake_client = MagicMock()
        fake_client.setex.side_effect = redis_lib.RedisError("write fail")
        monkeypatch.setattr(cache_module, "REDIS_AVAILABLE", True)
        monkeypatch.setattr(cache_module, "redis_client", fake_client)

        # 不应抛异常
        save_to_cache("text2", "simple", _make_result(), "default")
        # 仍写入内存
        assert get_cache_key("text2", "simple", "default") in _stats.memory_cache

    def test_memory_write_only_when_redis_disabled(self):
        """Redis 不可用时仅写入内存"""
        save_to_cache("text3", "simple", _make_result(), "default")
        key = get_cache_key("text3", "simple", "default")
        assert key in _stats.memory_cache
        data, ts = _stats.memory_cache[key]
        assert data["score"] == 0.8
        assert data["label"] == "positive"
        assert data["keywords"] == ["关键词"]

    def test_triggers_cleanup_when_full(self, monkeypatch):
        """内存缓存超限应触发 cleanup_memory_cache（124-125）"""
        called = {"count": 0}
        original_cleanup = cache_module.cleanup_memory_cache

        def spy_cleanup():
            called["count"] += 1
            original_cleanup()

        monkeypatch.setattr(cache_module, "cleanup_memory_cache", spy_cleanup)

        # 预填到超限（MEMORY_CACHE_MAX_SIZE + 1 个条目）
        for i in range(MEMORY_CACHE_MAX_SIZE + 1):
            _stats.memory_cache[f"prekey_{i}"] = ({"score": 0.5}, time.time())

        # 此时 len > MAX_SIZE，save 应触发 cleanup
        save_to_cache("new_text", "simple", _make_result(), "default")
        assert called["count"] >= 1

    def test_no_cleanup_when_under_limit(self, monkeypatch):
        """内存缓存未超限时不应触发 cleanup"""
        called = {"count": 0}
        monkeypatch.setattr(
            cache_module,
            "cleanup_memory_cache",
            lambda: called.__setitem__("count", called["count"] + 1),
        )

        save_to_cache("text4", "simple", _make_result(), "default")
        assert called["count"] == 0


# ----------------------------------------------------------------------
# 模块导入期 Redis 连接成功
# ----------------------------------------------------------------------


class TestModuleImportRedis:
    """测试模块导入期 Redis 连接成功路径（44-45）"""

    def test_redis_available_at_import(self, monkeypatch):
        """模拟 Redis 连接成功，模块应设置 REDIS_AVAILABLE=True"""
        import importlib

        from services.sentiment_service import cache as cache_mod

        fake_client = MagicMock()
        fake_client.ping.return_value = True
        monkeypatch.setattr(cache_mod.redis, "Redis", MagicMock(return_value=fake_client))

        try:
            importlib.reload(cache_mod)
            assert cache_mod.REDIS_AVAILABLE is True
            assert cache_mod.redis_client is fake_client
        finally:
            # 恢复：还原 redis.Redis 并重置模块全局为无 Redis 状态
            monkeypatch.undo()
            cache_mod.REDIS_AVAILABLE = False
            cache_mod.redis_client = None
