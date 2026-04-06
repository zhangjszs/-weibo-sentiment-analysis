import logging
import os
import threading

import jieba
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image  # 图片处理
from snownlp import SnowNLP
from wordcloud import WordCloud

from config.settings import BASE_DIR
from utils import getPublicData
from utils.query import query_dataframe

logger = logging.getLogger(__name__)


def get_abs_path(rel_path):
    # 静态文件在 src/static 目录下
    src_static = os.path.join(BASE_DIR, "src", "static")
    if os.path.exists(src_static):
        return os.path.join(src_static, os.path.basename(rel_path))
    return os.path.join(BASE_DIR, rel_path)


def getTypeList():
    try:
        df = query_dataframe(
            """
            SELECT DISTINCT type
            FROM article
            WHERE type IS NOT NULL AND type != ''
            ORDER BY type
            """
        )
        if df.empty:
            return []
        return df["type"].dropna().astype(str).tolist()
    except Exception as e:
        logger.warning(f"获取文章类型列表失败，降级到全量读取: {e}")
        return list({x[8] for x in getPublicData.getAllData()})


def _build_bucket_labels(range_num: int, bucket_count: int):
    return [
        f"{range_num * item}-{range_num * (item + 1)}"
        for item in range(1, bucket_count + 1)
    ]


def _get_article_histogram(column: str, default_type, range_num: int, bucket_count: int):
    labels = _build_bucket_labels(range_num, bucket_count)
    counts = [0 for _ in labels]

    case_lines = []
    for idx in range(bucket_count):
        upper_bound = range_num * (idx + 2)
        case_lines.append(
            f"WHEN COALESCE({column}, 0) < {upper_bound} THEN {idx}"
        )

    where_clause = "WHERE type IS NOT NULL AND type != ''"
    params = []
    if default_type:
        where_clause = "WHERE type IS NOT NULL AND type != '' AND type <> %s"
        params.append(default_type)

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

    try:
        df = query_dataframe(sql, params=params)
        if not df.empty:
            for _idx, row in df.iterrows():
                bucket_index = int(row["bucket_index"])
                if 0 <= bucket_index < len(counts):
                    counts[bucket_index] = int(row["count"])
            return labels, counts
    except Exception as e:
        logger.warning(f"文章图表聚合失败，降级到全量读取: {e}")

    articleList = getPublicData.getAllData()
    for article in articleList:
        if article[8] != default_type:
            for item in range(bucket_count):
                if int(article[1 if column == 'likeNum' else 2]) < range_num * (item + 2):
                    counts[item] += 1
                    break
    return labels, counts


def getArticleCharOneData(defaultType):
    return _get_article_histogram("likeNum", defaultType, 1000, 14)


def getArticleCharTwoData(defaultType):
    return _get_article_histogram("commentsLen", defaultType, 1000, 14)


def getArticleCharThreeData(defaultType):
    return _get_article_histogram("commentsLen", defaultType, 50, 29)


def getGeoCharDataOne():
    """
    获取评论地理分布数据

    Returns:
        list: 城市分布列表
    """
    try:
        df = query_dataframe(
            """
            SELECT region AS name, COUNT(*) AS value
            FROM comments
            WHERE region IS NOT NULL AND region != '' AND region != '无'
            GROUP BY region
            ORDER BY value DESC
            """
        )
        if df.empty:
            return []

        cityDicList = [
            {"name": str(row["name"]), "value": int(row["value"])}
            for _idx, row in df.iterrows()
        ]

        logger.info(f"获取评论地理分布数据成功，共 {len(cityDicList)} 个省份")
        return cityDicList

    except Exception as e:
        logger.error(f"获取评论地理分布数据失败: {e}")
        return []


def getGeoCharDataTwo():
    """
    获取文章地理分布数据

    Returns:
        list: 城市分布列表
    """
    try:
        df = query_dataframe(
            """
            SELECT region AS name, COUNT(*) AS value
            FROM article
            WHERE region IS NOT NULL AND region != '' AND region != '无'
            GROUP BY region
            ORDER BY value DESC
            """
        )
        if df.empty:
            return []

        cityDicList = [
            {"name": str(row["name"]), "value": int(row["value"])}
            for _idx, row in df.iterrows()
        ]

        logger.info(f"获取文章地理分布数据成功，共 {len(cityDicList)} 个省份")
        return cityDicList

    except Exception as e:
        logger.error(f"获取文章地理分布数据失败: {e}")
        return []


