#!/usr/bin/env python3
"""
数据大屏 API
提供实时统计数据和图表数据
"""

import logging
from datetime import datetime, timedelta

from flask import Blueprint, request

from repositories.article_repository import ArticleRepository
from repositories.comment_repository import CommentRepository
from services.sentiment_service import SentimentService
from utils.api_response import error, ok
from utils.rate_limiter import rate_limit
from utils.request_validation import get_int_arg

from ._shared import API_PREFIX

logger = logging.getLogger(__name__)

bigscreen_bp = Blueprint("bigscreen", __name__, url_prefix=API_PREFIX + "/bigscreen")

bp = bigscreen_bp  # 兼容旧引用：from views.api.bigscreen_api import bp


def _article_repo() -> ArticleRepository:
    return ArticleRepository()


def _comment_repo() -> CommentRepository:
    return CommentRepository()


# 显式演示数据：仅当路由收到 ?demo=true 且真实数据缺失时返回。
# 默认一律返回真实数据，缺失即为空（不再静默伪造）。
_DEMO_SENTIMENT = {"positive": 5023, "neutral": 3218, "negative": 1759}
_DEMO_REGION = [
    {"name": "北京", "value": 985},
    {"name": "上海", "value": 876},
    {"name": "广东", "value": 765},
    {"name": "浙江", "value": 654},
    {"name": "江苏", "value": 543},
    {"name": "四川", "value": 432},
    {"name": "湖北", "value": 321},
    {"name": "山东", "value": 234},
]
_DEMO_TREND = {
    "times": [f"{h:02d}:00" for h in range(24)],
    "counts": [120, 132, 201, 234, 290, 330, 410, 380, 350, 320, 340, 360,
               380, 400, 420, 450, 480, 520, 560, 600, 580, 550, 500, 450],
}
_DEMO_TOPICS = [
    {"name": "科技创新", "heat": 9856, "percent": 100},
    {"name": "人工智能", "heat": 8742, "percent": 89},
    {"name": "新能源", "heat": 7653, "percent": 78},
    {"name": "数字经济", "heat": 6521, "percent": 66},
    {"name": "绿色发展", "heat": 5896, "percent": 60},
]
_DEMO_ALERTS = [
    {"id": 1, "level": "danger", "title": "负面舆情激增", "time": "10:32"},
    {"id": 2, "level": "warning", "title": "讨论量异常增长", "time": "10:15"},
    {"id": 3, "level": "info", "title": "热点话题出现", "time": "09:58"},
]


def _demo_requested() -> bool:
    """是否显式请求演示数据（?demo=true）。"""
    return request.args.get("demo", "false").lower() == "true"


def _get_time_range(hours: int = 24):
    """获取时间范围"""
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    return start_time, end_time


def _get_sentiment_distribution():
    """获取情感分布统计"""
    try:
        # 从评论中获取最新数据
        texts = _comment_repo().get_recent_texts(limit=500)

        if not texts:
            return {"positive": 0, "neutral": 0, "negative": 0}

        # 使用情感分析服务
        try:
            distribution = SentimentService.analyze_distribution(texts, mode="simple", sample_size=200)
            return {
                "positive": distribution.get("正面", 0),
                "neutral": distribution.get("中性", 0),
                "negative": distribution.get("负面", 0),
            }
        except Exception as e:
            logger.warning(f"情感分析失败: {e}")
            # 不伪造按比例分布：缺失即返回 0（模拟数据仅 demo=true 显式请求时给）
            return {"positive": 0, "neutral": 0, "negative": 0}
    except Exception as e:
        logger.error(f"获取情感分布失败: {e}")
        return {"positive": 0, "neutral": 0, "negative": 0}


def _get_region_distribution():
    """获取地区分布"""
    try:
        articles = _article_repo().get_region_distribution()

        if not articles:
            # 缺失返回空；模拟数据仅 demo=true 显式请求时由路由层注入
            return []

        return articles
    except Exception as e:
        logger.error(f"获取地区分布失败: {e}")
        return []


