#!/usr/bin/env python3
"""
预警服务单元测试（P0 #5：DB 持久化适配）

测试内容：
- alert_engine.get_rules() 返回 list（DB 查询）
- AlertRule 构造正常（含构造期默认值）
- AlertType / AlertLevel 枚举值有效
- 重复 rule_id 被 DB PK 拒绝
- 规则启用/禁用切换（update_rule 持久化）
- check_alerts 端到端规则触发（规则从 DB 加载）
- _fire_alert 抑制/冷却路径（预警写 alerts 表）
- 预警历史/已读状态/统计（DB 聚合查询）

DB fixture：in-memory SQLite + scoped_session，monkeypatch ``database.db_session``。
引擎方法内部 ``from database import db_session`` 在调用时读取 ``database.db_session``
模块属性，故 patch 该属性即可让引擎读写测试 SQLite。``expire_on_commit=False``
使 _fire_alert 返回的 alert/rule 对象提交后属性仍可直接访问。
"""

import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.alert_service import (
    Alert,
    AlertLevel,
    AlertRule,
    AlertRuleEngine,
    AlertSuppression,
    AlertType,
    ThresholdChecker,
    ThresholdConfig,
    ThresholdOperator,
    ThresholdValidator,
)


# ---------------------------------------------------------------------------
# DB fixtures（alert_db / alert_engine 已在 conftest.py 共享；此处 engine 为
# test_alert_service 本地别名，依赖 conftest 的 alert_db 并 seed 默认规则）
# ---------------------------------------------------------------------------


@pytest.fixture
def engine(alert_db):
    """DB-backed 引擎实例，已 seed 5 条默认规则。"""
    eng = AlertRuleEngine()
    eng._ensure_defaults_seeded()
    return eng


# ---------------------------------------------------------------------------
# 纯内存测试（无需 DB）
# ---------------------------------------------------------------------------


class TestAlertEnums:
    """测试 AlertType 和 AlertLevel 枚举"""

    def test_alert_type_values(self):
        assert AlertType.NEGATIVE_SURGE.value == "negative_surge"
        assert AlertType.VOLUME_SPIKE.value == "volume_spike"
        assert AlertType.SENTIMENT_SHIFT.value == "sentiment_shift"
        assert AlertType.HOT_TOPIC.value == "hot_topic"
        assert AlertType.KEYWORD_MATCH.value == "keyword_match"
        assert AlertType.THRESHOLD_BREACH.value == "threshold_breach"
        assert AlertType.CUSTOM.value == "custom"

    def test_alert_level_values(self):
        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.DANGER.value == "danger"
        assert AlertLevel.CRITICAL.value == "critical"

    def test_alert_type_from_string(self):
        assert AlertType("negative_surge") == AlertType.NEGATIVE_SURGE

    def test_alert_level_from_string(self):
        assert AlertLevel("warning") == AlertLevel.WARNING


class TestAlertRule:
    """测试 AlertRule 构造（构造期默认值）"""

    def test_alert_rule_construction(self):
        rule = AlertRule(
            id="test_rule",
            name="测试规则",
            alert_type=AlertType.NEGATIVE_SURGE,
            level=AlertLevel.WARNING,
            priority=50,
        )
        assert rule.id == "test_rule"
        assert rule.name == "测试规则"
        assert rule.alert_type == AlertType.NEGATIVE_SURGE
        assert rule.level == AlertLevel.WARNING
        assert rule.priority == 50
        assert rule.enabled is True  # 构造期默认启用

    def test_alert_rule_with_thresholds(self):
        threshold = ThresholdConfig(
            field="negative_count",
            operator=ThresholdOperator.GREATER_THAN_OR_EQUAL,
            value=50,
            time_window_minutes=30,
        )
        rule = AlertRule(
            id="threshold_rule",
            name="阈值测试规则",
            alert_type=AlertType.THRESHOLD_BREACH,
            level=AlertLevel.DANGER,
            thresholds=[threshold],
        )
        assert len(rule.thresholds) == 1
        assert rule.thresholds[0].field == "negative_count"


