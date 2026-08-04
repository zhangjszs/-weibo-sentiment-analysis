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
from requests import RequestException
from sqlalchemy.exc import SQLAlchemyError

from services.spider_task_service import query_spider_task_progress, submit_spider_task
from utils.api_response import error, ok
from utils.authz import admin_required
from repositories.article_repository import ArticleRepository
from repositories.comment_repository import CommentRepository
from repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

spider_bp = Blueprint("spider_api", __name__, url_prefix="/api/spider")


def _article_repo() -> ArticleRepository:
    return ArticleRepository()


def _comment_repo() -> CommentRepository:
    return CommentRepository()


def _user_repo() -> UserRepository:
    return UserRepository()

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


def _apply_in_progress_state(result: dict, state: str) -> None:
    """Apply PENDING or PROGRESS state to spider state."""
    _spider_state["running"] = True
    progress_meta = result.get("progress", {}) if state == "PROGRESS" else {}
    _spider_state["progress"] = (
        _progress_to_percent(progress_meta) if state == "PROGRESS" else 0
    )
    _spider_state["message"] = (
        progress_meta.get("status") if isinstance(progress_meta, dict) else ""
    ) or result.get("status", "任务执行中...")


def _finalize_task(task_id: str, result: dict, final_status: str) -> None:
    """Record history for a finished task if not already finalized."""
    if _spider_state.get("last_finalized_task_id") == task_id:
        return

    task_label = _spider_state.get("current_task") or "爬虫任务"
    if final_status == "success":
        task_result = result.get("result", {})
        _add_history(
            task_label,
            "success",
            f"task_id={task_id}",
            _extract_result_count(task_result),
        )
    else:
        error_msg = result.get("error", "任务失败")
        _add_history(
            task_label,
            "error",
            f"task_id={task_id}: {error_msg}",
            0,
        )

    _spider_state["last_finalized_task_id"] = task_id


def _clear_current_task() -> None:
    """Clear all current-task fields in spider state."""
    _spider_state["current_task_id"] = None
    _spider_state["current_task_type"] = None
    _spider_state["current_task"] = None


def _apply_success_state(task_id: str, result: dict) -> None:
    """Apply SUCCESS state to spider state."""
    _spider_state["running"] = False
    _spider_state["progress"] = 100
    _spider_state["message"] = "任务完成"
    _finalize_task(task_id, result, "success")
    _clear_current_task()


def _apply_failure_state(task_id: str, result: dict) -> None:
    """Apply FAILURE state to spider state."""
    _spider_state["running"] = False
    _spider_state["progress"] = 0
    _spider_state["message"] = str(result.get("error", "任务失败"))
    _finalize_task(task_id, result, "failure")
    _clear_current_task()


_STATE_HANDLERS = {
    "PENDING": lambda _task_id, result: _apply_in_progress_state(result, "PENDING"),
    "PROGRESS": lambda _task_id, result: _apply_in_progress_state(result, "PROGRESS"),
    "SUCCESS": _apply_success_state,
    "FAILURE": _apply_failure_state,
}


def _refresh_task_state() -> None:
    task_id = _spider_state.get("current_task_id")
    if not task_id:
        return

    try:
        result = query_spider_task_progress(task_id)
    except (RequestException, SQLAlchemyError, OSError) as e:
        logger.warning("查询任务状态失败: task_id=%s, error=%s", task_id, e)
        return

    state = result.get("state")
    handler = _STATE_HANDLERS.get(state)
    if handler:
        handler(task_id, result)


def _query_table_count(table_name: str) -> int:
    """Return the row count for *table_name*, or 0 on failure."""
    try:
        if table_name == "article":
            return _article_repo().count_total()
        elif table_name == "comments":
            return _comment_repo().count_total()
        elif table_name == "user":
            return _user_repo().count_total()
        else:
            return 0
    except Exception as e:
        logger.debug("查询 %s 数量失败: %s", table_name, e)
        return 0


def _query_latest_time(table_name: str, fallback: str = "暂无数据") -> str:
    """Return the latest `created_at` value for *table_name*."""
    try:
        if table_name == "article":
            latest_time = _article_repo().get_latest_update_time()
            return str(latest_time) if latest_time else fallback
        elif table_name == "comments":
            latest_time = _comment_repo().count_by_date_range()
            if latest_time:
                latest_entry = latest_time[-1] if latest_time else None
                return str(latest_entry.get("created_at")) if latest_entry else fallback
            return fallback
        else:
            return fallback
    except Exception as e:
        logger.debug("查询 %s 最新时间失败: %s", table_name, e)
        return fallback


def _query_daily_trend(table_name: str) -> list[dict]:
    """Return the 7-day daily count trend for *table_name*."""
    try:
        if table_name == "article":
            return _article_repo().count_by_date_range()
        elif table_name == "comments":
            return _comment_repo().get_recent_trend(days=7)
        else:
            return []
    except Exception as e:
        logger.debug("查询 %s 每日趋势失败: %s", table_name, e)
        return []


def _build_overview_response() -> dict:
    """Build the full overview payload (DB stats + spider state)."""
    return {
        "articleCount": _query_table_count("article"),
        "commentCount": _query_table_count("comments"),
        "userCount": _query_table_count("user"),
        "latestArticleTime": _query_latest_time("article"),
        "latestCommentTime": _query_latest_time("comments"),
        "isRunning": _spider_state["running"],
        "currentTask": _spider_state["current_task"],
        "currentTaskId": _spider_state["current_task_id"],
        "progress": _spider_state["progress"],
        "message": _spider_state["message"],
        "dailyTrend": _query_daily_trend("article"),
        "commentTrend": _query_daily_trend("comments"),
        "history": _spider_state["history"][:20],
    }


@spider_bp.route("/overview", methods=["GET"])
@admin_required
def spider_overview():
    """获取爬虫概览数据：文章/评论/用户总数、最近文章时间等"""
    try:
        _refresh_task_state()
        return ok(_build_overview_response()), 200
    except SQLAlchemyError as e:
        logger.error("获取爬虫概览失败 (DB): %s", e)
        return error(f"获取概览失败: {e}", code=500), 500
    except OSError as e:
        logger.error("获取爬虫概览失败 (IO): %s", e)
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
    except (RequestException, SQLAlchemyError, OSError, RuntimeError) as e:
        logger.error("提交爬虫任务失败: %s", e)
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
    except (RequestException, SQLAlchemyError, OSError, RuntimeError) as e:
        logger.error("提交快速爬虫任务失败: %s", e)
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


def _read_log_tail(path: str, lines_num: int) -> list[str]:
    """Return the last *lines_num* non-empty lines from *path*."""
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
    except OSError as e:
        return [f"[读取日志失败: {path}] {e}"]

    return [line.strip() for line in all_lines[-lines_num:] if line.strip()]


@spider_bp.route("/logs", methods=["GET"])
@admin_required
def spider_logs():
    """获取爬虫运行日志（读取日志文件最近 N 行）"""
    lines_num = min(int(request.args.get("lines", 100)), 500)

    log_paths = [
        os.path.join(Config.LOG_DIR, "app.log"),
        os.path.join(Config.BASE_DIR, "spider", "weibo_spider.log"),
    ]

    log_lines: list[str] = []
    for lp in log_paths:
        if os.path.exists(lp):
            log_lines.extend(_read_log_tail(lp, lines_num))

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



