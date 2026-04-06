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
from typing import Any, Dict, Generator, List, Tuple

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from config.settings import Config
from services.domain_events import ArticlesUpsertedEvent, domain_event_bus
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
    """发布文章批量写入事件，解耦副作用。"""
    domain_event_bus.publish(
        ArticlesUpsertedEvent(
            task_id=task_id,
            pages=pages,
            crawled=crawled,
            imported=imported,
        )
    )


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def spider_hot_task(self, page_num: int = 3) -> Dict[str, Any]:
    """
    热门微博刷新任务（异步）
    统一用于 /api/spider/crawl(type=hot) 和 /api/spider/refresh。
    """
    task_id = self.request.id
    page_num = max(1, min(int(page_num), 10))

    cookie = os.getenv("WEIBO_COOKIE", "")
    if not cookie:
        return {
            "status": "failed",
            "task_id": task_id,
            "error": "WEIBO_COOKIE未配置",
        }

    import random

    import requests

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": cookie,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://weibo.com/",
    }

    rows: List[Tuple] = []
    crawled = 0

    try:
        for page in range(page_num):
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": page + 1,
                    "total": page_num,
                    "status": f"正在爬取第 {page + 1}/{page_num} 页热门微博",
                    "crawled": crawled,
                },
            )

            url = "https://weibo.com/ajax/feed/hottimeline"
            params = {
                "group_id": 102803,
                "max_id": 0,
                "count": 20,
                "refresh_type": 1,
            }
            try:
                response = requests.get(url, headers=headers, params=params, timeout=15)
                if response.status_code != 200:
                    logger.warning(
                        f"[任务{task_id}] 第{page + 1}页返回异常状态: {response.status_code}"
                    )
                    continue

                payload = response.json()
                statuses = (
                    payload.get("statuses", []) if isinstance(payload, dict) else []
                )
                for item in statuses:
                    user = item.get("user", {}) or {}
                    rows.append(
                        (
                            item.get("id", ""),
                            item.get("attitudes_count", 0),
                            item.get("comments_count", 0),
                            item.get("reposts_count", 0),
                            (item.get("region_name", "") or "无").replace(
                                "发布于 ", ""
                            )[:50],
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
                    )
                crawled = len(rows)
            except Exception as page_exc:
                logger.warning(f"[任务{task_id}] 第{page + 1}页爬取失败: {page_exc}")
                continue

            time.sleep(random.uniform(0.5, 1.0))

        self.update_state(
            state="PROGRESS",
            meta={
                "current": page_num,
                "total": page_num,
                "status": "正在批量入库...",
                "crawled": crawled,
            },
        )

        imported = _upsert_articles_batch(rows)
        _notify_articles_upserted_event(
            task_id=task_id,
            pages=page_num,
            crawled=crawled,
            imported=imported,
        )

        result = {
            "status": "success",
            "task_id": task_id,
            "pages": page_num,
            "crawled": crawled,
            "imported": imported,
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        logger.info(f"[任务{task_id}] 热门微博刷新完成: {result}")
        return result

    except Exception as exc:
        logger.error(f"[任务{task_id}] 热门微博刷新失败: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1)) from exc


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def spider_search_task(self, keyword: str, page_num: int = 3) -> Dict[str, Any]:
    """
    关键词搜索爬虫任务（异步）

    Args:
        keyword: 搜索关键词
        page_num: 爬取页数

    Returns:
        dict: 任务执行结果
    """
    task_id = self.request.id
    logger.info(f"[任务{task_id}] 开始搜索爬虫: keyword={keyword}, pages={page_num}")

    try:
        # 更新任务状态为"开始"
        self.update_state(
            state="PROGRESS",
            meta={
                "current": 0,
                "total": page_num,
                "status": "初始化爬虫...",
                "keyword": keyword,
            },
        )

        # 导入爬虫模块
        from spider.config import get_config_manager
        from spider.spiderContent import init, parse_json

        # 初始化
        init()

        # 获取配置
        config = get_config_manager()
        search_url = "https://weibo.com/ajax/statuses/search"

        total_articles = 0
        success_pages = 0

        # 逐页爬取
        for page in range(1, page_num + 1):
            try:
                # 更新进度
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

                # 构造搜索参数
                params = {
                    "q": keyword,
                    "type": "all",
                    "sub": "all",
                    "timescope": "custom",
                    "refer": "g",
                    "page": page,
                    "count": 10,
                }

                # 发送请求（使用配置管理器的安全请求方法）
                response = config.make_safe_request(
                    search_url, method="GET", params=params, use_proxy=True
                )

                if response and response.status_code == 200:
                    data = response.json()
                    if "data" in data and "list" in data["data"]:
                        statuses = data["data"]["list"]
                        valid_statuses = [
                            s for s in statuses if "text_raw" in s or "text" in s
                        ]

                        if valid_statuses:
                            parse_json(valid_statuses, f"搜索:{keyword}")
                            total_articles += len(valid_statuses)
                            success_pages += 1
                            logger.info(
                                f"[任务{task_id}] 第{page}页成功: {len(valid_statuses)}条"
                            )
                        else:
                            logger.warning(f"[任务{task_id}] 第{page}页无有效数据")
                    else:
                        logger.warning(f"[任务{task_id}] 第{page}页响应格式异常")
                else:
                    logger.error(
                        f"[任务{task_id}] 第{page}页请求失败: {response.status_code if response else 'None'}"
                    )

            except Exception as e:
                logger.error(f"[任务{task_id}] 第{page}页异常: {e}")
                # 继续下一页，不中断整个任务
                continue

        # 任务完成
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

    except Exception as exc:
        logger.error(f"[任务{task_id}] 失败: {exc}")
        # 触发重试
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1)) from exc


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def spider_comments_task(self, article_limit: int = 50) -> Dict[str, Any]:
    """
    评论爬虫任务（异步）
    爬取articleData.csv中的文章评论

    Args:
        article_limit: 限制爬取的文章数量（防止任务过长）

    Returns:
        dict: 任务执行结果
    """
    task_id = self.request.id
    logger.info(f"[任务{task_id}] 开始评论爬虫: limit={article_limit}")

    try:
        from spider.config import DEFAULT_DELAY, get_config_manager
        from spider.spiderComments import init, parse_json

        init()

        url = "https://weibo.com/ajax/statuses/buildComments"
        article_csv_path = os.path.join(Config.DATA_DIR, "articleData.csv")

        if not os.path.exists(article_csv_path):
            return {
                "status": "failed",
                "error": f"articleData.csv不存在: {article_csv_path}",
                "task_id": task_id,
            }

        total_comments = 0
        processed_articles = 0

        with open(article_csv_path, encoding="utf8") as readerFile:
            reader = csv.reader(readerFile)
            try:
                next(reader)  # 跳过标题
            except StopIteration:
                return {"status": "failed", "error": "CSV文件为空", "task_id": task_id}

            articles = list(reader)[:article_limit]  # 限制数量
            total = len(articles)

            for i, article in enumerate(articles):
                if not article:
                    continue

                try:
                    articleId = article[0]

                    # 更新进度
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "current": i + 1,
                            "total": total,
                            "status": f"正在爬取文章 {articleId} 的评论",
                            "comments": total_comments,
                        },
                    )

                    # 从detailUrl提取uid
                    uid = None
                    if len(article) > 9:
                        detail_url = article[9]
                        if detail_url and "weibo.com" in detail_url:
                            try:
                                parts = detail_url.replace(
                                    "https://weibo.com/", ""
                                ).split("/")
                                if len(parts) >= 1:
                                    uid = parts[0]
                            except Exception as e:
                                logger.debug("解析 detail_url 失败: %s", e)

                    # 延时
                    import random

                    if isinstance(DEFAULT_DELAY, tuple):
                        time.sleep(random.uniform(DEFAULT_DELAY[0], DEFAULT_DELAY[1]))
                    else:
                        time.sleep(DEFAULT_DELAY)

                    # 获取评论
                    config = get_config_manager()
                    headers = config.get_random_headers()
                    if uid:
                        headers["Referer"] = f"https://weibo.com/{uid}/"

                    params = {
                        "is_reload": "1",
                        "id": articleId,
                        "is_show_bulletin": "2",
                        "is_mix": "0",
                        "count": "10",
                        "uid": uid or "nouid",
                        "fetch_level": "0",
                        "locale": "zh-CN",
                    }

                    response = config.make_safe_request(
                        url, method="GET", params=params, use_proxy=True
                    )

                    if response and response.status_code == 200:
                        result = parse_json(response.json(), articleId)
                        if result == "SUCCESS":
                            total_comments += 1
                            processed_articles += 1

                except Exception as e:
                    logger.error(f"[任务{task_id}] 处理文章异常: {e}")
                    continue

        return {
            "status": "success",
            "task_id": task_id,
            "processed_articles": processed_articles,
            "total_comments_pages": total_comments,
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as exc:
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
    """
    生成器版本的微博搜索（用于实时进度反馈）

    Yields:
        dict: 每页的进度信息
    """
    from spider.config import get_config_manager
    from spider.spiderContent import init, parse_json

    init()
    config = get_config_manager()
    search_url = "https://weibo.com/ajax/statuses/search"

    for page in range(1, page_num + 1):
        params = {
            "q": keyword,
            "type": "all",
            "sub": "all",
            "timescope": "custom",
            "refer": "g",
            "page": page,
            "count": 10,
        }

        try:
            response = config.make_safe_request(
                search_url, method="GET", params=params, use_proxy=True
            )

            if response and response.status_code == 200:
                data = response.json()
                if "data" in data and "list" in data["data"]:
                    statuses = data["data"]["list"]
                    valid_statuses = [
                        s for s in statuses if "text_raw" in s or "text" in s
                    ]

                    if valid_statuses:
                        parse_json(valid_statuses, f"搜索:{keyword}")
                        yield {
                            "page": page,
                            "count": len(valid_statuses),
                            "status": "success",
                        }
                    else:
                        yield {"page": page, "count": 0, "status": "no_data"}
                else:
                    yield {"page": page, "count": 0, "status": "invalid_response"}
            else:
                yield {"page": page, "count": 0, "status": "request_failed"}

        except Exception as e:
            yield {"page": page, "count": 0, "status": "error", "error": str(e)}