class TestAlertSuppression:
    """测试告警抑制功能（纯内存）"""

    def test_suppression_should_suppress(self):
        suppression = AlertSuppression()
        rule_id = "test_suppression"
        for _ in range(10):
            assert suppression.should_suppress(rule_id, max_per_hour=10) is False
        assert suppression.should_suppress(rule_id, max_per_hour=10) is True

    def test_suppression_stats(self):
        suppression = AlertSuppression()
        rule_id = "test_stats"
        for _ in range(15):
            suppression.should_suppress(rule_id, max_per_hour=5)
        stats = suppression.get_stats()
        assert stats["suppressed_count"] == 10  # 15-5=10


class TestThresholdValidator:
    """测试阈值验证器（纯内存）"""

    def test_validate_threshold_valid(self):
        config = ThresholdConfig(
            field="count",
            operator=ThresholdOperator.GREATER_THAN_OR_EQUAL,
            value=10,
            time_window_minutes=30,
        )
        valid, msg = ThresholdValidator.validate_threshold(config)
        assert valid is True
        assert msg == "验证通过"

    def test_validate_threshold_empty_field(self):
        config = ThresholdConfig(
            field="",
            operator=ThresholdOperator.GREATER_THAN_OR_EQUAL,
            value=10,
            time_window_minutes=30,
        )
        valid, msg = ThresholdValidator.validate_threshold(config)
        assert valid is False
        assert "阈值字段不能为空" in msg

    def test_validate_threshold_negative_value(self):
        config = ThresholdConfig(
            field="count",
            operator=ThresholdOperator.GREATER_THAN_OR_EQUAL,
            value=-1,
            time_window_minutes=30,
        )
        valid, msg = ThresholdValidator.validate_threshold(config)
        assert valid is False
        assert "阈值不能为负数" in msg


class TestAlertSuppressionReset:
    def test_reset_by_rule_id(self):
        sup = AlertSuppression()
        sup.should_suppress("rule_a", max_per_hour=5)
        sup.should_suppress("rule_b", max_per_hour=5)
        sup.reset("rule_a")
        assert sup.get_stats()["active_rules"] == 1

    def test_reset_all(self):
        sup = AlertSuppression()
        for _ in range(10):
            sup.should_suppress("rule_a", max_per_hour=3)
        assert sup.get_stats()["suppressed_count"] == 7
        sup.reset()
        stats = sup.get_stats()
        assert stats["suppressed_count"] == 0
        assert stats["active_rules"] == 0


class TestThresholdValidatorEdgeCases:
    def test_validate_threshold_between_no_value_max(self):
        config = ThresholdConfig(
            field="count",
            operator=ThresholdOperator.BETWEEN,
            value=10,
            time_window_minutes=30,
        )
        valid, msg = ThresholdValidator.validate_threshold(config)
        assert valid is False
        assert "value_max" in msg

    def test_validate_threshold_between_value_gte_max(self):
        config = ThresholdConfig(
            field="count",
            operator=ThresholdOperator.BETWEEN,
            value=20,
            value_max=15,
            time_window_minutes=30,
        )
        valid, msg = ThresholdValidator.validate_threshold(config)
        assert valid is False
        assert "value 必须小于 value_max" in msg

    def test_validate_threshold_between_valid(self):
        config = ThresholdConfig(
            field="count",
            operator=ThresholdOperator.BETWEEN,
            value=10,
            value_max=20,
            time_window_minutes=30,
        )
        valid, _ = ThresholdValidator.validate_threshold(config)
        assert valid is True

    def test_validate_threshold_time_window_zero(self):
        config = ThresholdConfig(
            field="count",
            operator=ThresholdOperator.GREATER_THAN_OR_EQUAL,
            value=10,
            time_window_minutes=0,
        )
        valid, msg = ThresholdValidator.validate_threshold(config)
        assert valid is False
        assert "时间窗口" in msg

    def test_validate_rule_empty_id(self):
        rule = AlertRule(id="", name="测试", alert_type=AlertType.CUSTOM, level=AlertLevel.INFO)
        valid, errors = ThresholdValidator.validate_rule(rule)
        assert valid is False
        assert any("规则ID" in e for e in errors)

    def test_validate_rule_empty_name(self):
        rule = AlertRule(id="test", name="", alert_type=AlertType.CUSTOM, level=AlertLevel.INFO)
        valid, errors = ThresholdValidator.validate_rule(rule)
        assert valid is False
        assert any("规则名称" in e for e in errors)

    def test_validate_rule_negative_cooldown(self):
        rule = AlertRule(
            id="test", name="测试", alert_type=AlertType.CUSTOM,
            level=AlertLevel.INFO, cooldown_minutes=-1,
        )
        valid, errors = ThresholdValidator.validate_rule(rule)
        assert valid is False
        assert any("冷却时间" in e for e in errors)

    def test_validate_rule_max_alerts_zero(self):
        rule = AlertRule(
            id="test", name="测试", alert_type=AlertType.CUSTOM,
            level=AlertLevel.INFO, max_alerts_per_hour=0,
        )
        valid, errors = ThresholdValidator.validate_rule(rule)
        assert valid is False
        assert any("每小时最大告警数" in e for e in errors)

    def test_validate_rule_with_invalid_threshold(self):
        rule = AlertRule(
            id="test", name="测试", alert_type=AlertType.CUSTOM,
            level=AlertLevel.INFO,
            thresholds=[
                ThresholdConfig(
                    field="", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL,
                    value=10, time_window_minutes=30,
                ),
            ],
        )
        valid, errors = ThresholdValidator.validate_rule(rule)
        assert valid is False
        assert any("阈值1" in e for e in errors)


