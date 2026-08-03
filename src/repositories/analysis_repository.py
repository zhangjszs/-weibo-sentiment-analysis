"""Repository for aggregated analysis queries.

This repository is the only data-access point for ``AnalysisPipeline``.
It delegates to specialised repositories where possible but keeps the
query API focused on the analytical use case (topic + time range).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from repositories.article_repository import ArticleRepository
from repositories.comment_repository import CommentRepository

logger = logging.getLogger(__name__)


class AnalysisRepository:
    """Aggregated data access for the analysis pipeline."""

    def __init__(self) -> None:
        self._article_repo = ArticleRepository()
        self._comment_repo = CommentRepository()

    # ------------------------------------------------------------------
    # Articles
    # ------------------------------------------------------------------

    def find_articles(
        self,
        topic: str,
        start_at: datetime,
        end_at: datetime,
        limit: int = 50,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return (articles, total_count) filtered by topic and time range."""
        try:
            articles, total = self._article_repo.find_with_filter(
                keyword=topic,
                start_time=start_at.isoformat() if start_at else "",
                end_time=end_at.isoformat() if end_at else "",
                limit=limit,
                offset=0,
            )
            return articles, total
        except Exception as exc:
            logger.warning("AnalysisRepository.find_articles failed: %s", exc)
            return [], 0

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    def find_comments(
        self,
        topic: str,
        start_at: datetime,
        end_at: datetime,
        limit: int = 100,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return (comments, total_count) filtered by topic and time range."""
        try:
            comments, total = self._comment_repo.find_with_filter(
                keyword=topic,
                start_time=start_at.isoformat() if start_at else "",
                end_time=end_at.isoformat() if end_at else "",
                limit=limit,
                offset=0,
            )
            return comments, total
        except Exception as exc:
            logger.warning("AnalysisRepository.find_comments failed: %s", exc)
            return [], 0

    # ------------------------------------------------------------------
    # Trend
    # ------------------------------------------------------------------

    def get_trend(
        self,
        topic: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[dict[str, Any]]:
        """Return daily count trend over the given time range."""
        try:
            rows = self._comment_repo.get_recent_trend(days=7)
            return [
                {"date": str(r.get("date", "")), "count": int(r.get("count", 0))}
                for r in rows
                if r.get("date")
            ]
        except Exception as exc:
            logger.warning("AnalysisRepository.get_trend failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Sentiment stats
    # ------------------------------------------------------------------

    def get_sentiment_stats(
        self,
        topic: str,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[str, int]:
        """Return positive / neutral / negative counts."""
        try:
            from services.sentiment_service import SentimentService

            comment_rows, total_count = self.find_comments(topic, start_at, end_at, limit=200)
            texts = [c.get("content", "") for c in comment_rows if isinstance(c, dict) and c.get("content")]
            if not texts:
                return {"positive": 0, "neutral": 0, "negative": 0}

            distribution = SentimentService.analyze_distribution(
                texts, mode="simple", sample_size=len(texts)
            )
            return {
                "positive": int(distribution.get("正面", 0)),
                "neutral": int(distribution.get("中性", 0)),
                "negative": int(distribution.get("负面", 0)),
            }
        except Exception as exc:
            logger.warning("AnalysisRepository.get_sentiment_stats failed: %s", exc)
            return {"positive": 0, "neutral": 0, "negative": 0}

    # ------------------------------------------------------------------
    # Propagation summary
    # ------------------------------------------------------------------

    def get_propagation_summary(
        self,
        articles: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Return a lightweight propagation summary based on article metadata."""
        total_reposts = sum(int(a.get("reposts_count", 0)) for a in articles)
        return {
            "max_depth": 0,
            "total_nodes": total_reposts,
            "key_influencers": [],
        }