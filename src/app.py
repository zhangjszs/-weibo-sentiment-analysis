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
from services.startup_service import (
    ensure_demo_admin,
    get_startup_status,
    schedule_startup_warmup,
)
from services.notification_service import notification_service
from services.websocket_service import websocket_service
from utils.api_response import error, ok
from utils.authz import admin_required
from utils.jwt_handler import create_token, verify_token
from utils.config_validator import ConfigValidator

# 确保日志目录存在
os.makedirs(Config.LOG_DIR, exist_ok=True)

# 配置日志系统（按天轮转，保留 30 天）
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
logger = logging.getLogger(__name__)


# ===== 应用启动配置 =====
def create_app_directories():
    """创建应用必需的目录"""
    # 使用配置中的目录
    directories = [
        Config.LOG_DIR,
        Config.CACHE_DIR,
        os.path.join(Config.STATIC_DIR, "uploads"),
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"创建目录: {directory}")


# 创建Flask应用实例
app = Flask(__name__)

# ===== 响应压缩 =====
Compress(app)
app.config["COMPRESS_ALGORITHM"] = ["br", "gzip", "deflate"]
app.config["COMPRESS_MIN_SIZE"] = 500  # 仅压缩 > 500 bytes 的响应

# ===== CSRF保护配置 =====
# 初始化CSRF保护
csrf = CSRFProtect(app)

# 初始化CORS支持（解决跨域问题）
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

# CSRF配置
app.config["WTF_CSRF_ENABLED"] = True  # 启用CSRF保护
app.config["WTF_CSRF_TIME_LIMIT"] = None  # CSRF令牌不过期
app.config["WTF_CSRF_SSL_STRICT"] = False  # 非生产环境不强制HTTPS

# ===== 应用配置 =====
# 从环境变量加载安全密钥（使用 config/settings.py 统一管理）
Config.validate()
app.secret_key = Config.SECRET_KEY

# 根据环境变量设置调试模式
app.debug = Config.DEBUG

# 应用配置
app.config["JSON_AS_ASCII"] = Config.JSON_AS_ASCII  # 支持中文JSON响应
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = (
    Config.SEND_FILE_MAX_AGE_DEFAULT
)  # 静态文件缓存时间
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH  # 最大上传文件大小

# Session配置
app.config["PERMANENT_SESSION_LIFETIME"] = Config.PERMANENT_SESSION_LIFETIME

# ===== Session安全配置（根据环境自动调整）=====
# HttpOnly：防止JavaScript访问Cookie，防止XSS攻击
app.config["SESSION_COOKIE_HTTPONLY"] = True

# Secure：仅通过HTTPS传输Cookie（生产环境强制启用）
# 根据环境变量自动设置，生产环境必须为True
if Config.FLASK_ENV == "production":
    app.config["SESSION_COOKIE_SECURE"] = True
    logger.info("生产环境：启用Secure Cookie（仅HTTPS传输）")
else:
    app.config["SESSION_COOKIE_SECURE"] = False
    logger.info("开发环境：禁用Secure Cookie（允许HTTP传输）")

# SameSite：防止CSRF攻击
if Config.FLASK_ENV == "production":
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"  # 生产环境最严格
else:
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # 开发环境中等

# Session名称（避免使用默认的session）
app.config["SESSION_COOKIE_NAME"] = "weibo_session_id"

# 额外的安全头部
app.config["SESSION_COOKIE_PATH"] = "/"
app.config["SESSION_COOKIE_DOMAIN"] = None  # 默认当前域名

logger.info(
    f"Flask应用配置加载完成 [环境: {Config.FLASK_ENV}, 调试模式: {Config.DEBUG}]"
)