class TestThresholdChecker:
    """测试 ThresholdChecker（纯内存）"""

    def test_record_metric_and_get_values(self):
        checker = ThresholdChecker()
        checker.record_metric("test", 10.0)
        checker.record_metric("test", 20.0)
        checker.record_metric("test", 30.0)
        assert checker.get_metric_values("test", time_window_minutes=30) == [10.0, 20.0, 30.0]

    def test_get_metric_values_nonexistent(self):
        assert ThresholdChecker().get_metric_values("nonexistent") == []

    def test_record_metric_cache_trim(self):
        checker = ThresholdChecker()
        checker._max_cache_size = 3
        for v in [10.0, 20.0, 30.0, 40.0]:
            checker.record_metric("test", v)
        assert checker.get_metric_values("test") == [20.0, 30.0, 40.0]

    def test_get_metric_stats_with_values(self):
        checker = ThresholdChecker()
        checker.record_metric("test", 10.0)
        checker.record_metric("test", 20.0)
        checker.record_metric("test", 30.0)
        stats = checker.get_metric_stats("test")
        assert stats["count"] == 3
        assert stats["sum"] == 60.0
        assert stats["avg"] == 20.0
        assert stats["min"] == 10.0
        assert stats["max"] == 30.0
        assert stats["latest"] == 30.0

    def test_get_metric_stats_empty(self):
        stats = ThresholdChecker().get_metric_stats("nonexistent")
        assert stats["count"] == 0
        assert stats["sum"] == 0
        assert stats["avg"] == 0

    def test_check_threshold(self):
        checker = ThresholdChecker()
        config = ThresholdConfig(
            field="count", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=10
        )
        assert checker.check_threshold(config, 20) is True
        assert checker.check_threshold(config, 5) is False

    def test_check_multiple_thresholds_all_met(self):
        checker = ThresholdChecker()
        thresholds = [
            ThresholdConfig(field="count", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=10),
            ThresholdConfig(field="ratio", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=0.3),
        ]
        triggered, fields = checker.check_multiple_thresholds(thresholds, {"count": 20, "ratio": 0.5})
        assert triggered is True
        assert set(fields) == {"count", "ratio"}

    def test_check_multiple_thresholds_one_not_met(self):
        checker = ThresholdChecker()
        thresholds = [
            ThresholdConfig(field="count", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=10),
            ThresholdConfig(field="ratio", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=0.3),
        ]
        triggered, fields = checker.check_multiple_thresholds(thresholds, {"count": 20, "ratio": 0.1})
        assert triggered is False
        assert "count" in fields
        assert "ratio" not in fields

    def test_check_multiple_thresholds_field_not_in_metrics(self):
        checker = ThresholdChecker()
        thresholds = [
            ThresholdConfig(field="count", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=10),
            ThresholdConfig(field="missing", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=10),
        ]
        triggered, fields = checker.check_multiple_thresholds(thresholds, {"count": 20})
        assert triggered is True
        assert fields == ["count"]


