from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import asc, desc, func

from models.repost import Repost
from models.user import User

from .base_repository import BaseRepository


class RepostRepository(BaseRepository):
    def __init__(self):
        super().__init__(Repost)

    def find_by_article(
        self,
        article_id: str,
        limit: int = 500,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """按文章ID查找转发记录"""
        query = self.session.query(Repost).filter(Repost.article_id == article_id)

        total = query.count()

        rows = (
            query.order_by(asc(Repost.created_at)).limit(limit).offset(offset).all()
        )

        result = []
        for r in rows:
            result.append(
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "article_id": r.article_id,
                    "content": r.content,
                    "post_time": r.created_at,
                    "repost_count": r.repost_count,
                    "comment_count": r.comment_count,
                    "like_count": r.like_count,
                    "depth": r.depth,
                    "parent_id": r.parent_id,
                }
            )

        return result, total

    def find_with_users(
        self,
        article_id: str,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """查找转发记录并关联用户名"""
        rows, _ = self.find_by_article(article_id, limit=limit)

        if not rows:
            return []

        user_ids = sorted({str(r.get("user_id") or "") for r in rows if r.get("user_id")})
        user_name_map = {}

        if user_ids and len(user_ids) <= 1000:
            # 批量查询用户名
            users = (
                self.session.query(User.id, User.username)
                .filter(User.id.in_([int(uid) for uid in user_ids if uid.isdigit()]))
                .all()
            )
            user_name_map = {str(u.id): u.username for u in users}

        normalized = []
        for row in rows:
            copied = dict(row)
            user_id = str(copied.get("user_id") or "")
            copied["user_name"] = user_name_map.get(user_id) or f"用户{user_id or '未知'}"
            normalized.append(copied)

        return normalized