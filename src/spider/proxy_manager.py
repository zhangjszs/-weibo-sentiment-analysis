#!/usr/bin/env python3
"""
微博代理池管理模块
功能：自动获取、测试和管理代理IP
特性：支持多源代理获取、自动测试、质量评估
"""

import json
import logging
import os
import random
import threading
import time
from typing import List, Dict, Optional

import requests

logger = logging.getLogger("spider.proxy")


class ProxyManager:
    """
    代理池管理器
    负责自动获取、测试和管理代理IP
    """

    def __init__(self, proxy_file: str = "spider/working_proxies.json", test_url: str = "http://httpbin.org/ip"):
        """
        初始化代理池管理器

        Args:
            proxy_file: 代理文件路径
            test_url: 测试代理可用性的URL
        """
        self.proxy_file = proxy_file
        self.test_url = test_url
        self.working_proxies = []
        self.proxy_lock = threading.Lock()
        self._load_proxies()

    def _load_proxies(self):
        """
        从文件加载代理
        """
        try:
            if os.path.exists(self.proxy_file):
                with open(self.proxy_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 支持两种格式：字符串列表或字典列表
                    if isinstance(data, list):
                        # 字符串列表格式 ["ip:port", ...]
                        self.working_proxies = data
                    elif isinstance(data, dict) and "proxies" in data:
                        # 字典格式 {"proxies": [{"ip": "x", "port": "y"}, ...]}
                        self.working_proxies = [
                            f"{p['ip']}:{p['port']}"
                            for p in data["proxies"]
                            if "ip" in p and "port" in p
                        ]
                    else:
                        self.working_proxies = []
                logger.info(f"从文件加载代理: {len(self.working_proxies)} 个")
            else:
                logger.info("代理文件不存在，将在获取代理后创建")
        except Exception as e:
            logger.error(f"加载代理失败: {e}")
            self.working_proxies = []

    def _save_proxies(self):
        """
        保存代理到文件
        """
        try:
            # 创建目录（如果不存在）
            proxy_dir = os.path.dirname(self.proxy_file)
            if proxy_dir and not os.path.exists(proxy_dir):
                os.makedirs(proxy_dir)

            with open(self.proxy_file, "w", encoding="utf-8") as f:
                json.dump(self.working_proxies, f, indent=2, ensure_ascii=False)
            logger.info(f"代理已保存到文件: {self.proxy_file}")
        except Exception as e:
            logger.error(f"保存代理失败: {e}")

    def test_proxy(self, proxy_ip: str, timeout: int = 10) -> bool:
        """
        测试代理IP的可用性

        Args:
            proxy_ip: 代理地址 (格式: "ip:port")
            timeout: 测试超时时间

        Returns:
            bool: 代理是否可用
        """
        try:
            proxy_dict = {"http": f"http://{proxy_ip}", "https": f"http://{proxy_ip}"}

            # 随机User-Agent
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
            ]

            headers = {
                "User-Agent": random.choice(user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }

            start_time = time.time()
            response = requests.get(
                self.test_url,
                proxies=proxy_dict,
                headers=headers,
                timeout=timeout
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                logger.debug(
                    f"代理测试成功: {proxy_ip} → IP: {result.get('origin', 'Unknown')}, 响应时间: {response_time:.2f}s"
                )
                return True
            else:
                logger.debug(
                    f"代理测试失败: {proxy_ip} (状态码: {response.status_code})"
                )
                return False

        except Exception as e:
            logger.debug(f"代理测试异常: {proxy_ip} ({e})")
            return False

    def get_proxies_from_free_sources(self) -> List[str]:
        """
        从免费代理源获取代理IP

        Returns:
            List[str]: 代理IP列表
        """
        proxies = []

        # 代理源1: 快代理
        try:
            url = "https://www.kuaidaili.com/free/inha/1/"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                import re
                # 简单的正则匹配，实际项目中建议使用BeautifulSoup
                ip_pattern = r"<td data-title='IP'>(.*?)</td>"
                port_pattern = r"<td data-title='PORT'>(.*?)</td>"
                ips = re.findall(ip_pattern, response.text)
                ports = re.findall(port_pattern, response.text)
                for ip, port in zip(ips, ports):
                    proxies.append(f"{ip}:{port}")
                logger.info(f"从快代理获取到 {len(ips)} 个代理")
        except Exception as e:
            logger.error(f"从快代理获取代理失败: {e}")

        # 代理源2: 西刺代理
        try:
            url = "https://www.xicidaili.com/nn/1"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                import re
                ip_pattern = r"<td>(\d+\.\d+\.\d+\.\d+)</td>"
                port_pattern = r"<td>(\d+)</td>"
                ips = re.findall(ip_pattern, response.text)
                ports = re.findall(port_pattern, response.text)
                # 去重并配对
                unique_ips = []
                unique_ports = []
                seen = set()
                for ip, port in zip(ips, ports):
                    if ip not in seen:
                        seen.add(ip)
                        unique_ips.append(ip)
                        unique_ports.append(port)
                for ip, port in zip(unique_ips, unique_ports):
                    proxies.append(f"{ip}:{port}")
                logger.info(f"从西刺代理获取到 {len(unique_ips)} 个代理")
        except Exception as e:
            logger.error(f"从西刺代理获取代理失败: {e}")

        # 代理源3: 免费代理库API
        try:
            url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                proxy_list = response.text.strip().split('\n')
                for proxy in proxy_list:
                    if proxy:
                        proxies.append(proxy)
                logger.info(f"从ProxyScrape获取到 {len(proxy_list)} 个代理")
        except Exception as e:
            logger.error(f"从ProxyScrape获取代理失败: {e}")

        # 去重
        proxies = list(set(proxies))
        logger.info(f"总共获取到 {len(proxies)} 个唯一代理")
        return proxies

    def refresh_proxies(self):
        """
        刷新代理池
        """
        logger.info("开始刷新代理池...")

        # 获取新代理
        new_proxies = self.get_proxies_from_free_sources()

        # 测试新代理
        working_proxies = []
        total = len(new_proxies)
        for i, proxy in enumerate(new_proxies):
            logger.info(f"测试代理 {i+1}/{total}: {proxy}")
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
            # 避免请求过于频繁
            time.sleep(0.1)

        # 更新代理池
        with self.proxy_lock:
            self.working_proxies = working_proxies
            self._save_proxies()

        logger.info(f"代理池刷新完成，可用代理: {len(self.working_proxies)} 个")

    def get_working_proxy(self, verify: bool = False) -> Optional[Dict[str, str]]:
        """
        获取一个可用的代理

        Args:
            verify: 是否验证代理可用性

        Returns:
            Dict[str, str]: 代理配置字典，失败返回None
        """
        with self.proxy_lock:
            if not self.working_proxies:
                logger.warning("代理池为空，尝试刷新代理")
                self.refresh_proxies()

            if not self.working_proxies:
                logger.warning("无可用代理，将使用直连")
                return None

            # 随机选择一个代理
            proxy_ip = random.choice(self.working_proxies)

            # 如果需要验证，测试代理可用性
            if verify:
                if self.test_proxy(proxy_ip):
                    return {
                        "http": f"http://{proxy_ip}",
                        "https": f"http://{proxy_ip}",
                    }
                else:
                    # 移除失效代理
                    self.working_proxies.remove(proxy_ip)
                    self._save_proxies()
                    logger.warning(f"移除失效代理: {proxy_ip}")
                    # 递归获取下一个代理
                    return self.get_working_proxy(verify)

            # 直接返回（不验证以提高效率）
            return {"http": f"http://{proxy_ip}", "https": f"http://{proxy_ip}"}

    def add_proxy(self, proxy_ip: str) -> bool:
        """
        添加新代理到代理池

        Args:
            proxy_ip: 代理地址

        Returns:
            bool: 添加是否成功
        """
        with self.proxy_lock:
            if proxy_ip not in self.working_proxies:
                if self.test_proxy(proxy_ip):
                    self.working_proxies.append(proxy_ip)
                    self._save_proxies()
                    logger.info(f"添加可用代理: {proxy_ip}")
                    return True
                else:
                    logger.warning(f"代理不可用: {proxy_ip}")
                    return False
            return True

    def remove_proxy(self, proxy_ip: str):
        """
        从代理池移除代理

        Args:
            proxy_ip: 代理地址
        """
        with self.proxy_lock:
            if proxy_ip in self.working_proxies:
                self.working_proxies.remove(proxy_ip)
                self._save_proxies()
                logger.info(f"移除代理: {proxy_ip}")

    def get_proxy_count(self) -> int:
        """
        获取可用代理数量

        Returns:
            int: 可用代理数量
        """
        with self.proxy_lock:
            return len(self.working_proxies)

    def clear_proxies(self):
        """
        清空代理池
        """
        with self.proxy_lock:
            self.working_proxies = []
            if os.path.exists(self.proxy_file):
                os.remove(self.proxy_file)
            logger.info("代理池已清空")


# 全局代理管理器实例
_proxy_manager = None


def get_proxy_manager() -> ProxyManager:
    """
    获取全局代理管理器实例

    Returns:
        ProxyManager: 代理管理器实例
    """
    global _proxy_manager
    if _proxy_manager is None:
        _proxy_manager = ProxyManager()
    return _proxy_manager


def get_working_proxy(verify: bool = False) -> Optional[Dict[str, str]]:
    """
    获取一个可用的代理

    Args:
        verify: 是否验证代理可用性

    Returns:
        Dict[str, str]: 代理配置字典，失败返回None
    """
    return get_proxy_manager().get_working_proxy(verify)


def refresh_proxies():
    """
    刷新代理池
    """
    get_proxy_manager().refresh_proxies()


def get_proxy_count() -> int:
    """
    获取可用代理数量

    Returns:
        int: 可用代理数量
    """
    return get_proxy_manager().get_proxy_count()
