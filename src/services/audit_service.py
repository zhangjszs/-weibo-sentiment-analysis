#!/usr/bin/env python3
"""
安全审计日志服务
功能：记录关键用户操作（登录/登出/注册/修改密码等）
"""

import logging

from utils.log_sanitizer import SafeLogger
from utils.query import querys

logger = SafeLogger("audit_service", logging.INFO)


def audit_log(user_id, username, action, detail="", ip=""):
    """
    写入审计日志

    Args:
        user_id: 用户ID（未登录时为 None）
        username: 用户名
        action: 操作类型，如 login, register, change_password, logout
        detail: 操作细节
        ip: 客户端IP
    """
    try:
        querys(
            """INSERT INTO audit_log (user_id, username, action, detail, ip)
               VALUES (%s, %s, %s, %s, %s)""",
            [
                user_id,
                str(username)[:50],
                str(action)[:50],
                str(detail)[:500],
                str(ip)[:45],
            ],
            "insert",
        )
    except Exception as e:
        # 审计日志写入失败不应影响业务流程
        logger.error(f"审计日志写入失败: {e}")