class TestAlertCreation:
    """测试预警创建（构造期默认值 + to_dict）"""

    def test_alert_creation(self):
        alert = Alert(
            id="alert_001",
            rule_id="rule_001",
            rule_name="测试规则",
            alert_type=AlertType.NEGATIVE_SURGE,
            level=AlertLevel.WARNING,
            title="测试预警",
            message="这是一条测试预警消息",
        )
        assert alert.id == "alert_001"
        assert alert.rule_id == "rule_001"
        assert alert.title == "测试预警"
        assert alert.is_read is False  # 构造期默认未读

    def test_alert_to_dict(self):
        alert = Alert(
            id="alert_002",
            rule_id="rule_002",
            rule_name="测试规则",
            alert_type=AlertType.VOLUME_SPIKE,
            level=AlertLevel.DANGER,
            title="测试预警",
            message="这是一条测试预警消息",
        )
        data = alert.to_dict()
        assert isinstance(data, dict)
        assert data["id"] == "alert_002"
        assert data["title"] == "测试预警"
        assert data["level"] == "danger"


# ---------------------------------------------------------------------------
# DB-backed 测试
# ---------------------------------------------------------------------------


class TestAlertRuleEngine:
    """测试预警规则引擎（DB 查询）"""

    def test_get_rules_returns_list(self, engine):
        rules = engine.get_rules()
        assert isinstance(rules, list)
        assert len(rules) == 5  # 默认 5 条规则

    def test_get_rules_contains_rule_data(self, engine):
        rules = engine.get_rules()
        assert rules  # 非空
        rule = rules[0]
        assert "id" in rule
        assert "name" in rule
        assert "enabled" in rule
        assert "priority" in rule


class TestDuplicateRuleId:
    """测试重复 rule_id 处理（DB PK 约束）"""

    def test_duplicate_rule_id_rejected(self, engine):
        # P0 #5：DB 主键约束——重复 id 不再覆盖，而是被拒绝
        rule1 = AlertRule(
            id="duplicate_test", name="规则1",
            alert_type=AlertType.CUSTOM, level=AlertLevel.INFO,
        )
        assert engine.add_rule(rule1)[0] is True

        rule2 = AlertRule(
            id="duplicate_test", name="规则2",
            alert_type=AlertType.CUSTOM, level=AlertLevel.WARNING,
        )
        success, _ = engine.add_rule(rule2)
        assert success is False  # PK 冲突，DB 拒绝

        # 原规则未被覆盖
        rules = [r for r in engine.get_rules() if r["id"] == "duplicate_test"]
        assert len(rules) == 1
        assert rules[0]["name"] == "规则1"


class TestRuleToggle:
    """测试规则启用/禁用切换（update_rule 持久化）"""

    def test_rule_toggle_disable(self, engine):
        rule = AlertRule(
            id="toggle_test", name="切换测试规则",
            alert_type=AlertType.CUSTOM, level=AlertLevel.INFO, enabled=True,
        )
        engine.add_rule(rule)
        assert engine.update_rule("toggle_test", enabled=False)[0] is True
        rules = engine.get_rules()
        toggle_rule = next((r for r in rules if r["id"] == "toggle_test"), None)
        assert toggle_rule is not None
        assert toggle_rule["enabled"] is False

    def test_rule_toggle_enable(self, engine):
        rule = AlertRule(
            id="toggle_test2", name="切换测试规则2",
            alert_type=AlertType.CUSTOM, level=AlertLevel.INFO, enabled=False,
        )
        engine.add_rule(rule)
        assert engine.update_rule("toggle_test2", enabled=True)[0] is True
        rules = engine.get_rules()
        toggle_rule = next((r for r in rules if r["id"] == "toggle_test2"), None)
        assert toggle_rule["enabled"] is True


