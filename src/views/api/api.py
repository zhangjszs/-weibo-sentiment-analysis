"""API 路由聚合层（P2 拆分后）。

历史背景：本文件曾是 1041 行的"上帝文件"，包含 19 个路由与 ~20 个辅助函数，
覆盖 auth / user / 数据查询 / 情感分析 / 模型 / 爬虫 / 统计 7 个业务域。
P2 按业务域拆分为 ``_shared`` + 5 个 ``*_routes`` 子模块。

本文件现在只负责两件事：
1. 触发子模块导入，让 ``@bp.route`` 装饰器把路由注册到共享 ``bp`` 上；
2. 再导出 ``bp`` 和 4 个 service/repo 实例，保持对 ``app.py`` 与现有测试的
   向后兼容（``from views.api import api; api.bp`` / ``api.auth_service`` /
   ``api.article_service`` 等引用全部继续可用）。

路由实际定义见：
- ``auth_routes.py``    ``/api/auth/*``
- ``user_routes.py``    ``/api/user/*``
- ``data_routes.py``    ``/api/stats/*``、``/api/articles``、``/api/comments``
- ``ml_routes.py``      ``/api/sentiment/*``、``/api/predict/*``、``/api/model/*``
- ``spider_routes.py``  ``/api/spider/*``、``/api/tasks/<task_id>/status``
"""

from ._shared import (
    article_service,
    auth_service,
    bp,
    comment_service,
    logger,
    user_repo,
)
from . import (  # noqa: F401  导入即注册路由
    auth_routes,
    data_routes,
    ml_routes,
    spider_routes,
    user_routes,
)

__all__ = [
    "bp",
    "article_service",
    "auth_service",
    "comment_service",
    "user_repo",
    "logger",
]
