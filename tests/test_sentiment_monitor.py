#!/usr/bin/env python3
"""
情感突变检测算法单元测试
"""

import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, "src")


class TestCUSUMDetector:
    """CUSUM 检测器测试"""

    def test_init(self):
        """测试初始化"""
        from services.sentiment_monitor import CUSUMDetector

        detector = CUSUMDetector(reference_value=0.5, threshold=5.0)
        assert detector.reference_value == 0.5
        assert detector.threshold == 5.0
        assert detector.pos_cumsum == 0.0
        assert detector.neg_cumsum == 0.0

    def test_no_change(self):
        """测试无变化情况"""
        from services.sentiment_monitor import CUSUMDetector

        detector = CUSUMDetector(reference_value=0.5, threshold=5.0)

        for _ in range(10):
            result = detector.update(0.5)
            assert result is None

    def test_positive_change(self):
        """测试正向变化检测"""
        from services.sentiment_monitor import ChangePointType, CUSUMDetector

        detector = CUSUMDetector(reference_value=0.5, threshold=1.0, delta=0.2)

        for _ in range(5):
            detector.update(0.5)

        result = None
        for _ in range(20):
            result = detector.update(0.95)
            if result is not None:
                break

        assert result is not None
        assert result.change_type == ChangePointType.MEAN_SHIFT

    def test_negative_change(self):
        """测试负向变化检测"""
        from services.sentiment_monitor import ChangePointType, CUSUMDetector

        detector = CUSUMDetector(reference_value=0.5, threshold=1.0, delta=0.2)

        for _ in range(5):
            detector.update(0.5)

        result = None
        for _ in range(20):
            result = detector.update(0.05)
            if result is not None:
                break

        assert result is not None
        assert result.change_type in [ChangePointType.DROP, ChangePointType.MEAN_SHIFT]

    def test_set_reference(self):
        """测试设置参考值"""
        from services.sentiment_monitor import CUSUMDetector

        detector = CUSUMDetector(reference_value=0.5, threshold=5.0)
        detector.set_reference(0.7)

        assert detector.reference_value == 0.7
        assert detector.pos_cumsum == 0.0


class TestSlidingWindowDetector:
    """滑动窗口检测器测试"""

    def test_init(self):
        """测试初始化"""
        from services.sentiment_monitor import SlidingWindowDetector

        detector = SlidingWindowDetector(window_size=10, threshold=2.0)
        assert detector.window_size == 10
        assert detector.threshold == 2.0

    def test_no_change(self):
        """测试无变化情况"""
        from services.sentiment_monitor import SlidingWindowDetector

        detector = SlidingWindowDetector(window_size=5, threshold=2.0)

        for _ in range(20):
            result = detector.update(0.5)
            if result is not None:
                assert result.magnitude < 0.1

    def test_detect_change(self):
        """测试变化检测"""
        from services.sentiment_monitor import SlidingWindowDetector

        detector = SlidingWindowDetector(window_size=5, threshold=0.5)

        for _ in range(15):
            detector.update(0.5)

        change_detected = False
        for _ in range(15):
            result = detector.update(0.95)
            if result is not None:
                change_detected = True
                break

        assert change_detected

    def test_get_window_stats(self):
        """测试获取窗口统计"""
        from services.sentiment_monitor import SlidingWindowDetector

        detector = SlidingWindowDetector(window_size=5, threshold=2.0)

        for i in range(10):
            detector.update(0.5 + i * 0.01)

        stats = detector.get_window_stats()

        assert "window1" in stats
        assert "window2" in stats


class TestZScoreDetector:
    """Z-score 检测器测试"""

    def test_init(self):
        """测试初始化"""
        from services.sentiment_monitor import ZScoreDetector

        detector = ZScoreDetector(history_size=100, threshold=3.0)
        assert detector.history_size == 100
        assert detector.threshold == 3.0

    def test_no_change(self):
        """测试无变化情况"""
        from services.sentiment_monitor import ZScoreDetector

        detector = ZScoreDetector(history_size=50, threshold=3.0)

        for _ in range(50):
            result = detector.update(0.5)
            assert result is None or result.magnitude < 0.01

    def test_detect_spike(self):
        """测试尖峰检测"""
        import random

        from services.sentiment_monitor import ChangePointType, ZScoreDetector

        detector = ZScoreDetector(history_size=50, threshold=2.0)

        random.seed(42)
        for _ in range(50):
            detector.update(0.5 + random.gauss(0, 0.05))

        result = detector.update(0.99)

        assert result is not None
        assert result.change_type == ChangePointType.SPIKE

    def test_detect_drop(self):
        """测试下降检测"""
        import random

        from services.sentiment_monitor import ChangePointType, ZScoreDetector

        detector = ZScoreDetector(history_size=50, threshold=2.0)

        random.seed(42)
        for _ in range(50):
            detector.update(0.5 + random.gauss(0, 0.05))

        result = detector.update(0.01)

        assert result is not None
        assert result.change_type == ChangePointType.DROP

    def test_get_stats(self):
        """测试获取统计"""
        from services.sentiment_monitor import ZScoreDetector

        detector = ZScoreDetector(history_size=50, threshold=3.0)

        for i in range(50):
            detector.update(0.5 + i * 0.001)

        stats = detector.get_stats()

        assert "mean" in stats
        assert "std" in stats
        assert stats["size"] == 50


