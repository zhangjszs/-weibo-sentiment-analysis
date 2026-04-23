#!/usr/bin/env python3
"""
微博爬虫监控模块
功能：实时监控爬虫运行状态，提供预警和统计功能
特性：支持实时统计、异常预警、性能分析
"""

import json
import logging
import os
import time
from datetime import datetime
from threading import Thread, Lock
from typing import Dict, Optional

logger = logging.getLogger("spider.monitor")


class SpiderMonitor:
    """
    爬虫监控器
    负责实时监控爬虫运行状态
    """

    def __init__(self, log_file: str = "spider/monitor.log"):
        """
        初始化监控器

        Args:
            log_file: 监控日志文件路径
        """
        self.log_file = log_file
        self.stats = {
            "total_requests": 0,
            "success_requests": 0,
            "failed_requests": 0,
            "success_rate": 0.0,
            "start_time": time.time(),
            "last_update": time.time(),
            "proxy_usage": {},
            "cookie_status": "unknown",
            "errors": [],
            "current_url": "",
            "crawled_items": 0,
            "speed": 0.0,  # 每秒爬取速度
        }
        self.lock = Lock()
        self.alert_thresholds = {
            "success_rate": 0.5,  # 成功率低于50%报警
            "error_rate": 0.3,  # 错误率高于30%报警
            "request_interval": 0.1,  # 每秒请求数超过10次报警
        }
        self._initialize_log()

    def _initialize_log(self):
        """
        初始化监控日志文件
        """
        try:
            # 创建目录（如果不存在）
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # 写入初始化日志
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] 监控器初始化\n")
            logger.info("监控器初始化成功")
        except Exception as e:
            logger.error(f"初始化监控日志失败: {e}")

    def log_request(self, success: bool, url: str = ""):
        """
        记录请求结果

        Args:
            success: 请求是否成功
            url: 请求URL
        """
        with self.lock:
            self.stats["total_requests"] += 1
            if success:
                self.stats["success_requests"] += 1
            else:
                self.stats["failed_requests"] += 1
            
            # 更新成功率
            if self.stats["total_requests"] > 0:
                self.stats["success_rate"] = (
                    self.stats["success_requests"] / self.stats["total_requests"]
                )
            
            self.stats["last_update"] = time.time()
            self.stats["current_url"] = url

            # 检查是否需要报警
            self._check_alert()

    def log_proxy_usage(self, proxy: str, success: bool):
        """
        记录代理使用情况

        Args:
            proxy: 代理地址
            success: 是否成功
        """
        with self.lock:
            if proxy not in self.stats["proxy_usage"]:
                self.stats["proxy_usage"][proxy] = {
                    "total": 0,
                    "success": 0,
                    "success_rate": 0.0
                }
            
            usage = self.stats["proxy_usage"][proxy]
            usage["total"] += 1
            if success:
                usage["success"] += 1
            usage["success_rate"] = usage["success"] / usage["total"]

    def log_cookie_status(self, status: str):
        """
        记录Cookie状态

        Args:
            status: Cookie状态
        """
        with self.lock:
            self.stats["cookie_status"] = status

    def log_error(self, error: str):
        """
        记录错误信息

        Args:
            error: 错误信息
        """
        with self.lock:
            error_entry = {
                "time": datetime.now().isoformat(),
                "error": error
            }
            self.stats["errors"].append(error_entry)
            # 只保留最近100个错误
            if len(self.stats["errors"]) > 100:
                self.stats["errors"] = self.stats["errors"][-100:]

    def log_crawled_item(self):
        """
        记录爬取的项目
        """
        with self.lock:
            self.stats["crawled_items"] += 1
            # 计算爬取速度
            elapsed = time.time() - self.stats["start_time"]
            if elapsed > 0:
                self.stats["speed"] = self.stats["crawled_items"] / elapsed

    def _check_alert(self):
        """
        检查是否需要报警
        """
        # 检查成功率
        if self.stats["success_rate"] < self.alert_thresholds["success_rate"]:
            self._alert(f"成功率过低: {self.stats['success_rate']:.2f}")

        # 检查错误率
        error_rate = self.stats["failed_requests"] / max(self.stats["total_requests"], 1)
        if error_rate > self.alert_thresholds["error_rate"]:
            self._alert(f"错误率过高: {error_rate:.2f}")

    def _alert(self, message: str):
        """
        发送报警

        Args:
            message: 报警信息
        """
        alert_message = f"[{datetime.now()}] ALERT: {message}"
        logger.warning(alert_message)
        
        # 写入日志文件
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(alert_message + "\n")
        except Exception as e:
            logger.error(f"写入报警日志失败: {e}")

    def get_stats(self) -> Dict:
        """
        获取当前统计信息

        Returns:
            Dict: 统计信息
        """
        with self.lock:
            # 计算运行时间
            uptime = time.time() - self.stats["start_time"]
            stats_copy = self.stats.copy()
            stats_copy["uptime"] = uptime
            stats_copy["uptime_hours"] = uptime / 3600
            
            # 计算请求速度
            if uptime > 0:
                stats_copy["requests_per_second"] = stats_copy["total_requests"] / uptime
            
            return stats_copy

    def save_stats(self, file_path: str = "spider/stats.json"):
        """
        保存统计信息到文件

        Args:
            file_path: 保存路径
        """
        try:
            # 创建目录（如果不存在）
            stats_dir = os.path.dirname(file_path)
            if stats_dir and not os.path.exists(stats_dir):
                os.makedirs(stats_dir)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.get_stats(), f, indent=2, ensure_ascii=False)
            logger.info(f"统计信息已保存到: {file_path}")
        except Exception as e:
            logger.error(f"保存统计信息失败: {e}")

    def print_stats(self):
        """
        打印统计信息
        """
        stats = self.get_stats()
        print("=" * 60)
        print("爬虫运行统计")
        print("=" * 60)
        print(f"总请求数: {stats['total_requests']}")
        print(f"成功请求: {stats['success_requests']}")
        print(f"失败请求: {stats['failed_requests']}")
        print(f"成功率: {stats['success_rate']:.2f}")
        print(f"运行时间: {stats['uptime']:.2f}秒")
        print(f"爬取项目: {stats['crawled_items']}")
        print(f"爬取速度: {stats['speed']:.2f} 项/秒")
        print(f"请求速度: {stats.get('requests_per_second', 0):.2f} 请求/秒")
        print(f"Cookie状态: {stats['cookie_status']}")
        print(f"当前URL: {stats['current_url']}")
        print(f"错误数量: {len(stats['errors'])}")
        print(f"代理数量: {len(stats['proxy_usage'])}")
        print("=" * 60)


