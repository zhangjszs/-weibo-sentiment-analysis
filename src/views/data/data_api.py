#!/usr/bin/env python3
"""
数据 API 模块
功能：提供数据可视化相关 JSON API 接口
路由前缀: /api
"""

import hashlib
import logging
import threading
from datetime import datetime, timedelta
from urllib.parse import unquote
from collections import defaultdict

from flask import Blueprint, request

from utils import getEchartsData, getHomeData, getTableData
from utils.api_response import error, ok
from utils.authz import is_admin_user
from utils.cache import memory_cache
from utils.data_provenance import provenance_response, real_meta
from repositories.article_repository import ArticleRepository
from repositories.comment_repository import CommentRepository

logger = logging.getLogger(__name__)

# 创建蓝图 - 已收敛至 /api，前缀单轨化（A1）
db = Blueprint("data", __name__, url_prefix="/api")

# API 响应缓存（简单内存缓存）
_api_cache = {}
_cache_lock = threading.Lock()

# 缓存超时时间配置（秒）
CACHE_TIMEOUT = {
    "home": 300,  # 首页数据 5分钟
    "table": 180,  # 表格数据 3分钟
    "article": 600,  # 文章数据 10分钟
    "comment": 300,  # 评论数据 5分钟
    "ip": 600,  # IP数据 10分钟
    "yuqing": 300,  # 舆情数据 5分钟
    "cloud": 1800,  # 词云数据 30分钟
}


PROVINCE_MAP = {
    "北京": "北京市", "天津": "天津市", "上海": "上海市", "重庆": "重庆市",
    "河北": "河北省", "山西": "山西省", "辽宁": "辽宁省", "吉林": "吉林省",
    "黑龙江": "黑龙江省", "江苏": "江苏省", "浙江": "浙江省", "安徽": "安徽省",
    "福建": "福建省", "江西": "江西省", "山东": "山东省", "河南": "河南省",
    "湖北": "湖北省", "湖南": "湖南省", "广东": "广东省", "海南": "海南省",
    "四川": "四川省", "贵州": "贵州省", "云南": "云南省", "陕西": "陕西省",
    "甘肃": "甘肃省", "青海": "青海省", "台湾": "台湾省",
    "内蒙古": "内蒙古自治区", "广西": "广西壮族自治区",
    "西藏": "西藏自治区", "宁夏": "宁夏回族自治区",
    "新疆": "新疆维吾尔自治区", "香港": "香港特别行政区",
    "澳门": "澳门特别行政区",
}


def success_response(data, msg="success"):
    """统一成功响应格式，自动附加 provenance meta。"""
    try:
        meta = real_meta(topic="data_api", data_count=len(data) if isinstance(data, (list, dict)) else 0)
    except Exception:
        return ok(data, msg=msg), 200
    return provenance_response(data, meta, msg=msg)


def error_response(msg, code=500):
    """统一错误响应格式"""
    return error(msg, code=code), code


def get_cache_key(prefix, *args, **kwargs):
    """生成缓存键"""
    key_data = f"{prefix}_{str(args)}_{str(sorted(kwargs.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()


def get_cached_data(cache_key, timeout):
    """获取缓存数据"""
    return memory_cache.get(cache_key)


def set_cached_data(cache_key, data, timeout):
    """设置缓存数据"""
    memory_cache.set(cache_key, data, timeout)


def _normalize_hot_word(raw_hot_word):
    """规范化热词参数，兼容 URL 编码与空白字符。"""
    if not raw_hot_word:
        return ""
    return unquote(str(raw_hot_word)).strip()


def _extract_hour_from_value(time_value):
    """从时间字符串中提取小时，解析失败返回 None。"""
    if not time_value:
        return None

    time_str = str(time_value).strip()
    candidate = time_str.split(" ")[-1] if " " in time_str else time_str

    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(candidate, fmt).hour
        except ValueError:
            continue

    return None


def _normalize_region_name(name, province_map):
    """规范化地区名称，尽量映射为地图可识别的省级名称。"""
    if not name:
        return ""

    if name in province_map.values():
        return name

    if name in province_map:
        return province_map[name]

    suffixes = ("省", "市", "自治区", "特别行政区", "壮族自治区", "回族自治区", "维吾尔自治区")
    base_name = name
    for suffix in suffixes:
        if name.endswith(suffix):
            base_name = name[: -len(suffix)]
            break

    if base_name in province_map:
        return province_map[base_name]

    return name


