import csv
import logging
import os
import random
import re
import time

import requests
from jsonpath import jsonpath

from config import (
    DEFAULT_DELAY,
    DEFAULT_TIMEOUT,
    get_random_headers,
    get_working_proxy,
)

logger = logging.getLogger(__name__)


def _extract_uid_from_url(detail_url):
    """从微博详情URL中提取用户ID"""
    if not detail_url or "weibo.com" not in detail_url:
        return None
    parts = detail_url.replace("https://weibo.com/", "").split("/")
    return parts[0] if parts else None


def _read_csv_rows(file_path):
    """读取CSV文件，返回所有数据行（跳过标题）"""
    with open(file_path, encoding="utf8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # 跳过标题行
        return list(reader)


def _extract_friend_count(friend_info_text):
    """从好友信息文本中提取好友数量"""
    if not friend_info_text:
        return 0
    try:
        friend_match = re.findall(
            r"有\s<a>(\d+)</a>\s个好友", friend_info_text
        )
    except (re.error, TypeError):
        return 0
    return int(friend_match[0]) if friend_match else 0


def _jsonpath_extract_first(response, path):
    """用jsonpath提取字段，返回第一个匹配值或空字符串"""
    result = jsonpath(response, path)
    return result[0] if result else ""


class UserInfoSpider:
    """用户信息爬取类 - 基于博客技术优化"""

    def __init__(self):
        self.profile_detail_url = "https://weibo.com/ajax/profile/detail"
        self.profile_info_url = "https://weibo.com/ajax/profile/info"
        self.user_ids = set()  # 存储已收集的用户ID

    def init_user_csv(self):
        """初始化用户信息CSV文件"""
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(data_dir, exist_ok=True)
        user_info_path = os.path.join(data_dir, "userInfo.csv")

        if not os.path.exists(user_info_path):
            with open(user_info_path, "w", encoding="utf8", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    [
                        "user_id",  # 用户ID
                        "user_name",  # 用户名
                        "user_time",  # 账号创建时间
                        "user_gender",  # 用户性别
                        "user_description",  # 用户描述/格言
                        "user_level",  # 用户信用等级
                        "media_num",  # 视频播放量
                        "friend_info",  # 好友信息
                        "user_likes",  # 用户获赞数
                        "user_ips",  # 用户IP地址
                        "followers_count",  # 粉丝数
                        "follow_count",  # 关注数
                        "status_count",  # 微博数
                        "avatar_url",  # 头像URL
                        "verified",  # 是否认证
                        "verified_type",  # 认证类型
                    ]
                )

    def write_user_row(self, row):
        """写入用户数据到CSV（线程安全）"""
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        user_info_path = os.path.join(data_dir, "userInfo.csv")

        try:
            with open(user_info_path, "a", encoding="utf8", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(row)
            return True
        except OSError as e:
            logger.error("写入用户数据失败: %s", e)
            return False

    def get_user_detail(self, uid):
        """获取用户详细信息 - profile/detail API"""
        headers = get_random_headers()
        headers["Referer"] = f"https://weibo.com/u/{uid}?tabtype=feed"
        proxy = get_working_proxy()

        try:
            response = requests.get(
                self.profile_detail_url,
                headers=headers,
                params={"uid": uid},
                proxies=proxy,
                timeout=DEFAULT_TIMEOUT,
            )

            if response.status_code == 200:
                return response.json()
            logger.warning("获取用户 %s 详细信息失败，状态码: %s", uid, response.status_code)
            return None

        except requests.RequestException as e:
            logger.error("请求用户 %s 详细信息异常: %s", uid, e)
            return None

    def get_user_info(self, uid):
        """获取用户基本信息 - profile/info API"""
        headers = get_random_headers()
        headers["Referer"] = f"https://weibo.com/u/{uid}?tabtype=feed"
        proxy = get_working_proxy()

        try:
            response = requests.get(
                self.profile_info_url,
                headers=headers,
                params={"uid": uid},
                proxies=proxy,
                timeout=DEFAULT_TIMEOUT,
            )

            if response.status_code == 200:
                return response.json()
            logger.warning("获取用户 %s 基本信息失败，状态码: %s", uid, response.status_code)
            return None

        except requests.RequestException as e:
            logger.error("请求用户 %s 基本信息异常: %s", uid, e)
            return None

    def _extract_detail_fields(self, response):
        """从用户详细信息响应中提取所有字段"""
        fields = {
            "user_ips": "$..ip_location",
            "user_time": "$..created_at",
            "user_gender": "$..gender",
            "user_description": "$..description",
            "user_level": "$..sunshine_credit.level",
            "media_num": "$..label_desc[0].name",
            "friend_info": "$..friend_info",
        }
        extracted = {
            key: _jsonpath_extract_first(response, path)
            for key, path in fields.items()
        }
        extracted["friend_info"] = _extract_friend_count(extracted.get("friend_info"))
        return extracted

    def parse_user_detail(self, response):
        """解析用户详细信息"""
        if not response or response.get("ok") != 1:
            logger.warning("用户详细信息响应异常")
            return {}

        try:
            return self._extract_detail_fields(response)
        except (KeyError, ValueError, TypeError) as e:
            logger.error("解析用户详细信息失败: %s", e)
            return {}

    def parse_user_info(self, response):
        """解析用户基本信息"""
        if not response or response.get("ok") != 1:
            logger.warning("用户基本信息响应异常")
            return {}

        try:
            data = response.get("data", {})
            user_info = data.get("user", {})

            return {
                "user_name": user_info.get("screen_name", ""),
                "followers_count": user_info.get("followers_count_str", ""),
                "follow_count": user_info.get("follow_count", 0),
                "status_count": user_info.get("statuses_count", 0),
                "avatar_url": user_info.get("avatar_large", ""),
                "verified": user_info.get("verified", False),
                "verified_type": user_info.get("verified_type", -1),
            }

        except (KeyError, TypeError) as e:
            logger.error("解析用户基本信息失败: %s", e)
            return {}

    def _build_user_row(self, uid, detail_data, info_data):
        """将详细信息和基本信息合并为CSV行"""
        user_data = {
            "user_id": uid,
            "user_name": info_data.get("user_name", ""),
            "user_time": detail_data.get("user_time", ""),
            "user_gender": detail_data.get("user_gender", ""),
            "user_description": detail_data.get("user_description", ""),
            "user_level": detail_data.get("user_level", ""),
            "media_num": detail_data.get("media_num", ""),
            "friend_info": detail_data.get("friend_info", ""),
            "user_likes": 0,  # 这个字段在API中不太明确，暂设为0
            "user_ips": detail_data.get("user_ips", ""),
            "followers_count": info_data.get("followers_count", ""),
            "follow_count": info_data.get("follow_count", 0),
            "status_count": info_data.get("status_count", 0),
            "avatar_url": info_data.get("avatar_url", ""),
            "verified": info_data.get("verified", False),
            "verified_type": info_data.get("verified_type", -1),
        }
        return [user_data[key] for key in [
            "user_id", "user_name", "user_time", "user_gender",
            "user_description", "user_level", "media_num", "friend_info",
            "user_likes", "user_ips", "followers_count", "follow_count",
            "status_count", "avatar_url", "verified", "verified_type",
        ]]

    def crawl_user_info(self, uid):
        """爬取单个用户的完整信息"""
        try:
            logger.info("正在爬取用户 %s 的信息...", uid)

            # 延时控制
            if isinstance(DEFAULT_DELAY, tuple):
                delay = random.uniform(DEFAULT_DELAY[0], DEFAULT_DELAY[1])
            else:
                delay = DEFAULT_DELAY
            time.sleep(delay)

            # 获取详细信息
            detail_response = self.get_user_detail(uid)
            detail_data = self.parse_user_detail(detail_response)

            # 获取基本信息
            info_response = self.get_user_info(uid)
            info_data = self.parse_user_info(info_response)

            # 合并数据并写入CSV
            row = self._build_user_row(uid, detail_data, info_data)
            self.write_user_row(row)

            logger.info("用户 %s 信息爬取完成", uid)
            return True

        except (requests.RequestException, OSError, KeyError, ValueError) as e:
            logger.error("爬取用户 %s 信息失败: %s", uid, e)
            return False

    def _collect_ids_from_articles(self, article_path):
        """从文章CSV中提取用户ID"""
        if not os.path.exists(article_path):
            return
        try:
            rows = _read_csv_rows(article_path)
        except OSError as e:
            logger.warning("读取文章CSV失败: %s", e)
            return

        for row in rows:
            if len(row) <= 9 or not row[9]:
                continue
            uid = _extract_uid_from_url(row[9])
            if uid:
                self.user_ids.add(uid)

    def _collect_ids_from_comments(self, comments_path):
        """从评论CSV中提取用户ID"""
        if not os.path.exists(comments_path):
            return
        try:
            rows = _read_csv_rows(comments_path)
        except OSError as e:
            logger.warning("读取评论CSV失败: %s", e)
            return

        for row in rows:
            if len(row) <= 10:
                continue
            user_id = row[10]
            if user_id and user_id.isdigit():
                self.user_ids.add(user_id)

    def collect_user_ids_from_csv(self):
        """从现有CSV文件中收集用户ID"""
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

        self._collect_ids_from_articles(
            os.path.join(data_dir, "articleData.csv")
        )
        self._collect_ids_from_comments(
            os.path.join(data_dir, "commentsData.csv")
        )

        logger.info("收集到 %d 个唯一用户ID", len(self.user_ids))
        return list(self.user_ids)

    def start_user_crawl(self, max_users=100):
        """开始爬取用户信息"""
        self.init_user_csv()
        user_ids = self.collect_user_ids_from_csv()

        if not user_ids:
            logger.warning("没有找到可爬取的用户ID")
            return

        logger.info("开始爬取用户信息，共 %d 个用户...", len(user_ids))

        crawled_count = 0
        for uid in user_ids:
            if crawled_count >= max_users:
                break

            success = self.crawl_user_info(uid)
            if success:
                crawled_count += 1

        logger.info("用户信息爬取完成，共爬取 %d 个用户", crawled_count)


def start_user_spider(max_users=50):
    """启动用户信息爬虫"""
    spider = UserInfoSpider()
    spider.start_user_crawl(max_users)


if __name__ == "__main__":
    start_user_spider()
