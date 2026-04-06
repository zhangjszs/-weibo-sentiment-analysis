#!/usr/bin/env python3
"""
审计日志API模块
功能：管理员查看安全审计日志
"""

import logging

from flask import Blueprint, request

from utils.api_response import error, ok
from utils.authz import admin_required
from utils.log_sanitizer import SafeLogger
from utils.query import querys

logger = SafeLogger("audit_api", logging.INFO)

audit_bp = Blueprint("audit", __name__, url_prefix="/api/audit")


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

        # Build query
        where_clauses = []
        params = []

        if action_filter:
            where_clauses.append("action = %s")
            params.append(action_filter)

        if username_filter:
            where_clauses.append("username LIKE %s")
            params.append(f"%{username_filter}%")

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        # Count
        count_result = querys(
            f"SELECT COUNT(*) as total FROM audit_log{where_sql}", params, "select"
        )
        total = count_result[0]["total"] if count_result else 0

        # Data
        items = querys(
            f"""SELECT id, user_id, username, action, detail, ip, created_at
                FROM audit_log{where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s""",
            params + [limit, offset],
            "select",
        )

        results = []
        for item in items or []:
            results.append(
                {
                    "id": item.get("id"),
                    "user_id": item.get("user_id"),
                    "username": item.get("username", ""),
                    "action": item.get("action", ""),
                    "detail": item.get("detail", ""),
                    "ip": item.get("ip", ""),
                    "created_at": str(item.get("created_at", "")),
                }
            )

        return ok(
            {
                "items": results,
                "total": total,
                "page": page,
                "limit": limit,
            }
        ), 200
    except Exception as e:
        logger.error(f"获取审计日志异常: {e}")
        return error("服务器内部错误", code=500), 500
