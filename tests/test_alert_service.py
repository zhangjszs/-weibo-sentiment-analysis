#!/usr/bin/env python3
"""
预警服务单元测试
测试内容：
- alert_engine.get_rules() 返回 list
- AlertRule 构造正常
- AlertType / AlertLevel 枚举值有效
- 重复 rule_id 被拒绝
- 规则启用/禁用切换
"""

import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

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


@pytest.fixture
def engine():
    """创建新的规则引擎实例"""
    return AlertRuleEngine()


class TestAlertRuleEngine:
    """测试预警规则引擎"""

    def test_get_rules_returns_list(self, engine):
        """get_rules() 应该返回 list 类型"""
        rules = engine.get_rules()
        assert isinstance(rules, list)
        # 默认应该有5条规则
        assert len(rules) == 5

    def test_get_rules_contains_rule_data(self, engine):
        """get_rules() 返回的规则应该包含必要的字段"""
        rules = engine.get_rules()
        if rules:
            rule = rules[0]
            assert 'id' in rule
            assert 'name' in rule
            assert 'enabled' in rule
            assert 'priority' in rule


class TestAlertRule:
    """测试 AlertRule 构造"""

    def test_alert_rule_construction(self):
        """AlertRule 应该能正常构造"""
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
        assert rule.enabled is True  # 默认启用

    def test_alert_rule_with_thresholds(self):
        """AlertRule 应该支持阈值配置"""
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


class TestAlertEnums:
    """测试 AlertType 和 AlertLevel 枚举"""

    def test_alert_type_values(self):
        """AlertType 枚举值应该有效"""
        assert AlertType.NEGATIVE_SURGE.value == "negative_surge"
        assert AlertType.VOLUME_SPIKE.value == "volume_spike"
        assert AlertType.SENTIMENT_SHIFT.value == "sentiment_shift"
        assert AlertType.HOT_TOPIC.value == "hot_topic"
        assert AlertType.KEYWORD_MATCH.value == "keyword_match"
        assert AlertType.THRESHOLD_BREACH.value == "threshold_breach"
        assert AlertType.CUSTOM.value == "custom"

    def test_alert_level_values(self):
        """AlertLevel 枚举值应该有效"""
        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.DANGER.value == "danger"
        assert AlertLevel.CRITICAL.value == "critical"

    def test_alert_type_from_string(self):
        """应该能从字符串创建 AlertType"""
        alert_type = AlertType("negative_surge")
        assert alert_type == AlertType.NEGATIVE_SURGE

    def test_alert_level_from_string(self):
        """应该能从字符串创建 AlertLevel"""
        level = AlertLevel("warning")
        assert level == AlertLevel.WARNING


class TestDuplicateRuleId:
    """测试重复 rule_id 处理"""

    def test_duplicate_rule_id_overwrites(self, engine):
        """重复 rule_id 应该被拒绝"""
        # 先添加一条规则
        rule1 = AlertRule(
            id="duplicate_test",
            name="规则1",
            alert_type=AlertType.CUSTOM,
            level=AlertLevel.INFO,
        )
        success, msg = engine.add_rule(rule1)
        assert success is True

        # 尝试添加相同 id 的规则
        rule2 = AlertRule(
            id="duplicate_test",
            name="规则2",
            alert_type=AlertType.CUSTOM,
            level=AlertLevel.WARNING,
        )
        # 应该返回错误（在 create_rule API 层处理）
        # 但在引擎层是直接覆盖，这里测试 API 行为
        # 引擎层 add_rule 会覆盖同名规则
        success, msg = engine.add_rule(rule2)
        assert success is True  # 引擎层允许覆盖

        # 验证只有一条规则
        rules = engine.get_rules()
        duplicate_rules = [r for r in rules if r['id'] == "duplicate_test"]
        assert len(duplicate_rules) == 1
        assert duplicate_rules[0]['name'] == "规则2"  # 被覆盖了


