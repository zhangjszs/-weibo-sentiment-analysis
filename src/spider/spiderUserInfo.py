import csv
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
        except Exception as e:
            print(f"写入用户数据失败: {e}")
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
            else:
                print(f"获取用户 {uid} 详细信息失败，状态码: {response.status_code}")
                return None

        except Exception as e:
            print(f"请求用户 {uid} 详细信息异常: {e}")
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
            else:
                print(f"获取用户 {uid} 基本信息失败，状态码: {response.status_code}")
                return None

        except Exception as e:
            print(f"请求用户 {uid} 基本信息异常: {e}")
            return None

    def parse_user_detail(self, response):
        """解析用户详细信息"""
        if not response or response.get("ok") != 1:
            print("用户详细信息响应异常")
            return {}

        try:
            # 使用jsonpath提取字段
            fields = {
                "user_ips": "$..ip_location",
                "user_time": "$..created_at",
                "user_gender": "$..gender",
                "user_description": "$..description",
                "user_level": "$..sunshine_credit.level",
                "media_num": "$..label_desc[0].name",
                "friend_info": "$..friend_info",
            }

            # 批量提取字段
            extracted_data = {
                key: jsonpath(response, path) for key, path in fields.items()
            }

            # 处理 False 返回值，统一转换
            extracted_data = {
                key: value[0] if value else ""
                for key, value in extracted_data.items()
            }

            # 处理好友信息
            if extracted_data.get("friend_info"):
                try:
                    friend_match = re.findall(
                        r"有\s<a>(\d+)</a>\s个好友", extracted_data["friend_info"]
                    )
                    if friend_match:
                        extracted_data["friend_info"] = int(friend_match[0])
                    else:
                        extracted_data["friend_info"] = 0
                except Exception:
                    extracted_data["friend_info"] = 0

            return extracted_data

        except Exception as e:
            print(f"解析用户详细信息失败: {e}")
            return {}

    def parse_user_info(self, response):
        """解析用户基本信息"""
        if not response or response.get("ok") != 1:
            print("用户基本信息响应异常")
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

        except Exception as e:
            print(f"解析用户基本信息失败: {e}")
            return {}

    def crawl_user_info(self, uid):
        """爬取单个用户的完整信息"""
        try:
            print(f"正在爬取用户 {uid} 的信息...")

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

            # 合并数据
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

            # 写入CSV
            self.write_user_row(
                [
                    user_data["user_id"],
                    user_data["user_name"],
                    user_data["user_time"],
                    user_data["user_gender"],
                    user_data["user_description"],
                    user_data["user_level"],
                    user_data["media_num"],
                    user_data["friend_info"],
                    user_data["user_likes"],
                    user_data["user_ips"],
                    user_data["followers_count"],
                    user_data["follow_count"],
                    user_data["status_count"],
                    user_data["avatar_url"],
                    user_data["verified"],
                    user_data["verified_type"],
                ]
            )

            print(f"用户 {uid} 信息爬取完成")
            return True

        except Exception as e:
            print(f"爬取用户 {uid} 信息失败: {e}")
            return False

    def collect_user_ids_from_csv(self):
        """从现有CSV文件中收集用户ID"""
        # 从文章数据中收集用户ID
        article_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "articleData.csv"
        )
        if os.path.exists(article_path):
            with open(article_path, encoding="utf8") as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # 跳过标题行
                for row in reader:
                    if len(row) > 11:  # authorName在第12列
                        # 从detailUrl中提取用户ID
                        if len(row) > 9 and row[9]:  # detailUrl
                            try:
                                detail_url = row[9]
                                if "weibo.com" in detail_url:
                                    parts = detail_url.replace(
                                        "https://weibo.com/", ""
                                    ).split("/")
                                    if len(parts) >= 1:
                                        self.user_ids.add(parts[0])
                            except Exception:
                                continue
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        comments_path = os.path.join(data_dir, "commentsData.csv")

        if os.path.exists(comments_path):
            with open(comments_path, encoding="utf8") as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # 跳过标题行
                for row in reader:
                    if len(row) > 10:  # user_id在第11列
                        user_id = row[10]
                        if user_id and user_id.isdigit():
                            self.user_ids.add(user_id)

        print(f"收集到 {len(self.user_ids)} 个唯一用户ID")
        return list(self.user_ids)

    def start_user_crawl(self, max_users=100):
        """开始爬取用户信息"""
        self.init_user_csv()
        user_ids = self.collect_user_ids_from_csv()

        if not user_ids:
            print("没有找到可爬取的用户ID")
            return

        print(f"开始爬取用户信息，共 {len(user_ids)} 个用户...")

        crawled_count = 0
        for uid in user_ids:
            if crawled_count >= max_users:
                break

            success = self.crawl_user_info(uid)
            if success:
                crawled_count += 1

        print(f"用户信息爬取完成，共爬取 {crawled_count} 个用户")


def start_user_spider(max_users=50):
    """启动用户信息爬虫"""
    spider = UserInfoSpider()
    spider.start_user_crawl(max_users)


if __name__ == "__main__":
    start_user_spider()