# ===== 蓝图注册 =====
# 导入并注册应用蓝图模块
try:
    from views.api import api  # API视图蓝图
    from views.api.alert_api import bp as alert_bp  # 预警管理蓝图
    from views.api.audit_api import audit_bp  # 审计日志蓝图
    from views.api.bigscreen_api import bp as bigscreen_bp  # 数据大屏蓝图
    from views.api.favorites_api import favorites_bp  # 收藏管理蓝图
    from views.api.platform_api import bp as platform_bp  # 多平台数据蓝图
    from views.api.propagation_api import bp as propagation_bp  # 传播分析蓝图
    from views.api.report_api import bp as report_bp  # 报告生成蓝图
    from views.api.spider_api import spider_bp  # 爬虫管理蓝图
    from views.data import db  # 数据API蓝图
    from views.page import page  # 页面视图蓝图
    from views.user import user  # 用户认证蓝图

    app.register_blueprint(page.pb)  # 注册页面蓝图
    app.register_blueprint(user.ub)  # 注册用户蓝图
    app.register_blueprint(api.bp)  # 注册API蓝图
    app.register_blueprint(db)  # 注册数据API蓝图
    app.register_blueprint(spider_bp)  # 注册爬虫管理蓝图
    app.register_blueprint(alert_bp)  # 注册预警管理蓝图
    app.register_blueprint(propagation_bp)  # 注册传播分析蓝图
    app.register_blueprint(report_bp)  # 注册报告生成蓝图
    app.register_blueprint(platform_bp)  # 注册多平台数据蓝图
    app.register_blueprint(favorites_bp)  # 注册收藏管理蓝图
    app.register_blueprint(audit_bp)  # 注册审计日志蓝图
    app.register_blueprint(bigscreen_bp)  # 注册数据大屏蓝图

    # API 蓝图排除 CSRF（使用 Bearer Token 鉴权）
    csrf.exempt(api.bp)
    csrf.exempt(db)
    csrf.exempt(spider_bp)
    csrf.exempt(alert_bp)
    csrf.exempt(propagation_bp)
    csrf.exempt(report_bp)
    csrf.exempt(platform_bp)
    csrf.exempt(favorites_bp)
    csrf.exempt(audit_bp)

    logger.info(
        "蓝图注册完成: page, user, api, data, spider, alert, propagation, report, platform"
    )

except ImportError as e:
    logger.error(f"蓝图导入失败: {e}")
    raise


# ===== 工具函数 =====
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
    user_info = _attach_current_user_from_token()
    if not user_info:
        return error("缺少认证令牌", code=401), 401
    return None


# ===== 路由定义 =====
@app.route("/")
def index():
    """
    首页路由 - 重定向到登录页面
    确保用户必须登录才能使用系统
    """
    logger.info("访问首页，重定向到登录页面")
    return redirect("/user/login")


@app.route("/health")
def health_check():
    """
    健康检查端点
    用于监控系统状态和负载均衡健康检查

    Returns:
        JSON: 系统状态信息
    """
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time() - app.start_time if hasattr(app, "start_time") else 0,
            "version": "1.0.0",
        }
    )


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
    """
    检查用户会话状态

    Returns:
        JSON: 会话状态信息
    """
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
    """
    延长用户会话

    Returns:
        JSON: 延长结果
    """
    try:
        user = (
            getattr(request, "current_user", None)
            or getattr(g, "current_user", None)
            or {}
        )
        if not user:
            return error("未认证或登录已过期", code=401), 401
        username = user.get("username", "")
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