def _get_trend_data(hours: int = 24):
    """获取趋势数据"""
    try:
        comments = _comment_repo().count_by_date_range()

        if not comments:
            # 缺失返回空趋势；模拟数据仅 demo=true 显式请求时由路由层注入
            return {"times": [], "counts": []}

        times = [comment.get("created_at", "") for comment in comments]
        counts = [int(comment.get("count", 0)) for comment in comments]

        return {
            "times": times,
            "counts": counts,
        }
    except Exception as e:
        logger.error(f"获取趋势数据失败: {e}")
        return {"times": [], "counts": []}


def _get_hot_topics(limit: int = 10):
    """获取热门话题"""
    try:
        # 从热词统计获取
        from utils.getPublicData import getAllCiPingTotal

        hot_words = getAllCiPingTotal()
        if hot_words and len(hot_words) > 0:
            max_heat = hot_words[0][1] if hot_words[0][1] > 0 else 1
            return [
                {
                    "name": item[0],
                    "heat": int(item[1]),
                    "percent": int((item[1] / max_heat) * 100) if max_heat > 0 else 0,
                }
                for item in hot_words[:limit]
            ]
    except Exception as e:
        logger.warning(f"获取热词失败: {e}")

    # 缺失返回空；模拟数据仅 demo=true 显式请求时由路由层注入
    return []


def _get_recent_alerts(limit: int = 5):
    """获取最近预警"""
    try:
        from services.alert_service import alert_engine

        alerts = alert_engine.get_alert_history(limit=limit)
        if alerts:
            return [
                {
                    "id": alert.get("id", i),
                    "level": alert.get("level", "info"),
                    "title": alert.get("title", ""),
                    "time": alert.get("created_at", "")[-5:] if alert.get("created_at") else "--:--",
                }
                for i, alert in enumerate(alerts)
            ]
    except Exception as e:
        logger.warning(f"获取预警失败: {e}")

    # 缺失返回空；模拟数据仅 demo=true 显式请求时由路由层注入
    return []


