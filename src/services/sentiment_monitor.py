#!/usr/bin/env python3
"""
情感突变检测服务模块
功能：实时监测情感变化、突变点检测、趋势分析
算法：CUSUM、滑动窗口、Z-score、BOCPD
"""

import logging
import math
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ChangePointType(Enum):
    """变点类型"""

    MEAN_SHIFT = "mean_shift"
    VARIANCE_CHANGE = "variance_change"
    TREND_CHANGE = "trend_change"
    SPIKE = "spike"
    DROP = "drop"


class DetectionMethod(Enum):
    """检测方法"""

    CUSUM = "cusum"
    SLIDING_WINDOW = "sliding_window"
    Z_SCORE = "z_score"
    BOCPD = "bocpd"


@dataclass
class ChangePoint:
    """变点检测结果"""

    timestamp: datetime
    index: int
    change_type: ChangePointType
    method: DetectionMethod
    before_value: float
    after_value: float
    magnitude: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "index": self.index,
            "change_type": self.change_type.value,
            "method": self.method.value,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "magnitude": self.magnitude,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class SentimentSnapshot:
    """情感快照"""

    timestamp: datetime
    sentiment_score: float
    positive_ratio: float
    negative_ratio: float
    neutral_ratio: float
    volume: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class CUSUMDetector:
    """
    CUSUM 累积和检测器
    原理：通过计算累积偏差检测均值偏移
    """

    def __init__(
        self, reference_value: float = 0.0, threshold: float = 5.0, delta: float = 1.0
    ):
        self.reference_value = reference_value
        self.threshold = threshold
        self.delta = delta
        self.k = delta / 2
        self._reset()

    def _reset(self):
        self.pos_cumsum = 0.0
        self.neg_cumsum = 0.0
        self.detected_change = False

    def update(self, value: float) -> Optional[ChangePoint]:
        """更新检测器状态"""
        self.detected_change = False

        deviation = value - self.reference_value

        self.pos_cumsum = max(0, self.pos_cumsum + deviation - self.k)
        self.neg_cumsum = min(0, self.neg_cumsum + deviation + self.k)

        if self.pos_cumsum > self.threshold:
            self.detected_change = True
            change_type = ChangePointType.MEAN_SHIFT
            magnitude = self.pos_cumsum
            self._reset()
            return ChangePoint(
                timestamp=datetime.now(),
                index=0,
                change_type=change_type,
                method=DetectionMethod.CUSUM,
                before_value=self.reference_value,
                after_value=value,
                magnitude=magnitude,
                confidence=min(magnitude / self.threshold, 1.0),
            )

        if abs(self.neg_cumsum) > self.threshold:
            self.detected_change = True
            change_type = ChangePointType.DROP
            magnitude = abs(self.neg_cumsum)
            self._reset()
            return ChangePoint(
                timestamp=datetime.now(),
                index=0,
                change_type=change_type,
                method=DetectionMethod.CUSUM,
                before_value=self.reference_value,
                after_value=value,
                magnitude=magnitude,
                confidence=min(magnitude / self.threshold, 1.0),
            )

        return None

    def set_reference(self, value: float):
        """设置参考值"""
        self.reference_value = value
        self._reset()


class SlidingWindowDetector:
    """
    滑动窗口检测器
    原理：比较相邻窗口的统计量差异
    """

    def __init__(self, window_size: int = 30, threshold: float = 2.0):
        self.window_size = window_size
        self.threshold = threshold
        self.window1: deque = deque(maxlen=window_size)
        self.window2: deque = deque(maxlen=window_size)
        self._lock = threading.Lock()

    def update(self, value: float) -> Optional[ChangePoint]:
        """更新检测器状态"""
        with self._lock:
            self.window2.append(value)

            if len(self.window2) >= self.window_size:
                if len(self.window1) >= self.window_size:
                    mean1 = np.mean(self.window1)
                    mean2 = np.mean(self.window2)
                    std1 = np.std(self.window1)
                    std2 = np.std(self.window2)

                    pooled_std = math.sqrt((std1**2 + std2**2) / 2)
                    if pooled_std > 0:
                        t_stat = abs(mean2 - mean1) / pooled_std
                    else:
                        t_stat = 0

                    if t_stat > self.threshold:
                        change_type = ChangePointType.MEAN_SHIFT
                        if mean2 > mean1:
                            change_type = ChangePointType.SPIKE
                        elif mean2 < mean1:
                            change_type = ChangePointType.DROP

                        self.window1.clear()
                        self.window1.extend(self.window2)

                        return ChangePoint(
                            timestamp=datetime.now(),
                            index=0,
                            change_type=change_type,
                            method=DetectionMethod.SLIDING_WINDOW,
                            before_value=mean1,
                            after_value=mean2,
                            magnitude=abs(mean2 - mean1),
                            confidence=min(t_stat / self.threshold, 1.0),
                            metadata={"t_statistic": t_stat},
                        )

                self.window1.clear()
                self.window1.extend(self.window2)

            return None

    def get_window_stats(self) -> Dict:
        """获取窗口统计信息"""
        with self._lock:
            return {
                "window1": {
                    "size": len(self.window1),
                    "mean": np.mean(self.window1) if self.window1 else 0,
                    "std": np.std(self.window1) if self.window1 else 0,
                },
                "window2": {
                    "size": len(self.window2),
                    "mean": np.mean(self.window2) if self.window2 else 0,
                    "std": np.std(self.window2) if self.window2 else 0,
                },
            }


