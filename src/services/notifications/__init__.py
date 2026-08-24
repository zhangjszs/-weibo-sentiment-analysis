#!/usr/bin/env python3
"""Notifications package - re-exports for backward compatibility."""

from .channels import (
    EmailSender,
    NotificationMessage,
    NotificationQueue,
    NotificationTemplate,
    SMSSender,
)
from .recipient_resolver import (
    LEVEL_ORDER,
    NotificationChannel,
    NotificationLevel,
    NotificationRecipient,
    NotificationStatus,
    _parse_level,
)
from .service import NotificationService, notification_service

__all__ = [
    "NotificationChannel",
    "NotificationStatus",
    "NotificationLevel",
    "LEVEL_ORDER",
    "_parse_level",
    "NotificationRecipient",
    "NotificationMessage",
    "NotificationTemplate",
    "EmailSender",
    "SMSSender",
    "NotificationQueue",
    "NotificationService",
    "notification_service",
]
