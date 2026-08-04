#!/usr/bin/env python3
"""
sentiment_service/monitoring.py 单元测试
覆盖范围：
- _StatsManager.__init__（16-28）
- record_cache_hit / record_cache_miss（30-36）
- record_performance（38-48）：单次/多次/多模式累加、avg/max/min 更新
- reset_cache（50-52）：重置后归零并返回 dict
- reset_performance（54-61）：重置为默认值并返回 dict
- performance_monitor 装饰器（70-78）：记录耗时、默认 mode='simple'、显式 mode
- cleanup_memory_cache（81-91）：过期删除、新鲜保留、未超限不删、超限删最旧
"""

import pytest

pytestmark = pytest.mark.unit

import time

import pytest

from services.sentiment_service.monitoring import (
    MEMORY_CACHE_MAX_SIZE,
    MEMORY_CACHE_TTL,
    _stats,
    _StatsManager,
    cleanup_memory_cache,
    performance_monitor,
)


@pytest.fixture(autouse=True)
def reset_stats():
    """每个测试前后重置 _stats 状态，隔离测试"""
    _stats.reset_cache()
    _stats.reset_performance()
    _stats.memory_cache.clear()
    yield
    _stats.reset_cache()
    _stats.reset_performance()
    _stats.memory_cache.clear()


# ----------------------------------------------------------------------
# _StatsManager.__init__
# ----------------------------------------------------------------------


class TestStatsManagerInit:
    """测试 __init__（16-28）"""

    def test_initial_cache_state(self):
        m = _StatsManager()
        assert m.cache["hits"] == 0
        assert m.cache["misses"] == 0
        assert m.cache["total"] == 0
        assert "last_reset" in m.cache

    def test_initial_performance_state(self):
        m = _StatsManager()
        p = m.performance
        assert p["total_requests"] == 0
        assert p["total_time"] == 0
        assert p["avg_response_time"] == 0
        assert p["max_response_time"] == 0
        assert p["min_response_time"] == float("inf")
        assert p["requests_by_mode"] == {}
        assert p["time_by_mode"] == {}

    def test_initial_memory_cache_empty(self):
        m = _StatsManager()
        assert m.memory_cache == {}


# ----------------------------------------------------------------------
# record_cache_hit / record_cache_miss
# ----------------------------------------------------------------------


class TestRecordCache:
    """测试 record_cache_hit / record_cache_miss（30-36）"""

    def test_record_hit(self):
        _stats.record_cache_hit()
        assert _stats.cache["hits"] == 1
        assert _stats.cache["total"] == 1
        assert _stats.cache["misses"] == 0

    def test_record_miss(self):
        _stats.record_cache_miss()
        assert _stats.cache["misses"] == 1
        assert _stats.cache["total"] == 1
        assert _stats.cache["hits"] == 0

    def test_mixed_hits_misses(self):
        _stats.record_cache_hit()
        _stats.record_cache_hit()
        _stats.record_cache_miss()
        assert _stats.cache["hits"] == 2
        assert _stats.cache["misses"] == 1
        assert _stats.cache["total"] == 3


# ----------------------------------------------------------------------
# record_performance
# ----------------------------------------------------------------------


