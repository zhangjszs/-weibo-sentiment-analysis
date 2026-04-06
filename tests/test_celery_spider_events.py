#!/usr/bin/env python3
"""
爬虫任务领域事件测试
"""

from unittest.mock import patch

from services.domain_events import ArticlesUpsertedEvent
from tasks.celery_spider import _notify_articles_upserted_event


def test_notify_articles_upserted_event_publishes_domain_event():
    with patch("tasks.celery_spider.domain_event_bus.publish") as mock_publish:
        _notify_articles_upserted_event(
            task_id="task-123",
            pages=2,
            crawled=18,
            imported=18,
        )

    mock_publish.assert_called_once()
    published_event = mock_publish.call_args.args[0]
    assert isinstance(published_event, ArticlesUpsertedEvent)
    assert published_event.task_id == "task-123"
    assert published_event.pages == 2
    assert published_event.crawled == 18
    assert published_event.imported == 18
