#!/usr/bin/env python3
"""
预警数据模型（ORM）

P0 #5：``Alert`` / ``AlertRule`` 由 ``@dataclass`` 改为 SQLAlchemy ORM，持久化到
``alerts`` / ``alert_rules`` 两张表（见 Alembic 迁移 ``b2d5a3f9c0e1`` 与
init_database.sql）。``AlertHistory`` 合并入 ``alerts``（补 ``notes`` 列），其类与
``alert_history_service.py`` 一并移除（死代码）。

设计要点：
- 枚举 ``AlertLevel`` / ``AlertType`` / ``ThresholdOperator`` 保持不变，广泛被引用。
  ORM 用 ``sa.Enum(..., native_enum=False, values_callable=...)`` 存储 value
  （如 "warning"），与原 ``to_dict()`` 输出一致；加载时返回枚举成员，使引擎的
  ``rule.alert_type == AlertType.X`` 比较无需改动。
- ``ThresholdConfig`` 保留为 dataclass——作为 ``thresholds`` JSON 列的值对象载体，
  由 ``ThresholdListType`` 负责 List[ThresholdConfig] ↔ JSON 双向转换，使引擎
  ``rule.thresholds[0].evaluate(...)`` 无需改动。
- ``to_dict()`` 输出结构与原 dataclass 版本一致（``Alert`` 增补 ``notes`` 字段），
  保证 API 契约与前端、``notification_service.handle_alert`` 不受影响。
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Index,
    Integer,
    String,
    Text,
    TypeDecorator,
)

from database import Base


# ---------------------------------------------------------------------------
# 枚举（不变，广泛被引用）
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# ThresholdConfig：值对象（存于 AlertRule.thresholds JSON 列）
# ---------------------------------------------------------------------------


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


def _enum_values(enum_cls: type) -> List[str]:
    """供 SAEnum 使用：存储枚举的 value（小写字符串），而非 name。"""
    return [e.value for e in enum_cls]


class ThresholdListType(TypeDecorator):
    """``List[ThresholdConfig]`` ↔ JSON 双向转换。

    使引擎代码 ``rule.thresholds[0].evaluate(...)`` 无需改动：从 DB 加载时
    自动重建为 ``ThresholdConfig`` 对象列表；写入时序列化为 dict 列表存 JSON 列。
    """

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return [t.to_dict() if isinstance(t, ThresholdConfig) else t for t in value]

    def process_result_value(self, value, dialect):
        if not value:
            return []
        result: List[ThresholdConfig] = []
        for t in value:
            if isinstance(t, ThresholdConfig):
                result.append(t)
            elif isinstance(t, dict):
                result.append(
                    ThresholdConfig(
                        field=t["field"],
                        operator=ThresholdOperator(t["operator"]),
                        value=t["value"],
                        value_max=t.get("value_max"),
                        time_window_minutes=t.get("time_window_minutes", 30),
                    )
                )
        return result


# ---------------------------------------------------------------------------
# ORM 模型
# ---------------------------------------------------------------------------


class AlertRule(Base):
    """预警规则（持久化）"""

    __tablename__ = "alert_rules"
    __table_args__ = (
        Index("idx_alert_rules_enabled", "enabled"),
        Index("idx_alert_rules_priority", "priority"),
    )

    id = Column(String(64), primary_key=True)
    name = Column(String(200), nullable=False)
    alert_type = Column(
        SAEnum(
            AlertType,
            values_callable=_enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    level = Column(
        SAEnum(
            AlertLevel,
            values_callable=_enum_values,
            native_enum=False,
            length=16,
        ),
        nullable=False,
    )
    enabled = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    thresholds = Column(ThresholdListType, default=list)
    conditions = Column(JSON, default=dict)
    cooldown_minutes = Column(Integer, default=30, nullable=False)
    max_alerts_per_hour = Column(Integer, default=10, nullable=False)
    notification_channels = Column(JSON, default=lambda: ["websocket"])
    last_triggered = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    def __init__(self, **kwargs):
        # ORM Column default 仅 flush 时生效；此处补构造期默认，使直接构造后即可
        # 访问 enabled/cooldown_minutes 等（DB 加载走 __new__，不经此 __init__）
        super().__init__(**kwargs)
        if self.enabled is None:
            self.enabled = True
        if self.priority is None:
            self.priority = 0
        if self.thresholds is None:
            self.thresholds = []
        if self.conditions is None:
            self.conditions = {}
        if self.cooldown_minutes is None:
            self.cooldown_minutes = 30
        if self.max_alerts_per_hour is None:
            self.max_alerts_per_hour = 10
        if self.notification_channels is None:
            self.notification_channels = ["websocket"]
        if self.trigger_count is None:
            self.trigger_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "alert_type": self.alert_type.value if self.alert_type else None,
            "level": self.level.value if self.level else None,
            "enabled": self.enabled,
            "priority": self.priority,
            "thresholds": [t.to_dict() for t in (self.thresholds or [])],
            "conditions": self.conditions or {},
            "cooldown_minutes": self.cooldown_minutes,
            "max_alerts_per_hour": self.max_alerts_per_hour,
            "notification_channels": self.notification_channels or [],
            "last_triggered": self.last_triggered.isoformat()
            if self.last_triggered
            else None,
            "trigger_count": self.trigger_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Alert(Base):
    """预警消息（持久化，兼作历史——AlertHistory 已合并入此表）"""

    __tablename__ = "alerts"
    __table_args__ = (
        # 查询模式：历史列表按 created_at desc、未读过滤、按 level / rule_id 过滤
        Index("idx_alerts_created_at", "created_at"),
        Index("idx_alerts_is_read", "is_read"),
        Index("idx_alerts_level", "level"),
        Index("idx_alerts_rule_id", "rule_id"),
    )

    id = Column(String(36), primary_key=True)
    rule_id = Column(String(64))
    rule_name = Column(String(200))
    alert_type = Column(
        SAEnum(
            AlertType,
            values_callable=_enum_values,
            native_enum=False,
            length=32,
        )
    )
    level = Column(
        SAEnum(
            AlertLevel,
            values_callable=_enum_values,
            native_enum=False,
            length=16,
        )
    )
    title = Column(String(500))
    message = Column(Text)
    data = Column(JSON, default=dict)
    is_read = Column(Boolean, default=False, nullable=False)
    is_handled = Column(Boolean, default=False, nullable=False)
    handler = Column(String(255))
    handled_at = Column(DateTime)
    # P0 #5：由 AlertHistory 合并而来
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    def __init__(self, **kwargs):
        # ORM Column default 仅 flush 时生效；此处补构造期默认（DB 加载不经此 __init__）
        super().__init__(**kwargs)
        if self.is_read is None:
            self.is_read = False
        if self.is_handled is None:
            self.is_handled = False
        if self.data is None:
            self.data = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "alert_type": self.alert_type.value if self.alert_type else None,
            "level": self.level.value if self.level else None,
            "title": self.title,
            "message": self.message,
            "data": self.data or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
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
]
