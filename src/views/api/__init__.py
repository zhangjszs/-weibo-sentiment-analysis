"""API 蓝图统一注册入口（A3）。

P2 拆分后，``_shared.bp`` 是唯一的 api 蓝图（name="api"，prefix="/api"）；
各领域蓝图已收敛为 ``domain_bp`` 命名（alert_bp, platform_bp 等），
避免同名 ``bp`` 在 ``__init__`` 集中导入时产生 F811/覆盖。

本模块暴露 :func:`register_api` 供 ``src/app.py:create_app`` 调用，
集中完成 ``app.register_blueprint`` 与 ``csrf.exempt``。

向后兼容
----------
- ``from views.api import api`` 仍可用（``api.py`` 保留，对外导出 ``bp``）
- ``from views.api._shared import bp`` 仍为唯一的 api 蓝图
- 旧引用 ``from views.api.alert_api import bp`` 仍可用（各模块保留 ``bp = domain_bp`` 别名）
"""

from __future__ import annotations


def register_api(app, csrf=None):  # type: ignore[no-untyped-def]
    """统一注册所有 ``/api/*`` 蓝图并做 CSRF 豁免。

    Args:
        app: Flask 应用实例
        csrf: ``CSRFProtect`` 实例（可选），提供则对所有 API 蓝图做 ``exempt``

    Returns:
        已注册的蓝图列表（按注册顺序）
    """
    # 中央 API 蓝图（聚合 auth/data/ml/user/spider_routes 等，定义于 _shared/api）
    # isort: off
    from .alert_api import alert_bp
    from .api import bp as api_bp
    from .audit_api import audit_bp
    from .bigscreen_api import bigscreen_bp
    from .favorites_api import favorites_bp
    from .platform_api import platform_bp
    from .propagation_api import propagation_bp
    from .report_api import report_bp
    from .spider_api import spider_bp
    from .v1_analysis import v1_analysis_bp
    # isort: on

    # 数据蓝图（A1 已收敛至 /api，保留在此统一注册以便后续进一步合并到单蓝图）
    try:
        from views.data.data_api import db as data_bp
    except Exception:  # pragma: no cover - 导入失败时降级为不注册
        data_bp = None

    # 注册顺序保持与原 src/app.py 一致，便于 diff 与日志比对
    blueprints = [
        api_bp,
        data_bp,
        spider_bp,
        alert_bp,
        propagation_bp,
        report_bp,
        platform_bp,
        favorites_bp,
        audit_bp,
        bigscreen_bp,
        v1_analysis_bp,
    ]
    # 过滤 None（data_bp 导入失败时）
    blueprints = [bp for bp in blueprints if bp is not None]

    registered = []
    for bp in blueprints:
        # 避免在同一进程内重复注册同一 name（测试中 create_app 多次调用）
        if bp.name in app.blueprints:
            # 已注册则仅确保 CSRF 豁免
            if csrf is not None:
                try:
                    csrf.exempt(bp)
                except Exception:
                    pass
            continue
        app.register_blueprint(bp)
        if csrf is not None:
            try:
                csrf.exempt(bp)
            except Exception:
                pass
        registered.append(bp)

    return registered


__all__ = ["register_api"]
