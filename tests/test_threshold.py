#!/usr/bin/env python3
"""
阈值触发机制单元测试
"""

import sys

import pytest

sys.path.insert(0, "src")


class TestThresholdConfig:
    """阈值配置测试"""

    def test_threshold_greater_than(self):
        """测试大于运算符"""
        from models.alert import ThresholdConfig, ThresholdOperator

        config = ThresholdConfig(
            field="negative_count", operator=ThresholdOperator.GREATER_THAN, value=50
        )

        assert config.evaluate(60) is True
        assert config.evaluate(50) is False
        assert config.evaluate(40) is False

    def test_threshold_greater_than_or_equal(self):
        """测试大于等于运算符"""
        from models.alert import ThresholdConfig, ThresholdOperator

        config = ThresholdConfig(
            field="negative_count",
            operator=ThresholdOperator.GREATER_THAN_OR_EQUAL,
            value=50,
        )

        assert config.evaluate(60) is True
        assert config.evaluate(50) is True
        assert config.evaluate(40) is False

    def test_threshold_less_than(self):
        """测试小于运算符"""
        from models.alert import ThresholdConfig, ThresholdOperator

        config = ThresholdConfig(
            field="sentiment_score", operator=ThresholdOperator.LESS_THAN, value=0.3
        )

        assert config.evaluate(0.2) is True
        assert config.evaluate(0.3) is False
        assert config.evaluate(0.4) is False

    def test_threshold_between(self):
        """测试区间运算符"""
        from models.alert import ThresholdConfig, ThresholdOperator

        config = ThresholdConfig(
            field="volume", operator=ThresholdOperator.BETWEEN, value=10, value_max=100
        )

        assert config.evaluate(50) is True
        assert config.evaluate(10) is True
        assert config.evaluate(100) is True
        assert config.evaluate(5) is False
        assert config.evaluate(150) is False

    def test_threshold_to_dict(self):
        """测试阈值序列化"""
        from models.alert import ThresholdConfig, ThresholdOperator

        config = ThresholdConfig(
            field="test_field",
            operator=ThresholdOperator.GREATER_THAN,
            value=100,
            time_window_minutes=30,
        )

        result = config.to_dict()

        assert result["field"] == "test_field"
        assert result["operator"] == "greater_than"
        assert result["value"] == 100
        assert result["time_window_minutes"] == 30


class TestThresholdValidator:
    """阈值验证器测试"""

    def test_validate_valid_threshold(self):
        """测试有效阈值验证"""
        from models.alert import ThresholdConfig, ThresholdOperator
        from services.alert_service import ThresholdValidator

        config = ThresholdConfig(
            field="negative_count",
            operator=ThresholdOperator.GREATER_THAN,
            value=50,
            time_window_minutes=30,
        )

        valid, msg = ThresholdValidator.validate_threshold(config)
        assert valid is True
        assert msg == "验证通过"

    def test_validate_empty_field(self):
        """测试空字段验证"""
        from models.alert import ThresholdConfig, ThresholdOperator
        from services.alert_service import ThresholdValidator

        config = ThresholdConfig(
            field="", operator=ThresholdOperator.GREATER_THAN, value=50
        )

        valid, msg = ThresholdValidator.validate_threshold(config)
        assert valid is False
        assert "不能为空" in msg

    def test_validate_negative_value(self):
        """测试负值验证"""
        from models.alert import ThresholdConfig, ThresholdOperator
        from services.alert_service import ThresholdValidator

        config = ThresholdConfig(
            field="test", operator=ThresholdOperator.GREATER_THAN, value=-10
        )

        valid, msg = ThresholdValidator.validate_threshold(config)
        assert valid is False
        assert "不能为负数" in msg

    def test_validate_between_missing_max(self):
        """测试BETWEEN缺少最大值"""
        from models.alert import ThresholdConfig, ThresholdOperator
        from services.alert_service import ThresholdValidator

        config = ThresholdConfig(
            field="test", operator=ThresholdOperator.BETWEEN, value=10
        )

        valid, msg = ThresholdValidator.validate_threshold(config)
        assert valid is False
        assert "value_max" in msg

    def test_validate_rule(self):
        """测试规则验证"""
        from models.alert import (
            AlertLevel,
            AlertRule,
            AlertType,
            ThresholdConfig,
            ThresholdOperator,
        )
        from services.alert_service import ThresholdValidator

        rule = AlertRule(
            id="test_rule",
            name="测试规则",
            alert_type=AlertType.NEGATIVE_SURGE,
            level=AlertLevel.WARNING,
            thresholds=[
                ThresholdConfig(
                    field="negative_count",
                    operator=ThresholdOperator.GREATER_THAN,
                    value=50,
                )
            ],
        )

        valid, errors = ThresholdValidator.validate_rule(rule)
        assert valid is True
        assert len(errors) == 0


class TestAlertSuppression:
    """告警抑制测试"""

    def test_suppression_below_limit(self):
        """测试未超过限制"""
        from services.alert_service import AlertSuppression

        suppression = AlertSuppression()

        for i in range(5):
            result = suppression.should_suppress("rule_1", max_per_hour=10)
            assert result is False

    def test_suppression_exceeds_limit(self):
        """测试超过限制"""
        from services.alert_service import AlertSuppression

        suppression = AlertSuppression()

        for i in range(10):
            suppression.should_suppress("rule_1", max_per_hour=10)

        result = suppression.should_suppress("rule_1", max_per_hour=10)
        assert result is True

    def test_suppression_reset(self):
        """测试重置抑制"""
        from services.alert_service import AlertSuppression

        suppression = AlertSuppression()

        for i in range(10):
            suppression.should_suppress("rule_1", max_per_hour=10)

        suppression.reset("rule_1")

        result = suppression.should_suppress("rule_1", max_per_hour=10)
        assert result is False


