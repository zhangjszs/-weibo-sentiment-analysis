#!/usr/bin/env python3
"""
多平台数据模型
统一管理不同平台的数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class Platform(Enum):
    """平台枚举"""

    WEIBO = "weibo"
    WECHAT = "wechat"
    DOUYIN = "douyin"
    KUAISHOU = "kuaishou"
    ZHIHU = "zhihu"
    BILIBILI = "bilibili"


class ContentType(Enum):
    """内容类型"""

    POST = "post"
    VIDEO = "video"
    COMMENT = "comment"
    REPOST = "repost"
    ARTICLE = "article"


@dataclass
class PlatformContent:
    """统一内容数据模型"""

    platform: Platform
    content_id: str
    content_type: ContentType
    author_id: str
    author_name: str
    author_followers: int = 0
    author_verified: bool = False

    content: str = ""
    media_urls: List[str] = field(default_factory=list)

    like_count: int = 0
    comment_count: int = 0
    repost_count: int = 0
    view_count: int = 0

    published_at: Optional[datetime] = None
    collected_at: datetime = field(default_factory=datetime.now)

    keywords: List[str] = field(default_factory=list)
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None

    location: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    raw_data: Dict[str, Any] = field(default_factory=dict)

    parent_id: Optional[str] = None
    root_id: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "platform": self.platform.value,
            "content_id": self.content_id,
            "content_type": self.content_type.value,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "author_followers": self.author_followers,
            "author_verified": self.author_verified,
            "content": self.content,
            "media_urls": self.media_urls,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "repost_count": self.repost_count,
            "view_count": self.view_count,
            "published_at": self.published_at.isoformat()
            if self.published_at
            else None,
            "collected_at": self.collected_at.isoformat(),
            "keywords": self.keywords,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "location": self.location,
            "tags": self.tags,
            "parent_id": self.parent_id,
            "root_id": self.root_id,
        }

    @classmethod
    def from_weibo(cls, data: Dict) -> "PlatformContent":
        """从微博数据转换"""
        return cls(
            platform=Platform.WEIBO,
            content_id=str(data.get("id", "")),
            content_type=ContentType.POST,
            author_id=str(data.get("user_id", "")),
            author_name=data.get("username", ""),
            author_followers=data.get("followers_count", 0),
            author_verified=data.get("verified", False),
            content=data.get("content", ""),
            media_urls=data.get("pics", []),
            like_count=data.get("like_count", 0),
            comment_count=data.get("comment_count", 0),
            repost_count=data.get("repost_count", 0),
            view_count=data.get("attitudes_count", 0),
            published_at=data.get("created_at"),
            keywords=data.get("keywords", []),
            sentiment_score=data.get("sentiment_score"),
            location=data.get("location"),
            tags=data.get("tags", []),
            parent_id=data.get("parent_id"),
            raw_data=data,
        )

    @classmethod
    def from_wechat(cls, data: Dict) -> "PlatformContent":
        """从微信数据转换"""
        return cls(
            platform=Platform.WECHAT,
            content_id=data.get("msg_id", ""),
            content_type=ContentType.POST,
            author_id=data.get("account_id", ""),
            author_name=data.get("account_name", ""),
            author_followers=data.get("read_count", 0),
            content=data.get("content", ""),
            media_urls=data.get("img_urls", []),
            like_count=data.get("like_count", 0),
            comment_count=data.get("comment_count", 0),
            view_count=data.get("read_count", 0),
            published_at=data.get("publish_time"),
            keywords=data.get("keywords", []),
            tags=data.get("source", []),
            raw_data=data,
        )

    @classmethod
    def from_douyin(cls, data: Dict) -> "PlatformContent":
        """从抖音数据转换"""
        return cls(
            platform=Platform.DOUYIN,
            content_id=data.get("aweme_id", ""),
            content_type=ContentType.VIDEO,
            author_id=str(data.get("author_id", "")),
            author_name=data.get("nickname", ""),
            author_followers=data.get("follower_count", 0),
            author_verified=data.get("verified", False),
            content=data.get("desc", ""),
            media_urls=[data.get("video_url", "")],
            like_count=data.get("digg_count", 0),
            comment_count=data.get("comment_count", 0),
            repost_count=data.get("share_count", 0),
            view_count=data.get("play_count", 0),
            published_at=data.get("create_time"),
            keywords=data.get("keywords", []),
            location=data.get("location"),
            raw_data=data,
        )

    @classmethod
    def from_zhihu(cls, data: Dict) -> "PlatformContent":
        """从知乎数据转换"""
        return cls(
            platform=Platform.ZHIHU,
            content_id=data.get("id", ""),
            content_type=ContentType.ARTICLE
            if data.get("type") == "article"
            else ContentType.POST,
            author_id=data.get("author_id", ""),
            author_name=data.get("author_name", ""),
            author_followers=data.get("follower_count", 0),
            author_verified=data.get("is_verified", False),
            content=data.get("content", data.get("excerpt", "")),
            like_count=data.get("voteup_count", 0),
            comment_count=data.get("comment_count", 0),
            published_at=data.get("created_time"),
            keywords=data.get("keywords", []),
            tags=data.get("tags", []),
            raw_data=data,
        )


@dataclass
class PlatformStats:
    """平台统计数据"""

    platform: Platform
    total_content: int = 0
    total_users: int = 0
    total_interactions: int = 0
    positive_ratio: float = 0.0
    negative_ratio: float = 0.0
    neutral_ratio: float = 0.0

    top_keywords: List[Dict[str, Any]] = field(default_factory=list)
    top_users: List[Dict[str, Any]] = field(default_factory=list)

    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "platform": self.platform.value,
            "total_content": self.total_content,
            "total_users": self.total_users,
            "total_interactions": self.total_interactions,
            "positive_ratio": round(self.positive_ratio, 4),
            "negative_ratio": round(self.negative_ratio, 4),
            "neutral_ratio": round(self.neutral_ratio, 4),
            "top_keywords": self.top_keywords,
            "top_users": self.top_users,
            "updated_at": self.updated_at.isoformat(),
        }


class PlatformRegistry:
    """平台注册表"""

    _platforms: Dict[str, Dict] = {}

    @classmethod
    def register(cls, platform: Platform, name: str, enabled: bool = True):
        """注册平台"""
        cls._platforms[platform.value] = {
            "platform": platform,
            "name": name,
            "enabled": enabled,
        }

    @classmethod
    def get_platform(cls, platform: str) -> Optional[Platform]:
        """获取平台枚举"""
        try:
            return Platform(platform)
        except ValueError:
            return None

    @classmethod
    def list_platforms(cls, enabled_only: bool = True) -> List[Dict]:
        """列出所有平台"""
        platforms = cls._platforms.values()
        if enabled_only:
            platforms = [p for p in platforms if p["enabled"]]
        return platforms

    @classmethod
    def is_enabled(cls, platform: str) -> bool:
        """检查平台是否启用"""
        return cls._platforms.get(platform, {}).get("enabled", False)


PlatformRegistry.register(Platform.WEIBO, "微博", enabled=True)
PlatformRegistry.register(Platform.WECHAT, "微信公众号", enabled=True)
PlatformRegistry.register(Platform.DOUYIN, "抖音", enabled=True)
PlatformRegistry.register(Platform.KUAISHOU, "快手", enabled=False)
PlatformRegistry.register(Platform.ZHIHU, "知乎", enabled=True)
PlatformRegistry.register(Platform.BILIBILI, "B站", enabled=False)