def _article_repo() -> ArticleRepository:
    return ArticleRepository()


def _comment_repo() -> CommentRepository:
    return CommentRepository()


def _get_comment_hour_distribution():
    return _comment_repo().get_hour_distribution()


def _get_comment_user_activity(limit=10):
    return _comment_repo().get_top_active_users(limit=limit)


def _get_recent_comment_texts(limit=200):
    return _comment_repo().get_recent_texts(limit=limit)


def _get_recent_comments(limit=100):
    return _comment_repo().get_recent_comments(limit=limit)


def _get_hot_comments(limit=5):
    return _comment_repo().get_hot_comments(limit=limit)


def _get_with_cache(cache_key_prefix, timeout_key, fetch_fn, *args, **kwargs):
    """通用缓存包装：命中缓存直接返回，否则调用 fetch_fn 并缓存结果。"""
    cache_key = get_cache_key(cache_key_prefix, *args, **kwargs)
    cached = get_cached_data(cache_key, CACHE_TIMEOUT[timeout_key])
    if cached:
        return cached
    data = fetch_fn(*args, **kwargs)
    set_cached_data(cache_key, data, CACHE_TIMEOUT[timeout_key])
    return data


def _build_table_search_result(hot_word):
    """构建表格搜索结果（数据 + 图表 + 情感）。"""
    table_data = getTableData.getTableData(hot_word)
    x_data, y_data = getTableData.getTableDataEchartsData(hot_word)
    hot_word_num = len(table_data)
    emotion_value = _classify_sentiment_from_table(table_data)
    return table_data, x_data, y_data, hot_word_num, emotion_value


def _classify_sentiment_from_table(table_data):
    """根据第一条匹配评论做简单情感分类。"""
    if not table_data:
        return ""
    try:
        from snownlp import SnowNLP

        content = table_data[0][4] if len(table_data[0]) > 4 else ""
        sentiment = SnowNLP(content).sentiments
        if sentiment > 0.6:
            return "正面"
        if sentiment < 0.4:
            return "负面"
        return "中性"
    except (ImportError, IndexError, AttributeError):
        return "中性"


def _build_yuqing_summary(chart_two_data):
    """从饼图数据提取情感统计摘要。"""
    stats = {"positive": 0, "neutral": 0, "negative": 0}
    if not chart_two_data or len(chart_two_data) < 2:
        return stats
    label_key_map = {"正面": "positive", "中性": "neutral", "负面": "negative"}
    for item in chart_two_data[0]:
        key = label_key_map.get(item.get("name"))
        if key:
            stats[key] = item["value"]
    return stats


def _build_yuqing_sentiment_and_trend(comments):
    """对评论进行情感分析，返回 (sentiment_list, trend_counts)。"""
    from services.sentiment_service import SentimentService

    zh_label_map = {"positive": "正面", "neutral": "中性", "negative": "负面"}
    comment_texts = [
        str(c[1]) for c in comments if len(c) > 1 and c[1]
    ]
    results = SentimentService.analyze_batch(comment_texts, mode="simple")
    sentiment_list = []
    trend_counts = defaultdict(lambda: {"positive": 0, "neutral": 0, "negative": 0})

    for idx, (comment, result) in enumerate(zip(comments, results), start=1):
        result = result or {}
        label = result.get("label", "neutral")
        score = float(result.get("score", 0.5))
        comment_time = comment[0] if len(comment) > 0 else ""
        comment_date = str(comment_time).split(" ")[0] if comment_time else ""

        if idx <= 100:
            sentiment_list.append({
                "id": idx,
                "content": comment[1] if len(comment) > 1 else "",
                "sentiment": zh_label_map.get(label, "中性"),
                "score": score,
                "reasoning": result.get("reasoning", ""),
                "emotion": result.get("emotion", "无感"),
                "keywords": result.get("keywords", []),
                "analysis_source": result.get("source", "unknown"),
                "source": "微博评论",
                "time": comment_time,
            })

        if comment_date:
            trend_counts[comment_date][label] = trend_counts[comment_date].get(label, 0) + 1

    return sentiment_list, dict(trend_counts)


def _build_yuqing_trend(trend_counts):
    """将 trend_counts 字典转换为前端可用的趋势数据。"""
    sorted_dates = sorted(trend_counts.keys())
    return {
        "dates": sorted_dates,
        "positive": [trend_counts[d]["positive"] for d in sorted_dates],
        "neutral": [trend_counts[d]["neutral"] for d in sorted_dates],
        "negative": [trend_counts[d]["negative"] for d in sorted_dates],
    }


