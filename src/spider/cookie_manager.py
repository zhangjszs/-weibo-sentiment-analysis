#!/usr/bin/env python3
"""
微博Cookie管理模块
功能：自动登录微博并管理Cookie
特性：使用Playwright模拟浏览器登录，支持Cookie持久化
"""

import json
import logging
import os
import time
from typing import Dict, Optional

from playwright.sync_api import sync_playwright

logger = logging.getLogger("spider.cookie")


class CookieManager:
    """
    Cookie管理器
    负责微博自动登录和Cookie管理
    """

    def __init__(self, cookie_file: str = "spider/cookies.json"):
        """
        初始化Cookie管理器

        Args:
            cookie_file: Cookie文件路径
        """
        self.cookie_file = cookie_file
        self.cookies = {}
        self._load_cookies()

    def _load_cookies(self):
        """
        从文件加载Cookie
        """
        try:
            if os.path.exists(self.cookie_file):
                with open(self.cookie_file, "r", encoding="utf-8") as f:
                    self.cookies = json.load(f)
                logger.info(f"从文件加载Cookie: {len(self.cookies)} 条")
            else:
                logger.info("Cookie文件不存在，将在登录后创建")
        except Exception as e:
            logger.error(f"加载Cookie失败: {e}")
            self.cookies = {}

    def _save_cookies(self):
        """
        保存Cookie到文件
        """
        try:
            # 创建目录（如果不存在）
            cookie_dir = os.path.dirname(self.cookie_file)
            if cookie_dir and not os.path.exists(cookie_dir):
                os.makedirs(cookie_dir)

            with open(self.cookie_file, "w", encoding="utf-8") as f:
                json.dump(self.cookies, f, indent=2, ensure_ascii=False)
            logger.info(f"Cookie已保存到文件: {self.cookie_file}")
        except Exception as e:
            logger.error(f"保存Cookie失败: {e}")

    def get_cookie_string(self) -> str:
        """
        获取Cookie字符串

        Returns:
            str: Cookie字符串
        """
        cookie_pairs = []
        for name, value in self.cookies.items():
            cookie_pairs.append(f"{name}={value}")
        return "; ".join(cookie_pairs)

    def is_cookie_valid(self) -> bool:
        """
        检查Cookie是否有效

        Returns:
            bool: Cookie是否有效
        """
        if not self.cookies:
            return False

        # 检查关键Cookie是否存在
        required_cookies = ["SUB", "SUBP", "ALF", "SSOLoginState"]
        for cookie_name in required_cookies:
            if cookie_name not in self.cookies:
                logger.warning(f"缺少关键Cookie: {cookie_name}")
                return False

        # 检查ALF（过期时间）
        if "ALF" in self.cookies:
            try:
                alf = int(self.cookies["ALF"])
                if time.time() > alf:
                    logger.warning("Cookie已过期")
                    return False
            except ValueError:
                logger.warning("ALF格式错误")
                return False

        return True

    def login(self, username: str, password: str) -> bool:
        """
        自动登录微博

        Args:
            username: 微博用户名
            password: 微博密码

        Returns:
            bool: 登录是否成功
        """
        logger.info("开始自动登录微博...")

        try:
            with sync_playwright() as p:
                # 启动浏览器
                browser = p.chromium.launch(
                    headless=False,  # 非无头模式，便于调试
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox"
                    ]
                )
                context = browser.new_context()

                # 清除webdriver标志
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => false,
                    });
                """)

                page = context.new_page()

                # 访问微博登录页
                page.goto("https://weibo.com/login.php")
                page.wait_for_load_state("networkidle")

                # 等待登录表单加载
                page.wait_for_selector("#loginname", timeout=30000)

                # 输入用户名
                page.fill("#loginname", username)
                time.sleep(1)

                # 输入密码
                page.fill("#pl_login_form > div > div:nth-child(3) > div.info_list.password > div > input", password)
                time.sleep(1)

                # 点击登录按钮
                page.click("#pl_login_form > div > div:nth-child(3) > div.info_list.login_btn > a")
                time.sleep(5)

                # 检查是否登录成功
                try:
                    # 等待登录成功后的页面元素
                    page.wait_for_selector(".gn_name", timeout=30000)
                    logger.info("登录成功！")

                    # 获取Cookie
                    cookies = context.cookies()
                    for cookie in cookies:
                        if cookie["name"] and cookie["value"]:
                            self.cookies[cookie["name"]] = cookie["value"]

                    # 保存Cookie
                    self._save_cookies()
                    logger.info(f"获取到 {len(self.cookies)} 条Cookie")

                    browser.close()
                    return True
                except Exception as e:
                    logger.error(f"登录失败: {e}")
                    # 截图保存错误信息
                    screenshot_path = "login_error.png"
                    page.screenshot(path=screenshot_path)
                    logger.info(f"登录错误截图已保存到: {screenshot_path}")
                    browser.close()
                    return False

        except Exception as e:
            logger.error(f"登录过程异常: {e}")
            return False

    def refresh_cookies(self, username: str, password: str) -> bool:
        """
        刷新Cookie

        Args:
            username: 微博用户名
            password: 微博密码

        Returns:
            bool: 刷新是否成功
        """
        logger.info("刷新Cookie...")
        return self.login(username, password)

    def update_cookies(self, new_cookies: Dict[str, str]):
        """
        更新Cookie

        Args:
            new_cookies: 新的Cookie字典
        """
        self.cookies.update(new_cookies)
        self._save_cookies()
        logger.info(f"Cookie已更新，当前共 {len(self.cookies)} 条")

    def clear_cookies(self):
        """
        清除所有Cookie
        """
        self.cookies = {}
        if os.path.exists(self.cookie_file):
            os.remove(self.cookie_file)
        logger.info("Cookie已清除")


# 全局Cookie管理器实例
_cookie_manager = None


def get_cookie_manager() -> CookieManager:
    """
    获取全局Cookie管理器实例

    Returns:
        CookieManager: Cookie管理器实例
    """
    global _cookie_manager
    if _cookie_manager is None:
        _cookie_manager = CookieManager()
    return _cookie_manager


def get_cookie_string() -> str:
    """
    获取Cookie字符串

    Returns:
        str: Cookie字符串
    """
    return get_cookie_manager().get_cookie_string()


def is_cookie_valid() -> bool:
    """
    检查Cookie是否有效

    Returns:
        bool: Cookie是否有效
    """
    return get_cookie_manager().is_cookie_valid()


def login(username: str, password: str) -> bool:
    """
    自动登录微博

    Args:
        username: 微博用户名
        password: 微博密码

    Returns:
        bool: 登录是否成功
    """
    return get_cookie_manager().login(username, password)


def refresh_cookies(username: str, password: str) -> bool:
    """
    刷新Cookie

    Args:
        username: 微博用户名
        password: 微博密码

    Returns:
        bool: 刷新是否成功
    """
    return get_cookie_manager().refresh_cookies(username, password)