class TestRecordPerformance:
    """测试 record_performance（38-48）"""

    def test_single_call(self):
        _stats.record_performance(10.0, "simple")
        p = _stats.performance
        assert p["total_requests"] == 1
        assert p["total_time"] == 10.0
        assert p["avg_response_time"] == 10.0
        assert p["max_response_time"] == 10.0
        assert p["min_response_time"] == 10.0
        assert p["requests_by_mode"] == {"simple": 1}
        assert p["time_by_mode"] == {"simple": 10.0}

    def test_multiple_calls_avg(self):
        """多次调用应正确计算平均值"""
        _stats.record_performance(10.0, "simple")
        _stats.record_performance(30.0, "simple")
        p = _stats.performance
        assert p["total_requests"] == 2
        assert p["total_time"] == 40.0
        assert p["avg_response_time"] == 20.0
        assert p["max_response_time"] == 30.0
        assert p["min_response_time"] == 10.0

    def test_max_min_tracking(self):
        _stats.record_performance(5.0, "simple")
        _stats.record_performance(100.0, "simple")
        _stats.record_performance(50.0, "simple")
        p = _stats.performance
        assert p["max_response_time"] == 100.0
        assert p["min_response_time"] == 5.0

    def test_multiple_modes_accumulate_separately(self):
        """不同模式应分别累计"""
        _stats.record_performance(10.0, "simple")
        _stats.record_performance(20.0, "detailed")
        _stats.record_performance(30.0, "simple")
        p = _stats.performance
        assert p["requests_by_mode"] == {"simple": 2, "detailed": 1}
        assert p["time_by_mode"] == {"simple": 40.0, "detailed": 20.0}

    def test_repeated_mode_uses_setdefault_then_increment(self):
        """同一模式多次调用应正确累加（setdefault 不覆盖已有值）"""
        _stats.record_performance(10.0, "bert")
        _stats.record_performance(15.0, "bert")
        p = _stats.performance
        assert p["requests_by_mode"]["bert"] == 2
        assert p["time_by_mode"]["bert"] == 25.0


# ----------------------------------------------------------------------
# reset_cache
# ----------------------------------------------------------------------


class TestResetCache:
    """测试 reset_cache（50-52）"""

    def test_reset_clears_counters(self):
        _stats.record_cache_hit()
        _stats.record_cache_hit()
        _stats.record_cache_miss()

        result = _stats.reset_cache()
        assert _stats.cache["hits"] == 0
        assert _stats.cache["misses"] == 0
        assert _stats.cache["total"] == 0
        assert "last_reset" in _stats.cache

    def test_reset_returns_cache_dict(self):
        result = _stats.reset_cache()
        assert result is _stats.cache
        assert result["hits"] == 0

    def test_reset_updates_last_reset(self):
        old_reset = _stats.cache["last_reset"]
        time.sleep(0.01)
        _stats.reset_cache()
        assert _stats.cache["last_reset"] > old_reset


# ----------------------------------------------------------------------
# reset_performance
# ----------------------------------------------------------------------


class TestResetPerformance:
    """测试 reset_performance（54-61）"""

    def test_reset_clears_performance(self):
        _stats.record_performance(10.0, "simple")
        _stats.record_performance(20.0, "detailed")

        result = _stats.reset_performance()
        p = _stats.performance
        assert p["total_requests"] == 0
        assert p["total_time"] == 0
        assert p["avg_response_time"] == 0
        assert p["max_response_time"] == 0
        assert p["min_response_time"] == float("inf")
        assert p["requests_by_mode"] == {}
        assert p["time_by_mode"] == {}

    def test_reset_returns_performance_dict(self):
        result = _stats.reset_performance()
        assert result is _stats.performance

    def test_reset_updates_last_reset(self):
        old_reset = _stats.performance["last_reset"]
        time.sleep(0.01)
        _stats.reset_performance()
        assert _stats.performance["last_reset"] > old_reset


# ----------------------------------------------------------------------
# performance_monitor 装饰器
# ----------------------------------------------------------------------


class TestPerformanceMonitor:
    """测试 performance_monitor 装饰器（70-78）"""

    def test_decorator_returns_result(self):
        @performance_monitor
        def sample(**kwargs):
            return "ok"

        assert sample(mode="simple") == "ok"

    def test_decorator_records_performance(self):
        @performance_monitor
        def sample(**kwargs):
            return "ok"

        _stats.reset_performance()
        sample(mode="detailed")
        p = _stats.performance
        assert p["total_requests"] == 1
        assert p["requests_by_mode"]["detailed"] == 1
        assert p["time_by_mode"]["detailed"] >= 0
        assert p["max_response_time"] >= 0

    def test_decorator_default_mode_simple(self):
        """未传 mode 时默认 'simple'（76 kwargs.get('mode', 'simple')）"""
        @performance_monitor
        def sample(**kwargs):
            return "ok"

        _stats.reset_performance()
        sample()  # 无 mode 参数
        assert _stats.performance["requests_by_mode"]["simple"] == 1

    def test_decorator_multiple_calls_accumulate(self):
        @performance_monitor
        def sample(**kwargs):
            return "ok"

        _stats.reset_performance()
        sample(mode="simple")
        sample(mode="simple")
        sample(mode="bert")
        p = _stats.performance
        assert p["total_requests"] == 3
        assert p["requests_by_mode"]["simple"] == 2
        assert p["requests_by_mode"]["bert"] == 1

    def test_decorator_preserves_args(self):
        """装饰器应透传位置参数与关键字参数"""
        @performance_monitor
        def add(a, b, *, mode="simple"):
            return a + b

        assert add(2, 3, mode="simple") == 5


