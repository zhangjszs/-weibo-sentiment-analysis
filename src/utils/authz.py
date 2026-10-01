from functools import wraps

from flask import request

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
        if not user:
            # 未认证 401、已认证但无权限 403：两者混为 403 时前端无法区分
            # 「该去登录」还是「该去找管理员」（#15）
            return error("未认证", code=401), 401
        if not is_admin_user(user):
            return error("权限不足", code=403), 403
        return func(*args, **kwargs)

    return wrapper


# JWT 单轨装饰器统一（#15）：require_jwt 是 jwt_required 的真别名——
# 行为已一致（Bearer 头优先、回退 Config.AUTH_COOKIE_NAME cookie，未认证
# 401，错误结构走 utils.api_response.error），保留本名字以兼容既有 import。
# jwt_handler 不反向依赖 authz，无 import 环。
from utils.jwt_handler import jwt_required as require_jwt  # noqa: E402,F401

__all__ = ["admin_required", "is_admin_user", "require_jwt"]