class TestCheckAlerts:
    """测试 check_alerts 端到端规则触发（规则从 DB 加载）"""

    def test_check_alerts_negative_surge_triggered(self, engine):
        metrics = {"negative_count": 60, "total_count": 100, "time_window_minutes": 30}
        alerts = engine.check_alerts(metrics)
        assert len(alerts) > 0
        assert any(a.alert_type == AlertType.NEGATIVE_SURGE for a in alerts)

    def test_check_alerts_volume_spike_triggered(self, engine):
        metrics = {"current_count": 50, "baseline_count": 10, "time_window_minutes": 60}
        alerts = engine.check_alerts(metrics)
        assert len(alerts) > 0
        assert any(a.alert_type == AlertType.VOLUME_SPIKE for a in alerts)

    def test_check_alerts_sentiment_shift_triggered(self, engine):
        metrics = {
            "current_sentiment": 0.2, "previous_sentiment": 0.6, "time_window_minutes": 30,
        }
        alerts = engine.check_alerts(metrics)
        assert len(alerts) > 0
        assert any(a.alert_type == AlertType.SENTIMENT_SHIFT for a in alerts)

    def test_check_alerts_hot_topic_triggered(self, engine):
        metrics = {"topic_mentions": 150, "topic_name": "测试话题", "time_window_minutes": 60}
        alerts = engine.check_alerts(metrics)
        assert len(alerts) > 0
        assert any(a.alert_type == AlertType.HOT_TOPIC for a in alerts)

    def test_check_alerts_no_trigger_when_disabled(self, engine):
        # 禁用所有默认规则
        for r in engine.get_rules():
            engine.update_rule(r["id"], enabled=False)
        metrics = {"negative_count": 100, "total_count": 150, "time_window_minutes": 30}
        assert engine.check_alerts(metrics) == []

    def test_check_alerts_no_trigger_below_threshold(self, engine):
        metrics = {"negative_count": 10, "total_count": 100, "time_window_minutes": 30}
        alerts = engine.check_alerts(metrics)
        negative_surge_alerts = [a for a in alerts if a.alert_type == AlertType.NEGATIVE_SURGE]
        assert negative_surge_alerts == []

    def test_check_alerts_returns_alert_objects(self, engine):
        metrics = {"negative_count": 60, "total_count": 100, "time_window_minutes": 30}
        alerts = engine.check_alerts(metrics)
        for alert in alerts:
            assert isinstance(alert, Alert)
            assert alert.id is not None
            assert alert.rule_id is not None
            assert alert.title is not None

    def test_check_alerts_priority_order(self, engine):
        high_priority_rule = AlertRule(
            id="high_priority_test", name="高优先级测试规则",
            alert_type=AlertType.CUSTOM, level=AlertLevel.CRITICAL, priority=200, enabled=True,
        )
        engine.add_rule(high_priority_rule)
        metrics = {
            "negative_count": 60, "total_count": 100, "time_window_minutes": 30,
            "current_count": 50, "baseline_count": 10,
        }
        alerts = engine.check_alerts(metrics)
        assert len(alerts) > 0


class TestAlertRuleEngineRuleManagement:
    """测试规则管理（add/remove/update，DB 持久化）"""

    def test_add_rule_invalid_returns_error(self, engine):
        rule = AlertRule(id="", name="无效", alert_type=AlertType.CUSTOM, level=AlertLevel.INFO)
        success, msg = engine.add_rule(rule)
        assert success is False
        assert "规则ID" in msg

    def test_remove_rule_existing(self, engine):
        assert engine.remove_rule("hot_topic") is True
        assert engine.get_rule("hot_topic") is None

    def test_remove_rule_nonexistent(self, engine):
        assert engine.remove_rule("nonexistent") is False

    def test_update_rule_nonexistent(self, engine):
        success, msg = engine.update_rule("nonexistent", enabled=False)
        assert success is False
        assert "规则不存在" in msg

    def test_update_rule_validation_failure(self, engine):
        success, msg = engine.update_rule("hot_topic", cooldown_minutes=-1)
        assert success is False
        assert "冷却时间" in msg

    def test_update_rule_multiple_fields(self, engine):
        success, _ = engine.update_rule("hot_topic", enabled=False, priority=99)
        assert success is True
        rule = engine.get_rule("hot_topic")
        assert rule.enabled is False
        assert rule.priority == 99

    def test_update_rule_unknown_field_skipped(self, engine):
        success, _ = engine.update_rule("hot_topic", nonexistent_field="value")
        assert success is True


class TestAlertRuleEngineCallbacks:
    """测试回调注册和触发"""

    def test_register_and_trigger_callback(self, engine):
        received = []
        engine.register_callback(lambda alert: received.append(alert))
        rule = engine.get_rule("negative_surge")
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        engine._fire_alert(rule, "测试标题", "测试消息")
        assert len(received) == 1
        assert received[0].title == "测试标题"

    def test_callback_exception_does_not_propagate(self, engine):
        def bad_callback(alert):
            raise ValueError("callback error")

        engine.register_callback(bad_callback)
        rule = engine.get_rule("negative_surge")
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        alert = engine._fire_alert(rule, "标题", "消息")
        assert alert is not None  # 预警仍然触发


