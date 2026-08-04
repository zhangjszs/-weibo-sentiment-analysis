#!/usr/bin/env python3
"""
情感分析服务单元测试
测试内容：
- 正常文本分析返回结果不为 None
- 空文本不抛异常
- 批量分析返回列表
- 结果包含 sentiment/score 字段
"""

import pytest

pytestmark = pytest.mark.unit

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.sentiment_service import (
    SentimentResult,
    SentimentSchema,
    SentimentService,
    SnowNLPStrategy,
)


class TestSentimentService:
    """测试情感分析服务"""

    def test_analyze_returns_result_not_none(self):
        """正常文本分析返回结果不为 None"""
        result = SentimentService.analyze("这是一条测试文本", mode="simple")
        assert result is not None
        assert isinstance(result, dict)

    def test_analyze_contains_sentiment_field(self):
        """结果应该包含 sentiment/label 字段"""
        result = SentimentService.analyze("今天天气很好", mode="simple")
        assert "label" in result
        assert result["label"] in ["positive", "negative", "neutral"]

    def test_analyze_contains_score_field(self):
        """结果应该包含 score 字段"""
        result = SentimentService.analyze("今天天气很好", mode="simple")
        assert "score" in result
        assert isinstance(result["score"], float)
        assert 0 <= result["score"] <= 1

    def test_analyze_empty_text_no_exception(self):
        """空文本不抛异常"""
        result = SentimentService.analyze("", mode="simple")
        assert result is not None
        assert isinstance(result, dict)
        assert "label" in result
        assert "score" in result

    def test_analyze_whitespace_text(self):
        """空白文本应该能处理"""
        result = SentimentService.analyze("   ", mode="simple")
        assert result is not None
        assert "label" in result

    def test_analyze_long_text(self):
        """长文本应该能处理"""
        long_text = "这是一个很长的文本。" * 100
        result = SentimentService.analyze(long_text, mode="simple")
        assert result is not None
        assert "label" in result
        assert "score" in result


class TestSentimentBatchAnalysis:
    """测试批量情感分析"""

    def test_analyze_batch_returns_list(self):
        """批量分析返回列表"""
        texts = ["文本1", "文本2", "文本3"]
        results = SentimentService.analyze_batch(texts, mode="simple")
        assert isinstance(results, list)
        assert len(results) == 3

    def test_analyze_batch_empty_list(self):
        """空列表应该返回空结果"""
        results = SentimentService.analyze_batch([], mode="simple")
        assert isinstance(results, list)
        assert len(results) == 0

    def test_analyze_batch_results_contain_required_fields(self):
        """批量结果应该包含必要字段"""
        texts = ["很好", "一般", "很差"]
        results = SentimentService.analyze_batch(texts, mode="simple")

        for result in results:
            assert isinstance(result, dict)
            assert "label" in result
            assert "score" in result
            assert result["label"] in ["positive", "negative", "neutral"]

    def test_analyze_batch_mixed_empty_texts(self):
        """批量分析应该能处理包含空文本的列表"""
        texts = ["很好", "", "一般", "   ", "很差"]
        results = SentimentService.analyze_batch(texts, mode="simple")
        assert isinstance(results, list)
        assert len(results) == 5

        for result in results:
            assert "label" in result
            assert "score" in result


class TestSentimentResult:
    """测试 SentimentResult 类"""

    def test_sentiment_result_creation(self):
        """应该能创建 SentimentResult 对象"""
        result = SentimentResult(
            score=0.8,
            label="positive",
            reasoning="测试理由",
            emotion="喜悦",
            keywords=["好", "棒"],
            source="test"
        )
        assert result.score == 0.8
        assert result.label == "positive"
        assert result.reasoning == "测试理由"
        assert result.emotion == "喜悦"
        assert result.keywords == ["好", "棒"]
        assert result.source == "test"

    def test_sentiment_result_to_dict(self):
        """SentimentResult 应该能转换为字典"""
        result = SentimentResult(
            score=0.5,
            label="neutral",
            source="test"
        )
        data = result.to_dict()
        assert isinstance(data, dict)
        assert data["score"] == 0.5
        assert data["label"] == "neutral"
        assert data["source"] == "test"


