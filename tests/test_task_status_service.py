#!/usr/bin/env python3
"""
统一任务状态查询服务测试
"""

from requests import HTTPError, Response

from config.settings import Config
from services import task_status_service


def _http_error(status_code: int) -> HTTPError:
    response = Response()
    response.status_code = status_code
    response._content = b"{}"
    return HTTPError(response=response)


def test_query_task_progress_uses_spider_remote_first(monkeypatch):
    monkeypatch.setattr(Config, "SPIDER_SERVICE_ENABLED", True)
    monkeypatch.setattr(Config, "NLP_SERVICE_ENABLED", True)
    monkeypatch.setattr(
        task_status_service,
        "query_spider_remote",
        lambda task_id: {"task_id": task_id, "state": "SUCCESS", "source": "spider"},
    )

    def _should_not_call(task_id):
        raise AssertionError("should not call NLP remote when Spider already hit")

    monkeypatch.setattr(task_status_service, "query_nlp_remote", _should_not_call)

    result = task_status_service.query_task_progress("task-spider")
    assert result["source"] == "spider"


def test_query_task_progress_falls_through_to_nlp_remote(monkeypatch):
    monkeypatch.setattr(Config, "SPIDER_SERVICE_ENABLED", True)
    monkeypatch.setattr(Config, "NLP_SERVICE_ENABLED", True)

    def _raise_not_found(task_id):
        raise _http_error(404)

    monkeypatch.setattr(task_status_service, "query_spider_remote", _raise_not_found)
    monkeypatch.setattr(
        task_status_service,
        "query_nlp_remote",
        lambda task_id: {"task_id": task_id, "state": "PENDING", "source": "nlp"},
    )

    result = task_status_service.query_task_progress("task-nlp")
    assert result["source"] == "nlp"


def test_query_task_progress_fallbacks_to_local(monkeypatch):
    monkeypatch.setattr(Config, "SPIDER_SERVICE_ENABLED", True)
    monkeypatch.setattr(Config, "NLP_SERVICE_ENABLED", True)

    def _raise_spider_error(task_id):
        raise RuntimeError("spider down")

    def _raise_nlp_error(task_id):
        raise RuntimeError("nlp down")

    monkeypatch.setattr(
        task_status_service,
        "query_spider_remote",
        _raise_spider_error,
    )
    monkeypatch.setattr(
        task_status_service,
        "query_nlp_remote",
        _raise_nlp_error,
    )
    monkeypatch.setattr(
        task_status_service,
        "_query_local_task",
        lambda task_id: {"task_id": task_id, "state": "SUCCESS", "source": "local"},
    )

    result = task_status_service.query_task_progress("task-local")
    assert result["source"] == "local"


def test_query_task_progress_uses_local_when_remote_disabled(monkeypatch):
    monkeypatch.setattr(Config, "SPIDER_SERVICE_ENABLED", False)
    monkeypatch.setattr(Config, "NLP_SERVICE_ENABLED", False)
    monkeypatch.setattr(
        task_status_service,
        "_query_local_task",
        lambda task_id: {"task_id": task_id, "state": "PENDING", "source": "local"},
    )

    result = task_status_service.query_task_progress("task-any")
    assert result["source"] == "local"
