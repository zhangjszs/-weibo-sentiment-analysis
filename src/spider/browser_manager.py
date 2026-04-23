#!/usr/bin/env python3
"""
微博浏览器管理模块
功能：使用Playwright实现浏览器模拟
特性：支持无头浏览器、行为模拟、动态内容加载
"""

import logging
import time
from typing import Optional, Dict, Any

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

logger = logging.getLogger("spider.browser")


class BrowserManager:
    """
    浏览器管理器
    负责Playwright浏览器的初始化和管理
    """

    def __init__(self, headless: bool = True):
        """
        初始化浏览器管理器

        Args:
            headless: 是否使用无头模式
        """
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._initialize_browser()

    def _initialize_browser(self):
        """
        初始化浏览器
        """
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-extensions",
                    "--disable-gpu",
                    "--window-size=1920,1080"
                ],
                slow_mo=100  # 模拟人类操作速度
            )
            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            # 清除webdriver标志
            self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en-US', 'en'],
                });
                Object.defineProperty(navigator, 'userAgent', {
                    get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                });
            """)
            self.page = self.context.new_page()
            logger.info("浏览器初始化成功")
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            self._cleanup()

    def _cleanup(self):
        """
        清理浏览器资源
        """
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.error(f"清理浏览器资源失败: {e}")
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

    def get_page(self) -> Optional[Page]:
        """
        获取浏览器页面

        Returns:
            Page: 浏览器页面对象
        """
        if not self.page:
            self._initialize_browser()
        return self.page

    def navigate(self, url: str, wait_until: str = "networkidle") -> bool:
        """
        导航到指定URL

        Args:
            url: 目标URL
            wait_until: 等待条件

        Returns:
            bool: 导航是否成功
        """
        try:
            page = self.get_page()
            if not page:
                return False
            page.goto(url, wait_until=wait_until)
            logger.info(f"成功导航到: {url}")
            return True
        except Exception as e:
            logger.error(f"导航失败: {e}")
            return False

    def get_content(self) -> Optional[str]:
        """
        获取页面内容

        Returns:
            str: 页面HTML内容
        """
        try:
            page = self.get_page()
            if not page:
                return None
            return page.content()
        except Exception as e:
            logger.error(f"获取页面内容失败: {e}")
            return None

    def get_text(self, selector: str) -> Optional[str]:
        """
        获取指定选择器的文本

        Args:
            selector: CSS选择器

        Returns:
            str: 文本内容
        """
        try:
            page = self.get_page()
            if not page:
                return None
            element = page.query_selector(selector)
            if element:
                return element.text_content()
            return None
        except Exception as e:
            logger.error(f"获取文本失败: {e}")
            return None

    def click(self, selector: str) -> bool:
        """
        点击指定元素

        Args:
            selector: CSS选择器

        Returns:
            bool: 点击是否成功
        """
        try:
            page = self.get_page()
            if not page:
                return False
            page.click(selector)
            # 模拟人类点击后的延迟
            time.sleep(0.5)
            logger.info(f"成功点击元素: {selector}")
            return True
        except Exception as e:
            logger.error(f"点击失败: {e}")
            return False

    def fill(self, selector: str, text: str) -> bool:
        """
        填充文本到指定元素

        Args:
            selector: CSS选择器
            text: 要填充的文本

        Returns:
            bool: 填充是否成功
        """
        try:
            page = self.get_page()
            if not page:
                return False
            page.fill(selector, text)
            # 模拟人类输入的延迟
            time.sleep(0.1 * len(text))
            logger.info(f"成功填充文本到元素: {selector}")
            return True
        except Exception as e:
            logger.error(f"填充文本失败: {e}")
            return False

    def scroll(self, distance: int = 500) -> bool:
        """
        滚动页面

        Args:
            distance: 滚动距离

        Returns:
            bool: 滚动是否成功
        """
        try:
            page = self.get_page()
            if not page:
                return False
            page.mouse.wheel(0, distance)
            # 模拟人类滚动后的延迟
            time.sleep(0.3)
            logger.info(f"成功滚动页面 {distance} 像素")
            return True
        except Exception as e:
            logger.error(f"滚动失败: {e}")
            return False

    def wait_for_selector(self, selector: str, timeout: int = 30000) -> bool:
        """
        等待指定选择器出现

        Args:
            selector: CSS选择器
            timeout: 超时时间

        Returns:
            bool: 是否成功等待到选择器
        """
        try:
            page = self.get_page()
            if not page:
                return False
            page.wait_for_selector(selector, timeout=timeout)
            logger.info(f"成功等待到选择器: {selector}")
            return True
        except Exception as e:
            logger.error(f"等待选择器失败: {e}")
            return False

    def screenshot(self, path: str) -> bool:
        """
        截图

        Args:
            path: 截图保存路径

        Returns:
            bool: 截图是否成功
        """
        try:
            page = self.get_page()
            if not page:
                return False
            page.screenshot(path=path)
            logger.info(f"成功截图到: {path}")
            return True
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return False

    def execute_script(self, script: str) -> Any:
        """
        执行JavaScript

        Args:
            script: JavaScript代码

        Returns:
            Any: 执行结果
        """
        try:
            page = self.get_page()
            if not page:
                return None
            result = page.evaluate(script)
            logger.info("成功执行JavaScript")
            return result
        except Exception as e:
            logger.error(f"执行JavaScript失败: {e}")
            return None

    def close(self):
        """
        关闭浏览器
        """
        self._cleanup()
        logger.info("浏览器已关闭")


# 全局浏览器管理器实例
_browser_manager = None


def get_browser_manager(headless: bool = True) -> BrowserManager:
    """
    获取全局浏览器管理器实例

    Args:
        headless: 是否使用无头模式

    Returns:
        BrowserManager: 浏览器管理器实例
    """
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager(headless=headless)
    return _browser_manager


def get_page() -> Optional[Page]:
    """
    获取浏览器页面

    Returns:
        Page: 浏览器页面对象
    """
    return get_browser_manager().get_page()


def navigate(url: str, wait_until: str = "networkidle") -> bool:
    """
    导航到指定URL

    Args:
        url: 目标URL
        wait_until: 等待条件

    Returns:
        bool: 导航是否成功
    """
    return get_browser_manager().navigate(url, wait_until)


def get_content() -> Optional[str]:
    """
    获取页面内容

    Returns:
        str: 页面HTML内容
    """
    return get_browser_manager().get_content()


def click(selector: str) -> bool:
    """
    点击指定元素

    Args:
        selector: CSS选择器

    Returns:
        bool: 点击是否成功
    """
    return get_browser_manager().click(selector)


def fill(selector: str, text: str) -> bool:
    """
    填充文本到指定元素

    Args:
        selector: CSS选择器
        text: 要填充的文本

    Returns:
        bool: 填充是否成功
    """
    return get_browser_manager().fill(selector, text)


def scroll(distance: int = 500) -> bool:
    """
    滚动页面

    Args:
        distance: 滚动距离

    Returns:
        bool: 滚动是否成功
    """
    return get_browser_manager().scroll(distance)


def wait_for_selector(selector: str, timeout: int = 30000) -> bool:
    """
    等待指定选择器出现

    Args:
        selector: CSS选择器
        timeout: 超时时间

    Returns:
        bool: 是否成功等待到选择器
    """
    return get_browser_manager().wait_for_selector(selector, timeout)


def screenshot(path: str) -> bool:
    """
    截图

    Args:
        path: 截图保存路径

    Returns:
        bool: 截图是否成功
    """
    return get_browser_manager().screenshot(path)


def execute_script(script: str) -> Any:
    """
    执行JavaScript

    Args:
        script: JavaScript代码

    Returns:
        Any: 执行结果
    """
    return get_browser_manager().execute_script(script)


def close_browser():
    """
    关闭浏览器
    """
    global _browser_manager
    if _browser_manager:
        _browser_manager.close()
        _browser_manager = None
