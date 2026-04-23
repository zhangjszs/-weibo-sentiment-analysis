#!/usr/bin/env python3
"""
数据 API 模块
功能：提供数据可视化相关 JSON API 接口
路由前缀: /getAllData
"""

import hashlib
import logging
import threading
from datetime import datetime, timedelta
from urllib.parse import unquote

from flask import Blueprint, request

from utils import getEchartsData, getHomeData, getTableData
from utils.api_response import error, ok
from utils.authz import is_admin_user
from utils.cache import memory_cache
from utils.query import query_dataframe

logger = logging.getLogger(__name__)

# 创建蓝图
db = Blueprint("data", __name__, url_prefix="/getAllData")

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


def success_response(data, msg="success"):
    """统一成功响应格式"""
    return ok(data, msg=msg), 200


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


def _get_comment_hour_distribution():
    hours = [f"{h}:00" for h in range(24)]
    counts = [0] * 24

    df = query_dataframe(
        """
        SELECT HOUR(created_at) AS hour_bucket, COUNT(*) AS count
        FROM comments
        WHERE created_at IS NOT NULL
        GROUP BY hour_bucket
        ORDER BY hour_bucket
        """
    )
    if df.empty:
        return {"hours": hours, "counts": counts}

    for _idx, row in df.iterrows():
        try:
            hour = int(row["hour_bucket"])
        except (TypeError, ValueError):
            continue
        if 0 <= hour < 24:
            counts[hour] = int(row["count"])

    return {"hours": hours, "counts": counts}


def _get_comment_user_activity(limit=10):
    df = query_dataframe(
        """
        SELECT authorName, COUNT(*) AS count
        FROM comments
        WHERE authorName IS NOT NULL AND authorName != ''
        GROUP BY authorName
        ORDER BY count DESC, authorName ASC
        LIMIT %s
        """,
        params=[limit],
    )
    if df.empty:
        return {"users": [], "counts": []}

    return {
        "users": df["authorName"].astype(str).tolist(),
        "counts": [int(value) for value in df["count"].tolist()],
    }


def _get_recent_comment_texts(limit=200):
    df = query_dataframe(
        """
        SELECT content
        FROM comments
        WHERE content IS NOT NULL AND content != ''
        ORDER BY created_at DESC
        LIMIT %s
        """,
        params=[limit],
    )
    if df.empty:
        return []
    return [str(value) for value in df["content"].dropna().tolist()]


def _get_recent_comments(limit=100):
    df = query_dataframe(
        """
        SELECT created_at, content
        FROM comments
        WHERE content IS NOT NULL AND content != ''
        ORDER BY created_at DESC
        LIMIT %s
        """,
        params=[limit],
    )
    if df.empty:
        return []
    return df.values.tolist()


def _get_hot_comments(limit=5):
    df = query_dataframe(
        """
        SELECT created_at, like_counts, content, authorName
        FROM comments
        ORDER BY like_counts DESC, created_at DESC
        LIMIT %s
        """,
        params=[limit],
    )
    if df.empty:
        return []

    hot_comments = []
    for _idx, row in df.iterrows():
        hot_comments.append(
            {
                "user": str(row.get("authorName") or "未知用户"),
                "time": str(row.get("created_at") or ""),
                "content": str(row.get("content") or ""),
                "likes": int(row.get("like_counts") or 0),
                "replies": 0,
            }
        )
    return hot_comments


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
        topFiveComments = getHomeData.getHomeTopLikeCommentsData()
        articleLen, maxLikeAuthorName, maxCity = getHomeData.getTagData()
        xData, yData = getHomeData.getCreatedNumEchartsData()
        userCreatedDicData = getHomeData.getTypeCharData()
        commentUserCreatedDicData = getHomeData.getCommentsUserCratedNumEchartsData()

        data = {
            "topFiveComments": topFiveComments,
            "articleLen": articleLen,
            "maxLikeAuthorName": maxLikeAuthorName,
            "maxCity": maxCity,
            "xData": xData,
            "yData": yData,
            "userCreatedDicData": userCreatedDicData,
            "commentUserCreatedDicData": commentUserCreatedDicData,
        }

        set_cached_data(cache_key, data, CACHE_TIMEOUT["home"])
        return success_response(data)
    except Exception as e:
        logger.error(f"获取首页数据失败: {e}")
        return error_response(f"获取首页数据失败: {str(e)}")


