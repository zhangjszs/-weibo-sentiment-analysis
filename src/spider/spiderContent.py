#!/usr/bin/env python3
"""
微博文章爬虫模块
功能：爬取微博文章数据，支持分类爬取和关键词搜索
特性：请求重试、数据去重、完善的异常处理
"""

import csv
import logging
import os
import random
import re
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from .config import (
    DEFAULT_DELAY,
    get_random_headers,
    get_working_proxy,
)
from utils.deduplicator import article_deduplicator

# 导入监控系统
try:
    from monitor import log_request, log_error, log_crawled_item, log_proxy_usage
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False
    logging.warning("监控系统未加载")

# 导入浏览器管理器
try:
    from browser_manager import navigate, get_content, wait_for_selector, scroll
    BROWSER_AVAILABLE = True
except ImportError:
    BROWSER_AVAILABLE = False
    logging.warning("浏览器管理器未加载")

# 导入智能调度系统
try:
    from intelligent_scheduler import (
        get_scheduler, adjust_crawl_strategy, 
        get_optimal_delay, should_use_browser, 
        get_optimal_proxy
    )
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    logging.warning("智能调度系统未加载")

# 配置日志
logger = logging.getLogger("spider.content")

# ========== 配置常量 ==========
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY_BASE = 2  # 基础重试延迟（秒）
REQUEST_TIMEOUT = 30  # 请求超时（秒）
MAX_RETRY_DELAY = 60  # 最大重试延迟（秒）

# 全局CSV写入锁，防止并发写入冲突
_csv_write_lock = threading.Lock()


def _handle_request_error(error: Exception, context: str = "") -> None:
    """
    处理HTTP请求错误

    实现HTTP状态码分类处理、指数退避重试、特定错误处理（429限速、403禁止等）、
    日志记录和最大重试限制

    Args:
        error: 捕获的异常对象
        context: 错误上下文信息（如URL或操作描述）
    """
    error_type = type(error).__name__
    error_msg = str(error)

    # 根据异常类型进行分类处理
    if isinstance(error, requests.exceptions.HTTPError):
        # HTTP错误（4xx, 5xx）
        status_code = error.response.status_code if hasattr(error, 'response') else 0

        if status_code == 429:
            # 请求频率限制
            logger.error(f"[429] 请求频率过高，请稍后重试。上下文: {context}")
            # 计算退避时间
            retry_after = error.response.headers.get('Retry-After', RETRY_DELAY_BASE * 2)
            logger.info(f"建议等待 {retry_after} 秒后重试")
        elif status_code == 403:
            # 禁止访问（可能是Cookie过期）
            logger.error(f"[403] 访问被拒绝，可能Cookie已过期。上下文: {context}")
            logger.warning(">>> 请检查 spider/config.py 中的 Cookie 是否过期！ <<<")
        elif status_code == 401:
            # 未授权
            logger.error(f"[401] 未授权访问，请检查认证信息。上下文: {context}")
        elif status_code == 404:
            # 资源未找到
            logger.error(f"[404] 请求的资源不存在。上下文: {context}")
        elif status_code == 500:
            logger.error(f"[500] 服务器内部错误。上下文: {context}")
        elif status_code == 502:
            logger.error(f"[502] 网关错误。上下文: {context}")
        elif status_code == 503:
            logger.error(f"[503] 服务不可用。上下文: {context}")
        elif status_code == 504:
            logger.error(f"[504] 网关超时。上下文: {context}")
        else:
            logger.error(f"[HTTP {status_code}] 请求失败。上下文: {context}")

    elif isinstance(error, requests.exceptions.Timeout):
        # 请求超时
        logger.error(f"[Timeout] 请求超时。上下文: {context}")

    elif isinstance(error, requests.exceptions.ConnectionError):
        # 连接错误
        logger.error(f"[ConnectionError] 连接失败，请检查网络。上下文: {context}")

    elif isinstance(error, requests.exceptions.RequestException):
        # 其他请求异常
        logger.error(f"[RequestException] 请求异常: {error_msg}。上下文: {context}")

    else:
        # 未知异常
        logger.error(f"[{error_type}] 未处理的错误: {error_msg}。上下文: {context}")


