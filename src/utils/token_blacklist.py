#!/usr/bin/env python3
"""JWT jti 黑名单：logout 作废与会话旋转的撤销存储（#15）。

存储选择（懒初始化）：
- 优先 Redis（多 worker 共享，gunicorn -w 2 下撤销跨进程生效）；
- Redis 不可用时退化为进程内 LRU（``utils.cache.memory_cache``），
  撤销仅在当前进程生效——开发/单进程部署可用，多 worker 有半失效窗口，
  部署侧应保证 Redis 可用。
"""

import logging
import threading

from config.settings import Config

logger = logging.getLogger(__name__)

try:
    import redis as _redis_lib
except ImportError:  # pragma: no cover - redis 是主依赖，缺失仅见于裁剪环境
    _redis_lib = None

_KEY_PREFIX = "jwt:revoked:"

_client = None
_client_checked = False
_init_lock = threading.Lock()


def _get_client():
    """懒建 Redis 连接；失败置 None 并记住，避免每个请求重复重连。"""
    global _client, _client_checked
    if _client_checked:
        return _client
    with _init_lock:
        if _client_checked:
            return _client
        _client_checked = True
        if _redis_lib is not None:
            try:
                client = _redis_lib.Redis(**Config.get_redis_connection_params())
                client.ping()
                _client = client
            except Exception as e:
                logger.warning("Redis 不可用，jti 黑名单退化为进程内存: %s", e)
                _client = None
    return _client


def revoke_jti(jti: str, ttl_seconds: int) -> bool:
    """把 jti 加入黑名单，TTL 与 token 剩余寿命对齐。"""
    if not jti:
        return False
    ttl = max(int(ttl_seconds), 1)
    client = _get_client()
    if client is not None:
        try:
            client.setex(f"{_KEY_PREFIX}{jti}", ttl, "1")
            return True
        except Exception as e:
            logger.warning("jti 黑名单写入 Redis 失败，退化内存: %s", e)
    from utils.cache import memory_cache

    memory_cache.set(f"{_KEY_PREFIX}{jti}", True, ttl=ttl)
    return True


def is_jti_revoked(jti: str) -> bool:
    """jti 是否已被撤销。存储不可用时宁可放行（与无撤销等价），不放大故障。"""
    if not jti:
        return False
    client = _get_client()
    if client is not None:
        try:
            return bool(client.exists(f"{_KEY_PREFIX}{jti}"))
        except Exception as e:
            logger.warning("jti 黑名单查询 Redis 失败，退化内存: %s", e)
    from utils.cache import memory_cache

    return bool(memory_cache.get(f"{_KEY_PREFIX}{jti}"))
