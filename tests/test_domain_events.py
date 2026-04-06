#!/usr/bin/env python3
"""
领域事件总线测试
"""

from dataclasses import dataclass
from unittest.mock import patch

from services.domain_events import (
    ArticlesUpsertedEvent,
    DomainEvent,
    DomainEventBus,
    domain_event_bus,
)


@dataclass(frozen=True)
class SampleEvent(DomainEvent):
    value: int = 0


def test_event_bus_dispatches_registered_handlers():
    bus = DomainEventBus()
    received = []

    def handler(event: SampleEvent):
        received.append(event.value)

    bus.subscribe(SampleEvent, handler)
    bus.publish(SampleEvent(value=7))

    assert received == [7]


def test_event_bus_continues_when_handler_fails():
    bus = DomainEventBus()
    received = []

    def failing_handler(_: SampleEvent):
        raise RuntimeError("boom")

    def normal_handler(event: SampleEvent):
        received.append(event.value)

    bus.subscribe(SampleEvent, failing_handler)
    bus.subscribe(SampleEvent, normal_handler)
    bus.publish(SampleEvent(value=3))

    assert received == [3]


def test_articles_upserted_event_triggers_cache_clear():
    with patch("utils.cache.clear_all_cache") as mock_clear:
        domain_event_bus.publish(
            ArticlesUpsertedEvent(
                task_id="task-1",
                pages=3,
                crawled=20,
                imported=20,
            )
        )

    mock_clear.assert_called_once()
