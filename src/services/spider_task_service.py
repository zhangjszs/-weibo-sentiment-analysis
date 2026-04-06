#!/usr/bin/env python3
"""
Spider 任务调度服务
支持本地 Celery 与独立 Spider 服务两种后端。
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from config.settings import Config

logger = logging.getLogger(__name__)


def _normalize_crawl_type(crawl_type: str) -> str:
    normalized = (crawl_type or "hot").strip().lower()
    if normalized not in {"hot", "search", "comments"}:
        return "hot"
    return normalized


def _extract_remote_data(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Spider 服务返回格式无效")

    data = payload.get("data")
    if isinstance(data, dict):
        return data
    return payload


def _default_task_label(crawl_type: str, keyword: str) -> str:
    if crawl_type == "search":
        return f"关键词搜索: {keyword}"
    if crawl_type == "comments":
        return "爬取评论"
    return "刷新热门微博"


def _normalize_dispatch_result(
    payload: dict[str, Any],
    crawl_type: str,
    keyword: str,
    page_num: int,
    article_limit: int,
) -> dict[str, Any]:
    task_id = payload.get("task_id") or payload.get("taskId")
    if not task_id:
        raise ValueError("Spider 服务未返回 task_id")

    normalized_keyword = (payload.get("keyword") or keyword or "").strip()
    normalized_type = (
        payload.get("crawl_type") or payload.get("type") or crawl_type or "hot"
    )

    return {
        "task_id": str(task_id),
        "task_label": payload.get("task_label")
        or payload.get("taskLabel")
        or _default_task_label(normalized_type, normalized_keyword),
        "crawl_type": _normalize_crawl_type(str(normalized_type)),
        "keyword": normalized_keyword,
        "page_num": int(payload.get("page_num") or payload.get("pageNum") or page_num),
        "article_limit": int(
            payload.get("article_limit")
            or payload.get("articleLimit")
            or article_limit
        ),
    }


def _remote_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if Config.SPIDER_SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {Config.SPIDER_SERVICE_TOKEN}"
    return headers


def _submit_remote_task(
    crawl_type: str, keyword: str, page_num: int, article_limit: int
) -> dict[str, Any]:
    response = requests.post(
        f"{Config.SPIDER_SERVICE_BASE_URL}/api/spider/tasks",
        json={
            "type": crawl_type,
            "keyword": keyword,
            "page_num": page_num,
            "article_limit": article_limit,
        },
        headers=_remote_headers(),
        timeout=Config.SPIDER_SERVICE_TIMEOUT,
    )
    response.raise_for_status()
    payload = _extract_remote_data(response.json())
    return _normalize_dispatch_result(
        payload,
        crawl_type=crawl_type,
        keyword=keyword,
        page_num=page_num,
        article_limit=article_limit,
    )


def _submit_local_task(
    crawl_type: str, keyword: str, page_num: int, article_limit: int
) -> dict[str, Any]:
    from tasks.celery_spider import (
        spider_comments_task,
        spider_hot_task,
        spider_search_task,
    )

    if crawl_type == "search":
        if not keyword.strip():
            raise ValueError("关键词搜索模式下 keyword 不能为空")
        task = spider_search_task.delay(keyword.strip(), page_num)
    elif crawl_type == "comments":
        task = spider_comments_task.delay(article_limit)
    else:
        task = spider_hot_task.delay(page_num)

    return {
        "task_id": task.id,
        "task_label": _default_task_label(crawl_type, keyword.strip()),
        "crawl_type": crawl_type,
        "keyword": keyword.strip(),
        "page_num": page_num,
        "article_limit": article_limit,
    }


def submit_spider_task(
    crawl_type: str, keyword: str = "", page_num: int = 3, article_limit: int = 50
) -> dict[str, Any]:
    crawl_type = _normalize_crawl_type(crawl_type)
    normalized_keyword = (keyword or "").strip()
    page_num = max(1, min(int(page_num), 10))
    article_limit = max(1, min(int(article_limit), 100))

    if Config.SPIDER_SERVICE_ENABLED:
        try:
            return _submit_remote_task(
                crawl_type=crawl_type,
                keyword=normalized_keyword,
                page_num=page_num,
                article_limit=article_limit,
            )
        except Exception as exc:
            if not Config.SPIDER_SERVICE_FALLBACK_LOCAL:
                raise
            logger.warning("Spider 独立服务不可用，回退本地 Celery：%s", exc)

    return _submit_local_task(
        crawl_type=crawl_type,
        keyword=normalized_keyword,
        page_num=page_num,
        article_limit=article_limit,
    )


def _query_remote_task(task_id: str) -> dict[str, Any]:
    response = requests.get(
        f"{Config.SPIDER_SERVICE_BASE_URL}/api/spider/tasks/{task_id}/status",
        headers=_remote_headers(),
        timeout=Config.SPIDER_SERVICE_TIMEOUT,
    )
    response.raise_for_status()
    payload = _extract_remote_data(response.json())
    if not isinstance(payload, dict):
        raise ValueError("Spider 服务任务状态返回格式无效")
    return payload


def _query_local_task(task_id: str) -> dict[str, Any]:
    from tasks.celery_spider import get_task_progress

    return get_task_progress(task_id)


def query_spider_task_progress(task_id: str) -> dict[str, Any]:
    if Config.SPIDER_SERVICE_ENABLED:
        return _query_remote_task(task_id)
    return _query_local_task(task_id)

