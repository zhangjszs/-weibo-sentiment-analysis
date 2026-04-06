#!/usr/bin/env python3
"""
API限流模块
功能：基于IP和用户的请求频率限制
"""

import logging
import threading
import time
from collections import defaultdict
from functools import wraps
from typing import Callable, Dict

from flask import g, jsonify, request

logger = logging.getLogger(__name__)


class RateLimiter:
    """滑动窗口限流器"""

    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()

    def _clean_old_requests(self, key: str, window_seconds: int):
        """清理过期的请求记录"""
        now = time.time()
        cutoff = now - window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple:
        """
        检查是否允许请求

        Args:
            key: 限流键（如IP或用户ID）
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）

        Returns:
            tuple: (是否允许, 剩余请求数, 重置时间)
        """
        with self.lock:
            self._clean_old_requests(key, window_seconds)

            current_count = len(self.requests[key])
            remaining = max(0, max_requests - current_count)
            reset_time = int(time.time() + window_seconds)

            if current_count >= max_requests:
                return False, 0, reset_time

            self.requests[key].append(time.time())
            return True, remaining - 1, reset_time

    def get_stats(self, key: str) -> Dict:
        """获取限流统计"""
        with self.lock:
            return {
                "key": key,
                "request_count": len(self.requests.get(key, [])),
                "last_request": self.requests[key][-1]
                if self.requests.get(key)
                else None,
            }


class TokenBucket:
    """令牌桶限流器"""

    def __init__(self, rate: float = 10, capacity: int = 100):
        """
        Args:
            rate: 令牌生成速率（个/秒）
            capacity: 桶容量
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens: Dict[str, dict] = {}
        self.lock = threading.Lock()

    def _init_bucket(self, key: str):
        """初始化令牌桶"""
        if key not in self.tokens:
            self.tokens[key] = {"tokens": self.capacity, "last_update": time.time()}

    def consume(self, key: str, tokens: int = 1) -> bool:
        """
        消费令牌

        Args:
            key: 限流键
            tokens: 需要消费的令牌数

        Returns:
            bool: 是否成功消费
        """
        with self.lock:
            self._init_bucket(key)

            now = time.time()
            elapsed = now - self.tokens[key]["last_update"]

            self.tokens[key]["tokens"] = min(
                self.capacity, self.tokens[key]["tokens"] + elapsed * self.rate
            )
            self.tokens[key]["last_update"] = now

            if self.tokens[key]["tokens"] >= tokens:
                self.tokens[key]["tokens"] -= tokens
                return True

            return False


_global_limiter = RateLimiter()
_global_token_bucket = TokenBucket()


def get_client_ip() -> str:
    """获取客户端IP"""
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    elif request.headers.get("X-Real-IP"):
        return request.headers.get("X-Real-IP")
    return request.remote_addr or "unknown"


def get_rate_limit_key(prefix: str = "ip") -> str:
    """
    生成限流键

    Args:
        prefix: 键前缀

    Returns:
        str: 限流键
    """
    if prefix == "user":
        user_id = getattr(g, "user_id", None)
        if user_id:
            return f"user:{user_id}"

    return f"ip:{get_client_ip()}"


def rate_limit(
    max_requests: int = 60,
    window_seconds: int = 60,
    key_prefix: str = "ip",
    error_message: str = "请求过于频繁，请稍后再试",
):
    """
    API限流装饰器

    Args:
        max_requests: 时间窗口内最大请求数
        window_seconds: 时间窗口（秒）
        key_prefix: 限流键前缀
        error_message: 错误消息

    Usage:
        @rate_limit(max_requests=10, window_seconds=60)
        def my_api():
            return {'data': 'ok'}
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = get_rate_limit_key(key_prefix)
            limiter_key = f"{key_prefix}:{key}:{f.__name__}"

            allowed, remaining, reset_time = _global_limiter.is_allowed(
                limiter_key, max_requests, window_seconds
            )

            g.rate_limit_remaining = remaining
            g.rate_limit_reset = reset_time

            if not allowed:
                logger.warning(f"限流触发: key={limiter_key}")
                response = jsonify(
                    {
                        "code": 429,
                        "msg": error_message,
                        "data": {"retry_after": reset_time - int(time.time())},
                    }
                )
                response.status_code = 429
                response.headers["X-RateLimit-Limit"] = str(max_requests)
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = str(reset_time)
                response.headers["Retry-After"] = str(reset_time - int(time.time()))
                return response

            response = f(*args, **kwargs)

            if hasattr(response, "headers"):
                response.headers["X-RateLimit-Limit"] = str(max_requests)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(reset_time)

            return response

        return decorated_function

    return decorator


