#!/usr/bin/env python3
"""
微博舆情分析系统 - Flask主应用
功能：Web应用主入口，路由管理，用户认证中间件
特性：蓝图架构、会话管理、错误处理、安全防护
作者：微博舆情分析系统

系统架构：
- 用户认证：session-based认证，登录状态检查
- 路由管理：蓝图(Blueprint)模式，模块化路由
- 错误处理：自定义404页面，异常捕获
- 安全防护：路径拦截，静态文件保护
"""

import logging
import os
import re
import sys
import time
import uuid
from datetime import datetime

from flask import Flask, g, jsonify, redirect, render_template, request, session
from flask_compress import Compress
from flask_cors import CORS
from flask_wtf.csrf import CSRFError, CSRFProtect

# 导入统一配置模块
from config.settings import Config
from database import db_session
from services.notification_service import notification_service
from services.startup_service import (
    ensure_demo_admin,
    get_startup_status,
    schedule_startup_warmup,
)
from services.websocket_service import websocket_service
from utils.api_response import error, ok
from utils.authz import admin_required
from utils.config_validator import ConfigValidator
from utils.jwt_handler import create_token, verify_token

logger = logging.getLogger(__name__)

# ---- 日志配置幂等守卫 ----
_LOGGING_CONFIGURED = False


def _configure_logging() -> None:
    """配置日志系统（幂等，多次调用仅首次生效）。"""
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return
    os.makedirs(Config.LOG_DIR, exist_ok=True)
    from logging.handlers import TimedRotatingFileHandler

    file_handler = TimedRotatingFileHandler(
        os.path.join(Config.LOG_DIR, "app.log"),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.suffix = "%Y-%m-%d"
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
        format=Config.LOG_FORMAT,
        handlers=[
            file_handler,
            logging.StreamHandler(),
        ],
    )
    _LOGGING_CONFIGURED = True


# ===== 应用启动配置 =====
def create_app_directories():
    """创建应用必需的目录"""
    directories = [
        Config.LOG_DIR,
        Config.CACHE_DIR,
        os.path.join(Config.STATIC_DIR, "uploads"),
    ]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"创建目录: {directory}")


# ===== 工具函数（无副作用，可在 import 时定义）=====
def is_user_logged_in():
    """
    检查用户登录状态

    Returns:
        bool: 用户是否已登录
    """
    return session.get("username") is not None


def get_client_ip():
    """
    获取客户端真实IP地址
    处理代理和负载均衡情况

    Returns:
        str: 客户端IP地址
    """
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    elif request.headers.get("X-Real-IP"):
        return request.headers.get("X-Real-IP")
    else:
        return request.remote_addr


def log_request_info():
    """记录请求信息用于审计和调试"""
    user = session.get("username", "Anonymous")
    ip = get_client_ip()
    logger.info(f"请求: {request.method} {request.path} | 用户: {user} | IP: {ip}")


def _get_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None


def _get_auth_token():
    return _get_bearer_token() or request.cookies.get(Config.AUTH_COOKIE_NAME)


def _attach_current_user_from_token():
    token = _get_auth_token()
    if not token:
        return None
    user_info = verify_token(token)
    if not user_info:
        return None
    request.current_user = user_info
    g.current_user = user_info
    # rate_limiter 的 user 键读 g.user_id；此前从未设置，限流按 IP 走（#15）
    g.user_id = user_info.get("user_id")
    return user_info


def _set_auth_cookie(response, token: str):
    response.set_cookie(
        Config.AUTH_COOKIE_NAME,
        token,
        max_age=Config.JWT_EXPIRATION_HOURS * 3600,
        httponly=True,
        secure=Config.FLASK_ENV == "production",
        samesite="Strict" if Config.FLASK_ENV == "production" else "Lax",
        path="/",
    )