class TestSnowNLPStrategy:
    """测试 SnowNLP 策略"""

    def test_snownlp_analyze_positive(self):
        """应该能分析正面情感"""
        strategy = SnowNLPStrategy()
        result = strategy.analyze("这个产品非常好，我很喜欢！")
        assert isinstance(result, SentimentResult)
        assert result.label in ["positive", "neutral", "negative"]
        assert 0 <= result.score <= 1

    def test_snownlp_analyze_negative(self):
        """应该能分析负面情感"""
        strategy = SnowNLPStrategy()
        result = strategy.analyze("这个产品太差了，非常失望！")
        assert isinstance(result, SentimentResult)
        assert result.label in ["positive", "neutral", "negative"]
        assert 0 <= result.score <= 1

    def test_snownlp_analyze_empty(self):
        """空文本应该返回中性结果"""
        strategy = SnowNLPStrategy()
        result = strategy.analyze("")
        assert isinstance(result, SentimentResult)
        assert result.label == "neutral"
        assert result.score == 0.5


class TestSentimentSchema:
    """测试 SentimentSchema 校验"""

    def test_schema_valid_data(self):
        """有效数据应该通过校验"""
        data = {
            "score": 0.8,
            "label": "positive",
            "emotion": "喜悦",
            "reasoning": "测试",
            "keywords": ["好", "棒"]
        }
        schema = SentimentSchema(**data)
        assert schema.score == 0.8
        assert schema.label == "positive"

    def test_schema_invalid_label(self):
        """无效 label 应该转为 neutral"""
        data = {
            "score": 0.8,
            "label": "invalid_label"
        }
        schema = SentimentSchema(**data)
        assert schema.label == "neutral"

    def test_schema_score_out_of_range(self):
        """超出范围的 score 应该被 Pydantic 拒绝"""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SentimentSchema(score=1.5, label="positive")


class TestSentimentDistribution:
    """测试情感分布统计"""

    def test_analyze_distribution_returns_dict(self):
        """情感分布应该返回字典"""
        texts = ["很好", "不错", "一般", "不好", "很差"]
        result = SentimentService.analyze_distribution(texts, mode="simple")
        assert isinstance(result, dict)

    def test_analyze_distribution_contains_required_keys(self):
        """情感分布结果应该包含必要的键"""
        texts = ["很好", "不错", "一般"]
        result = SentimentService.analyze_distribution(texts, mode="simple")
        assert "正面" in result
        assert "中性" in result
        assert "负面" in result

    def test_analyze_distribution_empty_texts(self):
        """空文本列表应该返回零值分布"""
        result = SentimentService.analyze_distribution([], mode="simple")
        assert isinstance(result, dict)
        assert result["正面"] == 0
        assert result["中性"] == 0
        assert result["负面"] == 0


class TestSentimentServiceModes:
    """测试不同分析模式"""

    def test_simple_mode(self):
        """simple 模式应该正常工作"""
        result = SentimentService.analyze("测试文本", mode="simple")
        assert result is not None
        assert "label" in result

    def test_custom_mode(self):
        """custom 模式应该正常工作"""
        # custom 模式会尝试加载模型，如果模型不存在会降级到 snownlp
        result = SentimentService.analyze("测试文本", mode="custom")
        assert result is not None
        assert "label" in result

    @patch('services.sentiment_service.strategies.Config')
    def test_smart_mode_no_api_key(self, mock_config):
        """smart 模式在没有 API key 时应该降级"""
        mock_config.LLM_API_KEY = None
        result = SentimentService.analyze("测试文本", mode="smart")
        assert result is not None
        assert "label" in result


