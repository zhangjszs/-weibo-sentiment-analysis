#!/usr/bin/env python3
"""
收藏管理API模块
功能：文章收藏/取消收藏、收藏列表查询
"""

import logging

from flask import Blueprint, request

from utils.api_response import error, ok
from utils.log_sanitizer import SafeLogger
from utils.query import querys

logger = SafeLogger("favorites_api", logging.INFO)

favorites_bp = Blueprint("favorites", __name__, url_prefix="/api/favorites")


@favorites_bp.route("/<article_id>", methods=["POST"])
def add_favorite(article_id):
    """添加收藏"""
    user = getattr(request, "current_user", None)
    if not user:
        return error("未认证", code=401), 401

    try:
        article_id = str(article_id).strip()[:50]
        if not article_id:
            return error("文章ID不能为空", code=400), 400

        # Check if already favorited
        existing = querys(
            "SELECT id FROM user_favorites WHERE user_id = %s AND article_id = %s",
            [user["user_id"], article_id],
            "select",
        )
        if existing:
            return ok(msg="已收藏"), 200

        querys(
            "INSERT INTO user_favorites (user_id, article_id) VALUES (%s, %s)",
            [user["user_id"], article_id],
            "insert",
        )
        return ok(msg="收藏成功"), 200
    except Exception as e:
        logger.error(f"添加收藏异常: {e}")
        return error("服务器内部错误", code=500), 500


@favorites_bp.route("/<article_id>", methods=["DELETE"])
def remove_favorite(article_id):
    """取消收藏"""
    user = getattr(request, "current_user", None)
    if not user:
        return error("未认证", code=401), 401

    try:
        article_id = str(article_id).strip()[:50]
        querys(
            "DELETE FROM user_favorites WHERE user_id = %s AND article_id = %s",
            [user["user_id"], article_id],
            "delete",
        )
        return ok(msg="已取消收藏"), 200
    except Exception as e:
        logger.error(f"取消收藏异常: {e}")
        return error("服务器内部错误", code=500), 500


@favorites_bp.route("/check/<article_id>", methods=["GET"])
def check_favorite(article_id):
    """检查是否已收藏"""
    user = getattr(request, "current_user", None)
    if not user:
        return error("未认证", code=401), 401

    try:
        article_id = str(article_id).strip()[:50]
        existing = querys(
            "SELECT id FROM user_favorites WHERE user_id = %s AND article_id = %s",
            [user["user_id"], article_id],
            "select",
        )
        return ok({"favorited": bool(existing)}), 200
    except Exception as e:
        logger.error(f"检查收藏状态异常: {e}")
        return error("服务器内部错误", code=500), 500


@favorites_bp.route("", methods=["GET"])
def list_favorites():
    """获取收藏列表（分页，含文章信息）"""
    user = getattr(request, "current_user", None)
    if not user:
        return error("未认证", code=401), 401

    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = min(50, max(1, int(request.args.get("limit", 10))))
        offset = (page - 1) * limit

        # Count total
        count_result = querys(
            "SELECT COUNT(*) as total FROM user_favorites WHERE user_id = %s",
            [user["user_id"]],
            "select",
        )
        total = count_result[0]["total"] if count_result else 0

        # Get favorites with article details
        items = querys(
            """SELECT f.id, f.article_id, f.created_at AS favorited_at,
                      a.content, a.authorName AS source, a.created_at,
                      a.likeNum, a.commentsLen AS commentNum, a.reposts_count AS forwardNum
               FROM user_favorites f
               LEFT JOIN article a ON f.article_id = a.id
               WHERE f.user_id = %s
               ORDER BY f.created_at DESC
               LIMIT %s OFFSET %s""",
            [user["user_id"], limit, offset],
            "select",
        )

        results = []
        for item in items or []:
            results.append(
                {
                    "id": item.get("id"),
                    "article_id": item.get("article_id"),
                    "favorited_at": str(item.get("favorited_at", "")),
                    "content": item.get("content", ""),
                    "source": item.get("source", ""),
                    "created_at": str(item.get("created_at", "")),
                    "like_num": item.get("likeNum", 0),
                    "comment_num": item.get("commentNum", 0),
                    "forward_num": item.get("forwardNum", 0),
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
        logger.error(f"获取收藏列表异常: {e}")
        return error("服务器内部错误", code=500), 500


@favorites_bp.route("/batch-check", methods=["POST"])
def batch_check_favorites():
    """批量检查收藏状态"""
    user = getattr(request, "current_user", None)
    if not user:
        return error("未认证", code=401), 401

    try:
        data = request.get_json(silent=True) or {}
        article_ids = data.get("article_ids", [])
        if not article_ids or not isinstance(article_ids, list):
            return ok({"favorites": {}}), 200

        # Limit batch size
        article_ids = [str(aid).strip() for aid in article_ids[:100]]
        placeholders = ",".join(["%s"] * len(article_ids))
        params = [user["user_id"]] + article_ids

        results = querys(
            f"SELECT article_id FROM user_favorites WHERE user_id = %s AND article_id IN ({placeholders})",
            params,
            "select",
        )

        favorited_set = {r["article_id"] for r in (results or [])}
        favorites = {aid: aid in favorited_set for aid in article_ids}

        return ok({"favorites": favorites}), 200
    except Exception as e:
        logger.error(f"批量检查收藏异常: {e}")
        return error("服务器内部错误", code=500), 500
