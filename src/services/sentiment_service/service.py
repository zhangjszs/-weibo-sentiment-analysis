"""情感分析服务工厂。

拆分自原 ``sentiment_service.py``，逻辑保持不变。

``REDIS_AVAILABLE`` / ``redis_client`` 现定义在 :mod:`.cache`，本模块通过
``_cache.REDIS_AVAILABLE`` 属性访问（而非 ``from .cache import REDIS_AVAILABLE``），
以便 ``monkeypatch.setattr(cache_module, "REDIS_AVAILABLE", ...)`` 能在运行时生效。
"""

import hashlib
import json
import logging

from config.settings import Config

from .monitoring import performance_monitor, _stats
from . import cache as _cache
from .strategies import SnowNLPStrategy, LLMStrategy, CustomModelStrategy

logger = logging.getLogger(__name__)


class SentimentService:
    """情感分析服务工厂"""

    @staticmethod
    @performance_monitor
    def analyze(text: str, mode: str = "custom") -> dict:
        """
        执行情感分析
        Args:
            text: 待分析文本
            mode: 模式 'custom'(默认), 'smart'(LLM), 'simple'(SnowNLP), 'auto'(智能选择)
        Returns:
            dict: 分析结果字典
        """
        if mode == "smart":
            strategy = LLMStrategy()
        elif mode == "custom":
            strategy = CustomModelStrategy()
        elif mode == "auto":
            from ..sentiment_strategy_selector import AdaptiveStrategyManager
            manager = AdaptiveStrategyManager()
            return manager.analyze(text)
        elif mode == "contextual":
            from ..contextual_sentiment import contextual_analyzer
            result = contextual_analyzer.analyze(text)
            return result.to_dict()
        else:
            strategy = SnowNLPStrategy()

        result = strategy.analyze(text)
        return result.to_dict()

    @staticmethod
    @performance_monitor
    def analyze_batch(texts: list, mode: str = "smart") -> list:
        """
        批量情感分析
        Args:
            texts: 文本列表
            mode: 分析模式
        Returns:
            list: 结果列表
        """
        if not texts:
            return []

        # 对于智能模式，使用AdaptiveStrategyManager
        if mode == "auto":
            try:
                from ..sentiment_strategy_selector import AdaptiveStrategyManager
                manager = AdaptiveStrategyManager()
                return manager.analyze_batch(texts)
            except (ImportError, AttributeError, RuntimeError) as e:
                logger.error(f"智能批量分析失败，降级到逐个分析: {e}")
        # 对于上下文感知模式
        elif mode == "contextual":
            try:
                from ..contextual_sentiment import contextual_analyzer
                results = []
                for text in texts:
                    try:
                        result = contextual_analyzer.analyze(text)
                        results.append(result.to_dict())
                    except (ValueError, AttributeError, TypeError) as e:
                        logger.error(f"上下文分析失败: {e}")
                        results.append(
                            {
                                "score": 0.5,
                                "label": "neutral",
                                "reasoning": "分析失败",
                                "emotion": "未知",
                                "keywords": [],
                                "error": True,
                            }
                        )
                return results
            except (ImportError, AttributeError) as e:
                logger.error(f"上下文批量分析失败: {e}")
        # 对于自定义模型，使用批处理
        elif mode == "custom":
            try:
                strategy = CustomModelStrategy()
                batch_results = strategy.analyze_batch(texts)
                return [result.to_dict() for result in batch_results]
            except (RuntimeError, ValueError) as e:
                logger.error(f"批量分析失败，降级到逐个分析: {e}")
        # 对于SnowNLP模式，使用优化的批量处理
        elif mode == "simple":
            try:
                strategy = SnowNLPStrategy()
                results = []
                for text in texts:
                    try:
                        result = strategy.analyze(text)
                        results.append(result.to_dict())
                    except (ValueError, AttributeError) as e:
                        logger.error(f"SnowNLP分析失败: {e}")
                        results.append(
                            {
                                "score": 0.5,
                                "label": "neutral",
                                "reasoning": "分析失败",
                                "emotion": "未知",
                                "keywords": [],
                                "error": True,
                            }
                        )
                return results
            except (ValueError, AttributeError) as e:
                logger.error(f"SnowNLP批量分析失败: {e}")

        # 其他模式使用逐个分析
        results = []
        for text in texts:
            try:
                result = SentimentService.analyze(text, mode)
                results.append(result)
            except (ValueError, RuntimeError) as e:
                logger.error(f"批量分析失败: {e}")
                # 失败时返回中性结果
                results.append(
                    {
                        "score": 0.5,
                        "label": "neutral",
                        "reasoning": "分析失败",
                        "emotion": "未知",
                        "keywords": [],
                        "error": True,
                    }
                )
        return results

    @staticmethod
    def analyze_distribution(
        texts: list, mode: str = "simple", sample_size: int = 100
    ) -> dict:
        """
        统计文本情感分布并使用 Redis 缓存结果，避免接口层重复计算。
        """
        sentiment_counts = {"正面": 0, "中性": 0, "负面": 0}
        sample_texts = [
            str(text).strip() for text in (texts or []) if str(text).strip()
        ][:sample_size]

        if not sample_texts:
            return sentiment_counts

        cache_key = None
        if _cache.REDIS_AVAILABLE:
            # 限制 key_data 长度，避免超长文本导致内存/性能问题
            # 采样最多前100个字符的文本摘要用于生成缓存键
            max_text_len = 100
            max_samples = 50
            truncated_texts = [
                t[:max_text_len] for t in sample_texts[:max_samples]
            ]
            key_data = (
                f"sentiment:distribution:{mode}:{sample_size}:{'|'.join(truncated_texts)}"
            )
            cache_key = hashlib.sha256(key_data.encode()).hexdigest()
            try:
                cached = _cache.redis_client.get(cache_key)
                if cached:
                    loaded = json.loads(cached)
                    if isinstance(loaded, dict):
                        return {
                            "正面": int(loaded.get("正面", 0)),
                            "中性": int(loaded.get("中性", 0)),
                            "负面": int(loaded.get("负面", 0)),
                        }
            except (_cache.redis.RedisError, json.JSONDecodeError, TypeError) as e:
                logger.warning(f"情感分布缓存读取失败: {e}")

        results = SentimentService.analyze_batch(sample_texts, mode)
        for item in results:
            label = (item or {}).get("label", "neutral")
            if label == "positive":
                sentiment_counts["正面"] += 1
            elif label == "negative":
                sentiment_counts["负面"] += 1
            else:
                sentiment_counts["中性"] += 1

        if _cache.REDIS_AVAILABLE and cache_key:
            try:
                _cache.redis_client.setex(
                    cache_key,
                    Config.LLM_CACHE_TTL,
                    json.dumps(sentiment_counts, ensure_ascii=False),
                )
            except (_cache.redis.RedisError, TypeError) as e:
                logger.warning(f"情感分布缓存写入失败: {e}")

        return sentiment_counts

    @staticmethod
    def get_cache_stats() -> dict:
        cs = _stats.cache
        total = cs["total"]
        return {
            "redis_available": _cache.REDIS_AVAILABLE,
            "memory_cache_size": len(_stats.memory_cache),
            "cache_stats": {
                "hits": cs["hits"],
                "misses": cs["misses"],
                "total": total,
                "hit_rate": f"{cs['hits'] / total * 100:.2f}%" if total > 0 else "0.00%",
                "last_reset": cs["last_reset"],
            },
        }

    @staticmethod
    def reset_cache_stats() -> dict:
        return _stats.reset_cache()

    @staticmethod
    def get_performance_stats() -> dict:
        p = _stats.performance
        mode_stats = {}
        for mode, count in p["requests_by_mode"].items():
            if count > 0:
                mode_stats[mode] = {
                    "requests": count,
                    "total_time": p["time_by_mode"][mode],
                    "avg_response_time": p["time_by_mode"][mode] / count,
                }
        return {
            "total_requests": p["total_requests"],
            "total_time": p["total_time"],
            "avg_response_time": p["avg_response_time"],
            "max_response_time": p["max_response_time"],
            "min_response_time": p["min_response_time"] if p["min_response_time"] != float('inf') else 0,
            "mode_stats": mode_stats,
            "last_reset": p["last_reset"],
        }

    @staticmethod
    def reset_performance_stats() -> dict:
        return _stats.reset_performance()

    @staticmethod
    def analyze_sequence(texts: list, mode: str = "custom") -> dict:
        """
        分析文本序列的情感，考虑上下文关联，添加情感突变检测

        Args:
            texts: 文本序列列表
            mode: 分析模式

        Returns:
            dict: 包含序列情感分析结果和情感突变信息
        """
        if not texts:
            return {
                "sequence_analysis": [],
                "overall_sentiment": {
                    "label": "neutral",
                    "score": 0.5
                },
                "sentiment_changes": [],
                "emotion_transitions": [],
                "analysis_count": 0
            }

        # 分析每个文本的情感
        sequence_analysis = []
        previous_score = None
        previous_emotion = None
        sentiment_changes = []
        emotion_transitions = []

        for i, text in enumerate(texts):
            result = SentimentService.analyze(text, mode)
            sequence_analysis.append({
                "index": i,
                "text": text,
                "sentiment": result
            })

            # 检测情感突变
            if previous_score is not None:
                score_diff = abs(result["score"] - previous_score)
                if score_diff > 0.3:
                    sentiment_changes.append({
                        "from_index": i-1,
                        "to_index": i,
                        "from_score": previous_score,
                        "to_score": result["score"],
                        "change_score": score_diff,
                        "from_label": sequence_analysis[i-1]["sentiment"]["label"],
                        "to_label": result["label"]
                    })

            # 检测情感类型变化
            if previous_emotion is not None and result["emotion"] != previous_emotion:
                emotion_transitions.append({
                    "from_index": i-1,
                    "to_index": i,
                    "from_emotion": previous_emotion,
                    "to_emotion": result["emotion"]
                })

            previous_score = result["score"]
            previous_emotion = result["emotion"]

        # 计算整体情感
        scores = [item["sentiment"]["score"] for item in sequence_analysis]
        average_score = sum(scores) / len(scores) if scores else 0.5

        overall_label = "neutral"
        if average_score > 0.65:
            overall_label = "positive"
        elif average_score < 0.35:
            overall_label = "negative"

        return {
            "sequence_analysis": sequence_analysis,
            "overall_sentiment": {
                "label": overall_label,
                "score": average_score
            },
            "sentiment_changes": sentiment_changes,
            "emotion_transitions": emotion_transitions,
            "analysis_count": len(sequence_analysis)
        }