class TestCustomModelStrategyBackend:
    """Phase 3：CustomModelStrategy + ModelBackend 集成测试。"""

    def _make_strategy_with_mock_backend(self, predictions):
        """构造一个注入 mock backend 的 CustomModelStrategy。"""
        from services.sentiment_service import CustomModelStrategy

        strategy = CustomModelStrategy.__new__(CustomModelStrategy)
        strategy._snow_strategy = None
        strategy._backend = MagicMock()
        strategy._backend.name = "mock_backend"
        strategy._backend.predict_batch.return_value = predictions
        return strategy

    def test_analyze_uses_backend_prediction(self):
        """analyze 应使用 backend.predict_batch 的结果并填入 source。"""
        strategy = self._make_strategy_with_mock_backend(
            [("positive", 0.92)]
        )
        result = strategy.analyze("好棒")
        assert result.label == "positive"
        assert result.score == 0.92
        assert result.source == "mock_backend"
        strategy._backend.predict_batch.assert_called_once_with(["好棒"])

    def test_analyze_empty_text_short_circuits(self):
        strategy = self._make_strategy_with_mock_backend([("positive", 0.9)])
        result = strategy.analyze("")
        assert result.label == "neutral"
        assert result.source == "custom_model"
        # 空文本不应调用 backend
        strategy._backend.predict_batch.assert_not_called()

    def test_analyze_falls_back_to_snownlp_on_backend_failure(self):
        strategy = self._make_strategy_with_mock_backend([])
        strategy._backend.predict_batch.side_effect = RuntimeError("backend down")
        result = strategy.analyze("测试文本")
        # 降级到 SnowNLP，应该有结果
        assert result.label in ("positive", "negative", "neutral")
        assert 0.0 <= result.score <= 1.0

    def test_analyze_batch_uses_backend_predict_batch(self):
        strategy = self._make_strategy_with_mock_backend(
            [("positive", 0.8), ("negative", 0.7)]
        )
        results = strategy.analyze_batch(["好", "差"])
        assert len(results) == 2
        assert results[0].label == "positive"
        assert results[1].label == "negative"
        assert all(r.source == "mock_backend" for r in results)

    def test_analyze_batch_empty_input(self):
        strategy = self._make_strategy_with_mock_backend([])
        assert strategy.analyze_batch([]) == []

    def test_analyze_batch_falls_back_to_snownlp_on_failure(self):
        strategy = self._make_strategy_with_mock_backend([])
        strategy._backend.predict_batch.side_effect = RuntimeError("batch fail")
        results = strategy.analyze_batch(["好棒", "糟糕"])
        assert len(results) == 2
        for r in results:
            assert r.label in ("positive", "negative", "neutral")

    def test_cache_key_includes_backend_dimension(self):
        """不同 backend 应产生不同 cache key（避免污染）。"""
        from services.sentiment_service import get_cache_key

        key_bert = get_cache_key("test", "custom_model", "bert")
        key_sklearn = get_cache_key("test", "custom_model", "sklearn")
        key_default = get_cache_key("test", "custom_model")
        assert key_bert != key_sklearn
        assert key_bert != key_default
        assert key_sklearn != key_default


class TestSentimentServiceAnalyzeModes:
    """测试 analyze 的 auto/contextual/smart 模式分支（service.py 37-53）"""

    @patch('services.sentiment_service.service.LLMStrategy')
    def test_analyze_smart_mode_uses_llm_strategy(self, mock_llm_cls):
        """smart 模式应使用 LLMStrategy 并返回其结果"""
        mock_strategy = MagicMock()
        mock_strategy.analyze.return_value = SentimentResult(
            0.9, "positive", emotion="喜悦", source="llm"
        )
        mock_llm_cls.return_value = mock_strategy

        result = SentimentService.analyze("好开心", mode="smart")

        assert result["label"] == "positive"
        assert result["score"] == 0.9
        assert result["source"] == "llm"
        mock_strategy.analyze.assert_called_once_with("好开心")

    @patch('services.sentiment_strategy_selector.AdaptiveStrategyManager')
    def test_analyze_auto_mode_delegates_to_manager(self, mock_mgr_cls):
        """auto 模式应委托给 AdaptiveStrategyManager.analyze"""
        mock_manager = MagicMock()
        mock_manager.analyze.return_value = {"label": "positive", "score": 0.8}
        mock_mgr_cls.return_value = mock_manager

        result = SentimentService.analyze("测试", mode="auto")

        assert result == {"label": "positive", "score": 0.8}
        mock_manager.analyze.assert_called_once_with("测试")

    @patch('services.contextual_sentiment.contextual_analyzer')
    def test_analyze_contextual_mode_delegates_to_analyzer(self, mock_ctx):
        """contextual 模式应委托给 contextual_analyzer.analyze 并调用 to_dict"""
        mock_result = SentimentResult(0.7, "positive", emotion="喜悦", source="contextual")
        mock_ctx.analyze.return_value = mock_result

        result = SentimentService.analyze("测试", mode="contextual")

        assert result["label"] == "positive"
        assert result["score"] == 0.7
        assert result["source"] == "contextual"


