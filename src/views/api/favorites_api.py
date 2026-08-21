#!/usr/bin/env python3
"""
收藏管理API模块
功能：文章收藏/取消收藏、收藏列表查询
"""

import logging

from flask import Blueprint, request

from ._shared import API_PREFIX

from utils.api_response import error, ok
from utils.log_sanitizer import SafeLogger
from repositories.user_favorite_repository import UserFavoriteRepository

logger = SafeLogger("favorites_api", logging.INFO)

favorites_bp = Blueprint("favorites", __name__, url_prefix=API_PREFIX + "/favorites")


def _fav_repo() -> UserFavoriteRepository:
    return UserFavoriteRepository()


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
        existing = _fav_repo().find_by_user_and_article(user["user_id"], article_id)
        if existing:
            return ok(msg="已收藏"), 200

        _fav_repo().add_favorite(user["user_id"], article_id)
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
        _fav_repo().remove_favorite(user["user_id"], article_id)
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
        existing = _fav_repo().find_by_user_and_article(user["user_id"], article_id)
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

        items, total = _fav_repo().find_with_article(
            user_id=user["user_id"], limit=limit, offset=offset
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

        favorites = _fav_repo().check_batch(user["user_id"], article_ids)

        return ok({"favorites": favorites}), 200
    except Exception as e:
        logger.error(f"批量检查收藏异常: {e}")
        return error("服务器内部错误", code=500), 500