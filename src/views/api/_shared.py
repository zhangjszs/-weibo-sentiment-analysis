"""API 蓝图共享层。

P2 拆分后，本模块持有所有路由子模块共享的对象：
- ``bp``：唯一的 api 蓝图（name="api"，prefix="/api"）
- ``logger``：统一日志器（保留 "api" logger 名以兼容现有日志过滤/告警）
- 4 个 service/repo 实例：在进程内只创建一次，路由模块按引用导入。
  测试通过 ``monkeypatch.setattr(api_module.auth_service, "login", ...)``
  打补丁时，由于所有路由模块引用的是同一个实例，patch 对全部引用方生效。
- ``_require_authenticated_user``：跨 auth/user 域使用的小工具，放这里避免循环导入。
"""

import logging

from flask import Blueprint, request

from repositories.user_repository import UserRepository
from services.article_service import ArticleService
from services.auth_service import AuthService
from services.comment_service import CommentService
from utils.api_response import error
from utils.log_sanitizer import SafeLogger

logger = SafeLogger("api", logging.INFO)

API_PREFIX = "/api"

# 服务实例（进程内单例，按引用共享给各路由子模块）
article_service = ArticleService()
auth_service = AuthService()
comment_service = CommentService()
user_repo = UserRepository()

bp = Blueprint("api", __name__, url_prefix="/api")


def _require_authenticated_user():
    """Return the current user dict or an error response tuple."""
    user = getattr(request, "current_user", None)
    if not user:
        return None, (error("未认证", code=401), 401)
    return user, None