def init():
    """初始化CSV文件和目录"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    article_path = os.path.join(data_dir, "articleData.csv")

    if not os.path.exists(article_path):
        with open(article_path, "w", encoding="utf8", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "id",
                    "likeNum",
                    "commentsLen",
                    "reposts_count",
                    "region",
                    "content",
                    "contentLen",
                    "created_at",
                    "type",
                    "detailUrl",
                    "authorAvatar",
                    "authorName",
                    "authorDetail",
                    "isVip",
                    "source",  # 发布设备来源
                    "topics",  # 话题标签列表
                    "at_users",  # @提及的用户
                    "pic_urls",  # 图片URL列表
                    "video_url",  # 视频URL
                    "is_long_text",  # 是否长文本
                    "verified_type",  # 用户认证类型
                    "verified_reason",  # 认证描述
                    "followers_count",  # 粉丝数
                    "friends_count",  # 关注数
                    "retweeted_id",  # 转发的原微博ID
                    "retweeted_text",  # 转发的原微博内容
                    "retweeted_user",  # 原微博作者
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
    article_path = os.path.join(data_dir, "articleData.csv")

    try:
        with _csv_write_lock:
            with open(article_path, "a", encoding="utf8", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(row)
        return True
    except Exception as e:
        logger.error(f"CSV写入失败: {e}")
        return False


def get_json(
    url: str, params: Dict[str, Any], retries: int = MAX_RETRIES
) -> Optional[Dict]:
    """
    发送GET请求并返回JSON数据（带重试机制）

    Args:
        url: 请求URL
        params: 请求参数
        retries: 剩余重试次数

    Returns:
        JSON数据或None
    """
    headers = get_random_headers()
    
    # 使用智能调度系统获取代理
    if SCHEDULER_AVAILABLE:
        proxy = get_optimal_proxy()
    else:
        proxy = get_working_proxy()
    
    proxy_str = str(proxy) if proxy else "no_proxy"

    for attempt in range(retries):
        start_time = time.time()
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                proxies=proxy,
                timeout=REQUEST_TIMEOUT,
            )

            response_time = time.time() - start_time

            if response.status_code == 200:
                try:
                    json_data = response.json()
                    # 记录成功请求
                    if MONITOR_AVAILABLE:
                        log_request(True, url)
                        if proxy:
                            log_proxy_usage(proxy_str, True)
                    # 智能调度系统更新
                    if SCHEDULER_AVAILABLE:
                        adjust_crawl_strategy(True, response_time)
                    return json_data
                except ValueError as e:
                    logger.error(f"JSON解析失败: {e}")
                    logger.debug(f"响应内容: {response.text[:200]}...")
                    if MONITOR_AVAILABLE:
                        log_request(False, url)
                        log_error(f"JSON解析失败: {e}")
                    # 智能调度系统更新
                    if SCHEDULER_AVAILABLE:
                        adjust_crawl_strategy(False, response_time, "parse_error")
                    return None

            elif response.status_code == 403:
                logger.warning("请求被拒绝(403)，可能Cookie已过期")
                if MONITOR_AVAILABLE:
                    log_request(False, url)
                    log_error("请求被拒绝(403)，可能Cookie已过期")
                # 智能调度系统更新
                if SCHEDULER_AVAILABLE:
                    adjust_crawl_strategy(False, response_time, "cookie_expired")
                # 403错误不重试，直接返回
                return None

            elif response.status_code == 429:
                logger.warning("请求频率过高(429)，等待后重试")
                if MONITOR_AVAILABLE:
                    log_request(False, url)
                    log_error("请求频率过高(429)")
                # 智能调度系统更新
                if SCHEDULER_AVAILABLE:
                    adjust_crawl_strategy(False, response_time, "rate_limit")
                    # 使用智能调度系统的延迟
                    sleep_time = get_optimal_delay()
                else:
                    sleep_time = RETRY_DELAY_BASE * (attempt + 2)
                logger.info(f"等待 {sleep_time:.2f} 秒后重试")
                time.sleep(sleep_time)

            else:
                logger.warning(f"请求失败，状态码: {response.status_code}")
                if MONITOR_AVAILABLE:
                    log_request(False, url)
                    log_error(f"请求失败，状态码: {response.status_code}")
                # 智能调度系统更新
                if SCHEDULER_AVAILABLE:
                    adjust_crawl_strategy(False, response_time, "http_error")
                if attempt < retries - 1:
                    if SCHEDULER_AVAILABLE:
                        sleep_time = get_optimal_delay()
                    else:
                        sleep_time = RETRY_DELAY_BASE * (attempt + 1)
                    time.sleep(sleep_time)

        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            logger.warning(f"请求超时 (尝试 {attempt + 1}/{retries})")
            if MONITOR_AVAILABLE:
                log_request(False, url)
                log_error("请求超时")
            # 智能调度系统更新
            if SCHEDULER_AVAILABLE:
                adjust_crawl_strategy(False, response_time, "timeout")
            if attempt < retries - 1:
                if SCHEDULER_AVAILABLE:
                    sleep_time = get_optimal_delay()
                else:
                    sleep_time = RETRY_DELAY_BASE * (attempt + 1)
                time.sleep(sleep_time)

        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            logger.error(f"请求异常: {e}")
            if MONITOR_AVAILABLE:
                log_request(False, url)
                log_error(f"请求异常: {e}")
            # 智能调度系统更新
            if SCHEDULER_AVAILABLE:
                adjust_crawl_strategy(False, response_time, "request_error")
            if attempt < retries - 1:
                if SCHEDULER_AVAILABLE:
                    sleep_time = get_optimal_delay()
                else:
                    sleep_time = RETRY_DELAY_BASE * (attempt + 1)
                time.sleep(sleep_time)

    # 安全地记录 URL，隐藏可能的敏感参数
    safe_url = url[:100] + "..." if len(url) > 100 else url
    if "?" in safe_url:
        safe_url = safe_url.split("?")[0] + "?[params_hidden]"
    logger.error(f"请求最终失败: {safe_url}")
    if MONITOR_AVAILABLE:
        log_request(False, url)
        log_error(f"请求最终失败: {safe_url}")
    return None


def extract_topics(text: str) -> str:
    """提取话题标签 #xxx#"""
    if not text:
        return ""
    topics = re.findall(r"#([^#]+)#", text)
    return ",".join(topics) if topics else ""


