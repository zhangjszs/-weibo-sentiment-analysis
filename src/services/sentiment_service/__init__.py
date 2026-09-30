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

from .cache import (
    REDIS_AVAILABLE,
    get_cache_key,
    get_from_cache,
    redis_client,
    save_to_cache,
)
from .models import SentimentResult, SentimentSchema
from .monitoring import (
    MEMORY_CACHE_MAX_SIZE,
    MEMORY_CACHE_TTL,
    _stats,
    _StatsManager,
    cleanup_memory_cache,
    performance_monitor,
)
from .service import SentimentService
from .strategies import (
    CustomModelStrategy,
    LLMStrategy,
    SentimentStrategy,
    SnowNLPStrategy,
)

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