@bigscreen_bp.route("/stats", methods=["GET"])
@rate_limit(max_requests=30, window_seconds=60)
def get_bigscreen_stats():
    """
    获取大屏统计数据

    Query Params:
        realtime: 是否实时数据 (true/false)
    """
    try:
        # 获取基础统计
        article_count = _article_repo().count_total()
        comment_count = _comment_repo().count_total()

        # 获取情感分布
        sentiment = _get_sentiment_distribution()
        demo_used = _demo_requested() and sum(sentiment.values()) == 0
        if demo_used:
            sentiment = dict(_DEMO_SENTIMENT)

        return ok({
            "articleCount": article_count,
            "commentCount": comment_count,
            "positiveCount": sentiment.get("positive", 0),
            "neutralCount": sentiment.get("neutral", 0),
            "negativeCount": sentiment.get("negative", 0),
            "demo_mode": demo_used,
            "updatedAt": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"获取大屏统计失败: {e}")
        return error("获取统计数据失败", code=500), 500


@bigscreen_bp.route("/region", methods=["GET"])
@rate_limit(max_requests=20, window_seconds=60)
def get_region_data():
    """获取地区分布数据"""
    try:
        data = _get_region_distribution()
        demo_used = _demo_requested() and not data
        if demo_used:
            data = list(_DEMO_REGION)
        return ok({
            "data": data,
            "demo_mode": demo_used,
            "updatedAt": datetime.now().isoformat(),
        }), 200
    except Exception as e:
        logger.error(f"获取地区数据失败: {e}")
        return error("获取地区数据失败", code=500), 500


@bigscreen_bp.route("/trend", methods=["GET"])
@rate_limit(max_requests=20, window_seconds=60)
def get_trend_data():
    """
    获取趋势数据

    Query Params:
        hours: 时间范围（小时，默认24）
    """
    try:
        hours = get_int_arg("hours", 24, min_value=1, max_value=168)
        data = _get_trend_data(hours)
        demo_used = _demo_requested() and not data.get("times")
        if demo_used:
            data = dict(_DEMO_TREND)
        return ok({
            **data,
            "demo_mode": demo_used,
            "updatedAt": datetime.now().isoformat(),
        }), 200
    except Exception as e:
        logger.error(f"获取趋势数据失败: {e}")
        return error("获取趋势数据失败", code=500), 500


@bigscreen_bp.route("/hot-topics", methods=["GET"])
@rate_limit(max_requests=20, window_seconds=60)
def get_hot_topics():
    """获取热门话题"""
    try:
        limit = get_int_arg("limit", 10, min_value=1, max_value=50)
        data = _get_hot_topics(limit)
        demo_used = _demo_requested() and not data
        if demo_used:
            data = list(_DEMO_TOPICS)
        return ok({
            "topics": data,
            "demo_mode": demo_used,
            "updatedAt": datetime.now().isoformat(),
        }), 200
    except Exception as e:
        logger.error(f"获取热门话题失败: {e}")
        return error("获取热门话题失败", code=500), 500


@bigscreen_bp.route("/alerts", methods=["GET"])
@rate_limit(max_requests=20, window_seconds=60)
def get_recent_alerts():
    """获取最近预警"""
    try:
        limit = get_int_arg("limit", 5, min_value=1, max_value=50)
        data = _get_recent_alerts(limit)
        demo_used = _demo_requested() and not data
        if demo_used:
            data = list(_DEMO_ALERTS)
        return ok({
            "alerts": data,
            "demo_mode": demo_used,
            "updatedAt": datetime.now().isoformat(),
        }), 200
    except Exception as e:
        logger.error(f"获取预警数据失败: {e}")
        return error("获取预警数据失败", code=500), 500


@bigscreen_bp.route("/all", methods=["GET"])
@rate_limit(max_requests=10, window_seconds=60)
def get_all_data():
    """获取所有大屏数据（用于初始化）"""
    try:
        hours = get_int_arg("hours", 24, min_value=1, max_value=168)
        demo = _demo_requested()

        # 获取所有数据
        article_count = _article_repo().count_total()
        comment_count = _comment_repo().count_total()

        sentiment = _get_sentiment_distribution()
        demo_sentiment = demo and sum(sentiment.values()) == 0
        if demo_sentiment:
            sentiment = dict(_DEMO_SENTIMENT)
        stats = {
            "articleCount": article_count,
            "commentCount": comment_count,
            "positiveCount": sentiment.get("positive", 0),
            "neutralCount": sentiment.get("neutral", 0),
            "negativeCount": sentiment.get("negative", 0),
        }

        region_data = _get_region_distribution()
        demo_region = demo and not region_data
        if demo_region:
            region_data = list(_DEMO_REGION)
        trend_data = _get_trend_data(hours)
        demo_trend = demo and not trend_data.get("times")
        if demo_trend:
            trend_data = dict(_DEMO_TREND)
        hot_topics = _get_hot_topics(10)
        demo_topics = demo and not hot_topics
        if demo_topics:
            hot_topics = list(_DEMO_TOPICS)
        alerts = _get_recent_alerts(5)
        demo_alerts = demo and not alerts
        if demo_alerts:
            alerts = list(_DEMO_ALERTS)

        return ok({
            "stats": stats,
            "region": region_data,
            "trend": trend_data,
            "hotTopics": hot_topics,
            "alerts": alerts,
            "demo_mode": demo and any(
                [demo_sentiment, demo_region, demo_trend, demo_topics, demo_alerts]
            ),
            "updatedAt": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"获取大屏全部数据失败: {e}")
        return error("获取数据失败", code=500), 500
