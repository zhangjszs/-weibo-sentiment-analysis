#!/usr/bin/env python3
"""
平台采集器测试
"""

import pytest

from src.services.platform_collectors import (
    BilibiliCollector,
    DouyinCollector,
    Platform,
    PlatformCollectorFactory,
    WechatCollector,
    ZhihuCollector,
)


class TestPlatformCollectorFactory:
    """测试采集器工厂"""

    def test_get_supported_platforms(self):
        """测试获取支持的平台列表"""
        platforms = PlatformCollectorFactory.list_supported()
        assert len(platforms) > 0
        assert Platform.WECHAT in platforms

    def test_get_collector(self):
        """测试获取采集器实例"""
        collector = PlatformCollectorFactory.get(Platform.WECHAT)
        assert collector is not None
        assert isinstance(collector, WechatCollector)

    def test_get_collector_by_string(self):
        """测试通过字符串获取采集器"""
        collector = PlatformCollectorFactory.get("wechat")
        assert collector is not None

    def test_get_unsupported_platform(self):
        """测试获取不支持的平台"""
        collector = PlatformCollectorFactory.get("unsupported")
        assert collector is None

    def test_is_supported(self):
        """测试平台支持检查"""
        assert PlatformCollectorFactory.is_supported("wechat") is True
        assert PlatformCollectorFactory.is_supported("unsupported") is False


class TestWechatCollector:
    """测试微信采集器"""

    def test_platform_property(self):
        """测试平台属性"""
        collector = WechatCollector()
        assert collector.platform == Platform.WECHAT

    def test_collect_returns_data(self):
        """测试采集返回数据"""
        collector = WechatCollector()
        results = collector.collect("科技", limit=5)
        assert isinstance(results, list)
        assert len(results) > 0
        # 验证数据格式
        for item in results:
            assert item.platform == Platform.WECHAT
            assert item.content_id
            assert item.author_name


class TestDouyinCollector:
    """测试抖音采集器"""

    def test_platform_property(self):
        """测试平台属性"""
        collector = DouyinCollector()
        assert collector.platform == Platform.DOUYIN

    def test_collect_returns_data(self):
        """测试采集返回数据"""
        collector = DouyinCollector()
        results = collector.collect("科技", limit=5)
        assert isinstance(results, list)
        assert len(results) > 0


class TestZhihuCollector:
    """测试知乎采集器"""

    def test_platform_property(self):
        """测试平台属性"""
        collector = ZhihuCollector()
        assert collector.platform == Platform.ZHIHU

    def test_collect_returns_data(self):
        """测试采集返回数据"""
        collector = ZhihuCollector()
        results = collector.collect("科技", limit=5)
        assert isinstance(results, list)
        assert len(results) > 0


class TestBilibiliCollector:
    """测试B站采集器"""

    def test_platform_property(self):
        """测试平台属性"""
        collector = BilibiliCollector()
        assert collector.platform == Platform.BILIBILI

    def test_collect_returns_data(self):
        """测试采集返回数据"""
        collector = BilibiliCollector()
        results = collector.collect("科技", limit=5)
        assert isinstance(results, list)
        assert len(results) > 0