class TestSentimentServiceAnalyzeBatchModes:
    """测试 analyze_batch 各模式分支（service.py 66-153）"""

    @patch('services.sentiment_strategy_selector.AdaptiveStrategyManager')
    def test_batch_auto_mode_success(self, mock_mgr_cls):
        """auto 模式批量分析应委托给 manager.analyze_batch"""
        mock_manager = MagicMock()
        mock_manager.analyze_batch.return_value = [
            {"label": "positive", "score": 0.8}
        ]
        mock_mgr_cls.return_value = mock_manager

        results = SentimentService.analyze_batch(["好"], mode="auto")

        assert results == [{"label": "positive", "score": 0.8}]
        mock_manager.analyze_batch.assert_called_once_with(["好"])

    @patch('services.sentiment_strategy_selector.AdaptiveStrategyManager')
    def test_batch_auto_mode_failure_falls_back(self, mock_mgr_cls):
        """auto 模式 manager 初始化失败应降级到逐个分析（返回中性错误结果）"""
        mock_mgr_cls.side_effect = RuntimeError("init failed")

        results = SentimentService.analyze_batch(["好"], mode="auto")

        assert len(results) == 1
        assert results[0]["label"] == "neutral"
        assert results[0]["score"] == 0.5
        assert results[0].get("error") is True

    @patch('services.contextual_sentiment.contextual_analyzer')
    def test_batch_contextual_mode_success(self, mock_ctx):
        """contextual 模式批量分析应对每个文本调用 contextual_analyzer"""
        mock_ctx.analyze.return_value = SentimentResult(
            0.8, "positive", emotion="喜悦", source="contextual"
        )

        results = SentimentService.analyze_batch(["好", "不错"], mode="contextual")

        assert len(results) == 2
        assert all(r["label"] == "positive" for r in results)
        assert mock_ctx.analyze.call_count == 2

    @patch('services.contextual_sentiment.contextual_analyzer')
    def test_batch_contextual_mode_single_text_error(self, mock_ctx):
        """contextual 模式单文本分析失败应返回中性错误结果"""
        mock_ctx.analyze.side_effect = ValueError("bad text")

        results = SentimentService.analyze_batch(["bad"], mode="contextual")

        assert len(results) == 1
        assert results[0]["label"] == "neutral"
        assert results[0]["score"] == 0.5
        assert results[0].get("error") is True

    @patch('services.contextual_sentiment.contextual_analyzer')
    def test_batch_contextual_mode_text_attribute_error(self, mock_ctx):
        """contextual 模式 analyze 抛 AttributeError 被内层 except 捕获"""
        mock_ctx.analyze.side_effect = AttributeError("no analyze method")

        results = SentimentService.analyze_batch(["bad"], mode="contextual")

        # AttributeError 被 except (ValueError, AttributeError, TypeError) 捕获
        assert len(results) == 1
        assert results[0]["label"] == "neutral"
        assert results[0].get("error") is True

    def test_batch_contextual_mode_import_error(self, monkeypatch):
        """contextual_analyzer 不存在时导入失败，外层 except 降级到逐个分析"""
        import services.contextual_sentiment as ctx_mod

        monkeypatch.delattr(ctx_mod, "contextual_analyzer")
        # 逐个分析会再次调用 analyze(text, "contextual") 触发同样的导入失败，
        # 但 per-text 只捕获 (ValueError, RuntimeError)，因此 patch analyze 避免传播
        mock_analyze = MagicMock(
            return_value={"label": "neutral", "score": 0.5, "emotion": "无感"}
        )
        monkeypatch.setattr(SentimentService, "analyze", mock_analyze)

        results = SentimentService.analyze_batch(["bad"], mode="contextual")

        assert len(results) == 1
        assert results[0]["label"] == "neutral"

    @patch('services.sentiment_service.service.CustomModelStrategy')
    def test_batch_custom_mode_success(self, mock_custom_cls):
        """custom 模式应使用 CustomModelStrategy.analyze_batch"""
        mock_strategy = MagicMock()
        mock_strategy.analyze_batch.return_value = [
            SentimentResult(0.8, "positive", source="custom_model"),
            SentimentResult(0.3, "negative", source="custom_model"),
        ]
        mock_custom_cls.return_value = mock_strategy

        results = SentimentService.analyze_batch(["好", "差"], mode="custom")

        assert len(results) == 2
        assert results[0]["label"] == "positive"
        assert results[1]["label"] == "negative"

    @patch('services.sentiment_service.service.CustomModelStrategy')
    def test_batch_custom_mode_failure_falls_back(self, mock_custom_cls):
        """custom 模式策略初始化失败应降级到逐个分析"""
        mock_custom_cls.side_effect = RuntimeError("model load failed")

        results = SentimentService.analyze_batch(["好"], mode="custom")

        assert len(results) == 1
        assert results[0]["label"] == "neutral"
        assert results[0].get("error") is True

    def test_batch_simple_mode_success(self):
        """simple 模式应使用 SnowNLPStrategy 逐个分析"""
        results = SentimentService.analyze_batch(["好棒", "糟糕"], mode="simple")

        assert len(results) == 2
        for r in results:
            assert "label" in r
            assert r["label"] in ["positive", "negative", "neutral"]

    @patch('services.sentiment_service.service.SnowNLPStrategy')
    def test_batch_simple_mode_text_error(self, mock_snow_cls):
        """simple 模式单文本分析失败应返回中性错误结果"""
        mock_strategy = MagicMock()
        mock_strategy.analyze.side_effect = ValueError("bad")
        mock_snow_cls.return_value = mock_strategy

        results = SentimentService.analyze_batch(["bad"], mode="simple")

        assert len(results) == 1
        assert results[0]["label"] == "neutral"
        assert results[0].get("error") is True

    @patch('services.sentiment_service.service.SnowNLPStrategy')
    def test_batch_simple_mode_init_error(self, mock_snow_cls):
        """simple 模式策略初始化失败应降级到逐个分析"""
        mock_snow_cls.side_effect = ValueError("init failed")

        results = SentimentService.analyze_batch(["好"], mode="simple")

        assert len(results) == 1
        assert results[0]["label"] == "neutral"
        assert results[0].get("error") is True

    @patch('services.sentiment_service.service.LLMStrategy')
    def test_batch_smart_mode_uses_per_text_analysis(self, mock_llm_cls):
        """smart 模式不在 elif 分支，走逐个分析（调用 analyze smart）"""
        mock_strategy = MagicMock()
        mock_strategy.analyze.return_value = SentimentResult(0.7, "positive", source="llm")
        mock_llm_cls.return_value = mock_strategy

        results = SentimentService.analyze_batch(["好"], mode="smart")

        assert len(results) == 1
        assert results[0]["label"] == "positive"

    @patch('services.sentiment_service.service.LLMStrategy')
    def test_batch_smart_mode_text_error(self, mock_llm_cls):
        """逐个分析中单文本失败应返回中性错误结果"""
        mock_strategy = MagicMock()
        mock_strategy.analyze.side_effect = RuntimeError("api error")
        mock_llm_cls.return_value = mock_strategy

        results = SentimentService.analyze_batch(["bad"], mode="smart")

        assert len(results) == 1
        assert results[0]["label"] == "neutral"
        assert results[0].get("error") is True


