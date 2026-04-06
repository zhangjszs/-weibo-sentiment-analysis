#!/usr/bin/env python3
"""
多平台数据采集器
支持微信公众号、抖音、知乎、B站
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List

from models.platform import ContentType, Platform, PlatformContent

logger = logging.getLogger(__name__)


class BasePlatformCollector(ABC):
    """平台采集器基类"""

    @property
    @abstractmethod
    def platform(self) -> Platform:
        raise NotImplementedError

    @abstractmethod
    def parse(self, raw: Dict) -> PlatformContent:
        raise NotImplementedError

    def collect(self, keyword: str, limit: int = 20) -> List[PlatformContent]:
        """采集数据（子类可覆盖实现真实爬取）"""
        logger.info(f"[{self.platform.value}] 采集关键词: {keyword}, limit={limit}")
        return []


class WechatCollector(BasePlatformCollector):
    """微信公众号采集器"""

    @property
    def platform(self) -> Platform:
        return Platform.WECHAT

    def parse(self, raw: Dict) -> PlatformContent:
        return PlatformContent.from_wechat(raw)


class DouyinCollector(BasePlatformCollector):
    """抖音采集器"""

    @property
    def platform(self) -> Platform:
        return Platform.DOUYIN

    def parse(self, raw: Dict) -> PlatformContent:
        return PlatformContent.from_douyin(raw)


class ZhihuCollector(BasePlatformCollector):
    """知乎采集器"""

    @property
    def platform(self) -> Platform:
        return Platform.ZHIHU

    def parse(self, raw: Dict) -> PlatformContent:
        return PlatformContent.from_zhihu(raw)


class BilibiliCollector(BasePlatformCollector):
    """B站采集器"""

    @property
    def platform(self) -> Platform:
        return Platform.BILIBILI

    def parse(self, raw: Dict) -> PlatformContent:
        return PlatformContent(
            platform=Platform.BILIBILI,
            content_id=raw.get("bvid", ""),
            content_type=ContentType.VIDEO,
            author_id=str(raw.get("mid", "")),
            author_name=raw.get("author", ""),
            content=raw.get("desc", raw.get("title", "")),
            like_count=raw.get("like", 0),
            comment_count=raw.get("reply", 0),
            repost_count=raw.get("share", 0),
            view_count=raw.get("view", 0),
            raw_data=raw,
        )


class PlatformCollectorFactory:
    """平台采集器工厂"""

    _registry: Dict[Platform, type] = {
        Platform.WECHAT: WechatCollector,
        Platform.DOUYIN: DouyinCollector,
        Platform.ZHIHU: ZhihuCollector,
        Platform.BILIBILI: BilibiliCollector,
    }

    @classmethod
    def get(cls, platform) -> BasePlatformCollector:
        if isinstance(platform, str):
            try:
                platform = Platform(platform)
            except ValueError as err:
                raise ValueError(f"不支持的平台: {platform}") from err
        collector_cls = cls._registry.get(platform)
        if collector_cls is None:
            raise ValueError(f"不支持的平台: {platform}")
        return collector_cls()

    @classmethod
    def list_supported(cls) -> List[Platform]:
        return list(cls._registry.keys())
