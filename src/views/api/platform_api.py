#!/usr/bin/env python3
"""
多平台数据API
统一查询不同平台的数据
"""

import logging
from datetime import datetime, timedelta

from flask import Blueprint, request

from services.platform_collectors import PlatformCollectorFactory
from utils.api_response import error, ok
from utils.query import querys
from utils.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

bp = Blueprint("platform", __name__, url_prefix="/api/platform")

PLATFORM_META = {
    "weibo": {"name": "微博", "icon": "📱"},
    "wechat": {"name": "微信公众号", "icon": "💬"},
    "douyin": {"name": "抖音", "icon": "🎵"},
    "zhihu": {"name": "知乎", "icon": "💡"},
    "bilibili": {"name": "B站", "icon": "📺"},
}


def _parse_demo_mode(default: bool = False) -> bool:
    raw = request.args.get("demo")
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_datetime(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _load_platform_data(platform: str, count: int, demo_mode: bool, keyword: str = None):
    """加载平台数据：默认只返回真实数据，演示模式需显式开启。"""
    if demo_mode:
        return generate_demo_data(platform, count), "demo", True

    # 如果是支持的第三方平台，使用采集器
    if PlatformCollectorFactory.is_supported(platform):
        try:
            collector = PlatformCollectorFactory.get(platform)
            if collector:
                # 使用关键词或默认搜索词
                search_keyword = keyword or "科技"
                contents = collector.collect(search_keyword, count)
                if contents:
                    data = []
                    for item in contents:
                        item_dict = item.to_dict()
                        platform_info = PLATFORM_META.get(platform, PLATFORM_META["weibo"])
                        item_dict["platform_name"] = platform_info["name"]
                        item_dict["platform_icon"] = platform_info["icon"]
                        data.append(item_dict)
                    return data, f"{platform}_collector", False
        except Exception as exc:
            logger.warning(f"从采集器加载 {platform} 数据失败: {exc}")
            # 采集失败时降级到演示数据
            return generate_demo_data(platform, count), f"{platform}_collector_fallback", True

    # 微博平台从文章表加载
    try:
        rows = querys(
            """SELECT id, authorName, isVip, content, likeNum, commentsLen, reposts_count,
                      created_at, region
               FROM article
               ORDER BY created_at DESC
               LIMIT %s""",
            [max(1, min(count, 500))],
            "select",
        )

        if not rows:
            logger.info("平台数据未查询到真实内容")
            return [], "article_table_empty", False

        platform_info = PLATFORM_META.get(platform, PLATFORM_META["weibo"])
        data = []

        for idx, row in enumerate(rows):
            like_count = int(row.get("likeNum") or 0)
            comment_count = int(row.get("commentsLen") or 0)
            repost_count = int(row.get("reposts_count") or 0)
            engagement = like_count + comment_count + repost_count

            data.append(
                {
                    "platform": platform,
                    "platform_name": platform_info["name"],
                    "platform_icon": platform_info["icon"],
                    "content_id": str(row.get("id") or f"{platform}_{idx + 1}"),
                    "author_id": f"author_{idx + 1}",
                    "author_name": row.get("authorName") or "未知用户",
                    "author_verified": bool(row.get("isVip")),
                    "author_followers": max(100, engagement * 5),
                    "content": row.get("content") or "",
                    "like_count": like_count,
                    "comment_count": comment_count,
                    "repost_count": repost_count,
                    "view_count": max(1000, engagement * 20),
                    "published_at": _normalize_datetime(row.get("created_at")),
                    "sentiment": "neutral",
                    "sentiment_score": 0.5,
                    "keywords": [],
                    "location": row.get("region"),
                }
            )

        return data, "article_table", False
    except Exception as exc:
        logger.warning(f"加载真实平台数据失败: {exc}")
        return [], "article_table_error", False


def _summarize_platform_data(data):
    """基于已加载的平台数据计算统计摘要。"""
    total_content = len(data)
    total_likes = sum(int(item.get("like_count") or 0) for item in data)
    total_comments = sum(int(item.get("comment_count") or 0) for item in data)
    total_views = sum(int(item.get("view_count") or 0) for item in data)

    sentiment_distribution = {"positive": 0, "neutral": 0, "negative": 0}
    keyword_counts = {}

    for item in data:
        sentiment = str(item.get("sentiment") or "neutral").lower()
        if sentiment in sentiment_distribution:
            sentiment_distribution[sentiment] += 1
        else:
            sentiment_distribution["neutral"] += 1

        for keyword in item.get("keywords") or []:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

    top_keywords = [
        {"name": name, "count": count}
        for name, count in sorted(
            keyword_counts.items(), key=lambda pair: pair[1], reverse=True
        )[:10]
    ]

    return {
        "total_content": total_content,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_views": total_views,
        "avg_likes": round(total_likes / total_content, 2) if total_content else 0,
        "avg_comments": round(total_comments / total_content, 2)
        if total_content
        else 0,
        "avg_views": round(total_views / total_content, 2) if total_content else 0,
        "sentiment_distribution": sentiment_distribution,
        "top_keywords": top_keywords,
    }


def generate_demo_data(platform: str, count: int = 20):
    """生成演示数据"""
    platform_info = PLATFORM_META.get(platform, PLATFORM_META["weibo"])

    topics = [
        "人工智能",
        "科技创新",
        "新能源",
        "数字经济",
        "绿色发展",
        "智慧城市",
        "乡村振兴",
        "教育改革",
        "医疗健康",
        "文化传承",
    ]

    users = [
        ("user_001", "科技博主", True, 50000),
        ("user_002", "行业专家", True, 30000),
        ("user_003", "资讯搬运工", False, 10000),
        ("user_004", "普通网友", False, 1000),
        ("user_005", "热心市民", False, 500),
    ]

    data = []
    base_time = datetime.now() - timedelta(hours=24)

    for i in range(count):
        user = random.choice(users)
        topic = random.choice(topics)

        item = {
            "platform": platform,
            "platform_name": platform_info["name"],
            "platform_icon": platform_info["icon"],
            "content_id": f"{platform}_{i + 1}",
            "author_id": user[0],
            "author_name": user[1],
            "author_verified": user[2],
            "author_followers": user[3],
            "content": f"关于{topic}的{platform_info['name']}内容讨论... #{i + 1}",
            "like_count": random.randint(0, 10000),
            "comment_count": random.randint(0, 500),
            "repost_count": random.randint(0, 200),
            "view_count": random.randint(1000, 100000),
            "published_at": (
                base_time + timedelta(minutes=random.randint(0, 1440))
            ).isoformat(),
            "sentiment": random.choice(["positive", "neutral", "negative"]),
            "sentiment_score": round(random.uniform(0.3, 0.9), 2),
            "keywords": [topic, f"{topic}相关"],
            "location": random.choice(["北京", "上海", "广东", "浙江", None]),
        }
        data.append(item)

    return data


@bp.route("/list", methods=["GET"])
def list_platforms():
    """获取平台列表"""
    # 使用采集器工厂获取支持的平台列表
    collector_platforms = PlatformCollectorFactory.get_platform_info()
    
    # 添加微博（主平台，不走采集器）
    all_platforms = [
        {"id": "weibo", "name": "微博", "icon": "📱", "enabled": True},
        *collector_platforms,
        {"id": "kuaishou", "name": "快手", "icon": "🎬", "enabled": False},
    ]

    return ok({"platforms": all_platforms}), 200


@bp.route("/data/<platform>", methods=["GET"])
@rate_limit(max_requests=30, window_seconds=60)
def get_platform_data(platform: str):
    """获取指定平台数据"""
    valid_platforms = ["weibo", "wechat", "douyin", "zhihu", "bilibili"]

    if platform not in valid_platforms:
        return error("无效的平台ID", code=400), 400

    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    page_size = min(page_size, 100)

    demo_mode = _parse_demo_mode(default=False)
    all_data, data_source, effective_demo_mode = _load_platform_data(
        platform, 50, demo_mode
    )

    start = (page - 1) * page_size
    end = start + page_size
    page_data = all_data[start:end]

    return ok(
        {
            "platform": platform,
            "demo_mode": effective_demo_mode,
            "data_source": data_source,
            "data": page_data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": len(all_data),
                "total_pages": (len(all_data) + page_size - 1) // page_size,
            },
        }
    ), 200