def extract_at_users(text: str) -> str:
    """提取@提及的用户"""
    if not text:
        return ""
    at_users = re.findall(r"@([^\s:：,，]+)", text)
    return ",".join(at_users) if at_users else ""


def extract_pic_urls(article: Dict) -> str:
    """提取图片URL列表"""
    pic_urls = []

    # 方式1: pic_ids + pic_infos
    if "pic_infos" in article and article["pic_infos"]:
        for _pic_id, pic_info in article["pic_infos"].items():
            if "original" in pic_info:
                pic_urls.append(pic_info["original"].get("url", ""))
            elif "large" in pic_info:
                pic_urls.append(pic_info["large"].get("url", ""))

    # 方式2: pic_ids 直接拼接
    elif "pic_ids" in article and article["pic_ids"]:
        for pic_id in article["pic_ids"]:
            pic_urls.append(f"https://wx1.sinaimg.cn/large/{pic_id}.jpg")

    return "|".join(pic_urls) if pic_urls else ""


def extract_video_url(article: Dict) -> str:
    """提取视频URL"""
    try:
        page_info = article.get("page_info", {})
        if page_info and page_info.get("type") == "video":
            media_info = page_info.get("media_info", {})
            # 优先获取高清视频
            return (
                media_info.get("stream_url_hd")
                or media_info.get("stream_url")
                or media_info.get("mp4_hd_url")
                or media_info.get("mp4_sd_url")
                or ""
            )
    except Exception as e:
        logger.debug(f"提取视频URL失败: {e}")
    return ""


