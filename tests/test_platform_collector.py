# tests/test_platform_collector.py
"""
TDD: 多平台数据采集器
"""

import pytest

from models.platform import ContentType, Platform, PlatformContent
from services.platform_collector import (
    BasePlatformCollector,
    BilibiliCollector,
    DouyinCollector,
    PlatformCollectorFactory,
    WechatCollector,
    ZhihuCollector,
)

# --- BasePlatformCollector ---


def test_base_collector_is_abstract():
    with pytest.raises(TypeError):
        BasePlatformCollector()


# --- WechatCollector ---


def test_wechat_collector_platform():
    c = WechatCollector()
    assert c.platform == Platform.WECHAT


def test_wechat_collector_parse_returns_platform_content():
    c = WechatCollector()
    raw = {
        "msg_id": "wx001",
        "account_id": "acc1",
        "account_name": "测试公众号",
        "content": "这是一篇测试文章",
        "read_count": 1000,
        "like_count": 50,
        "comment_count": 10,
    }
    result = c.parse(raw)
    assert isinstance(result, PlatformContent)
    assert result.platform == Platform.WECHAT
    assert result.content_id == "wx001"
    assert result.content == "这是一篇测试文章"


def test_wechat_collector_parse_missing_fields():
    c = WechatCollector()
    result = c.parse({})
    assert isinstance(result, PlatformContent)
    assert result.platform == Platform.WECHAT


# --- DouyinCollector ---


def test_douyin_collector_platform():
    c = DouyinCollector()
    assert c.platform == Platform.DOUYIN


def test_douyin_collector_parse_returns_platform_content():
    c = DouyinCollector()
    raw = {
        "aweme_id": "dy001",
        "author_id": "user1",
        "nickname": "测试用户",
        "desc": "测试视频描述",
        "digg_count": 5000,
        "comment_count": 200,
        "share_count": 100,
        "play_count": 50000,
    }
    result = c.parse(raw)
    assert isinstance(result, PlatformContent)
    assert result.platform == Platform.DOUYIN
    assert result.content_id == "dy001"
    assert result.content_type == ContentType.VIDEO


# --- ZhihuCollector ---


def test_zhihu_collector_platform():
    c = ZhihuCollector()
    assert c.platform == Platform.ZHIHU


def test_zhihu_collector_parse_answer():
    c = ZhihuCollector()
    raw = {
        "id": "zh001",
        "author_id": "user1",
        "author_name": "知乎用户",
        "content": "这是一个回答",
        "voteup_count": 300,
        "comment_count": 20,
        "type": "answer",
    }
    result = c.parse(raw)
    assert isinstance(result, PlatformContent)
    assert result.platform == Platform.ZHIHU
    assert result.content_type == ContentType.POST


def test_zhihu_collector_parse_article():
    c = ZhihuCollector()
    raw = {
        "id": "zh002",
        "author_id": "user2",
        "author_name": "知乎作者",
        "content": "这是一篇文章",
        "voteup_count": 1000,
        "type": "article",
    }
    result = c.parse(raw)
    assert result.content_type == ContentType.ARTICLE


# --- BilibiliCollector ---


def test_bilibili_collector_platform():
    c = BilibiliCollector()
    assert c.platform == Platform.BILIBILI


def test_bilibili_collector_parse_returns_platform_content():
    c = BilibiliCollector()
    raw = {
        "bvid": "BV001",
        "mid": "user1",
        "author": "UP主",
        "title": "测试视频",
        "desc": "视频描述",
        "like": 2000,
        "reply": 500,
        "share": 300,
        "view": 100000,
    }
    result = c.parse(raw)
    assert isinstance(result, PlatformContent)
    assert result.platform == Platform.BILIBILI
    assert result.content_id == "BV001"
    assert result.content_type == ContentType.VIDEO


# --- PlatformCollectorFactory ---


def test_factory_get_wechat():
    c = PlatformCollectorFactory.get(Platform.WECHAT)
    assert isinstance(c, WechatCollector)


def test_factory_get_douyin():
    c = PlatformCollectorFactory.get(Platform.DOUYIN)
    assert isinstance(c, DouyinCollector)


def test_factory_get_zhihu():
    c = PlatformCollectorFactory.get(Platform.ZHIHU)
    assert isinstance(c, ZhihuCollector)


def test_factory_get_bilibili():
    c = PlatformCollectorFactory.get(Platform.BILIBILI)
    assert isinstance(c, BilibiliCollector)


def test_factory_get_unknown_raises():
    with pytest.raises(ValueError):
        PlatformCollectorFactory.get("unknown_platform")


def test_factory_list_supported():
    supported = PlatformCollectorFactory.list_supported()
    assert Platform.WECHAT in supported
    assert Platform.DOUYIN in supported
    assert Platform.ZHIHU in supported
    assert Platform.BILIBILI in supported
