"""
任务模块初始化文件
"""

# 导出主要任务
from .celery_sentiment import analyze_sentiment_batch, analyze_single_with_fallback
from .celery_spider import get_task_progress, spider_comments_task, spider_search_task

__all__ = [
    "spider_search_task",
    "spider_comments_task",
    "get_task_progress",
    "analyze_sentiment_batch",
    "analyze_single_with_fallback",
]