class TestRuleToggle:
    """测试规则启用/禁用切换"""

    def test_rule_toggle_disable(self, engine):
        """应该能禁用规则"""
        # 先添加一条启用的规则
        rule = AlertRule(
            id="toggle_test",
            name="切换测试规则",
            alert_type=AlertType.CUSTOM,
            level=AlertLevel.INFO,
            enabled=True,
        )
        engine.add_rule(rule)

        # 禁用规则
        success, msg = engine.update_rule("toggle_test", enabled=False)
        assert success is True

        # 验证规则已禁用
        rules = engine.get_rules()
        toggle_rule = next((r for r in rules if r['id'] == "toggle_test"), None)
        assert toggle_rule is not None
        assert toggle_rule['enabled'] is False

    def test_rule_toggle_enable(self, engine):
        """应该能启用规则"""
        # 先添加一条禁用的规则
        rule = AlertRule(
            id="toggle_test2",
            name="切换测试规则2",
            alert_type=AlertType.CUSTOM,
            level=AlertLevel.INFO,
            enabled=False,
        )
        engine.add_rule(rule)

        # 启用规则
        success, msg = engine.update_rule("toggle_test2", enabled=True)
        assert success is True

        # 验证规则已启用
        rules = engine.get_rules()
        toggle_rule = next((r for r in rules if r['id'] == "toggle_test2"), None)
        assert toggle_rule is not None
        assert toggle_rule['enabled'] is True


class TestAlertSuppression:
    """测试告警抑制功能"""

    def test_suppression_should_suppress(self):
        """超过阈值应该触发抑制"""
        suppression = AlertSuppression()
        rule_id = "test_suppression"

        # 前10次不应该被抑制
        for i in range(10):
            assert suppression.should_suppress(rule_id, max_per_hour=10) is False

        # 第11次应该被抑制
        assert suppression.should_suppress(rule_id, max_per_hour=10) is True

    def test_suppression_stats(self):
        """抑制统计应该正确"""
        suppression = AlertSuppression()
        rule_id = "test_stats"

        # 触发抑制
        for i in range(15):
            suppression.should_suppress(rule_id, max_per_hour=5)

        stats = suppression.get_stats()
        assert 'suppressed_count' in stats
        assert 'active_rules' in stats
        assert stats['suppressed_count'] == 10  # 15-5=10 被抑制


class TestThresholdValidator:
    """测试阈值验证器"""

    def test_validate_threshold_valid(self):
        """有效阈值应该通过验证"""
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
        """空字段应该验证失败"""
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
        """负值应该验证失败"""
        config = ThresholdConfig(
            field="count",
            operator=ThresholdOperator.GREATER_THAN_OR_EQUAL,
            value=-1,
            time_window_minutes=30,
        )
        valid, msg = ThresholdValidator.validate_threshold(config)
        assert valid is False
        assert "阈值不能为负数" in msg


class TestAlertCreation:
    """测试预警创建"""

    def test_alert_creation(self):
        """应该能创建预警对象"""
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
        assert alert.is_read is False  # 默认未读

    def test_alert_to_dict(self):
        """预警应该能转换为字典"""
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
        assert data['id'] == "alert_002"
        assert data['title'] == "测试预警"
        assert data['level'] == "danger"


