from typing import Any, Dict, List, Tuple

from sqlalchemy import desc

from models.comment import Comment

from .base_repository import BaseRepository


class CommentRepository(BaseRepository):
    def __init__(self):
        super().__init__(Comment)

    def find_with_filter(
        self,
        keyword: str = "",
        article_id: str = "",
        user: str = "",
        start_time: str = "",
        end_time: str = "",
        limit: int = 10,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query = self.session.query(Comment)

        if article_id:
            query = query.filter(Comment.articleId == article_id)

        if user:
            query = query.filter(Comment.user.like(f"%{user}%"))

        if keyword:
            query = query.filter(Comment.content.like(f"%{keyword}%"))

        if start_time and end_time:
            query = query.filter(Comment.created_at.between(start_time, end_time))

        total = query.count()
        rows = (
            query.order_by(desc(Comment.created_at)).limit(limit).offset(offset).all()
        )

        result: List[Dict[str, Any]] = []
        for c in rows:
            comment_id = f"{c.articleId}_{c.created_at}"
            result.append(
                {
                    "id": comment_id,
                    "articleId": c.articleId,
                    "rootId": c.rootId,
                    "content": c.content,
                    "likeNum": c.likeNum,
                    "created_at": c.created_at,
                    "user": c.user,
                }
            )

        return result, total
