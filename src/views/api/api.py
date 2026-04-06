#!/usr/bin/env python3
"""
API路由模块
功能：提供RESTful API接口
特性：分页查询、情感分析、参数验证、限流保护
作者：微博舆情分析系统
"""

import logging

from flask import Blueprint, request

from config.settings import Config
from repositories.user_repository import UserRepository
from services.article_service import ArticleService
from services.audit_service import audit_log
from services.auth_service import AuthService
from services.comment_service import CommentService
from services.nlp_task_service import (
    analyze_batch,
    analyze_text,
    submit_analyze_task,
    submit_retrain_task,
)
from services.task_status_service import query_task_progress
from utils.api_response import error, ok
from utils.authz import admin_required, is_admin_user
from utils.input_validator import sanitize_input, validate_password, validate_username
from utils.log_sanitizer import SafeLogger
from utils.rate_limiter import rate_limit

logger = SafeLogger("api", logging.INFO)
article_service = ArticleService()
auth_service = AuthService()
comment_service = CommentService()
user_repo = UserRepository()

bp = Blueprint("api", __name__, url_prefix="/api")


def _cookie_secure() -> bool:
    return Config.FLASK_ENV == "production"


def _cookie_samesite() -> str:
    return "Strict" if _cookie_secure() else "Lax"


def _set_auth_cookie(response, token: str) -> None:
    response.set_cookie(
        Config.AUTH_COOKIE_NAME,
        token,
        max_age=Config.JWT_EXPIRATION_HOURS * 3600,
        httponly=True,
        secure=_cookie_secure(),
        samesite=_cookie_samesite(),
        path="/",
    )


def _clear_auth_cookie(response) -> None:
    response.delete_cookie(
        Config.AUTH_COOKIE_NAME,
        path="/",
    )


@bp.route("/auth/login", methods=["POST"])
@rate_limit(
    max_requests=10, window_seconds=60, error_message="登录请求过于频繁，请稍后再试"
)
def api_login():
    try:
        data = request.get_json(silent=True) or {}
        username_raw = (data.get("username") or "").strip()
        password_raw = (data.get("password") or "").strip()

        username_validation = validate_username(username_raw)
        if not username_validation["valid"]:
            return error(username_validation["message"], code=400), 400

        password_validation = validate_password(password_raw)
        if not password_validation["valid"]:
            return error(password_validation["message"], code=400), 400

        username = sanitize_input(username_raw, max_length=20)
        success, msg, payload = auth_service.login(username, password_raw)
        if success:
            user_data = payload.get("user", {})
            audit_log(
                user_data.get("id"), username, "login", "登录成功", request.remote_addr
            )
            response = ok(payload, msg=msg)
            token = payload.get("token")
            if token:
                _set_auth_cookie(response, token)
            response.status_code = 200
            return response
        audit_log(None, username, "login_failed", "登录失败", request.remote_addr)
        return error(msg, code=401), 401
    except Exception as e:
        logger.error(f"API登录异常: {e}")
        return error("服务器内部错误", code=500), 500


@bp.route("/auth/register", methods=["POST"])
@rate_limit(
    max_requests=5, window_seconds=60, error_message="注册请求过于频繁，请稍后再试"
)
def api_register():
    try:
        data = request.get_json(silent=True) or {}
        username_raw = (data.get("username") or "").strip()
        password_raw = (data.get("password") or "").strip()
        confirm_raw = (
            data.get("confirmPassword") or data.get("passwordCheked") or ""
        ).strip()

        username_validation = validate_username(username_raw)
        if not username_validation["valid"]:
            return error(username_validation["message"], code=400), 400

        password_validation = validate_password(password_raw)
        if not password_validation["valid"]:
            return error(password_validation["message"], code=400), 400

        username = sanitize_input(username_raw, max_length=20)
        success, msg = auth_service.register(username, password_raw, confirm_raw)
        if success:
            audit_log(None, username, "register", "注册成功", request.remote_addr)
            return ok(msg=msg), 200
        return error(msg, code=400), 400
    except Exception as e:
        logger.error(f"API注册异常: {e}")
        return error("服务器内部错误", code=500), 500


@bp.route("/auth/me", methods=["GET"])
def api_me():
    user = getattr(request, "current_user", None)
    if not user:
        return error("未认证", code=401), 401
    try:
        info = user_repo.find_by_id(user["user_id"])
        if not info:
            return error("用户不存在", code=404), 404
        return ok(
            {
                "id": info.get("id"),
                "username": info.get("username"),
                "nickname": info.get("nickname") or info.get("username"),
                "email": info.get("email", ""),
                "bio": info.get("bio", ""),
                "avatar_color": info.get("avatar_color", "#2563EB"),
                "create_time": str(info.get("create_time", "")),
                "is_admin": is_admin_user(info),
            }
        ), 200
    except Exception as e:
        logger.error(f"获取当前用户信息异常: {e}")
        return error("服务器内部错误", code=500), 500