# ===== 中间件和钩子函数 =====
@app.before_request
def before_request():
    """
    请求前置处理中间件

    功能：
    1. 静态资源直接放行
    2. 登录/注册页面无需认证
    3. 健康检查端点无需认证
    4. API端点部分无需认证
    5. 其他页面需要登录验证
    6. 记录请求日志
    """
    # 记录请求信息
    log_request_info()

    g.request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex

    # 静态资源放行（CSS、JS、图片等）
    if request.path.startswith("/static"):
        return None

    # 公开访问的端点（无需登录）
    public_endpoints = [
        "/user/login",  # 登录页面
        "/user/register",  # 注册页面
        "/user/info",  # JWT保护的用户信息
        "/health",  # 健康检查
        "/",  # 首页（会重定向到登录）
    ]

    if request.path in public_endpoints:
        return None

    # API端点特殊处理 - 允许特定API无需登录
    if request.path.startswith("/api/"):
        # 允许的公开API
        public_apis = [
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/logout",
            "/api/session/check",
        ]

        # 检查是否是公开API
        if request.path in public_apis or any(
            request.path.startswith(p) for p in public_apis
        ):
            if request.path == "/api/session/check":
                _attach_current_user_from_token()
            return None

        auth_result = _require_jwt_auth()
        if auth_result is not None:
            return auth_result
        return None

    # 数据API端点 - JWT保护（用于Vue前端）
    if request.path.startswith("/getAllData/"):
        auth_result = _require_jwt_auth()
        if auth_result is not None:
            return auth_result
        return None

    # 旧版 Jinja 模板页面 (/page/*) 需要 session 登录验证
    if request.path.startswith("/page/"):
        if not is_user_logged_in():
            logger.warning(
                f"未登录访问受保护页面: {request.path} | IP: {get_client_ip()}"
            )
            redirect_url = request.path
            if request.query_string:
                redirect_url += "?" + request.query_string.decode("utf-8")
            return redirect(f"/user/login?redirect={redirect_url}")

    # 其他路径直接放行（Vue 前端路由由前端自行管理认证）
    return None


@app.after_request
def after_request(response):
    """
    请求后置处理中间件

    功能：
    1. 添加安全响应头
    2. 处理跨域请求
    3. 记录响应状态

    Args:
        response: Flask响应对象

    Returns:
        response: 处理后的响应对象
    """
    # 添加安全响应头
    response.headers["X-Content-Type-Options"] = "nosniff"  # 防止MIME类型嗅探
    response.headers["X-Frame-Options"] = "DENY"  # 防止页面被嵌入iframe
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

    # 缓存控制（根据内容类型）
    if request.path.startswith("/static"):
        response.headers["Cache-Control"] = "public, max-age=300"  # 静态文件缓存5分钟
    else:
        response.headers["Cache-Control"] = (
            "no-cache, no-store, must-revalidate"  # 页面不缓存
        )

    # 记录响应状态
    if response.status_code >= 400:
        logger.warning(f"响应错误: {response.status_code} | 路径: {request.path}")

    if getattr(g, "request_id", None):
        response.headers["X-Request-Id"] = g.request_id

    return response


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


# ===== 错误处理器 =====
@app.errorhandler(404)
def page_not_found(error):
    """
    404错误处理器
    当访问不存在的页面时显示友好的错误页面

    Args:
        error: 错误对象

    Returns:
        tuple: (模板, 状态码)
    """
    logger.warning(f"404错误: {request.path} | IP: {get_client_ip()}")

    # API请求返回JSON错误
    if request.path.startswith("/api/") or request.path.startswith("/getAllData/"):
        return error("请求的资源不存在", code=404), 404

    # 网页请求返回HTML错误页面
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    """
    500错误处理器
    处理服务器内部错误

    Args:
        error: 错误对象

    Returns:
        tuple: (响应, 状态码)
    """
    logger.error(f"500错误: {error} | 路径: {request.path} | IP: {get_client_ip()}")

    # API请求返回JSON错误
    if request.path.startswith("/api/") or request.path.startswith("/getAllData/"):
        return error("服务器内部错误，请稍后重试", code=500), 500

    # 网页请求返回错误页面
    try:
        return render_template("error.html", error_message="服务器内部错误"), 500
    except Exception as e:
        logger.error("模板加载失败，返回纯文本: %s", e)
        return "服务器内部错误，请稍后重试", 500


@app.errorhandler(403)
def forbidden(error):
    """
    403错误处理器
    处理权限不足错误
    """
    logger.warning(f"403错误: 权限不足 | 路径: {request.path} | IP: {get_client_ip()}")

    if request.path.startswith("/api/") or request.path.startswith("/getAllData/"):
        return error("权限不足", code=403), 403

    return render_template("error.html", error_message="权限不足"), 403


