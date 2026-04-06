#!/usr/bin/env python3
"""
多平台数据采集器基类
定义统一的采集接口和数据模型
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Platform(Enum):
    """支持的平台类型"""
    WEIBO = "weibo"
    WECHAT = "wechat"
    DOUYIN = "douyin"
    ZHIHU = "zhihu"
    BILIBILI = "bilibili"
    KUAISHOU = "kuaishou"


class ContentType(Enum):
    """内容类型"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    ARTICLE = "article"
    ANSWER = "answer"


@dataclass
class PlatformContent:
    """平台内容数据模型"""
    platform: Platform
    content_id: str
    content_type: ContentType
    author_id: str
    author_name: str
    content: str
    like_count: int = 0
    comment_count: int = 0
    repost_count: int = 0
    view_count: int = 0
    created_at: Optional[datetime] = None
    url: str = ""
    keywords: List[str] = field(default_factory=list)
    sentiment: str = "neutral"
    sentiment_score: float = 0.5
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "platform": self.platform.value,
            "content_id": self.content_id,
            "content_type": self.content_type.value,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "content": self.content,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "repost_count": self.repost_count,
            "view_count": self.view_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "url": self.url,
            "keywords": self.keywords,
            "sentiment": self.sentiment,
            "sentiment_score": self.sentiment_score,
        }

    @classmethod
    def from_wechat(cls, raw: Dict[str, Any]) -> "PlatformContent":
        """从微信公众号数据创建"""
        return cls(
            platform=Platform.WECHAT,
            content_id=raw.get("msg_link", ""),
            content_type=ContentType.ARTICLE,
            author_id=raw.get("nickname", ""),
            author_name=raw.get("nickname", ""),
            content=raw.get("title", ""),
            like_count=raw.get("like_num", 0),
            view_count=raw.get("view_num", 0),
            url=raw.get("msg_link", ""),
            raw_data=raw,
        )

    @classmethod
    def from_douyin(cls, raw: Dict[str, Any]) -> "PlatformContent":
        """从抖音数据创建"""
        stats = raw.get("statistics", {})
        return cls(
            platform=Platform.DOUYIN,
            content_id=raw.get("aweme_id", ""),
            content_type=ContentType.VIDEO,
            author_id=str(raw.get("author", {}).get("uid", "")),
            author_name=raw.get("author", {}).get("nickname", ""),
            content=raw.get("desc", ""),
            like_count=stats.get("digg_count", 0),
            comment_count=stats.get("comment_count", 0),
            repost_count=stats.get("share_count", 0),
            view_count=stats.get("play_count", 0),
            raw_data=raw,
        )

    @classmethod
    def from_zhihu(cls, raw: Dict[str, Any]) -> "PlatformContent":
        """从知乎数据创建"""
        return cls(
            platform=Platform.ZHIHU,
            content_id=str(raw.get("id", "")),
            content_type=ContentType.ANSWER,
            author_id=str(raw.get("author", {}).get("id", "")),
            author_name=raw.get("author", {}).get("name", ""),
            content=raw.get("excerpt", ""),
            like_count=raw.get("voteup_count", 0),
            comment_count=raw.get("comment_count", 0),
            view_count=raw.get("view_count", 0),
            url=raw.get("url", ""),
            raw_data=raw,
        )

    @classmethod
    def from_bilibili(cls, raw: Dict[str, Any]) -> "PlatformContent":
        """从B站数据创建"""
        stat = raw.get("stat", {})
        return cls(
            platform=Platform.BILIBILI,
            content_id=raw.get("bvid", ""),
            content_type=ContentType.VIDEO,
            author_id=str(raw.get("owner", {}).get("mid", "")),
            author_name=raw.get("owner", {}).get("name", ""),
            content=raw.get("title", ""),
            like_count=stat.get("like", 0),
            comment_count=stat.get("reply", 0),
            repost_count=stat.get("share", 0),
            view_count=stat.get("view", 0),
            url=f"https://www.bilibili.com/video/{raw.get('bvid', '')}",
            raw_data=raw,
        )


class BasePlatformCollector(ABC):
    """平台采集器基类"""

    def __init__(self):
        self.session = None
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def platform(self) -> Platform:
        """返回平台类型"""
        raise NotImplementedError

    @abstractmethod
    def parse(self, raw: Dict[str, Any]) -> PlatformContent:
        """解析原始数据为统一格式"""
        raise NotImplementedError

    def collect(self, keyword: str, limit: int = 20) -> List[PlatformContent]:
        """
        采集数据
        
        Args:
            keyword: 搜索关键词
            limit: 限制数量
            
        Returns:
            List[PlatformContent]: 采集到的内容列表
        """
        try:
            raw_data = self._fetch_data(keyword, limit)
            results = []
            for item in raw_data:
                try:
                    parsed = self.parse(item)
                    results.append(parsed)
                except Exception as e:
                    self.logger.warning(f"解析数据失败: {e}")
            return results
        except NotImplementedError:
            # 如果 _fetch_data 未实现，返回模拟数据
            self.logger.info(f"[{self.platform.value}] 使用模拟数据")
            return self._generate_demo_data(keyword, limit)
        except Exception as e:
            self.logger.error(f"采集失败: {e}")
            return []

    def _fetch_data(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """
        获取原始数据（子类必须实现或使用模拟数据）
        
        Raises:
            NotImplementedError: 如果未实现则使用模拟数据
        """
        raise NotImplementedError

    def _generate_demo_data(self, keyword: str, limit: int) -> List[PlatformContent]:
        """生成模拟数据（用于演示）"""
        from datetime import datetime, timedelta
        import random

        results = []
        topics = [
            "人工智能", "科技创新", "新能源", "数字经济",
            "绿色发展", "智慧城市", "乡村振兴", "教育改革"
        ]
        
        base_time = datetime.now() - timedelta(days=7)
        
        for i in range(min(limit, 20)):
            topic = random.choice(topics)
            results.append(PlatformContent(
                platform=self.platform,
                content_id=f"demo_{i}_{int(datetime.now().timestamp())}",
                content_type=ContentType.TEXT,
                author_id=f"user_{i}",
                author_name=f"用户{i}",
                content=f"关于{keyword}和{topic}的讨论内容...",
                like_count=random.randint(0, 1000),
                comment_count=random.randint(0, 100),
                repost_count=random.randint(0, 50),
                view_count=random.randint(100, 10000),
                created_at=base_time + timedelta(hours=i),
                keywords=[keyword, topic],
            ))
        
        return results
