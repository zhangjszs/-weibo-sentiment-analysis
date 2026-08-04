"""情感分析服务包。

由原 ``sentiment_service.py``（1218 行）物理拆分而来，对外保持完全兼容的
导入路径与公开 API：

    from services.sentiment_service import SentimentService   # 不变
    from services.sentiment_service import SentimentResult, SentimentSchema
    from services.sentiment_service import SnowNLPStrategy, LLMStrategy, CustomModelStrategy
    from services.sentiment_service import get_cache_key

拆分结构：
- :mod:`.models`        — SentimentResult / SentimentSchema
- :mod:`.monitoring`    — _StatsManager / performance_monitor / _stats
- :mod:`.cache`         — Redis + 内存缓存（REDIS_AVAILABLE / redis_client 在此定义）
- :mod:`.strategies`    — SnowNLPStrategy / LLMStrategy / CustomModelStrategy
- :mod:`.service`       — SentimentService 工厂

导入本包会触发 Redis 连接尝试（与原模块行为一致）。
"""

from .models import SentimentResult, SentimentSchema
from .monitoring import (
    _StatsManager,
    _stats,
    MEMORY_CACHE_MAX_SIZE,
    MEMORY_CACHE_TTL,
    performance_monitor,
    cleanup_memory_cache,
)
from .cache import (
    REDIS_AVAILABLE,
    redis_client,
    get_cache_key,
    _build_sentiment_from_cache_data,
    get_from_cache,
    save_to_cache,
)
from .strategies import (
    SentimentStrategy,
    SnowNLPStrategy,
    LLMStrategy,
    CustomModelStrategy,
)
from .service import SentimentService

__all__ = [
    "SentimentService",
    "SentimentResult",
    "SentimentSchema",
    "SentimentStrategy",
    "SnowNLPStrategy",
    "LLMStrategy",
    "CustomModelStrategy",
    "get_cache_key",
    "get_from_cache",
    "save_to_cache",
    "REDIS_AVAILABLE",
    "redis_client",
    "performance_monitor",
    "_stats",
    "_StatsManager",
    "cleanup_memory_cache",
    "MEMORY_CACHE_MAX_SIZE",
    "MEMORY_CACHE_TTL",
]
