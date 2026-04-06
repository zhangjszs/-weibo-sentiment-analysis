#!/usr/bin/env python3
"""
爬虫管理 API
功能：提供爬虫概览、同步爬取、日志查询等接口
"""

import logging
import os
import threading
import time
from datetime import datetime

from flask import Blueprint, request

from config.settings import Config
from services.spider_task_service import query_spider_task_progress, submit_spider_task
from utils.api_response import error, ok
from utils.authz import admin_required

logger = logging.getLogger(__name__)

spider_bp = Blueprint("spider_api", __name__, url_prefix="/api/spider")

# 爬虫任务状态（内存存储，进程级别）
_spider_state = {
    "running": False,
    "current_task": None,
    "current_task_id": None,
    "current_task_type": None,
    "last_finalized_task_id": None,
    "progress": 0,
    "message": "",
    "history": [],  # 最近的爬取记录
}
_spider_lock = threading.Lock()


def _add_history(action, status, detail="", count=0):
    """添加一条爬取历史记录"""
    record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "status": status,
        "detail": detail,
        "count": count,
    }
    with _spider_lock:
        _spider_state["history"].insert(0, record)
        # 只保留最近 50 条
        _spider_state["history"] = _spider_state["history"][:50]
    return record


def _progress_to_percent(progress_meta: dict) -> int:
    if not isinstance(progress_meta, dict):
        return 0
    current = progress_meta.get("current", 0)
    total = progress_meta.get("total", 0)
    if isinstance(total, int) and total > 0:
        return min(100, int((max(current, 0) / total) * 100))
    return int(progress_meta.get("progress", 0) or 0)


def _extract_result_count(result: dict) -> int:
    if not isinstance(result, dict):
        return 0
    return int(
        result.get("imported")
        or result.get("total_articles")
        or result.get("processed_articles")
        or result.get("total_comments_pages")
        or 0
    )


def dispatch_spider_task(
    crawl_type: str, keyword: str = "", page_num: int = 3, article_limit: int = 50
):
    return submit_spider_task(
        crawl_type=crawl_type,
        keyword=keyword,
        page_num=page_num,
        article_limit=article_limit,
    )


def register_submitted_task(dispatch_result: dict) -> None:
    with _spider_lock:
        _spider_state["running"] = True
        _spider_state["current_task"] = dispatch_result["task_label"]
        _spider_state["current_task_type"] = dispatch_result["crawl_type"]
        _spider_state["current_task_id"] = dispatch_result["task_id"]
        _spider_state["progress"] = 0
        _spider_state["message"] = "任务已提交，等待执行..."


def _refresh_task_state() -> None:
    task_id = _spider_state.get("current_task_id")
    if not task_id:
        return

    try:
        result = query_spider_task_progress(task_id)
    except Exception as e:
        logger.warning(f"查询任务状态失败: task_id={task_id}, error={e}")
        return

    state = result.get("state")
    if state in ("PENDING", "PROGRESS"):
        _spider_state["running"] = True
        progress_meta = result.get("progress", {}) if state == "PROGRESS" else {}
        _spider_state["progress"] = (
            _progress_to_percent(progress_meta) if state == "PROGRESS" else 0
        )
        _spider_state["message"] = (
            progress_meta.get("status") if isinstance(progress_meta, dict) else ""
        ) or result.get("status", "任务执行中...")
        return

    if state == "SUCCESS":
        _spider_state["running"] = False
        _spider_state["progress"] = 100
        _spider_state["message"] = "任务完成"
        if _spider_state.get("last_finalized_task_id") != task_id:
            task_result = result.get("result", {})
            _add_history(
                _spider_state.get("current_task") or "爬虫任务",
                "success",
                f"task_id={task_id}",
                _extract_result_count(task_result),
            )
            _spider_state["last_finalized_task_id"] = task_id
        _spider_state["current_task_id"] = None
        _spider_state["current_task_type"] = None
        _spider_state["current_task"] = None
        return

    if state == "FAILURE":
        _spider_state["running"] = False
        _spider_state["progress"] = 0
        error_msg = result.get("error", "任务失败")
        _spider_state["message"] = str(error_msg)
        if _spider_state.get("last_finalized_task_id") != task_id:
            _add_history(
                _spider_state.get("current_task") or "爬虫任务",
                "error",
                f"task_id={task_id}: {error_msg}",
                0,
            )
            _spider_state["last_finalized_task_id"] = task_id
        _spider_state["current_task_id"] = None
        _spider_state["current_task_type"] = None
        _spider_state["current_task"] = None


