#!/usr/bin/env python3
"""
去重过滤器模块
功能：提供布隆过滤器和内存去重功能，防止重复数据
特性：Bloom Filter（大规模）、内存Set（小规模）、持久化
"""

import hashlib
import logging
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from config.settings import Config
except ImportError:
    # 如果导入失败，使用默认配置
    Config = None

logger = logging.getLogger(__name__)

# 尝试导入Bloom Filter（可选依赖）
try:
    from pybloom_live import ScalableBloomFilter

    BLOOM_AVAILABLE = True
except ImportError:
    logger.warning("pybloom-live未安装，将使用内存Set去重")
    BLOOM_AVAILABLE = False


class DuplicateFilter:
    """去重过滤器基类"""

    def is_duplicate(self, key: str) -> bool:
        """检查是否重复"""
        raise NotImplementedError

    def add(self, key: str) -> None:
        """添加去重键"""
        raise NotImplementedError

    def save(self) -> None:
        """保存状态"""
        return None

    def load(self) -> None:
        """加载状态"""
        return None

    def get_stats(self) -> dict:
        """获取统计信息"""
        raise NotImplementedError


class BloomFilter(DuplicateFilter):
    """布隆过滤器（适合大规模数据）"""

    def __init__(
        self, name: str = "default", capacity: int = 100000, error_rate: float = 0.001
    ):
        self.name = name
        self.capacity = capacity
        self.error_rate = error_rate
        # 使用Config.CACHE_DIR或默认路径
        if Config:
            cache_dir = Config.CACHE_DIR
        else:
            cache_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "cache"
            )
        os.makedirs(cache_dir, exist_ok=True)
        self.filter_path = os.path.join(cache_dir, f"bloom_filter_{name}.jsonl")
        self.filter = None
        self.all_keys = set()
        self._init_filter()

    def _init_filter(self):
        """初始化或加载过滤器"""
        if BLOOM_AVAILABLE:
            self.filter = ScalableBloomFilter(
                initial_capacity=self.capacity, error_rate=self.error_rate
            )
        else:
            # 回退到内存Set
            self.filter = set()

        self._load_from_disk()

    def _load_from_disk(self):
        if not os.path.exists(self.filter_path):
            logger.info(f"新建去重过滤器: {self.name}")
            return

        loaded = 0
        try:
            with open(self.filter_path, encoding="utf-8") as f:
                for line in f:
                    key = line.strip()
                    if not key:
                        continue
                    self.all_keys.add(key)
                    self.filter.add(key)
                    loaded += 1
            logger.info(f"去重过滤器已加载: {self.name}, 数量: {loaded}")
        except Exception as e:
            logger.warning(f"加载去重过滤器失败: {e}")

    def _save_to_disk(self):
        temp_path = f"{self.filter_path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                for key in self.all_keys:
                    f.write(f"{key}\n")
            os.replace(temp_path, self.filter_path)
        except Exception as e:
            logger.error(f"保存去重过滤器失败: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def is_duplicate(self, key: str) -> bool:
        """检查是否重复"""
        if self.filter is None:
            return False
        return key in self.filter

    def add(self, key: str) -> None:
        """添加去重键"""
        if key in self.all_keys:
            return
        self.all_keys.add(key)
        if self.filter is not None:
            self.filter.add(key)

    def save(self) -> None:
        """保存过滤器状态"""
        self._save_to_disk()
        logger.info(f"去重过滤器已保存: {self.name}")

    def get_stats(self) -> dict:
        """获取统计信息"""
        if self.filter is None:
            return {"type": "none", "size": 0}

        if BLOOM_AVAILABLE:
            return {
                "type": "bloom_filter",
                "name": self.name,
                "capacity": self.capacity,
                "current_size": len(self.filter),
                "error_rate": self.error_rate,
                "persisted_keys": len(self.all_keys),
            }
        else:
            return {
                "type": "memory_set",
                "name": self.name,
                "size": len(self.filter),
                "persisted_keys": len(self.all_keys),
            }


class MemoryDuplicateFilter(DuplicateFilter):
    """内存去重过滤器（适合小规模数据）"""

    def __init__(self, name: str = "memory"):
        self.name = name
        self.seen = set()
        # 使用Config.CACHE_DIR或默认路径
        if Config:
            cache_dir = Config.CACHE_DIR
        else:
            cache_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "cache"
            )
        os.makedirs(cache_dir, exist_ok=True)
        self.filter_path = os.path.join(cache_dir, f"duplicate_filter_{name}.jsonl")
        self.load()

    def is_duplicate(self, key: str) -> bool:
        return key in self.seen

    def add(self, key: str) -> None:
        self.seen.add(key)

    def save(self) -> None:
        try:
            temp_path = f"{self.filter_path}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                for key in self.seen:
                    f.write(f"{key}\n")
            os.replace(temp_path, self.filter_path)
        except Exception as e:
            logger.error(f"保存去重状态失败: {e}")

    def load(self) -> None:
        if os.path.exists(self.filter_path):
            try:
                with open(self.filter_path, encoding="utf-8") as f:
                    self.seen = {line.strip() for line in f if line.strip()}
                logger.info(f"内存去重器已加载: {len(self.seen)}条记录")
            except Exception as e:
                logger.warning(f"加载去重状态失败: {e}")

    def get_stats(self) -> dict:
        return {"type": "memory", "size": len(self.seen), "name": self.name}