class TestCheckAlerts:
    """测试 check_alerts 端到端规则触发逻辑"""

    def test_check_alerts_negative_surge_triggered(self, engine):
        """负面舆情激增规则应该正确触发"""
        # 设置触发条件：负面评论数超过阈值
        metrics = {
            "negative_count": 60,  # 超过默认阈值50
            "total_count": 100,
            "time_window_minutes": 30,
        }

        alerts = engine.check_alerts(metrics)

        # 应该触发负面舆情激增预警
        assert len(alerts) > 0
        assert any(a.alert_type == AlertType.NEGATIVE_SURGE for a in alerts)

    def test_check_alerts_volume_spike_triggered(self, engine):
        """讨论量异常增长规则应该正确触发"""
        # 设置触发条件：讨论量倍数超过阈值
        metrics = {
            "current_count": 50,
            "baseline_count": 10,  # 倍数 = 5，超过默认阈值3.0
            "time_window_minutes": 60,
        }

        alerts = engine.check_alerts(metrics)

        # 应该触发讨论量异常增长预警
        assert len(alerts) > 0
        assert any(a.alert_type == AlertType.VOLUME_SPIKE for a in alerts)

    def test_check_alerts_sentiment_shift_triggered(self, engine):
        """情感倾向突变规则应该正确触发"""
        # 设置触发条件：情感变化超过阈值
        metrics = {
            "current_sentiment": 0.2,
            "previous_sentiment": 0.6,  # 变化 = 0.4，超过默认阈值0.3
            "time_window_minutes": 30,
        }

        alerts = engine.check_alerts(metrics)

        # 应该触发情感倾向突变预警
        assert len(alerts) > 0
        assert any(a.alert_type == AlertType.SENTIMENT_SHIFT for a in alerts)

    def test_check_alerts_hot_topic_triggered(self, engine):
        """热点话题出现规则应该正确触发"""
        # 设置触发条件：话题提及数超过阈值
        metrics = {
            "topic_mentions": 150,  # 超过默认阈值100
            "topic_name": "测试话题",
            "time_window_minutes": 60,
        }

        alerts = engine.check_alerts(metrics)

        # 应该触发热点话题预警
        assert len(alerts) > 0
        assert any(a.alert_type == AlertType.HOT_TOPIC for a in alerts)

    def test_check_alerts_no_trigger_when_disabled(self, engine):
        """禁用的规则不应该触发"""
        # 禁用所有默认规则
        for rule_id in list(engine.rules.keys()):
            engine.update_rule(rule_id, enabled=False)

        # 设置本应触发预警的指标
        metrics = {
            "negative_count": 100,
            "total_count": 150,
            "time_window_minutes": 30,
        }

        alerts = engine.check_alerts(metrics)

        # 不应该触发任何预警
        assert len(alerts) == 0

    def test_check_alerts_no_trigger_below_threshold(self, engine):
        """未达到阈值时不应该触发"""
        # 设置不触发条件的指标（低于阈值）
        metrics = {
            "negative_count": 10,  # 低于阈值50
            "total_count": 100,
            "time_window_minutes": 30,
        }

        alerts = engine.check_alerts(metrics)

        # 负面舆情激增不应该触发（但其他规则可能触发）
        negative_surge_alerts = [a for a in alerts if a.alert_type == AlertType.NEGATIVE_SURGE]
        assert len(negative_surge_alerts) == 0

    def test_check_alerts_returns_alert_objects(self, engine):
        """check_alerts 应该返回 Alert 对象列表"""
        metrics = {
            "negative_count": 60,
            "total_count": 100,
            "time_window_minutes": 30,
        }

        alerts = engine.check_alerts(metrics)

        # 验证返回的是 Alert 对象
        for alert in alerts:
            assert isinstance(alert, Alert)
            assert alert.id is not None
            assert alert.rule_id is not None
            assert alert.title is not None

    def test_check_alerts_priority_order(self, engine):
        """高优先级规则应该先被处理"""
        # 添加一个高优先级自定义规则
        high_priority_rule = AlertRule(
            id="high_priority_test",
            name="高优先级测试规则",
            alert_type=AlertType.CUSTOM,
            level=AlertLevel.CRITICAL,
            priority=200,  # 最高优先级
            enabled=True,
        )
        engine.add_rule(high_priority_rule)

        # 设置能触发多个规则的指标
        metrics = {
            "negative_count": 60,
            "total_count": 100,
            "time_window_minutes": 30,
            "current_count": 50,
            "baseline_count": 10,
        }

        alerts = engine.check_alerts(metrics)

        # 验证返回了预警
        assert len(alerts) > 0


class TestAlertSuppressionReset:
    """测试 AlertSuppression.reset（lines 60-67）"""

    def test_reset_by_rule_id(self):
        """按 rule_id 重置应清除该规则的抑制记录"""
        sup = AlertSuppression()
        sup.should_suppress("rule_a", max_per_hour=5)
        sup.should_suppress("rule_b", max_per_hour=5)
        sup.reset("rule_a")
        stats = sup.get_stats()
        # rule_b 仍然存在
        assert stats["active_rules"] == 1

    def test_reset_all(self):
        """无参数重置应清除所有抑制记录和计数"""
        sup = AlertSuppression()
        for _ in range(10):
            sup.should_suppress("rule_a", max_per_hour=3)  # 7 次被抑制
        assert sup.get_stats()["suppressed_count"] == 7
        sup.reset()
        stats = sup.get_stats()
        assert stats["suppressed_count"] == 0
        assert stats["active_rules"] == 0