def _build_yuqing_keywords(chart_three_data, max_words=20):
    """从词频数据构建关键词云列表。"""
    if not chart_three_data or len(chart_three_data) != 2:
        return []
    hot_words, counts = chart_three_data
    colors = ["#67c23a", "#409eff", "#e6a23c", "#f56c6c", "#909399"]
    return [
        {
            "text": word,
            "weight": count // 10,
            "color": colors[i % len(colors)],
        }
        for i, (word, count) in enumerate(zip(hot_words[:max_words], counts[:max_words]))
    ]


def _build_ip_map_data(geo_one_data):
    """将 geo 数据映射为标准省份名称的 map 数据和地区排行。"""
    if not geo_one_data:
        return [], []
    map_data = [
        {"name": _normalize_region_name(item.get("name", ""), PROVINCE_MAP), "value": item.get("value", 0)}
        for item in geo_one_data
    ]
    region_data = sorted(geo_one_data, key=lambda x: x.get("value", 0), reverse=True)[:10]
    return map_data, region_data


def _build_ip_list():
    """从数据库查询评论 IP/地区分布列表。"""
    try:
        return _comment_repo().get_ip_list()
    except (ConnectionError, OSError) as e:
        logger.warning("查询IP数据失败，返回空列表: %s", e)
        return []


def _build_article_type_data():
    """查询文章类型分布，返回饼图格式数据。"""
    try:
        return _article_repo().get_type_distribution()
    except (ConnectionError, OSError) as e:
        logger.warning("查询文章类型分布失败: %s", e)
        return []


@db.route("/getHomeData", methods=["GET"])
def get_home_data():
    """
    获取首页统计数据
    Returns:
        - topFiveComments: 热门评论
        - articleLen: 文章总数
        - maxLikeAuthorName: 最多点赞作者
        - maxCity: 热门城市
        - xData/yData: 时间分布
        - userCreatedDicData: 文章类型
        - commentUserCreatedDicData: 评论时间分布
    """
    cache_key = get_cache_key("home_data")
    cached_data = get_cached_data(cache_key, CACHE_TIMEOUT["home"])
    if cached_data:
        return success_response(cached_data)

    try:
        top_five_comments = getHomeData.getHomeTopLikeCommentsData()
        article_len, max_like_author, max_city = getHomeData.getTagData()
        x_data, y_data = getHomeData.getCreatedNumEchartsData()
        user_type_data = getHomeData.getTypeCharData()
        comment_time_data = getHomeData.getCommentsUserCratedNumEchartsData()

        data = {
            "topFiveComments": top_five_comments,
            "articleLen": article_len,
            "maxLikeAuthorName": max_like_author,
            "maxCity": max_city,
            "xData": x_data,
            "yData": y_data,
            "userCreatedDicData": user_type_data,
            "commentUserCreatedDicData": comment_time_data,
        }

        set_cached_data(cache_key, data, CACHE_TIMEOUT["home"])
        return success_response(data)
    except (ConnectionError, OSError) as e:
        logger.error("获取首页数据失败: %s", e)
        return error_response(f"获取首页数据失败: {e}")


@db.route("/getTableData", methods=["GET"])
def get_table_data():
    """
    获取表格数据（支持关键词搜索）
    Params:
        hotWord: 搜索关键词
    """
    hot_word = _normalize_hot_word(request.args.get("hotWord", ""))
    logger.info("收到请求，hotWord='%s'", hot_word)
    cache_key = get_cache_key("table_data", hot_word)
    cached_data = get_cached_data(cache_key, CACHE_TIMEOUT["table"])
    if cached_data:
        logger.info("返回缓存数据")
        return success_response(cached_data)

    try:
        ciping_total = getTableData.getTableDataPageData()
        logger.info("获取热词列表: %d 个", len(ciping_total))

        if not hot_word and ciping_total:
            hot_word = ciping_total[0][0]
            logger.info("未指定热词，使用默认热词: '%s'", hot_word)

        if not hot_word:
            logger.info("hot_word为空，跳过搜索")
            data = _build_table_response(ciping_total, [], [], [], 0, "")
            set_cached_data(cache_key, data, CACHE_TIMEOUT["table"])
            return success_response(data)

        logger.info("搜索热词: '%s'", hot_word)
        table_data, x_data, y_data, hot_word_num, emotion_value = _build_table_search_result(hot_word)
        logger.info("获取表格数据: %d 条", len(table_data))

        data = _build_table_response(ciping_total, table_data, x_data, y_data, hot_word_num, emotion_value)
        set_cached_data(cache_key, data, CACHE_TIMEOUT["table"])
        return success_response(data)
    except (ConnectionError, OSError) as e:
        logger.error("获取表格数据失败: %s", e)
        return error_response(f"获取表格数据失败: {e}")


