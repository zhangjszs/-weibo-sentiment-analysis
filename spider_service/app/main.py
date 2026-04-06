from __future__ import annotations

from flask import Flask, jsonify, request

try:
    from celery_app import celery_app
except ImportError:  # pragma: no cover - package mode fallback
    from spider_service.celery_app import celery_app

from celery.result import AsyncResult

from app.tasks import (
    build_task_response,
    spider_comments_task,
    spider_hot_task,
    spider_search_task,
)

app = Flask(__name__)


def _ok(data: dict, code: int = 200):
    return jsonify({"code": code, "msg": "ok", "data": data}), code


def _error(message: str, code: int = 400):
    return jsonify({"code": code, "msg": message, "data": {}}), code


@app.get("/health")
def health():
    return _ok({"status": "ok"})


@app.post("/api/spider/tasks")
def submit_task():
    payload = request.get_json(silent=True) or {}
    crawl_type = str(payload.get("type", "hot")).strip().lower()
    page_num = max(1, min(int(payload.get("page_num", 3)), 10))
    article_limit = max(1, min(int(payload.get("article_limit", 50)), 100))
    keyword = str(payload.get("keyword", "")).strip()

    if crawl_type == "search":
        if not keyword:
            return _error("关键词搜索模式下 keyword 不能为空", 400)
        task = spider_search_task.delay(keyword, page_num)
        task_label = f"关键词搜索: {keyword}"
    elif crawl_type == "comments":
        task = spider_comments_task.delay(article_limit)
        task_label = "爬取评论"
        crawl_type = "comments"
    else:
        task = spider_hot_task.delay(page_num)
        task_label = "刷新热门微博"
        crawl_type = "hot"

    return _ok(
        {
            "task_id": task.id,
            "task_label": task_label,
            "crawl_type": crawl_type,
            "keyword": keyword,
            "page_num": page_num,
            "article_limit": article_limit,
        }
    )


@app.get("/api/spider/tasks/<task_id>/status")
def query_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    payload = build_task_response(result.state, task_id, result.info or result.result)
    if result.state == "SUCCESS":
        payload["result"] = result.result or {}
    return _ok(payload)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