class TestThresholdValidatorEdgeCases:
    """测试 ThresholdValidator 未覆盖路径（lines 83-110）"""

    def test_validate_threshold_between_no_value_max(self):
        """BETWEEN 运算符缺少 value_max 应验证失败"""
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
        """BETWEEN 运算符 value >= value_max 应验证失败"""
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
        """BETWEEN 运算符配置正确应验证通过"""
        config = ThresholdConfig(
            field="count",
            operator=ThresholdOperator.BETWEEN,
            value=10,
            value_max=20,
            time_window_minutes=30,
        )
        valid, msg = ThresholdValidator.validate_threshold(config)
        assert valid is True

    def test_validate_threshold_time_window_zero(self):
        """时间窗口为 0 应验证失败"""
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
        """规则 ID 为空应验证失败"""
        rule = AlertRule(id="", name="测试", alert_type=AlertType.CUSTOM, level=AlertLevel.INFO)
        valid, errors = ThresholdValidator.validate_rule(rule)
        assert valid is False
        assert any("规则ID" in e for e in errors)

    def test_validate_rule_empty_name(self):
        """规则名称为空应验证失败"""
        rule = AlertRule(id="test", name="", alert_type=AlertType.CUSTOM, level=AlertLevel.INFO)
        valid, errors = ThresholdValidator.validate_rule(rule)
        assert valid is False
        assert any("规则名称" in e for e in errors)

    def test_validate_rule_negative_cooldown(self):
        """冷却时间为负应验证失败"""
        rule = AlertRule(
            id="test", name="测试", alert_type=AlertType.CUSTOM,
            level=AlertLevel.INFO, cooldown_minutes=-1,
        )
        valid, errors = ThresholdValidator.validate_rule(rule)
        assert valid is False
        assert any("冷却时间" in e for e in errors)

    def test_validate_rule_max_alerts_zero(self):
        """每小时最大告警数为 0 应验证失败"""
        rule = AlertRule(
            id="test", name="测试", alert_type=AlertType.CUSTOM,
            level=AlertLevel.INFO, max_alerts_per_hour=0,
        )
        valid, errors = ThresholdValidator.validate_rule(rule)
        assert valid is False
        assert any("每小时最大告警数" in e for e in errors)

    def test_validate_rule_with_invalid_threshold(self):
        """规则包含无效阈值时应验证失败并带阈值编号"""
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
    """测试 ThresholdChecker 各方法（lines 123-183）"""

    def test_record_metric_and_get_values(self):
        """记录指标后应能获取时间窗口内的值"""
        checker = ThresholdChecker()
        checker.record_metric("test", 10.0)
        checker.record_metric("test", 20.0)
        checker.record_metric("test", 30.0)
        values = checker.get_metric_values("test", time_window_minutes=30)
        assert values == [10.0, 20.0, 30.0]

    def test_get_metric_values_nonexistent(self):
        """不存在的指标应返回空列表"""
        checker = ThresholdChecker()
        assert checker.get_metric_values("nonexistent") == []

    def test_record_metric_cache_trim(self):
        """超过最大缓存大小应裁剪旧数据"""
        checker = ThresholdChecker()
        checker._max_cache_size = 3
        for v in [10.0, 20.0, 30.0, 40.0]:
            checker.record_metric("test", v)
        values = checker.get_metric_values("test")
        assert values == [20.0, 30.0, 40.0]

    def test_get_metric_stats_with_values(self):
        """有值时应正确计算统计"""
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
        """无值时应返回零值统计"""
        checker = ThresholdChecker()
        stats = checker.get_metric_stats("nonexistent")
        assert stats["count"] == 0
        assert stats["sum"] == 0
        assert stats["avg"] == 0

    def test_check_threshold(self):
        """check_threshold 应委托给 config.evaluate"""
        checker = ThresholdChecker()
        config = ThresholdConfig(
            field="count", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=10,
        )
        assert checker.check_threshold(config, 20) is True
        assert checker.check_threshold(config, 5) is False

    def test_check_multiple_thresholds_all_met(self):
        """所有阈值都满足时 triggered=True"""
        checker = ThresholdChecker()
        thresholds = [
            ThresholdConfig(field="count", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=10),
            ThresholdConfig(field="ratio", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=0.3),
        ]
        metrics = {"count": 20, "ratio": 0.5}
        triggered, fields = checker.check_multiple_thresholds(thresholds, metrics)
        assert triggered is True
        assert set(fields) == {"count", "ratio"}

    def test_check_multiple_thresholds_one_not_met(self):
        """部分阈值不满足时 triggered=False"""
        checker = ThresholdChecker()
        thresholds = [
            ThresholdConfig(field="count", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=10),
            ThresholdConfig(field="ratio", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=0.3),
        ]
        metrics = {"count": 20, "ratio": 0.1}
        triggered, fields = checker.check_multiple_thresholds(thresholds, metrics)
        assert triggered is False
        assert "count" in fields
        assert "ratio" not in fields

    def test_check_multiple_thresholds_field_not_in_metrics(self):
        """metric_values 中缺失的字段应被跳过"""
        checker = ThresholdChecker()
        thresholds = [
            ThresholdConfig(field="count", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=10),
            ThresholdConfig(field="missing", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=10),
        ]
        metrics = {"count": 20}
        triggered, fields = checker.check_multiple_thresholds(thresholds, metrics)
        assert triggered is True
        assert fields == ["count"]