@bp.route("/auth/logout", methods=["POST"])
def api_logout():
    response = ok()
    _clear_auth_cookie(response)
    response.status_code = 200
    return response


@bp.route("/user/profile", methods=["GET"])
def get_user_profile():
    """获取用户完整个人资料"""
    user = getattr(request, "current_user", None)
    if not user:
        return error("未认证", code=401), 401
    try:
        info = user_repo.find_by_id(user["user_id"])
        if not info:
            return error("用户不存在", code=404), 404
        return ok(
            {
                "id": info.get("id"),
                "username": info.get("username"),
                "nickname": info.get("nickname") or "",
                "email": info.get("email") or "",
                "bio": info.get("bio") or "",
                "avatar_color": info.get("avatar_color") or "#2563EB",
                "create_time": str(info.get("create_time", "")),
                "is_admin": is_admin_user(info),
            }
        ), 200
    except Exception as e:
        logger.error(f"获取用户资料异常: {e}")
        return error("服务器内部错误", code=500), 500


@bp.route("/user/profile", methods=["PUT"])
def update_user_profile():
    """更新用户个人资料"""
    user = getattr(request, "current_user", None)
    if not user:
        return error("未认证", code=401), 401
    try:
        data = request.get_json(silent=True) or {}
        updates = {}

        nickname = data.get("nickname")
        if nickname is not None:
            nickname = str(nickname).strip()[:50]
            updates["nickname"] = nickname

        email = data.get("email")
        if email is not None:
            email = str(email).strip()[:100]
            if email and "@" not in email:
                return error("邮箱格式不正确", code=400), 400
            updates["email"] = email

        bio = data.get("bio")
        if bio is not None:
            updates["bio"] = str(bio).strip()[:200]

        avatar_color = data.get("avatar_color")
        if avatar_color is not None:
            avatar_color = str(avatar_color).strip()
            if len(avatar_color) == 7 and avatar_color.startswith("#"):
                updates["avatar_color"] = avatar_color

        if not updates:
            return error("没有需要更新的字段", code=400), 400

        success = user_repo.update_profile(user["user_id"], **updates)
        if success:
            return ok(msg="资料更新成功"), 200
        return error("更新失败", code=500), 500
    except Exception as e:
        logger.error(f"更新用户资料异常: {e}")
        return error("服务器内部错误", code=500), 500


@bp.route("/user/password", methods=["PUT"])
def change_user_password():
    """修改用户密码"""
    user = getattr(request, "current_user", None)
    if not user:
        return error("未认证", code=401), 401
    try:
        data = request.get_json(silent=True) or {}
        old_password = (data.get("oldPassword") or "").strip()
        new_password = (data.get("newPassword") or "").strip()
        confirm_password = (data.get("confirmPassword") or "").strip()

        if not old_password or not new_password:
            return error("请填写完整的密码信息", code=400), 400

        if new_password != confirm_password:
            return error("两次输入的新密码不一致", code=400), 400

        password_validation = validate_password(new_password)
        if not password_validation["valid"]:
            return error(password_validation["message"], code=400), 400

        # Verify old password
        from utils.password_hasher import hash_password, verify_password

        info = user_repo.find_by_id(user["user_id"])
        if not info:
            return error("用户不存在", code=404), 404

        if not verify_password(old_password, info.get("password", "")):
            return error("旧密码不正确", code=400), 400

        new_hash = hash_password(new_password)
        success = user_repo.update_password(user["user_id"], new_hash)
        if success:
            logger.info(f"User {user['user_id']} changed password")
            audit_log(
                user["user_id"],
                info.get("username", ""),
                "change_password",
                "密码修改成功",
                request.remote_addr,
            )
            return ok(msg="密码修改成功"), 200
        return error("密码修改失败", code=500), 500
    except Exception as e:
        logger.error(f"修改密码异常: {e}")
        return error("服务器内部错误", code=500), 500


