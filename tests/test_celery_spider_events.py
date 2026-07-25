#!/usr/bin/env python3
"""
爬虫任务文章入库副作用测试。

原 test 断言领域事件总线 publish 被调用——那是实现细节。P2 简化后，
行为契约是：文章批量写入后清空缓存。本测试直接验证 clear_all_cache 被调用。
"""

from unittest.mock import patch

from tasks.celery_spider import _notify_articles_upserted_event


def test_notify_articles_upserted_event_clears_cache():
    with patch("utils.cache.clear_all_cache") as mock_clear:
        _notify_articles_upserted_event(
            task_id="task-123",
            pages=2,
            crawled=18,
            imported=18,
        )

    mock_clear.assert_called_once()
