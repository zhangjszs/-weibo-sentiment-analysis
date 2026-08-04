"""安全审计日志服务

记录关键用户操作，支持登录/登出/报告导出/数据删除/爬虫启动/配置修改等事件。
审计日志写入失败不应影响业务流程。
"""

from __future__ import annotations

import logging

from utils.log_sanitizer import SafeLogger
from utils.query import querys

logger = SafeLogger("audit_service", logging.INFO)

# 允许的审计事件类型
VALID_ACTIONS = {
    "login",
    "logout",
    "register",
    "change_password",
    "export_report",
    "delete_data",
    "spider_start",
    "config_change",
}


# 已知审计事件类型
VALID_ACTIONS = {
    "login",
    "logout",
    "register",
    "change_password",
    "export_report",
    "delete_data",
    "spider_start",
    "config_change",
    "sensitive_action",  # test only
}


def _coerce_str(val: object, max_len: int) -> str:
    """Convert *val* to a truncated string."""
    return str(val)[:max_len] if not isinstance(val, str) else val[:max_len]


def audit_log(
    user_id: int | None,
    username: str,
    action: str,
    detail: str = "",
    ip: str = "",
) -> int | None:
    """
    写入审计日志。

    写入失败不应影响业务流程。未知 action 类型会被记录警告但仍尝试写入。
    """
    if action not in VALID_ACTIONS:
        logger.warning(f"未知审计事件类型: {action}")

    try:
        result = querys(
            """INSERT INTO audit_log (user_id, username, action, detail, ip)
               VALUES (%s, %s, %s, %s, %s)""",
            [
                user_id,
                _coerce_str(username, 50),
                _coerce_str(action, 50),
                _coerce_str(detail, 500),
                _coerce_str(ip, 45),
            ],
            "insert",
        )
        if isinstance(result, (int, str)):
            return int(result) if result else None
        return None
    except Exception as e:
        logger.error(f"审计日志写入失败: {e}")
        return None


def log_export_report(
    user_id: int, username: str, topic: str, fmt: str, ip: str = ""
) -> int | None:
    """记录报告导出事件。"""
    return audit_log(
        user_id=user_id,
        username=username,
        action="export_report",
        detail=f"topic={topic}, format={fmt}",
        ip=ip,
    )


def log_delete_data(
    user_id: int,
    username: str,
    resource_type: str,
    resource_id: str,
    ip: str = "",
) -> int | None:
    """记录数据删除事件。"""
    return audit_log(
        user_id=user_id,
        username=username,
        action="delete_data",
        detail=f"resource_type={resource_type}, resource_id={resource_id}",
        ip=ip,
    )


def log_spider_start(
    user_id: int, username: str, keyword: str, crawl_type: str, ip: str = ""
) -> int | None:
    """记录爬虫启动事件。"""
    return audit_log(
        user_id=user_id,
        username=username,
        action="spider_start",
        detail=f"keyword={keyword}, type={crawl_type}",
        ip=ip,
    )