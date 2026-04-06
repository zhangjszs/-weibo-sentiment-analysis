#!/usr/bin/env python3
"""
预警数据模型
功能：预警规则、预警历史的数据库映射
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AlertLevel(Enum):
    """预警级别"""

    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"


class AlertType(Enum):
    """预警类型"""

    VOLUME_SPIKE = "volume_spike"
    NEGATIVE_SURGE = "negative_surge"
    SENTIMENT_SHIFT = "sentiment_shift"
    KEYWORD_MATCH = "keyword_match"
    HOT_TOPIC = "hot_topic"
    THRESHOLD_BREACH = "threshold_breach"
    CUSTOM = "custom"


class ThresholdOperator(Enum):
    """阈值比较运算符"""

    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    BETWEEN = "between"


@dataclass
class ThresholdConfig:
    """阈值配置"""

    field: str
    operator: ThresholdOperator
    value: float
    value_max: Optional[float] = None
    time_window_minutes: int = 30

    def evaluate(self, current_value: float) -> bool:
        """评估当前值是否触发阈值"""
        if self.operator == ThresholdOperator.GREATER_THAN:
            return current_value > self.value
        elif self.operator == ThresholdOperator.GREATER_THAN_OR_EQUAL:
            return current_value >= self.value
        elif self.operator == ThresholdOperator.LESS_THAN:
            return current_value < self.value
        elif self.operator == ThresholdOperator.LESS_THAN_OR_EQUAL:
            return current_value <= self.value
        elif self.operator == ThresholdOperator.EQUAL:
            return abs(current_value - self.value) < 0.001
        elif self.operator == ThresholdOperator.NOT_EQUAL:
            return abs(current_value - self.value) >= 0.001
        elif self.operator == ThresholdOperator.BETWEEN:
            if self.value_max is None:
                return False
            return self.value <= current_value <= self.value_max
        return False

    def to_dict(self) -> Dict:
        return {
            "field": self.field,
            "operator": self.operator.value,
            "value": self.value,
            "value_max": self.value_max,
            "time_window_minutes": self.time_window_minutes,
        }


@dataclass
class AlertRule:
    """预警规则"""

    id: str
    name: str
    alert_type: AlertType
    level: AlertLevel
    enabled: bool = True
    priority: int = 0
    thresholds: List[ThresholdConfig] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    cooldown_minutes: int = 30
    max_alerts_per_hour: int = 10
    notification_channels: List[str] = field(default_factory=lambda: ["websocket"])
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "alert_type": self.alert_type.value,
            "level": self.level.value,
            "enabled": self.enabled,
            "priority": self.priority,
            "thresholds": [t.to_dict() for t in self.thresholds],
            "conditions": self.conditions,
            "cooldown_minutes": self.cooldown_minutes,
            "max_alerts_per_hour": self.max_alerts_per_hour,
            "notification_channels": self.notification_channels,
            "last_triggered": self.last_triggered.isoformat()
            if self.last_triggered
            else None,
            "trigger_count": self.trigger_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Alert:
    """预警消息"""

    id: str
    rule_id: str
    rule_name: str
    alert_type: AlertType
    level: AlertLevel
    title: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_read: bool = False
    is_handled: bool = False
    handler: Optional[str] = None
    handled_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "alert_type": self.alert_type.value,
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "is_read": self.is_read,
            "is_handled": self.is_handled,
            "handler": self.handler,
            "handled_at": self.handled_at.isoformat() if self.handled_at else None,
        }


@dataclass
class AlertHistory:
    """预警历史记录"""

    id: str
    rule_id: str
    alert_type: AlertType
    level: AlertLevel
    title: str
    message: str
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_read: bool = False
    is_handled: bool = False
    handler: Optional[str] = None
    handled_at: Optional[datetime] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "alert_type": self.alert_type.value,
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "trigger_data": self.trigger_data,
            "created_at": self.created_at.isoformat(),
            "is_read": self.is_read,
            "is_handled": self.is_handled,
            "handler": self.handler,
            "handled_at": self.handled_at.isoformat() if self.handled_at else None,
            "notes": self.notes,
        }


__all__ = [
    "AlertLevel",
    "AlertType",
    "ThresholdOperator",
    "ThresholdConfig",
    "AlertRule",
    "Alert",
    "AlertHistory",
]
