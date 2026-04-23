#!/usr/bin/env python3
"""
微博爬虫行为模拟模块
功能：模拟人类行为，如鼠标移动、滚动、点击等
特性：支持自然的行为模式，避免被反爬系统检测
"""

import logging
import random
import time
from typing import Optional, Tuple

from playwright.sync_api import Page

logger = logging.getLogger("spider.behavior")


class BehaviorSimulator:
    """
    行为模拟器
    负责模拟人类的各种行为
    """

    def __init__(self, page: Page):
        """
        初始化行为模拟器

        Args:
            page: Playwright页面对象
        """
        self.page = page

    def move_mouse(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 1.0):
        """
        模拟鼠标移动

        Args:
            start_x: 起始X坐标
            start_y: 起始Y坐标
            end_x: 结束X坐标
            end_y: 结束Y坐标
            duration: 移动持续时间
        """
        try:
            # 移动到起始位置
            self.page.mouse.move(start_x, start_y)
            time.sleep(0.1)

            # 计算贝塞尔曲线路径
            points = self._generate_bezier_points(
                (start_x, start_y), (end_x, end_y), points=10
            )

            # 按照路径移动
            step_duration = duration / len(points)
            for point in points:
                self.page.mouse.move(point[0], point[1])
                time.sleep(step_duration)

            logger.info(f"成功模拟鼠标移动: ({start_x},{start_y}) → ({end_x},{end_y})")
        except Exception as e:
            logger.error(f"模拟鼠标移动失败: {e}")

    def _generate_bezier_points(self, start: Tuple[int, int], end: Tuple[int, int], points: int = 10) -> list:
        """
        生成贝塞尔曲线路径点

        Args:
            start: 起始点
            end: 结束点
            points: 生成的点数

        Returns:
            list: 路径点列表
        """
        import math

        points_list = []
        # 控制点
        control1 = (start[0] + random.randint(-100, 100), start[1] + random.randint(-100, 100))
        control2 = (end[0] + random.randint(-100, 100), end[1] + random.randint(-100, 100))

        for t in range(points):
            t /= points
            x = (1 - t)**3 * start[0] + 3 * (1 - t)**2 * t * control1[0] + 3 * (1 - t) * t**2 * control2[0] + t**3 * end[0]
            y = (1 - t)**3 * start[1] + 3 * (1 - t)**2 * t * control1[1] + 3 * (1 - t) * t**2 * control2[1] + t**3 * end[1]
            points_list.append((int(x), int(y)))

        return points_list

    def random_click(self, min_x: int = 100, max_x: int = 1800, min_y: int = 100, max_y: int = 900):
        """
        模拟随机点击

        Args:
            min_x: 最小X坐标
            max_x: 最大X坐标
            min_y: 最小Y坐标
            max_y: 最大Y坐标
        """
        try:
            # 随机目标位置
            target_x = random.randint(min_x, max_x)
            target_y = random.randint(min_y, max_y)

            # 获取当前鼠标位置
            current_x, current_y = self._get_mouse_position()

            # 移动到目标位置
            self.move_mouse(current_x, current_y, target_x, target_y)

            # 点击
            self.page.mouse.click(target_x, target_y)
            time.sleep(0.3)

            logger.info(f"成功模拟随机点击: ({target_x},{target_y})")
        except Exception as e:
            logger.error(f"模拟随机点击失败: {e}")

    def _get_mouse_position(self) -> Tuple[int, int]:
        """
        获取当前鼠标位置

        Returns:
            Tuple[int, int]: 鼠标位置
        """
        # 默认返回屏幕中心
        return 960, 540

    def natural_scroll(self, total_distance: int = 2000, step: int = 300):
        """
        模拟自然滚动

        Args:
            total_distance: 总滚动距离
            step: 每步滚动距离
        """
        try:
            remaining = total_distance
            while remaining > 0:
                # 随机滚动距离
                scroll_distance = random.randint(step // 2, step)
                scroll_distance = min(scroll_distance, remaining)

                # 滚动
                self.page.mouse.wheel(0, scroll_distance)

                # 随机延迟
                delay = random.uniform(0.2, 0.8)
                time.sleep(delay)

                remaining -= scroll_distance

                # 随机暂停
                if random.random() > 0.7:
                    pause = random.uniform(1, 3)
                    time.sleep(pause)

            logger.info(f"成功模拟自然滚动，总距离: {total_distance}px")
        except Exception as e:
            logger.error(f"模拟自然滚动失败: {e}")

    def random_movement(self, duration: float = 5.0):
        """
        模拟随机鼠标移动

        Args:
            duration: 持续时间
        """
        try:
            start_time = time.time()
            while time.time() - start_time < duration:
                # 随机目标位置
                target_x = random.randint(100, 1800)
                target_y = random.randint(100, 900)

                # 获取当前鼠标位置
                current_x, current_y = self._get_mouse_position()

                # 移动到目标位置
                move_duration = random.uniform(0.5, 1.5)
                self.move_mouse(current_x, current_y, target_x, target_y, move_duration)

                # 随机暂停
                pause = random.uniform(0.3, 1.0)
                time.sleep(pause)

            logger.info(f"成功模拟随机鼠标移动，持续时间: {duration}s")
        except Exception as e:
            logger.error(f"模拟随机鼠标移动失败: {e}")

    def human_typing(self, selector: str, text: str):
        """
        模拟人类打字

        Args:
            selector: CSS选择器
            text: 要输入的文本
        """
        try:
            # 点击输入框
            self.page.click(selector)
            time.sleep(0.2)

            # 逐字输入
            for char in text:
                self.page.keyboard.type(char)
                # 随机延迟
                delay = random.uniform(0.05, 0.2)
                time.sleep(delay)

            # 随机按Tab或Enter键
            if random.random() > 0.5:
                self.page.keyboard.press("Tab")
            else:
                self.page.keyboard.press("Enter")

            time.sleep(0.5)
            logger.info(f"成功模拟人类打字: {text}")
        except Exception as e:
            logger.error(f"模拟人类打字失败: {e}")

    def page_interaction(self, duration: float = 10.0):
        """
        模拟页面交互

        Args:
            duration: 交互持续时间
        """
        try:
            start_time = time.time()
            while time.time() - start_time < duration:
                # 随机选择行为
                action = random.choice(["scroll", "move", "click"])

                if action == "scroll":
                    # 随机滚动
                    distance = random.randint(100, 500)
                    self.page.mouse.wheel(0, distance)
                    time.sleep(random.uniform(0.3, 1.0))

                elif action == "move":
                    # 随机移动
                    target_x = random.randint(100, 1800)
                    target_y = random.randint(100, 900)
                    current_x, current_y = self._get_mouse_position()
                    self.move_mouse(current_x, current_y, target_x, target_y)
                    time.sleep(random.uniform(0.5, 1.5))

                elif action == "click":
                    # 随机点击
                    self.random_click()

            logger.info(f"成功模拟页面交互，持续时间: {duration}s")
        except Exception as e:
            logger.error(f"模拟页面交互失败: {e}")


# 全局行为模拟器实例
_behavior_simulator = None


def get_behavior_simulator(page: Optional[Page] = None) -> Optional[BehaviorSimulator]:
    """
    获取行为模拟器实例

    Args:
        page: Playwright页面对象

    Returns:
        BehaviorSimulator: 行为模拟器实例
    """
    global _behavior_simulator
    if _behavior_simulator is None and page:
        _behavior_simulator = BehaviorSimulator(page)
    return _behavior_simulator


def simulate_human_behavior(page: Page, duration: float = 5.0):
    """
    模拟人类行为

    Args:
        page: Playwright页面对象
        duration: 模拟持续时间
    """
    simulator = get_behavior_simulator(page)
    if simulator:
        simulator.page_interaction(duration)


def simulate_mouse_movement(page: Page, start_x: int, start_y: int, end_x: int, end_y: int):
    """
    模拟鼠标移动

    Args:
        page: Playwright页面对象
        start_x: 起始X坐标
        start_y: 起始Y坐标
        end_x: 结束X坐标
        end_y: 结束Y坐标
    """
    simulator = get_behavior_simulator(page)
    if simulator:
        simulator.move_mouse(start_x, start_y, end_x, end_y)


def simulate_natural_scroll(page: Page, total_distance: int = 2000):
    """
    模拟自然滚动

    Args:
        page: Playwright页面对象
        total_distance: 总滚动距离
    """
    simulator = get_behavior_simulator(page)
    if simulator:
        simulator.natural_scroll(total_distance)


def simulate_human_typing(page: Page, selector: str, text: str):
    """
    模拟人类打字

    Args:
        page: Playwright页面对象
        selector: CSS选择器
        text: 要输入的文本
    """
    simulator = get_behavior_simulator(page)
    if simulator:
        simulator.human_typing(selector, text)
