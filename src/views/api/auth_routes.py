"""认证路由 ``/api/auth/*``。

包含 cookie 辅助函数与 login/register/me/logout 四个端点。
"""

from flask import request

from config.settings import Config
from services.audit_service import audit_log
from utils.api_response import error, ok
from utils.authz import is_admin_user
from utils.input_validator import sanitize_input, validate_password, validate_username
from utils.rate_limiter import rate_limit

from ._shared import (
    _require_authenticated_user,
    auth_service,
    bp,
    logger,
    user_repo,
)


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
# Route handlers
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
