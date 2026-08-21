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
from typing import Any, Dict, List, Optional, Tuple

import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from spider.config import (
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


# ========== 初始化和写入 ==========


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
    except OSError as e:
        logger.error(f"CSV写入失败: {e}")
        return False


def _save_comment_to_db(
    comment_id, article_id, created_at, like_counts, region, content,
    author_name, author_gender, author_address, author_avatar, user_id,
    reply_count, comment_source, is_hot, parent_id, reply_to_user,
    verified_type, followers_count,
) -> None:
    """双写：将评论写入 DB（best-effort）。

    P1.2：CSV 仍是下游（spiderUserInfo / yuqing 模型 / main.py）依赖的数据源，
    DB 作为可靠副本以消除"CSV 写入失败静默丢数据"的风险。失败仅记录日志、不抛
    异常，不影响 CSV 主流程。schema 由 Alembic 迁移 a1c4f2e8b9d0 与
    归档 SQL（docs/database/，已冻结）统一管理（P0 #4 移除了运行时 ensure_comments_columns hack）。
    """
    try:
        from sqlalchemy.exc import IntegrityError

        from database import db_session
        from models.comment import Comment

        # articleId 在模型中是 BigInteger；非数字时跳过本次 DB 写入
        try:
            article_id_int = int(article_id)
        except (TypeError, ValueError):
            logger.warning("article_id 非数字，跳过 DB 写入: %r", article_id)
            return

        comment = Comment(
            articleId=article_id_int,
            created_at=created_at,
            content=content,
            likeNum=like_counts or 0,
            user=author_name,
            region=region,
            authorGender=author_gender,
            authorAddress=author_address,
            authorAvatar=author_avatar,
            comment_id=comment_id,
            user_id=user_id,
            reply_count=reply_count or 0,
            comment_source=comment_source,
            is_hot=bool(is_hot),
            parent_id=parent_id,
            reply_to_user=reply_to_user,
            verified_type=verified_type if verified_type is not None else -1,
            followers_count=followers_count or 0,
        )
        db_session.add(comment)
        db_session.commit()
    except IntegrityError as e:
        # comment_id 主键冲突 — 评论已存在（重爬同一微博评论），视为成功
        try:
            db_session.rollback()
        except Exception:
            pass
        logger.debug("评论已存在于DB（主键冲突），跳过: %s", getattr(e, "orig", e))
    except Exception as e:
        try:
            db_session.rollback()
        except Exception:
            pass
        logger.error("DB写入评论失败（CSV仍已写入）: %s", e)


# ========== 请求构建与执行 ==========


def _build_request_params(
    article_id: str, uid: Optional[str], max_id: int
) -> Dict[str, str]:
    """构建请求参数字典"""
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
    return params


def _execute_single_request(
    url: str,
    headers: Dict[str, str],
    params: Dict[str, str],
    proxy: Optional[Dict],
) -> Optional[Dict]:
    """
    执行单次HTTP请求并解析响应

    Returns:
        JSON数据、None（解析失败）、或抛出请求异常

    Raises:
        requests.exceptions.Timeout: 请求超时
        requests.exceptions.RequestException: 请求异常
    """
    response = requests.get(
        url,
        headers=headers,
        params=params,
        proxies=proxy,
        timeout=REQUEST_TIMEOUT,
    )

    if response.status_code == 200:
        return response.json()

    if response.status_code == 403:
        logger.warning("请求被拒绝(403)，可能Cookie已过期")
        return None

    if response.status_code == 429:
        logger.warning("请求频率过高(429)，等待后重试")
        import time
        time.sleep(RATE_LIMIT_WAIT)
        return "RETRY"

    logger.warning(f"请求失败，状态码: {response.status_code}")
    return "RETRY"


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

    params = _build_request_params(article_id, uid, max_id)

    for attempt in range(retries):
        try:
            result = _execute_single_request(url, headers, params, proxy)
            if result is None:
                return None
            if result == "RETRY":
                if attempt < retries - 1:
                    time.sleep(RETRY_DELAY_BASE * (attempt + 1))
                continue
            return result
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


# ========== HTML / 时间处理 ==========


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


# ========== 评论处理 ==========


def _extract_user_info(user: Dict) -> Dict[str, Any]:
    """从评论user字段中提取用户信息"""
    author_address = "Unknown"
    location = user.get("location", "")
    if location:
        author_address = location.split(" ")[0]

    return {
        "user_id": str(user.get("id", "")),
        "author_name": user.get("screen_name", "Unknown"),
        "author_gender": user.get("gender", "Unknown"),
        "author_address": author_address,
        "author_avatar": user.get("avatar_large", ""),
        "verified_type": user.get("verified_type", -1),
        "followers_count": user.get("followers_count", 0),
    }


def _extract_reply_to_user(comment: Dict) -> str:
    """提取回复目标用户名称"""
    reply_comment = comment.get("reply_comment")
    if not reply_comment:
        return ""
    reply_user_info = reply_comment.get("user", {})
    if not reply_user_info:
        return ""
    return reply_user_info.get("screen_name", "")


def _process_sub_comments(
    comment: Dict, article_id: str, parent_id: str
) -> None:
    """处理子回复（楼中楼）"""
    reply_count = comment.get("total_number", 0)
    if reply_count <= 0 or "comments" not in comment:
        return
    for sub_comment in comment.get("comments", []):
        process_comment(sub_comment, article_id, is_hot=False, parent_id=parent_id)


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
    user_info = _extract_user_info(comment.get("user", {}))

    # IP属地和来源
    region = comment.get("source", "").replace("来自", "").strip() or "无"
    comment_source = comment.get("source", "")

    # 评论内容
    content = comment.get("text_raw", "") or comment.get("text", "")
    content = remove_html_tags(content) or "表情"

    # 回复目标用户
    reply_to_user = _extract_reply_to_user(comment)

    # 写入CSV
    success = writerRow(
        [
            comment_id,
            article_id,
            created_at,
            like_counts,
            region,
            content,
            user_info["author_name"],
            user_info["author_gender"],
            user_info["author_address"],
            user_info["author_avatar"],
            user_info["user_id"],
            reply_count,
            comment_source,
            is_hot,
            parent_id,
            reply_to_user,
            user_info["verified_type"],
            user_info["followers_count"],
        ]
    )

    # 双写 DB（best-effort：失败仅记日志，不影响下方 CSV 成败判定与去重）
    _save_comment_to_db(
        comment_id=comment_id,
        article_id=article_id,
        created_at=created_at,
        like_counts=like_counts,
        region=region,
        content=content,
        author_name=user_info["author_name"],
        author_gender=user_info["author_gender"],
        author_address=user_info["author_address"],
        author_avatar=user_info["author_avatar"],
        user_id=user_info["user_id"],
        reply_count=reply_count,
        comment_source=comment_source,
        is_hot=is_hot,
        parent_id=parent_id,
        reply_to_user=reply_to_user,
        verified_type=user_info["verified_type"],
        followers_count=user_info["followers_count"],
    )

    if not success:
        return False

    # 添加到去重过滤器
    comment_deduplicator.add(comment_id, article_id)

    # 处理子回复（楼中楼）
    _process_sub_comments(comment, article_id, comment_id)

    return True


# ========== JSON解析 ==========


def _validate_response(response: Optional[Dict]) -> Optional[str]:
    """
    校验API响应的基本结构

    Returns:
        None表示校验通过，否则返回错误状态字符串
    """
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

    return None


def _process_hot_comments(
    hot_comments: List[Dict], article_id: str
) -> Tuple[int, set]:
    """
    处理热评列表

    Returns:
        (处理成功的评论数, 热评ID集合)
    """
    processed = 0
    hot_ids: set = set()
    if not hot_comments:
        return processed, hot_ids

    logger.debug(f"Found {len(hot_comments)} hot comments")
    for comment in hot_comments:
        hot_ids.add(comment.get("id"))
        if process_comment(comment, article_id, is_hot=True):
            processed += 1
    return processed, hot_ids


def _process_regular_comments(
    comment_list: List[Dict], hot_comment_ids: set, article_id: str
) -> int:
    """
    处理普通评论列表（排除已处理的热评）

    Returns:
        处理成功的评论数
    """
    if not comment_list or not isinstance(comment_list, list):
        return 0

    logger.debug(f"Found {len(comment_list)} regular comments")
    processed = 0
    for comment in comment_list:
        comment_id = comment.get("id", "")
        if comment_id not in hot_comment_ids:
            if process_comment(comment, article_id, is_hot=False):
                processed += 1
    return processed


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

    error_status = _validate_response(response)
    if error_status:
        return error_status

    try:
        hot_processed, hot_ids = _process_hot_comments(
            response.get("hot_comments", []), article_id
        )
        regular_processed = _process_regular_comments(
            response.get("data", []), hot_ids, article_id
        )

        comments_processed = hot_processed + regular_processed

        if comments_processed == 0:
            logger.info(f"No comments found for articleId {article_id}")
            return "NO_COMMENTS"

        logger.info(f"Successfully processed {comments_processed} comments")
        return "SUCCESS"

    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error processing comments: {e}")
        return "ERROR_PROCESSING"


# ========== 文章遍历 ==========


def _extract_uid(detail_url: str) -> Optional[str]:
    """从文章详情URL中提取用户uid"""
    if not detail_url or "weibo.com" not in detail_url:
        return None
    try:
        parts = detail_url.replace("https://weibo.com/", "").split("/")
        return parts[0] if parts else None
    except (ValueError, IndexError) as e:
        logger.debug(f"Failed to extract uid from URL: {e}")
        return None


def _parse_article_row(article: List[str], row_index: int) -> Optional[Tuple[str, Optional[str], int]]:
    """
    解析CSV的一行文章数据

    Returns:
        (article_id, uid, comments_count) 或 None（解析失败）
    """
    try:
        article_id = article[0]
        comments_count = (
            int(article[2])
            if len(article) > 2 and article[2].isdigit()
            else 0
        )
    except (IndexError, ValueError) as e:
        logger.warning(f"Skipping row {row_index}: {e}")
        return None

    # 提取uid
    uid = None
    if len(article) > 9:
        uid = _extract_uid(article[9])

    return article_id, uid, comments_count


def _get_delay_seconds() -> float:
    """获取一次随机延时（秒）"""
    import random
    if isinstance(DEFAULT_DELAY, tuple):
        return random.uniform(DEFAULT_DELAY[0], DEFAULT_DELAY[1])
    return DEFAULT_DELAY


def _handle_parse_result(parse_result: str, article_id: str) -> bool:
    """
    处理解析结果，决定是否继续分页

    Returns:
        True表示应继续下一页，False表示应停止
    """
    if parse_result == "RATE_LIMITED":
        logger.warning(
            f"Rate limit hit. Waiting for {RATE_LIMIT_WAIT} seconds..."
        )
        import time
        time.sleep(RATE_LIMIT_WAIT)
        return True  # 重试当前页（调用方需注意）

    if parse_result == "NO_COMMENTS":
        logger.info(f"No more comments for article {article_id}")
        return False

    if parse_result == "API_ERROR":
        logger.error(f"API error, stopping pagination for article {article_id}")
        return False

    return True  # SUCCESS 或其他未知状态


def _fetch_page_comments(
    url: str, article_id: str, uid: Optional[str], max_id: int
) -> Tuple[Optional[Dict], str]:
    """
    获取并解析一页评论

    Returns:
        (response_data, parse_result) — response_data 可为 None
    """
    response = get_json(url, article_id, uid, max_id)
    if response is None:
        return None, "ERROR_NONE_RESPONSE"

    parse_result = parse_json(response, article_id)
    return response, parse_result


def _process_single_article(
    url: str,
    article_id: str,
    uid: Optional[str],
    comments_count: int,
    max_comment_pages: int,
) -> bool:
    """
    处理单篇文章的所有评论页

    Returns:
        bool: 是否有评论被成功处理
    """
    import time

    pages_to_fetch = min(
        max_comment_pages, max(1, (comments_count // 20) + 1)
    )
    max_id = 0
    article_success = False

    for page in range(1, pages_to_fetch + 1):
        wait_seconds = _get_delay_seconds()
        logger.info(
            f"Fetching page {page}/{pages_to_fetch} for article {article_id}"
        )
        time.sleep(wait_seconds)

        response, parse_result = _fetch_page_comments(
            url, article_id, uid, max_id
        )

        if response is None:
            logger.warning(f"Failed to get response for page {page}")
            break

        if parse_result == "SUCCESS":
            article_success = True

        # 对 RATE_LIMITED 做特殊处理：重试当前页不前进 max_id
        if parse_result == "RATE_LIMITED":
            logger.warning(
                f"Rate limit hit. Waiting for {RATE_LIMIT_WAIT} seconds..."
            )
            time.sleep(RATE_LIMIT_WAIT)
            continue

        if not _handle_parse_result(parse_result, article_id):
            break

        # 获取用于下一页的max_id
        new_max_id = response.get("max_id", 0)
        if new_max_id == 0 or new_max_id == max_id:
            logger.info(f"No more pages available for article {article_id}")
            break
        max_id = new_max_id

    return article_success


def start(max_comment_pages: int = 5) -> int:
    """
    爬取评论数据

    Args:
        max_comment_pages: 每篇文章最多爬取的评论页数

    Returns:
        int: 成功处理的文章数量
    """
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

                parsed = _parse_article_row(article, i + 2)
                if parsed is None:
                    continue

                article_id, uid, comments_count = parsed
                logger.info(
                    f"\n=== Article {i + 2}: ID {article_id}, Comments: {comments_count} ==="
                )

                if _process_single_article(
                    url, article_id, uid, comments_count, max_comment_pages
                ):
                    processed_articles += 1

    except OSError as e:
        logger.error(f"爬取过程发生错误: {e}", exc_info=True)

    # 保存去重状态
    comment_deduplicator.save()

    logger.info(f"\n=== Finished processing {processed_articles} articles ===")
    return processed_articles


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    start(max_comment_pages=2)