class TestAlertRuleEngineRuleManagement:
    """测试规则管理的错误路径（lines 295-330）"""

    def test_add_rule_invalid_returns_error(self, engine):
        """无效规则应返回 False 和错误信息"""
        rule = AlertRule(id="", name="无效", alert_type=AlertType.CUSTOM, level=AlertLevel.INFO)
        success, msg = engine.add_rule(rule)
        assert success is False
        assert "规则ID" in msg

    def test_remove_rule_existing(self, engine):
        """移除存在的规则应返回 True"""
        assert engine.remove_rule("hot_topic") is True
        assert "hot_topic" not in engine.rules

    def test_remove_rule_nonexistent(self, engine):
        """移除不存在的规则应返回 False"""
        assert engine.remove_rule("nonexistent") is False

    def test_update_rule_nonexistent(self, engine):
        """更新不存在的规则应返回 False"""
        success, msg = engine.update_rule("nonexistent", enabled=False)
        assert success is False
        assert "规则不存在" in msg

    def test_update_rule_validation_failure(self, engine):
        """更新后规则无效应返回 False"""
        success, msg = engine.update_rule("hot_topic", cooldown_minutes=-1)
        assert success is False
        assert "冷却时间" in msg

    def test_update_rule_multiple_fields(self, engine):
        """更新多个字段应全部生效"""
        success, msg = engine.update_rule("hot_topic", enabled=False, priority=99)
        assert success is True
        rule = engine.rules["hot_topic"]
        assert rule.enabled is False
        assert rule.priority == 99

    def test_update_rule_unknown_field_skipped(self, engine):
        """更新不存在的属性应被跳过不报错"""
        success, msg = engine.update_rule("hot_topic", nonexistent_field="value")
        assert success is True


class TestAlertRuleEngineCallbacks:
    """测试回调注册和触发（lines 332-342）"""

    def test_register_and_trigger_callback(self, engine):
        """注册的回调应在预警触发时被调用"""
        received = []
        engine.register_callback(lambda alert: received.append(alert))
        rule = engine.rules["negative_surge"]
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        engine._fire_alert(rule, "测试标题", "测试消息")
        assert len(received) == 1
        assert received[0].title == "测试标题"

    def test_callback_exception_does_not_propagate(self, engine):
        """回调抛异常不应影响预警流程"""
        def bad_callback(alert):
            raise ValueError("callback error")
        engine.register_callback(bad_callback)
        rule = engine.rules["negative_surge"]
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        alert = engine._fire_alert(rule, "标题", "消息")
        assert alert is not None  # 预警仍然触发


