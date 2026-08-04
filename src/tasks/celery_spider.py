#!/usr/bin/env python3
"""
爬虫异步任务模块
功能：将同步爬虫改造为Celery异步任务，支持进度追踪
"""

import csv
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional, Tuple

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from config.settings import Config
from tasks.celery_config import celery_app

logger = logging.getLogger(__name__)


def _upsert_articles_batch(rows: List[Tuple], batch_size: int = 200) -> int:
    if not rows:
        return 0

    from sqlalchemy import text as sa_text

    from utils.query import engine

    sql = """INSERT INTO article
        (id, likeNum, commentsLen, reposts_count, region, content,
         contentLen, created_at, type, detailUrl, authorAvatar,
         authorName, authorDetail, isVip)
        VALUES (:p0, :p1, :p2, :p3, :p4, :p5, :p6, :p7, :p8, :p9, :p10, :p11, :p12, :p13)
        ON DUPLICATE KEY UPDATE
        likeNum=VALUES(likeNum),
        commentsLen=VALUES(commentsLen),
        reposts_count=VALUES(reposts_count)"""

    inserted = 0
    with engine.connect() as conn:
        for idx in range(0, len(rows), batch_size):
            batch = rows[idx : idx + batch_size]
            params = [{f"p{j}": v for j, v in enumerate(row)} for row in batch]
            conn.execute(sa_text(sql), params)
            inserted += len(batch)
        conn.commit()

    return inserted


def _notify_articles_upserted_event(
    task_id: str, pages: int, crawled: int, imported: int
) -> None:
    """文章批量写入后清理缓存（原走领域事件总线，P2 简化为直接调用）。"""
    from utils.cache import clear_all_cache

    clear_all_cache()
    logger.info(
        "文章入库后已触发缓存清理",
        extra={
            "task_id": task_id,
            "pages": pages,
            "crawled": crawled,
            "imported": imported,
        },
    )


def _build_hot_headers(cookie: str) -> Dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": cookie,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://weibo.com/",
    }


def _parse_hot_item(item: dict) -> Tuple:
    user = item.get("user", {}) or {}
    return (
        item.get("id", ""),
        item.get("attitudes_count", 0),
        item.get("comments_count", 0),
        item.get("reposts_count", 0),
        (item.get("region_name", "") or "无").replace("发布于 ", "")[:50],
        item.get("text_raw", "")[:2000],
        item.get("textLength", 0),
        datetime.now().strftime("%Y-%m-%d"),
        "热门",
        f"https://weibo.com/{user.get('id', '')}/{item.get('mblogid', '')}",
        user.get("avatar_large", "")[:500],
        user.get("screen_name", "")[:100],
        f"https://weibo.com/u/{user.get('id', '')}",
        user.get("v_plus", 0),
    )


