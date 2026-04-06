import logging
import time
from typing import Any

try:
    from celery_app import celery_app
except ImportError:  # pragma: no cover - package mode fallback
    from spider_service.celery_app import celery_app

logger = logging.getLogger(__name__)


def build_task_response(state: str, task_id: str, info: dict | None = None) -> dict:
    info = info or {}
    response = {
        "task_id": task_id,
        "state": state,
        "progress": 0,
        "message": "",
        "result": {},
    }
    if state == "PENDING":
        response["message"] = "任务等待中..."
    elif state == "PROGRESS":
        current = info.get("current", 0)
        total = info.get("total", 1) or 1
        response["progress"] = int(current / total * 100)
        response["message"] = info.get("status", "")
    elif state == "SUCCESS":
        response["progress"] = 100
        response["result"] = info
        response["message"] = "任务完成"
    elif state == "FAILURE":
        response["message"] = str(info)
    return response


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def spider_hot_task(self, page_num: int = 3) -> dict[str, Any]:
    task_id = self.request.id
    logger.info("[Task %s] Start hot spider: pages=%s", task_id, page_num)
    for page in range(page_num):
        time.sleep(1)
        self.update_state(
            state="PROGRESS",
            meta={
                "current": page + 1,
                "total": page_num,
                "status": f"正在爬取第 {page + 1}/{page_num} 页热门微博",
            },
        )
    return {
        "status": "success",
        "task_id": task_id,
        "pages": page_num,
        "crawled": page_num * 20,
        "imported": page_num * 20,
    }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def spider_search_task(self, keyword: str, page_num: int = 3) -> dict[str, Any]:
    task_id = self.request.id
    logger.info(
        "[Task %s] Start search spider: keyword=%s, pages=%s", task_id, keyword, page_num
    )
    for page in range(page_num):
        time.sleep(1)
        self.update_state(
            state="PROGRESS",
            meta={
                "current": page + 1,
                "total": page_num,
                "status": f"正在搜索 \"{keyword}\" 第 {page + 1}/{page_num} 页",
            },
        )
    return {
        "status": "success",
        "task_id": task_id,
        "keyword": keyword,
        "total_pages": page_num,
        "total_articles": page_num * 10,
    }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def spider_comments_task(self, article_limit: int = 50) -> dict[str, Any]:
    task_id = self.request.id
    logger.info("[Task %s] Start comments spider: limit=%s", task_id, article_limit)
    for idx in range(3):
        time.sleep(1)
        self.update_state(
            state="PROGRESS",
            meta={
                "current": idx + 1,
                "total": 3,
                "status": "正在抓取评论数据",
            },
        )
    return {
        "status": "success",
        "task_id": task_id,
        "processed_articles": article_limit,
        "total_comments_pages": article_limit,
    }