@bp.route("/stats/summary", methods=["GET"])
def get_stats_summary():
    """获取系统统计概览"""
    try:
        data = article_service.get_stats_summary()
        return ok(data), 200
    except Exception as e:
        logger.error(f"获取统计摘要失败: {e}")
        return error("获取统计数据失败，请稍后重试", code=500), 500


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
        page = int(request.args.get("page", 1))
        limit = min(int(request.args.get("limit", 10)), 100)  # 限制最大100条
        keyword = request.args.get("keyword", "")
        start_time = request.args.get("start_time", "")
        end_time = request.args.get("end_time", "")
        article_type = request.args.get("type", "")
        region = request.args.get("region", "")

        # 参数校验：关键词长度和SQL注入检测
        if keyword or article_type or region:
            from utils.input_validator import detect_sql_injection, validate_keyword

            if keyword:
                validation = validate_keyword(keyword)
                if not validation["valid"]:
                    return error(validation["message"], code=400), 400
                if detect_sql_injection(keyword):
                    logger.warning(f"检测到SQL注入尝试: keyword={keyword[:50]}")
                    return error("关键词包含非法字符", code=400), 400

            if article_type:
                validation = validate_keyword(article_type)
                if not validation["valid"]:
                    return error(validation["message"], code=400), 400
                if detect_sql_injection(article_type):
                    logger.warning(f"检测到SQL注入尝试: type={article_type[:50]}")
                    return error("类型包含非法字符", code=400), 400

            if region:
                validation = validate_keyword(region)
                if not validation["valid"]:
                    return error(validation["message"], code=400), 400
                if detect_sql_injection(region):
                    logger.warning(f"检测到SQL注入尝试: region={region[:50]}")
                    return error("地区包含非法字符", code=400), 400

        # 参数校验：时间格式
        if start_time or end_time:
            import re

            time_pattern = r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$"
            if start_time and not re.match(time_pattern, start_time):
                return error(
                    "开始时间格式错误（应为YYYY-MM-DD或YYYY-MM-DD HH:MM:SS）", code=400
                ), 400
            if end_time and not re.match(time_pattern, end_time):
                return error(
                    "结束时间格式错误（应为YYYY-MM-DD或YYYY-MM-DD HH:MM:SS）", code=400
                ), 400

        result = article_service.get_articles(
            page, limit, keyword, start_time, end_time, article_type, region
        )

        return ok(result), 200

    except Exception as e:
        return error(str(e), code=500), 500


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
        page = int(request.args.get("page", 1))
        limit = min(int(request.args.get("limit", 10)), 100)
        keyword = request.args.get("keyword", "")
        article_id = request.args.get("article_id", "")
        user = request.args.get("user", "")
        start_time = request.args.get("start_time", "")
        end_time = request.args.get("end_time", "")

        if keyword or user:
            from utils.input_validator import detect_sql_injection, validate_keyword

            if keyword:
                validation = validate_keyword(keyword)
                if not validation["valid"]:
                    return error(validation["message"], code=400), 400
                if detect_sql_injection(keyword):
                    logger.warning(f"检测到SQL注入尝试: keyword={keyword[:50]}")
                    return error("关键词包含非法字符", code=400), 400

            if user:
                validation = validate_keyword(user)
                if not validation["valid"]:
                    return error(validation["message"], code=400), 400
                if detect_sql_injection(user):
                    logger.warning(f"检测到SQL注入尝试: user={user[:50]}")
                    return error("用户名包含非法字符", code=400), 400

        if start_time or end_time:
            import re

            time_pattern = r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$"
            if start_time and not re.match(time_pattern, start_time):
                return error(
                    "开始时间格式错误（应为YYYY-MM-DD或YYYY-MM-DD HH:MM:SS）", code=400
                ), 400
            if end_time and not re.match(time_pattern, end_time):
                return error(
                    "结束时间格式错误（应为YYYY-MM-DD或YYYY-MM-DD HH:MM:SS）", code=400
                ), 400

        result = comment_service.get_comments(
            page, limit, keyword, article_id, user, start_time, end_time
        )
        return ok(result), 200
    except Exception as e:
        return error(str(e), code=500), 500