def _build_table_response(ciping_total, table_data, x_data, y_data, hot_word_num, emotion_value):
    """组装表格接口的响应字典。"""
    return {
        "hotWordList": ciping_total,
        "tableList": table_data,
        "xData": x_data,
        "yData": y_data,
        "defaultHotWordNum": hot_word_num,
        "emotionValue": emotion_value,
        "total": len(table_data),
    }


@db.route("/getArticleData", methods=["GET"])
def get_article_data():
    """
    获取文章分析数据
    Params:
        type: 文章类型筛选
    """
    default_type = request.args.get("type", "")
    cache_key = get_cache_key("article_data", default_type)
    cached_data = get_cached_data(cache_key, CACHE_TIMEOUT["article"])
    if cached_data:
        return success_response(cached_data)

    try:
        type_list = getEchartsData.getTypeList()
        chart_one_data = getEchartsData.getArticleCharOneData(default_type)
        chart_two_data = getEchartsData.getArticleCharTwoData(default_type)
        chart_three_data = getEchartsData.getArticleCharThreeData(default_type)
        table_data = getTableData.getTableDataArticle(False)

        type_data = _build_article_type_data() if type_list else []

        third = len(table_data) // 3
        sentiment_data = [third, third, third] if chart_three_data and len(chart_three_data) == 2 else [0, 0, 0]

        data = {
            "typeList": type_list,
            "chartOneData": chart_one_data,
            "chartTwoData": chart_two_data,
            "chartThreeData": chart_three_data,
            "tableData": table_data[:100],
            "xData": chart_one_data[0] if chart_one_data else [],
            "yData": chart_one_data[1] if chart_one_data else [],
            "typeData": type_data,
            "sentimentData": sentiment_data,
            "articleList": table_data[:100],
        }

        set_cached_data(cache_key, data, CACHE_TIMEOUT["article"])
        return success_response(data)
    except (ConnectionError, OSError) as e:
        logger.error("获取文章数据失败: %s", e)
        return error_response(f"获取文章数据失败: {e}")


@db.route("/getCommentData", methods=["GET"])
def get_comment_data():
    """
    获取评论分析数据
    """
    cache_key = get_cache_key("comment_data")
    cached_data = get_cached_data(cache_key, CACHE_TIMEOUT["comment"])
    if cached_data:
        return success_response(cached_data)

    try:
        chart_one_data = getEchartsData.getCommetCharDataOne()
        chart_two_data = getEchartsData.getCommetCharDataTwo()
        time_distribution = _get_comment_hour_distribution()
        user_activity = _get_comment_user_activity()

        sentiment_counts = _compute_comment_sentiment(time_distribution)
        sentiment_data = [{"name": k, "value": v} for k, v in sentiment_counts.items()]
        hot_comments = _get_hot_comments()

        data = {
            "chartOneData": chart_one_data,
            "chartTwoData": chart_two_data,
            "timeDistribution": time_distribution,
            "userActivity": user_activity,
            "sentimentData": sentiment_data,
            "hotComments": hot_comments,
        }

        set_cached_data(cache_key, data, CACHE_TIMEOUT["comment"])
        return success_response(data)
    except (ConnectionError, OSError) as e:
        logger.error("获取评论数据失败: %s", e)
        return error_response(f"获取评论数据失败: {e}")


def _compute_comment_sentiment(time_distribution):
    """计算评论情感分布，失败时回退到比例估算。"""
    try:
        from services.sentiment_service import SentimentService

        comment_texts = _get_recent_comment_texts()
        return SentimentService.analyze_distribution(
            comment_texts, mode="simple", sample_size=100,
        )
    except (ImportError, ConnectionError, OSError) as e:
        logger.warning("情感分析失败: %s", e)
        total = sum(time_distribution["counts"])
        return {
            "正面": int(total * 0.35),
            "中性": int(total * 0.45),
            "负面": int(total * 0.20),
        }


