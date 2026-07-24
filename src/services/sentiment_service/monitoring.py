"""缓存与性能统计管理。

拆分自原 ``sentiment_service.py``，逻辑保持不变。
"""

import logging
import time
from typing import Dict

logger = logging.getLogger(__name__)


class _StatsManager:
    """Encapsulates cache and performance statistics."""

    def __init__(self):
        self.cache = {"hits": 0, "misses": 0, "total": 0, "last_reset": time.time()}
        self.performance = {
            "total_requests": 0,
            "total_time": 0,
            "avg_response_time": 0,
            "max_response_time": 0,
            "min_response_time": float('inf'),
            "requests_by_mode": {},
            "time_by_mode": {},
            "last_reset": time.time(),
        }
        self.memory_cache: Dict[str, tuple] = {}

    def record_cache_hit(self):
        self.cache["hits"] += 1
        self.cache["total"] += 1

    def record_cache_miss(self):
        self.cache["misses"] += 1
        self.cache["total"] += 1

    def record_performance(self, processing_time: float, mode: str):
        p = self.performance
        p["total_requests"] += 1
        p["total_time"] += processing_time
        p["avg_response_time"] = p["total_time"] / p["total_requests"]
        p["max_response_time"] = max(p["max_response_time"], processing_time)
        p["min_response_time"] = min(p["min_response_time"], processing_time)
        p["requests_by_mode"].setdefault(mode, 0)
        p["time_by_mode"].setdefault(mode, 0.0)
        p["requests_by_mode"][mode] += 1
        p["time_by_mode"][mode] += processing_time

    def reset_cache(self):
        self.cache = {"hits": 0, "misses": 0, "total": 0, "last_reset": time.time()}
        return self.cache

    def reset_performance(self):
        self.performance = {
            "total_requests": 0, "total_time": 0, "avg_response_time": 0,
            "max_response_time": 0, "min_response_time": float('inf'),
            "requests_by_mode": {}, "time_by_mode": {},
            "last_reset": time.time(),
        }
        return self.performance


_stats = _StatsManager()

MEMORY_CACHE_MAX_SIZE = 10000
MEMORY_CACHE_TTL = 3600


def performance_monitor(func):
    """性能监控装饰器"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        processing_time = (time.time() - start_time) * 1000
        _stats.record_performance(processing_time, kwargs.get('mode', 'simple'))
        return result
    return wrapper


def cleanup_memory_cache():
    """清理过期的内存缓存项"""
    cache = _stats.memory_cache
    now = time.time()
    expired = [k for k, (_, ts) in cache.items() if now - ts > MEMORY_CACHE_TTL]
    for k in expired:
        del cache[k]
    if len(cache) > MEMORY_CACHE_MAX_SIZE:
        oldest = sorted(cache.items(), key=lambda x: x[1][1])
        for k, _ in oldest[:len(cache) - MEMORY_CACHE_MAX_SIZE]:
            del cache[k]
