import logging
from datetime import datetime

from snownlp import SnowNLP

from utils.getPublicData import getAllCiPingTotal, getAllCommentsData, getAllData
from repositories.comment_repository import CommentRepository
from repositories.article_repository import ArticleRepository

logger = logging.getLogger(__name__)


def _extract_date_part(value):
    """从时间字符串中提取 YYYY-MM-DD 日期部分，失败返回 None。"""
    if value is None:
        return None

    date_part = str(value).strip().split(" ")[0]
    try:
        datetime.strptime(date_part, "%Y-%m-%d")
        return date_part
    except ValueError:
        logger.debug(f"跳过无效日期格式: {value}")
        return None


def _comment_repo() -> CommentRepository:
    return CommentRepository()


def _article_repo() -> ArticleRepository:
    return ArticleRepository()


def getTableDataPageData():
    return getAllCiPingTotal()


def getTableData(hotWord):
    """
    根据关键词获取评论数据（优化版：使用数据库查询代替Python过滤）

    Args:
        hotWord: 搜索关键词

    Returns:
        list: 匹配的评论列表
    """
    try:
        # 使用 Repository 搜索
        results = _comment_repo().search_by_content(hotWord, limit=1000)

        if not results:
            logger.info(f"未找到包含关键词 '{hotWord}' 的评论")
            return []

        logger.info(f"找到 {len(results)} 条包含关键词 '{hotWord}' 的评论")
        return [
            [
                r["articleId"], r["created_at"], r["like_counts"], r["region"],
                r["content"], r["authorName"], r["authorGender"],
                r["authorAddress"], r["authorAvatar"]
            ]
            for r in results
        ]

    except Exception as e:
        logger.error(f"查询评论数据失败: {e}")
        # 降级到原始方法
        logger.warning("降级到原始查询方法")
        commentList = getAllCommentsData()
        tableData = []
        for comment in commentList:
            if comment[4].find(hotWord) != -1:
                tableData.append(comment)
        return tableData


def getTableDataEchartsData(hotWord):
    tableList = getTableData(hotWord)
    # 先统计每日条数，避免后续频繁 index 查找导致 O(n^2)
    date_count = {}
    for comment in tableList:
        if not (
            isinstance(comment, (list, tuple))
            and len(comment) > 1
        ):
            continue
        date_part = _extract_date_part(comment[1])
        if not date_part:
            continue
        date_count[date_part] = date_count.get(date_part, 0) + 1

    if not date_count:
        return [], []

    try:
        xData = sorted(
            date_count.keys(),
            key=lambda x: datetime.strptime(x, "%Y-%m-%d").timestamp(),
            reverse=True,
        )
    except ValueError as e:
        logger.warning(f"日期排序失败: {e}")
        return [], []

    yData = [date_count.get(day, 0) for day in xData]
    return xData, yData


def getTableDataArticle(flag):
    try:
        articles, _ = _article_repo().find_with_filter(limit=1000, offset=0)
        table_list = [
            [
                a["id"], a["likeNum"], a["commentsLen"], a["reposts_count"],
                a["region"], a["content"], a["contentLen"], a["created_at"],
                a["type"], a["detailUrl"], a["authorName"], a["authorDetail"],
                a["isVip"], 0  # vipLevel 字段不存在，用 0 占位
            ]
            for a in articles
        ]
    except Exception as e:
        logger.error(f"查询文章表格数据失败: {e}")
        table_list = getAllData()

    if not flag:
        return table_list

    try:
        from services.sentiment_service import SentimentService

        texts = [
            str(item[5]).strip()
            for item in table_list
            if len(item) > 5 and str(item[5]).strip()
        ]
        analysis_results = SentimentService.analyze_batch(texts, mode="simple")
        sentiment_iter = iter(analysis_results)

        result_rows = []
        for item in table_list:
            row = list(item)
            if len(row) > 5 and str(row[5]).strip():
                result = next(sentiment_iter, {"label": "neutral"})
                label = result.get("label", "neutral")
                if label == "positive":
                    sentiment_value = "正面"
                elif label == "negative":
                    sentiment_value = "负面"
                else:
                    sentiment_value = "中性"
            else:
                sentiment_value = "中性"
            row.append(sentiment_value)
            result_rows.append(row)
        return result_rows
    except Exception as e:
        logger.warning(f"批量情感分析失败，降级到逐条分析: {e}")
        result_rows = []
        for item in table_list:
            row = list(item)
            emotion_value = SnowNLP(row[5]).sentiments if len(row) > 5 and row[5] else 0.5
            if emotion_value > 0.5:
                row.append("正面")
            elif emotion_value < 0.5:
                row.append("负面")
            else:
                row.append("中性")
            result_rows.append(row)
        return result_rows