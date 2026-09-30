from typing import Any

from sqlalchemy import desc, func

from models.comment import Comment
from utils.sql_safety import coerce_positive_int, escape_like

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
    ) -> tuple[list[dict[str, Any]], int]:
        query = self.session.query(Comment)

        if article_id:
            query = query.filter(Comment.articleId == article_id)

        if user:
            query = query.filter(
                Comment.user.like(f"%{escape_like(user)}%", escape="\\")
            )

        if keyword:
            query = query.filter(
                Comment.content.like(f"%{escape_like(keyword)}%", escape="\\")
            )

        if start_time and end_time:
            query = query.filter(Comment.created_at.between(start_time, end_time))

        total = query.count()
        rows = (
            query.order_by(desc(Comment.created_at)).limit(limit).offset(offset).all()
        )

        result: list[dict[str, Any]] = []
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

    # === 新增聚合方法，替代裸 SQL ===

    def count_total(self) -> int:
        """评论总数"""
        return self.session.query(func.count(Comment.comment_id)).scalar() or 0

    def get_top_liked_comments(self, limit: int = 4) -> list[dict[str, Any]]:
        """点赞最多的评论（含作者信息）"""
        rows = (
            self.session.query(
                Comment.articleId,
                Comment.created_at,
                Comment.likeNum,
                Comment.region,
                Comment.content,
                Comment.user,
                Comment.authorGender,
                Comment.authorAddress,
                Comment.authorAvatar,
            )
            .order_by(Comment.likeNum.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "articleId": r.articleId,
                "created_at": r.created_at,
                "like_counts": r.likeNum,
                "region": r.region,
                "content": r.content,
                "authorName": r.user,
                "authorGender": r.authorGender,
                "authorAddress": r.authorAddress,
                "authorAvatar": r.authorAvatar,
            }
            for r in rows
        ]

    def count_by_date_range(self) -> list[dict[str, Any]]:
        """按日期分组统计（created_at 为文本：按前 10 位截断分组，避免按秒 GROUP BY）"""
        day = func.substr(Comment.created_at, 1, 10).label("day")
        rows = (
            self.session.query(day, func.count(Comment.comment_id).label("count"))
            .filter(Comment.created_at.isnot(None))
            .group_by(day)
            .order_by(day.desc())
            .all()
        )
        return [{"created_at": str(r.day), "count": r.count} for r in rows]

    def get_all_for_export(self, limit: int = 1000) -> list[dict[str, Any]]:
        """导出评论（SQL 侧 LIMIT，默认 1000，避免全量 .all() OOM）"""
        rows = self.session.query(Comment).limit(max(1, min(limit, 10000))).all()
        return [
            {
                "comment_id": c.comment_id,
                "articleId": c.articleId,
                "created_at": c.created_at,
                "content": c.content,
                "like_counts": c.likeNum,
                "authorName": c.user,
                "region": c.region,
                "authorGender": c.authorGender,
                "authorAddress": c.authorAddress,
                "authorAvatar": c.authorAvatar,
                "user_id": c.user_id,
                "reply_count": c.reply_count,
                "comment_source": c.comment_source,
                "is_hot": c.is_hot,
                "parent_id": c.parent_id,
                "reply_to_user": c.reply_to_user,
                "verified_type": c.verified_type,
                "followers_count": c.followers_count,
            }
            for c in rows
        ]

    def search_by_content(self, keyword: str, limit: int = 1000) -> list[dict[str, Any]]:
        """根据内容关键词搜索评论"""
        rows = (
            self.session.query(
                Comment.articleId,
                Comment.created_at,
                Comment.likeNum,
                Comment.region,
                Comment.content,
                Comment.user,
                Comment.authorGender,
                Comment.authorAddress,
                Comment.authorAvatar,
            )
            .filter(Comment.content.like(f"%{escape_like(keyword)}%", escape="\\"))
            .order_by(Comment.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "articleId": r.articleId,
                "created_at": r.created_at,
                "like_counts": r.likeNum,
                "region": r.region,
                "content": r.content,
                "authorName": r.user,
                "authorGender": r.authorGender,
                "authorAddress": r.authorAddress,
                "authorAvatar": r.authorAvatar,
            }
            for r in rows
        ]

    def get_region_distribution(self) -> list[dict[str, Any]]:
        """评论地域分布"""
        rows = (
            self.session.query(Comment.region, func.count(Comment.comment_id).label("count"))
            .filter(Comment.region.isnot(None))
            .filter(Comment.region != "")
            .filter(Comment.region != "无")
            .group_by(Comment.region)
            .order_by(func.count(Comment.comment_id).desc())
            .all()
        )
        return [{"name": r.region, "value": r.count} for r in rows]

    def get_gender_distribution(self) -> list[dict[str, Any]]:
        """评论性别分布"""
        rows = (
            self.session.query(Comment.authorGender, func.count(Comment.comment_id).label("count"))
            .filter(Comment.authorGender.isnot(None))
            .filter(Comment.authorGender != "")
            .group_by(Comment.authorGender)
            .order_by(func.count(Comment.comment_id).desc())
            .all()
        )
        return [{"name": r.authorGender, "value": r.count} for r in rows]

    def get_like_histogram(
        self,
        range_num: int = 20,
        bucket_count: int = 99,
    ) -> tuple[list[str], list[int]]:
        """
        评论点赞数直方图
        使用 CASE WHEN 分桶
        """
        range_num = coerce_positive_int(range_num, 20, maximum=100000)
        bucket_count = coerce_positive_int(bucket_count, 99, maximum=100)
        labels = [f"{range_num * i}-{range_num * (i + 1)}" for i in range(1, bucket_count + 1)]
        counts = [0] * len(labels)

        case_lines = []
        for idx in range(bucket_count):
            upper_bound = range_num * (idx + 2)
            case_lines.append(
                f"WHEN COALESCE(likeNum, 0) < {upper_bound} THEN {idx}"
            )

        sql = f"""
            SELECT bucket_index, COUNT(*) AS count
            FROM (
                SELECT
                    CASE
                        {' '.join(case_lines)}
                        ELSE NULL
                    END AS bucket_index
                FROM comments
            ) buckets
            WHERE bucket_index IS NOT NULL
            GROUP BY bucket_index
            ORDER BY bucket_index
        """

        from sqlalchemy import text

        from database import engine

        with engine.connect() as conn:
            result = conn.execute(text(sql))
            for row in result:
                bucket_index = int(row[0])
                if 0 <= bucket_index < len(counts):
                    counts[bucket_index] = int(row[1])

        return labels, counts

    def get_recent_texts(self, limit: int = 200) -> list[str]:
        """获取最近评论内容用于情感/词云分析"""
        rows = (
            self.session.query(Comment.content)
            .filter(Comment.content.isnot(None))
            .filter(Comment.content != "")
            .order_by(Comment.created_at.desc())
            .limit(max(1, min(limit, 1000)))
            .all()
        )
        return [r[0] for r in rows if r[0]]

    # === data_api 专用 ===

    def get_hour_distribution(self, limit: int = 5000) -> dict[str, list[Any]]:
        """评论小时分布（0-23点，Python 侧分桶：跨方言，不用 func.hour MySQL 方言）"""
        rows = (
            self.session.query(Comment.created_at)
            .filter(Comment.created_at.isnot(None))
            .order_by(Comment.created_at.desc())
            .limit(max(1, min(limit, 20000)))
            .all()
        )
        hours = [f"{h}:00" for h in range(24)]
        counts = [0] * 24
        for (created_at,) in rows:
            try:
                hour = int(str(created_at).split(" ")[1].split(":")[0])
            except (IndexError, ValueError, AttributeError):
                continue
            if 0 <= hour < 24:
                counts[hour] += 1
        return {"hours": hours, "counts": counts}

    def get_top_active_users(self, limit: int = 10) -> dict[str, list[Any]]:
        """评论最活跃用户"""
        rows = (
            self.session.query(Comment.user, func.count(Comment.comment_id).label("count"))
            .filter(Comment.user.isnot(None))
            .filter(Comment.user != "")
            .group_by(Comment.user)
            .order_by(func.count(Comment.comment_id).desc(), Comment.user)
            .limit(limit)
            .all()
        )
        return {
            "users": [r.user for r in rows],
            "counts": [r.count for r in rows],
        }

    def get_recent_comments(self, limit: int = 100) -> list[tuple[str, str]]:
        """获取最近评论（时间, 内容）"""
        rows = (
            self.session.query(Comment.created_at, Comment.content)
            .filter(Comment.content.isnot(None))
            .filter(Comment.content != "")
            .order_by(Comment.created_at.desc())
            .limit(limit)
            .all()
        )
        return [(str(r.created_at), str(r.content)) for r in rows]

    def get_hot_comments(self, limit: int = 5) -> list[dict[str, Any]]:
        """热门评论（点赞数降序）"""
        rows = (
            self.session.query(
                Comment.created_at,
                Comment.likeNum,
                Comment.content,
                Comment.user,
            )
            .order_by(Comment.likeNum.desc(), Comment.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "user": str(r.user or "未知用户"),
                "time": str(r.created_at or ""),
                "content": str(r.content or ""),
                "likes": int(r.likeNum or 0),
                "replies": 0,
            }
            for r in rows
        ]

    def get_ip_list(self, limit: int = 10) -> list[dict[str, Any]]:
        """IP/地区分布列表（作者地址去重统计）"""
        rows = (
            self.session.query(
                func.max(Comment.user).label("authorName"),
                Comment.authorAddress,
                func.count(Comment.comment_id).label("count"),
                func.max(Comment.created_at).label("last_time"),
            )
            .filter(Comment.authorAddress.isnot(None))
            .filter(Comment.authorAddress != "")
            .group_by(Comment.authorAddress)
            .order_by(func.count(Comment.comment_id).desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "ip": "",
                "location": r.authorAddress,
                "count": r.count,
                "lastTime": str(r.last_time),
                "user": r.authorName,
            }
            for r in rows
        ]

    def get_recent_trend(self, days: int = 7) -> list[dict[str, Any]]:
        """最近 N 天评论数趋势"""
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)
        rows = (
            self.session.query(Comment.created_at, func.count(Comment.comment_id).label("count"))
            .filter(Comment.created_at >= cutoff)
            .group_by(Comment.created_at)
            .order_by(Comment.created_at)
            .all()
        )
        return [{"date": str(r.created_at), "count": r.count} for r in rows]
