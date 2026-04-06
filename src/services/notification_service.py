#!/usr/bin/env python3
"""
预警通知服务模块
功能：邮件通知、短信通知、WebSocket推送、通知队列、失败重试
"""

import logging
import smtplib
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """通知渠道"""

    EMAIL = "email"
    SMS = "sms"
    WEBSOCKET = "websocket"


class NotificationStatus(Enum):
    """通知状态"""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationLevel(Enum):
    """通知级别"""

    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"


@dataclass
class NotificationRecipient:
    """通知接收人"""

    user_id: int
    email: Optional[str] = None
    phone: Optional[str] = None
    min_level: NotificationLevel = NotificationLevel.INFO
    channels: List[NotificationChannel] = field(default_factory=list)
    quiet_hours: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True

    def can_receive(
        self, level: NotificationLevel, channel: NotificationChannel
    ) -> bool:
        """检查是否可以接收通知"""
        if not self.enabled:
            return False

        level_order = {
            NotificationLevel.INFO: 0,
            NotificationLevel.WARNING: 1,
            NotificationLevel.DANGER: 2,
            NotificationLevel.CRITICAL: 3,
        }

        if level_order.get(level, 0) < level_order.get(self.min_level, 0):
            return False

        if channel not in self.channels:
            return False

        if self.quiet_hours:
            now = datetime.now()
            start = self.quiet_hours.get("start", "00:00")
            end = self.quiet_hours.get("end", "00:00")
            current_time = now.strftime("%H:%M")

            if start <= end:
                if start <= current_time <= end:
                    return False
            else:
                if current_time >= start or current_time <= end:
                    return False

        return True


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
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
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

    def render(self, context: Dict[str, Any]) -> tuple:
        """渲染模板"""
        subject = self.subject_template.format(**context)
        content = self.content_template.format(**context)
        sms = self.sms_template.format(**context) if self.sms_template else ""
        return subject, content, sms


class EmailSender:
    """邮件发送服务"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.smtp_host = self.config.get("smtp_host", "smtp.example.com")
        self.smtp_port = self.config.get("smtp_port", 465)
        self.smtp_user = self.config.get("smtp_user", "")
        self.smtp_password = self.config.get("smtp_password", "")
        self.from_email = self.config.get("from_email", "noreply@example.com")
        self.from_name = self.config.get("from_name", "舆情监测系统")
        self.use_ssl = self.config.get("use_ssl", True)

    def send(
        self, to_email: str, subject: str, content: str, html: bool = True
    ) -> tuple:
        """发送邮件"""
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

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False, str(e)


class SMSSender:
    """短信发送服务（模拟实现）"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.access_key = self.config.get("access_key", "")
        self.secret_key = self.config.get("secret_key", "")
        self.sign_name = self.config.get("sign_name", "舆情监测")
        self.template_code = self.config.get("template_code", "")

    def send(self, phone: str, content: str, template_params: Dict = None) -> tuple:
        """发送短信"""
        try:
            logger.info(f"[模拟] 短信发送成功: {phone} - {content[:50]}...")
            return True, "发送成功"

        except Exception as e:
            logger.error(f"短信发送失败: {e}")
            return False, str(e)

    def send_batch(self, phones: List[str], content: str) -> Dict[str, tuple]:
        """批量发送短信"""
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
        """入队"""
        with self._lock:
            if len(self._queue) >= self.max_size:
                logger.warning("通知队列已满")
                return False
            self._queue.append(message)
            self._stats["total_queued"] += 1
            return True

    def dequeue(self) -> Optional[NotificationMessage]:
        """出队"""
        with self._lock:
            if self._queue:
                return self._queue.popleft()
            return None

    def enqueue_retry(self, message: NotificationMessage) -> bool:
        """加入重试队列"""
        with self._lock:
            if len(self._retry_queue) >= self.max_size:
                return False
            message.status = NotificationStatus.RETRYING
            self._retry_queue.append(message)
            self._stats["total_retries"] += 1
            return True

    def get_retry_message(self) -> Optional[NotificationMessage]:
        """获取重试消息"""
        with self._lock:
            if self._retry_queue:
                return self._retry_queue.popleft()
            return None

    def size(self) -> int:
        """队列大小"""
        with self._lock:
            return len(self._queue)

    def retry_size(self) -> int:
        """重试队列大小"""
        with self._lock:
            return len(self._retry_queue)

    def get_stats(self) -> Dict:
        """获取统计"""
        with self._lock:
            return {
                **self._stats,
                "queue_size": len(self._queue),
                "retry_queue_size": len(self._retry_queue),
            }


