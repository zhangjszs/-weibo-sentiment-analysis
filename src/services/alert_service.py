#!/usr/bin/env python3
"""
实时预警服务模块
功能：舆情预警规则引擎、阈值检测、情感突变检测、告警抑制
"""

import logging
import threading
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple

from models.alert import (
    Alert,
    AlertHistory,
    AlertLevel,
    AlertRule,
    AlertType,
    ThresholdConfig,
    ThresholdOperator,
)

logger = logging.getLogger(__name__)


class AlertSuppression:
    """告警抑制管理器"""

    def __init__(self):
        self._alert_counts: Dict[str, List[datetime]] = defaultdict(list)
        self._lock = threading.Lock()
        self._suppressed_count = 0

    def should_suppress(self, rule_id: str, max_per_hour: int = 10) -> bool:
        """检查是否应该抑制告警"""
        with self._lock:
            now = datetime.now()
            one_hour_ago = now - timedelta(hours=1)

            self._alert_counts[rule_id] = [
                t for t in self._alert_counts[rule_id] if t > one_hour_ago
            ]

            if len(self._alert_counts[rule_id]) >= max_per_hour:
                self._suppressed_count += 1
                return True

            self._alert_counts[rule_id].append(now)
            return False

    def get_stats(self) -> Dict:
        """获取抑制统计"""
        with self._lock:
            return {
                "suppressed_count": self._suppressed_count,
                "active_rules": len(self._alert_counts),
            }

    def reset(self, rule_id: Optional[str] = None):
        """重置抑制计数"""
        with self._lock:
            if rule_id:
                self._alert_counts.pop(rule_id, None)
            else:
                self._alert_counts.clear()
                self._suppressed_count = 0


class ThresholdValidator:
    """阈值验证器"""

    @staticmethod
    def validate_threshold(config: ThresholdConfig) -> Tuple[bool, str]:
        """验证阈值配置是否有效"""
        if not config.field:
            return False, "阈值字段不能为空"

        if config.value < 0:
            return False, "阈值不能为负数"

        if config.operator == ThresholdOperator.BETWEEN:
            if config.value_max is None:
                return False, "BETWEEN 运算符需要 value_max 参数"
            if config.value >= config.value_max:
                return False, "value 必须小于 value_max"

        if config.time_window_minutes < 1:
            return False, "时间窗口必须大于0分钟"

        return True, "验证通过"

    @staticmethod
    def validate_rule(rule: AlertRule) -> Tuple[bool, List[str]]:
        """验证预警规则"""
        errors = []

        if not rule.id:
            errors.append("规则ID不能为空")
        if not rule.name:
            errors.append("规则名称不能为空")
        if rule.cooldown_minutes < 0:
            errors.append("冷却时间不能为负数")
        if rule.max_alerts_per_hour < 1:
            errors.append("每小时最大告警数必须大于0")

        for i, threshold in enumerate(rule.thresholds):
            valid, msg = ThresholdValidator.validate_threshold(threshold)
            if not valid:
                errors.append(f"阈值{i + 1}: {msg}")

        return len(errors) == 0, errors