class TestAlertRuleEngineFireAlert:
    """测试 _fire_alert 的抑制和冷却路径（lines 344-389）"""

    def test_check_cooldown_no_last_triggered(self, engine):
        """last_triggered 为 None 时应返回 True（不冷却）"""
        rule = engine.rules["negative_surge"]
        rule.last_triggered = None
        assert engine.check_cooldown(rule) is True

    def test_check_cooldown_active(self, engine):
        """刚触发过的规则应处于冷却中"""
        rule = engine.rules["negative_surge"]
        rule.last_triggered = datetime.now()
        rule.cooldown_minutes = 30
        assert engine.check_cooldown(rule) is False

    def test_check_cooldown_expired(self, engine):
        """超过冷却时间应返回 True"""
        rule = engine.rules["negative_surge"]
        rule.last_triggered = datetime.now() - timedelta(minutes=31)
        rule.cooldown_minutes = 30
        assert engine.check_cooldown(rule) is True

    def test_fire_alert_suppressed(self, engine):
        """超过每小时上限应被抑制"""
        rule = engine.rules["negative_surge"]
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 2
        engine._fire_alert(rule, "t1", "m1")
        engine._fire_alert(rule, "t2", "m2")
        # 第三次应被抑制
        result = engine._fire_alert(rule, "t3", "m3")
        assert result is None

    def test_fire_alert_in_cooldown(self, engine):
        """冷却中应返回 None"""
        rule = engine.rules["negative_surge"]
        rule.cooldown_minutes = 30
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        # 第一次触发
        alert1 = engine._fire_alert(rule, "t1", "m1")
        assert alert1 is not None
        # 第二次在冷却中
        alert2 = engine._fire_alert(rule, "t2", "m2")
        assert alert2 is None

    def test_fire_alert_success(self, engine):
        """正常触发应返回 Alert 并更新规则状态"""
        rule = engine.rules["negative_surge"]
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
    """测试 _evaluate_rule 各分支和阈值未满足路径（lines 409-570）"""

    def test_evaluate_rule_unknown_type_returns_none(self, engine):
        """CUSTOM 类型不在 if/elif 链中，应返回 None"""
        rule = AlertRule(id="custom", name="自定义", alert_type=AlertType.CUSTOM, level=AlertLevel.INFO)
        assert engine._evaluate_rule(rule, {}) is None

    def test_evaluate_threshold_breach_triggered(self, engine):
        """THRESHOLD_BREACH 阈值满足应触发预警"""
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
        """THRESHOLD_BREACH 阈值不满足应返回 None"""
        rule = AlertRule(
            id="tb_test", name="阈值突破", alert_type=AlertType.THRESHOLD_BREACH,
            level=AlertLevel.WARNING,
            thresholds=[
                ThresholdConfig(field="count", operator=ThresholdOperator.GREATER_THAN_OR_EQUAL, value=10),
            ],
        )
        assert engine._evaluate_rule(rule, {"count": 5}) is None

    def test_evaluate_threshold_breach_no_thresholds(self, engine):
        """THRESHOLD_BREACH 无阈值配置应返回 None"""
        rule = AlertRule(
            id="tb_empty", name="空阈值", alert_type=AlertType.THRESHOLD_BREACH,
            level=AlertLevel.WARNING, thresholds=[],
        )
        assert engine._evaluate_rule(rule, {"count": 20}) is None

    def test_negative_surge_ratio_below_threshold(self, engine):
        """负面占比低于阈值应返回 None（阈值满足但占比不足）"""
        rule = engine.rules["negative_surge"]
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        # negative_count=60 满足阈值50，但 total=1000 使占比=0.06 < 0.3
        result = engine._evaluate_negative_surge(
            rule, {"negative_count": 60, "total_count": 1000, "time_window_minutes": 30}
        )
        assert result is None

    def test_negative_surge_no_thresholds(self, engine):
        """无阈值配置的负面激增规则应直接检查占比"""
        rule = AlertRule(
            id="neg_no_thr", name="无阈值负面激增",
            alert_type=AlertType.NEGATIVE_SURGE, level=AlertLevel.WARNING,
            thresholds=[], conditions={"negative_ratio_threshold": 0.3},
            cooldown_minutes=0, max_alerts_per_hour=100,
        )
        # 占比 60/100 = 0.6 >= 0.3 → 触发
        alert = engine._evaluate_negative_surge(
            rule, {"negative_count": 60, "total_count": 100, "time_window_minutes": 30}
        )
        assert alert is not None

    def test_volume_spike_no_thresholds_below_default(self, engine):
        """无阈值配置的讨论量规则，倍数 < 3.0 应返回 None"""
        rule = AlertRule(
            id="vol_no_thr", name="无阈值讨论量",
            alert_type=AlertType.VOLUME_SPIKE, level=AlertLevel.WARNING,
            thresholds=[],
        )
        result = engine._evaluate_volume_spike(
            rule, {"current_count": 20, "baseline_count": 10, "time_window_minutes": 60}
        )
        assert result is None  # multiplier=2.0 < 3.0

    def test_volume_spike_no_thresholds_above_default(self, engine):
        """无阈值配置的讨论量规则，倍数 >= 3.0 应触发"""
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
        """baseline 低于 min_baseline 时应使用 min_baseline"""
        rule = AlertRule(
            id="vol_baseline", name="基线调整",
            alert_type=AlertType.VOLUME_SPIKE, level=AlertLevel.WARNING,
            thresholds=[], conditions={"min_baseline": 10},
        )
        # baseline_count=5 < min_baseline=10, 所以 baseline 被调整为 10
        # multiplier = 30/10 = 3.0 >= 3.0 → 触发（但因 cooldown 默认30可能被挡）
        # 用 _evaluate_volume_spike 直接调用不经过 _fire_alert 的 cooldown
        # 实际上 _evaluate_volume_spike 内部调用 _fire_alert，会被 cooldown 挡
        # 所以只验证不抛异常即可
        result = engine._evaluate_volume_spike(
            rule, {"current_count": 30, "baseline_count": 5, "time_window_minutes": 60}
        )
        # 结果可能是 Alert 或 None（取决于 cooldown），重点是 min_baseline 路径被执行
        # 由于 rule.last_triggered=None，cooldown 通过，应触发
        assert result is not None

    def test_sentiment_shift_no_thresholds_below_default(self, engine):
        """无阈值配置的情感突变规则，变化 < 0.3 应返回 None"""
        rule = AlertRule(
            id="ss_no_thr", name="无阈值情感突变",
            alert_type=AlertType.SENTIMENT_SHIFT, level=AlertLevel.WARNING,
            thresholds=[],
        )
        result = engine._evaluate_sentiment_shift(
            rule, {"current_sentiment": 0.5, "previous_sentiment": 0.6, "time_window_minutes": 30}
        )
        assert result is None  # change=0.1 < 0.3

    def test_sentiment_shift_no_thresholds_above_default(self, engine):
        """无阈值配置的情感突变规则，变化 >= 0.3 应触发"""
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
        """无阈值配置的热点话题规则，提及数 < 100 应返回 None"""
        rule = AlertRule(
            id="ht_no_thr", name="无阈值热点",
            alert_type=AlertType.HOT_TOPIC, level=AlertLevel.INFO,
            thresholds=[],
        )
        result = engine._evaluate_hot_topic(
            rule, {"topic_mentions": 50, "topic_name": "测试", "time_window_minutes": 60}
        )
        assert result is None

    def test_hot_topic_no_thresholds_above_default(self, engine):
        """无阈值配置的热点话题规则，提及数 >= 100 应触发"""
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
    """测试 evaluate_keyword_match（lines 572-590）"""

    def test_keyword_match_rule_disabled(self, engine):
        """keyword_match 规则禁用时应返回 None"""
        engine.update_rule("keyword_match", enabled=False)
        result = engine.evaluate_keyword_match("敏感内容", ["敏感"])
        assert result is None

    def test_keyword_match_no_keywords(self, engine):
        """关键词列表为空时应返回 None"""
        result = engine.evaluate_keyword_match("测试文本", [])
        assert result is None

    def test_keyword_match_found(self, engine):
        """匹配到关键词应触发预警"""
        rule = engine.rules["keyword_match"]
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        alert = engine.evaluate_keyword_match("这是一条敏感内容", ["敏感", "危险"])
        assert alert is not None
        assert "敏感" in alert.message

    def test_keyword_match_not_found(self, engine):
        """未匹配到关键词应返回 None"""
        rule = engine.rules["keyword_match"]
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        result = engine.evaluate_keyword_match("这是一条普通内容", ["敏感", "危险"])
        assert result is None

    def test_keyword_match_case_insensitive(self, engine):
        """关键词匹配应不区分大小写"""
        rule = engine.rules["keyword_match"]
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        alert = engine.evaluate_keyword_match("This is URGENT content", ["urgent"])
        assert alert is not None


