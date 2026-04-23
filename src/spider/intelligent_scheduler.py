#!/usr/bin/env python3
"""
智能调度系统模块
功能：根据爬取过程中的各种指标自动调整爬取策略
特性：动态调整请求间隔、自动切换代理、智能选择爬取模式
"""

import json
import logging
import os
import random
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from .config import get_config_manager, get_working_proxy
from .monitor import get_monitoring_stats

# 配置日志
logger = logging.getLogger("spider.scheduler")


class IntelligentScheduler:
    """
    智能调度器
    根据爬取过程中的各种指标自动调整爬取策略
    """

    def __init__(self):
        """初始化智能调度器"""
        self.config_manager = get_config_manager()
        
        # 性能指标
        self.success_rate = 1.0  # 成功率
        self.error_rate = 0.0    # 错误率
        self.avg_response_time = 0.0  # 平均响应时间
        self.retry_count = 0     # 重试次数
        self.rate_limit_count = 0  # 被限流次数
        
        # 策略参数
        self.base_delay = 15.0  # 基础延迟
        self.max_delay = 60.0   # 最大延迟
        self.min_delay = 5.0    # 最小延迟
        self.current_delay = self.base_delay
        
        # 爬取模式选择
        self.use_browser_mode = False  # 是否使用浏览器模式
        self.browser_mode_threshold = 0.7  # 成功率低于此值时使用浏览器模式
        
        # 代理策略
        self.proxy_rotation_interval = 10  # 每10次请求轮换一次代理
        self.request_count = 0
        
        # 统计数据
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limit_errors": 0,
            "proxy_errors": 0,
            "browser_mode_used": 0,
            "api_mode_used": 0,
        }
        
        # 历史记录
        self.history = []
        self.history_max_length = 50
        
        # 策略调整记录
        self.adjustment_history = []
        
        logger.info("智能调度器初始化完成")

    def update_metrics(self, success: bool, response_time: float = 0, error_type: str = None):
        """
        更新性能指标
        
        Args:
            success: 请求是否成功
            response_time: 响应时间
            error_type: 错误类型
        """
        self.request_count += 1
        self.stats["total_requests"] += 1
        
        if success:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1
            if error_type == "rate_limit":
                self.stats["rate_limit_errors"] += 1
                self.rate_limit_count += 1
            elif error_type == "proxy":
                self.stats["proxy_errors"] += 1
        
        # 更新成功率和错误率
        total = self.stats["total_requests"]
        if total > 0:
            self.success_rate = self.stats["successful_requests"] / total
            self.error_rate = 1 - self.success_rate
        
        # 更新平均响应时间
        if response_time > 0:
            if self.avg_response_time == 0:
                self.avg_response_time = response_time
            else:
                self.avg_response_time = (self.avg_response_time * 0.9) + (response_time * 0.1)
        
        # 记录历史数据
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "response_time": response_time,
            "error_type": error_type,
            "current_delay": self.current_delay,
            "use_browser_mode": self.use_browser_mode,
            "success_rate": self.success_rate
        })
        
        # 限制历史记录长度
        if len(self.history) > self.history_max_length:
            self.history = self.history[-self.history_max_length:]
        
        # 调整策略
        self.adjust_strategy()

    def adjust_strategy(self):
        """
        根据性能指标调整爬取策略
        """
        adjustments = []
        
        # 1. 调整请求延迟
        new_delay = self.current_delay
        
        if self.success_rate < 0.5:
            # 成功率低，增加延迟
            new_delay = min(self.current_delay * 1.5, self.max_delay)
            if new_delay != self.current_delay:
                adjustments.append(f"增加延迟: {self.current_delay:.2f}s → {new_delay:.2f}s")
                self.current_delay = new_delay
        elif self.success_rate > 0.8:
            # 成功率高，减少延迟
            new_delay = max(self.current_delay * 0.8, self.min_delay)
            if new_delay != self.current_delay:
                adjustments.append(f"减少延迟: {self.current_delay:.2f}s → {new_delay:.2f}s")
                self.current_delay = new_delay
        
        # 2. 调整爬取模式
        if self.success_rate < self.browser_mode_threshold and not self.use_browser_mode:
            # 成功率低，切换到浏览器模式
            self.use_browser_mode = True
            adjustments.append("切换到浏览器模式")
            self.stats["browser_mode_used"] += 1
        elif self.success_rate > 0.9 and self.use_browser_mode:
            # 成功率高，切换到API模式
            self.use_browser_mode = False
            adjustments.append("切换到API模式")
            self.stats["api_mode_used"] += 1
        
        # 3. 处理限流情况
        if self.rate_limit_count > 3:
            # 频繁被限流，大幅增加延迟
            new_delay = min(self.current_delay * 2, self.max_delay)
            if new_delay != self.current_delay:
                adjustments.append(f"因限流增加延迟: {self.current_delay:.2f}s → {new_delay:.2f}s")
                self.current_delay = new_delay
            self.rate_limit_count = 0
        
        # 记录调整
        if adjustments:
            adjustment_record = {
                "timestamp": datetime.now().isoformat(),
                "adjustments": adjustments,
                "metrics": {
                    "success_rate": self.success_rate,
                    "error_rate": self.error_rate,
                    "avg_response_time": self.avg_response_time,
                    "rate_limit_count": self.rate_limit_count
                }
            }
            self.adjustment_history.append(adjustment_record)
            logger.info(f"策略调整: {', '.join(adjustments)}")

    def get_sleep_time(self) -> float:
        """
        获取当前应该的睡眠时间
        
        Returns:
            float: 睡眠时间（秒）
        """
        # 在基础延迟上添加一些随机波动
        sleep_time = self.current_delay * random.uniform(0.8, 1.2)
        return sleep_time

    def should_use_browser_mode(self) -> bool:
        """
        判断是否应该使用浏览器模式
        
        Returns:
            bool: 是否使用浏览器模式
        """
        return self.use_browser_mode

    def get_proxy(self) -> Optional[Dict[str, str]]:
        """
        获取代理，根据策略定期轮换
        
        Returns:
            Optional[Dict[str, str]]: 代理配置
        """
        # 每N次请求轮换一次代理
        if self.request_count % self.proxy_rotation_interval == 0:
            proxy = get_working_proxy(verify=True)
            if proxy:
                logger.debug(f"轮换代理: {proxy.get('http', '')}")
            return proxy
        return get_working_proxy()

    def get_scheduling_stats(self) -> Dict:
        """
        获取调度器统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            "current_delay": self.current_delay,
            "use_browser_mode": self.use_browser_mode,
            "success_rate": self.success_rate,
            "error_rate": self.error_rate,
            "avg_response_time": self.avg_response_time,
            "request_count": self.request_count,
            "rate_limit_count": self.rate_limit_count,
            "stats": self.stats,
            "adjustment_history_count": len(self.adjustment_history)
        }

    def save_stats(self, file_path: str = "scheduler_stats.json"):
        """
        保存统计信息到文件
        
        Args:
            file_path: 保存文件路径
        """
        stats_data = {
            "timestamp": datetime.now().isoformat(),
            "scheduling_stats": self.get_scheduling_stats(),
            "adjustment_history": self.adjustment_history[-10:],  # 只保存最近10条调整记录
            "recent_history": self.history[-20:],  # 只保存最近20条历史记录
        }
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(stats_data, f, indent=2, ensure_ascii=False)
            logger.info(f"统计信息已保存到: {file_path}")
        except Exception as e:
            logger.error(f"保存统计信息失败: {e}")

    def load_stats(self, file_path: str = "scheduler_stats.json"):
        """
        从文件加载统计信息
        
        Args:
            file_path: 加载文件路径
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    stats_data = json.load(f)
                
                # 恢复调度器状态
                if "scheduling_stats" in stats_data:
                    stats = stats_data["scheduling_stats"]
                    self.current_delay = stats.get("current_delay", self.base_delay)
                    self.use_browser_mode = stats.get("use_browser_mode", False)
                    self.success_rate = stats.get("success_rate", 1.0)
                    self.error_rate = stats.get("error_rate", 0.0)
                    self.avg_response_time = stats.get("avg_response_time", 0.0)
                    self.request_count = stats.get("request_count", 0)
                    self.rate_limit_count = stats.get("rate_limit_count", 0)
                    
                logger.info(f"统计信息已从: {file_path} 加载")
        except Exception as e:
            logger.error(f"加载统计信息失败: {e}")


