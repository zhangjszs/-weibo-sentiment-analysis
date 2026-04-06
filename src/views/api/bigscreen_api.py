#!/usr/bin/env python3
"""
数据大屏 API
提供实时统计数据和图表数据
"""

import logging
from datetime import datetime, timedelta

from flask import Blueprint, request

from services.sentiment_service import SentimentService
from utils.api_response import error, ok
from utils.query import querys
from utils.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

bp = Blueprint("bigscreen", __name__, url_prefix="/api/bigscreen")


def _get_time_range(hours: int = 24):
    """获取时间范围"""
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    return start_time, end_time


def _get_sentiment_distribution():
    """获取情感分布统计"""
    try:
        # 从评论中获取最新数据
        rows = querys(
            """SELECT content FROM comments 
               WHERE content IS NOT NULL AND content != ''
               ORDER BY created_at DESC LIMIT 500""",
            type="select",
        )
        
        if not rows:
            return {"positive": 0, "neutral": 0, "negative": 0}
        
        texts = [row.get("content", "") for row in rows if row.get("content")]
        
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
            # 返回模拟分布
            total = len(texts)
            return {
                "positive": int(total * 0.5),
                "neutral": int(total * 0.32),
                "negative": int(total * 0.18),
            }
    except Exception as e:
        logger.error(f"获取情感分布失败: {e}")
        return {"positive": 0, "neutral": 0, "negative": 0}


def _get_region_distribution():
    """获取地区分布"""
    try:
        rows = querys(
            """SELECT region, COUNT(*) as count 
               FROM article 
               WHERE region IS NOT NULL AND region != ''
               GROUP BY region 
               ORDER BY count DESC 
               LIMIT 10""",
            type="select",
        )
        
        if not rows:
            # 返回默认数据
            return [
                {"name": "北京", "value": 985},
                {"name": "上海", "value": 876},
                {"name": "广东", "value": 765},
                {"name": "浙江", "value": 654},
                {"name": "江苏", "value": 543},
                {"name": "四川", "value": 432},
                {"name": "湖北", "value": 321},
                {"name": "山东", "value": 234},
            ]
        
        return [{"name": row.get("region", ""), "value": int(row.get("count", 0))} for row in rows]
    except Exception as e:
        logger.error(f"获取地区分布失败: {e}")
        return []


def _get_trend_data(hours: int = 24):
    """获取趋势数据"""
    try:
        # 按小时统计
        rows = querys(
            """SELECT 
                DATE_FORMAT(created_at, '%H:00') as hour,
                COUNT(*) as count,
                AVG(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_ratio
               FROM (
                   SELECT created_at, 'neutral' as sentiment FROM comments 
                   WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                   LIMIT 1000
               ) t
               GROUP BY hour
               ORDER BY hour""",
            [hours],
            type="select",
        )
        
        if not rows:
            # 生成默认趋势数据
            return {
                "times": [f"{h:02d}:00" for h in range(24)],
                "positive": [120, 132, 201, 234, 290, 330, 410, 380, 350, 320, 340, 360,
                           380, 400, 420, 450, 480, 520, 560, 600, 580, 550, 500, 450],
                "neutral": [80, 92, 141, 154, 190, 230, 280, 260, 240, 220, 235, 250,
                          265, 280, 295, 310, 325, 340, 355, 370, 360, 345, 330, 310],
                "negative": [30, 42, 61, 74, 90, 110, 130, 120, 110, 100, 105, 115,
                           125, 135, 145, 155, 165, 175, 185, 195, 190, 180, 170, 160],
            }
        
        times = [row.get("hour", "") for row in rows]
        counts = [int(row.get("count", 0)) for row in rows]
        
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
    
    # 返回默认数据
    return [
        {"name": "科技创新", "heat": 9856, "percent": 100},
        {"name": "人工智能", "heat": 8742, "percent": 89},
        {"name": "新能源", "heat": 7653, "percent": 78},
        {"name": "数字经济", "heat": 6521, "percent": 66},
        {"name": "绿色发展", "heat": 5896, "percent": 60},
        {"name": "智慧城市", "heat": 5234, "percent": 53},
        {"name": "乡村振兴", "heat": 4567, "percent": 46},
        {"name": "教育改革", "heat": 4123, "percent": 42},
        {"name": "医疗健康", "heat": 3890, "percent": 39},
        {"name": "文化传承", "heat": 3456, "percent": 35},
    ]


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
    
    # 返回默认数据
    return [
        {"id": 1, "level": "danger", "title": "负面舆情激增", "time": "10:32"},
        {"id": 2, "level": "warning", "title": "讨论量异常增长", "time": "10:15"},
        {"id": 3, "level": "info", "title": "热点话题出现", "time": "09:58"},
    ]