# 全局监控器实例
_monitor = None


def get_monitor() -> SpiderMonitor:
    """
    获取全局监控器实例

    Returns:
        SpiderMonitor: 监控器实例
    """
    global _monitor
    if _monitor is None:
        _monitor = SpiderMonitor()
    return _monitor


def log_request(success: bool, url: str = ""):
    """
    记录请求结果

    Args:
        success: 请求是否成功
        url: 请求URL
    """
    get_monitor().log_request(success, url)


def log_proxy_usage(proxy: str, success: bool):
    """
    记录代理使用情况

    Args:
        proxy: 代理地址
        success: 是否成功
    """
    get_monitor().log_proxy_usage(proxy, success)


def log_cookie_status(status: str):
    """
    记录Cookie状态

    Args:
        status: Cookie状态
    """
    get_monitor().log_cookie_status(status)


def log_error(error: str):
    """
    记录错误信息

    Args:
        error: 错误信息
    """
    get_monitor().log_error(error)


def log_crawled_item():
    """
    记录爬取的项目
    """
    get_monitor().log_crawled_item()


def get_stats() -> Dict:
    """
    获取当前统计信息

    Returns:
        Dict: 统计信息
    """
    return get_monitor().get_stats()


def print_stats():
    """
    打印统计信息
    """
    get_monitor().print_stats()


def save_stats(file_path: str = "spider/stats.json"):
    """
    保存统计信息到文件

    Args:
        file_path: 保存路径
    """
    get_monitor().save_stats(file_path)


class MonitorThread(Thread):
    """
    监控线程
    定期打印和保存统计信息
    """

    def __init__(self, interval: int = 60):
        """
        初始化监控线程

        Args:
            interval: 监控间隔（秒）
        """
        super().__init__(daemon=True)
        self.interval = interval

    def run(self):
        """
        运行监控线程
        """
        while True:
            try:
                # 打印统计信息
                print_stats()
                # 保存统计信息
                save_stats()
                # 等待下一次监控
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"监控线程异常: {e}")
                time.sleep(self.interval)


def start_monitor_thread(interval: int = 60):
    """
    启动监控线程

    Args:
        interval: 监控间隔（秒）
    """
    thread = MonitorThread(interval)
    thread.start()
    logger.info(f"监控线程已启动，间隔: {interval}秒")