class TestAlertRuleEngineFireAlert:
    """测试 _fire_alert 的抑制和冷却路径"""

    def test_check_cooldown_no_last_triggered(self, engine):
        rule = engine.get_rule("negative_surge")
        rule.last_triggered = None
        assert engine.check_cooldown(rule) is True

    def test_check_cooldown_active(self, engine):
        rule = engine.get_rule("negative_surge")
        rule.last_triggered = datetime.now()
        rule.cooldown_minutes = 30
        assert engine.check_cooldown(rule) is False

    def test_check_cooldown_expired(self, engine):
        rule = engine.get_rule("negative_surge")
        rule.last_triggered = datetime.now() - timedelta(minutes=31)
        rule.cooldown_minutes = 30
        assert engine.check_cooldown(rule) is True

    def test_fire_alert_suppressed(self, engine):
        rule = engine.get_rule("negative_surge")
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 2
        engine._fire_alert(rule, "t1", "m1")
        engine._fire_alert(rule, "t2", "m2")
        # 第三次应被抑制
        assert engine._fire_alert(rule, "t3", "m3") is None

    def test_fire_alert_in_cooldown(self, engine):
        rule = engine.get_rule("negative_surge")
        rule.cooldown_minutes = 30
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        alert1 = engine._fire_alert(rule, "t1", "m1")
        assert alert1 is not None
        # 第二次在冷却中
        assert engine._fire_alert(rule, "t2", "m2") is None

    def test_fire_alert_success(self, engine):
        rule = engine.get_rule("negative_surge")
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        rule.trigger_count = 0
        alert = engine._fire_alert(rule, "测试", "消息", data={"k": "v"})
        assert alert is not None
        assert alert.title == "测试"
        assert alert.data == {"k": "v"}
        assert rule.trigger_count == 1
        assert rule.last_triggered is not None


