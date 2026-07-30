#!/usr/bin/env python3
"""
预警通知服务单元测试
"""

import smtplib
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, "src")


class TestNotificationRecipient:
    """通知接收人测试"""

    def test_init(self):
        """测试初始化"""
        from services.notification_service import (
            NotificationChannel,
            NotificationRecipient,
        )

        recipient = NotificationRecipient(
            user_id=1,
            email="test@example.com",
            phone="13800138000",
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
        )

        assert recipient.user_id == 1
        assert recipient.email == "test@example.com"
        assert recipient.phone == "13800138000"
        assert len(recipient.channels) == 2

    def test_can_receive_enabled(self):
        """测试启用状态"""
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationRecipient,
        )

        recipient = NotificationRecipient(
            user_id=1,
            email="test@example.com",
            channels=[NotificationChannel.EMAIL],
            enabled=True,
        )

        assert recipient.can_receive(
            NotificationLevel.WARNING, NotificationChannel.EMAIL
        )

    def test_can_receive_disabled(self):
        """测试禁用状态"""
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationRecipient,
        )

        recipient = NotificationRecipient(
            user_id=1,
            email="test@example.com",
            channels=[NotificationChannel.EMAIL],
            enabled=False,
        )

        assert not recipient.can_receive(
            NotificationLevel.WARNING, NotificationChannel.EMAIL
        )

    def test_can_receive_level_filter(self):
        """测试级别过滤"""
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationRecipient,
        )

        recipient = NotificationRecipient(
            user_id=1,
            email="test@example.com",
            channels=[NotificationChannel.EMAIL],
            min_level=NotificationLevel.DANGER,
        )

        assert not recipient.can_receive(
            NotificationLevel.INFO, NotificationChannel.EMAIL
        )
        assert not recipient.can_receive(
            NotificationLevel.WARNING, NotificationChannel.EMAIL
        )
        assert recipient.can_receive(
            NotificationLevel.DANGER, NotificationChannel.EMAIL
        )
        assert recipient.can_receive(
            NotificationLevel.CRITICAL, NotificationChannel.EMAIL
        )

    def test_can_receive_channel_filter(self):
        """测试渠道过滤"""
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationRecipient,
        )

        recipient = NotificationRecipient(
            user_id=1,
            email="test@example.com",
            phone="13800138000",
            channels=[NotificationChannel.EMAIL],
        )

        assert recipient.can_receive(
            NotificationLevel.WARNING, NotificationChannel.EMAIL
        )
        assert not recipient.can_receive(
            NotificationLevel.WARNING, NotificationChannel.SMS
        )


class TestNotificationMessage:
    """通知消息测试"""

    def test_init(self):
        """测试初始化"""
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationMessage,
            NotificationRecipient,
            NotificationStatus,
        )

        recipient = NotificationRecipient(user_id=1, email="test@example.com")
        message = NotificationMessage(
            id="msg-001",
            alert_id="alert-001",
            channel=NotificationChannel.EMAIL,
            recipient=recipient,
            subject="测试通知",
            content="测试内容",
            level=NotificationLevel.WARNING,
        )

        assert message.id == "msg-001"
        assert message.status == NotificationStatus.PENDING
        assert message.retry_count == 0

    def test_to_dict(self):
        """测试序列化"""
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationMessage,
            NotificationRecipient,
        )

        recipient = NotificationRecipient(user_id=1, email="test@example.com")
        message = NotificationMessage(
            id="msg-001",
            alert_id="alert-001",
            channel=NotificationChannel.EMAIL,
            recipient=recipient,
            subject="测试通知",
            content="测试内容",
            level=NotificationLevel.WARNING,
        )

        result = message.to_dict()

        assert result["id"] == "msg-001"
        assert result["channel"] == "email"
        assert result["level"] == "warning"
        assert result["status"] == "pending"


class TestNotificationTemplate:
    """通知模板测试"""

    def test_init(self):
        """测试初始化"""
        from services.notification_service import (
            NotificationChannel,
            NotificationTemplate,
        )

        template = NotificationTemplate(
            name="测试模板",
            alert_type="test",
            channel=NotificationChannel.EMAIL,
            subject_template="【预警】{level}",
            content_template="内容：{message}",
        )

        assert template.name == "测试模板"
        assert template.enabled is True

    def test_render(self):
        """测试模板渲染"""
        from services.notification_service import (
            NotificationChannel,
            NotificationTemplate,
        )

        template = NotificationTemplate(
            name="测试模板",
            alert_type="test",
            channel=NotificationChannel.EMAIL,
            subject_template="【预警】{level} - {title}",
            content_template="预警内容：{message}\n时间：{time}",
            sms_template="【预警】{message}",
        )

        context = {
            "level": "高",
            "title": "测试预警",
            "message": "这是一条测试消息",
            "time": "2026-02-21 10:00:00",
        }

        subject, content, sms = template.render(context)

        assert subject == "【预警】高 - 测试预警"
        assert "这是一条测试消息" in content
        assert sms == "【预警】这是一条测试消息"


