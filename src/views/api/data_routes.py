"""数据查询路由 ``/api/stats/*``、``/api/articles``、``/api/comments``。

文章/评论查询参数的构建与校验辅助仅本模块使用，故就近放置。
"""

import re

from flask import request

from utils.api_response import error, ok

from ._shared import article_service, bp, comment_service, logger

_TIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$")


# ---------------------------------------------------------------------------
# Validation helpers (return error tuple or None)
# ---------------------------------------------------------------------------


def _validate_search_param(value, field_label):
    """Validate a single search parameter against injection and keyword rules.

    Returns an error response tuple on failure, or None on success.

    说明：validate_keyword 已内置 SQL 注入检测（纵深防御），此处不再二次
    detect_sql_injection；参数化查询为主，黑名单为辅。
    """
    from utils.input_validator import validate_keyword

    if not value:
        return None

    validation = validate_keyword(value)
    if not validation["valid"]:
        logger.warning("关键词校验失败: %s=%s 原因=%s", field_label, value[:50], validation["message"])
        return error(validation["message"], code=400), 400

    return None


def _validate_time_range(start_time, end_time):
    """Validate start/end time strings.

    Returns an error response tuple on failure, or None on success.
    """
    if start_time and not _TIME_PATTERN.match(start_time):
        return error(
            "开始时间格式错误（应为YYYY-MM-DD或YYYY-MM-DD HH:MM:SS）", code=400
        ), 400

    if end_time and not _TIME_PATTERN.match(end_time):
        return error(
            "结束时间格式错误（应为YYYY-MM-DD或YYYY-MM-DD HH:MM:SS）", code=400
        ), 400

    return None


# ---------------------------------------------------------------------------
# Article / comment helpers
# ---------------------------------------------------------------------------


def _parse_pagination():
    """Extract and clamp page/limit from query string — 收敛到统一 pagination 工具。"""
    from utils.pagination import get_pagination_params

    page, limit, _ = get_pagination_params(request, default_limit=10, max_limit=100)
    return page, limit


def _build_article_query_params():
    """Build and validate all article-list query parameters.

    Returns (params_dict, error_response).  On success error_response is None.
    """
    page, limit = _parse_pagination()
    keyword = request.args.get("keyword", "")
    start_time = request.args.get("start_time", "")
    end_time = request.args.get("end_time", "")
    article_type = request.args.get("type", "")
    region = request.args.get("region", "")

    for field_label, value in [
        ("关键词", keyword),
        ("类型", article_type),
        ("地区", region),
    ]:
        err = _validate_search_param(value, field_label)
        if err is not None:
            return None, err

    err = _validate_time_range(start_time, end_time)
    if err is not None:
        return None, err

    return {
        "page": page,
        "limit": limit,
        "keyword": keyword,
        "start_time": start_time,
        "end_time": end_time,
        "article_type": article_type,
        "region": region,
    }, None


def _format_article_response(params):
    """Fetch and return the article list for validated *params*."""
    result = article_service.get_articles(
        params["page"],
        params["limit"],
        params["keyword"],
        params["start_time"],
        params["end_time"],
        params["article_type"],
        params["region"],
    )
    return ok(result), 200


def _build_comment_query_params():
    """Build and validate all comment-list query parameters.

    Returns (params_dict, error_response).  On success error_response is None.
    """
    page, limit = _parse_pagination()
    keyword = request.args.get("keyword", "")
    article_id = request.args.get("article_id", "")
    user = request.args.get("user", "")
    start_time = request.args.get("start_time", "")
    end_time = request.args.get("end_time", "")

    for field_label, value in [("关键词", keyword), ("用户名", user)]:
        err = _validate_search_param(value, field_label)
        if err is not None:
            return None, err

    err = _validate_time_range(start_time, end_time)
    if err is not None:
        return None, err

    return {
        "page": page,
        "limit": limit,
        "keyword": keyword,
        "article_id": article_id,
        "user": user,
        "start_time": start_time,
        "end_time": end_time,
    }, None


def _format_comment_response(params):
    """Fetch and return the comment list for validated *params*."""
    result = comment_service.get_comments(
        params["page"],
        params["limit"],
        params["keyword"],
        params["article_id"],
        params["user"],
        params["start_time"],
        params["end_time"],
    )
    return ok(result), 200


# ---------------------------------------------------------------------------
# Route handlers – stats
# ---------------------------------------------------------------------------


@bp.route("/stats/summary", methods=["GET"])
def get_stats_summary():
    """获取系统统计概览"""
    try:
        data = article_service.get_stats_summary()
        return ok(data), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("获取统计摘要参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("获取统计摘要服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("获取统计摘要失败: %s", e)
        return error("获取统计数据失败，请稍后重试", code=500), 500


# ---------------------------------------------------------------------------
# Route handlers – articles & comments
# ---------------------------------------------------------------------------


@bp.route("/articles", methods=["GET"])
def get_articles():
    """
    获取文章列表（支持分页、关键词搜索、时间筛选）
    Params:
        page: 页码 (默认1)
        limit: 每页数量 (默认10)
        keyword: 搜索关键词
        start_time: 开始时间
        end_time: 结束时间
    """
    try:
        params, err = _build_article_query_params()
        if err is not None:
            return err
        return _format_article_response(params)
    except (ValueError, KeyError, TypeError) as e:
        return error(f"请求参数错误: {e}", code=400), 400
    except ConnectionError as e:
        logger.error("获取文章列表服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("获取文章列表异常: %s", e)
        return error("服务器内部错误", code=500), 500


@bp.route("/comments", methods=["GET"])
def get_comments():
    """
    获取评论列表（支持分页、关键词搜索、时间筛选）
    Params:
        page: 页码 (默认1)
        limit: 每页数量 (默认10)
        keyword: 搜索关键词（评论内容）
        article_id: 文章ID（rootId）
        user: 评论用户名（模糊匹配）
        start_time: 开始时间
        end_time: 结束时间
    """
    try:
        params, err = _build_comment_query_params()
        if err is not None:
            return err
        return _format_comment_response(params)
    except (ValueError, KeyError, TypeError) as e:
        return error(f"请求参数错误: {e}", code=400), 400
    except ConnectionError as e:
        logger.error("获取评论列表服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("获取评论列表异常: %s", e)
        return error("服务器内部错误", code=500), 500


# ---------------------------------------------------------------------------
# Route handlers – today stats
# ---------------------------------------------------------------------------


@bp.route("/stats/today", methods=["GET"])
def get_today_stats():
    """获取今日数据统计"""
    try:
        return ok(article_service.get_today_stats()), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("获取今日统计参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("获取今日统计服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("获取今日统计失败: %s", e)
        return error(str(e), code=500), 500