def getCommetCharDataOne():
    range_num = 20
    bucket_count = 99
    x_data = _build_bucket_labels(range_num, bucket_count)
    y_data = [0 for _ in x_data]

    case_lines = []
    for idx in range(bucket_count):
        upper_bound = range_num * (idx + 2)
        case_lines.append(
            f"WHEN COALESCE(like_counts, 0) < {upper_bound} THEN {idx}"
        )

    try:
        df = query_dataframe(
            f"""
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
        )
        if not df.empty:
            for _idx, row in df.iterrows():
                bucket_index = int(row["bucket_index"])
                if 0 <= bucket_index < len(y_data):
                    y_data[bucket_index] = int(row["count"])
            return x_data, y_data
    except Exception as e:
        logger.warning(f"评论点赞分布聚合失败，降级到全量读取: {e}")

    comment_list = getPublicData.getAllCommentsData()
    for comment in comment_list:
        for item in range(bucket_count):
            if int(comment[2]) < range_num * (item + 2):
                y_data[item] += 1
                break
    return x_data, y_data


def getCommetCharDataTwo():
    try:
        df = query_dataframe(
            """
            SELECT authorGender AS name, COUNT(*) AS value
            FROM comments
            WHERE authorGender IS NOT NULL AND authorGender != ''
            GROUP BY authorGender
            ORDER BY value DESC
            """
        )
        if not df.empty:
            return [
                {"name": str(row["name"]), "value": int(row["value"])}
                for _idx, row in df.iterrows()
            ]
    except Exception as e:
        logger.warning(f"评论性别分布聚合失败，降级到全量读取: {e}")

    comment_list = getPublicData.getAllCommentsData()
    gender_dic = {}
    for item in comment_list:
        if gender_dic.get(item[6], -1) == -1:
            gender_dic[item[6]] = 1
        else:
            gender_dic[item[6]] += 1
    return [{"name": key, "value": value} for key, value in gender_dic.items()]


def stopwordslist():
    path = get_abs_path("model/stopWords.txt")
    try:
        stopwords = [line.strip() for line in open(path, encoding="UTF-8").readlines()]
    except Exception as e:
        print(f"Errors reading stopwords from {path}: {e}")
        return []
    return stopwords


_plt_lock = threading.Lock()


def _build_cloud_text(table_name: str, limit: int = 1000):
    texts = _load_recent_texts(table_name, limit=limit)
    if not texts:
        return ""
    return " ".join(texts)


def getContentCloud():
    text = _build_cloud_text("article", limit=1000)
    stopwords = stopwordslist()
    cut = jieba.cut(text)
    newCut = []
    for word in cut:
        if word not in stopwords:
            newCut.append(word)
    string = " ".join(newCut)
    img_path = get_abs_path("static/content.jpg")
    img = Image.open(img_path)  # 打开遮罩图片
    img_arr = np.array(img)  # 将图片转化为列表
    wc = WordCloud(
        width=1000,
        height=600,
        background_color="white",
        colormap="Blues",
        font_path="STHUPO.TTF",
        mask=img_arr,
    )
    wc.generate_from_text(string)

    save_path = get_abs_path("static/contentCloud.jpg")

    # 加锁防止多线程绘图冲突
    with _plt_lock:
        try:
            # 绘制图片
            plt.figure(1)
            plt.imshow(wc)
            plt.axis("off")  # 不显示坐标轴
            plt.savefig(save_path, dpi=500)
        finally:
            plt.close()

    return "/static/contentCloud.jpg"


def getCommentContentCloud():
    text = _build_cloud_text("comments", limit=1000)
    stopwords = stopwordslist()
    cut = jieba.cut(text)
    newCut = []
    for word in cut:
        if word not in stopwords:
            newCut.append(word)
    string = " ".join(newCut)
    img_path = get_abs_path("static/comment.jpg")
    img = Image.open(img_path)  # 打开遮罩图片
    img_arr = np.array(img)  # 将图片转化为列表
    wc = WordCloud(
        width=1000,
        height=600,
        background_color="white",
        colormap="Blues",
        font_path="STHUPO.TTF",
        mask=img_arr,
    )
    wc.generate_from_text(string)

    save_path = get_abs_path("static/commentCloud.jpg")

    # 加锁防止多线程绘图冲突
    with _plt_lock:
        try:
            # 绘制图片
            plt.figure(1)
            plt.imshow(wc)
            plt.axis("off")  # 不显示坐标轴
            plt.savefig(save_path, dpi=500)
        finally:
            plt.close()

    return "/static/commentCloud.jpg"


def getYuQingCharDataOne():
    hotWordList = getPublicData.getAllCiPingTotal()
    xData = ["正面", "中性", "负面"]
    yData = [0, 0, 0]
    for hotWord in hotWordList:
        emotionValue = SnowNLP(hotWord[0]).sentiments
        if emotionValue > 0.5:
            yData[0] += 1
        elif emotionValue == 0.5:
            yData[1] += 1
        elif emotionValue < 0.5:
            yData[2] += 1
    bieData = [
        {"name": "正面", "value": yData[0]},
        {"name": "中性", "value": yData[1]},
        {"name": "负面", "value": yData[2]},
    ]
    return xData, yData, bieData


def _load_recent_texts(table_name: str, limit: int = 200):
    try:
        df = query_dataframe(
            f"""
            SELECT content
            FROM {table_name}
            WHERE content IS NOT NULL AND content != ''
            ORDER BY created_at DESC
            LIMIT %s
            """,
            params=[max(1, min(limit, 1000))],
        )
        if df.empty:
            return []
        return df["content"].dropna().astype(str).tolist()
    except Exception as e:
        logger.warning(f"加载 {table_name} 文本失败: {e}")
        return []


def getYuQingCharDataTwo():
    from services.sentiment_service import SentimentService

    def to_pie_data(counts):
        return [
            {"name": "正面", "value": int(counts.get("正面", 0))},
            {"name": "中性", "value": int(counts.get("中性", 0))},
            {"name": "负面", "value": int(counts.get("负面", 0))},
        ]

    comment_texts = _load_recent_texts("comments", limit=200)
    article_texts = _load_recent_texts("article", limit=200)

    comment_counts = SentimentService.analyze_distribution(
        comment_texts, mode="simple", sample_size=200
    )
    article_counts = SentimentService.analyze_distribution(
        article_texts, mode="simple", sample_size=200
    )

    return to_pie_data(comment_counts), to_pie_data(article_counts)


def getYuQingCharDataThree():
    hotWordList = getPublicData.getAllCiPingTotal()
    return [x[0] for x in hotWordList], [int(x[1]) for x in hotWordList]