class TestNotificationQueue:
    """通知队列测试"""

    def test_init(self):
        """测试初始化"""
        from services.notification_service import NotificationQueue

        queue = NotificationQueue(max_size=100)

        assert queue.max_size == 100
        assert queue.size() == 0

    def test_enqueue_dequeue(self):
        """测试入队出队"""
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationMessage,
            NotificationQueue,
            NotificationRecipient,
        )

        queue = NotificationQueue()
        recipient = NotificationRecipient(user_id=1)
        message = NotificationMessage(
            id="msg-001",
            alert_id="alert-001",
            channel=NotificationChannel.EMAIL,
            recipient=recipient,
            subject="测试",
            content="内容",
            level=NotificationLevel.WARNING,
        )

        assert queue.enqueue(message)
        assert queue.size() == 1

        dequeued = queue.dequeue()
        assert dequeued.id == "msg-001"
        assert queue.size() == 0

    def test_retry_queue(self):
        """测试重试队列"""
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationMessage,
            NotificationQueue,
            NotificationRecipient,
            NotificationStatus,
        )

        queue = NotificationQueue()
        recipient = NotificationRecipient(user_id=1)
        message = NotificationMessage(
            id="msg-001",
            alert_id="alert-001",
            channel=NotificationChannel.EMAIL,
            recipient=recipient,
            subject="测试",
            content="内容",
            level=NotificationLevel.WARNING,
        )

        queue.enqueue_retry(message)
        assert message.status == NotificationStatus.RETRYING
        assert queue.retry_size() == 1

    def test_get_stats(self):
        """测试统计"""
        from services.notification_service import NotificationQueue

        queue = NotificationQueue()
        stats = queue.get_stats()

        assert "total_queued" in stats
        assert "queue_size" in stats
        assert "retry_queue_size" in stats


class TestEmailSender:
    """邮件发送测试"""

    def test_init(self):
        """测试初始化"""
        from services.notification_service import EmailSender

        sender = EmailSender(
            {
                "smtp_host": "smtp.test.com",
                "smtp_port": 465,
                "smtp_user": "user@test.com",
                "smtp_password": "password",
            }
        )

        assert sender.smtp_host == "smtp.test.com"
        assert sender.smtp_port == 465

    def test_send_invalid_email(self):
        """测试无效邮箱"""
        from services.notification_service import EmailSender

        sender = EmailSender({"smtp_host": "invalid.host", "smtp_port": 465})

        success, error = sender.send("invalid@test.com", "测试", "内容")
        assert success is False


class TestSMSSender:
    """短信发送测试"""

    def test_init(self):
        """测试初始化"""
        from services.notification_service import SMSSender

        sender = SMSSender(
            {
                "access_key": "test_key",
                "secret_key": "test_secret",
                "sign_name": "测试签名",
            }
        )

        assert sender.access_key == "test_key"
        assert sender.sign_name == "测试签名"

    def test_send_mock(self):
        """测试模拟发送"""
        from services.notification_service import SMSSender

        sender = SMSSender()
        success, error = sender.send("13800138000", "测试短信内容")

        assert success is True

    def test_send_batch(self):
        """测试批量发送"""
        from services.notification_service import SMSSender

        sender = SMSSender()
        phones = ["13800138001", "13800138002", "13800138003"]
        results = sender.send_batch(phones, "测试批量短信")

        assert len(results) == 3
        for phone in phones:
            assert results[phone][0] is True


