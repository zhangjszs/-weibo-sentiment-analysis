from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func

from models.user_favorite import UserFavorite

from .base_repository import BaseRepository


class UserFavoriteRepository(BaseRepository):
    def __init__(self):
        super().__init__(UserFavorite)

    def find_by_user_and_article(self, user_id: int, article_id: str) -> Optional[UserFavorite]:
        return (
            self.session.query(UserFavorite)
            .filter(UserFavorite.user_id == user_id)
            .filter(UserFavorite.article_id == article_id)
            .first()
        )

    def find_with_article(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取用户收藏列表（带文章详情）"""
        from models.article import Article

        # Count
        total = (
            self.session.query(func.count(UserFavorite.id))
            .filter(UserFavorite.user_id == user_id)
            .scalar()
            or 0
        )

        # Data with join
        rows = (
            self.session.query(
                UserFavorite.id,
                UserFavorite.article_id,
                UserFavorite.created_at.label("favorited_at"),
                Article.content,
                Article.authorName.label("source"),
                Article.created_at,
                Article.likeNum,
                Article.commentsLen.label("commentNum"),
                Article.reposts_count.label("forwardNum"),
            )
            .outerjoin(Article, UserFavorite.article_id == Article.id)
            .filter(UserFavorite.user_id == user_id)
            .order_by(desc(UserFavorite.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

        results = []
        for r in rows:
            results.append(
                {
                    "id": r.id,
                    "article_id": r.article_id,
                    "favorited_at": str(r.favorited_at),
                    "content": r.content or "",
                    "source": r.source or "",
                    "created_at": str(r.created_at) if r.created_at else "",
                    "like_num": r.likeNum or 0,
                    "comment_num": r.commentNum or 0,
                    "forward_num": r.forwardNum or 0,
                }
            )

        return results, total

    def check_batch(self, user_id: int, article_ids: List[str]) -> Dict[str, bool]:
        """批量检查收藏状态"""
        if not article_ids:
            return {}

        rows = (
            self.session.query(UserFavorite.article_id)
            .filter(UserFavorite.user_id == user_id)
            .filter(UserFavorite.article_id.in_(article_ids))
            .all()
        )
        favorited_set = {r[0] for r in rows}
        return {aid: aid in favorited_set for aid in article_ids}

    def add_favorite(self, user_id: int, article_id: str) -> UserFavorite:
        fav = UserFavorite(user_id=user_id, article_id=article_id)
        self.save(fav)
        return fav

    def remove_favorite(self, user_id: int, article_id: str) -> int:
        deleted = (
            self.session.query(UserFavorite)
            .filter(UserFavorite.user_id == user_id)
            .filter(UserFavorite.article_id == article_id)
            .delete()
        )
        self.session.commit()
        return deleted