class TestSentimentServiceStats:
    """测试统计方法（service.py 219-261）"""

    def setup_method(self):
        """每个测试前重置统计，避免相互污染"""
        SentimentService.reset_cache_stats()
        SentimentService.reset_performance_stats()

    def test_get_cache_stats_empty(self):
        """无请求时缓存统计应为零值"""
        stats = SentimentService.get_cache_stats()

        assert stats["cache_stats"]["hits"] == 0
        assert stats["cache_stats"]["misses"] == 0
        assert stats["cache_stats"]["total"] == 0
        assert stats["cache_stats"]["hit_rate"] == "0.00%"
        assert "redis_available" in stats
        assert "memory_cache_size" in stats

    def test_get_cache_stats_with_hits(self):
        """有命中/未命中时 hit_rate 应正确计算"""
        from services.sentiment_service.monitoring import _stats

        _stats.record_cache_hit()
        _stats.record_cache_hit()
        _stats.record_cache_miss()

        stats = SentimentService.get_cache_stats()

        assert stats["cache_stats"]["hits"] == 2
        assert stats["cache_stats"]["misses"] == 1
        assert stats["cache_stats"]["total"] == 3
        assert stats["cache_stats"]["hit_rate"] == "66.67%"

    def test_reset_cache_stats(self):
        """reset_cache_stats 应清零缓存统计"""
        from services.sentiment_service.monitoring import _stats

        _stats.record_cache_hit()
        _stats.record_cache_miss()

        result = SentimentService.reset_cache_stats()

        assert result["hits"] == 0
        assert result["misses"] == 0
        assert result["total"] == 0

    def test_get_performance_stats_empty(self):
        """无请求时性能统计应为零值，min_response_time(inf) 应转为 0"""
        stats = SentimentService.get_performance_stats()

        assert stats["total_requests"] == 0
        assert stats["total_time"] == 0
        assert stats["avg_response_time"] == 0
        assert stats["max_response_time"] == 0
        assert stats["min_response_time"] == 0
        assert stats["mode_stats"] == {}

    def test_get_performance_stats_with_data(self):
        """有请求时应正确计算 mode_stats 和聚合值"""
        from services.sentiment_service.monitoring import _stats

        _stats.record_performance(10.0, "simple")
        _stats.record_performance(20.0, "simple")
        _stats.record_performance(30.0, "custom")

        stats = SentimentService.get_performance_stats()

        assert stats["total_requests"] == 3
        assert stats["total_time"] == 60.0
        assert stats["max_response_time"] == 30.0
        assert stats["min_response_time"] == 10.0
        assert "simple" in stats["mode_stats"]
        assert stats["mode_stats"]["simple"]["requests"] == 2
        assert stats["mode_stats"]["simple"]["avg_response_time"] == 15.0
        assert "custom" in stats["mode_stats"]
        assert stats["mode_stats"]["custom"]["requests"] == 1

    def test_reset_performance_stats(self):
        """reset_performance_stats 应清零性能统计"""
        from services.sentiment_service.monitoring import _stats

        _stats.record_performance(10.0, "simple")

        result = SentimentService.reset_performance_stats()

        assert result["total_requests"] == 0
        assert result["total_time"] == 0
        assert result["requests_by_mode"] == {}