@bp.route("/all", methods=["GET"])
@rate_limit(max_requests=20, window_seconds=60)
def get_all_platforms_data():
    """获取所有平台汇总数据"""
    platforms = request.args.get("platforms", "weibo,wechat,douyin,zhihu").split(",")
    page_size = request.args.get("page_size", 10, type=int)
    demo_mode = _parse_demo_mode(default=False)

    results = {}
    data_source_map = {}
    effective_demo_mode = False

    for platform in platforms:
        data, source, current_demo_mode = _load_platform_data(
            platform, page_size, demo_mode
        )
        data_source_map[platform] = source
        effective_demo_mode = effective_demo_mode or current_demo_mode

        results[platform] = {
            "count": len(data),
            "total_likes": sum(item["like_count"] for item in data),
            "total_comments": sum(item["comment_count"] for item in data),
            "total_views": sum(item["view_count"] for item in data),
            "data": data[:5],
        }

    return ok(
        {
            "demo_mode": effective_demo_mode,
            "data_source": data_source_map,
            "platforms": results,
            "summary": {
                "total_content": sum(r["count"] for r in results.values()),
                "total_likes": sum(r["total_likes"] for r in results.values()),
                "total_comments": sum(r["total_comments"] for r in results.values()),
            },
        }
    ), 200


@bp.route("/stats/<platform>", methods=["GET"])
@rate_limit(max_requests=30, window_seconds=60)
def get_platform_stats(platform: str):
    """获取平台统计数据"""
    if platform == "all":
        platforms = ["weibo", "wechat", "douyin", "zhihu"]
    else:
        platforms = [platform]

    stats = {}
    demo_mode = _parse_demo_mode(default=False)

    for p in platforms:
        data, data_source, effective_demo_mode = _load_platform_data(p, 100, demo_mode)
        stats[p] = {
            **_summarize_platform_data(data),
            "total_users": len(
                {item.get("author_id") for item in data if item.get("author_id")}
            ),
            "demo_mode": effective_demo_mode,
            "data_source": data_source,
        }

    return ok(stats), 200


@bp.route("/compare", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def compare_platforms():
    """对比多个平台数据"""
    data = request.json
    platforms = data.get("platforms", ["weibo", "wechat"])
    demo_mode = _parse_demo_mode(default=False)

    if len(platforms) < 2:
        return error("至少需要2个平台进行对比", code=400), 400

    comparison = {}

    for platform in platforms:
        platform_data, data_source, effective_demo_mode = _load_platform_data(
            platform, 50, demo_mode
        )
        summary = _summarize_platform_data(platform_data)
        comparison[platform] = {
            **summary,
            "demo_mode": effective_demo_mode,
            "data_source": data_source,
        }

    return ok(
        {
            "comparison": comparison,
            "metrics": ["total_content", "avg_likes", "avg_comments", "avg_views"],
        }
    ), 200
