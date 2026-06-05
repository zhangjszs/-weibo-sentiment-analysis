#!/usr/bin/env python3
"""
API路由模块
功能：提供RESTful API接口
特性：分页查询、情感分析、参数验证、限流保护
作者：微博舆情分析系统
"""

import logging
import re

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

_TIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$")


# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Validation helpers (return error tuple or None)
# ---------------------------------------------------------------------------


def _validate_search_param(value, field_label):
    """Validate a single search parameter against injection and keyword rules.

    Returns an error response tuple on failure, or None on success.
    """
    from utils.input_validator import detect_sql_injection, validate_keyword

    if not value:
        return None

    validation = validate_keyword(value)
    if not validation["valid"]:
        return error(validation["message"], code=400), 400

    if detect_sql_injection(value):
        logger.warning("检测到SQL注入尝试: %s=%s", field_label, value[:50])
        return error(f"{field_label}包含非法字符", code=400), 400

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


def _require_authenticated_user():
    """Return the current user dict or an error response tuple."""
    user = getattr(request, "current_user", None)
    if not user:
        return None, (error("未认证", code=401), 401)
    return user, None


# ---------------------------------------------------------------------------
# Article / comment helpers
# ---------------------------------------------------------------------------


def _parse_pagination():
    """Extract and clamp page/limit from query string."""
    page = int(request.args.get("page", 1))
    limit = min(int(request.args.get("limit", 10)), 100)
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
# Profile / password helpers
# ---------------------------------------------------------------------------


def _validate_email(email):
    """Return True if *email* looks valid, False otherwise."""
    return not email or "@" in email


def _parse_avatar_color(raw):
    """Return a validated avatar_color string or None."""
    color = str(raw).strip()
    if len(color) == 7 and color.startswith("#"):
        return color
    return None


def _parse_profile_updates(data):
    """Extract and validate profile update fields from *data*.

    Returns (updates_dict, error_response).  On success error_response is None.
    """
    updates = {}

    nickname = data.get("nickname")
    if nickname is not None:
        updates["nickname"] = str(nickname).strip()[:50]

    email = data.get("email")
    if email is not None:
        email = str(email).strip()[:100]
        if not _validate_email(email):
            return None, (error("邮箱格式不正确", code=400), 400)
        updates["email"] = email

    bio = data.get("bio")
    if bio is not None:
        updates["bio"] = str(bio).strip()[:200]

    avatar_color = data.get("avatar_color")
    if avatar_color is not None:
        parsed = _parse_avatar_color(avatar_color)
        if parsed is not None:
            updates["avatar_color"] = parsed

    if not updates:
        return None, error("没有需要更新的字段", code=400), 400

    return updates, None


def _save_profile_updates(user_id, updates):
    """Persist profile *updates* and return the appropriate response."""
    success = user_repo.update_profile(user_id, **updates)
    if success:
        return ok(msg="资料更新成功"), 200
    return error("更新失败", code=500), 500


def _parse_password_change_data(data):
    """Extract and validate password-change inputs from *data*.

    Returns ((old_pw, new_pw), error_response).  On success error_response is None.
    """
    old_password = (data.get("oldPassword") or "").strip()
    new_password = (data.get("newPassword") or "").strip()
    confirm_password = (data.get("confirmPassword") or "").strip()

    if not old_password or not new_password:
        return None, error("请填写完整的密码信息", code=400), 400

    if new_password != confirm_password:
        return None, error("两次输入的新密码不一致", code=400), 400

    validation = validate_password(new_password)
    if not validation["valid"]:
        return None, error(validation["message"], code=400), 400

    return (old_password, new_password), None


def _execute_password_change(user, old_password, new_password):
    """Verify old password, hash new one, persist, and audit.

    Returns a response tuple.
    """
    from utils.password_hasher import hash_password, verify_password

    info = user_repo.find_by_id(user["user_id"])
    if not info:
        return error("用户不存在", code=404), 404

    if not verify_password(old_password, info.get("password", "")):
        return error("旧密码不正确", code=400), 400

    new_hash = hash_password(new_password)
    success = user_repo.update_password(user["user_id"], new_hash)
    if not success:
        return error("密码修改失败", code=500), 500

    logger.info("User %s changed password", user["user_id"])
    audit_log(
        user["user_id"],
        info.get("username", ""),
        "change_password",
        "密码修改成功",
        request.remote_addr,
    )
    return ok(msg="密码修改成功"), 200