class ArticleDeduplicator:
    """文章去重器 - 专门用于微博文章去重"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 使用布隆过滤器（大规模）或内存Set（小规模）
        if BLOOM_AVAILABLE:
            self.filter = BloomFilter(
                name="articles", capacity=1000000, error_rate=0.0001
            )
        else:
            self.filter = MemoryDuplicateFilter(name="articles")

        self._initialized = True
        logger.info("文章去重器初始化完成")

    def generate_key(self, article_id: str, content_hash: str = None) -> str:
        """生成去重键
        Args:
            article_id: 微博ID
            content_hash: 内容哈希（可选）
        Returns:
            str: 去重键
        """
        if content_hash:
            return f"{article_id}:{content_hash[:16]}"
        return article_id

    def is_duplicate(self, article_id: str, content: str = None) -> bool:
        """检查文章是否重复
        Args:
            article_id: 微博ID
            content: 微博内容（用于生成内容哈希）
        Returns:
            bool: 是否重复
        """
        if content:
            content_hash = hashlib.md5(content.encode()).hexdigest()
            key = self.generate_key(article_id, content_hash)
        else:
            key = article_id

        return self.filter.is_duplicate(key)

    def add(self, article_id: str, content: str = None) -> None:
        """添加文章到去重集合"""
        if content:
            content_hash = hashlib.md5(content.encode()).hexdigest()
            key = self.generate_key(article_id, content_hash)
        else:
            key = article_id

        self.filter.add(key)

    def save(self) -> None:
        """保存去重状态"""
        self.filter.save()

    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.filter.get_stats()


class CommentDeduplicator:
    """评论去重器 - 专门用于微博评论去重"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 评论数量通常比文章多，使用布隆过滤器
        if BLOOM_AVAILABLE:
            self.filter = BloomFilter(
                name="comments", capacity=5000000, error_rate=0.0001
            )
        else:
            self.filter = MemoryDuplicateFilter(name="comments")

        self._initialized = True
        logger.info("评论去重器初始化完成")

    def generate_key(self, comment_id: str, article_id: str) -> str:
        """生成去重键"""
        return f"{article_id}:{comment_id}"

    def is_duplicate(self, comment_id: str, article_id: str) -> bool:
        """检查评论是否重复"""
        key = self.generate_key(comment_id, article_id)
        return self.filter.is_duplicate(key)

    def add(self, comment_id: str, article_id: str) -> None:
        """添加评论到去重集合"""
        key = self.generate_key(comment_id, article_id)
        self.filter.add(key)

    def save(self) -> None:
        """保存去重状态"""
        self.filter.save()

    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.filter.get_stats()


# 全局去重器实例
article_deduplicator = ArticleDeduplicator()
comment_deduplicator = CommentDeduplicator()


def check_duplicate_article(article_id: str, content: str = None) -> bool:
    """便捷函数：检查文章是否重复"""
    return article_deduplicator.is_duplicate(article_id, content)


def add_article_to_filter(article_id: str, content: str = None) -> None:
    """便捷函数：添加文章到去重集合"""
    article_deduplicator.add(article_id, content)


def check_duplicate_comment(comment_id: str, article_id: str) -> bool:
    """便捷函数：检查评论是否重复"""
    return comment_deduplicator.is_duplicate(comment_id, article_id)


def add_comment_to_filter(comment_id: str, article_id: str) -> None:
    """便捷函数：添加评论到去重集合"""
    comment_deduplicator.add(comment_id, article_id)


def save_deduplicators() -> None:
    """保存所有去重器状态"""
    article_deduplicator.save()
    comment_deduplicator.save()
    logger.info("去重器状态已保存")


def get_deduplicator_stats() -> dict:
    """获取所有去重器统计"""
    return {
        "articles": article_deduplicator.get_stats(),
        "comments": comment_deduplicator.get_stats(),
    }