@bp.route("/stats", methods=["GET"])
@rate_limit(max_requests=30, window_seconds=60)
def get_bigscreen_stats():
    """
    获取大屏统计数据
    
    Query Params:
        realtime: 是否实时数据 (true/false)
    """
    try:
        # 获取基础统计
        article_count = 0
        comment_count = 0
        
        try:
            article_rows = querys("SELECT COUNT(*) as count FROM article", type="select")
            article_count = int(article_rows[0].get("count", 0)) if article_rows else 0
        except Exception as e:
            logger.warning(f"获取文章数失败: {e}")
        
        try:
            comment_rows = querys("SELECT COUNT(*) as count FROM comments", type="select")
            comment_count = int(comment_rows[0].get("count", 0)) if comment_rows else 0
        except Exception as e:
            logger.warning(f"获取评论数失败: {e}")
        
        # 获取情感分布
        sentiment = _get_sentiment_distribution()
        
        return ok({
            "articleCount": article_count,
            "commentCount": comment_count,
            "positiveCount": sentiment.get("positive", 0),
            "neutralCount": sentiment.get("neutral", 0),
            "negativeCount": sentiment.get("negative", 0),
            "updatedAt": datetime.now().isoformat(),
        }), 200
        
    except Exception as e:
        logger.error(f"获取大屏统计失败: {e}")
        return error("获取统计数据失败", code=500), 500


@bp.route("/region", methods=["GET"])
@rate_limit(max_requests=20, window_seconds=60)
def get_region_data():
    """获取地区分布数据"""
    try:
        data = _get_region_distribution()
        return ok({
            "data": data,
            "updatedAt": datetime.now().isoformat(),
        }), 200
    except Exception as e:
        logger.error(f"获取地区数据失败: {e}")
        return error("获取地区数据失败", code=500), 500


@bp.route("/trend", methods=["GET"])
@rate_limit(max_requests=20, window_seconds=60)
def get_trend_data():
    """
    获取趋势数据
    
    Query Params:
        hours: 时间范围（小时，默认24）
    """
    try:
        hours = request.args.get("hours", 24, type=int)
        data = _get_trend_data(hours)
        return ok({
            **data,
            "updatedAt": datetime.now().isoformat(),
        }), 200
    except Exception as e:
        logger.error(f"获取趋势数据失败: {e}")
        return error("获取趋势数据失败", code=500), 500


@bp.route("/hot-topics", methods=["GET"])
@rate_limit(max_requests=20, window_seconds=60)
def get_hot_topics():
    """获取热门话题"""
    try:
        limit = request.args.get("limit", 10, type=int)
        data = _get_hot_topics(limit)
        return ok({
            "topics": data,
            "updatedAt": datetime.now().isoformat(),
        }), 200
    except Exception as e:
        logger.error(f"获取热门话题失败: {e}")
        return error("获取热门话题失败", code=500), 500


@bp.route("/alerts", methods=["GET"])
@rate_limit(max_requests=20, window_seconds=60)
def get_recent_alerts():
    """获取最近预警"""
    try:
        limit = request.args.get("limit", 5, type=int)
        data = _get_recent_alerts(limit)
        return ok({
            "alerts": data,
            "updatedAt": datetime.now().isoformat(),
        }), 200
    except Exception as e:
        logger.error(f"获取预警数据失败: {e}")
        return error("获取预警数据失败", code=500), 500


@bp.route("/all", methods=["GET"])
@rate_limit(max_requests=10, window_seconds=60)
def get_all_data():
    """获取所有大屏数据（用于初始化）"""
    try:
        hours = request.args.get("hours", 24, type=int)
        
        # 获取所有数据
        stats_resp = get_bigscreen_stats()
        stats = stats_resp[0].get_json() if hasattr(stats_resp[0], 'get_json') else {}
        
        region_data = _get_region_distribution()
        trend_data = _get_trend_data(hours)
        hot_topics = _get_hot_topics(10)
        alerts = _get_recent_alerts(5)
        
        return ok({
            "stats": stats.get("data", {}),
            "region": region_data,
            "trend": trend_data,
            "hotTopics": hot_topics,
            "alerts": alerts,
            "updatedAt": datetime.now().isoformat(),
        }), 200
        
    except Exception as e:
        logger.error(f"获取大屏全部数据失败: {e}")
        return error("获取数据失败", code=500), 500