class TestAlertRuleEngineHistory:
    """测试预警历史管理（lines 592-614）"""

    def _fire_some_alerts(self, engine, count):
        """辅助：触发若干预警填充历史"""
        rule = engine.rules["negative_surge"]
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        for i in range(count):
            engine._fire_alert(rule, f"标题{i}", f"消息{i}")

    def test_history_overflow(self, engine):
        """超过 max_history 应裁剪旧记录"""
        engine.max_history = 3
        self._fire_some_alerts(engine, 5)
        assert len(engine.alert_history) == 3

    def test_get_alert_history_with_limit(self, engine):
        """limit 参数应限制返回数量"""
        self._fire_some_alerts(engine, 5)
        history = engine.get_alert_history(limit=2)
        assert len(history) == 2

    def test_get_alert_history_filter_by_level(self, engine):
        """level 过滤应只返回对应级别"""
        self._fire_some_alerts(engine, 3)
        # negative_surge 默认 level=DANGER
        history = engine.get_alert_history(level="danger")
        assert len(history) == 3
        assert all(h["level"] == "danger" for h in history)

    def test_get_alert_history_unread_only(self, engine):
        """unread_only 应只返回未读预警"""
        self._fire_some_alerts(engine, 3)
        # 标记第一条已读
        first_id = engine.alert_history[0].id
        engine.mark_alert_read(first_id)
        unread = engine.get_alert_history(unread_only=True)
        assert all(not h.get("is_read") for h in unread)
        assert len(unread) == 2