def parse_created_time(created_at: str) -> str:
    """
    解析微博时间格式

    Args:
        created_at: 原始时间字符串

    Returns:
        格式化后的时间字符串
    """
    if not created_at:
        return ""

    # 尝试多种时间格式
    time_formats = [
        "%a %b %d %H:%M:%S %z %Y",  # 标准格式: Mon Jan 01 12:00:00 +0800 2024
        "%Y-%m-%d %H:%M:%S",  # 简单格式
        "%Y-%m-%dT%H:%M:%S",  # ISO格式
    ]

    for fmt in time_formats:
        try:
            parsed = datetime.strptime(created_at, fmt)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

    # 所有格式都失败，返回原始值
    logger.warning(f"无法解析时间格式: {created_at}")
    return created_at


def parse_json(response: List[Dict], type_name: str) -> int:
    """
    解析微博JSON数据，提取完整字段

    Args:
        response: 微博数据列表
        type_name: 类型名称

    Returns:
        int: 成功处理的微博数量
    """
    processed_count = 0

    for article in response:
        try:
            article_id = str(article.get("id", ""))

            # 检查是否重复
            if article_deduplicator.is_duplicate(article_id):
                logger.debug(f"跳过重复文章: {article_id}")
                continue

            # === 基础字段 ===
            likeNum = article.get("attitudes_count", 0)
            commentsLen = article.get("comments_count", 0)
            reposts_count = article.get("reposts_count", 0)

            # IP属地
            region = article.get("region_name", "").replace("发布于 ", "") or "无"

            # 正文内容
            content = article.get("text_raw", "") or article.get("text", "")
            contentLen = article.get("textLength", len(content))

            # 是否长文本
            is_long_text = article.get("isLongText", False)

            # 发布时间（使用改进的解析函数）
            created_at = parse_created_time(article.get("created_at", ""))

            # 详情URL
            detailUrl = ""
            try:
                user_id = article.get("user", {}).get("id", "")
                mblogid = article.get("mblogid", "")
                if user_id and mblogid:
                    detailUrl = f"https://weibo.com/{user_id}/{mblogid}"
            except Exception as e:
                logger.debug(f"构建详情URL失败: {e}")

            # === 用户信息 ===
            user = article.get("user", {})
            authorAvatar = user.get("avatar_large", "") or user.get("avatar_hd", "")
            authorName = user.get("screen_name", "")
            authorDetail = "https://weibo.com" + user.get("profile_url", "")
            isVip = user.get("v_plus", 0) or user.get("mbrank", 0)

            # 用户认证信息
            verified_type = user.get("verified_type", -1)
            verified_reason = user.get("verified_reason", "")

            # 粉丝数和关注数
            followers_count = user.get("followers_count", 0)
            friends_count = user.get("friends_count", 0)

            # === 附加字段 ===
            source = article.get("source", "").replace("来自", "").strip()
            topics = extract_topics(content)
            at_users = extract_at_users(content)
            pic_urls = extract_pic_urls(article)
            video_url = extract_video_url(article)

            # === 转发信息 ===
            retweeted_id = ""
            retweeted_text = ""
            retweeted_user = ""
            retweeted_status = article.get("retweeted_status")
            if retweeted_status:
                retweeted_id = str(retweeted_status.get("id", ""))
                retweeted_text = retweeted_status.get(
                    "text_raw", ""
                ) or retweeted_status.get("text", "")
                retweeted_user_info = retweeted_status.get("user", {})
                retweeted_user = (
                    retweeted_user_info.get("screen_name", "")
                    if retweeted_user_info
                    else "[已删除]"
                )

            # 写入CSV
            success = writerRow(
                [
                    article_id,
                    likeNum,
                    commentsLen,
                    reposts_count,
                    region,
                    content,
                    contentLen,
                    created_at,
                    type_name,
                    detailUrl,
                    authorAvatar,
                    authorName,
                    authorDetail,
                    isVip,
                    source,
                    topics,
                    at_users,
                    pic_urls,
                    video_url,
                    is_long_text,
                    verified_type,
                    verified_reason,
                    followers_count,
                    friends_count,
                    retweeted_id,
                    retweeted_text,
                    retweeted_user,
                ]
            )

            if success:
                # 添加到去重过滤器
                article_deduplicator.add(article_id)
                processed_count += 1

        except Exception as e:
            logger.error(f"解析微博数据失败: {e}, ID: {article.get('id', 'unknown')}")

    return processed_count


