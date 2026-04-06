#!/usr/bin/env python3
"""
NLP 任务调度服务测试
"""

import pytest

from config.settings import Config
from services import nlp_task_service


def test_analyze_text_uses_local_backend_when_remote_disabled(monkeypatch):
    monkeypatch.setattr(Config, "NLP_SERVICE_ENABLED", False)
    monkeypatch.setattr(
        nlp_task_service,
        "_analyze_local_text",
        lambda text, mode: {"text": text, "mode": mode, "label": "neutral"},
    )

    result = nlp_task_service.analyze_text("测试文本", "simple")
    assert result["mode"] == "simple"
    assert result["label"] == "neutral"


def test_analyze_text_fallbacks_to_local_when_remote_error(monkeypatch):
    monkeypatch.setattr(Config, "NLP_SERVICE_ENABLED", True)
    monkeypatch.setattr(Config, "NLP_SERVICE_FALLBACK_LOCAL", True)

    def _raise_remote(**kwargs):
        raise RuntimeError("remote down")

    monkeypatch.setattr(nlp_task_service, "_analyze_remote_text", _raise_remote)
    monkeypatch.setattr(
        nlp_task_service,
        "_analyze_local_text",
        lambda text, mode: {"text": text, "mode": mode, "label": "positive"},
    )

    result = nlp_task_service.analyze_text("测试文本", "smart")
    assert result["label"] == "positive"


def test_analyze_text_raises_when_remote_error_and_no_fallback(monkeypatch):
    monkeypatch.setattr(Config, "NLP_SERVICE_ENABLED", True)
    monkeypatch.setattr(Config, "NLP_SERVICE_FALLBACK_LOCAL", False)

    def _raise_remote(**kwargs):
        raise RuntimeError("remote down")

    monkeypatch.setattr(nlp_task_service, "_analyze_remote_text", _raise_remote)

    with pytest.raises(RuntimeError, match="remote down"):
        nlp_task_service.analyze_text("测试文本", "smart")


def test_query_nlp_task_progress_selects_backend(monkeypatch):
    monkeypatch.setattr(Config, "NLP_SERVICE_ENABLED", False)
    monkeypatch.setattr(
        nlp_task_service,
        "_query_local_task",
        lambda task_id: {"task_id": task_id, "state": "SUCCESS"},
    )
    result_local = nlp_task_service.query_nlp_task_progress("task-a")
    assert result_local["state"] == "SUCCESS"

    monkeypatch.setattr(Config, "NLP_SERVICE_ENABLED", True)
    monkeypatch.setattr(
        nlp_task_service,
        "_query_remote_task",
        lambda task_id: {"task_id": task_id, "state": "PENDING"},
    )
    result_remote = nlp_task_service.query_nlp_task_progress("task-b")
    assert result_remote["state"] == "PENDING"


def test_query_nlp_task_progress_fallbacks_to_local(monkeypatch):
    monkeypatch.setattr(Config, "NLP_SERVICE_ENABLED", True)
    monkeypatch.setattr(Config, "NLP_SERVICE_FALLBACK_LOCAL", True)

    def _raise_remote(task_id):
        raise RuntimeError("remote down")

    monkeypatch.setattr(nlp_task_service, "_query_remote_task", _raise_remote)
    monkeypatch.setattr(
        nlp_task_service,
        "_query_local_task",
        lambda task_id: {"task_id": task_id, "state": "SUCCESS"},
    )

    result = nlp_task_service.query_nlp_task_progress("task-c")
    assert result["state"] == "SUCCESS"


def test_query_nlp_task_progress_raises_when_no_fallback(monkeypatch):
    monkeypatch.setattr(Config, "NLP_SERVICE_ENABLED", True)
    monkeypatch.setattr(Config, "NLP_SERVICE_FALLBACK_LOCAL", False)

    def _raise_remote(task_id):
        raise RuntimeError("remote down")

    monkeypatch.setattr(nlp_task_service, "_query_remote_task", _raise_remote)

    with pytest.raises(RuntimeError, match="remote down"):
        nlp_task_service.query_nlp_task_progress("task-d")


def test_normalize_task_result_accepts_camel_case_fields():
    payload = {
        "taskId": "remote-1",
        "taskLabel": "情感分析",
        "mode": "smart",
        "status": "PENDING",
    }

    normalized = nlp_task_service._normalize_task_result(payload, "情感分析")

    assert normalized["task_id"] == "remote-1"
    assert normalized["task_label"] == "情感分析"
    assert normalized["mode"] == "smart"
    assert normalized["status"] == "PENDING"
