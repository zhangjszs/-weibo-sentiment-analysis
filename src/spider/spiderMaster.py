#!/usr/bin/env python3
"""
微博爬虫主控制器
功能：协调文章、评论、用户信息三大爬虫模块
特性：支持顺序/并发/智能三种爬取模式，完善的异常处理和日志记录
"""

import logging
import os
import random
import sys
import threading
import time
from threading import Event, Lock
from typing import Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import save_to_sql
from spiderComments import start as start_comments
from spiderContent import start as start_content
from spiderUserInfo import start_user_spider

# ========== 配置常量 ==========
MAX_REQUESTS = 3  # 每个模块最多请求次数
REQUEST_INTERVAL_MIN = 1.5  # 最小请求间隔（秒）
REQUEST_INTERVAL_MAX = 3.0  # 最大请求间隔（秒）
THREAD_START_DELAY = 2.0  # 线程启动间隔（秒）


# ========== 日志配置 ==========
def setup_logging() -> logging.Logger:
    """配置日志记录器"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("weibo_spider")
    logger.setLevel(logging.INFO)

    # 避免重复添加处理器
    if not logger.handlers:
        # 文件处理器
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "weibo_spider.log"), encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 格式化器
        formatter = logging.Formatter(
            "%(asctime)s - %(threadName)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


logger = setup_logging()


class WeiboSpiderController:
    """
    微博爬虫控制器

    管理三种爬虫模块的协调执行：
    1. 文章爬取 (spiderContent)
    2. 评论爬取 (spiderComments)
    3. 用户信息爬取 (spiderUserInfo)

    支持三种运行模式：
    - 顺序模式：按依赖关系依次执行，最稳定
    - 并发模式：多线程并行执行，效率最高
    - 智能模式：平衡稳定性和效率
    """

    def __init__(self, delay: float = 2.0, max_workers: int = 3):
        """
        初始化控制器

        Args:
            delay: 模块间延迟（秒）
            max_workers: 最大工作线程数
        """
        self.delay = delay
        self.max_workers = max_workers

        # 任务完成状态
        self.content_completed = Event()
        self.comments_completed = Event()
        self.user_completed = Event()

        # 搜索模式配置
        self.search_mode = False
        self.search_keyword: Optional[str] = None

        # 线程同步锁
        self._lock = Lock()
        self._error_count = 0
        self._max_errors = 5

    def _get_request_interval(self) -> float:
        """获取随机请求间隔"""
        return random.uniform(REQUEST_INTERVAL_MIN, REQUEST_INTERVAL_MAX)

    def content_spider_thread(self) -> None:
        """文章爬取线程"""
        thread_name = threading.current_thread().name
        logger.info(f"[{thread_name}] 开始执行文章爬取任务")

        try:
            if self.search_mode and self.search_keyword:
                logger.info(f"[{thread_name}] 执行关键词搜索: {self.search_keyword}")
                start_content(
                    typeNum=1, pageNum=10, mode="search", keyword=self.search_keyword
                )
            else:
                logger.info(f"[{thread_name}] 执行分类爬取")
                start_content(typeNum=10, pageNum=5, mode="category")

            self.content_completed.set()
            logger.info(f"[{thread_name}] 文章爬取任务完成")

        except Exception as e:
            logger.error(f"[{thread_name}] 文章爬取线程异常: {e}", exc_info=True)
            self._error_count += 1
            self.content_completed.set()  # 即使失败也标记完成，避免阻塞

    def comments_spider_thread(self) -> None:
        """评论爬取线程 - 等待文章爬取完成后执行"""
        thread_name = threading.current_thread().name
        logger.info(f"[{thread_name}] 等待文章爬取完成...")

        # 等待文章爬取完成（带超时）
        if not self.content_completed.wait(timeout=300):  # 5分钟超时
            logger.error(f"[{thread_name}] 等待文章爬取超时")
            self.comments_completed.set()
            return

        # 检查文章爬取是否成功
        if self._error_count > 0:
            logger.warning(f"[{thread_name}] 文章爬取出现错误，跳过评论爬取")
            self.comments_completed.set()
            return

        # 模块间延迟
        time.sleep(self.delay)

        try:
            logger.info(f"[{thread_name}] 开始执行评论爬取任务")
            start_comments()
            self.comments_completed.set()
            logger.info(f"[{thread_name}] 评论爬取任务完成")

        except Exception as e:
            logger.error(f"[{thread_name}] 评论爬取线程异常: {e}", exc_info=True)
            self._error_count += 1
            self.comments_completed.set()

    def user_spider_thread(self) -> None:
        """用户信息爬取线程 - 等待评论爬取完成后执行"""
        thread_name = threading.current_thread().name
        logger.info(f"[{thread_name}] 等待评论爬取完成...")

        # 等待评论爬取完成（带超时）
        if not self.comments_completed.wait(timeout=300):  # 5分钟超时
            logger.error(f"[{thread_name}] 等待评论爬取超时")
            self.user_completed.set()
            return

        # 模块间延迟
        time.sleep(self.delay)

        try:
            logger.info(f"[{thread_name}] 开始执行用户信息爬取任务")
            start_user_spider(max_users=50)
            self.user_completed.set()
            logger.info(f"[{thread_name}] 用户信息爬取任务完成")

        except Exception as e:
            logger.error(f"[{thread_name}] 用户信息爬取线程异常: {e}", exc_info=True)
            self._error_count += 1
            self.user_completed.set()

    def concurrent_spider_mode(self, keyword: Optional[str] = None) -> None:
        """
        并发爬取模式

        使用线程Event替代锁机制，避免死锁问题
        文章 -> 评论 -> 用户 按依赖顺序执行

        Args:
            keyword: 搜索关键词（可选）
        """
        logger.info("=" * 60)
        logger.info("启动并发爬取模式")
        logger.info("=" * 60)

        start_time = time.time()

        # 重置状态
        self.content_completed.clear()
        self.comments_completed.clear()
        self.user_completed.clear()
        self._error_count = 0

        if keyword:
            self.search_mode = True
            self.search_keyword = keyword

        # 创建线程
        threads = [
            threading.Thread(target=self.content_spider_thread, name="ContentSpider"),
            threading.Thread(target=self.comments_spider_thread, name="CommentsSpider"),
            threading.Thread(target=self.user_spider_thread, name="UserSpider"),
        ]

        # 启动所有线程（它们会自动按依赖关系等待）
        for i, thread in enumerate(threads):
            thread.start()
            if i < len(threads) - 1:  # 最后一个线程不需要延迟
                time.sleep(THREAD_START_DELAY)

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        elapsed = time.time() - start_time
        logger.info(f"所有爬取任务完成！总耗时: {elapsed:.2f}秒")

        # 保存数据
        if self._error_count < self._max_errors:
            self._save_data()
        else:
            logger.error(f"错误次数过多({self._error_count})，跳过数据保存")

    def sequential_spider_mode(self, keyword: Optional[str] = None) -> None:
        """
        顺序爬取模式 - 最稳定

        按依赖关系依次执行：文章 -> 评论 -> 用户

        Args:
            keyword: 搜索关键词（可选）
        """
        logger.info("=" * 60)
        logger.info("启动顺序爬取模式")
        logger.info("=" * 60)

        start_time = time.time()
        self._error_count = 0

        try:
            # 阶段1: 文章爬取
            logger.info("【阶段1/3】开始爬取文章数据")
            if keyword:
                start_content(typeNum=1, pageNum=10, mode="search", keyword=keyword)
            else:
                start_content(typeNum=10, pageNum=5)
            logger.info("【阶段1/3】文章爬取完成")

            time.sleep(self.delay)

            # 阶段2: 评论爬取
            logger.info("【阶段2/3】开始爬取评论数据")
            start_comments()
            logger.info("【阶段2/3】评论爬取完成")

            time.sleep(self.delay)

            # 阶段3: 用户信息爬取
            logger.info("【阶段3/3】开始爬取用户信息")
            start_user_spider(max_users=50)
            logger.info("【阶段3/3】用户信息爬取完成")

            elapsed = time.time() - start_time
            logger.info(f"所有爬取任务顺序完成！总耗时: {elapsed:.2f}秒")

            # 保存数据
            self._save_data()

        except Exception as e:
            logger.error(f"顺序爬取模式异常: {e}", exc_info=True)
            raise

    def smart_spider_mode(self) -> None:
        """
        智能爬取模式 - 平衡稳定性和效率

        文章顺序爬取，评论和用户并发爬取
        """
        logger.info("=" * 60)
        logger.info("启动智能爬取模式")
        logger.info("=" * 60)

        start_time = time.time()
        self._error_count = 0

        try:
            # 阶段1: 文章爬取（必须顺序）
            logger.info("【阶段1/2】爬取文章数据")
            start_content(typeNum=10, pageNum=5)
            logger.info("【阶段1/2】文章爬取完成")

            # 阶段2: 并发爬取评论和用户信息
            logger.info("【阶段2/2】并发爬取评论和用户信息")

            self.comments_completed.clear()
            self.user_completed.clear()

            comments_thread = threading.Thread(
                target=self._run_comments_with_event, name="CommentsSpiderSmart"
            )
            user_thread = threading.Thread(
                target=self._run_user_with_event, name="UserSpiderSmart"
            )

            comments_thread.start()
            time.sleep(1)
            user_thread.start()

            comments_thread.join()
            user_thread.join()

            elapsed = time.time() - start_time
            logger.info(f"智能爬取模式完成！总耗时: {elapsed:.2f}秒")

            self._save_data()

        except Exception as e:
            logger.error(f"智能爬取模式异常: {e}", exc_info=True)
            raise

    def _run_comments_with_event(self) -> None:
        """包装评论爬取函数，设置Event"""
        try:
            time.sleep(self.delay)
            start_comments()
            self.comments_completed.set()
        except Exception as e:
            logger.error(f"评论爬取异常: {e}")
            self.comments_completed.set()

    def _run_user_with_event(self) -> None:
        """包装用户爬取函数，设置Event"""
        try:
            time.sleep(self.delay + 1)
            start_user_spider(max_users=30)
            self.user_completed.set()
        except Exception as e:
            logger.error(f"用户爬取异常: {e}")
            self.user_completed.set()

    def _save_data(self) -> None:
        """保存数据到数据库"""
        try:
            logger.info("开始将数据保存到数据库...")
            save_to_sql()
            logger.info("数据入库完成")
        except Exception as e:
            logger.error(f"数据入库失败: {e}", exc_info=True)


def display_menu() -> None:
    """显示主菜单"""
    print("\n" + "=" * 60)
    print("        微博舆情分析爬虫系统")
    print("=" * 60)
    print("请选择爬取模式:")
    print("  1. 顺序爬取模式（推荐-最稳定）")
    print("  2. 并发爬取模式（高效-有风险）")
    print("  3. 智能爬取模式（平衡推荐）")
    print("  4. 仅爬取文章")
    print("  5. 仅爬取评论")
    print("  6. 仅爬取用户信息")
    print("  7. 关键词搜索爬取")
    print("  0. 退出")
    print("=" * 60)


def main() -> None:
    """主函数"""
    controller = WeiboSpiderController(delay=2.0)

    while True:
        display_menu()
        choice = input("请输入选项 (0-7): ").strip()

        if choice == "0":
            print("感谢使用，再见！")
            break

        elif choice == "1":
            controller.sequential_spider_mode()

        elif choice == "2":
            confirm = input("并发模式可能导致IP被封，是否继续? (y/n): ").strip().lower()
            if confirm == "y":
                controller.concurrent_spider_mode()
            else:
                print("已取消")

        elif choice == "3":
            controller.smart_spider_mode()

        elif choice == "4":
            logger.info("仅执行文章爬取")
            try:
                start_content(typeNum=10, pageNum=5)
            except Exception as e:
                logger.error(f"文章爬取失败: {e}")

        elif choice == "5":
            logger.info("仅执行评论爬取")
            try:
                start_comments()
            except Exception as e:
                logger.error(f"评论爬取失败: {e}")

        elif choice == "6":
            logger.info("仅执行用户信息爬取")
            try:
                start_user_spider(max_users=50)
            except Exception as e:
                logger.error(f"用户爬取失败: {e}")

        elif choice == "7":
            keyword = input("请输入搜索关键词: ").strip()
            if keyword:
                logger.info(f"开始搜索爬取: {keyword}")
                controller.sequential_spider_mode(keyword=keyword)
            else:
                print("未输入关键词，返回主菜单")

        else:
            print("无效选项，请重新选择")

        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"程序异常退出: {e}", exc_info=True)
        sys.exit(1)
