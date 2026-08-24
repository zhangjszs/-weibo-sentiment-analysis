#!/usr/bin/env python3
"""Recipient resolution helpers for notification service."""

import logging
from dataclasses import dataclass, field
from datetime import (
    datetime,  # noqa: F401  # kept for re-export; logic uses dynamic import
)
from enum import Enum
from typing import Any

logger = logging.getLogger("services.notification_service")

LEVEL_ORDER: dict["NotificationLevel", int] = {}


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


LEVEL_ORDER = {
    NotificationLevel.INFO: 0,
    NotificationLevel.WARNING: 1,
    NotificationLevel.DANGER: 2,
    NotificationLevel.CRITICAL: 3,
}


def _parse_level(level_str: str) -> NotificationLevel:
    """Parse a level string into a NotificationLevel, defaulting to WARNING."""
    try:
        return NotificationLevel(level_str)
    except ValueError:
        return NotificationLevel.WARNING


@dataclass
class NotificationRecipient:
    """通知接收人"""

    user_id: int
    email: str | None = None
    phone: str | None = None
    min_level: NotificationLevel = NotificationLevel.INFO
    channels: list[NotificationChannel] = field(default_factory=list)
    quiet_hours: dict[str, str] = field(default_factory=dict)
    enabled: bool = True

    def can_receive(
        self, level: NotificationLevel, channel: NotificationChannel
    ) -> bool:
        """检查是否可以接收通知"""
        if not self.enabled:
            return False
        if LEVEL_ORDER.get(level, 0) < LEVEL_ORDER.get(self.min_level, 0):
            return False
        if channel not in self.channels:
            return False
        if self._in_quiet_hours():
            return False
        return True

    def _in_quiet_hours(self) -> bool:
        """Check whether the current time falls within quiet hours."""
        if not self.quiet_hours:
            return False
        # Use dynamic lookup so tests patching services.notification_service.datetime work
        try:
            import services.notification_service as _ns

            _dt = _ns.datetime  # type: ignore[attr-defined]
        except Exception:
            _dt = datetime
        now_time = _dt.now().strftime("%H:%M")
        start = self.quiet_hours.get("start", "00:00")
        end = self.quiet_hours.get("end", "00:00")
        if start <= end:
            return start <= now_time <= end
        return now_time >= start or now_time <= end


class RecipientResolverMixin:
    """Mixin providing recipient management and channel resolution."""

    # Expected attributes on self: recipients, _lock, _normalize_channels helpers

    def add_recipient(self, recipient: NotificationRecipient):
        """添加接收人"""
        with self._lock:  # type: ignore[attr-defined]
            self.recipients[recipient.user_id] = recipient  # type: ignore[attr-defined]

    def remove_recipient(self, user_id: int):
        """移除接收人"""
        with self._lock:  # type: ignore[attr-defined]
            self.recipients.pop(user_id, None)  # type: ignore[attr-defined]

    def get_recipients(self) -> list[NotificationRecipient]:
        """获取所有接收人"""
        with self._lock:  # type: ignore[attr-defined]
            return list(self.recipients.values())  # type: ignore[attr-defined]

    def _normalize_channels(
        self, channel_values: list[Any] | None
    ) -> list[NotificationChannel]:
        """规范化渠道列表，过滤非法值并去重。"""
        normalized: list[NotificationChannel] = []
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

    def resolve_channels(self, alert_data: dict[str, Any]) -> list[NotificationChannel]:
        """解析预警对应的通知渠道。"""
        channel_values = alert_data.get("notification_channels")
        if not channel_values and alert_data.get("rule_id"):
            channel_values = self._fetch_rule_channels(alert_data["rule_id"])  # type: ignore[attr-defined]
        channels = self._normalize_channels(channel_values)
        return channels or [NotificationChannel.WEBSOCKET]

    def _fetch_rule_channels(self, rule_id: Any) -> list | None:
        """从 DB 按规则 ID 取其通知渠道配置。"""
        try:
            from database import db_session
            from models.alert import AlertRule

            rule = db_session.get(AlertRule, rule_id)
            if rule:
                return getattr(rule, "notification_channels", None)
        except Exception as e:
            logger.debug(f"读取预警规则渠道失败: {e}")
        return None

    # --- Admin recipient sync helpers ---

    def _fetch_admin_users(
        self, admin_usernames: set[str]
    ) -> list[dict[str, Any] | None]:
        """Fetch user records for admin usernames from the repository."""
        from repositories.user_repository import UserRepository

        repo = UserRepository()
        return [
            repo.find_by_username(username)
            for username in sorted(admin_usernames)
        ]

    def _build_recipient(
        self,
        user: dict[str, Any],
        admin_usernames: set[str],
    ) -> NotificationRecipient | None:
        """Build a NotificationRecipient from a user record, or None if invalid."""
        username = (user.get("username") or "").strip()
        if username not in admin_usernames:
            return None
        user_id = user.get("id")
        if user_id is None:
            return None
        existing = self.recipients.get(user_id)  # type: ignore[attr-defined]
        channels = self._build_admin_channels(user, existing)  # type: ignore[attr-defined]
        return NotificationRecipient(
            user_id=user_id,
            email=user.get("email") or (existing.email if existing else None),
            phone=existing.phone if existing else None,
            min_level=existing.min_level if existing else NotificationLevel.INFO,
            channels=channels,
            quiet_hours=existing.quiet_hours if existing else {},
            enabled=existing.enabled if existing else True,
        )

    def _build_admin_channels(
        self,
        user: dict[str, Any],
        existing: NotificationRecipient | None,
    ) -> list[NotificationChannel]:
        """Build the channel list for an admin user, merging with existing."""
        channels = self._normalize_channels(
            list(existing.channels) if existing else []
        )
        for channel in [NotificationChannel.WEBSOCKET, NotificationChannel.EMAIL]:
            if channel == NotificationChannel.EMAIL and not user.get("email"):
                continue
            if channel not in channels:
                channels.append(channel)
        return channels

    def _merge_recipients(
        self,
        user_records: list[dict[str, Any] | None],
        admin_usernames: set[str],
    ) -> int:
        """Merge admin user records into self.recipients under lock. Returns count."""
        synced = 0
        with self._lock:  # type: ignore[attr-defined]
            for user in user_records:
                if not user:
                    continue
                recipient = self._build_recipient(user, admin_usernames)  # type: ignore[attr-defined]
                if recipient is None:
                    continue
                self.recipients[recipient.user_id] = recipient  # type: ignore[attr-defined]
                synced += 1
        return synced

    def sync_admin_recipients(
        self,
        user_records: list[dict[str, Any]] | None = None,
        admin_usernames: set[str] | None = None,
    ) -> int:
        """同步管理员为默认通知接收人。"""
        if admin_usernames is None:
            from config.settings import Config

            admin_usernames = set(Config.ADMIN_USERS)
        if not admin_usernames:
            return 0
        if user_records is None:
            user_records = self._fetch_admin_users(admin_usernames)  # type: ignore[attr-defined]
        return self._merge_recipients(user_records, admin_usernames)  # type: ignore[attr-defined]