# ---------------------------------------------------------------------------
# Route handlers – auth
# ---------------------------------------------------------------------------


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
    except (ValueError, KeyError, TypeError) as e:
        logger.error("API登录参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("API登录服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("API登录异常: %s", e)
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
    except (ValueError, KeyError, TypeError) as e:
        logger.error("API注册参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("API注册服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("API注册异常: %s", e)
        return error("服务器内部错误", code=500), 500


@bp.route("/auth/me", methods=["GET"])
def api_me():
    user, err = _require_authenticated_user()
    if err is not None:
        return err

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
    except (ValueError, KeyError, TypeError) as e:
        logger.error("获取当前用户信息参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("获取当前用户信息服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("获取当前用户信息异常: %s", e)
        return error("服务器内部错误", code=500), 500


@bp.route("/auth/logout", methods=["POST"])
def api_logout():
    response = ok()
    _clear_auth_cookie(response)
    response.status_code = 200
    return response


# ---------------------------------------------------------------------------
# Route handlers – user profile & password
# ---------------------------------------------------------------------------


@bp.route("/user/profile", methods=["GET"])
def get_user_profile():
    """获取用户完整个人资料"""
    user, err = _require_authenticated_user()
    if err is not None:
        return err

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
    except (ValueError, KeyError, TypeError) as e:
        logger.error("获取用户资料参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("获取用户资料服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("获取用户资料异常: %s", e)
        return error("服务器内部错误", code=500), 500


@bp.route("/user/profile", methods=["PUT"])
def update_user_profile():
    """更新用户个人资料"""
    user, err = _require_authenticated_user()
    if err is not None:
        return err

    try:
        data = request.get_json(silent=True) or {}
        updates, err = _parse_profile_updates(data)
        if err is not None:
            return err
        return _save_profile_updates(user["user_id"], updates)
    except (ValueError, KeyError, TypeError) as e:
        logger.error("更新用户资料参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("更新用户资料服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("更新用户资料异常: %s", e)
        return error("服务器内部错误", code=500), 500


@bp.route("/user/password", methods=["PUT"])
def change_user_password():
    """修改用户密码"""
    user, err = _require_authenticated_user()
    if err is not None:
        return err

    try:
        data = request.get_json(silent=True) or {}
        creds, err = _parse_password_change_data(data)
        if err is not None:
            return err

        old_password, new_password = creds
        return _execute_password_change(user, old_password, new_password)
    except (ValueError, KeyError, TypeError) as e:
        logger.error("修改密码参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("修改密码服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("修改密码异常: %s", e)
        return error("服务器内部错误", code=500), 500


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
# Route handlers – sentiment analysis
# ---------------------------------------------------------------------------


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

        from utils.input_validator import validate_keyword

        validation = validate_keyword(text[:50])  # 只校验前50字符
        if not validation["valid"]:
            return error(validation["message"], code=400), 400

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

        result = analyze_text(text=text, mode=mode)
        return ok(result), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("情感分析参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("情感分析服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("情感分析接口异常: %s", e)
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
    except (ValueError, KeyError, TypeError) as e:
        logger.error("批量预测参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("批量预测服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("批量预测接口异常: %s", e)
        return error("服务器内部错误", code=500), 500


# ---------------------------------------------------------------------------
# Route handlers – model
# ---------------------------------------------------------------------------


@bp.route("/model/info", methods=["GET"])
def get_model_info():
    """获取模型信息接口"""
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
            except (ValueError, OSError) as e:
                logger.debug("读取训练摘要文件失败: %s", e)

        return ok(info), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("获取模型信息参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("获取模型信息服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("获取模型信息异常: %s", e)
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
    except (ValueError, KeyError, TypeError) as e:
        logger.error("模型重训练参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("模型重训练服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("模型重训练接口异常: %s", e)
        return error("服务器内部错误", code=500), 500


# ---------------------------------------------------------------------------
# Route handlers – spider / tasks
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Route handlers – today stats & strategy
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


@bp.route("/sentiment/strategy/stats", methods=["GET"])
def get_strategy_stats():
    """获取情感分析策略性能统计"""
    try:
        from services.sentiment_strategy_selector import AdaptiveStrategyManager

        manager = AdaptiveStrategyManager()
        stats = manager.get_performance_stats()
        return ok(stats), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("获取策略统计参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("获取策略统计服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("获取策略统计失败: %s", e)
        return error("服务器内部错误", code=500), 500


@bp.route("/sentiment/strategy/health", methods=["GET"])
def get_strategy_health():
    """获取情感分析策略健康状态"""
    try:
        from services.sentiment_strategy_selector import AdaptiveStrategyManager

        manager = AdaptiveStrategyManager()
        health = manager.get_health_status()
        return ok(health), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("获取策略健康状态参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("获取策略健康状态服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("获取策略健康状态失败: %s", e)
        return error("服务器内部错误", code=500), 500