@bp.route("/sentiment/analyze", methods=["POST"])
@rate_limit(
    max_requests=30, window_seconds=60, error_message="情感分析请求过于频繁，请稍后再试"
)
def analyze_sentiment():
    """
    文本情感分析接口
    Body:
        text: 待分析文本
        mode: 分析模式 (simple/smart)，默认 simple
        async: 是否异步执行（默认false）
    """
    try:
        data = request.json
        text = data.get("text", "")
        mode = data.get("mode", "simple")
        is_async = data.get("async", False)

        if not text:
            return error("text is required", code=400), 400

        # 参数校验
        from utils.input_validator import validate_keyword

        validation = validate_keyword(text[:50])  # 只校验前50字符
        if not validation["valid"]:
            return error(validation["message"], code=400), 400

        # 异步模式
        if is_async:
            dispatch_result = submit_analyze_task(text=text, mode=mode)
            return ok(
                {
                    "task_id": dispatch_result["task_id"],
                    "status": dispatch_result.get("status", "PENDING"),
                    "check_url": f"/api/tasks/{dispatch_result['task_id']}/status",
                },
                msg="任务已提交",
                code=202,
            ), 202

        # 同步模式
        result = analyze_text(text=text, mode=mode)

        return ok(result), 200

    except Exception as e:
        logger.error(f"情感分析接口异常: {e}")
        return error("服务器内部错误", code=500), 500


@bp.route("/predict/batch", methods=["POST"])
@rate_limit(
    max_requests=10, window_seconds=60, error_message="批量预测请求过于频繁，请稍后再试"
)
def predict_batch():
    """
    批量文本情感分析接口
    Body:
        texts: 待分析文本列表
        mode: 分析模式 (simple/smart/custom)，默认 custom
    """
    try:
        data = request.json
        texts = data.get("texts", [])
        mode = data.get("mode", "custom")

        if not texts or not isinstance(texts, list):
            return error("texts 必须是非空数组", code=400), 400

        if len(texts) > 100:
            return error("单次最多预测100条文本", code=400), 400

        results = analyze_batch(texts=texts, mode=mode)

        return ok({"total": len(results), "results": results}), 200

    except Exception as e:
        logger.error(f"批量预测接口异常: {e}")
        return error("服务器内部错误", code=500), 500


@bp.route("/model/info", methods=["GET"])
def get_model_info():
    """
    获取模型信息接口
    """
    try:
        import json
        import os
        from pathlib import Path

        model_dir = Path(Config.BASE_DIR) / "model"
        model_path = model_dir / "best_sentiment_model.pkl"

        info = {
            "model_type": "TF-IDF + 分类器",
            "best_model": "NaiveBayes",
            "accuracy": None,
            "f1_score": None,
            "training_samples": None,
            "last_updated": None,
            "model_exists": model_path.exists(),
        }

        if model_path.exists():
            import os.path
            from datetime import datetime

            mtime = os.path.getmtime(model_path)
            info["last_updated"] = datetime.fromtimestamp(mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        summary_path = model_dir / "analysis_summary.json"
        if summary_path.exists():
            try:
                with open(summary_path, encoding="utf-8") as f:
                    summary = json.load(f)
                    info["training_samples"] = summary.get("total_comments")
            except Exception as e:
                logger.debug("读取训练摘要文件失败: %s", e)

        return ok(info), 200

    except Exception as e:
        logger.error(f"获取模型信息异常: {e}")
        return error("服务器内部错误", code=500), 500


@bp.route("/model/retrain", methods=["POST"])
@admin_required
def retrain_model():
    """
    触发模型重训练（异步）
    Body:
        optimize: 是否进行超参数优化
    """
    try:
        data = request.json or {}
        optimize = data.get("optimize", False)

        dispatch_result = submit_retrain_task(optimize=bool(optimize))

        logger.info("模型重训练任务已提交: task_id=%s", dispatch_result["task_id"])

        return ok(
            {
                "task_id": dispatch_result["task_id"],
                "status": dispatch_result.get("status", "PENDING"),
                "check_url": f"/api/tasks/{dispatch_result['task_id']}/status",
            },
            msg="模型重训练任务已提交",
            code=202,
        ), 202

    except Exception as e:
        logger.error(f"模型重训练接口异常: {e}")
        return error("服务器内部错误", code=500), 500


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

    except Exception as e:
        logger.error(f"爬虫接口异常: {e}")
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

    except Exception as e:
        logger.error(f"评论爬虫接口异常: {e}")
        return error("服务器内部错误", code=500), 500


@bp.route("/tasks/<task_id>/status", methods=["GET"])
@admin_required
def get_task_status(task_id):
    """
    查询异步任务状态
    """
    try:
        result = query_task_progress(task_id)

        return ok(result), 200

    except Exception as e:
        logger.error(f"查询任务状态异常: {e}")
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

    except Exception as e:
        logger.error(f"刷新数据异常: {e}")
        return error("服务器内部错误", code=500), 500


@bp.route("/stats/today", methods=["GET"])
def get_today_stats():
    """获取今日数据统计"""
    try:
        return ok(article_service.get_today_stats()), 200
    except Exception as e:
        logger.error(f"获取今日统计失败: {e}")
        return error(str(e), code=500), 500