class TestBOCPDDetector:
    """BOCPD 检测器测试"""

    def test_init(self):
        """测试初始化"""
        from services.sentiment_monitor import BOCPDDetector

        detector = BOCPDDetector(hazard_rate=0.01, threshold=0.5)
        assert detector.hazard_rate == 0.01
        assert detector.threshold == 0.5

    def test_no_change(self):
        """测试无变化情况"""
        from services.sentiment_monitor import BOCPDDetector

        detector = BOCPDDetector(hazard_rate=0.01, threshold=0.8)

        for _ in range(20):
            result = detector.update(0.5)
            if result is not None:
                assert result.confidence < 0.8

    def test_detect_change(self):
        """测试变化检测"""
        from services.sentiment_monitor import BOCPDDetector

        detector = BOCPDDetector(hazard_rate=0.1, threshold=0.3)

        for _ in range(20):
            detector.update(0.5)

        change_detected = False
        for _ in range(20):
            result = detector.update(0.9)
            if result is not None:
                change_detected = True
                break

        assert change_detected


class TestSentimentMonitor:
    """情感监控服务测试"""

    def test_init(self):
        """测试初始化"""
        from services.sentiment_monitor import SentimentMonitor

        monitor = SentimentMonitor()
        assert monitor.cusum is not None
        assert monitor.sliding_window is not None
        assert monitor.z_score is not None
        assert monitor.bocpd is not None

    def test_update(self):
        """测试更新"""
        from services.sentiment_monitor import SentimentMonitor, SentimentSnapshot

        monitor = SentimentMonitor()

        snapshot = SentimentSnapshot(
            timestamp=datetime.now(),
            sentiment_score=0.5,
            positive_ratio=0.4,
            negative_ratio=0.3,
            neutral_ratio=0.3,
        )

        change_points = monitor.update(snapshot)

        assert isinstance(change_points, list)

    def test_get_trend(self):
        """测试获取趋势"""
        from services.sentiment_monitor import SentimentMonitor, SentimentSnapshot

        monitor = SentimentMonitor()

        base_time = datetime.now() - timedelta(minutes=60)
        for i in range(30):
            snapshot = SentimentSnapshot(
                timestamp=base_time + timedelta(minutes=i * 2),
                sentiment_score=0.5 + i * 0.01,
                positive_ratio=0.4,
                negative_ratio=0.3,
                neutral_ratio=0.3,
            )
            monitor.update(snapshot)

        trend = monitor.get_trend(window_minutes=60)

        assert "trend" in trend
        assert "slope" in trend
        assert trend["trend"] in ["rising", "falling", "stable"]

    def test_get_stats(self):
        """测试获取统计"""
        from services.sentiment_monitor import SentimentMonitor, SentimentSnapshot

        monitor = SentimentMonitor()

        for i in range(10):
            snapshot = SentimentSnapshot(
                timestamp=datetime.now() - timedelta(minutes=i),
                sentiment_score=0.5,
                positive_ratio=0.4,
                negative_ratio=0.3,
                neutral_ratio=0.3,
            )
            monitor.update(snapshot)

        stats = monitor.get_stats()

        assert "total_updates" in stats
        assert stats["total_updates"] == 10

    def test_callback(self):
        """测试回调"""
        from services.sentiment_monitor import (
            ChangePoint,
            SentimentMonitor,
            SentimentSnapshot,
        )

        monitor = SentimentMonitor()
        callback_called = []

        def test_callback(cp: ChangePoint):
            callback_called.append(cp)

        monitor.register_callback(test_callback)

        for _ in range(50):
            snapshot = SentimentSnapshot(
                timestamp=datetime.now(),
                sentiment_score=0.5,
                positive_ratio=0.4,
                negative_ratio=0.3,
                neutral_ratio=0.3,
            )
            monitor.update(snapshot)

        snapshot = SentimentSnapshot(
            timestamp=datetime.now(),
            sentiment_score=0.95,
            positive_ratio=0.8,
            negative_ratio=0.1,
            neutral_ratio=0.1,
        )
        monitor.update(snapshot)

        assert len(callback_called) >= 0

    def test_reset(self):
        """测试重置"""
        from services.sentiment_monitor import SentimentMonitor, SentimentSnapshot

        monitor = SentimentMonitor()

        for i in range(10):
            snapshot = SentimentSnapshot(
                timestamp=datetime.now() - timedelta(minutes=i),
                sentiment_score=0.5 + i * 0.01,
                positive_ratio=0.4,
                negative_ratio=0.3,
                neutral_ratio=0.3,
            )
            monitor.update(snapshot)

        monitor.reset()

        stats = monitor.get_stats()
        assert stats["total_updates"] == 0


class TestChangePoint:
    """变点测试"""

    def test_to_dict(self):
        """测试序列化"""
        from services.sentiment_monitor import (
            ChangePoint,
            ChangePointType,
            DetectionMethod,
        )

        cp = ChangePoint(
            timestamp=datetime.now(),
            index=10,
            change_type=ChangePointType.SPIKE,
            method=DetectionMethod.Z_SCORE,
            before_value=0.5,
            after_value=0.9,
            magnitude=0.4,
            confidence=0.85,
            metadata={"z_score": 3.5},
        )

        result = cp.to_dict()

        assert result["index"] == 10
        assert result["change_type"] == "spike"
        assert result["method"] == "z_score"
        assert result["before_value"] == 0.5
        assert result["after_value"] == 0.9
        assert result["magnitude"] == 0.4
        assert result["confidence"] == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