@app.errorhandler(401)
def unauthorized(error):
    if request.path.startswith("/api/") or request.path.startswith("/getAllData/"):
        return error("未认证或登录已过期", code=401), 401
    return redirect("/user/login")


@app.errorhandler(CSRFError)
def handle_csrf_error(err):
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
def unprocessable_entity(err):
    if request.path.startswith("/api/") or request.path.startswith("/getAllData/"):
        return error("请求参数无效", code=422), 422
    return render_template("error.html", error_message="请求参数无效"), 422

# ===== 通用路由捕获（仅拦截恶意请求）=====
@app.route("/<path:path>")
def catch_all(path):
    """
    捕获所有未定义的路径
    仅拦截恶意请求，其他返回默认404

    注意：Vue 客户端路由（/home, /hot-words 等）在开发环境由 Vite 代理处理，
    不会到达此处。生产环境应由 Nginx 转发到 index.html。
    """
    # 一些常见的恶意请求路径，静默拒绝
    malicious_patterns = [
        r"\.php$",  # PHP文件
        r"wp-admin",  # WordPress后台
        r"phpmyadmin",  # phpMyAdmin
        r"\.env$",  # 环境变量文件
        r"\.git",  # Git仓库
        r"admin\.php",  # 管理页面
        r"login\.php",  # PHP登录页面
    ]

    for pattern in malicious_patterns:
        if re.search(pattern, path, re.IGNORECASE):
            logger.warning(f"检测到可疑请求: /{path} | IP: {get_client_ip()}")
            return "", 404  # 直接返回404，不提供任何信息

    # 其他未知路径返回404（不做重定向，避免与Vue Router冲突）
    logger.info(f"未定义路径: /{path} | IP: {get_client_ip()}")
    return render_template("404.html"), 404


# ===== 应用启动配置 =====


def initialize_app():
    """初始化应用"""
    # 记录启动时间
    app.start_time = time.time()

    # 创建必要目录
    create_app_directories()

    # 验证配置
    ConfigValidator.print_config_summary()

    # 开发环境演示管理员账号引导
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

    # 初始化 WebSocket 服务
    websocket_service.init_app(app)

    # 初始化预警通知桥接
    try:
        from services.alert_service import alert_engine

        synced_recipients = notification_service.sync_admin_recipients()
        notification_service.bind_alert_engine(alert_engine)
        notification_service.start()
        logger.info("预警通知服务已启动，默认接收人: %s", synced_recipients)
    except Exception as exc:
        logger.warning(f"预警通知服务初始化失败: {exc}")

    # 异步预热核心接口缓存（pytest 环境下跳过，避免测试期后台线程干扰）
    if not os.getenv("PYTEST_CURRENT_TEST"):
        if schedule_startup_warmup(app):
            logger.info("已启动核心接口预热线程")

    # 记录启动信息
    logger.info("=" * 50)
    logger.info("微博舆情分析系统启动")
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"调试模式: {'开启' if app.debug else '关闭'}")
    logger.info(f"Python版本: {sys.version}")
    logger.info("=" * 50)


# 模块级别初始化（确保通过 run.py 导入时也会执行）
initialize_app()


# ===== 主程序入口 =====
if __name__ == "__main__":
    try:
        # 启动Flask+SocketIO开发服务器
        # 生产环境请使用gunicorn或uwsgi等WSGI服务器
        if websocket_service.socketio:
            websocket_service.socketio.run(
                app,
                host="127.0.0.1",  # 监听地址（生产环境可设为0.0.0.0）
                port=5000,  # 监听端口
                debug=Config.DEBUG,  # 从配置读取调试模式
                use_reloader=Config.IS_DEVELOPMENT,  # 仅开发环境启用自动重载
            )
        else:
            app.run(
                host="127.0.0.1",
                port=5000,
                debug=Config.DEBUG,
                threaded=True,
                use_reloader=Config.IS_DEVELOPMENT,
            )

    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise
    finally:
        logger.info("应用已停止")