class TestAlertRuleEngineEvaluateBranches:
    """测试 _evaluate_rule 各分支和阈值未满足路径"""

    def test_evaluate_rule_unknown_type_returns_none(self, engine):
        rule = AlertRule(id="custom", name="自定义", alert_type=AlertType.CUSTOM, level=AlertLevel.INFO)
        assert engine._evaluate_rule(rule, {}) is None

    def test_evaluate_threshold_breach_triggered(self, engine):
        rule = AlertRule(
            id="tb_test", name="阈值突破", alert_type=AlertType.THRESHOLD_BREACH,
            level=AlertLevel.WARNING, cooldown_minutes=0, max_alerts_per_hour=100,
            thresholds=[
                ThresholdConfig(field="count", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=10),
            ],
        )
        alert = engine._evaluate_rule(rule, {"count": 20})
        assert alert is not None
        assert alert.alert_type == AlertType.THRESHOLD_BREACH

    def test_evaluate_threshold_breach_not_triggered(self, engine):
        rule = AlertRule(
            id="tb_test", name="阈值突破", alert_type=AlertType.THRESHOLD_BREACH,
            level=AlertLevel.WARNING,
            thresholds=[
                ThresholdConfig(field="count", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=10),
            ],
        )
        assert engine._evaluate_rule(rule, {"count": 5}) is None

    def test_evaluate_threshold_breach_no_thresholds(self, engine):
        rule = AlertRule(
            id="tb_empty", name="空阈值", alert_type=AlertType.THRESHOLD_BREACH,
            level=AlertLevel.WARNING, thresholds=[],
        )
        assert engine._evaluate_rule(rule, {"count": 20}) is None

    def test_negative_surge_ratio_below_threshold(self, engine):
        rule = engine.get_rule("negative_surge")
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        # negative_count=60 满足阈值50，但 total=1000 使占比=0.06 < 0.3
        result = engine._evaluate_negative_surge(
            rule, {"negative_count": 60, "total_count": 1000, "time_window_minutes": 30}
        )
        assert result is None

    def test_negative_surge_no_thresholds(self, engine):
        rule = AlertRule(
            id="neg_no_thr", name="无阈值负面激增",
            alert_type=AlertType.NEGATIVE_SURGE, level=AlertLevel.WARNING,
            thresholds=[], conditions={"negative_ratio_threshold": 0.3},
            cooldown_minutes=0, max_alerts_per_hour=100,
        )
        alert = engine._evaluate_negative_surge(
            rule, {"negative_count": 60, "total_count": 100, "time_window_minutes": 30}
        )
        assert alert is not None

    def test_volume_spike_no_thresholds_below_default(self, engine):
        rule = AlertRule(
            id="vol_no_thr", name="无阈值讨论量",
            alert_type=AlertType.VOLUME_SPIKE, level=AlertLevel.WARNING, thresholds=[],
        )
        result = engine._evaluate_volume_spike(
            rule, {"current_count": 20, "baseline_count": 10, "time_window_minutes": 60}
        )
        assert result is None  # multiplier=2.0 < 3.0

    def test_volume_spike_no_thresholds_above_default(self, engine):
        rule = AlertRule(
            id="vol_no_thr", name="无阈值讨论量",
            alert_type=AlertType.VOLUME_SPIKE, level=AlertLevel.WARNING,
            thresholds=[], cooldown_minutes=0, max_alerts_per_hour=100,
        )
        alert = engine._evaluate_volume_spike(
            rule, {"current_count": 60, "baseline_count": 10, "time_window_minutes": 60}
        )
        assert alert is not None

    def test_volume_spike_min_baseline_adjustment(self, engine):
        rule = AlertRule(
            id="vol_baseline", name="基线调整",
            alert_type=AlertType.VOLUME_SPIKE, level=AlertLevel.WARNING,
            thresholds=[], conditions={"min_baseline": 10},
            cooldown_minutes=0, max_alerts_per_hour=100,
        )
        # baseline_count=5 < min_baseline=10 → baseline 调整为 10, multiplier=30/10=3.0
        result = engine._evaluate_volume_spike(
            rule, {"current_count": 30, "baseline_count": 5, "time_window_minutes": 60}
        )
        assert result is not None

    def test_sentiment_shift_no_thresholds_below_default(self, engine):
        rule = AlertRule(
            id="ss_no_thr", name="无阈值情感突变",
            alert_type=AlertType.SENTIMENT_SHIFT, level=AlertLevel.WARNING, thresholds=[],
        )
        result = engine._evaluate_sentiment_shift(
            rule, {"current_sentiment": 0.5, "previous_sentiment": 0.6, "time_window_minutes": 30}
        )
        assert result is None  # change=0.1 < 0.3

    def test_sentiment_shift_no_thresholds_above_default(self, engine):
        rule = AlertRule(
            id="ss_no_thr2", name="无阈值情感突变",
            alert_type=AlertType.SENTIMENT_SHIFT, level=AlertLevel.WARNING,
            thresholds=[], cooldown_minutes=0, max_alerts_per_hour=100,
        )
        alert = engine._evaluate_sentiment_shift(
            rule, {"current_sentiment": 0.2, "previous_sentiment": 0.6, "time_window_minutes": 30}
        )
        assert alert is not None  # change=0.4 >= 0.3

    def test_hot_topic_no_thresholds_below_default(self, engine):
        rule = AlertRule(
            id="ht_no_thr", name="无阈值热点",
            alert_type=AlertType.HOT_TOPIC, level=AlertLevel.INFO, thresholds=[],
        )
        result = engine._evaluate_hot_topic(
            rule, {"topic_mentions": 50, "topic_name": "测试", "time_window_minutes": 60}
        )
        assert result is None

    def test_hot_topic_no_thresholds_above_default(self, engine):
        rule = AlertRule(
            id="ht_no_thr2", name="无阈值热点",
            alert_type=AlertType.HOT_TOPIC, level=AlertLevel.INFO,
            thresholds=[], cooldown_minutes=0, max_alerts_per_hour=100,
        )
        alert = engine._evaluate_hot_topic(
            rule, {"topic_mentions": 150, "topic_name": "测试", "time_window_minutes": 60}
        )
        assert alert is not None


class TestAlertRuleEngineKeywordMatch:
    """测试 evaluate_keyword_match（keyword_match 规则从 DB 加载）"""

    def test_keyword_match_rule_disabled(self, engine):
        engine.update_rule("keyword_match", enabled=False)
        assert engine.evaluate_keyword_match("敏感内容", ["敏感"]) is None

    def test_keyword_match_no_keywords(self, engine):
        assert engine.evaluate_keyword_match("测试文本", []) is None

    def test_keyword_match_found(self, engine):
        rule = engine.get_rule("keyword_match")
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        alert = engine.evaluate_keyword_match("这是一条敏感内容", ["敏感", "危险"])
        assert alert is not None
        assert "敏感" in alert.message

    def test_keyword_match_not_found(self, engine):
        rule = engine.get_rule("keyword_match")
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        assert engine.evaluate_keyword_match("这是一条普通内容", ["敏感", "危险"]) is None

    def test_keyword_match_case_insensitive(self, engine):
        rule = engine.get_rule("keyword_match")
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        alert = engine.evaluate_keyword_match("This is URGENT content", ["urgent"])
        assert alert is not None