# ----------------------------------------------------------------------
# cleanup_memory_cache
# ----------------------------------------------------------------------


class TestCleanupMemoryCache:
    """测试 cleanup_memory_cache（81-91）"""

    def test_removes_expired_entries(self):
        """过期条目应被删除（87）"""
        _stats.memory_cache["fresh"] = ({"data"}, time.time())
        _stats.memory_cache["expired1"] = ({"data"}, time.time() - MEMORY_CACHE_TTL - 1)
        _stats.memory_cache["expired2"] = ({"data"}, time.time() - MEMORY_CACHE_TTL - 100)

        cleanup_memory_cache()
        assert "fresh" in _stats.memory_cache
        assert "expired1" not in _stats.memory_cache
        assert "expired2" not in _stats.memory_cache

    def test_keeps_fresh_entries(self):
        """未过期条目应保留"""
        now = time.time()
        _stats.memory_cache["k1"] = ({"data"}, now)
        _stats.memory_cache["k2"] = ({"data"}, now - 10)
        _stats.memory_cache["k3"] = ({"data"}, now - 100)

        cleanup_memory_cache()
        assert len(_stats.memory_cache) == 3

    def test_under_limit_no_removal(self):
        """未超限时不删除条目（覆盖 88->exit False 分支）"""
        _stats.memory_cache["k1"] = ({"data"}, time.time())
        _stats.memory_cache["k2"] = ({"data"}, time.time())

        cleanup_memory_cache()
        assert len(_stats.memory_cache) == 2

    def test_empty_cache_noop(self):
        """空缓存调用应无异常"""
        cleanup_memory_cache()
        assert _stats.memory_cache == {}

    def test_over_limit_removes_oldest(self):
        """超限时应删除最旧的条目直到等于 MAX_SIZE（88-91）"""
        base = time.time()
        # 填充到 MAX_SIZE + 2，时间戳递增（k_0 最旧）
        for i in range(MEMORY_CACHE_MAX_SIZE + 2):
            _stats.memory_cache[f"k_{i}"] = ({"data"}, base + i)

        cleanup_memory_cache()
        assert len(_stats.memory_cache) == MEMORY_CACHE_MAX_SIZE
        # 最旧的两个被删除
        assert "k_0" not in _stats.memory_cache
        assert "k_1" not in _stats.memory_cache
        # 最新的保留
        assert f"k_{MEMORY_CACHE_MAX_SIZE + 1}" in _stats.memory_cache

    def test_expired_and_overflow_combined(self):
        """同时存在过期与超限时，先删过期再处理超限"""
        base = time.time()
        # 全部超限，其中前两个已过期
        for i in range(MEMORY_CACHE_MAX_SIZE + 2):
            ts = base - MEMORY_CACHE_TTL - 1 if i < 2 else base + i
            _stats.memory_cache[f"k_{i}"] = ({"data"}, ts)

        cleanup_memory_cache()
        # 过期的 2 个先被删，剩 MAX_SIZE 个，正好等于上限不再删
        assert len(_stats.memory_cache) == MEMORY_CACHE_MAX_SIZE
        assert "k_0" not in _stats.memory_cache
        assert "k_1" not in _stats.memory_cache


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
