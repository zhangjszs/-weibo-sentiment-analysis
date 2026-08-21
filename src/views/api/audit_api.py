#!/usr/bin/env python3
"""
审计日志API模块
功能：管理员查看安全审计日志
"""

import logging

from flask import Blueprint, request

from ._shared import API_PREFIX

from utils.api_response import error, ok
from utils.authz import admin_required
from utils.log_sanitizer import SafeLogger
from repositories.audit_repository import AuditRepository

logger = SafeLogger("audit_api", logging.INFO)

audit_bp = Blueprint("audit", __name__, url_prefix=API_PREFIX + "/audit")


def _audit_repo() -> AuditRepository:
    return AuditRepository()


@audit_bp.route("/logs", methods=["GET"])
@admin_required
def get_audit_logs():
    """获取审计日志列表（分页，仅管理员）"""
    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = min(100, max(1, int(request.args.get("limit", 20))))
        offset = (page - 1) * limit

        action_filter = request.args.get("action", "").strip()
        username_filter = request.args.get("username", "").strip()

        items, total = _audit_repo().find_with_filter(
            action=action_filter,
            username=username_filter,
            limit=limit,
            offset=offset,
        )

        return ok(
            {
                "items": items,
                "total": total,
                "page": page,
                "limit": limit,
            }
        ), 200
    except Exception as e:
        logger.error(f"获取审计日志异常: {e}")
        return error("服务器内部错误", code=500), 500