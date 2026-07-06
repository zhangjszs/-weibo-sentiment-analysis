"""``src/utils/sentiment.py`` 单元测试（Phase 3.7 标签 schema 统一）。"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utils.sentiment import (  # noqa: E402
    LABEL_NEGATIVE,
    LABEL_NEUTRAL,
    LABEL_POSITIVE,
    analyze_sentiment_distribution,
    get_sentiment_color,
    get_sentiment_label,
    get_sentiment_score,
    label_to_chinese,
    label_to_english,
)


class TestLabelToChinese:
    def test_english_to_chinese(self):
        assert label_to_chinese(LABEL_POSITIVE) == "正面"
        assert label_to_chinese(LABEL_NEUTRAL) == "中性"
        assert label_to_chinese(LABEL_NEGATIVE) == "负面"

    def test_case_insensitive(self):
        assert label_to_chinese("POSITIVE") == "正面"
        assert label_to_chinese("Negative") == "负面"

    def test_chinese_passthrough(self):
        assert label_to_chinese("正面") == "正面"
        assert label_to_chinese("积极") == "正面"

    def test_unknown_label_returns_neutral(self):
        assert label_to_chinese("") == "中性"
        assert label_to_chinese("foobar") == "中性"
        assert label_to_chinese(None) == "中性"


class TestLabelToEnglish:
    def test_chinese_to_english(self):
        assert label_to_english("正面") == LABEL_POSITIVE
        assert label_to_english("积极") == LABEL_POSITIVE
        assert label_to_english("中性") == LABEL_NEUTRAL
        assert label_to_english("负面") == LABEL_NEGATIVE
        assert label_to_english("消极") == LABEL_NEGATIVE

    def test_english_passthrough(self):
        assert label_to_english(LABEL_POSITIVE) == LABEL_POSITIVE
        assert label_to_english("positive") == LABEL_POSITIVE

    def test_short_forms(self):
        assert label_to_english("pos") == LABEL_POSITIVE
        assert label_to_english("neu") == LABEL_NEUTRAL
        assert label_to_english("neg") == LABEL_NEGATIVE

    def test_unknown_returns_neutral(self):
        assert label_to_english("") == LABEL_NEUTRAL
        assert label_to_english("xxx") == LABEL_NEUTRAL


class TestGetSentimentLabel:
    def test_thresholds(self):
        # 阈值：>0.6 → positive, <0.4 → negative, 其余 neutral
        assert get_sentiment_label(0.8) == LABEL_POSITIVE
        assert get_sentiment_label(0.61) == LABEL_POSITIVE
        assert get_sentiment_label(0.6) == LABEL_NEUTRAL  # 不严格大于 0.6
        assert get_sentiment_label(0.4) == LABEL_NEUTRAL  # 不严格小于 0.4
        assert get_sentiment_label(0.5) == LABEL_NEUTRAL
        assert get_sentiment_label(0.39) == LABEL_NEGATIVE
        assert get_sentiment_label(0.2) == LABEL_NEGATIVE


class TestGetSentimentScore:
    def test_english_labels(self):
        assert get_sentiment_score(LABEL_POSITIVE) == 0.8
        assert get_sentiment_score(LABEL_NEUTRAL) == 0.5
        assert get_sentiment_score(LABEL_NEGATIVE) == 0.2

    def test_chinese_labels(self):
        assert get_sentiment_score("正面") == 0.8
        assert get_sentiment_score("积极") == 0.8
        assert get_sentiment_score("中性") == 0.5
        assert get_sentiment_score("负面") == 0.2
        assert get_sentiment_score("消极") == 0.2

    def test_unknown_label(self):
        assert get_sentiment_score("xxx") == 0.5


class TestGetSentimentColor:
    def test_color_per_label(self):
        assert get_sentiment_color(0.8) == "#67C23A"
        assert get_sentiment_color(0.5) == "#E6A23C"
        assert get_sentiment_color(0.2) == "#F56C6C"


class TestAnalyzeSentimentDistribution:
    def test_empty(self):
        d = analyze_sentiment_distribution([])
        assert d[LABEL_POSITIVE] == 0
        assert d[LABEL_NEUTRAL] == 0
        assert d[LABEL_NEGATIVE] == 0
        assert d["total"] == 0
        assert d["average"] == 0

    def test_distribution(self):
        scores = [0.9, 0.85, 0.5, 0.3, 0.1]
        d = analyze_sentiment_distribution(scores)
        assert d[LABEL_POSITIVE] == 2
        assert d[LABEL_NEUTRAL] == 1
        assert d[LABEL_NEGATIVE] == 2
        assert d["total"] == 5
        assert d["positive_ratio"] == pytest.approx(0.4, abs=1e-3)
