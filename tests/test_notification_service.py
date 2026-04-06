#!/usr/bin/env python3
"""
预警通知服务单元测试
"""

import sys

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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