def _require_jwt_auth():
    # 缺失与无效区分提示（#15）：前端据此决定跳登录页还是提示重新登录
    if not _get_auth_token():
        return error("缺少认证令牌", code=401), 401
    user_info = _attach_current_user_from_token()
    if not user_info:
        return error("认证令牌无效或已过期", code=401), 401
    return None


def _validate_origin_for_state_change():
    """对 CSRF 豁免的 API 路径做 Origin 校验（defense-in-depth）。

    鉴权模型（Bearer 主轨 + Cookie 副轨）：
    - Bearer（Authorization 头）是主轨：非 ambient 凭证，不依赖 Cookie，
      不受 CSRF 影响；无 Origin 时放行（curl / API SDK / 服务间调用）。
    - Cookie（AUTH_COOKIE_NAME 内为 JWT）是副轨，仅供前端同源 SPA 使用：
      SameSite=Strict（生产）是主防线，本检查是第二层。浏览器 POST/PUT/
      PATCH/DELETE 必然携带 Origin（fetch 规范），因此 Cookie 轨的状态变更
      请求若既无 Origin 又无 Referer，视为可疑（可能被剥离头部的跨站请求），
      直接 403。纯 Bearer 或无凭证请求不受此限（无凭证者由 JWT 层返回 401）。

    Returns:
        None 或 (error_response, status_code) 元组
    """
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return None

    origin = request.headers.get("Origin")
    if origin:
        if origin in Config.ALLOWED_ORIGINS:
            return None
        logger.warning(
            "CSRF Origin 校验失败: origin=%s path=%s method=%s ip=%s",
            origin, request.path, request.method, get_client_ip(),
        )
        return error("跨站请求被拒绝", code=403), 403

    # Origin 缺失：回退到 Referer（部分隐私模式会去掉 Origin）
    referer = request.headers.get("Referer", "")
    if referer:
        for allowed in Config.ALLOWED_ORIGINS:
            if referer.startswith(allowed):
                return None
        logger.warning(
            "CSRF Referer 校验失败: referer=%s path=%s method=%s ip=%s",
            referer, request.path, request.method, get_client_ip(),
        )
        return error("跨站请求被拒绝", code=403), 403

    # 既无 Origin 也无 Referer：
    # - Cookie 副轨（带认证 Cookie 但无 Bearer 头）：浏览器必然带 Origin，
    #   缺失即视为 CSRF 风险 → 403。
    # - Bearer 主轨 / 无凭证：视为非浏览器客户端 → 放行（JWT 层会处理未认证）。
    has_bearer = bool(_get_bearer_token())
    has_auth_cookie = bool(request.cookies.get(Config.AUTH_COOKIE_NAME))
    if has_auth_cookie and not has_bearer:
        logger.warning(
            "CSRF 校验失败: Cookie 状态变更请求缺失 Origin/Referer path=%s method=%s ip=%s",
            request.path, request.method, get_client_ip(),
        )
        return error("跨站请求被拒绝", code=403), 403
    return None


