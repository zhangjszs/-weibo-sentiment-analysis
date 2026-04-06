from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc

from models.article import Article

from .base_repository import BaseRepository


class ArticleRepository(BaseRepository):
    def __init__(self):
        super().__init__(Article)

    def find_with_filter(
        self,
        keyword: str = "",
        start_time: str = "",
        end_time: str = "",
        article_type: str = "",
        region: str = "",
        limit: int = 10,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query = self.session.query(Article)

        if keyword:
            query = query.filter(Article.content.like(f"%{keyword}%"))

        if article_type:
            query = query.filter(Article.type == article_type)

        if region:
            query = query.filter(Article.region.like(f"%{region}%"))

        if start_time and end_time:
            query = query.filter(Article.created_at.between(start_time, end_time))

        total = query.count()

        articles = (
            query.order_by(desc(Article.created_at)).limit(limit).offset(offset).all()
        )

        result = []
        for a in articles:
            result.append(
                {
                    "id": a.id,
                    "likeNum": a.likeNum,
                    "commentsLen": a.commentsLen,
                    "reposts_count": a.reposts_count,
                    "region": a.region,
                    "content": a.content,
                    "contentLen": a.contentLen,
                    "created_at": a.created_at,
                    "type": a.type,
                    "detailUrl": a.detailUrl,
                    "authorAvatar": a.authorAvatar,
                    "authorName": a.authorName,
                    "authorDetail": a.authorDetail,
                    "isVip": a.isVip,
                }
            )

        return result, total

    def get_latest_update_time(self) -> Optional[str]:
        # Using session query directly for aggregate
        from sqlalchemy import func

        result = self.session.query(func.max(Article.created_at)).scalar()
        return result if result else None

    def count_by_date(self, date_str: str) -> int:
        return (
            self.session.query(Article).filter(Article.created_at == date_str).count()
        )
