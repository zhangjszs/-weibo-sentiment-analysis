#!/usr/bin/env python3
"""Channel senders, queue and message models."""

import logging
import smtplib
import threading
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from .recipient_resolver import (
    NotificationChannel,
    NotificationLevel,
    NotificationRecipient,
    NotificationStatus,
)

logger = logging.getLogger("services.notification_service")


@dataclass
class NotificationMessage:
    """通知消息"""

    id: str
    alert_id: str
    channel: NotificationChannel
    recipient: NotificationRecipient
    subject: str
    content: str
    level: NotificationLevel
    status: NotificationStatus = NotificationStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    error_message: str | None = None
    sent_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "channel": self.channel.value,
            "recipient_user_id": self.recipient.user_id,
            "subject": self.subject,
            "content": self.content,
            "level": self.level.value,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class NotificationTemplate:
    """通知模板"""

    name: str
    alert_type: str
    channel: NotificationChannel
    subject_template: str
    content_template: str
    sms_template: str = ""
    enabled: bool = True

    def render(self, context: dict[str, Any]) -> tuple:
        subject = self.subject_template.format(**context)
        content = self.content_template.format(**context)
        sms = self.sms_template.format(**context) if self.sms_template else ""
        return subject, content, sms


class EmailSender:
    """邮件发送服务"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.smtp_host = self.config.get("smtp_host", "smtp.example.com")
        self.smtp_port = self.config.get("smtp_port", 465)
        self.smtp_user = self.config.get("smtp_user", "")
        self.smtp_password = self.config.get("smtp_password", "")
        self.from_email = self.config.get("from_email", "noreply@example.com")
        self.from_name = self.config.get("from_name", "舆情监测系统")
        self.use_ssl = self.config.get("use_ssl", True)

    def send(self, to_email: str, subject: str, content: str, html: bool = True) -> tuple:
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            if html:
                msg.attach(MIMEText(content, "html", "utf-8"))
            else:
                msg.attach(MIMEText(content, "plain", "utf-8"))
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, to_email, msg.as_string())
            server.quit()
            logger.info(f"邮件发送成功: {to_email}")
            return True, "发送成功"
        except smtplib.SMTPException as e:
            logger.error(f"邮件发送失败: {e}")
            return False, str(e)
        except OSError as e:
            logger.error(f"邮件连接失败: {e}")
            return False, str(e)


class SMSSender:
    """短信发送服务（模拟实现）"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.access_key = self.config.get("access_key", "")
        self.secret_key = self.config.get("secret_key", "")
        self.sign_name = self.config.get("sign_name", "舆情监测")
        self.template_code = self.config.get("template_code", "")

    def send(self, phone: str, content: str, template_params: dict = None) -> tuple:
        try:
            logging.getLogger("services.notification_service").info(
                f"[模拟] 短信发送成功: {phone} - {content[:50]}..."
            )
            return True, "发送成功"
        except ConnectionError as e:
            logger.error(f"短信发送失败: {e}")
            return False, str(e)

    def send_batch(self, phones: list[str], content: str) -> dict[str, tuple]:
        results = {}
        for phone in phones:
            results[phone] = self.send(phone, content)
        return results


class NotificationQueue:
    """通知队列服务"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queue: deque = deque(maxlen=max_size)
        self._retry_queue: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._stats = {
            "total_queued": 0,
            "total_sent": 0,
            "total_failed": 0,
            "total_retries": 0,
        }

    def enqueue(self, message: NotificationMessage) -> bool:
        with self._lock:
            if len(self._queue) >= self.max_size:
                logger.warning("通知队列已满")
                return False
            self._queue.append(message)
            self._stats["total_queued"] += 1
            return True

    def dequeue(self) -> NotificationMessage | None:
        with self._lock:
            if self._queue:
                return self._queue.popleft()
            return None

    def enqueue_retry(self, message: NotificationMessage) -> bool:
        with self._lock:
            if len(self._retry_queue) >= self.max_size:
                return False
            message.status = NotificationStatus.RETRYING
            self._retry_queue.append(message)
            self._stats["total_retries"] += 1
            return True

    def get_retry_message(self) -> NotificationMessage | None:
        with self._lock:
            if self._retry_queue:
                return self._retry_queue.popleft()
            return None

    def size(self) -> int:
        with self._lock:
            return len(self._queue)

    def retry_size(self) -> int:
        with self._lock:
            return len(self._retry_queue)

    def get_stats(self) -> dict:
        with self._lock:
            return {
                **self._stats,
                "queue_size": len(self._queue),
                "retry_queue_size": len(self._retry_queue),
            }

    def mark_sent(self) -> None:
        with self._lock:
            self._stats["total_sent"] += 1

    def mark_failed(self) -> None:
        with self._lock:
            self._stats["total_failed"] += 1


class ChannelMixin:
    """Mixin providing channel-specific send helpers."""

    def _send_email(self, message: NotificationMessage) -> tuple:
        if not message.recipient.email:
            return False, "接收人邮箱为空"
        return self.email_sender.send(  # type: ignore[attr-defined]
            message.recipient.email, message.subject, message.content
        )

    def _send_sms(self, message: NotificationMessage) -> tuple:
        if not message.recipient.phone:
            return False, "接收人手机号为空"
        return self.sms_sender.send(message.recipient.phone, message.content)  # type: ignore[attr-defined]

    def _send_websocket(self, message: NotificationMessage) -> tuple:
        try:
            from services.websocket_service import websocket_service

            if not websocket_service.socketio:
                return False, "WebSocket服务未初始化"
            websocket_service.send_to_user(
                str(message.recipient.user_id),
                websocket_service.create_message(
                    websocket_service.MessageType.NOTIFICATION,
                    title=message.subject,
                    content=message.content,
                    level=message.level.value,
                ),
            )
            return True, ""
        except (ImportError, AttributeError) as e:
            return False, str(e)

    def _get_channel_sender(
        self, channel: NotificationChannel
    ) -> Callable[[NotificationMessage], tuple]:
        sender_map = {
            NotificationChannel.EMAIL: self._send_email,  # type: ignore[attr-defined]
            NotificationChannel.SMS: self._send_sms,  # type: ignore[attr-defined]
            NotificationChannel.WEBSOCKET: self._send_websocket,  # type: ignore[attr-defined]
        }
        return sender_map[channel]

    def send_notification(self, message: NotificationMessage) -> tuple:
        sender = self._get_channel_sender(message.channel)  # type: ignore[attr-defined]
        success, error_msg = sender(message)
        if success:
            message.status = NotificationStatus.SENT
            message.sent_at = datetime.now()
            self.queue.mark_sent()  # type: ignore[attr-defined]
        else:
            message.status = NotificationStatus.FAILED
            message.error_message = error_msg
            self.queue.mark_failed()  # type: ignore[attr-defined]
        self._trigger_callbacks(message)  # type: ignore[attr-defined]
        return success, error_msg
