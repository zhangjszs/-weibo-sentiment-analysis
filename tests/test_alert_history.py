#!/usr/bin/env python3
"""
预警历史记录管理单元测试
"""

import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, "src")


class TestAlertHistoryFilter:
    """历史记录筛选测试"""

    def test_init(self):
        """测试初始化"""
        from services.alert_history_service import AlertHistoryFilter

        filter_params = AlertHistoryFilter()
        assert filter_params.start_time is None
        assert filter_params.end_time is None
        assert filter_params.alert_type is None

    def test_matches_time_range(self):
        """测试时间范围筛选"""
        from models.alert import AlertHistory, AlertLevel, AlertType
        from services.alert_history_service import AlertHistoryFilter

        alert = AlertHistory(
            id="test-001",
            rule_id="rule-001",
            alert_type=AlertType.NEGATIVE_SURGE,
            level=AlertLevel.WARNING,
            title="测试预警",
            message="测试消息",
            created_at=datetime.now(),
        )

        filter_params = AlertHistoryFilter(
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=1),
        )
        assert filter_params.matches(alert)

        filter_params = AlertHistoryFilter(
            start_time=datetime.now() + timedelta(hours=1)
        )
        assert not filter_params.matches(alert)

    def test_matches_level(self):
        """测试级别筛选"""
        from models.alert import AlertHistory, AlertLevel, AlertType
        from services.alert_history_service import AlertHistoryFilter

        alert = AlertHistory(
            id="test-001",
            rule_id="rule-001",
            alert_type=AlertType.NEGATIVE_SURGE,
            level=AlertLevel.DANGER,
            title="测试预警",
            message="测试消息",
        )

        filter_params = AlertHistoryFilter(level=AlertLevel.DANGER)
        assert filter_params.matches(alert)

        filter_params = AlertHistoryFilter(level=AlertLevel.WARNING)
        assert not filter_params.matches(alert)

    def test_matches_keyword(self):
        """测试关键词筛选"""
        from models.alert import AlertHistory, AlertLevel, AlertType
        from services.alert_history_service import AlertHistoryFilter

        alert = AlertHistory(
            id="test-001",
            rule_id="rule-001",
            alert_type=AlertType.NEGATIVE_SURGE,
            level=AlertLevel.WARNING,
            title="负面舆情激增预警",
            message="检测到大量负面评论",
        )

        filter_params = AlertHistoryFilter(keyword="负面")
        assert filter_params.matches(alert)

        filter_params = AlertHistoryFilter(keyword="正面")
        assert not filter_params.matches(alert)


class TestPaginationParams:
    """分页参数测试"""

    def test_init(self):
        """测试初始化"""
        from services.alert_history_service import PaginationParams

        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20
        assert params.sort_by == "created_at"
        assert params.sort_order == "desc"