def search_weibo(keyword: str, pageNum: int = 10) -> int:
    """
    根据关键词搜索微博

    Args:
        keyword: 搜索关键词
        pageNum: 爬取页数

    Returns:
        int: 成功处理的微博总数
    """
    search_url = "https://weibo.com/ajax/statuses/search"
    init()

    total_processed = 0
    logger.info(f"开始搜索关键词: {keyword}，计划爬取 {pageNum} 页")

    for page in range(1, pageNum + 1):
        # 使用智能调度系统获取延迟时间
        if SCHEDULER_AVAILABLE:
            delay = get_optimal_delay()
            logger.info(f"使用智能调度系统的延迟: {delay:.2f}秒")
        elif isinstance(DEFAULT_DELAY, tuple):
            delay = random.uniform(DEFAULT_DELAY[0], DEFAULT_DELAY[1])
        else:
            delay = DEFAULT_DELAY
        time.sleep(delay)

        logger.info(f"正在爬取关键词 [{keyword}] 的第 {page}/{pageNum} 页")

        params = {
            "q": keyword,
            "type": "all",
            "sub": "all",
            "timescope": "",
            "refer": "g",
            "page": page,
            "count": 25,
        }

        # 尝试使用浏览器模拟（基于智能调度系统的决策）
        response = None
        use_browser = False
        if SCHEDULER_AVAILABLE:
            use_browser = should_use_browser()
        else:
            use_browser = BROWSER_AVAILABLE

        if use_browser and BROWSER_AVAILABLE:
            logger.info("使用浏览器模拟获取搜索数据")
            try:
                # 构建完整URL
                full_url = search_url + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
                if navigate(full_url):
                    # 等待页面加载
                    if wait_for_selector("body", timeout=10000):
                        # 滚动页面以加载更多数据
                        for _ in range(3):
                            scroll(500)
                            time.sleep(1)
                        # 获取页面内容
                        content = get_content()
                        if content:
                            # 尝试从HTML中提取JSON数据
                            import re
                            json_match = re.search(r'\{"ok":1,"data":.*?\}\s*<\/script>', content, re.DOTALL)
                            if json_match:
                                json_str = json_match.group(0).replace('</script>', '')
                                try:
                                    import json
                                    response = json.loads(json_str)
                                    logger.info("从浏览器模拟中成功提取搜索JSON数据")
                                    # 智能调度系统更新
                                    if SCHEDULER_AVAILABLE:
                                        adjust_crawl_strategy(True, 0)
                                except json.JSONDecodeError:
                                    logger.warning("浏览器模拟提取JSON失败，回退到API方式")
                                    response = get_json(search_url, params)
                            else:
                                logger.warning("未找到JSON数据，回退到API方式")
                                response = get_json(search_url, params)
                        else:
                            logger.warning("浏览器内容为空，回退到API方式")
                            response = get_json(search_url, params)
                    else:
                        logger.warning("页面加载超时，回退到API方式")
                        response = get_json(search_url, params)
                else:
                    logger.warning("浏览器导航失败，回退到API方式")
                    response = get_json(search_url, params)
            except Exception as e:
                logger.error(f"浏览器模拟失败: {e}")
                # 回退到传统API方式
                response = get_json(search_url, params)
                # 智能调度系统更新
                if SCHEDULER_AVAILABLE:
                    adjust_crawl_strategy(False, 0, "browser_error")
        else:
            # 使用传统API方式
            response = get_json(search_url, params)

        if response is None:
            logger.warning(f"请求失败，跳过第 {page} 页")
            continue

        if "data" not in response or "list" not in response["data"]:
            logger.warning(f"响应格式异常，跳过第 {page} 页")
            continue

        statuses = response["data"]["list"]

        # 过滤掉非微博内容
        valid_statuses = [s for s in statuses if "text_raw" in s or "text" in s]

        if valid_statuses:
            count = parse_json(valid_statuses, f"搜索:{keyword}")
            total_processed += count
            logger.info(f"第 {page} 页处理完成，新增 {count} 条微博")
        else:
            logger.info(f"第 {page} 页未找到有效微博数据")

        # 检查是否还有更多数据
        if len(valid_statuses) < 10:
            logger.info("数据量不足，可能已到末尾")
            break

    logger.info(f"搜索完成，共处理 {total_processed} 条微博")
    return total_processed