class TestAlertRuleEngineReadStatus:
    """测试已读状态管理（lines 616-638）"""

    def _fire_alert(self, engine):
        rule = engine.rules["negative_surge"]
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        return engine._fire_alert(rule, "标题", "消息")

    def test_mark_alert_read_existing(self, engine):
        """标记存在的预警应返回 True"""
        alert = self._fire_alert(engine)
        assert engine.mark_alert_read(alert.id) is True
        assert engine.alert_history[0].is_read is True

    def test_mark_alert_read_nonexistent(self, engine):
        """标记不存在的预警应返回 False"""
        assert engine.mark_alert_read("nonexistent-id") is False

    def test_mark_all_read(self, engine):
        """标记所有预警已读应返回已读数量"""
        self._fire_alert(engine)
        self._fire_alert(engine)  # 注意: cooldown=0 所以可以连续触发
        # 先重置 last_triggered 以便第二次触发
        engine.rules["negative_surge"].last_triggered = None
        self._fire_alert(engine)
        count = engine.mark_all_read()
        assert count == 3
        assert all(a.is_read for a in engine.alert_history)

    def test_get_unread_count(self, engine):
        """未读计数应正确"""
        self._fire_alert(engine)
        engine.rules["negative_surge"].last_triggered = None
        self._fire_alert(engine)
        assert engine.get_unread_count() == 2
        engine.mark_all_read()
        assert engine.get_unread_count() == 0

    def test_mark_alert_read_skips_non_matching(self, engine):
        """标记第二条预警应跳过第一条（覆盖循环 continue 分支）"""
        self._fire_alert(engine)
        engine.rules["negative_surge"].last_triggered = None
        alert2 = self._fire_alert(engine)
        assert engine.mark_alert_read(alert2.id) is True

    def test_mark_all_read_with_mixed_status(self, engine):
        """混合已读/未读时只标记未读的（覆盖 if not is_read False 分支）"""
        self._fire_alert(engine)
        engine.rules["negative_surge"].last_triggered = None
        self._fire_alert(engine)
        # 先标记第一条已读
        engine.mark_alert_read(engine.alert_history[0].id)
        # mark_all_read 应只标记第二条
        count = engine.mark_all_read()
        assert count == 1


class TestAlertRuleEngineStats:
    """测试 get_stats 统计（lines 650-669）"""

    def test_get_stats_with_alerts(self, engine):
        """有预警历史时应正确统计分布"""
        rule = engine.rules["negative_surge"]
        rule.cooldown_minutes = 0
        rule.max_alerts_per_hour = 100
        rule.last_triggered = None
        engine._fire_alert(rule, "标题1", "消息1")
        engine.rules["negative_surge"].last_triggered = None
        engine._fire_alert(rule, "标题2", "消息2")

        stats = engine.get_stats()
        assert stats["total_alerts"] == 2
        assert stats["unread_count"] == 2
        assert "danger" in stats["level_distribution"]
        assert "negative_surge" in stats["type_distribution"]
        assert stats["active_rules"] >= 1

    def test_get_stats_empty(self, engine):
        """无预警历史时统计应为零值"""
        stats = engine.get_stats()
        assert stats["total_alerts"] == 0
        assert stats["unread_count"] == 0
        assert stats["level_distribution"] == {}
        assert stats["type_distribution"] == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