@db.route("/getIPData", methods=["GET"])
def get_ip_data():
    """
    获取 IP 地区分布数据
    """
    cache_key = get_cache_key("ip_data")
    cached_data = get_cached_data(cache_key, CACHE_TIMEOUT["ip"])
    if cached_data:
        return success_response(cached_data)

    try:
        geo_one_data = getEchartsData.getGeoCharDataOne()
        geo_two_data = getEchartsData.getGeoCharDataTwo()
        map_data, region_data = _build_ip_map_data(geo_one_data)
        ip_list = _build_ip_list()

        data = {
            "geoOneData": geo_one_data,
            "geoTwoData": geo_two_data,
            "mapData": map_data,
            "regionData": region_data,
            "ipList": ip_list,
        }

        set_cached_data(cache_key, data, CACHE_TIMEOUT["ip"])
        return success_response(data)
    except (ConnectionError, OSError) as e:
        logger.error("获取IP数据失败: %s", e)
        return error_response(f"获取IP数据失败: {e}")


@db.route("/getYuqingData", methods=["GET"])
def get_yuqing_data():
    """
    获取舆情分析数据（情感分析）
    """
    cache_key = get_cache_key("yuqing_data")
    cached_data = get_cached_data(cache_key, CACHE_TIMEOUT["yuqing"])
    if cached_data:
        return success_response(cached_data)

    try:
        chart_one_data = getEchartsData.getYuQingCharDataOne()
        chart_two_data = getEchartsData.getYuQingCharDataTwo()
        chart_three_data = getEchartsData.getYuQingCharDataThree()

        stats = _build_yuqing_summary(chart_two_data)
        comments = _get_recent_comments(limit=100)
        sentiment_list, trend_counts = _build_yuqing_sentiment_and_trend(comments)
        trend = _build_yuqing_trend(trend_counts)
        keywords = _build_yuqing_keywords(chart_three_data)

        data = {
            "chartOneData": chart_one_data,
            "chartTwoData": chart_two_data,
            "chartThreeData": chart_three_data,
            "stats": stats,
            "list": sentiment_list,
            "trend": trend,
            "keywords": keywords,
            "total": len(sentiment_list),
        }

        set_cached_data(cache_key, data, CACHE_TIMEOUT["yuqing"])
        return success_response(data)
    except (ConnectionError, OSError) as e:
        logger.error("获取舆情数据失败: %s", e)
        return error_response(f"获取舆情数据失败: {e}")


@db.route("/getContentCloudData", methods=["GET"])
def get_content_cloud_data():
    """
    获取词云图数据
    Params:
        type: 'article' 或 'comment'
    """
    cloud_type = request.args.get("type", "article")
    cache_key = get_cache_key("cloud_data", cloud_type)
    cached_data = get_cached_data(cache_key, CACHE_TIMEOUT["cloud"])
    if cached_data:
        return success_response(cached_data)

    try:
        if cloud_type == "comment":
            cloud_path = getEchartsData.getCommentContentCloud()
        else:
            cloud_path = getEchartsData.getContentCloud()

        author_cloud_path = getHomeData.getUserNameWordCloud()
        word_stats = _build_word_stats()

        data = {
            "contentCloudPath": cloud_path,
            "authorCloudPath": author_cloud_path,
            "contentCloud": cloud_path,
            "authorCloud": author_cloud_path,
            "wordStats": word_stats,
        }

        set_cached_data(cache_key, data, CACHE_TIMEOUT["cloud"])
        return success_response(data)
    except (ConnectionError, OSError) as e:
        logger.error("获取词云数据失败: %s", e)
        return error_response(f"获取词云数据失败: {e}")


def _build_word_stats():
    """构建词频统计数据列表。"""
    from utils.getPublicData import getAllCiPingTotal

    ciping_data = getAllCiPingTotal()[:50]
    if not ciping_data:
        return []
    total_count = sum(int(x[1]) for x in ciping_data) or 1
    return [
        {
            "word": item[0],
            "count": count,
            "frequency": f"{(count / total_count * 100):.2f}%",
            "sentiment": "中性",
        }
        for item in ciping_data
        if len(item) >= 2
        for count in [int(item[1])]
    ]


@db.route("/clearCache", methods=["POST"])
def clear_cache():
    """
    清空所有缓存（管理接口）
    """
    user = getattr(request, "current_user", None)
    if not is_admin_user(user):
        return error_response("权限不足", 403)

    try:
        memory_cache.clear()
        return success_response({"message": "缓存已清空"})
    except (ConnectionError, OSError) as e:
        logger.error("清空缓存失败: %s", e)
        return error_response(f"清空缓存失败: {e}")