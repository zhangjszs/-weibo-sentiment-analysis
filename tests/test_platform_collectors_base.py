#!/usr/bin/env python3
"""
平台采集器基类单元测试
覆盖范围（base.py）：
- PlatformContent.to_dict()（58-74，含 created_at 有/无分支）
- PlatformContent.from_wechat()（79-90）
- PlatformContent.from_douyin()（95-108，嵌套 statistics/author）
- PlatformContent.from_bilibili()（130-144，嵌套 stat/owner + url 构造）
- PlatformContent.from_zhihu()（113-125，补全模型测试）
- BasePlatformCollector 基类默认行为（176-233）：
  * collect 走 _fetch_data → parse 成功路径
  * collect parse 失败跳过
  * collect _fetch_data 抛 NotImplementedError → 基类 _generate_demo_data
  * collect _fetch_data 抛其他异常 → 返回空列表
  * 基类 _fetch_data 默认抛 NotImplementedError
  * 基类 _generate_demo_data 结构 + limit 截断为 20

注：所有具体采集器（wechat/douyin/bilibili/zhihu）都重写了 _fetch_data 与
_generate_demo_data，因此基类版本此前从未被执行，本文件用一个最小可实例化
子类 _MinimalCollector 来触发基类默认实现。
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from services.platform_collectors import (
    BasePlatformCollector,
    ContentType,
    Platform,
    PlatformContent,
)


class _MinimalCollector(BasePlatformCollector):
    """最小可实例化子类，用于测试基类默认行为（不重写 _fetch_data/_generate_demo_data）"""

    @property
    def platform(self) -> Platform:
        return Platform.WEIBO

    def parse(self, raw):
        return PlatformContent.from_wechat(raw)


# ----------------------------------------------------------------------
# PlatformContent.to_dict()
# ----------------------------------------------------------------------


class TestPlatformContentToDict:
    """测试 to_dict()（base.py 56-74）"""

    def test_to_dict_with_created_at(self):
        """created_at 有值时应输出 isoformat 字符串"""
        content = PlatformContent(
            platform=Platform.WECHAT,
            content_id="id1",
            content_type=ContentType.ARTICLE,
            author_id="aid",
            author_name="aname",
            content="content",
            like_count=10,
            comment_count=2,
            repost_count=3,
            view_count=100,
            created_at=datetime(2026, 7, 29, 10, 30),
            url="http://x",
            keywords=["k1", "k2"],
            sentiment="positive",
            sentiment_score=0.8,
        )
        d = content.to_dict()
        assert d["platform"] == "wechat"
        assert d["content_id"] == "id1"
        assert d["content_type"] == "article"
        assert d["author_id"] == "aid"
        assert d["author_name"] == "aname"
        assert d["content"] == "content"
        assert d["like_count"] == 10
        assert d["comment_count"] == 2
        assert d["repost_count"] == 3
        assert d["view_count"] == 100
        assert d["created_at"] == "2026-07-29T10:30:00"
        assert d["url"] == "http://x"
        assert d["keywords"] == ["k1", "k2"]
        assert d["sentiment"] == "positive"
        assert d["sentiment_score"] == 0.8

    def test_to_dict_without_created_at(self):
        """created_at 为 None 时应输出 None"""
        content = PlatformContent(
            platform=Platform.WECHAT,
            content_id="id1",
            content_type=ContentType.ARTICLE,
            author_id="aid",
            author_name="aname",
            content="content",
        )
        d = content.to_dict()
        assert d["created_at"] is None


# ----------------------------------------------------------------------
# PlatformContent.from_wechat()
# ----------------------------------------------------------------------


class TestFromWechat:
    """测试 from_wechat()（base.py 76-90）"""

    def test_full_data(self):
        raw = {
            "msg_link": "http://mp.weixin.qq.com/s/1",
            "nickname": "科技前沿",
            "title": "深度分析",
            "like_num": 100,
            "view_num": 5000,
        }
        c = PlatformContent.from_wechat(raw)
        assert c.platform is Platform.WECHAT
        assert c.content_id == "http://mp.weixin.qq.com/s/1"
        assert c.content_type is ContentType.ARTICLE
        assert c.author_id == "科技前沿"
        assert c.author_name == "科技前沿"
        assert c.content == "深度分析"
        assert c.like_count == 100
        assert c.view_count == 5000
        assert c.url == "http://mp.weixin.qq.com/s/1"
        assert c.raw_data is raw

    def test_empty_dict_defaults(self):
        c = PlatformContent.from_wechat({})
        assert c.content_id == ""
        assert c.author_id == ""
        assert c.author_name == ""
        assert c.content == ""
        assert c.like_count == 0
        assert c.view_count == 0
        assert c.url == ""


# ----------------------------------------------------------------------
# PlatformContent.from_douyin()
# ----------------------------------------------------------------------


class TestFromDouyin:
    """测试 from_douyin()（base.py 92-108）"""

    def test_full_data(self):
        raw = {
            "aweme_id": "7012345",
            "author": {"uid": "uid1", "nickname": "科技达人"},
            "desc": "测试视频",
            "statistics": {
                "digg_count": 1000,
                "comment_count": 100,
                "share_count": 50,
                "play_count": 10000,
            },
        }
        c = PlatformContent.from_douyin(raw)
        assert c.platform is Platform.DOUYIN
        assert c.content_id == "7012345"
        assert c.content_type is ContentType.VIDEO
        assert c.author_id == "uid1"
        assert c.author_name == "科技达人"
        assert c.content == "测试视频"
        assert c.like_count == 1000
        assert c.comment_count == 100
        assert c.repost_count == 50
        assert c.view_count == 10000
        assert c.raw_data is raw

    def test_empty_dict_defaults(self):
        c = PlatformContent.from_douyin({})
        assert c.content_id == ""
        assert c.author_id == ""
        assert c.author_name == ""
        assert c.content == ""
        assert c.like_count == 0
        assert c.comment_count == 0
        assert c.repost_count == 0
        assert c.view_count == 0


# ----------------------------------------------------------------------
# PlatformContent.from_bilibili()
# ----------------------------------------------------------------------


class TestFromBilibili:
    """测试 from_bilibili()（base.py 127-144）"""

    def test_full_data(self):
        raw = {
            "bvid": "BV1xx411x7",
            "owner": {"mid": 123, "name": "科技美学"},
            "title": "测试视频",
            "stat": {
                "like": 5000,
                "reply": 200,
                "share": 100,
                "view": 50000,
            },
        }
        c = PlatformContent.from_bilibili(raw)
        assert c.platform is Platform.BILIBILI
        assert c.content_id == "BV1xx411x7"
        assert c.content_type is ContentType.VIDEO
        assert c.author_id == "123"  # str(mid)
        assert c.author_name == "科技美学"
        assert c.content == "测试视频"
        assert c.like_count == 5000
        assert c.comment_count == 200
        assert c.repost_count == 100
        assert c.view_count == 50000
        assert c.url == "https://www.bilibili.com/video/BV1xx411x7"
        assert c.raw_data is raw

    def test_empty_dict_defaults(self):
        c = PlatformContent.from_bilibili({})
        assert c.content_id == ""
        assert c.author_id == ""
        assert c.author_name == ""
        assert c.content == ""
        assert c.like_count == 0
        assert c.url == "https://www.bilibili.com/video/"


# ----------------------------------------------------------------------
# PlatformContent.from_zhihu()（补全模型测试）
# ----------------------------------------------------------------------


class TestFromZhihu:
    """测试 from_zhihu()（base.py 110-125）"""

    def test_full_data(self):
        raw = {
            "id": 123,
            "author": {"id": "uid1", "name": "作者A"},
            "excerpt": "摘要",
            "voteup_count": 100,
            "comment_count": 10,
            "view_count": 1000,
            "url": "http://zhihu.com/answer/123",
        }
        c = PlatformContent.from_zhihu(raw)
        assert c.platform is Platform.ZHIHU
        assert c.content_id == "123"  # str(id)
        assert c.content_type is ContentType.ANSWER
        assert c.author_id == "uid1"
        assert c.author_name == "作者A"
        assert c.content == "摘要"
        assert c.like_count == 100
        assert c.comment_count == 10
        assert c.view_count == 1000
        assert c.url == "http://zhihu.com/answer/123"
        assert c.raw_data is raw

    def test_empty_dict_defaults(self):
        c = PlatformContent.from_zhihu({})
        assert c.content_id == ""
        assert c.author_id == ""
        assert c.author_name == ""
        assert c.content == ""
        assert c.like_count == 0


# ----------------------------------------------------------------------
# BasePlatformCollector 基类默认行为
# ----------------------------------------------------------------------


class TestBasePlatformCollectorInit:
    """测试 BasePlatformCollector.__init__（base.py 150-152）"""

    def test_init_sets_session_and_logger(self):
        c = _MinimalCollector()
        assert c.session is None
        assert c.logger is not None
        assert c.logger.name == "_MinimalCollector"

    def test_platform_property(self):
        c = _MinimalCollector()
        assert c.platform is Platform.WEIBO


class TestBaseFetchData:
    """测试基类 _fetch_data 默认实现（base.py 194-201）"""

    def test_base_fetch_data_raises_not_implemented(self):
        c = _MinimalCollector()
        with pytest.raises(NotImplementedError):
            c._fetch_data("kw", 5)


class TestBaseGenerateDemoData:
    """测试基类 _generate_demo_data（base.py 203-233）"""

    def test_demo_data_structure(self):
        c = _MinimalCollector()
        results = c._generate_demo_data("AI", limit=5)
        assert len(results) == 5
        for r in results:
            assert r.platform is Platform.WEIBO
            assert r.content_type is ContentType.TEXT  # 基类用 TEXT
            assert r.content_id.startswith("demo_")
            assert "AI" in r.keywords
            assert r.author_id.startswith("user_")
            assert r.created_at is not None

    def test_demo_data_capped_at_20(self):
        """limit 超过 20 应被截断"""
        c = _MinimalCollector()
        results = c._generate_demo_data("AI", limit=50)
        assert len(results) == 20

    def test_demo_data_limit_zero(self):
        c = _MinimalCollector()
        assert c._generate_demo_data("AI", limit=0) == []


class TestBaseCollect:
    """测试基类 collect() 编排（base.py 165-192）"""

    def test_collect_falls_back_to_base_demo_data(self):
        """_fetch_data 抛 NotImplementedError 时回退到基类 _generate_demo_data（186-189, 205-233）"""
        c = _MinimalCollector()
        results = c.collect("AI", limit=5)
        assert len(results) == 5
        # 基类 _generate_demo_data 生成 TEXT 类型
        assert all(r.content_type is ContentType.TEXT for r in results)
        assert all(r.platform is Platform.WEIBO for r in results)

    def test_collect_with_fetch_data_success(self, monkeypatch):
        """_fetch_data 返回数据时走 parse 路径（176-185）"""
        c = _MinimalCollector()
        raw = {"msg_link": "link1", "nickname": "作者", "title": "标题", "like_num": 5}
        monkeypatch.setattr(c, "_fetch_data", lambda k, l: [raw])
        results = c.collect("kw", 5)
        assert len(results) == 1
        assert results[0].author_name == "作者"
        assert results[0].content == "标题"
        assert results[0].like_count == 5

    def test_collect_skips_parse_failure(self, monkeypatch):
        """parse 失败的条目应被跳过（183-184）"""
        c = _MinimalCollector()
        good = PlatformContent.from_wechat({"nickname": "ok"})
        with patch.object(c, "parse", side_effect=[ValueError("bad"), good]):
            with patch.object(c, "_fetch_data", return_value=[{"i": 1}, {"i": 2}]):
                results = c.collect("kw", 5)
        assert len(results) == 1
        assert results[0] is good

    def test_collect_returns_empty_on_other_exception(self, monkeypatch):
        """_fetch_data 抛非 NotImplementedError 异常时返回空列表（190-192）"""
        c = _MinimalCollector()

        def boom(keyword, limit):
            raise ValueError("network down")

        monkeypatch.setattr(c, "_fetch_data", boom)
        assert c.collect("kw", 5) == []

    def test_collect_empty_raw_data(self, monkeypatch):
        """_fetch_data 返回空列表 → collect 返回空列表"""
        c = _MinimalCollector()
        monkeypatch.setattr(c, "_fetch_data", lambda k, l: [])
        assert c.collect("kw", 5) == []


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