def token_bucket_limit(
    rate: float = 10,
    capacity: int = 100,
    key_prefix: str = "ip",
    error_message: str = "请求过于频繁，请稍后再试",
):
    """
    令牌桶限流装饰器

    Args:
        rate: 令牌生成速率
        capacity: 桶容量
        key_prefix: 限流键前缀
        error_message: 错误消息
    """
    bucket = TokenBucket(rate=rate, capacity=capacity)

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = get_rate_limit_key(key_prefix)
            bucket_key = f"{key_prefix}:{key}:{f.__name__}"

            if not bucket.consume(bucket_key):
                logger.warning(f"令牌桶限流触发: key={bucket_key}")
                response = jsonify({"code": 429, "msg": error_message})
                response.status_code = 429
                return response

            return f(*args, **kwargs)

        return decorated_function

    return decorator


class RateLimitMiddleware:
    """Flask限流中间件"""

    def __init__(self, app=None, default_limits: Dict[str, tuple] = None):
        self.app = app
        self.default_limits = default_limits or {
            "default": (60, 60),
            "auth": (5, 60),
            "api": (30, 60),
            "predict": (10, 60),
        }

        if app:
            self.init_app(app)

    def init_app(self, app):
        """初始化中间件"""
        app.before_request(self._before_request)
        app.after_request(self._after_request)

    def _get_limit_config(self, endpoint: str) -> tuple:
        """获取限流配置"""
        if "auth" in endpoint or "login" in endpoint or "register" in endpoint:
            return self.default_limits.get("auth", (5, 60))
        elif "predict" in endpoint or "sentiment" in endpoint:
            return self.default_limits.get("predict", (10, 60))
        elif "api" in endpoint:
            return self.default_limits.get("api", (30, 60))
        return self.default_limits.get("default", (60, 60))

    def _before_request(self):
        """请求前处理"""
        if request.path.startswith("/static") or request.path.startswith("/health"):
            return

        endpoint = request.endpoint or "default"
        max_requests, window_seconds = self._get_limit_config(endpoint)

        key = get_rate_limit_key("ip")
        limiter_key = f"middleware:{key}:{endpoint}"

        allowed, remaining, reset_time = _global_limiter.is_allowed(
            limiter_key, max_requests, window_seconds
        )

        g.rate_limit_remaining = remaining
        g.rate_limit_reset = reset_time
        g.rate_limit_limit = max_requests

        if not allowed:
            logger.warning(f"中间件限流触发: endpoint={endpoint}, key={limiter_key}")
            response = jsonify(
                {
                    "code": 429,
                    "msg": "请求过于频繁，请稍后再试",
                    "data": {"retry_after": reset_time - int(time.time())},
                }
            )
            response.status_code = 429
            return response

    def _after_request(self, response):
        """请求后处理"""
        if hasattr(g, "rate_limit_limit"):
            response.headers["X-RateLimit-Limit"] = str(g.rate_limit_limit)
        if hasattr(g, "rate_limit_remaining"):
            response.headers["X-RateLimit-Remaining"] = str(g.rate_limit_remaining)
        if hasattr(g, "rate_limit_reset"):
            response.headers["X-RateLimit-Reset"] = str(g.rate_limit_reset)
        return response


def get_rate_limit_stats() -> Dict:
    """获取限流统计信息"""
    return {
        "active_keys": len(_global_limiter.requests),
        "total_tracked_requests": sum(
            len(v) for v in _global_limiter.requests.values()
        ),
    }


def clear_rate_limit_stats():
    """清空限流统计"""
    with _global_limiter.lock:
        _global_limiter.requests.clear()


if __name__ == "__main__":
    print("API限流模块演示:")
    print("=" * 50)

    limiter = RateLimiter()

    for i in range(12):
        allowed, remaining, reset_time = limiter.is_allowed("test_key", 10, 60)
        print(f"请求 {i + 1}: 允许={allowed}, 剩余={remaining}")

    print("\n令牌桶演示:")
    bucket = TokenBucket(rate=2, capacity=5)

    for i in range(7):
        time.sleep(0.3)
        result = bucket.consume("test_bucket")
        print(f"请求 {i + 1}: 成功={result}")
