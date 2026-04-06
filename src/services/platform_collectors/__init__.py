#!/usr/bin/env python3
"""
多平台数据采集器模块
支持微信公众号、抖音、知乎、B站等平台数据采集
"""

from .base import BasePlatformCollector, ContentType, Platform, PlatformContent
from .bilibili import BilibiliCollector
from .douyin import DouyinCollector
from .factory import PlatformCollectorFactory
from .wechat import WechatCollector
from .zhihu import ZhihuCollector

__all__ = [
    "BasePlatformCollector",
    "Platform",
    "ContentType",
    "PlatformContent",
    "WechatCollector",
    "DouyinCollector",
    "ZhihuCollector",
    "BilibiliCollector",
    "PlatformCollectorFactory",
]
