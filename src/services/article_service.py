from typing import Any, Dict

from repositories.article_repository import ArticleRepository


class ArticleService:
    def __init__(self):
        self.article_repo = ArticleRepository()

    def get_articles(
        self,
        page: int,
        limit: int,
        keyword: str,
        start_time: str,
        end_time: str,
        article_type: str = "",
        region: str = "",
    ) -> Dict[str, Any]:
        offset = (page - 1) * limit
        articles, total = self.article_repo.find_with_filter(
            keyword, start_time, end_time, article_type, region, limit, offset
        )

        # Format dates
        for item in articles:
            if "created_at" in item and item["created_at"]:
                item["created_at"] = str(item["created_at"])

        return {"total": total, "page": page, "limit": limit, "list": articles}

    def get_stats_summary(self) -> Dict[str, int]:
        # This assumes other repositories exist, for now we use ArticleRepository as the entry point
        # In a full refactor, we'd inject other repos or have a dedicated StatsService
        from utils.query import (
            querys,  # Fallback for now to avoid creating too many files at once
        )

        article_count = self.article_repo.count()
        comment_count = querys("SELECT count(*) as count FROM comments", type="select")[
            0
        ]["count"]
        user_count = querys("SELECT count(*) as count FROM user", type="select")[0][
            "count"
        ]

        return {
            "articles": article_count,
            "comments": comment_count,
            "users": user_count,
        }

    def get_today_stats(self) -> Dict[str, Any]:
        """获取今日新增统计与最新更新时间。"""
        from datetime import date

        from utils.query import querys

        today = date.today().strftime("%Y-%m-%d")

        article_rows = querys(
            "SELECT count(*) as count FROM article WHERE DATE(created_at) = %s",
            [today],
            type="select",
        )
        comment_rows = querys(
            "SELECT count(*) as count FROM comments WHERE DATE(created_at) = %s",
            [today],
            type="select",
        )
        latest = self.article_repo.get_latest_update_time()

        today_articles = int(article_rows[0].get("count", 0)) if article_rows else 0
        today_comments = int(comment_rows[0].get("count", 0)) if comment_rows else 0

        return {
            "today_articles": today_articles,
            "today_comments": today_comments,
            "latest_update": str(latest) if latest else None,
        }
