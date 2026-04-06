#!/usr/bin/env python3
"""
情感分析服务单元测试
测试内容：
- 正常文本分析返回结果不为 None
- 空文本不抛异常
- 批量分析返回列表
- 结果包含 sentiment/score 字段
"""

import os
import sys
from unittest.mock import patch

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

    @patch('services.sentiment_service.Config')
    def test_smart_mode_no_api_key(self, mock_config):
        """smart 模式在没有 API key 时应该降级"""
        mock_config.LLM_API_KEY = None
        result = SentimentService.analyze("测试文本", mode="smart")
        assert result is not None
        assert "label" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