class ZScoreDetector:
    """
    Z-score 检测器
    原理：计算当前值与历史均值的标准化距离
    """

    def __init__(self, history_size: int = 100, threshold: float = 3.0):
        self.history_size = history_size
        self.threshold = threshold
        self.history: deque = deque(maxlen=history_size)
        self._lock = threading.Lock()

    def update(self, value: float) -> Optional[ChangePoint]:
        """更新检测器状态"""
        with self._lock:
            if len(self.history) < 10:
                self.history.append(value)
                return None

            mean = np.mean(self.history)
            std = np.std(self.history)

            if std > 0:
                z_score = (value - mean) / std
            else:
                z_score = 0

            self.history.append(value)

            if abs(z_score) > self.threshold:
                if z_score > 0:
                    change_type = ChangePointType.SPIKE
                else:
                    change_type = ChangePointType.DROP

                return ChangePoint(
                    timestamp=datetime.now(),
                    index=0,
                    change_type=change_type,
                    method=DetectionMethod.Z_SCORE,
                    before_value=mean,
                    after_value=value,
                    magnitude=abs(value - mean),
                    confidence=min(abs(z_score) / self.threshold, 1.0),
                    metadata={"z_score": z_score},
                )

            return None

    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self._lock:
            if not self.history:
                return {"mean": 0, "std": 0, "size": 0}
            return {
                "mean": np.mean(self.history),
                "std": np.std(self.history),
                "size": len(self.history),
            }


class BOCPDDetector:
    """
    贝叶斯在线变点检测器（简化版）
    原理：基于贝叶斯推断估计变点后验概率
    """

    def __init__(self, hazard_rate: float = 0.01, threshold: float = 0.5):
        self.hazard_rate = hazard_rate
        self.threshold = threshold
        self._reset()

    def _reset(self):
        self.run_lengths = [0]
        self.message = 1.0
        self.t = 0
        self.mean_estimate = 0.5
        self.variance_estimate = 0.1

    def _predictive_prob(self, x: float, run_length: int) -> float:
        """计算预测概率"""
        mean = self.mean_estimate
        var = max(self.variance_estimate, 0.01)
        return (1.0 / math.sqrt(2 * math.pi * var)) * math.exp(
            -0.5 * (x - mean) ** 2 / var
        )

    def update(self, value: float) -> Optional[ChangePoint]:
        """更新检测器状态"""
        self.t += 1

        new_run_lengths = []
        growth_probs = []

        for rl in self.run_lengths:
            pp = self._predictive_prob(value, rl)
            growth_prob = pp * (1 - self.hazard_rate)
            new_run_lengths.append(rl + 1)
            growth_probs.append(growth_prob)

        cp_prob = sum(growth_probs) * self.hazard_rate
        new_run_lengths.insert(0, 0)
        growth_probs.insert(0, cp_prob)

        total = sum(growth_probs)
        if total > 0:
            growth_probs = [p / total for p in growth_probs]

        self.run_lengths = new_run_lengths

        max_run_length = self.run_lengths[growth_probs.index(max(growth_probs))]

        self.mean_estimate = 0.9 * self.mean_estimate + 0.1 * value
        self.variance_estimate = (
            0.9 * self.variance_estimate + 0.1 * (value - self.mean_estimate) ** 2
        )

        if max_run_length == 0 and cp_prob > self.threshold:
            return ChangePoint(
                timestamp=datetime.now(),
                index=self.t,
                change_type=ChangePointType.MEAN_SHIFT,
                method=DetectionMethod.BOCPD,
                before_value=self.mean_estimate,
                after_value=value,
                magnitude=abs(value - self.mean_estimate),
                confidence=min(cp_prob, 1.0),
                metadata={"run_length": max_run_length, "cp_probability": cp_prob},
            )

        return None


