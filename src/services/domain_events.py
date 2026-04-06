#!/usr/bin/env python3
"""
领域事件总线
用于在服务内解耦业务动作与副作用处理。
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DomainEvent:
    """领域事件基类"""

    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class ArticlesUpsertedEvent(DomainEvent):
    """文章批量写入后事件"""

    task_id: str = ""
    pages: int = 0
    crawled: int = 0
    imported: int = 0


EventType = TypeVar("EventType", bound=DomainEvent)
EventHandler = Callable[[DomainEvent], None]


class DomainEventBus:
    """线程安全的进程内事件总线"""

    def __init__(self):
        self._subscribers: dict[type[DomainEvent], list[EventHandler]] = {}
        self._lock = threading.Lock()

    def subscribe(
        self, event_type: type[EventType], handler: Callable[[EventType], None]
    ) -> None:
        with self._lock:
            handlers = self._subscribers.setdefault(event_type, [])
            if handler not in handlers:
                handlers.append(handler)  # type: ignore[arg-type]

    def publish(self, event: DomainEvent) -> None:
        handlers: list[EventHandler] = []
        with self._lock:
            for event_type, subscribed_handlers in self._subscribers.items():
                if isinstance(event, event_type):
                    handlers.extend(subscribed_handlers)

        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "领域事件处理失败",
                    extra={
                        "event_type": event.__class__.__name__,
                        "handler": getattr(handler, "__name__", repr(handler)),
                    },
                )


def clear_cache_on_articles_upserted(event: ArticlesUpsertedEvent) -> None:
    """文章入库后清理缓存（副作用处理）"""
    from utils.cache import clear_all_cache

    clear_all_cache()
    logger.info(
        "文章入库后已触发缓存清理",
        extra={
            "task_id": event.task_id,
            "pages": event.pages,
            "crawled": event.crawled,
            "imported": event.imported,
        },
    )


domain_event_bus = DomainEventBus()
domain_event_bus.subscribe(ArticlesUpsertedEvent, clear_cache_on_articles_upserted)


__all__ = [
    "DomainEvent",
    "ArticlesUpsertedEvent",
    "DomainEventBus",
    "domain_event_bus",
]