class TestSentimentServiceDistributionRedis:
    """测试 analyze_distribution 的 Redis 缓存路径（service.py 171-214）"""

    def test_distribution_redis_cache_hit(self, monkeypatch):
        """Redis 缓存命中应直接返回缓存结果，不调用分析"""
        from services.sentiment_service import cache as cache_module

        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps({"正面": 3, "中性": 2, "负面": 1})
        monkeypatch.setattr(cache_module, "REDIS_AVAILABLE", True)
        monkeypatch.setattr(cache_module, "redis_client", mock_redis)
        mock_batch = MagicMock(return_value=[])
        monkeypatch.setattr(SentimentService, "analyze_batch", mock_batch)

        result = SentimentService.analyze_distribution(["好", "差", "一般"], mode="simple")

        assert result == {"正面": 3, "中性": 2, "负面": 1}
        mock_batch.assert_not_called()

    def test_distribution_redis_cache_miss_and_write(self, monkeypatch):
        """Redis 缓存未命中应分析后写入缓存"""
        from services.sentiment_service import cache as cache_module

        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        monkeypatch.setattr(cache_module, "REDIS_AVAILABLE", True)
        monkeypatch.setattr(cache_module, "redis_client", mock_redis)
        mock_batch = MagicMock(return_value=[
            {"label": "positive", "score": 0.8, "emotion": "喜悦"},
            {"label": "negative", "score": 0.2, "emotion": "悲伤"},
        ])
        monkeypatch.setattr(SentimentService, "analyze_batch", mock_batch)

        result = SentimentService.analyze_distribution(["好", "差"], mode="simple")

        assert result == {"正面": 1, "中性": 0, "负面": 1}
        mock_redis.setex.assert_called_once()
        mock_batch.assert_called_once()

    def test_distribution_redis_read_failure(self, monkeypatch):
        """Redis 读取失败应降级到分析"""
        from services.sentiment_service import cache as cache_module

        mock_redis = MagicMock()
        mock_redis.get.side_effect = cache_module.redis.RedisError("connection lost")
        monkeypatch.setattr(cache_module, "REDIS_AVAILABLE", True)
        monkeypatch.setattr(cache_module, "redis_client", mock_redis)
        mock_batch = MagicMock(return_value=[
            {"label": "positive", "score": 0.8, "emotion": "喜悦"},
        ])
        monkeypatch.setattr(SentimentService, "analyze_batch", mock_batch)

        result = SentimentService.analyze_distribution(["好"], mode="simple")

        assert result == {"正面": 1, "中性": 0, "负面": 0}

    def test_distribution_redis_write_failure(self, monkeypatch):
        """Redis 写入失败不应影响返回结果"""
        from services.sentiment_service import cache as cache_module

        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.setex.side_effect = cache_module.redis.RedisError("write failed")
        monkeypatch.setattr(cache_module, "REDIS_AVAILABLE", True)
        monkeypatch.setattr(cache_module, "redis_client", mock_redis)
        mock_batch = MagicMock(return_value=[
            {"label": "positive", "score": 0.8, "emotion": "喜悦"},
        ])
        monkeypatch.setattr(SentimentService, "analyze_batch", mock_batch)

        result = SentimentService.analyze_distribution(["好"], mode="simple")

        assert result == {"正面": 1, "中性": 0, "负面": 0}

    def test_distribution_redis_cache_hit_invalid_json(self, monkeypatch):
        """Redis 缓存值非 dict（如列表）应降级到分析"""
        from services.sentiment_service import cache as cache_module

        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps([1, 2, 3])  # 非 dict
        monkeypatch.setattr(cache_module, "REDIS_AVAILABLE", True)
        monkeypatch.setattr(cache_module, "redis_client", mock_redis)
        mock_batch = MagicMock(return_value=[
            {"label": "neutral", "score": 0.5, "emotion": "无感"},
        ])
        monkeypatch.setattr(SentimentService, "analyze_batch", mock_batch)

        result = SentimentService.analyze_distribution(["一般"], mode="simple")

        # isinstance(loaded, dict) 为 False，降级到分析
        assert result == {"正面": 0, "中性": 1, "负面": 0}
        mock_batch.assert_called_once()


