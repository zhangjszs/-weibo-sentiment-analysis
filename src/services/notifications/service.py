#!/usr/bin/env python3
"""Main NotificationService orchestration."""

import logging
import threading
import time
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from .channels import (
    ChannelMixin,
    EmailSender,
    NotificationMessage,
    NotificationQueue,
    NotificationTemplate,
    SMSSender,
)
from .recipient_resolver import (
    NotificationChannel,
    NotificationLevel,
    NotificationRecipient,
    RecipientResolverMixin,
    _parse_level,
)

logger = logging.getLogger("services.notification_service")


class NotificationService(RecipientResolverMixin, ChannelMixin):
    """通知服务"""

    def __init__(self, email_config: dict = None, sms_config: dict = None):
        self.email_sender = EmailSender(email_config or {})
        self.sms_sender = SMSSender(sms_config or {})
        self.queue = NotificationQueue()
        self.templates: dict[str, NotificationTemplate] = {}
        self.recipients: dict[int, NotificationRecipient] = {}
        self._lock = threading.Lock()
        self._running = False
        self._worker_thread: threading.Thread | None = None
        self._callbacks: list[Callable[[NotificationMessage], None]] = []
        self._alert_bridge_registered = False
        self._init_default_templates()

    def _init_default_templates(self):
        """初始化默认模板"""
        default_templates = [
            NotificationTemplate(
                name="负面舆情激增",
                alert_type="negative_surge",
                channel=NotificationChannel.EMAIL,
                subject_template="【舆情预警】负面舆情激增 - {level}",
                content_template="尊敬的用户：\n预警级别：{level}\n触发时间：{trigger_time}\n预警内容：{message}\n负面评论数：{negative_count}\n总评论数：{total_count}\n负面比例：{negative_ratio:.1%}\n此致 舆情监测系统 {system_time}",
                sms_template="【舆情预警】负面舆情激增：{message}。详情请登录系统查看。",
            ),
            NotificationTemplate(
                name="情感突变",
                alert_type="sentiment_shift",
                channel=NotificationChannel.EMAIL,
                subject_template="【舆情预警】情感倾向突变 - {level}",
                content_template="尊敬的用户：\n预警级别：{level}\n触发时间：{trigger_time}\n变化方向：{direction}\n变化幅度：{magnitude:.2f}\n当前情感指数：{current_sentiment:.2f}\n变化前：{previous_sentiment:.2f}\n此致 舆情监测系统 {system_time}",
                sms_template="【舆情预警】情感突变：{direction}{magnitude:.2f}。请关注。",
            ),
            NotificationTemplate(
                name="热点话题",
                alert_type="hot_topic",
                channel=NotificationChannel.EMAIL,
                subject_template="【舆情预警】热点话题出现 - {topic_name}",
                content_template="尊敬的用户：\n话题名称：{topic_name}\n提及次数：{mention_count}\n时间窗口：{time_window}分钟\n此致 舆情监测系统 {system_time}",
                sms_template="【舆情预警】热点话题：{topic_name}，提及{mention_count}次。",
            ),
        ]
        for template in default_templates:
            self.templates[template.alert_type] = template
        logger.info(f"已加载 {len(self.templates)} 个通知模板")

    def handle_alert(self, alert: Any):
        """处理预警事件并按规则渠道入队通知。"""
        alert_data = alert.to_dict() if hasattr(alert, "to_dict") else dict(alert or {})
        self.queue_notification(alert_data, channels=self.resolve_channels(alert_data))

    def bind_alert_engine(self, alert_engine) -> bool:
        """将通知服务挂接到预警引擎，避免重复注册。"""
        if self._alert_bridge_registered:
            return False
        alert_engine.register_callback(self.handle_alert)
        self._alert_bridge_registered = True
        return True

    def register_callback(self, callback: Callable[[NotificationMessage], None]):
        """注册回调"""
        self._callbacks.append(callback)

    def _trigger_callbacks(self, message: NotificationMessage):
        """触发回调"""
        for callback in self._callbacks:
            try:
                callback(message)
            except (TypeError, ValueError, RuntimeError) as e:
                logger.error(f"回调执行失败: {e}")

    def create_notification(
        self,
        alert_data: dict,
        channel: NotificationChannel,
        recipient: NotificationRecipient,
    ) -> NotificationMessage | None:
        """创建通知消息"""
        alert_type = alert_data.get("alert_type", "custom")
        template = self.templates.get(alert_type)
        if not template:
            subject = f"【舆情预警】{alert_data.get('title', '未知预警')}"
            content = alert_data.get("message", "")
            sms_content = content[:70]
        else:
            subject, content, sms_content = self._render_template(template, alert_data)
        level = _parse_level(alert_data.get("level", "warning"))
        message = NotificationMessage(
            id=str(uuid.uuid4()),
            alert_id=alert_data.get("id", ""),
            channel=channel,
            recipient=recipient,
            subject=subject,
            content=content if channel == NotificationChannel.EMAIL else sms_content,
            level=level,
            metadata={"alert_data": alert_data},
        )
        return message

    def _render_template(
        self, template: NotificationTemplate, alert_data: dict
    ) -> tuple:
        """Render a template against alert data."""
        alert_context = (
            alert_data.get("data", {})
            if isinstance(alert_data.get("data"), dict)
            else {}
        )
        context = {
            "level": alert_data.get("level", "warning"),
            "trigger_time": alert_data.get("created_at", datetime.now().isoformat()),
            "message": alert_data.get("message", ""),
            "system_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **alert_context,
            **alert_data,
        }
        return template.render(context)

    def _resolve_alert_level(self, alert_data: dict) -> NotificationLevel:
        return _parse_level(alert_data.get("level", "warning"))

    def _queue_for_recipient(
        self,
        recipient: NotificationRecipient,
        channels: list[NotificationChannel],
        level: NotificationLevel,
        alert_data: dict,
    ) -> None:
        for channel in channels:
            if not recipient.can_receive(level, channel):
                continue
            message = self.create_notification(alert_data, channel, recipient)
            if message:
                self.queue.enqueue(message)

    def queue_notification(
        self, alert_data: dict, channels: list[NotificationChannel] = None
    ):
        if channels is None:
            channels = [NotificationChannel.EMAIL, NotificationChannel.SMS]
        level = self._resolve_alert_level(alert_data)
        with self._lock:
            recipients = list(self.recipients.values())
        for recipient in recipients:
            self._queue_for_recipient(recipient, channels, level, alert_data)

    def _process_queue(self):
        while self._running:
            self._process_pending_message()
            self._process_retry_message()
            time.sleep(0.1)

    def _process_pending_message(self) -> None:
        message = self.queue.dequeue()
        if not message:
            return
        success, _error = self.send_notification(message)
        if not success and message.retry_count < message.max_retries:
            message.retry_count += 1
            self.queue.enqueue_retry(message)

    def _process_retry_message(self) -> None:
        retry_message = self.queue.get_retry_message()
        if not retry_message:
            return
        time.sleep(2**retry_message.retry_count)
        self.send_notification(retry_message)

    def start(self):
        if self._running:
            return
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        logger.info("通知服务已启动")

    def stop(self):
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        logger.info("通知服务已停止")

    def get_stats(self) -> dict:
        return {
            "queue_stats": self.queue.get_stats(),
            "recipient_count": len(self.recipients),
            "template_count": len(self.templates),
            "running": self._running,
        }


notification_service = NotificationService()
__all__ = ["NotificationService", "notification_service"]