class TestAlertRuleEngineHistory:
    """测试预警历史管理（DB alerts 表）"""

    def _fire_some_alerts(self, engine, count):
        """触发若干预警，返回已触发的 Alert 对象列表"""
        rule = engine.get_rule("negative_surge")
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        alerts = []
        for i in range(count):
            a = engine._fire_alert(rule, f"标题{i}", f"消息{i}")
            if a is not None:
                alerts.append(a)
        return alerts

    def test_history_persisted_no_cap(self, engine):
        # P0 #5：DB 无 max_history 上限，全部持久化
        alerts = self._fire_some_alerts(engine, 5)
        assert len(alerts) == 5
        assert len(engine.get_alert_history(limit=100)) == 5

    def test_get_alert_history_with_limit(self, engine):
        self._fire_some_alerts(engine, 5)
        assert len(engine.get_alert_history(limit=2)) == 2

    def test_get_alert_history_filter_by_level(self, engine):
        self._fire_some_alerts(engine, 3)
        history = engine.get_alert_history(level="danger")
        assert len(history) == 3
        assert all(h["level"] == "danger" for h in history)

    def test_get_alert_history_unread_only(self, engine):
        alerts = self._fire_some_alerts(engine, 3)
        engine.mark_alert_read(alerts[0].id)
        unread = engine.get_alert_history(unread_only=True)
        assert all(not h.get("is_read") for h in unread)
        assert len(unread) == 2


class TestAlertRuleEngineReadStatus:
    """测试已读状态管理（DB）"""

    def _fire_alert(self, engine):
        rule = engine.get_rule("negative_surge")
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        return engine._fire_alert(rule, "标题", "消息")

    def test_mark_alert_read_existing(self, engine):
        alert = self._fire_alert(engine)
        assert engine.mark_alert_read(alert.id) is True
        fetched = [h for h in engine.get_alert_history(limit=100) if h["id"] == alert.id]
        assert fetched[0]["is_read"] is True

    def test_mark_alert_read_nonexistent(self, engine):
        assert engine.mark_alert_read("nonexistent-id") is False

    def test_mark_all_read(self, engine):
        self._fire_alert(engine)
        self._fire_alert(engine)
        self._fire_alert(engine)
        count = engine.mark_all_read()
        assert count == 3
        assert engine.get_unread_count() == 0

    def test_get_unread_count(self, engine):
        self._fire_alert(engine)
        self._fire_alert(engine)
        assert engine.get_unread_count() == 2
        engine.mark_all_read()
        assert engine.get_unread_count() == 0

    def test_mark_alert_read_skips_non_matching(self, engine):
        self._fire_alert(engine)
        alert2 = self._fire_alert(engine)
        assert engine.mark_alert_read(alert2.id) is True

    def test_mark_all_read_with_mixed_status(self, engine):
        alert1 = self._fire_alert(engine)
        self._fire_alert(engine)
        engine.mark_alert_read(alert1.id)
        count = engine.mark_all_read()
        assert count == 1


class TestAlertRuleEngineStats:
    """测试 get_stats 统计（DB 聚合查询）"""

    def test_get_stats_with_alerts(self, engine):
        rule = engine.get_rule("negative_surge")
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        engine._fire_alert(rule, "标题1", "消息1")
        engine._fire_alert(rule, "标题2", "消息2")
        stats = engine.get_stats()
        assert stats["total_alerts"] == 2
        assert stats["unread_count"] == 2
        assert "danger" in stats["level_distribution"]
        assert "negative_surge" in stats["type_distribution"]
        assert stats["active_rules"] >= 1

    def test_get_stats_empty(self, engine):
        stats = engine.get_stats()
        assert stats["total_alerts"] == 0
        assert stats["unread_count"] == 0
        assert stats["level_distribution"] == {}
        assert stats["type_distribution"] == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