def start(
    typeNum: int = 10,
    pageNum: int = 5,
    mode: str = "category",
    keyword: Optional[str] = None,
) -> int:
    """
    启动爬虫

    Args:
        typeNum: 爬取的类型数量
        pageNum: 每个类型的爬取页数
        mode: 'category' (分类) or 'search' (关键词搜索)
        keyword: 搜索关键词

    Returns:
        int: 成功处理的微博总数
    """
    if mode == "search":
        if not keyword:
            logger.error("搜索模式必须提供关键词！")
            return 0
        return search_weibo(keyword, pageNum)

    # 分类爬取模式
    articleUrl = "https://weibo.com/ajax/feed/hottimeline"
    init()

    total_processed = 0
    typeNumCount = 0
    base_dir = os.path.dirname(os.path.dirname(__file__))
    nav_path = os.path.join(base_dir, "data", "navData.csv")

    # 内置导航数据（当导航文件不存在时使用）
    default_nav_data = [
        ["推荐", "102803", "102803"],
        ["热搜", "102803", "102803&page_type=searchtab"],
        ["娱乐", "102803", "102803&category=entertainment"],
        ["体育", "102803", "102803&category=sports"],
        ["财经", "102803", "102803&category=finance"],
        ["科技", "102803", "102803&category=technology"],
        ["教育", "102803", "102803&category=education"],
        ["健康", "102803", "102803&category=health"],
        ["汽车", "102803", "102803&category=auto"],
        ["旅游", "102803", "102803&category=travel"],
    ]

    nav_data = []

    # 尝试从文件加载导航数据
    if os.path.exists(nav_path):
        try:
            with open(nav_path, encoding="utf8") as readerFile:
                reader = csv.reader(readerFile)
                try:
                    next(reader)  # 跳过标题行
                except StopIteration:
                    logger.warning("导航文件为空，使用默认导航数据")
                    nav_data = default_nav_data
                else:
                    for nav in reader:
                        if len(nav) >= 3:
                            nav_data.append(nav)
                        else:
                            logger.warning(f"跳过无效导航行: {nav}")
                    if not nav_data:
                        logger.warning("导航文件无有效数据，使用默认导航数据")
                        nav_data = default_nav_data
        except Exception as e:
            logger.error(f"读取导航文件失败: {e}")
            nav_data = default_nav_data
    else:
        logger.warning(f"导航文件不存在: {nav_path}，使用默认导航数据")
        nav_data = default_nav_data

    # 限制导航数据数量
    nav_data = nav_data[:typeNum]

    try:
        for nav in nav_data:
            if typeNumCount >= typeNum:
                break

            if len(nav) < 3:
                logger.warning(f"跳过无效导航行: {nav}")
                continue

            for page in range(pageNum):
                # 使用智能调度系统获取延迟时间
                if SCHEDULER_AVAILABLE:
                    delay = get_optimal_delay()
                    logger.info(f"使用智能调度系统的延迟: {delay:.2f}秒")
                elif isinstance(DEFAULT_DELAY, tuple):
                    delay = random.uniform(DEFAULT_DELAY[0], DEFAULT_DELAY[1])
                else:
                    delay = DEFAULT_DELAY
                time.sleep(delay)

                logger.info(f"正在爬取类型：{nav[0]} 第 {page + 1}/{pageNum} 页")

                params = {
                    "group_id": nav[1],
                    "containerid": nav[2],
                    "max_id": page,
                    "count": 25,
                    "extparam": "discover|new_feed",
                }

                if page == 0:
                    params["since_id"] = "0"
                    params["refresh"] = "0"
                else:
                    params["refresh"] = "2"

                # 尝试使用浏览器模拟（基于智能调度系统的决策）
                use_browser = False
                if SCHEDULER_AVAILABLE:
                    use_browser = should_use_browser()
                else:
                    use_browser = BROWSER_AVAILABLE

                if use_browser and BROWSER_AVAILABLE:
                    logger.info("使用浏览器模拟获取数据")
                    try:
                        # 构建完整URL
                        full_url = articleUrl + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
                        if navigate(full_url):
                            # 等待页面加载
                            if wait_for_selector("body", timeout=10000):
                                # 滚动页面以加载更多数据
                                for _ in range(3):
                                    scroll(500)
                                    time.sleep(1)
                                # 获取页面内容
                                content = get_content()
                                if content:
                                    # 尝试从HTML中提取JSON数据
                                    import re
                                    json_match = re.search(r'\{"ok":1,"data":.*?\}\s*<\/script>', content, re.DOTALL)
                                    if json_match:
                                        json_str = json_match.group(0).replace('</script>', '')
                                        try:
                                            import json
                                            response = json.loads(json_str)
                                            logger.info("从浏览器模拟中成功提取JSON数据")
                                            # 智能调度系统更新
                                            if SCHEDULER_AVAILABLE:
                                                adjust_crawl_strategy(True, 0)
                                        except json.JSONDecodeError:
                                            logger.warning("浏览器模拟提取JSON失败，回退到API方式")
                                            response = get_json(articleUrl, params)
                                    else:
                                        logger.warning("未找到JSON数据，回退到API方式")
                                        response = get_json(articleUrl, params)
                                else:
                                    logger.warning("浏览器内容为空，回退到API方式")
                                    response = get_json(articleUrl, params)
                            else:
                                logger.warning("页面加载超时，回退到API方式")
                                response = get_json(articleUrl, params)
                        else:
                            logger.warning("浏览器导航失败，回退到API方式")
                            response = get_json(articleUrl, params)
                    except Exception as e:
                        logger.error(f"浏览器模拟失败: {e}")
                        # 回退到传统API方式
                        response = get_json(articleUrl, params)
                        # 智能调度系统更新
                        if SCHEDULER_AVAILABLE:
                            adjust_crawl_strategy(False, 0, "browser_error")
                else:
                    # 使用传统API方式
                    response = get_json(articleUrl, params)

                if response is None:
                    logger.warning(f"请求失败，跳过类型：{nav[0]} 第{page + 1}页")
                    continue

                if "statuses" not in response:
                    logger.warning(
                        f"响应格式异常，跳过类型：{nav[0]} 第{page + 1}页"
                    )
                    continue

                count = parse_json(response["statuses"], nav[0])
                total_processed += count

            typeNumCount += 1

    except Exception as e:
        logger.error(f"爬取过程发生错误: {e}", exc_info=True)

    # 保存去重状态
    article_deduplicator.save()

    logger.info(f"分类爬取完成，共处理 {total_processed} 条微博")
    return total_processed


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    start(typeNum=2, pageNum=1)
