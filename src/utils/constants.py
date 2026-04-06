#!/usr/bin/env python3
"""
常量定义模块
功能：集中定义项目中使用的所有业务常量
作者：微博舆情分析系统

说明：
- 将分散在代码中的魔法数字统一管理
- 每个常量都有详细注释说明用途
- 其他模块应从此处导入常量
"""

import os
from typing import Final

from config.settings import Config

# ========== 数据分布统计常量 ==========

# 点赞数/转发数分布区间大小
LIKE_COUNT_RANGE: Final[int] = 1000
"""点赞数分布区间大小，用于统计不同点赞区间的文章数量"""

# 转发数分布区间大小
FORWARD_COUNT_RANGE: Final[int] = 1000
"""转发数分布区间大小"""

# 评论数分布区间大小
COMMENT_COUNT_RANGE: Final[int] = 50
"""评论数分布区间大小"""

# 评论点赞分布区间大小
COMMENT_LIKE_RANGE: Final[int] = 20
"""评论点赞数分布区间大小"""

# 文章分布统计区间数量
ARTICLE_DISTRIBUTION_BUCKETS: Final[int] = 14
"""将点赞/转发数划分为14个区间进行统计"""

# 评论分布统计区间数量
COMMENT_DISTRIBUTION_BUCKETS: Final[int] = 29
"""评论数划分为29个区间进行统计"""

# 评论点赞分布统计区间数量
COMMENT_LIKE_DISTRIBUTION_BUCKETS: Final[int] = 99
"""评论点赞数划分为99个区间进行统计"""


# ========== 展示数量限制 ==========

# 热词排行展示数量
TOP_HOT_WORDS_COUNT: Final[int] = 10
"""舆情分析页面显示的热词数量"""

# 首页热门评论数量
TOP_COMMENTS_COUNT: Final[int] = 5
"""首页展示的热门评论数量"""


# ========== 情感分析常量 ==========

# 情感分析阈值
SENTIMENT_POSITIVE_THRESHOLD: Final[float] = 0.5
"""情感分析中判断为正面的阈值"""

SENTIMENT_NEGATIVE_THRESHOLD: Final[float] = 0.5
"""情感分析中判断为负面的阈值"""

# 情感标签
SENTIMENT_LABELS: Final[tuple] = ("正面", "中性", "负面")
"""情感分析的三种标签"""


# ========== 词云相关常量 ==========

# 词云图片尺寸
WORDCLOUD_WIDTH: Final[int] = 1000
"""词云图片宽度"""

WORDCLOUD_HEIGHT: Final[int] = 600
"""词云图片高度"""

# 词云图片DPI
WORDCLOUD_DPI: Final[int] = 500
"""词云图片保存时的DPI"""


# ========== 数据库表名 ==========

TABLE_ARTICLE: Final[str] = "article"
"""文章数据表名"""

TABLE_COMMENTS: Final[str] = "comments"
"""评论数据表名"""

TABLE_USER: Final[str] = "user"
"""用户数据表名"""


# ========== 文件路径常量 ==========

# 停用词文件路径
STOPWORDS_FILE: Final[str] = os.path.join(Config.MODEL_DIR, "stopWords.txt")
"""停用词文件路径"""

# 词云模板图片路径
CONTENT_MASK_IMAGE: Final[str] = os.path.join(Config.STATIC_DIR, "content.jpg")
"""内容词云遮罩图片"""

COMMENT_MASK_IMAGE: Final[str] = os.path.join(Config.STATIC_DIR, "comment.jpg")
"""评论词云遮罩图片"""

# 词云输出路径
CONTENT_CLOUD_OUTPUT: Final[str] = os.path.join(Config.STATIC_DIR, "contentCloud.jpg")
"""内容词云输出路径"""

COMMENT_CLOUD_OUTPUT: Final[str] = os.path.join(Config.STATIC_DIR, "commentCloud.jpg")
"""评论词云输出路径"""


# ========== 字体配置 ==========

# 词云使用的字体
WORDCLOUD_FONT: Final[str] = "STHUPO.TTF"
"""词云使用的中文字体"""

# 词云颜色方案
WORDCLOUD_COLORMAP: Final[str] = "Blues"
"""词云颜色方案"""

# 词云背景颜色
WORDCLOUD_BACKGROUND: Final[str] = "white"
"""词云背景颜色"""
