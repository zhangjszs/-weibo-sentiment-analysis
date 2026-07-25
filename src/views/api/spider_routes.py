"""爬虫任务路由 ``/api/spider/*``、``/api/tasks/<task_id>/status``。

这些路由是 spider_api.py 中 ``dispatch_spider_task`` / ``register_submitted_task``
的薄包装，负责参数校验与 HTTP 响应封装。任务状态查询走 task_status_service。
"""

from flask import request

from services.task_status_service import query_task_progress
from utils.api_response import error, ok
from utils.authz import admin_required

from ._shared import bp, logger


@bp.route("/spider/search", methods=["POST"])
@admin_required
def spider_search():
    """
    触发关键词搜索爬虫（异步）
    Body:
        keyword: 搜索关键词
        page_num: 爬取页数（默认3页）
    """
    try:
        data = request.json or {}
        keyword = data.get("keyword", "")
        page_num = data.get("page_num", 3)

        from utils.input_validator import validate_keyword

        validation = validate_keyword(keyword)
        if not validation["valid"]:
            return error(validation["message"], code=400), 400

        from views.api.spider_api import dispatch_spider_task, register_submitted_task

        dispatch_result = dispatch_spider_task(
            crawl_type="search",
            keyword=keyword,
            page_num=page_num,
        )
        register_submitted_task(dispatch_result)

        return ok(
            {
                "task_id": dispatch_result["task_id"],
                "keyword": dispatch_result["keyword"],
                "page_num": dispatch_result["page_num"],
                "status": "PENDING",
                "check_url": f"/api/tasks/{dispatch_result['task_id']}/status",
            },
            msg="爬虫任务已提交",
        ), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("爬虫参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("爬虫服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("爬虫接口异常: %s", e)
        return error("服务器内部错误", code=500), 500


@bp.route("/spider/comments", methods=["POST"])
@admin_required
def spider_comments():
    """
    触发评论爬虫（异步）
    Body:
        article_limit: 限制爬取的文章数量（默认50）
    """
    try:
        data = request.json or {}
        article_limit = data.get("article_limit", 50)

        from views.api.spider_api import dispatch_spider_task, register_submitted_task

        dispatch_result = dispatch_spider_task(
            crawl_type="comments",
            article_limit=article_limit,
        )
        register_submitted_task(dispatch_result)

        return ok(
            {
                "task_id": dispatch_result["task_id"],
                "article_limit": dispatch_result["article_limit"],
                "status": "PENDING",
                "check_url": f"/api/tasks/{dispatch_result['task_id']}/status",
            },
            msg="评论爬虫任务已提交",
        ), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("评论爬虫参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("评论爬虫服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("评论爬虫接口异常: %s", e)
        return error("服务器内部错误", code=500), 500


@bp.route("/tasks/<task_id>/status", methods=["GET"])
@admin_required
def get_task_status(task_id):
    """查询异步任务状态"""
    try:
        result = query_task_progress(task_id)
        return ok(result), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("查询任务状态参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("查询任务状态服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("查询任务状态异常: %s", e)
        return error("查询失败", code=500), 500


@bp.route("/spider/refresh", methods=["POST"])
@admin_required
def refresh_data():
    """
    同步刷新热门微博数据
    直接爬取最新热门微博并更新数据库
    Body:
        page_num: 爬取页数（默认3页）
    """
    try:
        data = request.json or {}
        page_num = data.get("page_num", 3)

        from views.api.spider_api import dispatch_spider_task, register_submitted_task

        dispatch_result = dispatch_spider_task(
            crawl_type="hot",
            page_num=page_num,
        )
        register_submitted_task(dispatch_result)

        return ok(
            {
                "task_id": dispatch_result["task_id"],
                "pages": dispatch_result["page_num"],
                "status": "PENDING",
                "check_url": f"/api/tasks/{dispatch_result['task_id']}/status",
            },
            msg="刷新任务已提交",
        ), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("刷新数据参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("刷新数据服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("刷新数据异常: %s", e)
        return error("服务器内部错误", code=500), 500
