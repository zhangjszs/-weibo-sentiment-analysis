#!/usr/bin/env python3
"""登录失败锁定（#15）：同一 username+IP 连续失败达阈值后临时锁定。

存储用 ``utils.cache.memory_cache``（进程内 LRU，带 TTL）：开发/单进程足够；
多 worker 部署计数分散在各进程，锁定强度按 worker 数稀释——与 jti 黑名单
一样，生产侧应保证共享存储（见 token_blacklist 的说明）。
"""

import logging

from utils.cache import memory_cache

logger = logging.getLogger(__name__)

MAX_FAILURES = 5
FAILURE_WINDOW_SECONDS = 15 * 60
LOCKOUT_SECONDS = 15 * 60

_LOCKED_MESSAGE = "登录失败次数过多，账户已临时锁定，请稍后再试"


def _fail_key(username: str, ip: str) -> str:
    return f"login_lock:fail:{(username or '').lower()}@{ip or '-'}"


def _lock_key(username: str, ip: str) -> str:
    return f"login_lock:locked:{(username or '').lower()}@{ip or '-'}"


def is_locked(username: str, ip: str) -> bool:
    return bool(memory_cache.get(_lock_key(username, ip)))


def locked_message() -> str:
    return _LOCKED_MESSAGE


def record_failure(username: str, ip: str) -> None:
    key = _fail_key(username, ip)
    count = int(memory_cache.get(key) or 0) + 1
    memory_cache.set(key, count, ttl=FAILURE_WINDOW_SECONDS)
    if count >= MAX_FAILURES:
        memory_cache.set(_lock_key(username, ip), True, ttl=LOCKOUT_SECONDS)
        memory_cache.delete(key)
        logger.warning(
            "登录失败锁定生效: username=%s ip=%s failures=%s",
            username,
            ip,
            count,
        )


def clear_failures(username: str, ip: str) -> None:
    memory_cache.delete(_fail_key(username, ip))
