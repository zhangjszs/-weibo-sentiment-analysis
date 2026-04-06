"""
高性能缓存系统模块
功能：提供内存缓存和文件缓存两套机制，显著提升系统性能
特性：LRU算法、过期机制、序列化存储、线程安全、性能监控
"""

import hashlib
import json
import logging
import os
import threading
import time
from collections import OrderedDict
from functools import wraps

logger = logging.getLogger(__name__)


class LRUCache:
    """
    基于LRU(Least Recently Used)算法的内存缓存
    自动淘汰最久未使用的缓存项，防止内存溢出
    """

    def __init__(self, max_size=1000, default_ttl=300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.expire_times = {}
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.start_time = time.time()

    def _is_expired(self, key):
        if key not in self.expire_times:
            return True
        return time.time() > self.expire_times[key]

    def _evict_expired(self):
        current_time = time.time()
        expired_keys = [
            key
            for key, expire_time in self.expire_times.items()
            if current_time > expire_time
        ]
        for key in expired_keys:
            self._remove_item(key)

    def _remove_item(self, key):
        if key in self.cache:
            del self.cache[key]
        if key in self.expire_times:
            del self.expire_times[key]

    def _evict_lru(self):
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            self._remove_item(oldest_key)
            self.evictions += 1

    def get(self, key, default=None):
        with self.lock:
            self._evict_expired()
            if key in self.cache and not self._is_expired(key):
                value = self.cache.pop(key)
                self.cache[key] = value
                self.hits += 1
                return value
            else:
                self.misses += 1
                if key in self.cache:
                    self._remove_item(key)
                return default

    def set(self, key, value, ttl=None):
        with self.lock:
            ttl = ttl or self.default_ttl
            expire_time = time.time() + ttl
            if key in self.cache:
                self._remove_item(key)
            self._evict_lru()
            self.cache[key] = value
            self.expire_times[key] = expire_time

    def delete(self, key):
        with self.lock:
            if key in self.cache:
                self._remove_item(key)
                return True
            return False

    def clear(self):
        with self.lock:
            self.cache.clear()
            self.expire_times.clear()
            logger.info("清空所有内存缓存")

    def size(self):
        with self.lock:
            self._evict_expired()
            return len(self.cache)

    def get_stats(self):
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / max(total_requests, 1)) * 100
            uptime = time.time() - self.start_time
            return {
                "type": "LRU Memory Cache",
                "max_size": self.max_size,
                "current_size": len(self.cache),
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.2f}%",
                "evictions": self.evictions,
                "uptime_hours": uptime / 3600,
                "requests_per_second": total_requests / max(uptime, 1),
            }


class FileCache:
    """文件缓存类"""

    def __init__(self, cache_dir="./cache", default_timeout=3600):
        self.cache_dir = cache_dir
        self.default_timeout = default_timeout
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def _get_cache_path(self, key):
        return os.path.join(self.cache_dir, f"{key}.cache")

    def get(self, key):
        cache_path = self._get_cache_path(key)
        if os.path.exists(cache_path):
            if time.time() - os.path.getmtime(cache_path) < self.default_timeout:
                try:
                    with open(cache_path, encoding="utf-8") as f:
                        payload = json.load(f)
                    if isinstance(payload, dict) and "data" in payload:
                        return payload["data"]
                    return payload
                except (json.JSONDecodeError, OSError, ValueError, TypeError):
                    os.remove(cache_path)
            else:
                os.remove(cache_path)
        return None

    def set(self, key, value):
        cache_path = self._get_cache_path(key)
        temp_path = f"{cache_path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump({"data": value}, f, ensure_ascii=False, default=str)
            os.replace(temp_path, cache_path)
        except Exception as e:
            logger.error(f"缓存写入失败: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def clear(self):
        for filename in os.listdir(self.cache_dir):
            if filename.endswith(".cache"):
                os.remove(os.path.join(self.cache_dir, filename))


memory_cache = LRUCache(max_size=1000, default_ttl=300)
file_cache = FileCache(default_timeout=1800)


def cache_result(ttl=300, timeout=None, use_file_cache=False, key_func=None):
    """
    缓存装饰器
    自动缓存函数结果，提升性能

    Args:
        ttl: 缓存时间（秒）
        timeout: 缓存时间（秒），兼容旧参数名
        use_file_cache: 是否使用文件缓存
        key_func: 自定义键生成函数

    Returns:
        装饰器函数
    """
    if timeout is not None:
        ttl = timeout

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5("_".join(key_parts).encode()).hexdigest()

            result = memory_cache.get(cache_key)
            if result is not None:
                return result

            if use_file_cache:
                result = file_cache.get(cache_key)
                if result is not None:
                    memory_cache.set(cache_key, result, ttl)
                    return result

            result = func(*args, **kwargs)

            memory_cache.set(cache_key, result, ttl)
            if use_file_cache:
                file_cache.set(cache_key, result)

            return result

        return wrapper

    return decorator


def clear_all_cache():
    """清空所有缓存"""
    memory_cache.clear()
    file_cache.clear()
    logger.info("所有缓存已清空")


def get_cache_info():
    """获取缓存信息"""
    return {
        "memory_cache_size": memory_cache.size(),
        "memory_cache_stats": memory_cache.get_stats(),
        "file_cache_dir": file_cache.cache_dir,
        "file_cache_count": len(
            [f for f in os.listdir(file_cache.cache_dir) if f.endswith(".cache")]
        ),
    }


__all__ = [
    "LRUCache",
    "FileCache",
    "memory_cache",
    "file_cache",
    "cache_result",
    "clear_all_cache",
    "get_cache_info",
]
