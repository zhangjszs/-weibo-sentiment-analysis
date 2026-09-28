from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func

from models.article import Article
from utils.sql_safety import (
    coerce_positive_int,
    escape_like,
    validate_identifier,
)

from .base_repository import BaseRepository

# 直方图允许的数值列白名单（原生 SQL 拼接前必须校验）
ARTICLE_HISTOGRAM_COLUMNS = frozenset({"likeNum", "commentsLen"})


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
            query = query.filter(
                Article.content.like(f"%{escape_like(keyword)}%", escape="\\")
            )

        if article_type:
            query = query.filter(Article.type == article_type)

        if region:
            query = query.filter(
                Article.region.like(f"%{escape_like(region)}%", escape="\\")
            )

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
        result = self.session.query(func.max(Article.created_at)).scalar()
        return result if result else None

    def count_by_date(self, date_str: str) -> int:
        return (
            self.session.query(Article).filter(Article.created_at == date_str).count()
        )

    # === 新增聚合方法，替代裸 SQL ===

    def count_total(self) -> int:
        """文章总数"""
        return self.session.query(func.count(Article.id)).scalar() or 0

    def count_by_type(self) -> List[Dict[str, Any]]:
        """按类型分组统计"""
        rows = (
            self.session.query(Article.type, func.count(Article.id).label("count"))
            .group_by(Article.type)
            .order_by(func.count(Article.id).desc())
            .all()
        )
        return [
            {"type": r.type or "未知", "count": r.count}
            for r in rows
        ]

    def count_by_region(self, limit: int = 1) -> List[Dict[str, Any]]:
        """按地区分组统计（排除空值）"""
        rows = (
            self.session.query(Article.region, func.count(Article.id).label("count"))
            .filter(Article.region.isnot(None))
            .filter(Article.region != "")
            .filter(Article.region != "无")
            .group_by(Article.region)
            .order_by(func.count(Article.id).desc())
            .limit(limit)
            .all()
        )
        return [{"region": r.region, "count": r.count} for r in rows]

    def get_top_liked_author(self) -> Optional[str]:
        """点赞最多文章的作者"""
        row = (
            self.session.query(Article.authorName)
            .order_by(Article.likeNum.desc())
            .first()
        )
        return row[0] if row else None

    def count_by_date_range(self) -> List[Dict[str, Any]]:
        """按日期分组统计（用于趋势图，按 DATE 截断分组，避免按秒 GROUP BY）"""
        day = func.date(Article.created_at).label("day")
        rows = (
            self.session.query(day, func.count(Article.id).label("count"))
            .group_by(day)
            .order_by(day.desc())
            .all()
        )
        return [{"created_at": str(r.day), "count": r.count} for r in rows]

    def get_distinct_types(self) -> List[str]:
        """获取所有文章类型"""
        rows = (
            self.session.query(Article.type)
            .filter(Article.type.isnot(None))
            .filter(Article.type != "")
            .distinct()
            .order_by(Article.type)
            .all()
        )
        return [r[0] for r in rows]

    def get_region_distribution(self) -> List[Dict[str, Any]]:
        """文章地域分布"""
        rows = (
            self.session.query(Article.region, func.count(Article.id).label("count"))
            .filter(Article.region.isnot(None))
            .filter(Article.region != "")
            .filter(Article.region != "无")
            .group_by(Article.region)
            .order_by(func.count(Article.id).desc())
            .all()
        )
        return [{"name": r.region, "value": r.count} for r in rows]

    def get_histogram(
        self,
        column: str,
        exclude_type: Optional[str] = None,
        range_num: int = 1000,
        bucket_count: int = 14,
    ) -> Tuple[List[str], List[int]]:
        """
        文章数值直方图（likeNum / commentsLen）
        使用 CASE WHEN 分桶
        """
        validate_identifier(column, ARTICLE_HISTOGRAM_COLUMNS)
        range_num = coerce_positive_int(range_num, 1000, maximum=100000)
        bucket_count = coerce_positive_int(bucket_count, 14, maximum=100)
        labels = [f"{range_num * i}-{range_num * (i + 1)}" for i in range(1, bucket_count + 1)]
        counts = [0] * len(labels)

        # 构建 CASE WHEN
        case_lines = []
        for idx in range(bucket_count):
            upper_bound = range_num * (idx + 2)
            case_lines.append(
                f"WHEN COALESCE({column}, 0) < {upper_bound} THEN {idx}"
            )

        where_clause = "WHERE type IS NOT NULL AND type != ''"
        params: dict[str, Any] = {}
        if exclude_type:
            where_clause += " AND type <> :exclude_type"
            params["exclude_type"] = exclude_type

        sql = f"""
            SELECT bucket_index, COUNT(*) AS count
            FROM (
                SELECT
                    CASE
                        {' '.join(case_lines)}
                        ELSE NULL
                    END AS bucket_index
                FROM article
                {where_clause}
            ) buckets
            WHERE bucket_index IS NOT NULL
            GROUP BY bucket_index
            ORDER BY bucket_index
        """

        from database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(text(sql), params)
            for row in result:
                bucket_index = int(row[0])
                if 0 <= bucket_index < len(counts):
                    counts[bucket_index] = int(row[1])

        return labels, counts

    def get_recent_texts(self, limit: int = 200) -> List[str]:
        """获取最近文章内容用于情感/词云分析"""
        rows = (
            self.session.query(Article.content)
            .filter(Article.content.isnot(None))
            .filter(Article.content != "")
            .order_by(Article.created_at.desc())
            .limit(max(1, min(limit, 1000)))
            .all()
        )
        return [r[0] for r in rows if r[0]]

    # === data_api 专用 ===

    def get_type_distribution(self) -> List[Dict[str, Any]]:
        """文章类型分布（饼图格式）"""
        rows = (
            self.session.query(Article.type, func.count(Article.id).label("count"))
            .group_by(Article.type)
            .order_by(func.count(Article.id).desc())
            .all()
        )
        return [
            {"name": r.type if r.type else "未知", "value": r.count}
            for r in rows
        ]