class ThresholdChecker:
    """阈值检查服务"""

    def __init__(self):
        self._metrics_cache: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        self._lock = threading.Lock()
        self._max_cache_size = 10000

    def record_metric(self, metric_name: str, value: float):
        """记录指标值"""
        with self._lock:
            self._metrics_cache[metric_name].append((datetime.now(), value))

            if len(self._metrics_cache[metric_name]) > self._max_cache_size:
                self._metrics_cache[metric_name] = self._metrics_cache[metric_name][
                    -self._max_cache_size :
                ]

    def get_metric_values(
        self, metric_name: str, time_window_minutes: int = 30
    ) -> List[float]:
        """获取时间窗口内的指标值"""
        with self._lock:
            now = datetime.now()
            cutoff = now - timedelta(minutes=time_window_minutes)

            values = [
                v for t, v in self._metrics_cache.get(metric_name, []) if t > cutoff
            ]
            return values

    def get_metric_stats(self, metric_name: str, time_window_minutes: int = 30) -> Dict:
        """获取指标统计"""
        values = self.get_metric_values(metric_name, time_window_minutes)

        if not values:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0, "latest": 0}

        return {
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "latest": values[-1],
        }

    def check_threshold(self, config: ThresholdConfig, current_value: float) -> bool:
        """检查是否触发阈值"""
        return config.evaluate(current_value)

    def check_multiple_thresholds(
        self, thresholds: List[ThresholdConfig], metric_values: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        """检查多个阈值（AND逻辑）"""
        triggered = True
        triggered_fields = []

        for threshold in thresholds:
            value = metric_values.get(threshold.field)
            if value is None:
                continue

            if threshold.evaluate(value):
                triggered_fields.append(threshold.field)
            else:
                triggered = False

        return triggered, triggered_fields


class AlertRuleEngine:
    """预警规则引擎"""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alert_history: List[Alert] = []
        self.max_history = 1000
        self._lock = threading.Lock()
        self._callbacks: List[Callable[[Alert], None]] = []
        self.suppression = AlertSuppression()
        self.threshold_checker = ThresholdChecker()
        self.validator = ThresholdValidator()

        self._init_default_rules()

    def _init_default_rules(self):
        """初始化默认预警规则"""
        default_rules = [
            AlertRule(
                id="negative_surge",
                name="负面舆情激增",
                alert_type=AlertType.NEGATIVE_SURGE,
                level=AlertLevel.DANGER,
                priority=100,
                thresholds=[
                    ThresholdConfig(
                        field="negative_count",
                        operator=ThresholdOperator.GREATER_THAN_OR_EQUAL,
                        value=50,
                        time_window_minutes=30,
                    )
                ],
                conditions={"negative_ratio_threshold": 0.3},
                cooldown_minutes=30,
                max_alerts_per_hour=5,
            ),
            AlertRule(
                id="volume_spike",
                name="讨论量异常增长",
                alert_type=AlertType.VOLUME_SPIKE,
                level=AlertLevel.WARNING,
                priority=80,
                thresholds=[
                    ThresholdConfig(
                        field="volume_multiplier",
                        operator=ThresholdOperator.GREATER_THAN_OR_EQUAL,
                        value=3.0,
                        time_window_minutes=60,
                    )
                ],
                conditions={"min_baseline": 10},
                cooldown_minutes=60,
                max_alerts_per_hour=3,
            ),
            AlertRule(
                id="sentiment_shift",
                name="情感倾向突变",
                alert_type=AlertType.SENTIMENT_SHIFT,
                level=AlertLevel.WARNING,
                priority=70,
                thresholds=[
                    ThresholdConfig(
                        field="sentiment_change",
                        operator=ThresholdOperator.GREATER_THAN_OR_EQUAL,
                        value=0.3,
                        time_window_minutes=30,
                    )
                ],
                cooldown_minutes=30,
                max_alerts_per_hour=5,
            ),
            AlertRule(
                id="hot_topic",
                name="热点话题出现",
                alert_type=AlertType.HOT_TOPIC,
                level=AlertLevel.INFO,
                priority=50,
                thresholds=[
                    ThresholdConfig(
                        field="topic_mentions",
                        operator=ThresholdOperator.GREATER_THAN_OR_EQUAL,
                        value=100,
                        time_window_minutes=60,
                    )
                ],
                cooldown_minutes=60,
                max_alerts_per_hour=10,
            ),
            AlertRule(
                id="keyword_match",
                name="敏感关键词匹配",
                alert_type=AlertType.KEYWORD_MATCH,
                level=AlertLevel.DANGER,
                priority=90,
                conditions={"keywords": [], "match_mode": "any"},
                cooldown_minutes=15,
                max_alerts_per_hour=20,
            ),
        ]

        for rule in default_rules:
            self.rules[rule.id] = rule

        logger.info(f"已加载 {len(self.rules)} 条默认预警规则")

    def add_rule(self, rule: AlertRule) -> Tuple[bool, str]:
        """添加预警规则"""
        valid, errors = self.validator.validate_rule(rule)
        if not valid:
            return False, "; ".join(errors)

        with self._lock:
            self.rules[rule.id] = rule
            logger.info(f"添加预警规则: {rule.name} (优先级: {rule.priority})")
        return True, "规则添加成功"

    def remove_rule(self, rule_id: str) -> bool:
        """移除预警规则"""
        with self._lock:
            if rule_id in self.rules:
                del self.rules[rule_id]
                self.suppression.reset(rule_id)
                logger.info(f"移除预警规则: {rule_id}")
                return True
            return False

    def update_rule(self, rule_id: str, **kwargs) -> Tuple[bool, str]:
        """更新预警规则"""
        with self._lock:
            if rule_id not in self.rules:
                return False, f"规则不存在: {rule_id}"

            rule = self.rules[rule_id]
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)

            rule.updated_at = datetime.now()

            valid, errors = self.validator.validate_rule(rule)
            if not valid:
                return False, "; ".join(errors)

            logger.info(f"更新预警规则: {rule_id}")
            return True, "规则更新成功"

    def register_callback(self, callback: Callable[[Alert], None]):
        """注册预警回调函数"""
        self._callbacks.append(callback)

    def _trigger_callbacks(self, alert: Alert):
        """触发回调函数"""
        for callback in self._callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"预警回调执行失败: {e}")

    def check_cooldown(self, rule: AlertRule) -> bool:
        """检查规则冷却时间"""
        if rule.last_triggered is None:
            return True

        elapsed = datetime.now() - rule.last_triggered
        return elapsed >= timedelta(minutes=rule.cooldown_minutes)

    def _create_alert(
        self, rule: AlertRule, title: str, message: str, data: Dict = None
    ) -> Alert:
        """创建预警消息"""
        alert = Alert(
            id=str(uuid.uuid4()),
            rule_id=rule.id,
            rule_name=rule.name,
            alert_type=rule.alert_type,
            level=rule.level,
            title=title,
            message=message,
            data=data or {},
        )
        return alert

    def _fire_alert(
        self, rule: AlertRule, title: str, message: str, data: Dict = None
    ) -> Optional[Alert]:
        """触发预警（带抑制检查）"""
        if self.suppression.should_suppress(rule.id, rule.max_alerts_per_hour):
            logger.debug(f"预警被抑制: {rule.name}")
            return None

        if not self.check_cooldown(rule):
            logger.debug(f"预警在冷却中: {rule.name}")
            return None

        rule.last_triggered = datetime.now()
        rule.trigger_count += 1

        alert = self._create_alert(rule, title, message, data)

        self._add_to_history(alert)
        self._trigger_callbacks(alert)

        logger.info(f"触发预警: {title} - {message}")
        return alert

    def check_alerts(self, metrics: Dict[str, float]) -> List[Alert]:
        """检查所有规则并触发预警"""
        triggered_alerts = []

        sorted_rules = sorted(
            self.rules.values(), key=lambda r: r.priority, reverse=True
        )

        for rule in sorted_rules:
            if not rule.enabled:
                continue

            alert = self._evaluate_rule(rule, metrics)
            if alert:
                triggered_alerts.append(alert)

        return triggered_alerts

    def _evaluate_rule(
        self, rule: AlertRule, metrics: Dict[str, float]
    ) -> Optional[Alert]:
        """评估单条规则"""
        if rule.alert_type == AlertType.NEGATIVE_SURGE:
            return self._evaluate_negative_surge(rule, metrics)
        elif rule.alert_type == AlertType.VOLUME_SPIKE:
            return self._evaluate_volume_spike(rule, metrics)
        elif rule.alert_type == AlertType.SENTIMENT_SHIFT:
            return self._evaluate_sentiment_shift(rule, metrics)
        elif rule.alert_type == AlertType.HOT_TOPIC:
            return self._evaluate_hot_topic(rule, metrics)
        elif rule.alert_type == AlertType.THRESHOLD_BREACH:
            return self._evaluate_threshold_breach(rule, metrics)
        return None

    def _evaluate_negative_surge(
        self, rule: AlertRule, metrics: Dict[str, float]
    ) -> Optional[Alert]:
        """评估负面舆情激增"""
        negative_count = metrics.get("negative_count", 0)
        total_count = metrics.get("total_count", 1)
        time_window = metrics.get("time_window_minutes", 30)

        if rule.thresholds:
            threshold = rule.thresholds[0]
            if not threshold.evaluate(negative_count):
                return None

        negative_ratio = negative_count / max(total_count, 1)
        ratio_threshold = rule.conditions.get("negative_ratio_threshold", 0.3)

        if negative_ratio >= ratio_threshold:
            return self._fire_alert(
                rule,
                title="负面舆情激增",
                message=f"过去{time_window}分钟内检测到{negative_count}条负面评论，占比{negative_ratio * 100:.1f}%",
                data={
                    "negative_count": negative_count,
                    "total_count": total_count,
                    "negative_ratio": negative_ratio,
                    "time_window": time_window,
                },
            )
        return None

    def _evaluate_volume_spike(
        self, rule: AlertRule, metrics: Dict[str, float]
    ) -> Optional[Alert]:
        """评估讨论量异常增长"""
        current_count = metrics.get("current_count", 0)
        baseline_count = metrics.get("baseline_count", 10)
        time_window = metrics.get("time_window_minutes", 60)

        min_baseline = rule.conditions.get("min_baseline", 10)
        if baseline_count < min_baseline:
            baseline_count = min_baseline

        multiplier = current_count / max(baseline_count, 1)

        if rule.thresholds:
            threshold = rule.thresholds[0]
            if not threshold.evaluate(multiplier):
                return None
        else:
            if multiplier < 3.0:
                return None

        return self._fire_alert(
            rule,
            title="讨论量异常增长",
            message=f"过去{time_window}分钟内讨论量达到{current_count}条，是基线{baseline_count}的{multiplier:.1f}倍",
            data={
                "current_count": current_count,
                "baseline_count": baseline_count,
                "multiplier": multiplier,
                "time_window": time_window,
            },
        )

    def _evaluate_sentiment_shift(
        self, rule: AlertRule, metrics: Dict[str, float]
    ) -> Optional[Alert]:
        """评估情感倾向突变"""
        current_sentiment = metrics.get("current_sentiment", 0.5)
        previous_sentiment = metrics.get("previous_sentiment", 0.5)
        time_window = metrics.get("time_window_minutes", 30)

        sentiment_change = abs(current_sentiment - previous_sentiment)

        if rule.thresholds:
            threshold = rule.thresholds[0]
            if not threshold.evaluate(sentiment_change):
                return None
        else:
            if sentiment_change < 0.3:
                return None

        direction = "下降" if current_sentiment < previous_sentiment else "上升"

        return self._fire_alert(
            rule,
            title="情感倾向突变",
            message=f"过去{time_window}分钟内情感指数{direction}{sentiment_change:.2f}，当前情感指数{current_sentiment:.2f}",
            data={
                "current_sentiment": current_sentiment,
                "previous_sentiment": previous_sentiment,
                "sentiment_change": sentiment_change,
                "direction": direction,
                "time_window": time_window,
            },
        )

    def _evaluate_hot_topic(
        self, rule: AlertRule, metrics: Dict[str, float]
    ) -> Optional[Alert]:
        """评估热点话题"""
        topic_mentions = metrics.get("topic_mentions", 0)
        topic_name = metrics.get("topic_name", "未知话题")
        time_window = metrics.get("time_window_minutes", 60)

        if rule.thresholds:
            threshold = rule.thresholds[0]
            if not threshold.evaluate(topic_mentions):
                return None
        else:
            if topic_mentions < 100:
                return None

        return self._fire_alert(
            rule,
            title="热点话题出现",
            message=f"话题「{topic_name}」在过去{time_window}分钟内被提及{topic_mentions}次",
            data={
                "topic_name": topic_name,
                "topic_mentions": topic_mentions,
                "time_window": time_window,
            },
        )

    def _evaluate_threshold_breach(
        self, rule: AlertRule, metrics: Dict[str, float]
    ) -> Optional[Alert]:
        """评估通用阈值突破"""
        if not rule.thresholds:
            return None

        triggered, fields = self.threshold_checker.check_multiple_thresholds(
            rule.thresholds, metrics
        )

        if triggered:
            return self._fire_alert(
                rule,
                title=f"阈值突破: {rule.name}",
                message=f"以下字段触发阈值: {', '.join(fields)}",
                data={
                    "triggered_fields": fields,
                    "metrics": {k: v for k, v in metrics.items() if k in fields},
                },
            )
        return None

    def evaluate_keyword_match(self, text: str, keywords: List[str]) -> Optional[Alert]:
        """评估关键词匹配"""
        rule = self.rules.get("keyword_match")
        if not rule or not rule.enabled:
            return None

        if not keywords:
            return None

        matched_keywords = [kw for kw in keywords if kw.lower() in text.lower()]

        if matched_keywords:
            return self._fire_alert(
                rule,
                title="敏感关键词匹配",
                message=f"检测到敏感关键词: {', '.join(matched_keywords)}",
                data={"matched_keywords": matched_keywords, "text_preview": text[:100]},
            )
        return None

    def _add_to_history(self, alert: Alert):
        """添加到预警历史"""
        with self._lock:
            self.alert_history.append(alert)
            if len(self.alert_history) > self.max_history:
                self.alert_history = self.alert_history[-self.max_history :]

    def get_alert_history(
        self, limit: int = 50, level: str = None, unread_only: bool = False
    ) -> List[Dict]:
        """获取预警历史"""
        with self._lock:
            alerts = self.alert_history.copy()

        if level:
            alerts = [a for a in alerts if a.level.value == level]

        if unread_only:
            alerts = [a for a in alerts if not a.is_read]

        alerts = sorted(alerts, key=lambda x: x.created_at, reverse=True)

        return [a.to_dict() for a in alerts[:limit]]

    def mark_alert_read(self, alert_id: str) -> bool:
        """标记预警已读"""
        with self._lock:
            for alert in self.alert_history:
                if alert.id == alert_id:
                    alert.is_read = True
                    return True
        return False

    def mark_all_read(self) -> int:
        """标记所有预警已读"""
        count = 0
        with self._lock:
            for alert in self.alert_history:
                if not alert.is_read:
                    alert.is_read = True
                    count += 1
        return count

    def get_unread_count(self) -> int:
        """获取未读预警数量"""
        with self._lock:
            return sum(1 for a in self.alert_history if not a.is_read)

    def get_rules(self) -> List[Dict]:
        """获取所有规则"""
        with self._lock:
            return [
                rule.to_dict()
                for rule in sorted(
                    self.rules.values(), key=lambda r: r.priority, reverse=True
                )
            ]

    def get_stats(self) -> Dict:
        """获取预警统计"""
        with self._lock:
            alerts = self.alert_history

        level_counts = defaultdict(int)
        type_counts = defaultdict(int)

        for alert in alerts:
            level_counts[alert.level.value] += 1
            type_counts[alert.alert_type.value] += 1

        return {
            "total_alerts": len(alerts),
            "unread_count": sum(1 for a in alerts if not a.is_read),
            "level_distribution": dict(level_counts),
            "type_distribution": dict(type_counts),
            "active_rules": sum(1 for r in self.rules.values() if r.enabled),
            "suppression_stats": self.suppression.get_stats(),
        }


alert_engine = AlertRuleEngine()


__all__ = [
    "AlertLevel",
    "AlertType",
    "ThresholdOperator",
    "ThresholdConfig",
    "AlertRule",
    "Alert",
    "AlertHistory",
    "AlertSuppression",
    "ThresholdValidator",
    "ThresholdChecker",
    "AlertRuleEngine",
    "alert_engine",
]