class TestNotificationService:
    """通知服务测试"""

    def test_init(self):
        """测试初始化"""
        from services.notification_service import NotificationService

        service = NotificationService()

        assert service.email_sender is not None
        assert service.sms_sender is not None
        assert service.queue is not None
        assert len(service.templates) >= 3

    def test_add_remove_recipient(self):
        """测试添加移除接收人"""
        from services.notification_service import (
            NotificationChannel,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()
        recipient = NotificationRecipient(
            user_id=1,
            email="test@example.com",
            phone="13800138000",
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
        )

        service.add_recipient(recipient)
        recipients = service.get_recipients()
        assert len(recipients) == 1

        service.remove_recipient(1)
        recipients = service.get_recipients()
        assert len(recipients) == 0

    def test_create_notification(self):
        """测试创建通知"""
        from services.notification_service import (
            NotificationChannel,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()
        recipient = NotificationRecipient(
            user_id=1, email="test@example.com", channels=[NotificationChannel.EMAIL]
        )

        alert_data = {
            "id": "alert-001",
            "alert_type": "negative_surge",
            "level": "danger",
            "title": "负面舆情激增",
            "message": "检测到大量负面评论",
            "negative_count": 100,
            "total_count": 200,
            "negative_ratio": 0.5,
        }

        message = service.create_notification(
            alert_data, NotificationChannel.EMAIL, recipient
        )

        assert message is not None
        assert message.recipient.user_id == 1
        assert "负面舆情" in message.subject or "预警" in message.subject

    def test_queue_notification(self):
        """测试队列通知"""
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()
        recipient = NotificationRecipient(
            user_id=1,
            email="test@example.com",
            channels=[NotificationChannel.EMAIL],
            min_level=NotificationLevel.INFO,
        )

        service.add_recipient(recipient)

        alert_data = {
            "id": "alert-001",
            "alert_type": "hot_topic",
            "level": "critical",
            "message": "测试预警",
            "topic_name": "测试话题",
            "mention_count": 100,
            "time_window": 60,
        }

        service.queue_notification(alert_data, channels=[NotificationChannel.EMAIL])

        assert service.queue.size() >= 1

    def test_handle_alert_uses_rule_channels(self):
        """测试预警事件会按规则渠道入队通知"""
        from services.notification_service import (
            NotificationChannel,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()
        recipient = NotificationRecipient(
            user_id=1,
            email="test@example.com",
            channels=[NotificationChannel.EMAIL, NotificationChannel.WEBSOCKET],
        )
        service.add_recipient(recipient)

        service.handle_alert(
            {
                "id": "alert-queue-001",
                "alert_type": "hot_topic",
                "level": "warning",
                "title": "热点话题",
                "message": "测试预警",
                "notification_channels": ["email", "websocket"],
                "data": {
                    "topic_name": "测试话题",
                    "mention_count": 120,
                    "time_window": 60,
                },
            }
        )

        assert service.queue.size() == 2

    def test_sync_admin_recipients_adds_websocket_channel(self):
        """测试管理员同步会创建默认 WebSocket 接收人"""
        from services.notification_service import (
            NotificationChannel,
            NotificationService,
        )

        service = NotificationService()

        synced = service.sync_admin_recipients(
            user_records=[
                {
                    "id": 7,
                    "username": "admin",
                    "email": "admin@example.com",
                }
            ],
            admin_usernames={"admin"},
        )

        assert synced == 1
        recipients = service.get_recipients()
        assert len(recipients) == 1
        assert NotificationChannel.WEBSOCKET in recipients[0].channels
        assert NotificationChannel.EMAIL in recipients[0].channels

    def test_get_stats(self):
        """测试获取统计"""
        from services.notification_service import NotificationService

        service = NotificationService()
        stats = service.get_stats()

        assert "queue_stats" in stats
        assert "recipient_count" in stats
        assert "template_count" in stats
        assert "running" in stats

    def test_start_stop(self):
        """测试启动停止"""
        from services.notification_service import NotificationService

        service = NotificationService()

        service.start()
        assert service._running is True

        service.stop()
        assert service._running is False


class TestIntegration:
    """集成测试"""

    def test_full_notification_flow(self):
        """测试完整通知流程"""
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()

        recipient = NotificationRecipient(
            user_id=1,
            email="admin@example.com",
            phone="13800138000",
            min_level=NotificationLevel.WARNING,
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
        )

        service.add_recipient(recipient)

        alert_data = {
            "id": "alert-integration-001",
            "alert_type": "sentiment_shift",
            "level": "danger",
            "title": "情感突变预警",
            "message": "检测到情感倾向急剧下降",
            "direction": "下降",
            "magnitude": 0.35,
            "current_sentiment": 0.25,
            "previous_sentiment": 0.60,
        }

        service.queue_notification(alert_data)

        assert service.queue.size() >= 1

        stats = service.get_stats()
        assert stats["queue_stats"]["total_queued"] >= 1


# ----------------------------------------------------------------------
# 补充测试：覆盖 notification_service.py 剩余路径
# ----------------------------------------------------------------------


class TestParseLevel:
    """测试 _parse_level（service.py 59-64）"""

    def test_valid_level(self):
        from services.notification_service import NotificationLevel, _parse_level

        assert _parse_level("warning") == NotificationLevel.WARNING
        assert _parse_level("critical") == NotificationLevel.CRITICAL

    def test_invalid_level_defaults_warning(self):
        from services.notification_service import NotificationLevel, _parse_level

        assert _parse_level("nonexistent") == NotificationLevel.WARNING
        assert _parse_level("") == NotificationLevel.WARNING


class TestQuietHours:
    """测试免打扰时段逻辑（service.py 92-108）"""

    @staticmethod
    def _patch_time(monkeypatch, hhmm):
        """将 notification_service.datetime.now().strftime() 固定为 hhmm"""
        from services import notification_service as ns

        class _FakeNow:
            def strftime(self, fmt):
                return hhmm

        class _FakeDateTime:
            @classmethod
            def now(cls):
                return _FakeNow()

        monkeypatch.setattr(ns, "datetime", _FakeDateTime)

    @staticmethod
    def _recipient(quiet_hours):
        from services.notification_service import (
            NotificationChannel,
            NotificationRecipient,
        )

        return NotificationRecipient(
            user_id=1,
            email="x@y.com",
            channels=[NotificationChannel.EMAIL],
            quiet_hours=quiet_hours,
        )

    def test_empty_quiet_hours(self):
        """无配置不算免打扰"""
        assert self._recipient({})._in_quiet_hours() is False

    def test_in_range_same_day(self, monkeypatch):
        self._patch_time(monkeypatch, "10:30")
        assert self._recipient({"start": "09:00", "end": "17:00"})._in_quiet_hours() is True

    def test_out_of_range_same_day(self, monkeypatch):
        self._patch_time(monkeypatch, "20:00")
        assert self._recipient({"start": "09:00", "end": "17:00"})._in_quiet_hours() is False

    def test_overnight_in_range_evening(self, monkeypatch):
        self._patch_time(monkeypatch, "23:00")
        assert self._recipient({"start": "22:00", "end": "06:00"})._in_quiet_hours() is True

    def test_overnight_in_range_morning(self, monkeypatch):
        self._patch_time(monkeypatch, "03:00")
        assert self._recipient({"start": "22:00", "end": "06:00"})._in_quiet_hours() is True

    def test_overnight_out_of_range(self, monkeypatch):
        self._patch_time(monkeypatch, "10:00")
        assert self._recipient({"start": "22:00", "end": "06:00"})._in_quiet_hours() is False

    def test_can_receive_blocked_by_quiet_hours(self, monkeypatch):
        """免打扰时段内 can_receive 应返回 False（service.py 92-93）"""
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
        )

        self._patch_time(monkeypatch, "10:30")
        recipient = self._recipient({"start": "09:00", "end": "17:00"})
        assert (
            recipient.can_receive(NotificationLevel.WARNING, NotificationChannel.EMAIL)
            is False
        )


class TestEmailSenderAdvanced:
    """测试 EmailSender 高级路径（service.py 195, 200-212）"""

    def test_send_plain_text(self):
        """html=False 分支（195）"""
        from services.notification_service import EmailSender

        sender = EmailSender({"smtp_host": "smtp.test.com", "smtp_port": 465})
        with patch("smtplib.SMTP_SSL") as mock_ssl:
            success, _ = sender.send("x@y.com", "s", "c", html=False)
        assert success is True
        mock_ssl.return_value.sendmail.assert_called_once()

    def test_send_starttls_success(self):
        """use_ssl=False 走 SMTP + starttls 成功路径（200-208）"""
        from services.notification_service import EmailSender

        sender = EmailSender(
            {"smtp_host": "smtp.test.com", "smtp_port": 587, "use_ssl": False}
        )
        with patch("smtplib.SMTP") as mock_smtp:
            instance = mock_smtp.return_value
            success, _ = sender.send("x@y.com", "s", "c")
        assert success is True
        instance.starttls.assert_called_once()
        instance.login.assert_called_once()
        instance.sendmail.assert_called_once()
        instance.quit.assert_called_once()

    def test_send_smtp_exception(self):
        """SMTPException 分支（211-212）"""
        from services.notification_service import EmailSender

        sender = EmailSender({"smtp_host": "smtp.test.com", "smtp_port": 465})
        with patch("smtplib.SMTP_SSL") as mock_ssl:
            mock_ssl.return_value.login.side_effect = smtplib.SMTPException(
                "login failed"
            )
            success, error = sender.send("x@y.com", "s", "c")
        assert success is False
        assert "login failed" in error


class TestSMSSenderError:
    """测试 SMS 异常路径（service.py 234-236）"""

    def test_send_connection_error(self, monkeypatch):
        """logger.info 抛 ConnectionError 应被捕获并返回失败"""
        from services import notification_service as ns

        monkeypatch.setattr(
            ns.logger,
            "info",
            MagicMock(side_effect=ConnectionError("network down")),
        )
        sender = ns.SMSSender()
        success, error = sender.send("13800138000", "content")
        assert success is False
        assert "network down" in error


class TestNotificationQueueAdvanced:
    """测试队列边界（service.py 265-266, 282, 292, 316-322）"""

    @staticmethod
    def _make_message(mid="m"):
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationMessage,
            NotificationRecipient,
        )

        return NotificationMessage(
            id=mid,
            alert_id="a",
            channel=NotificationChannel.EMAIL,
            recipient=NotificationRecipient(user_id=1),
            subject="s",
            content="c",
            level=NotificationLevel.WARNING,
        )

    def test_enqueue_full(self):
        from services.notification_service import NotificationQueue

        queue = NotificationQueue(max_size=1)
        assert queue.enqueue(self._make_message("1")) is True
        assert queue.enqueue(self._make_message("2")) is False
        assert queue.size() == 1

    def test_enqueue_retry_full(self):
        from services.notification_service import NotificationQueue

        queue = NotificationQueue(max_size=1)
        assert queue.enqueue_retry(self._make_message("1")) is True
        assert queue.enqueue_retry(self._make_message("2")) is False
        assert queue.retry_size() == 1

    def test_get_retry_message_empty(self):
        from services.notification_service import NotificationQueue

        assert NotificationQueue().get_retry_message() is None

    def test_mark_sent_mark_failed(self):
        from services.notification_service import NotificationQueue

        queue = NotificationQueue()
        queue.mark_sent()
        queue.mark_failed()
        stats = queue.get_stats()
        assert stats["total_sent"] == 1
        assert stats["total_failed"] == 1


class TestNormalizeChannels:
    """测试渠道规范化（service.py 457-476）"""

    def test_mixed_valid_invalid(self):
        from services.notification_service import (
            NotificationChannel,
            NotificationService,
        )

        service = NotificationService()
        result = service._normalize_channels(
            ["email", "invalid", "sms", NotificationChannel.EMAIL]
        )
        assert result == [NotificationChannel.EMAIL, NotificationChannel.SMS]

    def test_empty(self):
        from services.notification_service import NotificationService

        service = NotificationService()
        assert service._normalize_channels(None) == []
        assert service._normalize_channels([]) == []

    def test_dedup(self):
        from services.notification_service import (
            NotificationChannel,
            NotificationService,
        )

        service = NotificationService()
        result = service._normalize_channels(["email", "email", "email"])
        assert result == [NotificationChannel.EMAIL]


class TestResolveChannels:
    """测试渠道解析（service.py 478-500）

    P0 #5：``_fetch_rule_channels`` 改为直接查 ``alert_rules`` 表
    （``alert_engine.rules`` 内存缓存已删除）。触及 DB 的用例依赖 conftest 的
    ``alert_db`` fixture（in-memory SQLite，monkeypatch ``database.db_session``），
    在测试库内构造规则再断言 ``resolve_channels`` 解析结果。
    """

    def test_explicit_channels(self):
        from services.notification_service import (
            NotificationChannel,
            NotificationService,
        )

        service = NotificationService()
        assert service.resolve_channels({"notification_channels": ["email"]}) == [
            NotificationChannel.EMAIL
        ]

    def test_fallback_to_rule(self, alert_db):
        """alert_data 无 notification_channels 但有 rule_id → 从 DB 取规则渠道"""
        from models.alert import AlertLevel, AlertRule, AlertType
        from services.notification_service import (
            NotificationChannel,
            NotificationService,
        )

        rule = AlertRule(
            id="rule-1",
            name="测试规则",
            alert_type=AlertType.CUSTOM,
            level=AlertLevel.WARNING,
            notification_channels=["sms"],
        )
        alert_db.add(rule)
        alert_db.commit()

        service = NotificationService()
        assert service.resolve_channels({"rule_id": "rule-1"}) == [
            NotificationChannel.SMS
        ]

    def test_rule_not_found_returns_websocket(self, alert_db):
        """规则不存在时 _fetch_rule_channels 返回 None → 回退 WEBSOCKET"""
        from services.notification_service import (
            NotificationChannel,
            NotificationService,
        )

        service = NotificationService()
        assert service.resolve_channels({"rule_id": "unknown"}) == [
            NotificationChannel.WEBSOCKET
        ]

    def test_no_channels_no_rule(self):
        from services.notification_service import (
            NotificationChannel,
            NotificationService,
        )

        service = NotificationService()
        assert service.resolve_channels({}) == [NotificationChannel.WEBSOCKET]

    def test_fetch_rule_channels_db_error_returns_none(self, monkeypatch):
        """DB 查询异常时 _fetch_rule_channels 应吞异常返回 None（best-effort）"""
        import database
        from services.notification_service import NotificationService

        fake_session = MagicMock()
        fake_session.get.side_effect = RuntimeError("db down")
        monkeypatch.setattr(database, "db_session", fake_session)

        service = NotificationService()
        assert service._fetch_rule_channels("rule-1") is None

    def test_fetch_rule_channels_returns_rule_channels(self, alert_db):
        """规则存在时直接返回其 notification_channels 配置"""
        from models.alert import AlertLevel, AlertRule, AlertType
        from services.notification_service import NotificationService

        rule = AlertRule(
            id="rule-ch",
            name="带渠道规则",
            alert_type=AlertType.CUSTOM,
            level=AlertLevel.INFO,
            notification_channels=["email", "sms"],
        )
        alert_db.add(rule)
        alert_db.commit()

        service = NotificationService()
        assert service._fetch_rule_channels("rule-ch") == ["email", "sms"]


class TestFetchAdminUsers:
    """测试管理员用户拉取（service.py 506-516）"""

    def test_fetch_admin_users(self, monkeypatch):
        from services.notification_service import NotificationService

        fake_repo = MagicMock()
        fake_repo.find_by_username.side_effect = (
            lambda u: {"id": 1, "username": u} if u == "admin" else None
        )
        monkeypatch.setattr(
            "repositories.user_repository.UserRepository", lambda: fake_repo
        )

        service = NotificationService()
        records = service._fetch_admin_users({"admin", "other"})
        # sorted: admin, other
        assert records[0] == {"id": 1, "username": "admin"}
        assert records[1] is None


class TestBuildRecipient:
    """测试接收人构建（service.py 518-559）"""

    def test_username_not_in_admins(self):
        from services.notification_service import NotificationService

        service = NotificationService()
        result = service._build_recipient({"id": 1, "username": "regular"}, {"admin"})
        assert result is None

    def test_user_id_none(self):
        from services.notification_service import NotificationService

        service = NotificationService()
        result = service._build_recipient({"username": "admin"}, {"admin"})
        assert result is None

    def test_admin_without_email_skips_email_channel(self):
        from services.notification_service import (
            NotificationChannel,
            NotificationService,
        )

        service = NotificationService()
        result = service._build_recipient(
            {"id": 1, "username": "admin"}, {"admin"}
        )
        assert result is not None
        assert NotificationChannel.WEBSOCKET in result.channels
        assert NotificationChannel.EMAIL not in result.channels

    def test_build_admin_channels_with_existing_no_dup(self):
        """已有渠道时应跳过追加（service.py 557->554）"""
        from services.notification_service import (
            NotificationChannel,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()
        existing = NotificationRecipient(
            user_id=1,
            email="a@b.com",
            channels=[NotificationChannel.WEBSOCKET, NotificationChannel.EMAIL],
        )
        service.add_recipient(existing)
        result = service._build_recipient(
            {"id": 1, "username": "admin", "email": "a@b.com"}, {"admin"}
        )
        assert result is not None
        assert result.channels.count(NotificationChannel.WEBSOCKET) == 1
        assert result.channels.count(NotificationChannel.EMAIL) == 1


class TestMergeRecipients:
    """测试接收人合并（service.py 561-577）"""

    def test_skip_none_records(self):
        from services.notification_service import NotificationService

        service = NotificationService()
        synced = service._merge_recipients(
            [None, {"id": 1, "username": "admin", "email": "a@b.com"}], {"admin"}
        )
        assert synced == 1

    def test_skip_invalid_recipient(self):
        from services.notification_service import NotificationService

        service = NotificationService()
        synced = service._merge_recipients([{"id": 1, "username": "x"}], {"admin"})
        assert synced == 0


class TestSyncAdminRecipientsConfig:
    """测试管理员同步入口（service.py 579-596）"""

    def test_admin_usernames_none_uses_config(self, monkeypatch):
        from services import notification_service as ns

        monkeypatch.setattr("config.settings.Config", MagicMock(ADMIN_USERS=["admin1"]))
        records = [{"id": 1, "username": "admin1", "email": "a@b.com"}]
        monkeypatch.setattr(
            ns.NotificationService, "_fetch_admin_users", lambda self, u: records
        )
        service = ns.NotificationService()
        assert service.sync_admin_recipients() == 1

    def test_empty_admin_usernames(self):
        from services.notification_service import NotificationService

        service = NotificationService()
        assert service.sync_admin_recipients(admin_usernames=set()) == 0

    def test_user_records_none_fetches(self, monkeypatch):
        from services.notification_service import NotificationService

        service = NotificationService()
        fetched = [{"id": 1, "username": "admin", "email": "a@b.com"}]
        monkeypatch.setattr(service, "_fetch_admin_users", lambda u: fetched)
        assert service.sync_admin_recipients(admin_usernames={"admin"}) == 1


class TestAlertBridge:
    """测试预警桥接与回调（service.py 602-626）"""

    def test_bind_alert_engine(self):
        from services.notification_service import NotificationService

        service = NotificationService()
        engine = MagicMock()
        assert service.bind_alert_engine(engine) is True
        engine.register_callback.assert_called_once_with(service.handle_alert)
        assert service._alert_bridge_registered is True

    def test_bind_alert_engine_duplicate(self):
        from services.notification_service import NotificationService

        service = NotificationService()
        engine = MagicMock()
        service.bind_alert_engine(engine)
        assert service.bind_alert_engine(engine) is False
        engine.register_callback.assert_called_once()

    def test_register_callback_and_trigger(self):
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationMessage,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()
        calls = []
        service.register_callback(lambda msg: calls.append(msg.id))

        recipient = NotificationRecipient(
            user_id=1, email="x@y.com", channels=[NotificationChannel.EMAIL]
        )
        message = NotificationMessage(
            id="m1",
            alert_id="a",
            channel=NotificationChannel.EMAIL,
            recipient=recipient,
            subject="s",
            content="c",
            level=NotificationLevel.WARNING,
        )
        with patch.object(service.email_sender, "send", return_value=(True, "")):
            service.send_notification(message)
        assert calls == ["m1"]

    def test_trigger_callbacks_swallows_error(self):
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationMessage,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()
        service.register_callback(lambda msg: (_ for _ in ()).throw(TypeError("bad")))
        good = []
        service.register_callback(lambda msg: good.append(msg.id))

        recipient = NotificationRecipient(
            user_id=1, email="x@y.com", channels=[NotificationChannel.EMAIL]
        )
        message = NotificationMessage(
            id="m1",
            alert_id="a",
            channel=NotificationChannel.EMAIL,
            recipient=recipient,
            subject="s",
            content="c",
            level=NotificationLevel.WARNING,
        )
        with patch.object(service.email_sender, "send", return_value=(True, "")):
            service.send_notification(message)  # 不应抛异常
        assert good == ["m1"]


class TestCreateNotificationNoTemplate:
    """测试无模板兜底（service.py 642-645）"""

    def test_no_template_falls_back(self):
        from services.notification_service import (
            NotificationChannel,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()
        recipient = NotificationRecipient(user_id=1, email="x@y.com")
        alert_data = {
            "alert_type": "unknown_type",
            "title": "自定义预警",
            "message": "内容",
            "level": "warning",
        }
        message = service.create_notification(
            alert_data, NotificationChannel.EMAIL, recipient
        )
        assert "自定义预警" in message.subject
        assert message.content == "内容"

    def test_invalid_level_defaults_warning(self):
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()
        recipient = NotificationRecipient(user_id=1)
        alert_data = {
            "alert_type": "unknown",
            "level": "bogus",
            "title": "t",
            "message": "m",
        }
        message = service.create_notification(
            alert_data, NotificationChannel.EMAIL, recipient
        )
        assert message.level == NotificationLevel.WARNING


class TestChannelSenders:
    """测试渠道发送器（service.py 689-736）"""

    @staticmethod
    def _message(channel, recipient=None):
        from services.notification_service import (
            NotificationLevel,
            NotificationMessage,
            NotificationRecipient,
        )

        return NotificationMessage(
            id="m",
            alert_id="a",
            channel=channel,
            recipient=recipient or NotificationRecipient(user_id=1),
            subject="s",
            content="c",
            level=NotificationLevel.WARNING,
        )

    def test_send_email_no_email(self):
        from services.notification_service import (
            NotificationChannel,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()
        recipient = NotificationRecipient(user_id=1, email=None)
        success, error = service._send_email(
            self._message(NotificationChannel.EMAIL, recipient)
        )
        assert success is False
        assert "邮箱为空" in error

    def test_send_sms_no_phone(self):
        from services.notification_service import (
            NotificationChannel,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()
        recipient = NotificationRecipient(user_id=1, phone=None)
        success, error = service._send_sms(
            self._message(NotificationChannel.SMS, recipient)
        )
        assert success is False
        assert "手机号为空" in error

    def test_send_websocket_socketio_none(self, monkeypatch):
        import sys

        fake_module = MagicMock()
        fake_module.websocket_service.socketio = None
        monkeypatch.setitem(sys.modules, "services.websocket_service", fake_module)

        from services.notification_service import (
            NotificationChannel,
            NotificationService,
        )

        service = NotificationService()
        success, error = service._send_websocket(self._message(NotificationChannel.WEBSOCKET))
        assert success is False
        assert "未初始化" in error

    def test_send_websocket_success(self, monkeypatch):
        import sys

        fake_module = MagicMock()
        fake_module.websocket_service.socketio = MagicMock()  # truthy
        monkeypatch.setitem(sys.modules, "services.websocket_service", fake_module)

        from services.notification_service import (
            NotificationChannel,
            NotificationService,
        )

        service = NotificationService()
        success, error = service._send_websocket(self._message(NotificationChannel.WEBSOCKET))
        assert success is True
        assert error == ""
        fake_module.websocket_service.send_to_user.assert_called_once()

    def test_send_websocket_import_error(self, monkeypatch):
        import sys

        monkeypatch.setitem(sys.modules, "services.websocket_service", None)

        from services.notification_service import (
            NotificationChannel,
            NotificationService,
        )

        service = NotificationService()
        success, _ = service._send_websocket(self._message(NotificationChannel.WEBSOCKET))
        assert success is False

    def test_send_websocket_attribute_error(self, monkeypatch):
        import sys

        fake_module = MagicMock()
        fake_module.websocket_service = MagicMock(spec=[])  # 无 socketio 属性
        monkeypatch.setitem(sys.modules, "services.websocket_service", fake_module)

        from services.notification_service import (
            NotificationChannel,
            NotificationService,
        )

        service = NotificationService()
        success, _ = service._send_websocket(self._message(NotificationChannel.WEBSOCKET))
        assert success is False

    def test_get_channel_sender_all(self):
        from services.notification_service import (
            NotificationChannel,
            NotificationService,
        )

        service = NotificationService()
        # bound method 每次访问都生成新对象，用 == 比较 __func__
        assert (
            service._get_channel_sender(NotificationChannel.EMAIL).__func__
            is NotificationService._send_email
        )
        assert (
            service._get_channel_sender(NotificationChannel.SMS).__func__
            is NotificationService._send_sms
        )
        assert (
            service._get_channel_sender(NotificationChannel.WEBSOCKET).__func__
            is NotificationService._send_websocket
        )

    def test_send_sms_success(self):
        """_send_sms 手机号存在时应调用 sms_sender.send（service.py 701）"""
        from services.notification_service import (
            NotificationChannel,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()
        recipient = NotificationRecipient(user_id=1, phone="13800138000")
        success, _ = service._send_sms(
            self._message(NotificationChannel.SMS, recipient)
        )
        assert success is True


class TestSendNotification:
    """测试 send_notification 状态流转（service.py 738-753）"""

    @staticmethod
    def _message():
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationMessage,
            NotificationRecipient,
        )

        return NotificationMessage(
            id="m",
            alert_id="a",
            channel=NotificationChannel.EMAIL,
            recipient=NotificationRecipient(user_id=1, email="x@y.com"),
            subject="s",
            content="c",
            level=NotificationLevel.WARNING,
        )

    def test_send_success(self):
        from services.notification_service import (
            NotificationService,
            NotificationStatus,
        )

        service = NotificationService()
        message = self._message()
        with patch.object(service.email_sender, "send", return_value=(True, "")):
            success, _ = service.send_notification(message)
        assert success is True
        assert message.status == NotificationStatus.SENT
        assert message.sent_at is not None
        assert service.queue.get_stats()["total_sent"] == 1

    def test_send_failure(self):
        from services.notification_service import (
            NotificationService,
            NotificationStatus,
        )

        service = NotificationService()
        message = self._message()
        with patch.object(service.email_sender, "send", return_value=(False, "smtp down")):
            success, error = service.send_notification(message)
        assert success is False
        assert error == "smtp down"
        assert message.status == NotificationStatus.FAILED
        assert message.error_message == "smtp down"
        assert service.queue.get_stats()["total_failed"] == 1


class TestQueueForRecipient:
    """测试入队过滤（service.py 763-791）"""

    def test_skips_when_cannot_receive(self):
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()
        recipient = NotificationRecipient(
            user_id=1,
            email="x@y.com",
            channels=[NotificationChannel.EMAIL],
            min_level=NotificationLevel.CRITICAL,
        )
        service.add_recipient(recipient)

        alert_data = {
            "id": "a",
            "alert_type": "x",
            "level": "info",
            "message": "m",
            "title": "t",
        }
        service.queue_notification(alert_data, channels=[NotificationChannel.EMAIL])
        assert service.queue.size() == 0

    def test_queue_for_recipient_multiple_channels(self):
        """多渠道都能接收时应循环入队（service.py 775->771）"""
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()
        recipient = NotificationRecipient(
            user_id=1,
            email="x@y.com",
            phone="13800138000",
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
        )
        alert_data = {
            "id": "a",
            "alert_type": "x",
            "level": "warning",
            "message": "m",
            "title": "t",
        }
        service._queue_for_recipient(
            recipient,
            [NotificationChannel.EMAIL, NotificationChannel.SMS],
            NotificationLevel.WARNING,
            alert_data,
        )
        assert service.queue.size() == 2

    def test_queue_for_recipient_skips_when_message_none(self, monkeypatch):
        """create_notification 返回 None 时应跳过入队（service.py 775->771 防御分支）"""
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationRecipient,
            NotificationService,
        )

        service = NotificationService()
        recipient = NotificationRecipient(
            user_id=1,
            email="x@y.com",
            phone="13800138000",
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
        )
        original = service.create_notification

        def fake_create(alert_data, channel, recipient):
            if channel == NotificationChannel.EMAIL:
                return None
            return original(alert_data, channel, recipient)

        monkeypatch.setattr(service, "create_notification", fake_create)
        alert_data = {
            "id": "a",
            "alert_type": "x",
            "level": "warning",
            "message": "m",
            "title": "t",
        }
        service._queue_for_recipient(
            recipient,
            [NotificationChannel.EMAIL, NotificationChannel.SMS],
            NotificationLevel.WARNING,
            alert_data,
        )
        assert service.queue.size() == 1


class TestWorkerLoop:
    """测试 worker 循环（service.py 797-820）"""

    @staticmethod
    def _message(retry_count=0):
        from services.notification_service import (
            NotificationChannel,
            NotificationLevel,
            NotificationMessage,
            NotificationRecipient,
        )

        return NotificationMessage(
            id="m",
            alert_id="a",
            channel=NotificationChannel.EMAIL,
            recipient=NotificationRecipient(user_id=1, email="x@y.com"),
            subject="s",
            content="c",
            level=NotificationLevel.WARNING,
            retry_count=retry_count,
        )

    def test_process_pending_message_empty(self):
        from services.notification_service import NotificationService

        service = NotificationService()
        service._process_pending_message()
        assert service.queue.size() == 0

    def test_process_pending_message_retry_on_failure(self):
        from services.notification_service import NotificationService

        service = NotificationService()
        service.queue.enqueue(self._message())
        with patch.object(service, "send_notification", return_value=(False, "err")):
            service._process_pending_message()
        assert service.queue.retry_size() == 1

    def test_process_pending_message_no_retry_when_max_exceeded(self):
        from services.notification_service import (
            NotificationMessage,
            NotificationService,
        )

        service = NotificationService()
        message = self._message(retry_count=3)
        message.max_retries = 3
        service.queue.enqueue(message)
        with patch.object(service, "send_notification", return_value=(False, "err")):
            service._process_pending_message()
        assert service.queue.retry_size() == 0

    def test_process_retry_message_empty(self):
        from services.notification_service import NotificationService

        service = NotificationService()
        service._process_retry_message()  # 无消息，no-op

    def test_process_retry_message_sends(self, monkeypatch):
        from services.notification_service import NotificationService

        service = NotificationService()
        message = self._message(retry_count=1)
        service.queue.enqueue_retry(message)

        monkeypatch.setattr("time.sleep", lambda x: None)
        with patch.object(service, "send_notification", return_value=(True, "")) as mock_send:
            service._process_retry_message()
            mock_send.assert_called_once_with(message)
        assert service.queue.retry_size() == 0


class TestStartStopEdge:
    """测试启停边界（service.py 822-837）"""

    def test_start_when_already_running(self):
        from services.notification_service import NotificationService

        service = NotificationService()
        service.start()
        first_thread = service._worker_thread
        service.start()  # 已运行，应直接返回
        assert service._worker_thread is first_thread
        service.stop()

    def test_stop_without_start(self):
        from services.notification_service import NotificationService

        service = NotificationService()
        service.stop()  # _worker_thread 为 None，不应报错
        assert service._running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
