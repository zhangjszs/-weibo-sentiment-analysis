#!/usr/bin/env python3
"""
Spider 任务调度服务测试
"""

from config.settings import Config
from services import spider_task_service


def test_submit_spider_task_uses_local_backend_when_remote_disabled(monkeypatch):
    monkeypatch.setattr(Config, "SPIDER_SERVICE_ENABLED", False)

    expected = {
        "task_id": "local-1",
        "task_label": "刷新热门微博",
        "crawl_type": "hot",
        "keyword": "",
        "page_num": 3,
        "article_limit": 50,
    }
    monkeypatch.setattr(
        spider_task_service, "_submit_local_task", lambda **_: expected
    )

    result = spider_task_service.submit_spider_task("hot", page_num=3)
    assert result == expected


def test_submit_spider_task_fallbacks_to_local_when_remote_error(monkeypatch):
    monkeypatch.setattr(Config, "SPIDER_SERVICE_ENABLED", True)
    monkeypatch.setattr(Config, "SPIDER_SERVICE_FALLBACK_LOCAL", True)

    def _raise_remote(**kwargs):
        raise RuntimeError("remote down")

    monkeypatch.setattr(spider_task_service, "_submit_remote_task", _raise_remote)
    monkeypatch.setattr(
        spider_task_service,
        "_submit_local_task",
        lambda **_: {
            "task_id": "local-fallback",
            "task_label": "刷新热门微博",
            "crawl_type": "hot",
            "keyword": "",
            "page_num": 3,
            "article_limit": 50,
        },
    )

    result = spider_task_service.submit_spider_task("hot", page_num=3)
    assert result["task_id"] == "local-fallback"


def test_submit_spider_task_raises_when_remote_error_and_no_fallback(monkeypatch):
    monkeypatch.setattr(Config, "SPIDER_SERVICE_ENABLED", True)
    monkeypatch.setattr(Config, "SPIDER_SERVICE_FALLBACK_LOCAL", False)

    def _raise_remote(**kwargs):
        raise RuntimeError("remote down")

    monkeypatch.setattr(spider_task_service, "_submit_remote_task", _raise_remote)

    try:
        spider_task_service.submit_spider_task("hot", page_num=3)
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "remote down" in str(exc)


def test_query_spider_task_progress_selects_backend(monkeypatch):
    monkeypatch.setattr(Config, "SPIDER_SERVICE_ENABLED", False)
    monkeypatch.setattr(
        spider_task_service,
        "_query_local_task",
        lambda task_id: {"task_id": task_id, "state": "SUCCESS"},
    )
    result_local = spider_task_service.query_spider_task_progress("task-a")
    assert result_local["state"] == "SUCCESS"

    monkeypatch.setattr(Config, "SPIDER_SERVICE_ENABLED", True)
    monkeypatch.setattr(
        spider_task_service,
        "_query_remote_task",
        lambda task_id: {"task_id": task_id, "state": "PENDING"},
    )
    result_remote = spider_task_service.query_spider_task_progress("task-b")
    assert result_remote["state"] == "PENDING"


def test_normalize_dispatch_result_accepts_camel_case_fields():
    payload = {
        "taskId": "remote-1",
        "taskLabel": "关键词搜索: AI",
        "type": "search",
        "keyword": "AI",
        "pageNum": 5,
        "articleLimit": 88,
    }

    normalized = spider_task_service._normalize_dispatch_result(
        payload=payload,
        crawl_type="search",
        keyword="AI",
        page_num=3,
        article_limit=50,
    )

    assert normalized["task_id"] == "remote-1"
    assert normalized["task_label"] == "关键词搜索: AI"
    assert normalized["crawl_type"] == "search"
    assert normalized["page_num"] == 5
    assert normalized["article_limit"] == 88
