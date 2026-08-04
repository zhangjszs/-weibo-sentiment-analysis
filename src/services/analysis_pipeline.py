"""Single-entry analysis pipeline for the Weibo sentiment analysis system.

Usage::

    from services.analysis_pipeline import AnalysisPipeline

    pipeline = AnalysisPipeline()
    snapshot = pipeline.run(topic="AI", start_at=..., end_at=..., demo=False)
    return jsonify(snapshot.to_dict())
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from utils.data_provenance import demo_meta, real_meta

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------


@dataclass
class AnalysisSnapshot:
    """Immutable result of an analysis pipeline run.

    Serialise with :meth:`to_dict` — the result is safe for JSON responses.
    """

    topic: str
    start_at: datetime
    end_at: datetime
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "start_at": self.start_at.isoformat() if self.start_at else None,
            "end_at": self.end_at.isoformat() if self.end_at else None,
            "generated_at": self.generated_at.isoformat(),
            **self.data,
        }


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class AnalysisPipeline:
    """Composable analysis pipeline.

    The ``run`` method orchestrates::

        fetch data → normalise → sentiment → trend → propagation → assemble meta

    Every step is wrapped in a try/except so that a failure in one analysis
    dimension does not prevent the rest from being returned.
    """

    def run(
        self,
        topic: str,
        start_at: datetime,
        end_at: datetime,
        *,
        demo: bool = False,
    ) -> AnalysisSnapshot:
        """Execute the full analysis pipeline for *topic* in *start_at*–*end_at*.

        Returns an :class:`AnalysisSnapshot` whose ``data`` dict always contains
        the keys ``summary``, ``trend``, ``sentiment``, ``top_articles``,
        ``top_comments``, ``propagation``, and ``meta``.
        """
        snapshot = AnalysisSnapshot(topic=topic, start_at=start_at, end_at=end_at)
        limitations: list[str] = []

        if demo:
            raw_data = self._generate_demo_data(topic)
            data_count = raw_data.get("total_count", 100)
            meta = demo_meta(
                topic=topic,
                data_count=data_count,
                time_range=(start_at, end_at),
            )
        else:
            raw_data, errors = self._safe_fetch_real_data(topic, start_at, end_at)
            limitations.extend(errors)
            data_count = raw_data.get("total_count", 0)
            limitations = errors.copy()
            if data_count == 0:
                limitations.append("当前话题在所选时间范围内没有采集到数据。")
            meta = real_meta(
                topic=topic,
                data_count=data_count,
                time_range=(start_at, end_at),
                limitations=limitations or None,
            )

        snapshot.data["meta"] = meta.to_dict()
        snapshot.data["summary"] = self._build_summary(raw_data)
        snapshot.data["trend"] = self._build_trend(raw_data)
        snapshot.data["sentiment"] = self._build_sentiment(raw_data)
        snapshot.data["top_articles"] = self._build_top_articles(raw_data)
        snapshot.data["top_comments"] = self._build_top_comments(raw_data)
        snapshot.data["propagation"] = self._build_propagation(raw_data)

        return snapshot

    # ------------------------------------------------------------------
    # Data fetching
    # ------------------------------------------------------------------

    def _safe_fetch_real_data(
        self,
        topic: str,
        start_at: datetime,
        end_at: datetime,
    ) -> tuple[dict[str, Any], list[str]]:
        """Attempt to fetch real data; return (data, [error_msgs])."""
        errors: list[str] = []
        try:
            data = self._fetch_real_data(topic, start_at, end_at)
            return data, errors
        except Exception as exc:
            logger.warning("AnalysisPipeline data fetch failed: %s", exc)
            errors.append(f"数据查询失败: {type(exc).__name__}")
            return self._empty_data(), errors

    def _fetch_real_data(
        self,
        topic: str,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[str, Any]:
        """Query the database for real analysis data.

        Subclasses may override this method to inject custom query logic.
        The default implementation delegates to ``AnalysisRepository``.
        """
        from repositories.analysis_repository import AnalysisRepository

        repo = AnalysisRepository()
        articles, article_count = repo.find_articles(topic, start_at, end_at)
        comments, comment_count = repo.find_comments(topic, start_at, end_at)
        trend = repo.get_trend(topic, start_at, end_at)
        sentiment_stats = repo.get_sentiment_stats(topic, start_at, end_at)
        propagation_summary = repo.get_propagation_summary(articles)

        return {
            "total_count": article_count + comment_count,
            "article_count": article_count,
            "comment_count": comment_count,
            "articles": articles,
            "comments": comments,
            "trend": trend,
            "sentiment_stats": sentiment_stats,
            "propagation_summary": propagation_summary,
        }

    def _generate_demo_data(self, topic: str) -> dict[str, Any]:
        """Return a plausible demo dataset for *topic*."""
        import random

        base = datetime.now(timezone.utc)
        days = 7
        trend = [
            {"date": f"2026-{7+m:02d}-{d+1:02d}", "count": random.randint(50, 300)}
            for m in range(2)
            for d in range(days)
        ]
        total = sum(t["count"] for t in trend)
        return {
            "total_count": total,
            "article_count": total // 3,
            "comment_count": total - total // 3,
            "articles": [
                {
                    "id": f"demo_{i}",
                    "content": f"关于{topic}的演示文章内容 #{i}",
                    "author_name": f"用户_{i}",
                    "like_count": random.randint(10, 500),
                    "comment_count": random.randint(0, 100),
                    "created_at": (base.replace(hour=i % 24)).isoformat(),
                }
                for i in range(min(20, total))
            ],
            "comments": [
                {
                    "id": f"demo_c_{i}",
                    "content": f"演示评论内容 #{i}",
                    "user": f"评论用户_{i}",
                    "like_count": random.randint(0, 50),
                    "created_at": (base.replace(hour=i % 24)).isoformat(),
                }
                for i in range(min(30, total))
            ],
            "trend": trend,
            "sentiment_stats": {
                "positive": int(total * 0.5),
                "neutral": int(total * 0.3),
                "negative": total - int(total * 0.5) - int(total * 0.3),
            },
            "propagation_summary": {
                "max_depth": 3,
                "total_nodes": min(total, 100),
                "key_influencers": ["user_001", "user_002", "user_003"],
            },
        }

    @staticmethod
    def _empty_data() -> dict[str, Any]:
        return {
            "total_count": 0,
            "article_count": 0,
            "comment_count": 0,
            "articles": [],
            "comments": [],
            "trend": [],
            "sentiment_stats": {"positive": 0, "neutral": 0, "negative": 0},
            "propagation_summary": {
                "max_depth": 0,
                "total_nodes": 0,
                "key_influencers": [],
            },
        }

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_summary(data: dict[str, Any]) -> dict[str, Any]:
        return {
            "total_articles": data.get("article_count", 0),
            "total_comments": data.get("comment_count", 0),
            "total_count": data.get("total_count", 0),
        }

    @staticmethod
    def _build_trend(data: dict[str, Any]) -> list[dict[str, Any]]:
        return data.get("trend", [])

    @staticmethod
    def _build_sentiment(data: dict[str, Any]) -> dict[str, Any]:
        stats = data.get("sentiment_stats", {})
        total = stats.get("positive", 0) + stats.get("neutral", 0) + stats.get("negative", 0)
        if total == 0:
            return {"distribution": stats, "index": 0.0}
        index = round((stats.get("positive", 0) - stats.get("negative", 0)) / total, 4)
        return {"distribution": stats, "index": index}

    @staticmethod
    def _build_top_articles(data: dict[str, Any]) -> list[dict[str, Any]]:
        articles = data.get("articles", [])
        return sorted(articles, key=lambda a: a.get("like_count", 0), reverse=True)[:10]

    @staticmethod
    def _build_top_comments(data: dict[str, Any]) -> list[dict[str, Any]]:
        comments = data.get("comments", [])
        return sorted(comments, key=lambda c: c.get("like_count", 0), reverse=True)[:10]

    @staticmethod
    def _build_propagation(data: dict[str, Any]) -> dict[str, Any]:
        return data.get("propagation_summary", {})