class TestThresholdChecker:
    """阈值检查服务测试"""

    def test_record_metric(self):
        """测试记录指标"""
        from services.alert_service import ThresholdChecker

        checker = ThresholdChecker()
        checker.record_metric("test_metric", 10.5)
        checker.record_metric("test_metric", 20.5)

        values = checker.get_metric_values("test_metric", time_window_minutes=60)
        assert len(values) == 2
        assert 10.5 in values
        assert 20.5 in values

    def test_get_metric_stats(self):
        """测试获取指标统计"""
        from services.alert_service import ThresholdChecker

        checker = ThresholdChecker()
        checker.record_metric("test_metric", 10)
        checker.record_metric("test_metric", 20)
        checker.record_metric("test_metric", 30)

        stats = checker.get_metric_stats("test_metric", time_window_minutes=60)

        assert stats["count"] == 3
        assert stats["sum"] == 60
        assert stats["avg"] == 20
        assert stats["min"] == 10
        assert stats["max"] == 30
        assert stats["latest"] == 30

    def test_check_threshold(self):
        """测试阈值检查"""
        from models.alert import ThresholdConfig, ThresholdOperator
        from services.alert_service import ThresholdChecker

        checker = ThresholdChecker()
        config = ThresholdConfig(
            field="test", operator=ThresholdOperator.GREATER_THAN, value=50
        )

        assert checker.check_threshold(config, 60) is True
        assert checker.check_threshold(config, 40) is False


class TestAlertRuleEngine:
    """预警规则引擎测试"""

    def test_init_default_rules(self):
        """测试默认规则初始化"""
        from services.alert_service import AlertRuleEngine

        engine = AlertRuleEngine()

        assert len(engine.rules) >= 4
        assert "negative_surge" in engine.rules
        assert "volume_spike" in engine.rules
        assert "sentiment_shift" in engine.rules
        assert "hot_topic" in engine.rules

    def test_check_alerts_negative_surge(self):
        """测试负面舆情激增检测"""
        from services.alert_service import AlertRuleEngine

        engine = AlertRuleEngine()

        metrics = {"negative_count": 60, "total_count": 100, "time_window_minutes": 30}

        alerts = engine.check_alerts(metrics)

        negative_alerts = [a for a in alerts if a.rule_id == "negative_surge"]
        assert len(negative_alerts) > 0

    def test_check_alerts_volume_spike(self):
        """测试讨论量异常检测"""
        from services.alert_service import AlertRuleEngine

        engine = AlertRuleEngine()

        metrics = {
            "current_count": 100,
            "baseline_count": 20,
            "time_window_minutes": 60,
        }

        alerts = engine.check_alerts(metrics)

        volume_alerts = [a for a in alerts if a.rule_id == "volume_spike"]
        assert len(volume_alerts) > 0

    def test_check_alerts_sentiment_shift(self):
        """测试情感突变检测"""
        from services.alert_service import AlertRuleEngine

        engine = AlertRuleEngine()

        metrics = {
            "current_sentiment": 0.2,
            "previous_sentiment": 0.7,
            "time_window_minutes": 30,
        }

        alerts = engine.check_alerts(metrics)

        sentiment_alerts = [a for a in alerts if a.rule_id == "sentiment_shift"]
        assert len(sentiment_alerts) > 0

    def test_priority_ordering(self):
        """测试优先级排序"""
        from services.alert_service import AlertRuleEngine

        engine = AlertRuleEngine()
        rules = engine.get_rules()

        priorities = [r["priority"] for r in rules]
        assert priorities == sorted(priorities, reverse=True)

    def test_add_rule(self):
        """测试添加规则"""
        from models.alert import (
            AlertLevel,
            AlertRule,
            AlertType,
            ThresholdConfig,
            ThresholdOperator,
        )
        from services.alert_service import AlertRuleEngine

        engine = AlertRuleEngine()

        rule = AlertRule(
            id="custom_rule",
            name="自定义规则",
            alert_type=AlertType.CUSTOM,
            level=AlertLevel.INFO,
            thresholds=[
                ThresholdConfig(
                    field="custom_field",
                    operator=ThresholdOperator.GREATER_THAN,
                    value=100,
                )
            ],
        )

        success, msg = engine.add_rule(rule)
        assert success is True
        assert "custom_rule" in engine.rules

    def test_remove_rule(self):
        """测试移除规则"""
        from services.alert_service import AlertRuleEngine

        engine = AlertRuleEngine()

        result = engine.remove_rule("hot_topic")
        assert result is True
        assert "hot_topic" not in engine.rules

    def test_cooldown(self):
        """测试冷却时间"""
        from services.alert_service import AlertRuleEngine

        engine = AlertRuleEngine()

        metrics = {"negative_count": 60, "total_count": 100, "time_window_minutes": 30}

        engine.check_alerts(metrics)

        metrics2 = {"negative_count": 70, "total_count": 100, "time_window_minutes": 30}

        alerts2 = engine.check_alerts(metrics2)
        negative_alerts = [a for a in alerts2 if a.rule_id == "negative_surge"]
        assert len(negative_alerts) == 0

    def test_get_stats(self):
        """测试获取统计"""
        from services.alert_service import AlertRuleEngine

        engine = AlertRuleEngine()

        stats = engine.get_stats()

        assert "total_alerts" in stats
        assert "unread_count" in stats
        assert "level_distribution" in stats
        assert "type_distribution" in stats
        assert "active_rules" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