class NotificationService:
    """通知服务"""

    def __init__(self, email_config: Dict = None, sms_config: Dict = None):
        self.email_sender = EmailSender(email_config or {})
        self.sms_sender = SMSSender(sms_config or {})
        self.queue = NotificationQueue()
        self.templates: Dict[str, NotificationTemplate] = {}
        self.recipients: Dict[int, NotificationRecipient] = {}
        self._lock = threading.Lock()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[NotificationMessage], None]] = []
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
                content_template="""
尊敬的用户：

您好！系统检测到负面舆情激增：

预警级别：{level}
触发时间：{trigger_time}
预警内容：{message}

相关数据：
- 负面评论数：{negative_count}
- 总评论数：{total_count}
- 负面比例：{negative_ratio:.1%}

建议措施：
1. 密切关注舆情发展
2. 及时回应公众关切
3. 做好危机公关准备

此致
舆情监测系统
{system_time}
""",
                sms_template="【舆情预警】负面舆情激增：{message}。详情请登录系统查看。",
            ),
            NotificationTemplate(
                name="情感突变",
                alert_type="sentiment_shift",
                channel=NotificationChannel.EMAIL,
                subject_template="【舆情预警】情感倾向突变 - {level}",
                content_template="""
尊敬的用户：

您好！系统检测到情感倾向发生突变：

预警级别：{level}
触发时间：{trigger_time}
变化方向：{direction}
变化幅度：{magnitude:.2f}

当前情感指数：{current_sentiment:.2f}
变化前情感指数：{previous_sentiment:.2f}

请及时关注舆情变化。

此致
舆情监测系统
{system_time}
""",
                sms_template="【舆情预警】情感突变：{direction}{magnitude:.2f}。请关注。",
            ),
            NotificationTemplate(
                name="热点话题",
                alert_type="hot_topic",
                channel=NotificationChannel.EMAIL,
                subject_template="【舆情预警】热点话题出现 - {topic_name}",
                content_template="""
尊敬的用户：

您好！系统检测到热点话题：

话题名称：{topic_name}
提及次数：{mention_count}
时间窗口：{time_window}分钟

请及时关注相关讨论。

此致
舆情监测系统
{system_time}
""",
                sms_template="【舆情预警】热点话题：{topic_name}，提及{mention_count}次。",
            ),
        ]

        for template in default_templates:
            self.templates[template.alert_type] = template

        logger.info(f"已加载 {len(self.templates)} 个通知模板")

    def add_recipient(self, recipient: NotificationRecipient):
        """添加接收人"""
        with self._lock:
            self.recipients[recipient.user_id] = recipient

    def remove_recipient(self, user_id: int):
        """移除接收人"""
        with self._lock:
            self.recipients.pop(user_id, None)

    def get_recipients(self) -> List[NotificationRecipient]:
        """获取所有接收人"""
        with self._lock:
            return list(self.recipients.values())

    def _normalize_channels(
        self, channel_values: Optional[List[Any]]
    ) -> List[NotificationChannel]:
        """规范化渠道列表，过滤非法值并去重。"""
        normalized: List[NotificationChannel] = []

        for value in channel_values or []:
            try:
                channel = (
                    value
                    if isinstance(value, NotificationChannel)
                    else NotificationChannel(str(value))
                )
            except ValueError:
                continue

            if channel not in normalized:
                normalized.append(channel)

        return normalized

    def resolve_channels(self, alert_data: Dict[str, Any]) -> List[NotificationChannel]:
        """解析预警对应的通知渠道。"""
        channel_values = alert_data.get("notification_channels")

        if not channel_values and alert_data.get("rule_id"):
            try:
                from services.alert_service import alert_engine

                rule = alert_engine.rules.get(alert_data.get("rule_id"))
                if rule:
                    channel_values = getattr(rule, "notification_channels", None)
            except Exception as e:
                logger.debug(f"读取预警规则渠道失败: {e}")

        channels = self._normalize_channels(channel_values)
        return channels or [NotificationChannel.WEBSOCKET]

    def sync_admin_recipients(
        self,
        user_records: Optional[List[Dict[str, Any]]] = None,
        admin_usernames: Optional[set[str]] = None,
    ) -> int:
        """同步管理员为默认通知接收人。"""
        if admin_usernames is None:
            from config.settings import Config

            admin_usernames = set(Config.ADMIN_USERS)

        if not admin_usernames:
            return 0

        if user_records is None:
            from repositories.user_repository import UserRepository

            repo = UserRepository()
            user_records = [
                repo.find_by_username(username)
                for username in sorted(admin_usernames)
            ]

        synced = 0
        with self._lock:
            for user in user_records:
                if not user:
                    continue

                username = (user.get("username") or "").strip()
                if username not in admin_usernames:
                    continue

                user_id = user.get("id")
                if user_id is None:
                    continue

                existing = self.recipients.get(user_id)
                channels = self._normalize_channels(
                    list(existing.channels) if existing else []
                )
                for channel in [NotificationChannel.WEBSOCKET, NotificationChannel.EMAIL]:
                    if channel == NotificationChannel.EMAIL and not user.get("email"):
                        continue
                    if channel not in channels:
                        channels.append(channel)

                self.recipients[user_id] = NotificationRecipient(
                    user_id=user_id,
                    email=user.get("email") or (existing.email if existing else None),
                    phone=existing.phone if existing else None,
                    min_level=existing.min_level if existing else NotificationLevel.INFO,
                    channels=channels,
                    quiet_hours=existing.quiet_hours if existing else {},
                    enabled=existing.enabled if existing else True,
                )
                synced += 1

        return synced

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
            except Exception as e:
                logger.error(f"回调执行失败: {e}")

    def create_notification(
        self,
        alert_data: Dict,
        channel: NotificationChannel,
        recipient: NotificationRecipient,
    ) -> Optional[NotificationMessage]:
        """创建通知消息"""
        alert_type = alert_data.get("alert_type", "custom")
        template = self.templates.get(alert_type)

        if not template:
            subject = f"【舆情预警】{alert_data.get('title', '未知预警')}"
            content = alert_data.get("message", "")
            sms_content = content[:70]
        else:
            alert_context = (
                alert_data.get("data", {})
                if isinstance(alert_data.get("data"), dict)
                else {}
            )
            context = {
                "level": alert_data.get("level", "warning"),
                "trigger_time": alert_data.get(
                    "created_at", datetime.now().isoformat()
                ),
                "message": alert_data.get("message", ""),
                "system_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                **alert_context,
                **alert_data,
            }
            subject, content, sms_content = template.render(context)

        level_str = alert_data.get("level", "warning")
        level = (
            NotificationLevel(level_str)
            if level_str in [e.value for e in NotificationLevel]
            else NotificationLevel.WARNING
        )

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

    def send_notification(self, message: NotificationMessage) -> tuple:
        """发送通知"""
        success = False
        error_msg = ""

        if message.channel == NotificationChannel.EMAIL:
            if message.recipient.email:
                success, error_msg = self.email_sender.send(
                    message.recipient.email, message.subject, message.content
                )
            else:
                error_msg = "接收人邮箱为空"

        elif message.channel == NotificationChannel.SMS:
            if message.recipient.phone:
                success, error_msg = self.sms_sender.send(
                    message.recipient.phone, message.content
                )
            else:
                error_msg = "接收人手机号为空"

        elif message.channel == NotificationChannel.WEBSOCKET:
            try:
                from services.websocket_service import websocket_service

                if websocket_service.socketio:
                    websocket_service.send_to_user(
                        str(message.recipient.user_id),
                        websocket_service.create_message(
                            websocket_service.MessageType.NOTIFICATION,
                            title=message.subject,
                            content=message.content,
                            level=message.level.value,
                        ),
                    )
                    success = True
                else:
                    error_msg = "WebSocket服务未初始化"
            except Exception as e:
                error_msg = str(e)

        if success:
            message.status = NotificationStatus.SENT
            message.sent_at = datetime.now()
            self.queue._stats["total_sent"] += 1
        else:
            message.status = NotificationStatus.FAILED
            message.error_message = error_msg
            self.queue._stats["total_failed"] += 1

        self._trigger_callbacks(message)
        return success, error_msg

    def queue_notification(
        self, alert_data: Dict, channels: List[NotificationChannel] = None
    ):
        """将通知加入队列"""
        if channels is None:
            channels = [NotificationChannel.EMAIL, NotificationChannel.SMS]

        level_str = alert_data.get("level", "warning")
        level = (
            NotificationLevel(level_str)
            if level_str in [e.value for e in NotificationLevel]
            else NotificationLevel.WARNING
        )

        with self._lock:
            recipients = list(self.recipients.values())

        for recipient in recipients:
            for channel in channels:
                if not recipient.can_receive(level, channel):
                    continue

                message = self.create_notification(alert_data, channel, recipient)
                if message:
                    self.queue.enqueue(message)

    def _process_queue(self):
        """处理队列"""
        while self._running:
            message = self.queue.dequeue()
            if message:
                success, error = self.send_notification(message)

                if not success and message.retry_count < message.max_retries:
                    message.retry_count += 1
                    self.queue.enqueue_retry(message)

            retry_message = self.queue.get_retry_message()
            if retry_message:
                time.sleep(2**retry_message.retry_count)
                self.send_notification(retry_message)

            time.sleep(0.1)

    def start(self):
        """启动服务"""
        if self._running:
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        logger.info("通知服务已启动")

    def stop(self):
        """停止服务"""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        logger.info("通知服务已停止")

    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            "queue_stats": self.queue.get_stats(),
            "recipient_count": len(self.recipients),
            "template_count": len(self.templates),
            "running": self._running,
        }


notification_service = NotificationService()


__all__ = [
    "NotificationChannel",
    "NotificationStatus",
    "NotificationLevel",
    "NotificationRecipient",
    "NotificationMessage",
    "NotificationTemplate",
    "EmailSender",
    "SMSSender",
    "NotificationQueue",
    "NotificationService",
    "notification_service",
]