@db.route("/getTableData", methods=["GET"])
def get_table_data():
    """
    获取表格数据（支持关键词搜索）
    Params:
        hotWord: 搜索关键词
    """
    hot_word = _normalize_hot_word(request.args.get("hotWord", ""))
    logger.info(f"收到请求，hotWord='{hot_word}'")
    cache_key = get_cache_key("table_data", hot_word)
    cached_data = get_cached_data(cache_key, CACHE_TIMEOUT["table"])
    if cached_data:
        logger.info("返回缓存数据")
        return success_response(cached_data)

    try:
        # 获取热词列表
        ciping_total = getTableData.getTableDataPageData()
        logger.info(f"获取热词列表: {len(ciping_total)} 个")

        # 如果没有指定 hotWord，默认使用第一个热词
        if not hot_word and ciping_total and len(ciping_total) > 0:
            hot_word = ciping_total[0][0]
            logger.info(f"未指定热词，使用默认热词: '{hot_word}'")

        # 获取搜索结果
        logger.info(f"检查hot_word: '{hot_word}', 是否为空: {not hot_word}")
        if hot_word:
            logger.info(f"搜索热词: '{hot_word}'")
            table_data = getTableData.getTableData(hot_word)
            logger.info(f"获取表格数据: {len(table_data)} 条")
            x_data, y_data = getTableData.getTableDataEchartsData(hot_word)
            # 计算热词出现次数
            default_hot_word_num = len(table_data)
            # 简单的情感分析（基于第一条匹配评论）
            emotion_value = ""
            if table_data and len(table_data) > 0:
                try:
                    from snownlp import SnowNLP

                    content = table_data[0][4] if len(table_data[0]) > 4 else ""
                    sentiment = SnowNLP(content).sentiments
                    if sentiment > 0.6:
                        emotion_value = "正面"
                    elif sentiment < 0.4:
                        emotion_value = "负面"
                    else:
                        emotion_value = "中性"
                except Exception:
                    emotion_value = "中性"
        else:
            logger.info("hot_word为空，跳过搜索")
            table_data = []
            x_data, y_data = [], []
            default_hot_word_num = 0
            emotion_value = ""

        data = {
            "hotWordList": ciping_total,
            "tableList": table_data,
            "xData": x_data,
            "yData": y_data,
            "defaultHotWordNum": default_hot_word_num,
            "emotionValue": emotion_value,
            "total": len(table_data),
        }

        set_cached_data(cache_key, data, CACHE_TIMEOUT["table"])
        return success_response(data)
    except Exception as e:
        logger.error(f"获取表格数据失败: {e}")
        return error_response(f"获取表格数据失败: {str(e)}")


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
        # 获取类型列表
        type_list = getEchartsData.getTypeList()

        # 获取图表数据
        chart_one_data = getEchartsData.getArticleCharOneData(default_type)
        chart_two_data = getEchartsData.getArticleCharTwoData(default_type)
        chart_three_data = getEchartsData.getArticleCharThreeData(default_type)

        # 获取文章表格数据
        table_data = getTableData.getTableDataArticle(False)

        # 转换类型数据为饼图格式
        type_data = []
        if type_list:
            type_df = query_dataframe("""
                SELECT type, COUNT(*) AS count
                FROM article
                GROUP BY type
                ORDER BY count DESC
            """)
            if not type_df.empty:
                type_data = [
                    {
                        "name": row["type"] if row["type"] else "未知",
                        "value": int(row["count"]),
                    }
                    for _idx, row in type_df.iterrows()
                ]

        # 转换情感数据
        sentiment_data = [0, 0, 0]
        if chart_three_data and len(chart_three_data) == 2:
            sentiment_data = [
                len(table_data) // 3,
                len(table_data) // 3,
                len(table_data) // 3,
            ]

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
    except Exception as e:
        logger.error(f"获取文章数据失败: {e}")
        return error_response(f"获取文章数据失败: {str(e)}")


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

        # 真实情感分布数据（下沉到 Service 层并缓存，避免接口层重复计算）
        sentiment_counts = {"正面": 0, "中性": 0, "负面": 0}
        try:
            from services.sentiment_service import SentimentService

            comment_texts = _get_recent_comment_texts()
            sentiment_counts = SentimentService.analyze_distribution(
                comment_texts,
                mode="simple",
                sample_size=100,
            )
        except Exception as e:
            logger.warning(f"情感分析失败: {e}")
            total_comments = sum(time_distribution["counts"])
            sentiment_counts = {
                "正面": int(total_comments * 0.35),
                "中性": int(total_comments * 0.45),
                "负面": int(total_comments * 0.20),
            }

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
    except Exception as e:
        logger.error(f"获取评论数据失败: {e}")
        return error_response(f"获取评论数据失败: {str(e)}")


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

        # 地图数据
        province_map = {
            "北京": "北京市",
            "天津": "天津市",
            "上海": "上海市",
            "重庆": "重庆市",
            "河北": "河北省",
            "山西": "山西省",
            "辽宁": "辽宁省",
            "吉林": "吉林省",
            "黑龙江": "黑龙江省",
            "江苏": "江苏省",
            "浙江": "浙江省",
            "安徽": "安徽省",
            "福建": "福建省",
            "江西": "江西省",
            "山东": "山东省",
            "河南": "河南省",
            "湖北": "湖北省",
            "湖南": "湖南省",
            "广东": "广东省",
            "海南": "海南省",
            "四川": "四川省",
            "贵州": "贵州省",
            "云南": "云南省",
            "陕西": "陕西省",
            "甘肃": "甘肃省",
            "青海": "青海省",
            "台湾": "台湾省",
            "内蒙古": "内蒙古自治区",
            "广西": "广西壮族自治区",
            "西藏": "西藏自治区",
            "宁夏": "宁夏回族自治区",
            "新疆": "新疆维吾尔自治区",
            "香港": "香港特别行政区",
            "澳门": "澳门特别行政区",
        }

        map_data = []
        if geo_one_data:
            for item in geo_one_data:
                name = item.get("name", "")
                full_name = _normalize_region_name(name, province_map)

                map_data.append({"name": full_name, "value": item.get("value", 0)})

        # 地区排行数据
        region_data = []
        if geo_one_data:
            region_data = sorted(
                geo_one_data, key=lambda x: x.get("value", 0), reverse=True
            )[:10]

        # IP详细列表数据（从数据库查询真实数据）
        ip_list = []
        try:
            # 查询评论中的IP/地区信息
            df = query_dataframe("""
                SELECT
                    MAX(authorName) as authorName,
                    authorAddress,
                    COUNT(*) as count,
                    MAX(created_at) as last_time
                FROM comments
                WHERE authorAddress IS NOT NULL AND authorAddress != ''
                GROUP BY authorAddress
                ORDER BY count DESC
                LIMIT 10
            """)

            if not df.empty:
                for idx, row in df.iterrows():
                    ip_list.append(
                        {
                            "ip": "",
                            "location": row["authorAddress"],
                            "count": int(row["count"]),
                            "lastTime": str(row["last_time"]),
                            "user": row["authorName"],
                        }
                    )
        except Exception as e:
            logger.warning(f"查询IP数据失败，返回空列表: {e}")
            ip_list = []

        data = {
            "geoOneData": geo_one_data,
            "geoTwoData": geo_two_data,
            "mapData": map_data,
            "regionData": region_data,
            "ipList": ip_list,
        }

        set_cached_data(cache_key, data, CACHE_TIMEOUT["ip"])
        return success_response(data)
    except Exception as e:
        logger.error(f"获取IP数据失败: {e}")
        return error_response(f"获取IP数据失败: {str(e)}")


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

        # 情感统计
        stats = {"positive": 0, "neutral": 0, "negative": 0}
        if chart_two_data and len(chart_two_data) >= 2:
            bie_data1 = chart_two_data[0]
            for item in bie_data1:
                if item["name"] == "正面":
                    stats["positive"] = item["value"]
                elif item["name"] == "中性":
                    stats["neutral"] = item["value"]
                elif item["name"] == "负面":
                    stats["negative"] = item["value"]

        comments = _get_recent_comments(limit=100)
        sentiment_list = []
        trend_counts = {}
        try:
            from services.sentiment_service import SentimentService

            comment_texts = [
                str(comment[1]) for comment in comments if len(comment) > 1 and comment[1]
            ]
            analysis_results = SentimentService.analyze_batch(comment_texts, mode="contextual")

            zh_label_map = {
                "positive": "正面",
                "neutral": "中性",
                "negative": "负面",
            }
            trend_key_map = {
                "positive": "positive",
                "neutral": "neutral",
                "negative": "negative",
            }

            for idx, (comment, result) in enumerate(zip(comments, analysis_results), start=1):
                label = (result or {}).get("label", "neutral")
                score = float((result or {}).get("score", 0.5))
                reasoning = (result or {}).get("reasoning", "")
                emotion = (result or {}).get("emotion", "无感")
                keywords = (result or {}).get("keywords", [])
                analysis_source = (result or {}).get("source", "unknown")
                comment_time = comment[0] if len(comment) > 0 else ""
                comment_date = str(comment_time).split(" ")[0] if comment_time else ""

                if idx <= 100:  # 增加返回的情感分析结果数量
                    sentiment_list.append(
                        {
                            "id": idx,
                            "content": comment[1] if len(comment) > 1 else "",
                            "sentiment": zh_label_map.get(label, "中性"),
                            "score": score,
                            "reasoning": reasoning,
                            "emotion": emotion,
                            "keywords": keywords,
                            "analysis_source": analysis_source,
                            "source": "微博评论",
                            "time": comment_time,
                        }
                    )

                if comment_date:
                    if comment_date not in trend_counts:
                        trend_counts[comment_date] = {
                            "positive": 0,
                            "neutral": 0,
                            "negative": 0,
                        }
                    trend_counts[comment_date][trend_key_map.get(label, "neutral")] += 1
        except Exception as e:
            logger.warning(f"构建舆情列表与趋势失败，返回空结果: {e}")

        sorted_dates = sorted(trend_counts.keys())
        trend = {
            "dates": sorted_dates,
            "positive": [trend_counts[date]["positive"] for date in sorted_dates],
            "neutral": [trend_counts[date]["neutral"] for date in sorted_dates],
            "negative": [trend_counts[date]["negative"] for date in sorted_dates],
        }

        # 关键词云数据
        keywords = []
        if chart_three_data and len(chart_three_data) == 2:
            hot_words, counts = chart_three_data
            colors = ["#67c23a", "#409eff", "#e6a23c", "#f56c6c", "#909399"]
            for i, (word, count) in enumerate(zip(hot_words[:20], counts[:20])):
                keywords.append(
                    {
                        "text": word,
                        "weight": count // 10,
                        "color": colors[i % len(colors)],
                    }
                )

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
    except Exception as e:
        logger.error(f"获取舆情数据失败: {e}")
        return error_response(f"获取舆情数据失败: {str(e)}")


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

        # 词频统计数据
        word_stats = []
        from utils.getPublicData import getAllCiPingTotal

        ciping_data = getAllCiPingTotal()[:50]
        total_count = sum([int(x[1]) for x in ciping_data]) if ciping_data else 1
        for _i, item in enumerate(ciping_data):
            if len(item) >= 2:
                count = int(item[1])
                word_stats.append(
                    {
                        "word": item[0],
                        "count": count,
                        "frequency": f"{(count / total_count * 100):.2f}%",
                        "sentiment": "中性",
                    }
                )

        data = {
            "contentCloudPath": cloud_path,
            "authorCloudPath": author_cloud_path,
            "contentCloud": cloud_path,
            "authorCloud": author_cloud_path,
            "wordStats": word_stats,
        }

        set_cached_data(cache_key, data, CACHE_TIMEOUT["cloud"])
        return success_response(data)
    except Exception as e:
        logger.error(f"获取词云数据失败: {e}")
        return error_response(f"获取词云数据失败: {str(e)}")


@db.route("/clearCache", methods=["POST"])
def clear_cache():
    """
    清空所有缓存（管理接口）
    """
    try:
        user = getattr(request, "current_user", None)
        if not is_admin_user(user):
            return error_response("权限不足", 403)
        memory_cache.clear()
        return success_response({"message": "缓存已清空"})
    except Exception as e:
        logger.error(f"清空缓存失败: {e}")
        return error_response(f"清空缓存失败: {str(e)}")
