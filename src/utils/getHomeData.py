import os
import time

import jieba
import matplotlib.pyplot as plt
from wordcloud import WordCloud

from config.settings import BASE_DIR
from utils.cache import cache_result
from repositories.article_repository import ArticleRepository
from repositories.comment_repository import CommentRepository


def get_abs_path(rel_path):
    return os.path.join(BASE_DIR, rel_path)


def _article_repo() -> ArticleRepository:
    return ArticleRepository()


def _comment_repo() -> CommentRepository:
    return CommentRepository()


@cache_result(timeout=300)  # 缓存5分钟
def getHomeTopLikeCommentsData():
    """获取点赞最多的评论 - 优化版"""
    try:
        comments = _comment_repo().get_top_liked_comments(limit=4)
        return [
            [
                c["articleId"], c["created_at"], c["like_counts"], c["region"],
                c["content"], c["authorName"], c["authorGender"],
                c["authorAddress"], c["authorAvatar"]
            ]
            for c in comments
        ]
    except Exception as e:
        print(f"获取热门评论失败: {e}")
        return []


@cache_result(timeout=600)  # 缓存10分钟
def getTagData():
    """获取标签数据 - 优化版"""
    try:
        article_count = _article_repo().count_total()
        max_like_author = _article_repo().get_top_liked_author() or ""
        max_city_rows = _article_repo().count_by_region(limit=1)
        max_city = max_city_rows[0]["region"] if max_city_rows else ""
        return article_count, max_like_author, max_city
    except Exception as e:
        print(f"获取标签数据失败: {e}")
        return 0, "", ""


@cache_result(timeout=600)  # 缓存10分钟
def getCreatedNumEchartsData():
    """获取创建数量图表数据 - 优化版"""
    try:
        rows = _article_repo().count_by_date_range()
        if not rows:
            return [], []
        xData = [r["created_at"] for r in rows]
        yData = [r["count"] for r in rows]
        return xData, yData
    except Exception as e:
        print(f"获取时间数据失败: {e}")
        return [], []


@cache_result(timeout=600)  # 缓存10分钟
def getTypeCharData():
    """获取类型图表数据 - 优化版"""
    try:
        rows = _article_repo().count_by_type()
        if not rows:
            return []
        resultData = [
            {"name": r["type"], "value": r["count"]}
            for r in rows
        ]
        return resultData
    except Exception as e:
        print(f"获取类型数据失败: {e}")
        return []


@cache_result(timeout=300)  # 缓存5分钟
def getCommentsUserCratedNumEchartsData():
    """获取评论用户创建数量图表数据 - 优化版"""
    try:
        rows = _comment_repo().count_by_date_range()
        if not rows:
            return []
        resultData = [
            {"name": r["created_at"], "value": r["count"]}
            for r in rows
        ]
        return resultData
    except Exception as e:
        print(f"获取评论时间数据失败: {e}")
        return []


def stopwordslist():
    """获取停用词列表"""
    try:
        stopwords_path = get_abs_path("model/stopWords.txt")
        if os.path.exists(stopwords_path):
            stopwords = [
                line.strip()
                for line in open(stopwords_path, encoding="UTF-8").readlines()
            ]
            return stopwords
        else:
            print(f"停用词文件不存在: {stopwords_path}")
            return []
    except Exception as e:
        print(f"读取停用词文件失败: {e}")
        return []


@cache_result(timeout=1800, use_file_cache=True)  # 缓存30分钟，词云生成较耗时
def getUserNameWordCloud():
    """生成用户名词云 - 优化版"""
    try:
        # 检查是否已有词云文件且较新
        output_path = get_abs_path("static/authorNameCloud.jpg")
        if os.path.exists(output_path):
            # 如果文件存在且在30分钟内，直接返回
            if time.time() - os.path.getmtime(output_path) < 1800:  # 30分钟
                return output_path

        stopwords = stopwordslist()
        comments = _comment_repo().get_all_for_export()
        # 只取最近 1000 条，兼容旧逻辑
        recent_comments = comments[:1000] if len(comments) > 1000 else comments
        text = " ".join(c["authorName"] for c in recent_comments if c.get("authorName"))

        if not text.strip():
            print("没有找到用户名数据")
            return None

        # 分词处理
        cut = jieba.cut(text)
        newCut = []
        for word in cut:
            if word not in stopwords and len(word.strip()) > 1:  # 过滤单字符
                newCut.append(word)

        if not newCut:
            print("分词后没有有效词汇")
            return None

        string = " ".join(newCut)

        # 生成词云
        wc = WordCloud(
            width=1000,
            height=600,
            background_color="white",
            colormap="Blues",
            font_path="STHUPO.TTF",
            max_words=100,  # 限制词汇数量提升性能
            relative_scaling=0.5,
        )
        wc.generate_from_text(string)

        # 绘制图片
        plt.figure(figsize=(10, 6))
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")

        # 保存到文件
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()  # 释放内存

        print(f"词云已生成: {output_path}")
        return output_path

    except Exception as e:
        print(f"生成词云失败: {e}")
        return None