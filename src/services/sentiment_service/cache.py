"""Redis 与内存缓存读写。

拆分自原 ``sentiment_service.py``，逻辑保持不变。

注意：``REDIS_AVAILABLE`` / ``redis_client`` 定义在本模块。需要使其可被
``monkeypatch`` 替换的调用方（如 ``service.analyze_distribution``）应通过
属性访问（``_cache.REDIS_AVAILABLE``）而非 ``from .cache import REDIS_AVAILABLE``，
后者会在导入时绑定快照、无法被后续 patch 影响。
"""

import hashlib
import json
import logging
import time
from typing import Optional

from config.settings import Config

from .monitoring import (
    _stats,
    cleanup_memory_cache,
    MEMORY_CACHE_MAX_SIZE,
    MEMORY_CACHE_TTL,
)
from .models import SentimentResult

logger = logging.getLogger(__name__)

# 尝试导入Redis（可选依赖）
try:
    import redis
    from redis.backoff import NoBackoff
    from redis.retry import Retry

    redis_params = Config.get_redis_connection_params()
    redis_params.update(
        {
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
            "health_check_interval": 30,
            # redis-py 8.0 默认 retry=10 次（ExponentialWithJitterBackoff），
            # Redis 不可用时 ping() 会重试 10 轮，叠加 Windows TCP 拒绝连接
            # 的 ~2s 延迟，导入阶段即阻塞 ~20s，拖垮测试套件。缓存层应
            # fail-fast 退回内存缓存，而非反复重试。
            "retry": Retry(NoBackoff(), 0),
        }
    )
    redis_client = redis.Redis(**redis_params)
    # 测试连接
    redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("Redis缓存已启用")
except (redis.RedisError, OSError) as e:
    logger.warning(f"Redis连接失败，将使用内存缓存: {e}")
    redis_client = None
    REDIS_AVAILABLE = False


def get_cache_key(text: str, mode: str, backend: str = "default") -> str:
    """生成缓存键。

    Phase 3 起改为 ``sentiment:v4:{backend}:{mode}:{text}``，把 backend 维度
    纳入 key 以避免 BERT/sklearn/snownlp 互相污染缓存（旧 v3 缓存自然失效）。
    """
    # 限制文本长度，避免缓存键过长
    max_text_length = 1000
    truncated_text = text[:max_text_length]
    key_data = f"sentiment:v4:{backend}:{mode}:{truncated_text}"
    return hashlib.md5(key_data.encode()).hexdigest()


def _build_sentiment_from_cache_data(data: dict, source: str) -> SentimentResult:
    return SentimentResult(
        score=data.get("score", 0.5),
        label=data.get("label", "neutral"),
        reasoning=data.get("reasoning"),
        emotion=data.get("emotion"),
        keywords=data.get("keywords", []),
        cached=True,
        source=source,
    )


def get_from_cache(
    text: str, mode: str, backend: str = "default"
) -> Optional[SentimentResult]:
    """从缓存获取结果"""
    cache_key = get_cache_key(text, mode, backend)

    if REDIS_AVAILABLE:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                _stats.record_cache_hit()
                return _build_sentiment_from_cache_data(json.loads(cached), "cache_redis")
        except (redis.RedisError, json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Redis缓存读取失败: {e}")

    cache = _stats.memory_cache
    if cache_key in cache:
        data, timestamp = cache[cache_key]
        if time.time() - timestamp < MEMORY_CACHE_TTL:
            _stats.record_cache_hit()
            return _build_sentiment_from_cache_data(data, "cache_memory")
        del cache[cache_key]

    _stats.record_cache_miss()
    return None


def save_to_cache(
    text: str, mode: str, result: SentimentResult, backend: str = "default"
) -> None:
    """保存结果到缓存"""
    cache_key = get_cache_key(text, mode, backend)
    data = {
        "score": result.score,
        "label": result.label,
        "reasoning": result.reasoning,
        "emotion": result.emotion,
        "keywords": result.keywords,
    }

    if REDIS_AVAILABLE:
        try:
            redis_client.setex(cache_key, Config.LLM_CACHE_TTL, json.dumps(data))
        except (redis.RedisError, TypeError) as e:
            logger.warning(f"Redis缓存写入失败: {e}")

    cache = _stats.memory_cache
    if len(cache) > MEMORY_CACHE_MAX_SIZE:
        cleanup_memory_cache()
    cache[cache_key] = (data, time.time())