# ===== 工厂 =====
def create_app() -> Flask:
    """显式应用工厂：import 无副作用，急切构造仅发生在组合根。

    分区：
    - bootstrap：配置校验、日志、目录
    - wire：Flask/CORS/CSRF/蓝图/中间件/错误处理
    - startup：引导（演示账号）/ 通知桥接 / 预热
    """
    # ---- bootstrap ----
    _configure_logging()
    Config.validate()
    create_app_directories()
    ConfigValidator.print_config_summary()

    app = Flask(__name__)

    # ---- wire: 响应压缩 ----
    Compress(app)
    app.config["COMPRESS_ALGORITHM"] = ["br", "gzip", "deflate"]
    app.config["COMPRESS_MIN_SIZE"] = 500

    # ---- wire: CSRF + CORS ----
    csrf = CSRFProtect(app)
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": Config.ALLOWED_ORIGINS,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            },
            r"/getAllData/*": {
                "origins": Config.ALLOWED_ORIGINS,
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            },
            r"/user/*": {
                "origins": Config.ALLOWED_ORIGINS,
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            },
        },
    )
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_TIME_LIMIT"] = None
    app.config["WTF_CSRF_SSL_STRICT"] = False

    # ---- wire: 应用配置 ----
    app.secret_key = Config.SECRET_KEY
    app.debug = Config.DEBUG
    app.config["JSON_AS_ASCII"] = Config.JSON_AS_ASCII
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = Config.SEND_FILE_MAX_AGE_DEFAULT
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH
    app.config["PERMANENT_SESSION_LIFETIME"] = Config.PERMANENT_SESSION_LIFETIME

    # Session 安全
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    if Config.FLASK_ENV == "production":
        app.config["SESSION_COOKIE_SECURE"] = True
        logger.info("生产环境：启用Secure Cookie（仅HTTPS传输）")
    else:
        app.config["SESSION_COOKIE_SECURE"] = False
        logger.info("开发环境：禁用Secure Cookie（允许HTTP传输）")
    if Config.FLASK_ENV == "production":
        app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
    else:
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_NAME"] = "weibo_session_id"
    app.config["SESSION_COOKIE_PATH"] = "/"
    app.config["SESSION_COOKIE_DOMAIN"] = None

    logger.info(
        f"Flask应用配置加载完成 [环境: {Config.FLASK_ENV}, 调试模式: {Config.DEBUG}]"
    )

    # ---- wire: 蓝图注册 ----
    from views.page import page  # 页面视图蓝图
    from views.user import user  # 用户认证蓝图

    app.register_blueprint(page.pb)  # 注册页面蓝图
    app.register_blueprint(user.ub)  # 注册用户蓝图

    # A3: 统一 API 蓝图注册（集中处理 /api/* 蓝图与 CSRF 豁免）
    try:
        from views.api import register_api

        register_api(app, csrf)
    except ImportError as e:
        logger.error(f"蓝图导入失败: {e}")
        raise

    # A1 过渡期别名：/getAllData/* -> 307 /api/*（保留一版本，向后兼容）
    # 仅保留此一处别名，其余不再出现旧前缀
    from flask import Blueprint as _AliasBlueprint

    data_legacy_alias = _AliasBlueprint("data_legacy_alias", __name__, url_prefix="/getAllData")

    @data_legacy_alias.route(
        "/<path:subpath>",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    )
    def _legacy_data_alias_redirect(subpath):
        qs = request.query_string.decode("utf-8")
        target = f"/api/{subpath}"
        if qs:
            target += f"?{qs}"
        return redirect(target, code=307)

    @data_legacy_alias.route(
        "/",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    )
    def _legacy_data_alias_root():
        qs = request.query_string.decode("utf-8")
        target = "/api/"
        if qs:
            target += f"?{qs}"
        return redirect(target, code=307)

    app.register_blueprint(data_legacy_alias)
    csrf.exempt(data_legacy_alias)

    logger.info(
        "蓝图注册完成: page, user, api, data, spider, alert, propagation, report, platform"
    )

    # ---- wire: 路由 ----
    @app.route("/")
    def index():
        """首页路由 - 重定向到登录页面"""
        logger.info("访问首页，重定向到登录页面")
        return redirect("/user/login")

    @app.route("/health")
    def health_check():
        """Liveness probe.

        Returns 200 as long as the Flask process is alive.  This endpoint must
        NOT perform any I/O (no database, no Redis, no filesystem) so that
        load balancers and ``scripts/healthcheck.py`` can rely on it even when
        external dependencies are down.
        """
        return jsonify({"status": "ok"})

    @app.route("/ready")
    def ready_check():
        """Readiness probe with bounded-time dependency checks."""
        import concurrent.futures

        checks: dict[str, dict] = {}
        overall_ready = True

        def _check_database() -> dict:
            try:
                from sqlalchemy import text

                db_session.execute(text("SELECT 1"))
                db_session.remove()
                return {"ready": True}
            except Exception as exc:
                return {"ready": False, "error": type(exc).__name__}

        def _check_redis() -> dict:
            try:
                import redis as redis_lib

                client = redis_lib.Redis(
                    host=Config.REDIS_HOST,
                    port=Config.REDIS_PORT,
                    db=Config.REDIS_DB,
                    password=Config.REDIS_PASSWORD or None,
                    socket_connect_timeout=3,
                    socket_timeout=3,
                )
                client.ping()
                return {"ready": True}
            except Exception as exc:
                return {"ready": False, "error": type(exc).__name__}

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {"database": executor.submit(_check_database)}
            if Config.REDIS_URL and Config.REDIS_URL != "disabled":
                futures["redis"] = executor.submit(_check_redis)
            for name, future in futures.items():
                try:
                    result = future.result(timeout=6)
                except concurrent.futures.TimeoutError:
                    result = {"ready": False, "error": "timeout"}
                except Exception as exc:
                    result = {"ready": False, "error": type(exc).__name__}
                checks[name] = result
                if not result.get("ready"):
                    overall_ready = False

        status_code = 200 if overall_ready else 503
        return jsonify(
            {
                "status": "ready" if overall_ready else "degraded",
                "checks": checks,
            }
        ), status_code

    @app.route("/api/health/details")
    @admin_required
    def health_details():
        try:
            from utils.query import get_database_stats

            db_stats = get_database_stats()
            return ok(
                {
                    "status": "healthy",
                    "database": {
                        "connected": bool(db_stats),
                        "stats": db_stats,
                    },
                    "uptime": time.time() - app.start_time
                    if hasattr(app, "start_time")
                    else 0,
                    "version": "1.0.0",
                }
            ), 200
        except Exception as e:
            logger.error(f"健康详情检查失败: {e}")
            return error("健康详情检查失败", code=500), 500

    @app.route("/api/startup/status")
    @admin_required
    def startup_status():
        """获取启动引导与预热状态（仅管理员）。"""
        try:
            return ok(get_startup_status()), 200
        except Exception as e:
            logger.error(f"获取启动状态失败: {e}")
            return error("获取启动状态失败", code=500), 500

    @app.route("/api/session/check")
    def session_check():
        """检查用户会话状态"""
        try:
            user = (
                getattr(request, "current_user", None)
                or getattr(g, "current_user", None)
                or _attach_current_user_from_token()
            )
            authenticated = bool(user)
            return ok({"authenticated": authenticated, "user": user or None}), 200
        except Exception as e:
            logger.error(f"会话检查失败: {e}")
            return error("会话检查过程中发生错误", code=500), 500

    @csrf.exempt
    @app.route("/api/session/extend", methods=["POST"])
    def session_extend():
        """延长用户会话"""
        try:
            user = (
                getattr(request, "current_user", None)
                or getattr(g, "current_user", None)
                or {}
            )
            if not user:
                return error("未认证或登录已过期", code=401), 401
            username = user.get("username", "")
            # 旋转（#15）：新 token 签发的同时撤销旧 token，旧 token 泄露后
            # 不能再靠 extend 前的窗口继续使用
            old_token = _get_auth_token()
            if old_token:
                from utils.jwt_handler import revoke_token

                revoke_token(old_token)
            refreshed_token = create_token(user.get("user_id"), username)
            logger.info(f"用户 {username} 延长会话（JWT） | IP: {get_client_ip()}")
            response = ok(
                {"extended": True, "user": user, "token": refreshed_token},
                msg="会话已成功延长",
            )
            _set_auth_cookie(response, refreshed_token)
            response.status_code = 200
            return response
        except Exception as e:
            logger.error(f"会话延长失败: {e}")
            return error("会话延长过程中发生错误", code=500), 500

    # ---- wire: 中间件 ----
    @app.before_request
    def before_request():
        log_request_info()
        # 客户端提供的 X-Request-Id 只接受受限字符集，防止日志注入/伪造（#15）
        client_request_id = request.headers.get("X-Request-Id") or ""
        if re.fullmatch(r"[A-Za-z0-9_-]{1,64}", client_request_id):
            g.request_id = client_request_id
        else:
            g.request_id = uuid.uuid4().hex
        if request.path.startswith("/static"):
            return None
        # A2 JWT 单轨：白名单直通，其余均需 JWT（/page/* 仅保留登录/注册页直出，其余 401）
        # 注意：/user/info 必须经过 JWT 鉴权，不得加入白名单；
        # /getAllData/* 旧别名同样先鉴权再 307，保证与 /api/* 行为一致。
        public_endpoints = [
            "/",
            "/health",
            "/ready",
            "/user/login",
            "/user/register",
        ]
        if request.path in public_endpoints:
            return None
        public_api_prefixes = [
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/logout",
            "/api/session/check",
        ]
        if any(
            request.path == p or request.path.startswith(p)
            for p in public_api_prefixes
        ):
            if request.path == "/api/session/check":
                _attach_current_user_from_token()
            return None
        # A1: /getAllData/* 已收敛至 /api/*，旧前缀为 307 重定向别名。
        # 安全起见别名本身同样要求 JWT（先鉴权再重定向），避免不跟随跳转的客户端裸奔。
        # 鉴权失败一律 401；通过后再由别名视图 307 到 /api/*（目标处会再次鉴权，结果一致）。
        # JWT 单轨：其余所有路径（含 /page/*、/api/*、/user/*、/getAllData/* 等）均需 JWT
        # 保留 SameSite+Origin 双层防护，但收敛调用点：先做 JWT，再做 Origin
        # 这样未认证时一律 401（不受 Origin 影响），已认证跨站再 403
        auth_result = _require_jwt_auth()
        if auth_result is not None:
            return auth_result
        origin_err = _validate_origin_for_state_change()
        if origin_err is not None:
            return origin_err
        return None

    @app.after_request
    def after_request(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        if not Config.IS_DEVELOPMENT:
            proto = request.headers.get("X-Forwarded-Proto", "http")
            if request.is_secure or proto == "https":
                response.headers["Strict-Transport-Security"] = (
                    "max-age=31536000; includeSubDomains"
                )
        if response.mimetype == "text/html":
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "base-uri 'self'; "
                "frame-ancestors 'none'; "
                "img-src 'self' data:; "
                "style-src 'self' 'unsafe-inline'; "
                "script-src 'self' 'unsafe-inline'; "
                "connect-src 'self'"
            )
        if request.path.startswith("/static"):
            response.headers["Cache-Control"] = "public, max-age=300"
        else:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        if response.status_code >= 400:
            logger.warning(f"响应错误: {response.status_code} | 路径: {request.path}")
        if getattr(g, "request_id", None):
            response.headers["X-Request-Id"] = g.request_id
        return response

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    # ---- wire: 错误处理器 ----
    @app.errorhandler(404)
    def page_not_found(err):  # noqa: ARG001
        logger.warning(f"404错误: {request.path} | IP: {get_client_ip()}")
        if request.path.startswith("/api/") or request.path.startswith("/getAllData/"):
            return error("请求的资源不存在", code=404), 404
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(err):  # noqa: ARG001
        logger.error(f"500错误: {err} | 路径: {request.path} | IP: {get_client_ip()}")
        if request.path.startswith("/api/") or request.path.startswith("/getAllData/"):
            return error("服务器内部错误，请稍后重试", code=500), 500
        try:
            return render_template("error.html", error_message="服务器内部错误"), 500
        except Exception as e:
            logger.error("模板加载失败，返回纯文本: %s", e)
            return "服务器内部错误，请稍后重试", 500

    @app.errorhandler(403)
    def forbidden(err):  # noqa: ARG001
        logger.warning(f"403错误: 权限不足 | 路径: {request.path} | IP: {get_client_ip()}")
        if request.path.startswith("/api/") or request.path.startswith("/getAllData/"):
            return error("权限不足", code=403), 403
        return render_template("error.html", error_message="权限不足"), 403

    @app.errorhandler(401)
    def unauthorized(err):  # noqa: ARG001
        if request.path.startswith("/api/") or request.path.startswith("/getAllData/"):
            return error("未认证或登录已过期", code=401), 401
        return redirect("/user/login")

    @app.errorhandler(CSRFError)
    def handle_csrf_error(err):  # noqa: ARG001
        accepts_json = request.headers.get("Accept", "").startswith("application/json")
        if (
            request.path.startswith("/api/")
            or request.path.startswith("/getAllData/")
            or request.is_json
            or accepts_json
        ):
            return error("CSRF 校验失败", code=400), 400
        return render_template("error.html", error_message="CSRF 校验失败"), 400

    @app.errorhandler(422)
    def unprocessable_entity(err):  # noqa: ARG001
        if request.path.startswith("/api/") or request.path.startswith("/getAllData/"):
            return error("请求参数无效", code=422), 422
        return render_template("error.html", error_message="请求参数无效"), 422

    @app.route("/<path:path>")
    def catch_all(path):
        malicious_patterns = [
            r"\.php$",
            r"wp-admin",
            r"phpmyadmin",
            r"\.env$",
            r"\.git",
            r"admin\.php",
            r"login\.php",
        ]
        for pattern in malicious_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                logger.warning(f"检测到可疑请求: /{path} | IP: {get_client_ip()}")
                return "", 404
        logger.info(f"未定义路径: /{path} | IP: {get_client_ip()}")
        return render_template("404.html"), 404

    # ---- startup: 引导 / wire 扩展 / 预热 ----
    app.start_time = time.time()

    # 引导：演示账号
    admin_bootstrap = ensure_demo_admin()
    if admin_bootstrap.get("action") == "created":
        logger.info(
            "已创建演示管理员账号: %s（请通过环境变量修改默认密码）",
            admin_bootstrap.get("username"),
        )
    elif admin_bootstrap.get("action") == "reset_password":
        logger.info(
            "已重置演示管理员账号密码: %s",
            admin_bootstrap.get("username"),
        )
    elif admin_bootstrap.get("action") == "error":
        logger.warning(
            "演示管理员账号引导失败: %s",
            admin_bootstrap.get("error"),
        )

    # wire 扩展：WebSocket / 通知桥接
    websocket_service.init_app(app)
    try:
        from services.alert_service import alert_engine

        synced_recipients = notification_service.sync_admin_recipients()
        notification_service.bind_alert_engine(alert_engine)
        notification_service.start()
        logger.info("预警通知服务已启动，默认接收人: %s", synced_recipients)
    except Exception as exc:
        logger.warning(f"预警通知服务初始化失败: {exc}")

    # 预热：异步缓存
    if not os.getenv("PYTEST_CURRENT_TEST"):
        if schedule_startup_warmup(app):
            logger.info("已启动核心接口预热线程")

    logger.info("=" * 50)
    logger.info("微博舆情分析系统启动")
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"调试模式: {'开启' if app.debug else '关闭'}")
    logger.info(f"Python版本: {sys.version}")
    logger.info("=" * 50)

    return app


# ===== 工厂直接运行（保留 `python src/app.py` 能力）=====
if __name__ == "__main__":
    _app = create_app()
    try:
        if websocket_service.socketio:
            websocket_service.socketio.run(
                _app,
                host="127.0.0.1",
                port=5000,
                debug=_app.config.get("DEBUG", False),
                use_reloader=Config.IS_DEVELOPMENT,
            )
        else:
            _app.run(
                host="127.0.0.1",
                port=5000,
                debug=_app.config.get("DEBUG", False),
                threaded=True,
                use_reloader=Config.IS_DEVELOPMENT,
            )
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise
    finally:
        logger.info("应用已停止")
