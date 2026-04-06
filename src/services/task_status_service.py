#!/usr/bin/env python3
"""
统一任务状态查询服务
优先查询远程 Spider/NLP 服务，无法命中时回退本地 Celery 结果后端。
"""

from __future__ import annotations

import logging
from typing import Any

from celery.result import AsyncResult
from requests import HTTPError

from config.settings import Config
from services.nlp_task_service import _query_remote_task as query_nlp_remote
from services.spider_task_service import _query_remote_task as query_spider_remote
from tasks.celery_config import celery_app

logger = logging.getLogger(__name__)


def _is_not_found_error(exc: Exception) -> bool:
    if not isinstance(exc, HTTPError):
        return False
    response = exc.response
    return bool(response is not None and response.status_code == 404)


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


def query_task_progress(task_id: str) -> dict[str, Any]:
    if Config.SPIDER_SERVICE_ENABLED:
        try:
            return query_spider_remote(task_id)
        except Exception as exc:
            if not _is_not_found_error(exc):
                logger.warning("Spider 远程任务状态查询失败: %s", exc)

    if Config.NLP_SERVICE_ENABLED:
        try:
            return query_nlp_remote(task_id)
        except Exception as exc:
            if not _is_not_found_error(exc):
                logger.warning("NLP 远程任务状态查询失败: %s", exc)

    return _query_local_task(task_id)