class TestAlertHistoryManager:
    """预警历史管理器测试"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        from services.alert_history_service import AlertHistoryManager

        return AlertHistoryManager()

    @pytest.fixture
    def sample_alert(self):
        """创建示例预警"""
        from models.alert import Alert, AlertLevel, AlertType

        return Alert(
            id="alert-001",
            rule_id="rule-001",
            rule_name="负面舆情激增",
            alert_type=AlertType.NEGATIVE_SURGE,
            level=AlertLevel.DANGER,
            title="负面舆情激增预警",
            message="检测到大量负面评论",
        )

    def test_init(self, manager):
        """测试初始化"""
        assert manager.max_records == 10000
        assert manager.count() == 0

    def test_add_alert(self, manager, sample_alert):
        """测试添加预警"""
        history = manager.add_alert(sample_alert)

        assert history.id == sample_alert.id
        assert manager.count() == 1

    def test_get_by_id(self, manager, sample_alert):
        """测试根据ID获取"""
        manager.add_alert(sample_alert)

        result = manager.get_by_id("alert-001")
        assert result is not None
        assert result.id == "alert-001"

        result = manager.get_by_id("non-existent")
        assert result is None

    def test_query_all(self, manager, sample_alert):
        """测试查询所有"""
        manager.add_alert(sample_alert)

        result = manager.query()

        assert result.total == 1
        assert len(result.items) == 1

    def test_query_with_pagination(self, manager):
        """测试分页查询"""
        from models.alert import Alert, AlertLevel, AlertType

        for i in range(25):
            alert = Alert(
                id=f"alert-{i:03d}",
                rule_id="rule-001",
                rule_name="测试规则",
                alert_type=AlertType.NEGATIVE_SURGE,
                level=AlertLevel.WARNING,
                title=f"测试预警 {i}",
                message="测试消息",
            )
            manager.add_alert(alert)

        from services.alert_history_service import PaginationParams

        pagination = PaginationParams(page=1, page_size=10)
        result = manager.query(pagination=pagination)

        assert result.total == 25
        assert len(result.items) == 10
        assert result.page == 1
        assert result.total_pages == 3
        assert result.has_next is True
        assert result.has_prev is False

        pagination = PaginationParams(page=2, page_size=10)
        result = manager.query(pagination=pagination)

        assert result.page == 2
        assert result.has_next is True
        assert result.has_prev is True

    def test_query_with_filter(self, manager, sample_alert):
        """测试筛选查询"""
        from models.alert import Alert, AlertLevel, AlertType
        from services.alert_history_service import AlertHistoryFilter

        manager.add_alert(sample_alert)

        alert2 = Alert(
            id="alert-002",
            rule_id="rule-002",
            rule_name="情感突变",
            alert_type=AlertType.SENTIMENT_SHIFT,
            level=AlertLevel.WARNING,
            title="情感突变预警",
            message="情感倾向发生变化",
        )
        manager.add_alert(alert2)

        filter_params = AlertHistoryFilter(level=AlertLevel.DANGER)
        result = manager.query(filter_params=filter_params)

        assert result.total == 1
        assert result.items[0]["id"] == "alert-001"

    def test_mark_read(self, manager, sample_alert):
        """测试标记已读"""
        manager.add_alert(sample_alert)

        assert manager.count_unread() == 1

        success = manager.mark_read("alert-001")
        assert success is True
        assert manager.count_unread() == 0

        success = manager.mark_read("non-existent")
        assert success is False

    def test_mark_handled(self, manager, sample_alert):
        """测试标记已处理"""
        manager.add_alert(sample_alert)

        assert manager.count_unhandled() == 1

        success = manager.mark_handled("alert-001", "admin", "已处理")
        assert success is True
        assert manager.count_unhandled() == 0

        result = manager.get_by_id("alert-001")
        assert result.is_handled is True
        assert result.handler == "admin"
        assert result.notes == "已处理"

    def test_batch_mark_read(self, manager):
        """测试批量标记已读"""
        from models.alert import Alert, AlertLevel, AlertType

        alert_ids = []
        for i in range(5):
            alert = Alert(
                id=f"alert-{i:03d}",
                rule_id="rule-001",
                rule_name="测试规则",
                alert_type=AlertType.NEGATIVE_SURGE,
                level=AlertLevel.WARNING,
                title=f"测试预警 {i}",
                message="测试消息",
            )
            manager.add_alert(alert)
            alert_ids.append(f"alert-{i:03d}")

        count = manager.batch_mark_read(alert_ids[:3])
        assert count == 3
        assert manager.count_unread() == 2

    def test_delete(self, manager, sample_alert):
        """测试删除"""
        manager.add_alert(sample_alert)

        assert manager.count() == 1

        success = manager.delete("alert-001")
        assert success is True
        assert manager.count() == 0

        success = manager.delete("non-existent")
        assert success is False

    def test_clear_all(self, manager):
        """测试清空"""
        from models.alert import Alert, AlertLevel, AlertType

        for i in range(5):
            alert = Alert(
                id=f"alert-{i:03d}",
                rule_id="rule-001",
                rule_name="测试规则",
                alert_type=AlertType.NEGATIVE_SURGE,
                level=AlertLevel.WARNING,
                title=f"测试预警 {i}",
                message="测试消息",
            )
            manager.add_alert(alert)

        count = manager.clear_all()
        assert count == 5
        assert manager.count() == 0

    def test_get_statistics(self, manager):
        """测试获取统计"""
        from models.alert import Alert, AlertLevel, AlertType

        for i in range(10):
            level = AlertLevel.WARNING if i < 5 else AlertLevel.DANGER
            alert = Alert(
                id=f"alert-{i:03d}",
                rule_id="rule-001",
                rule_name="测试规则",
                alert_type=AlertType.NEGATIVE_SURGE,
                level=level,
                title=f"测试预警 {i}",
                message="测试消息",
            )
            manager.add_alert(alert)

        stats = manager.get_statistics(time_range=7)

        assert stats["total_alerts"] == 10
        assert "level_distribution" in stats
        assert "type_distribution" in stats
        assert "daily_trend" in stats
        assert "hourly_trend" in stats

    def test_export_to_csv(self, manager, sample_alert):
        """测试导出CSV"""
        manager.add_alert(sample_alert)

        csv_data = manager.export_to_csv()

        assert "alert-001" in csv_data
        assert "负面舆情激增预警" in csv_data
        assert "ID,规则ID,预警类型" in csv_data

    def test_export_to_json(self, manager, sample_alert):
        """测试导出JSON"""
        manager.add_alert(sample_alert)

        json_data = manager.export_to_json()

        assert "alert-001" in json_data
        assert "负面舆情激增预警" in json_data

    def test_max_records_limit(self):
        """测试最大记录限制"""
        from models.alert import Alert, AlertLevel, AlertType
        from services.alert_history_service import AlertHistoryManager

        manager = AlertHistoryManager(max_records=5)

        for i in range(10):
            alert = Alert(
                id=f"alert-{i:03d}",
                rule_id="rule-001",
                rule_name="测试规则",
                alert_type=AlertType.NEGATIVE_SURGE,
                level=AlertLevel.WARNING,
                title=f"测试预警 {i}",
                message="测试消息",
            )
            manager.add_alert(alert)

        assert manager.count() == 5


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        from models.alert import Alert, AlertLevel, AlertType
        from services.alert_history_service import (
            AlertHistoryFilter,
            AlertHistoryManager,
            PaginationParams,
        )

        manager = AlertHistoryManager()

        for i in range(20):
            level = [
                AlertLevel.INFO,
                AlertLevel.WARNING,
                AlertLevel.DANGER,
                AlertLevel.CRITICAL,
            ][i % 4]
            alert_type = [
                AlertType.NEGATIVE_SURGE,
                AlertType.SENTIMENT_SHIFT,
                AlertType.HOT_TOPIC,
            ][i % 3]

            alert = Alert(
                id=f"alert-{i:03d}",
                rule_id=f"rule-{i % 3}",
                rule_name="测试规则",
                alert_type=alert_type,
                level=level,
                title=f"测试预警 {i}",
                message=f"测试消息 {i}",
            )
            manager.add_alert(alert)

        assert manager.count() == 20

        filter_params = AlertHistoryFilter(level=AlertLevel.DANGER)
        result = manager.query(filter_params=filter_params)
        assert result.total == 5

        pagination = PaginationParams(page=1, page_size=5)
        result = manager.query(pagination=pagination)
        assert len(result.items) == 5
        assert result.has_next is True

        manager.mark_read("alert-000")
        assert manager.count_unread() == 19

        manager.mark_handled("alert-001", "admin", "已处理")
        assert manager.count_unhandled() == 19

        stats = manager.get_statistics()
        assert stats["total_alerts"] == 20

        csv_data = manager.export_to_csv()
        assert "alert-000" in csv_data

        json_data = manager.export_to_json()
        assert "alert-000" in json_data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
