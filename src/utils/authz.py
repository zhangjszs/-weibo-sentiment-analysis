from functools import wraps

from flask import g, request

from config.settings import Config
from utils.api_response import error


def is_admin_user(user):
    user_info = user or {}
    username = user_info.get("username")
    if not Config.ADMIN_USERS:
        return False
    return bool(username and username in Config.ADMIN_USERS)


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = getattr(request, "current_user", None) or {}
        if not is_admin_user(user):
            return error("权限不足", code=403), 403
        return func(*args, **kwargs)

    return wrapper


def require_jwt(func):
    """JWT 单轨装饰器：供蓝图复用，与 ``before_request`` 保持同等校验逻辑。

    - 同时支持 ``Authorization: Bearer <token>`` 与 ``Config.AUTH_COOKIE_NAME`` cookie。
    - 校验通过后将用户信息挂载到 ``request.current_user`` / ``g.current_user``。
    - 未认证时返回 401 JSON（与 ``_require_jwt_auth`` 行为一致），前端据此接管鉴权。
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        else:
            token = request.cookies.get(Config.AUTH_COOKIE_NAME)
        if not token:
            return error("缺少认证令牌", code=401), 401
        from utils.jwt_handler import verify_token

        user_info = verify_token(token)
        if not user_info:
            return error("缺少认证令牌", code=401), 401
        request.current_user = user_info
        g.current_user = user_info
        return func(*args, **kwargs)

    return wrapper