@spider_bp.route("/overview", methods=["GET"])
@admin_required
def spider_overview():
    """
    获取爬虫概览数据：文章/评论/用户总数、最近文章时间等
    """
    try:
        _refresh_task_state()
        from utils.query import query_dataframe, querys

        # 统计各表数量
        article_count = 0
        comment_count = 0
        user_count = 0
        latest_article_time = "暂无数据"
        latest_comment_time = "暂无数据"

        try:
            result = querys("SELECT COUNT(*) as cnt FROM article", [], "select")
            if result:
                article_count = (
                    result[0][0]
                    if isinstance(result[0], (list, tuple))
                    else result[0].get("cnt", 0)
                )
        except Exception as e:
            logger.debug("查询 article 数量失败: %s", e)

        try:
            result = querys("SELECT COUNT(*) as cnt FROM comments", [], "select")
            if result:
                comment_count = (
                    result[0][0]
                    if isinstance(result[0], (list, tuple))
                    else result[0].get("cnt", 0)
                )
        except Exception as e:
            logger.debug("查询 comments 数量失败: %s", e)

        try:
            result = querys("SELECT COUNT(*) as cnt FROM user", [], "select")
            if result:
                user_count = (
                    result[0][0]
                    if isinstance(result[0], (list, tuple))
                    else result[0].get("cnt", 0)
                )
        except Exception as e:
            logger.debug("查询 user 数量失败: %s", e)

        try:
            result = querys(
                "SELECT MAX(created_at) as latest FROM article", [], "select"
            )
            if result and result[0]:
                val = (
                    result[0][0]
                    if isinstance(result[0], (list, tuple))
                    else result[0].get("latest", "")
                )
                if val:
                    latest_article_time = str(val)
        except Exception as e:
            logger.debug("查询 article 最新时间失败: %s", e)

        try:
            result = querys(
                "SELECT MAX(created_at) as latest FROM comments", [], "select"
            )
            if result and result[0]:
                val = (
                    result[0][0]
                    if isinstance(result[0], (list, tuple))
                    else result[0].get("latest", "")
                )
                if val:
                    latest_comment_time = str(val)
        except Exception as e:
            logger.debug("查询 comments 最新时间失败: %s", e)

        # 获取每日文章数趋势（最近 7 天）
        daily_trend = []
        try:
            df = query_dataframe("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM article
                WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    daily_trend.append(
                        {
                            "date": str(row["date"]),
                            "count": int(row["count"]),
                        }
                    )
        except Exception as e:
            logger.debug("查询每日文章趋势失败: %s", e)

        # 获取每日评论数趋势
        comment_trend = []
        try:
            df = query_dataframe("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM comments
                WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    comment_trend.append(
                        {
                            "date": str(row["date"]),
                            "count": int(row["count"]),
                        }
                    )
        except Exception as e:
            logger.debug("查询每日评论趋势失败: %s", e)

        return ok(
            {
                "articleCount": article_count,
                "commentCount": comment_count,
                "userCount": user_count,
                "latestArticleTime": latest_article_time,
                "latestCommentTime": latest_comment_time,
                "isRunning": _spider_state["running"],
                "currentTask": _spider_state["current_task"],
                "currentTaskId": _spider_state["current_task_id"],
                "progress": _spider_state["progress"],
                "message": _spider_state["message"],
                "dailyTrend": daily_trend,
                "commentTrend": comment_trend,
                "history": _spider_state["history"][:20],
            }
        ), 200

    except Exception as e:
        logger.error(f"获取爬虫概览失败: {e}")
        return error(f"获取概览失败: {e}", code=500), 500


@spider_bp.route("/crawl", methods=["POST"])
@admin_required
def spider_crawl():
    """
    触发异步爬取任务（统一通过 Celery 编排）
    Body:
        type: 'hot' | 'search' | 'comments'
        keyword: 搜索关键词（type=search 时必填）
        pageNum: 爬取页数（默认 3）
    """
    _refresh_task_state()

    with _spider_lock:
        if _spider_state["running"]:
            return ok(
                {
                    "currentTask": _spider_state["current_task"],
                    "progress": _spider_state["progress"],
                    "task_id": _spider_state["current_task_id"],
                },
                msg="已有爬虫任务正在运行，请等待完成",
                code=409,
            ), 409

    data = request.json or {}
    crawl_type = data.get("type", "hot")
    keyword = data.get("keyword", "")
    page_num = data.get("pageNum", 3)
    article_limit = data.get("article_limit", 50)

    try:
        dispatch_result = dispatch_spider_task(
            crawl_type=crawl_type,
            keyword=keyword,
            page_num=page_num,
            article_limit=article_limit,
        )
    except ValueError as ve:
        return error(str(ve), code=400), 400
    except Exception as e:
        logger.error(f"提交爬虫任务失败: {e}")
        return error("任务提交失败", code=500), 500

    register_submitted_task(dispatch_result)

    return ok(
        {
            "type": dispatch_result["crawl_type"],
            "keyword": dispatch_result["keyword"],
            "pageNum": dispatch_result["page_num"],
            "article_limit": dispatch_result["article_limit"],
            "task_id": dispatch_result["task_id"],
            "check_url": f"/api/tasks/{dispatch_result['task_id']}/status",
        },
        msg=f"爬虫任务已提交: {dispatch_result['task_label']}",
    ), 200


@spider_bp.route("/logs", methods=["GET"])
@admin_required
def spider_logs():
    """获取爬虫运行日志（读取日志文件最近 N 行）"""
    lines_num = min(int(request.args.get("lines", 100)), 500)

    log_paths = [
        os.path.join(Config.LOG_DIR, "app.log"),
        os.path.join(Config.BASE_DIR, "spider", "weibo_spider.log"),
    ]

    log_lines = []
    for lp in log_paths:
        if os.path.exists(lp):
            try:
                with open(lp, encoding="utf-8", errors="ignore") as f:
                    all_lines = f.readlines()
                    # 取最后 lines_num 行
                    tail = all_lines[-lines_num:]
                    for line in tail:
                        line = line.strip()
                        if line:
                            log_lines.append(line)
            except Exception as e:
                log_lines.append(f"[读取日志失败: {lp}] {e}")

    # 按时间倒序（最新在前）
    log_lines.reverse()

    return ok({"logs": log_lines[:lines_num], "total": len(log_lines)}), 200


@spider_bp.route("/status", methods=["GET"])
@admin_required
def spider_status():
    """获取当前爬虫运行状态"""
    _refresh_task_state()
    return ok(
        {
            "isRunning": _spider_state["running"],
            "currentTask": _spider_state["current_task"],
            "currentTaskId": _spider_state["current_task_id"],
            "progress": _spider_state["progress"],
            "message": _spider_state["message"],
        }
    ), 200


# ========== 爬取实现函数 ==========


def _crawl_hot(page_num=3):
    """同步爬取热门微博并导入数据库"""
    import random

    import requests as req

    from utils.query import querys

    cookie = os.getenv("WEIBO_COOKIE", "")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": cookie,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://weibo.com/",
    }

    articles = []
    for page in range(page_num):
        _spider_state["progress"] = int((page / page_num) * 80)
        _spider_state["message"] = f"正在爬取第 {page + 1}/{page_num} 页..."

        url = "https://weibo.com/ajax/feed/hottimeline"
        params = {"group_id": 102803, "max_id": 0, "count": 20, "refresh_type": 1}

        try:
            response = req.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                result = response.json()
                if "statuses" in result:
                    for item in result["statuses"]:
                        user = item.get("user", {}) or {}
                        articles.append(
                            {
                                "id": item.get("id", ""),
                                "likeNum": item.get("attitudes_count", 0),
                                "commentsLen": item.get("comments_count", 0),
                                "reposts_count": item.get("reposts_count", 0),
                                "region": (item.get("region_name", "") or "无").replace(
                                    "发布于 ", ""
                                )[:50],
                                "content": item.get("text_raw", "")[:2000],
                                "contentLen": item.get("textLength", 0),
                                "created_at": datetime.now().strftime("%Y-%m-%d"),
                                "type": "热门",
                                "detailUrl": f"https://weibo.com/{user.get('id', '')}/{item.get('mblogid', '')}",
                                "authorAvatar": user.get("avatar_large", "")[:500],
                                "authorName": user.get("screen_name", "")[:100],
                                "authorDetail": f"https://weibo.com/u/{user.get('id', '')}",
                                "isVip": user.get("v_plus", 0),
                            }
                        )
        except Exception as e:
            logger.warning(f"爬取第{page + 1}页失败: {e}")
        time.sleep(random.uniform(0.5, 1))

    _spider_state["progress"] = 85
    _spider_state["message"] = "正在导入数据库..."

    imported = 0
    for a in articles:
        try:
            sql = """INSERT INTO article
                (id, likeNum, commentsLen, reposts_count, region, content,
                 contentLen, created_at, type, detailUrl, authorAvatar,
                 authorName, authorDetail, isVip)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                likeNum=VALUES(likeNum), commentsLen=VALUES(commentsLen)"""
            querys(
                sql,
                [
                    a["id"],
                    a["likeNum"],
                    a["commentsLen"],
                    a["reposts_count"],
                    a["region"],
                    a["content"],
                    a["contentLen"],
                    a["created_at"],
                    a["type"],
                    a["detailUrl"],
                    a["authorAvatar"],
                    a["authorName"],
                    a["authorDetail"],
                    a["isVip"],
                ],
            )
            imported += 1
        except Exception as e:
            logger.warning(f"导入文章失败: {e}")

    # 清除缓存
    try:
        from utils.cache import clear_cache

        clear_cache()
    except Exception as e:
        logger.debug("清除缓存失败: %s", e)

    logger.info(f"热门微博刷新完成: 爬取{len(articles)}条, 导入{imported}条")
    return imported


def _crawl_search(keyword, page_num=3):
    """同步关键词搜索爬取"""
    import random

    import requests as req

    from utils.query import querys

    cookie = os.getenv("WEIBO_COOKIE", "")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": cookie,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://weibo.com/",
    }

    articles = []
    for page in range(1, page_num + 1):
        _spider_state["progress"] = int((page / page_num) * 80)
        _spider_state["message"] = f'正在搜索 "{keyword}" 第 {page}/{page_num} 页...'

        # 搜索 API
        search_url = "https://weibo.com/ajax/statuses/searchResult"
        params = {"q": keyword, "page": page, "count": 20}

        try:
            response = req.get(search_url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                result = response.json()
                statuses = (
                    result.get("data", {}).get("statuses", [])
                    if isinstance(result.get("data"), dict)
                    else []
                )
                for item in statuses:
                    user = item.get("user", {}) or {}
                    articles.append(
                        {
                            "id": item.get("id", ""),
                            "likeNum": item.get("attitudes_count", 0),
                            "commentsLen": item.get("comments_count", 0),
                            "reposts_count": item.get("reposts_count", 0),
                            "region": (item.get("region_name", "") or "无").replace(
                                "发布于 ", ""
                            )[:50],
                            "content": item.get("text_raw", "")[:2000],
                            "contentLen": item.get("textLength", 0),
                            "created_at": datetime.now().strftime("%Y-%m-%d"),
                            "type": f"搜索:{keyword}",
                            "detailUrl": f"https://weibo.com/{user.get('id', '')}/{item.get('mblogid', '')}",
                            "authorAvatar": user.get("avatar_large", "")[:500],
                            "authorName": user.get("screen_name", "")[:100],
                            "authorDetail": f"https://weibo.com/u/{user.get('id', '')}",
                            "isVip": user.get("v_plus", 0),
                        }
                    )
        except Exception as e:
            logger.warning(f"搜索第{page}页失败: {e}")
        time.sleep(random.uniform(1, 2))

    _spider_state["progress"] = 85
    _spider_state["message"] = "正在导入数据库..."

    imported = 0
    for a in articles:
        try:
            sql = """INSERT INTO article
                (id, likeNum, commentsLen, reposts_count, region, content,
                 contentLen, created_at, type, detailUrl, authorAvatar,
                 authorName, authorDetail, isVip)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                likeNum=VALUES(likeNum), commentsLen=VALUES(commentsLen)"""
            querys(
                sql,
                [
                    a["id"],
                    a["likeNum"],
                    a["commentsLen"],
                    a["reposts_count"],
                    a["region"],
                    a["content"],
                    a["contentLen"],
                    a["created_at"],
                    a["type"],
                    a["detailUrl"],
                    a["authorAvatar"],
                    a["authorName"],
                    a["authorDetail"],
                    a["isVip"],
                ],
            )
            imported += 1
        except Exception as e:
            logger.warning(f"导入搜索文章失败: {e}")

    try:
        from utils.cache import clear_cache

        clear_cache()
    except Exception as e:
        logger.debug("清除缓存失败: %s", e)

    logger.info(f"关键词搜索完成 [{keyword}]: 爬取{len(articles)}条, 导入{imported}条")
    return imported


def _crawl_comments():
    """同步爬取评论"""
    _spider_state["progress"] = 10
    _spider_state["message"] = "正在获取待爬取文章列表..."

    try:
        from utils.query import querys

        # 获取最近的文章 ID
        articles = querys(
            "SELECT id FROM article ORDER BY created_at DESC LIMIT 20", [], "select"
        )
        if not articles:
            logger.warning("没有文章可爬取评论")
            return 0

        import random

        import requests as req

        cookie = os.getenv("WEIBO_COOKIE", "")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": cookie,
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://weibo.com/",
        }

        total_imported = 0
        for idx, article in enumerate(articles):
            aid = (
                article[0]
                if isinstance(article, (list, tuple))
                else article.get("id", "")
            )
            _spider_state["progress"] = int(10 + (idx / len(articles)) * 70)
            _spider_state["message"] = (
                f"正在爬取文章 {idx + 1}/{len(articles)} 的评论..."
            )

            url = "https://weibo.com/ajax/statuses/buildComments"
            params = {"id": aid, "is_show_bulletin": 2, "count": 20}

            try:
                response = req.get(url, headers=headers, params=params, timeout=15)
                if response.status_code == 200:
                    result = response.json()
                    comments = (
                        result.get("data", [])
                        if isinstance(result.get("data"), list)
                        else []
                    )
                    for c in comments:
                        c_user = c.get("user", {}) or {}
                        try:
                            sql = """INSERT IGNORE INTO comments
                                (articleId, created_at, like_counts, region, content,
                                 authorName, authorGender, authorAddress, authorAvatar)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                            querys(
                                sql,
                                [
                                    str(aid),
                                    c.get("created_at", "")[:50],
                                    c.get("like_counts", 0),
                                    (c.get("source", "") or "无")[:50],
                                    (c.get("text_raw", "") or "")[:2000],
                                    c_user.get("screen_name", "")[:100],
                                    c_user.get("gender", "unknown")[:10],
                                    (c_user.get("location", "") or "")[:200],
                                    c_user.get("avatar_large", "")[:500],
                                ],
                            )
                            total_imported += 1
                        except Exception as e:
                            logger.warning(f"导入评论失败: {e}")
            except Exception as e:
                logger.warning(f"爬取文章 {aid} 评论失败: {e}")

            time.sleep(random.uniform(0.5, 1.5))

        try:
            from utils.cache import clear_cache

            clear_cache()
        except Exception as e:
            logger.debug("清除缓存失败: %s", e)

        logger.info(f"评论爬取完成: 导入{total_imported}条")
        return total_imported

    except Exception as e:
        logger.error(f"评论爬取失败: {e}")
        raise
