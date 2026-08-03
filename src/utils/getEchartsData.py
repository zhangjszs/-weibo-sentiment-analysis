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
from utils.getPublicData import getAllCiPingTotal
from repositories.article_repository import ArticleRepository
from repositories.comment_repository import CommentRepository

logger = logging.getLogger(__name__)


def get_abs_path(rel_path):
    # 静态文件在 src/static 目录下
    src_static = os.path.join(BASE_DIR, "src", "static")
    if os.path.exists(src_static):
        return os.path.join(src_static, os.path.basename(rel_path))
    return os.path.join(BASE_DIR, rel_path)


def _article_repo() -> ArticleRepository:
    return ArticleRepository()


def _comment_repo() -> CommentRepository:
    return CommentRepository()


def getTypeList():
    try:
        return _article_repo().get_distinct_types()
    except Exception as e:
        logger.warning(f"获取文章类型列表失败，降级到全量读取: {e}")
        return list({x[8] for x in getAllData()})


def _build_bucket_labels(range_num: int, bucket_count: int):
    return [
        f"{range_num * item}-{range_num * (item + 1)}"
        for item in range(1, bucket_count + 1)
    ]


def getArticleCharOneData(defaultType):
    return _article_repo().get_histogram("likeNum", exclude_type=defaultType, range_num=1000, bucket_count=14)


def getArticleCharTwoData(defaultType):
    return _article_repo().get_histogram("commentsLen", exclude_type=defaultType, range_num=1000, bucket_count=14)


def getArticleCharThreeData(defaultType):
    return _article_repo().get_histogram("commentsLen", exclude_type=defaultType, range_num=50, bucket_count=29)


def getGeoCharDataOne():
    """
    获取评论地理分布数据

    Returns:
        list: 城市分布列表
    """
    try:
        return _comment_repo().get_region_distribution()
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
        return _article_repo().get_region_distribution()
    except Exception as e:
        logger.error(f"获取文章地理分布数据失败: {e}")
        return []


def getCommetCharDataOne():
    try:
        return _comment_repo().get_like_histogram(range_num=20, bucket_count=99)
    except Exception as e:
        logger.warning(f"评论点赞分布聚合失败，降级到全量读取: {e}")
        comment_list = getAllCommentsData()
        range_num = 20
        bucket_count = 99
        x_data = _build_bucket_labels(range_num, bucket_count)
        y_data = [0 for _ in x_data]
        for comment in comment_list:
            for item in range(bucket_count):
                if int(comment[2]) < range_num * (item + 2):
                    y_data[item] += 1
                    break
        return x_data, y_data


def getCommetCharDataTwo():
    try:
        return _comment_repo().get_gender_distribution()
    except Exception as e:
        logger.warning(f"评论性别分布聚合失败，降级到全量读取: {e}")
        comment_list = getAllCommentsData()
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
    if table_name == "article":
        texts = _article_repo().get_recent_texts(limit=limit)
    elif table_name == "comments":
        texts = _comment_repo().get_recent_texts(limit=limit)
    else:
        texts = []
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
    hotWordList = getAllCiPingTotal()
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


def getYuQingCharDataTwo():
    from services.sentiment_service import SentimentService

    def to_pie_data(counts):
        return [
            {"name": "正面", "value": int(counts.get("正面", 0))},
            {"name": "中性", "value": int(counts.get("中性", 0))},
            {"name": "负面", "value": int(counts.get("负面", 0))},
        ]

    comment_texts = _comment_repo().get_recent_texts(limit=200)
    article_texts = _article_repo().get_recent_texts(limit=200)

    comment_counts = SentimentService.analyze_distribution(
        comment_texts, mode="simple", sample_size=200
    )
    article_counts = SentimentService.analyze_distribution(
        article_texts, mode="simple", sample_size=200
    )

    return to_pie_data(comment_counts), to_pie_data(article_counts)


def getYuQingCharDataThree():
    hotWordList = getAllCiPingTotal()
    return [x[0] for x in hotWordList], [int(x[1]) for x in hotWordList]


def getAllData():
    """兼容旧接口：返回所有文章数据"""
    from utils.getPublicData import getAllData as _getAllData
    return _getAllData()


def getAllCommentsData():
    """兼容旧接口：返回所有评论数据"""
    from utils.getPublicData import getAllCommentsData as _getAllCommentsData
    return _getAllCommentsData()