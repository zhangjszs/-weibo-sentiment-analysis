#!/usr/bin/env python3
"""
平台采集器工厂
统一管理各平台采集器的创建和获取
"""

import logging
from typing import Dict, List, Optional, Type

from .base import BasePlatformCollector, Platform
from .bilibili import BilibiliCollector
from .douyin import DouyinCollector
from .wechat import WechatCollector
from .zhihu import ZhihuCollector

logger = logging.getLogger(__name__)


class PlatformCollectorFactory:
    """平台采集器工厂"""

    _registry: Dict[Platform, Type[BasePlatformCollector]] = {
        Platform.WECHAT: WechatCollector,
        Platform.DOUYIN: DouyinCollector,
        Platform.ZHIHU: ZhihuCollector,
        Platform.BILIBILI: BilibiliCollector,
    }

    @classmethod
    def get(cls, platform: Platform | str) -> Optional[BasePlatformCollector]:
        """
        获取采集器实例

        Args:
            platform: 平台类型或平台ID字符串

        Returns:
            Optional[BasePlatformCollector]: 采集器实例，不支持的平台返回None
        """
        if isinstance(platform, str):
            try:
                platform = Platform(platform.lower())
            except ValueError:
                logger.warning(f"不支持的平台: {platform}")
                return None

        collector_cls = cls._registry.get(platform)
        if collector_cls is None:
            logger.warning(f"未找到平台 {platform.value} 的采集器")
            return None

        return collector_cls()

    @classmethod
    def list_supported(cls) -> List[Platform]:
        """
        获取支持的平台列表

        Returns:
            List[Platform]: 支持的平台列表
        """
        return list(cls._registry.keys())

    @classmethod
    def list_supported_ids(cls) -> List[str]:
        """
        获取支持的平台ID列表

        Returns:
            List[str]: 平台ID字符串列表
        """
        return [p.value for p in cls._registry.keys()]

    @classmethod
    def register(cls, platform: Platform, collector_class: Type[BasePlatformCollector]):
        """
        注册新的采集器

        Args:
            platform: 平台类型
            collector_class: 采集器类
        """
        cls._registry[platform] = collector_class
        logger.info(f"注册平台采集器: {platform.value}")

    @classmethod
    def is_supported(cls, platform: Platform | str) -> bool:
        """
        检查平台是否受支持

        Args:
            platform: 平台类型或ID

        Returns:
            bool: 是否支持
        """
        if isinstance(platform, str):
            try:
                platform = Platform(platform.lower())
            except ValueError:
                return False
        return platform in cls._registry

    @classmethod
    def get_platform_info(cls) -> List[Dict]:
        """
        获取所有支持的平台信息

        Returns:
            List[Dict]: 平台信息列表
        """
        platform_info = {
            Platform.WECHAT: {"name": "微信公众号", "icon": "💬", "enabled": True},
            Platform.DOUYIN: {"name": "抖音", "icon": "🎵", "enabled": True},
            Platform.ZHIHU: {"name": "知乎", "icon": "💡", "enabled": True},
            Platform.BILIBILI: {"name": "B站", "icon": "📺", "enabled": False},
        }

        results = []
        for platform in cls._registry.keys():
            info = platform_info.get(platform, {"name": platform.value, "icon": "📱", "enabled": False})
            results.append({
                "id": platform.value,
                **info,
            })

        return results

    @classmethod
    def collect_all(
        cls,
        keyword: str,
        platforms: Optional[List[Platform | str]] = None,
        limit: int = 20,
    ) -> Dict[str, List]:
        """
        从多个平台采集数据

        Args:
            keyword: 搜索关键词
            platforms: 平台列表，None表示所有支持的平台
            limit: 每个平台采集数量

        Returns:
            Dict[str, List]: 各平台采集结果
        """
        if platforms is None:
            platforms = cls.list_supported()

        results = {}
        for platform in platforms:
            collector = cls.get(platform)
            if collector:
                platform_id = platform.value if isinstance(platform, Platform) else platform
                try:
                    data = collector.collect(keyword, limit)
                    results[platform_id] = [item.to_dict() for item in data]
                except Exception as e:
                    logger.error(f"从 {platform_id} 采集失败: {e}")
                    results[platform_id] = []
            else:
                platform_id = platform if isinstance(platform, str) else platform.value
                results[platform_id] = []

        return results