class TestSentimentServiceAnalyzeSequence:
    """测试 analyze_sequence（service.py 264-338）"""

    def test_sequence_empty(self):
        """空列表应返回默认结构"""
        result = SentimentService.analyze_sequence([], mode="simple")

        assert result["sequence_analysis"] == []
        assert result["overall_sentiment"]["label"] == "neutral"
        assert result["overall_sentiment"]["score"] == 0.5
        assert result["sentiment_changes"] == []
        assert result["emotion_transitions"] == []
        assert result["analysis_count"] == 0

    @patch.object(SentimentService, 'analyze')
    def test_sequence_single_text(self, mock_analyze):
        """单文本序列应正确计算整体情感"""
        mock_analyze.return_value = {"score": 0.8, "label": "positive", "emotion": "喜悦"}

        result = SentimentService.analyze_sequence(["好开心"], mode="simple")

        assert result["analysis_count"] == 1
        assert result["overall_sentiment"]["label"] == "positive"
        assert result["overall_sentiment"]["score"] == 0.8
        assert result["sentiment_changes"] == []
        assert result["emotion_transitions"] == []
        assert result["sequence_analysis"][0]["text"] == "好开心"

    @patch.object(SentimentService, 'analyze')
    def test_sequence_sentiment_change_detected(self, mock_analyze):
        """score_diff > 0.3 应记录情感突变"""
        mock_analyze.side_effect = [
            {"score": 0.9, "label": "positive", "emotion": "喜悦"},
            {"score": 0.2, "label": "negative", "emotion": "悲伤"},
        ]

        result = SentimentService.analyze_sequence(["好棒", "太差了"], mode="simple")

        assert len(result["sentiment_changes"]) == 1
        change = result["sentiment_changes"][0]
        assert change["from_index"] == 0
        assert change["to_index"] == 1
        assert change["from_score"] == 0.9
        assert change["to_score"] == 0.2
        assert change["change_score"] == 0.7
        assert change["from_label"] == "positive"
        assert change["to_label"] == "negative"

    @patch.object(SentimentService, 'analyze')
    def test_sequence_no_change_when_diff_small(self, mock_analyze):
        """score_diff <= 0.3 不应记录突变"""
        mock_analyze.side_effect = [
            {"score": 0.6, "label": "positive", "emotion": "喜悦"},
            {"score": 0.7, "label": "positive", "emotion": "喜悦"},
        ]

        result = SentimentService.analyze_sequence(["好", "不错"], mode="simple")

        assert result["sentiment_changes"] == []

    @patch.object(SentimentService, 'analyze')
    def test_sequence_emotion_transition(self, mock_analyze):
        """情绪类型变化应记录到 emotion_transitions"""
        mock_analyze.side_effect = [
            {"score": 0.8, "label": "positive", "emotion": "喜悦"},
            {"score": 0.2, "label": "negative", "emotion": "愤怒"},
        ]

        result = SentimentService.analyze_sequence(["好", "气"], mode="simple")

        assert len(result["emotion_transitions"]) == 1
        transition = result["emotion_transitions"][0]
        assert transition["from_emotion"] == "喜悦"
        assert transition["to_emotion"] == "愤怒"

    @patch.object(SentimentService, 'analyze')
    def test_sequence_no_emotion_transition_when_same(self, mock_analyze):
        """情绪类型不变时不应记录 transition"""
        mock_analyze.side_effect = [
            {"score": 0.8, "label": "positive", "emotion": "喜悦"},
            {"score": 0.7, "label": "positive", "emotion": "喜悦"},
        ]

        result = SentimentService.analyze_sequence(["好", "不错"], mode="simple")

        assert result["emotion_transitions"] == []

    @patch.object(SentimentService, 'analyze')
    def test_sequence_overall_positive(self, mock_analyze):
        """平均分 > 0.65 时整体情感应为 positive"""
        mock_analyze.side_effect = [
            {"score": 0.8, "label": "positive", "emotion": "喜悦"},
            {"score": 0.7, "label": "positive", "emotion": "喜悦"},
        ]

        result = SentimentService.analyze_sequence(["好", "不错"], mode="simple")

        assert result["overall_sentiment"]["label"] == "positive"
        assert result["overall_sentiment"]["score"] == 0.75

    @patch.object(SentimentService, 'analyze')
    def test_sequence_overall_negative(self, mock_analyze):
        """平均分 < 0.35 时整体情感应为 negative"""
        mock_analyze.side_effect = [
            {"score": 0.2, "label": "negative", "emotion": "悲伤"},
            {"score": 0.3, "label": "negative", "emotion": "悲伤"},
        ]

        result = SentimentService.analyze_sequence(["差", "糟"], mode="simple")

        assert result["overall_sentiment"]["label"] == "negative"
        assert result["overall_sentiment"]["score"] == 0.25

    @patch.object(SentimentService, 'analyze')
    def test_sequence_overall_neutral(self, mock_analyze):
        """平均分在 0.35-0.65 之间时整体情感应为 neutral"""
        mock_analyze.side_effect = [
            {"score": 0.5, "label": "neutral", "emotion": "无感"},
            {"score": 0.5, "label": "neutral", "emotion": "无感"},
        ]

        result = SentimentService.analyze_sequence(["一般", "还行"], mode="simple")

        assert result["overall_sentiment"]["label"] == "neutral"
        assert result["overall_sentiment"]["score"] == 0.5

    @patch.object(SentimentService, 'analyze')
    def test_sequence_boundary_positive(self, mock_analyze):
        """平均分刚好 0.65 应判定为 positive（> 0.65）"""
        mock_analyze.side_effect = [
            {"score": 0.6, "label": "neutral", "emotion": "无感"},
            {"score": 0.7, "label": "positive", "emotion": "喜悦"},
        ]

        result = SentimentService.analyze_sequence(["还行", "好"], mode="simple")

        # avg = 0.65, 不大于 0.65, 所以是 neutral
        assert result["overall_sentiment"]["label"] == "neutral"

    @patch.object(SentimentService, 'analyze')
    def test_sequence_boundary_negative(self, mock_analyze):
        """平均分刚好 0.35 应判定为 neutral（< 0.35 为 negative）"""
        mock_analyze.side_effect = [
            {"score": 0.3, "label": "negative", "emotion": "悲伤"},
            {"score": 0.4, "label": "neutral", "emotion": "无感"},
        ]

        result = SentimentService.analyze_sequence(["差", "还行"], mode="simple")

        # avg = 0.35, 不小于 0.35, 所以是 neutral
        assert result["overall_sentiment"]["label"] == "neutral"

    @patch.object(SentimentService, 'analyze')
    def test_sequence_three_texts_with_multiple_changes(self, mock_analyze):
        """多文本序列应正确检测多个突变和情绪变化"""
        mock_analyze.side_effect = [
            {"score": 0.9, "label": "positive", "emotion": "喜悦"},
            {"score": 0.2, "label": "negative", "emotion": "悲伤"},
            {"score": 0.8, "label": "positive", "emotion": "喜悦"},
        ]

        result = SentimentService.analyze_sequence(["好", "差", "又好了"], mode="simple")

        assert result["analysis_count"] == 3
        assert len(result["sentiment_changes"]) == 2
        assert len(result["emotion_transitions"]) == 2
        # overall avg = (0.9 + 0.2 + 0.8) / 3 = 0.633, neutral
        assert result["overall_sentiment"]["label"] == "neutral"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