# 全局调度器实例
_scheduler = None

def get_scheduler() -> IntelligentScheduler:
    """
    获取全局调度器实例（单例模式）
    
    Returns:
        IntelligentScheduler: 调度器实例
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = IntelligentScheduler()
    return _scheduler


def adjust_crawl_strategy(success: bool, response_time: float = 0, error_type: str = None):
    """
    调整爬取策略（便捷函数）
    
    Args:
        success: 请求是否成功
        response_time: 响应时间
        error_type: 错误类型
    """
    scheduler = get_scheduler()
    scheduler.update_metrics(success, response_time, error_type)


def get_optimal_delay() -> float:
    """
    获取最优延迟（便捷函数）
    
    Returns:
        float: 最优延迟时间
    """
    scheduler = get_scheduler()
    return scheduler.get_sleep_time()


def should_use_browser() -> bool:
    """
    判断是否应该使用浏览器模式（便捷函数）
    
    Returns:
        bool: 是否使用浏览器模式
    """
    scheduler = get_scheduler()
    return scheduler.should_use_browser_mode()


def get_optimal_proxy() -> Optional[Dict[str, str]]:
    """
    获取最优代理（便捷函数）
    
    Returns:
        Optional[Dict[str, str]]: 代理配置
    """
    scheduler = get_scheduler()
    return scheduler.get_proxy()


def get_scheduler_stats() -> Dict:
    """
    获取调度器统计信息（便捷函数）
    
    Returns:
        Dict: 统计信息
    """
    scheduler = get_scheduler()
    return scheduler.get_scheduling_stats()


if __name__ == "__main__":
    # 测试智能调度器
    logging.basicConfig(level=logging.INFO)
    scheduler = get_scheduler()
    
    # 模拟一些请求结果
    for i in range(20):
        # 模拟成功率逐渐降低
        success = random.random() > (i * 0.05)
        response_time = random.uniform(0.5, 5.0)
        error_type = "rate_limit" if not success and random.random() > 0.5 else None
        
        print(f"请求 {i+1}: 成功={success}, 响应时间={response_time:.2f}s, 错误类型={error_type}")
        scheduler.update_metrics(success, response_time, error_type)
        print(f"当前延迟: {scheduler.current_delay:.2f}s, 使用浏览器模式: {scheduler.use_browser_mode}")
        print(f"成功率: {scheduler.success_rate:.2f}, 错误率: {scheduler.error_rate:.2f}")
        print()
        
        # 模拟请求间隔
        time.sleep(0.1)
    
    # 保存统计信息
    scheduler.save_stats()
    
    # 打印最终统计
    print("最终统计:")
    print(scheduler.get_scheduling_stats())