def _fetch_hot_page(
    headers: Dict[str, str], page: int, task_id: str
) -> List[Tuple]:
    import requests as req

    url = "https://weibo.com/ajax/feed/hottimeline"
    params = {"group_id": 102803, "max_id": 0, "count": 20, "refresh_type": 1}
    try:
        response = req.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            logger.warning(
                f"[任务{task_id}] 第{page + 1}页返回异常状态: {response.status_code}"
            )
            return []
        payload = response.json()
        statuses = payload.get("statuses", []) if isinstance(payload, dict) else []
        return [_parse_hot_item(item) for item in statuses]
    except (req.RequestException, ValueError) as exc:
        logger.warning(f"[任务{task_id}] 第{page + 1}页爬取失败: {exc}")
        return []


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def spider_hot_task(self, page_num: int = 3) -> Dict[str, Any]:
    """热门微博刷新任务（异步）"""
    task_id = self.request.id
    page_num = max(1, min(int(page_num), 10))

    cookie = os.getenv("WEIBO_COOKIE", "")
    if not cookie:
        return {"status": "failed", "task_id": task_id, "error": "WEIBO_COOKIE未配置"}

    import random

    headers = _build_hot_headers(cookie)
    rows: List[Tuple] = []

    try:
        for page in range(page_num):
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": page + 1,
                    "total": page_num,
                    "status": f"正在爬取第 {page + 1}/{page_num} 页热门微博",
                    "crawled": len(rows),
                },
            )
            rows.extend(_fetch_hot_page(headers, page, task_id))
            time.sleep(random.uniform(0.5, 1.0))

        self.update_state(
            state="PROGRESS",
            meta={
                "current": page_num,
                "total": page_num,
                "status": "正在批量入库...",
                "crawled": len(rows),
            },
        )

        imported = _upsert_articles_batch(rows)
        _notify_articles_upserted_event(task_id, page_num, len(rows), imported)

        result = {
            "status": "success",
            "task_id": task_id,
            "pages": page_num,
            "crawled": len(rows),
            "imported": imported,
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        logger.info(f"[任务{task_id}] 热门微博刷新完成: {result}")
        return result

    except (requests.RequestException, OSError) as exc:
        logger.error(f"[任务{task_id}] 热门微博刷新失败: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1)) from exc


def _build_search_params(keyword: str, page: int) -> Dict[str, Any]:
    return {
        "q": keyword,
        "type": "all",
        "sub": "all",
        "timescope": "custom",
        "refer": "g",
        "page": page,
        "count": 10,
    }


def _fetch_search_page(config, search_url: str, keyword: str, page: int, task_id: str):
    """Fetch one search page and return (valid_statuses, error_msg)."""
    params = _build_search_params(keyword, page)
    try:
        response = config.make_safe_request(
            search_url, method="GET", params=params, use_proxy=True
        )
    except (requests.RequestException, OSError) as exc:
        logger.error(f"[任务{task_id}] 第{page}页请求异常: {exc}")
        return None, str(exc)

    if not response or response.status_code != 200:
        code = response.status_code if response else "None"
        logger.error(f"[任务{task_id}] 第{page}页请求失败: {code}")
        return None, f"HTTP {code}"

    data = response.json()
    if "data" not in data or "list" not in data["data"]:
        logger.warning(f"[任务{task_id}] 第{page}页响应格式异常")
        return None, "invalid response"

    statuses = data["data"]["list"]
    valid = [s for s in statuses if "text_raw" in s or "text" in s]
    if not valid:
        logger.warning(f"[任务{task_id}] 第{page}页无有效数据")
        return [], None

    return valid, None


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def spider_search_task(self, keyword: str, page_num: int = 3) -> Dict[str, Any]:
    """关键词搜索爬虫任务（异步）"""
    task_id = self.request.id
    logger.info(f"[任务{task_id}] 开始搜索爬虫: keyword={keyword}, pages={page_num}")

    try:
        self.update_state(
            state="PROGRESS",
            meta={
                "current": 0,
                "total": page_num,
                "status": "初始化爬虫...",
                "keyword": keyword,
            },
        )

        from spider.config import get_config_manager
        from spider.spiderContent import init, parse_json

        init()
        config = get_config_manager()
        search_url = "https://weibo.com/ajax/statuses/search"

        total_articles = 0
        success_pages = 0

        for page in range(1, page_num + 1):
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": page,
                    "total": page_num,
                    "status": f"正在爬取第 {page}/{page_num} 页",
                    "articles": total_articles,
                    "keyword": keyword,
                },
            )

            valid_statuses, _ = _fetch_search_page(
                config, search_url, keyword, page, task_id
            )
            if valid_statuses:
                parse_json(valid_statuses, f"搜索:{keyword}")
                total_articles += len(valid_statuses)
                success_pages += 1
                logger.info(
                    f"[任务{task_id}] 第{page}页成功: {len(valid_statuses)}条"
                )

        result = {
            "status": "success",
            "task_id": task_id,
            "keyword": keyword,
            "total_pages": page_num,
            "success_pages": success_pages,
            "total_articles": total_articles,
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        logger.info(f"[任务{task_id}] 完成: {result}")
        return result

    except (requests.RequestException, OSError) as exc:
        logger.error(f"[任务{task_id}] 失败: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1)) from exc


def _parse_uid_from_url(detail_url: str) -> Optional[str]:
    if not detail_url or "weibo.com" not in detail_url:
        return None
    try:
        parts = detail_url.replace("https://weibo.com/", "").split("/")
        return parts[0] if parts else None
    except (IndexError, AttributeError):
        return None


def _fetch_article_comments(
    config, url: str, article_id: str, uid: Optional[str]
) -> str:
    """Fetch comments for one article. Returns parse result status."""
    import random

    from spider.config import DEFAULT_DELAY

    delay = (
        random.uniform(*DEFAULT_DELAY)
        if isinstance(DEFAULT_DELAY, tuple)
        else DEFAULT_DELAY
    )
    time.sleep(delay)

    headers = config.get_random_headers()
    if uid:
        headers["Referer"] = f"https://weibo.com/{uid}/"

    params = {
        "is_reload": "1",
        "id": article_id,
        "is_show_bulletin": "2",
        "is_mix": "0",
        "count": "10",
        "uid": uid or "nouid",
        "fetch_level": "0",
        "locale": "zh-CN",
    }

    response = config.make_safe_request(url, method="GET", params=params, use_proxy=True)
    if not response or response.status_code != 200:
        return "FAILED"

    from spider.spiderComments import parse_json

    return parse_json(response.json(), article_id)


def _load_articles_from_csv(csv_path: str, limit: int) -> List[list]:
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, encoding="utf8") as f:
        reader = csv.reader(f)
        try:
            next(reader)
        except StopIteration:
            return []
        return [a for a in reader if a][:limit]


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def spider_comments_task(self, article_limit: int = 50) -> Dict[str, Any]:
    """评论爬虫任务（异步）"""
    task_id = self.request.id
    logger.info(f"[任务{task_id}] 开始评论爬虫: limit={article_limit}")

    try:
        from spider.config import get_config_manager
        from spider.spiderComments import init

        init()

        url = "https://weibo.com/ajax/statuses/buildComments"
        csv_path = os.path.join(Config.DATA_DIR, "articleData.csv")

        articles = _load_articles_from_csv(csv_path, article_limit)
        if not articles:
            return {
                "status": "failed",
                "error": f"articleData.csv不存在或为空: {csv_path}",
                "task_id": task_id,
            }

        config = get_config_manager()
        total_comments = 0
        processed_articles = 0

        for i, article in enumerate(articles):
            article_id = article[0]
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": i + 1,
                    "total": len(articles),
                    "status": f"正在爬取文章 {article_id} 的评论",
                    "comments": total_comments,
                },
            )

            uid = _parse_uid_from_url(article[9] if len(article) > 9 else "")

            try:
                result = _fetch_article_comments(config, url, article_id, uid)
                if result == "SUCCESS":
                    total_comments += 1
                    processed_articles += 1
            except (requests.RequestException, OSError, ValueError) as exc:
                logger.error(f"[任务{task_id}] 处理文章 {article_id} 异常: {exc}")

        return {
            "status": "success",
            "task_id": task_id,
            "processed_articles": processed_articles,
            "total_comments_pages": total_comments,
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    except (requests.RequestException, OSError) as exc:
        logger.error(f"[任务{task_id}] 评论爬虫失败: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1)) from exc


def _build_task_response(result, task_id: str) -> dict:
    """将 Celery AsyncResult 映射为统一的五字段结构"""
    state = result.state
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
        info = result.info or {}
        current = info.get("current", 0)
        total = info.get("total", 1) or 1
        response["progress"] = int(current / total * 100)
        response["message"] = info.get("status", "")
    elif state == "SUCCESS":
        response["progress"] = 100
        response["result"] = result.result or {}
        response["message"] = "任务完成"
    elif state == "FAILURE":
        response["message"] = str(result.info)
    return response


@celery_app.task(bind=True)
def get_task_progress(self, task_id: str) -> Dict[str, Any]:
    """查询任务进度，返回统一的五字段结构"""
    from celery.result import AsyncResult

    result = AsyncResult(task_id, app=celery_app)
    return _build_task_response(result, task_id)


def search_weibo_generator(keyword: str, page_num: int) -> Generator[Dict, None, None]:
    """生成器版本的微博搜索（用于实时进度反馈）"""
    from spider.config import get_config_manager
    from spider.spiderContent import init, parse_json

    init()
    config = get_config_manager()
    search_url = "https://weibo.com/ajax/statuses/search"

    for page in range(1, page_num + 1):
        valid_statuses, error = _fetch_search_page(
            config, search_url, keyword, page, "generator"
        )
        if valid_statuses:
            parse_json(valid_statuses, f"搜索:{keyword}")
            yield {"page": page, "count": len(valid_statuses), "status": "success"}
        elif error:
            yield {"page": page, "count": 0, "status": "error", "error": error}
        else:
            yield {"page": page, "count": 0, "status": "no_data"}
