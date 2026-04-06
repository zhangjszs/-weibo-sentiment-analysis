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
        if not is_admin_user(user):
            return error("权限不足", code=403), 403
        return func(*args, **kwargs)

    return wrapper
