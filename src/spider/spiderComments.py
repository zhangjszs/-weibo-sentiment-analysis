#!/usr/bin/env python3
"""
微博评论爬虫模块
功能：爬取微博评论数据，支持热评和普通评论
特性：请求重试、数据去重、完善的异常处理
"""

import csv
import logging
import os
import re
import sys
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    DEFAULT_DELAY,
    get_random_headers,
    get_working_proxy,
)
from utils.deduplicator import comment_deduplicator

# 配置日志
logger = logging.getLogger("spider.comments")

# ========== 配置常量 ==========
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY_BASE = 2  # 基础重试延迟（秒）
REQUEST_TIMEOUT = 30  # 请求超时（秒）
RATE_LIMIT_WAIT = 60  # 频率限制等待时间（秒）

# 全局CSV写入锁，防止并发写入冲突
_csv_write_lock = threading.Lock()


def init():
    """初始化CSV文件和目录"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    comments_path = os.path.join(data_dir, "commentsData.csv")

    if not os.path.exists(comments_path):
        with open(comments_path, "w", encoding="utf8", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "comment_id",  # 评论ID
                    "articleId",  # 文章ID
                    "created_at",  # 创建时间
                    "like_counts",  # 点赞数
                    "region",  # IP属地
                    "content",  # 评论内容
                    "authorName",  # 作者名称
                    "authorGender",  # 作者性别
                    "authorAddress",  # 作者地址
                    "authorAvatar",  # 作者头像
                    "user_id",  # 用户ID
                    "reply_count",  # 回复数
                    "comment_source",  # 评论来源
                    "is_hot",  # 是否热评
                    "parent_id",  # 父评论ID（子回复专用）
                    "reply_to_user",  # 回复的目标用户
                    "verified_type",  # 用户认证类型
                    "followers_count",  # 粉丝数
                ]
            )


def writerRow(row: List[Any]) -> bool:
    """
    线程安全的CSV行写入

    Args:
        row: 要写入的数据行

    Returns:
        bool: 写入是否成功
    """
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    comments_path = os.path.join(data_dir, "commentsData.csv")

    try:
        with _csv_write_lock:
            with open(comments_path, "a", encoding="utf8", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(row)
        return True
    except Exception as e:
        logger.error(f"CSV写入失败: {e}")
        return False


def get_json(
    url: str,
    article_id: str,
    uid: Optional[str] = None,
    max_id: int = 0,
    retries: int = MAX_RETRIES,
) -> Optional[Dict]:
    """
    获取评论JSON数据（带重试机制）

    Args:
        url: API地址
        article_id: 文章ID
        uid: 用户ID
        max_id: 分页参数
        retries: 剩余重试次数

    Returns:
        JSON数据或None
    """
    import time

    headers = get_random_headers()
    proxy = get_working_proxy()

    # 设置正确的Referer
    if uid:
        headers["Referer"] = f"https://weibo.com/{uid}/"

    params = {
        "is_reload": "1",
        "id": article_id,
        "is_show_bulletin": "2",
        "is_mix": "0",
        "count": "20",
        "uid": uid or "nouid",
        "fetch_level": "0",
        "locale": "zh-CN",
    }

    if max_id > 0:
        params["max_id"] = str(max_id)

    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                proxies=proxy,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError as e:
                    logger.error(f"JSON解析失败: {e}")
                    return None

            elif response.status_code == 403:
                logger.warning("请求被拒绝(403)，可能Cookie已过期")
                return None

            elif response.status_code == 429:
                logger.warning("请求频率过高(429)，等待后重试")
                time.sleep(RATE_LIMIT_WAIT)

            else:
                logger.warning(f"请求失败，状态码: {response.status_code}")
                if attempt < retries - 1:
                    time.sleep(RETRY_DELAY_BASE * (attempt + 1))

        except requests.exceptions.Timeout:
            logger.warning(f"请求超时 (尝试 {attempt + 1}/{retries})")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY_BASE * (attempt + 1))

        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {e}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY_BASE * (attempt + 1))

    logger.error(f"请求最终失败: article_id={article_id}")
    return None


def remove_html_tags(html_text: str) -> str:
    """移除HTML标签"""
    if not html_text:
        return ""
    return re.sub(r"<[^>]+>", "", html_text)


def parse_created_time(created_at_raw: str) -> str:
    """
    解析评论时间格式

    Args:
        created_at_raw: 原始时间字符串

    Returns:
        格式化后的时间字符串
    """
    if not created_at_raw:
        return "Unknown"

    time_formats = [
        "%a %b %d %H:%M:%S %z %Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for fmt in time_formats:
        try:
            parsed = datetime.strptime(created_at_raw, fmt)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

    return created_at_raw


def process_comment(
    comment: Dict, article_id: str, is_hot: bool = False, parent_id: str = ""
) -> bool:
    """
    处理每条评论的逻辑

    Args:
        comment: 评论数据
        article_id: 文章ID
        is_hot: 是否热评
        parent_id: 父评论ID

    Returns:
        bool: 处理是否成功
    """
    try:
        comment_id = str(comment.get("id", ""))

        # 检查是否重复
        if comment_deduplicator.is_duplicate(comment_id, article_id):
            logger.debug(f"跳过重复评论: {comment_id}")
            return False

        # 解析时间
        created_at = parse_created_time(comment.get("created_at", ""))

        # 基础字段
        like_counts = comment.get("attitudes_count", 0)
        reply_count = comment.get("total_number", 0)

        # 用户信息
        user = comment.get("user", {})
        user_id = str(user.get("id", ""))
        author_name = user.get("screen_name", "Unknown")
        author_gender = user.get("gender", "Unknown")
        author_address = (
            user.get("location", "Unknown").split(" ")[0]
            if user.get("location")
            else "Unknown"
        )
        author_avatar = user.get("avatar_large", "")

        # 用户认证和粉丝数
        verified_type = user.get("verified_type", -1)
        followers_count = user.get("followers_count", 0)

        # IP属地和来源
        region = comment.get("source", "").replace("来自", "").strip() or "无"
        comment_source = comment.get("source", "")

        # 评论内容
        content = comment.get("text_raw", "") or comment.get("text", "")
        content = remove_html_tags(content) or "表情"

        # 回复目标用户
        reply_to_user = ""
        if "reply_comment" in comment and comment["reply_comment"]:
            reply_user_info = comment["reply_comment"].get("user", {})
            reply_to_user = (
                reply_user_info.get("screen_name", "") if reply_user_info else ""
            )

        # 写入CSV
        success = writerRow(
            [
                comment_id,
                article_id,
                created_at,
                like_counts,
                region,
                content,
                author_name,
                author_gender,
                author_address,
                author_avatar,
                user_id,
                reply_count,
                comment_source,
                is_hot,
                parent_id,
                reply_to_user,
                verified_type,
                followers_count,
            ]
        )

        if success:
            # 添加到去重过滤器
            comment_deduplicator.add(comment_id, article_id)

            # 处理子回复（楼中楼）
            if reply_count > 0 and "comments" in comment:
                sub_comments = comment.get("comments", [])
                for sub_comment in sub_comments:
                    process_comment(
                        sub_comment, article_id, is_hot=False, parent_id=comment_id
                    )

            return True

        return False

    except Exception as e:
        logger.error(f"处理评论失败: article_id={article_id}, error={e}")
        return False


def parse_json(response: Optional[Dict], article_id: str) -> str:
    """
    解析评论JSON数据

    Args:
        response: API响应数据
        article_id: 文章ID

    Returns:
        str: 处理结果状态
    """
    logger.debug(f"Processing articleId {article_id}")

    if response is None:
        logger.error("Received None response")
        return "ERROR_NONE_RESPONSE"

    if not isinstance(response, dict):
        logger.error(f"Expected response to be a dict, but got {type(response)}")
        return "ERROR_INVALID_TYPE"

    if response.get("ok") == 0:
        error_msg = response.get("msg", "Unknown API error")
        logger.error(f"API returned failure: {error_msg}")
        if "访问频次过高" in error_msg:
            return "RATE_LIMITED"
        return "API_ERROR"

    try:
        comments_processed = 0

        # 处理热评
        hot_comments = response.get("hot_comments", [])
        if hot_comments:
            logger.debug(f"Found {len(hot_comments)} hot comments")
            for comment in hot_comments:
                if process_comment(comment, article_id, is_hot=True):
                    comments_processed += 1

        # 处理普通评论
        comment_list = response.get("data", [])
        if comment_list and isinstance(comment_list, list):
            logger.debug(f"Found {len(comment_list)} regular comments")

            # 获取热评ID集合，避免重复处理
            hot_comment_ids = (
                {hc.get("id") for hc in hot_comments} if hot_comments else set()
            )

            for comment in comment_list:
                comment_id = comment.get("id", "")
                if comment_id not in hot_comment_ids:
                    if process_comment(comment, article_id, is_hot=False):
                        comments_processed += 1

        if comments_processed == 0:
            logger.info(f"No comments found for articleId {article_id}")
            return "NO_COMMENTS"

        logger.info(f"Successfully processed {comments_processed} comments")
        return "SUCCESS"

    except Exception as e:
        logger.error(f"Error processing comments: {e}")
        return "ERROR_PROCESSING"


def start(max_comment_pages: int = 5) -> int:
    """
    爬取评论数据

    Args:
        max_comment_pages: 每篇文章最多爬取的评论页数

    Returns:
        int: 成功处理的文章数量
    """
    import random
    import time

    init()
    url = "https://weibo.com/ajax/statuses/buildComments"
    article_csv_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "articleData.csv"
    )

    if not os.path.exists(article_csv_path):
        logger.error(f"Input file not found: {article_csv_path}")
        return 0

    processed_articles = 0

    try:
        with open(article_csv_path, encoding="utf8") as readerFile:
            reader = csv.reader(readerFile)
            try:
                header = next(reader)
                logger.info(f"Input CSV Header: {header}")
            except StopIteration:
                logger.error(f"Input file is empty: {article_csv_path}")
                return 0

            for i, article in enumerate(reader):
                if not article:
                    continue

                try:
                    article_id = article[0]
                    comments_count = (
                        int(article[2])
                        if len(article) > 2 and article[2].isdigit()
                        else 0
                    )
                except (IndexError, ValueError) as e:
                    logger.warning(f"Skipping row {i + 2}: {e}")
                    continue

                # 提取uid
                uid = None
                if len(article) > 9:
                    detail_url = article[9]
                    if detail_url and "weibo.com" in detail_url:
                        try:
                            parts = detail_url.replace("https://weibo.com/", "").split(
                                "/"
                            )
                            if len(parts) >= 1:
                                uid = parts[0]
                        except Exception as e:
                            logger.debug(f"Failed to extract uid from URL: {e}")

                logger.info(
                    f"\n=== Article {i + 2}: ID {article_id}, Comments: {comments_count} ==="
                )

                # 根据评论数量决定爬取页数
                pages_to_fetch = min(
                    max_comment_pages, max(1, (comments_count // 20) + 1)
                )
                max_id = 0
                article_success = False

                for page in range(1, pages_to_fetch + 1):
                    # 延时防爬
                    if isinstance(DEFAULT_DELAY, tuple):
                        wait_seconds = random.uniform(
                            DEFAULT_DELAY[0], DEFAULT_DELAY[1]
                        )
                    else:
                        wait_seconds = DEFAULT_DELAY

                    logger.info(
                        f"Fetching page {page}/{pages_to_fetch} for article {article_id}"
                    )
                    time.sleep(wait_seconds)

                    # 请求评论数据
                    response = get_json(url, article_id, uid, max_id)

                    if response is None:
                        logger.warning(f"Failed to get response for page {page}")
                        break

                    # 解析评论
                    parse_result = parse_json(response, article_id)

                    if parse_result == "RATE_LIMITED":
                        logger.warning(
                            f"Rate limit hit. Waiting for {RATE_LIMIT_WAIT} seconds..."
                        )
                        time.sleep(RATE_LIMIT_WAIT)
                        continue
                    elif parse_result == "NO_COMMENTS":
                        logger.info(f"No more comments for article {article_id}")
                        break
                    elif parse_result == "API_ERROR":
                        logger.error(
                            f"API error, stopping pagination for article {article_id}"
                        )
                        break
                    elif parse_result == "SUCCESS":
                        article_success = True

                    # 获取用于下一页的max_id
                    new_max_id = response.get("max_id", 0)
                    if new_max_id == 0 or new_max_id == max_id:
                        logger.info(f"No more pages available for article {article_id}")
                        break
                    max_id = new_max_id

                if article_success:
                    processed_articles += 1

    except Exception as e:
        logger.error(f"爬取过程发生错误: {e}", exc_info=True)

    # 保存去重状态
    comment_deduplicator.save()

    logger.info(f"\n=== Finished processing {processed_articles} articles ===")
    return processed_articles


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    start(max_comment_pages=2)