class SentimentMonitor:
    """
    情感监控服务
    整合多种检测算法，提供统一的监控接口
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self._lock = threading.Lock()

        self.cusum = CUSUMDetector(
            reference_value=self.config.get("cusum_reference", 0.5),
            threshold=self.config.get("cusum_threshold", 5.0),
            delta=self.config.get("cusum_delta", 1.0),
        )

        self.sliding_window = SlidingWindowDetector(
            window_size=self.config.get("window_size", 30),
            threshold=self.config.get("window_threshold", 2.0),
        )

        self.z_score = ZScoreDetector(
            history_size=self.config.get("history_size", 100),
            threshold=self.config.get("z_threshold", 3.0),
        )

        self.bocpd = BOCPDDetector(
            hazard_rate=self.config.get("hazard_rate", 0.01),
            threshold=self.config.get("bocpd_threshold", 0.5),
        )

        self.snapshots: deque = deque(maxlen=1000)
        self.change_points: List[ChangePoint] = []
        self._callbacks: List[Callable[[ChangePoint], None]] = []

        self._stats = {
            "total_updates": 0,
            "change_points_detected": 0,
            "by_method": {m.value: 0 for m in DetectionMethod},
        }

    def register_callback(self, callback: Callable[[ChangePoint], None]):
        """注册变点回调"""
        self._callbacks.append(callback)

    def _trigger_callbacks(self, change_point: ChangePoint):
        """触发回调"""
        for callback in self._callbacks:
            try:
                callback(change_point)
            except Exception as e:
                logger.error(f"回调执行失败: {e}")

    def update(self, snapshot: SentimentSnapshot) -> List[ChangePoint]:
        """更新监控状态"""
        with self._lock:
            self.snapshots.append(snapshot)
            self._stats["total_updates"] += 1

            change_points = []

            cp = self.cusum.update(snapshot.sentiment_score)
            if cp:
                cp.index = len(self.snapshots) - 1
                change_points.append(cp)
                self._stats["by_method"]["cusum"] += 1

            cp = self.sliding_window.update(snapshot.sentiment_score)
            if cp:
                cp.index = len(self.snapshots) - 1
                change_points.append(cp)
                self._stats["by_method"]["sliding_window"] += 1

            cp = self.z_score.update(snapshot.sentiment_score)
            if cp:
                cp.index = len(self.snapshots) - 1
                change_points.append(cp)
                self._stats["by_method"]["z_score"] += 1

            cp = self.bocpd.update(snapshot.sentiment_score)
            if cp:
                cp.index = len(self.snapshots) - 1
                change_points.append(cp)
                self._stats["by_method"]["bocpd"] += 1

            for cp in change_points:
                self.change_points.append(cp)
                self._stats["change_points_detected"] += 1
                self._trigger_callbacks(cp)

            return change_points

    def get_trend(self, window_minutes: int = 30) -> Dict:
        """获取情感趋势"""
        with self._lock:
            if not self.snapshots:
                return {"trend": "unknown", "slope": 0}

            cutoff = datetime.now() - timedelta(minutes=window_minutes)
            recent = [s for s in self.snapshots if s.timestamp > cutoff]

            if len(recent) < 2:
                return {"trend": "unknown", "slope": 0}

            scores = [s.sentiment_score for s in recent]
            x = np.arange(len(scores))
            slope = np.polyfit(x, scores, 1)[0]

            if slope > 0.01:
                trend = "rising"
            elif slope < -0.01:
                trend = "falling"
            else:
                trend = "stable"

            return {
                "trend": trend,
                "slope": slope,
                "mean": np.mean(scores),
                "std": np.std(scores),
                "count": len(recent),
            }

    def get_stats(self) -> Dict:
        """获取监控统计"""
        with self._lock:
            return {
                **self._stats,
                "snapshot_count": len(self.snapshots),
                "change_point_count": len(self.change_points),
                "cusum_stats": {
                    "reference": self.cusum.reference_value,
                    "pos_cumsum": self.cusum.pos_cumsum,
                    "neg_cumsum": self.cusum.neg_cumsum,
                },
                "z_score_stats": self.z_score.get_stats(),
                "window_stats": self.sliding_window.get_window_stats(),
            }

    def get_recent_change_points(self, limit: int = 20) -> List[Dict]:
        """获取最近的变点"""
        with self._lock:
            return [cp.to_dict() for cp in self.change_points[-limit:]]

    def reset(self):
        """重置监控器"""
        with self._lock:
            self.cusum._reset()
            self.sliding_window.window1.clear()
            self.sliding_window.window2.clear()
            self.z_score.history.clear()
            self.bocpd._reset()
            self.snapshots.clear()
            self.change_points.clear()
            self._stats = {
                "total_updates": 0,
                "change_points_detected": 0,
                "by_method": {m.value: 0 for m in DetectionMethod},
            }


sentiment_monitor = SentimentMonitor()


__all__ = [
    "ChangePointType",
    "DetectionMethod",
    "ChangePoint",
    "SentimentSnapshot",
    "CUSUMDetector",
    "SlidingWindowDetector",
    "ZScoreDetector",
    "BOCPDDetector",
    "SentimentMonitor",
    "sentiment_monitor",
]
