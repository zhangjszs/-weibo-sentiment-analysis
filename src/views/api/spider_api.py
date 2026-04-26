#!/usr/bin/env python3
"""
爬虫管理 API
功能：提供爬虫概览、同步爬取、日志查询等接口
"""

import logging
import os
import threading
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


@spider_bp.route("/quick-crawl", methods=["POST"])
def spider_quick_crawl():
    """
    快速爬取接口（所有已登录用户可用）
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
                },
                msg="已有爬虫任务正在运行，请等待完成",
                code=409,
            ), 409

    data = request.json or {}
    crawl_type = data.get("type", "hot")
    keyword = data.get("keyword", "")
    page_num = data.get("pageNum", 3)

    try:
        dispatch_result = dispatch_spider_task(
            crawl_type=crawl_type,
            keyword=keyword,
            page_num=page_num,
        )
    except ValueError as ve:
        return error(str(ve), code=400), 400
    except Exception as e:
        logger.error(f"提交快速爬虫任务失败: {e}")
        return error("任务提交失败", code=500), 500

    register_submitted_task(dispatch_result)

    return ok(
        {
            "type": dispatch_result["crawl_type"],
            "keyword": dispatch_result.get("keyword", ""),
            "task_id": dispatch_result["task_id"],
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



