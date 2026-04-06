from typing import Any, Dict

from repositories.comment_repository import CommentRepository


class CommentService:
    def __init__(self):
        self.comment_repo = CommentRepository()

    def get_comments(
        self,
        page: int,
        limit: int,
        keyword: str,
        article_id: str,
        user: str,
        start_time: str,
        end_time: str,
    ) -> Dict[str, Any]:
        offset = (page - 1) * limit
        comments, total = self.comment_repo.find_with_filter(
            keyword=keyword,
            article_id=article_id,
            user=user,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset,
        )

        for item in comments:
            if "created_at" in item and item["created_at"]:
                item["created_at"] = str(item["created_at"])

        return {"total": total, "page": page, "limit": limit, "list": comments}
