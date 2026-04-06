#!/usr/bin/env python3
"""
NLP 任务调度服务
支持本地执行与独立 NLP 服务两种后端。
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from celery.result import AsyncResult

from config.settings import Config
from services.sentiment_service import SentimentService
from tasks.celery_config import celery_app

logger = logging.getLogger(__name__)


def _extract_remote_data(payload: Any) -> Any:
    if not isinstance(payload, dict):
        raise ValueError("NLP 服务返回格式无效")
    return payload.get("data", payload)


def _remote_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if Config.NLP_SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {Config.NLP_SERVICE_TOKEN}"
    return headers


def _normalize_task_result(
    payload: dict[str, Any], default_label: str, mode: str = "smart"
) -> dict[str, Any]:
    task_id = payload.get("task_id") or payload.get("taskId")
    if not task_id:
        raise ValueError("NLP 服务未返回 task_id")

    return {
        "task_id": str(task_id),
        "task_label": payload.get("task_label")
        or payload.get("taskLabel")
        or default_label,
        "mode": str(payload.get("mode") or mode),
        "status": payload.get("status") or "PENDING",
    }


def _analyze_remote_text(text: str, mode: str) -> dict[str, Any]:
    response = requests.post(
        f"{Config.NLP_SERVICE_BASE_URL}/api/nlp/analyze",
        json={"text": text, "mode": mode},
        headers=_remote_headers(),
        timeout=Config.NLP_SERVICE_TIMEOUT,
    )
    response.raise_for_status()
    payload = _extract_remote_data(response.json())
    if not isinstance(payload, dict):
        raise ValueError("NLP 分析返回格式无效")
    return payload


def _analyze_local_text(text: str, mode: str) -> dict[str, Any]:
    return SentimentService.analyze(text, mode)


def analyze_text(text: str, mode: str = "custom") -> dict[str, Any]:
    normalized_mode = (mode or "custom").strip()
    if Config.NLP_SERVICE_ENABLED:
        try:
            return _analyze_remote_text(text=text, mode=normalized_mode)
        except Exception as exc:
            if not Config.NLP_SERVICE_FALLBACK_LOCAL:
                raise
            logger.warning("NLP 独立服务不可用，回退本地分析：%s", exc)
    return _analyze_local_text(text=text, mode=normalized_mode)


def _analyze_remote_batch(texts: list[str], mode: str) -> list[dict[str, Any]]:
    response = requests.post(
        f"{Config.NLP_SERVICE_BASE_URL}/api/nlp/predict/batch",
        json={"texts": texts, "mode": mode},
        headers=_remote_headers(),
        timeout=Config.NLP_SERVICE_TIMEOUT,
    )
    response.raise_for_status()
    payload = _extract_remote_data(response.json())
    if isinstance(payload, dict):
        results = payload.get("results", [])
        if isinstance(results, list):
            return results
    if isinstance(payload, list):
        return payload
    raise ValueError("NLP 批量分析返回格式无效")


def _analyze_local_batch(texts: list[str], mode: str) -> list[dict[str, Any]]:
    return SentimentService.analyze_batch(texts, mode)


def analyze_batch(texts: list[str], mode: str = "custom") -> list[dict[str, Any]]:
    normalized_mode = (mode or "custom").strip()
    if Config.NLP_SERVICE_ENABLED:
        try:
            return _analyze_remote_batch(texts=texts, mode=normalized_mode)
        except Exception as exc:
            if not Config.NLP_SERVICE_FALLBACK_LOCAL:
                raise
            logger.warning("NLP 独立服务不可用，回退本地批量分析：%s", exc)
    return _analyze_local_batch(texts=texts, mode=normalized_mode)


def _submit_remote_analyze_task(text: str, mode: str) -> dict[str, Any]:
    response = requests.post(
        f"{Config.NLP_SERVICE_BASE_URL}/api/nlp/tasks/analyze",
        json={"text": text, "mode": mode},
        headers=_remote_headers(),
        timeout=Config.NLP_SERVICE_TIMEOUT,
    )
    response.raise_for_status()
    payload = _extract_remote_data(response.json())
    if not isinstance(payload, dict):
        raise ValueError("NLP 异步分析返回格式无效")
    return _normalize_task_result(payload, default_label="情感分析", mode=mode)


def _submit_local_analyze_task(text: str, mode: str) -> dict[str, Any]:
    from tasks.celery_sentiment import analyze_single_with_fallback

    task = analyze_single_with_fallback.delay(text, mode)
    return {
        "task_id": task.id,
        "task_label": "情感分析",
        "mode": mode,
        "status": "PENDING",
    }


def submit_analyze_task(text: str, mode: str = "smart") -> dict[str, Any]:
    normalized_mode = (mode or "smart").strip()
    if Config.NLP_SERVICE_ENABLED:
        try:
            return _submit_remote_analyze_task(text=text, mode=normalized_mode)
        except Exception as exc:
            if not Config.NLP_SERVICE_FALLBACK_LOCAL:
                raise
            logger.warning("NLP 独立服务不可用，回退本地异步分析：%s", exc)
    return _submit_local_analyze_task(text=text, mode=normalized_mode)


def _submit_remote_retrain_task(optimize: bool) -> dict[str, Any]:
    response = requests.post(
        f"{Config.NLP_SERVICE_BASE_URL}/api/nlp/tasks/retrain",
        json={"optimize": bool(optimize)},
        headers=_remote_headers(),
        timeout=Config.NLP_SERVICE_TIMEOUT,
    )
    response.raise_for_status()
    payload = _extract_remote_data(response.json())
    if not isinstance(payload, dict):
        raise ValueError("NLP 重训练返回格式无效")
    return _normalize_task_result(payload, default_label="模型重训练", mode="custom")


def _submit_local_retrain_task(optimize: bool) -> dict[str, Any]:
    from tasks.celery_sentiment import retrain_model_task

    task = retrain_model_task.delay(optimize=bool(optimize))
    return {
        "task_id": task.id,
        "task_label": "模型重训练",
        "mode": "custom",
        "status": "PENDING",
    }


def submit_retrain_task(optimize: bool = False) -> dict[str, Any]:
    if Config.NLP_SERVICE_ENABLED:
        try:
            return _submit_remote_retrain_task(optimize=bool(optimize))
        except Exception as exc:
            if not Config.NLP_SERVICE_FALLBACK_LOCAL:
                raise
            logger.warning("NLP 独立服务不可用，回退本地重训练：%s", exc)
    return _submit_local_retrain_task(optimize=bool(optimize))


def _query_remote_task(task_id: str) -> dict[str, Any]:
    response = requests.get(
        f"{Config.NLP_SERVICE_BASE_URL}/api/nlp/tasks/{task_id}/status",
        headers=_remote_headers(),
        timeout=Config.NLP_SERVICE_TIMEOUT,
    )
    response.raise_for_status()
    payload = _extract_remote_data(response.json())
    if not isinstance(payload, dict):
        raise ValueError("NLP 任务状态返回格式无效")
    return payload


def _query_local_task(task_id: str) -> dict[str, Any]:
    result = AsyncResult(task_id, app=celery_app)
    state = result.state
    payload: dict[str, Any] = {
        "task_id": task_id,
        "state": state,
        "progress": 0,
        "message": "",
        "result": {},
    }
    if state == "PENDING":
        payload["message"] = "任务等待中..."
    elif state == "PROGRESS":
        info = result.info or {}
        current = int(info.get("current", 0) or 0)
        total = int(info.get("total", 1) or 1)
        payload["progress"] = int(current / max(total, 1) * 100)
        payload["message"] = str(info.get("status", ""))
    elif state == "SUCCESS":
        payload["progress"] = 100
        payload["result"] = result.result or {}
        payload["message"] = "任务完成"
    elif state == "FAILURE":
        payload["message"] = str(result.info)
    return payload


def query_nlp_task_progress(task_id: str) -> dict[str, Any]:
    if Config.NLP_SERVICE_ENABLED:
        try:
            return _query_remote_task(task_id)
        except Exception as exc:
            if not Config.NLP_SERVICE_FALLBACK_LOCAL:
                raise
            logger.warning("NLP 独立服务状态查询失败，回退本地查询：%s", exc)
    return _query_local_task(task_id)
