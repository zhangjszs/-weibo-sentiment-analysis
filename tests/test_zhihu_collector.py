#!/usr/bin/env python3
"""
知乎采集器单元测试
覆盖范围：
- platform 属性（zhihu.py 20-22）
- parse() 解析（zhihu.py 24-25，委托 PlatformContent.from_zhihu）
- _fetch_data() 全分支（zhihu.py 27-78）：
  * env 开关（未设置 / false / 其他值 / true / 大小写不敏感）
  * 200 + answer / article / 非 search_result / 非 answer-article / 空 data / 无 data 键
  * 非 200 状态码 → NotImplementedError
  * 请求异常 → NotImplementedError
- collect() 编排（base.py 165-192）：
  * 启用时走真实 fetch + parse
  * 未启用时回退模拟数据
  * _fetch_data 抛非 NotImplementedError 异常 → 返回空列表
  * parse 失败的条目被跳过
- _generate_demo_data() 模拟数据生成（zhihu.py 80-112）
"""

import pytest

pytestmark = pytest.mark.unit

from unittest.mock import MagicMock, patch

import pytest

from services.platform_collectors import (
    ContentType,
    Platform,
    PlatformContent,
    ZhihuCollector,
)


@pytest.fixture
def collector():
    return ZhihuCollector()


# 知乎搜索 API 返回的 answer object 样本
ANSWER_OBJECT = {
    "type": "answer",
    "id": 12345,
    "author": {"id": "uid-1", "name": "作者A"},
    "excerpt": "这是回答摘要",
    "voteup_count": 100,
    "comment_count": 10,
    "view_count": 1000,
    "url": "https://www.zhihu.com/answer/12345",
}

ARTICLE_OBJECT = {
    "type": "article",
    "id": 67890,
    "author": {"id": "uid-2", "name": "作者B"},
    "excerpt": "这是文章摘要",
    "voteup_count": 50,
    "comment_count": 5,
    "view_count": 500,
    "url": "https://zhuanlan.zhihu.com/p/67890",
}


def _make_response(status_code=200, data=None, raw_json=None):
    """构造 mock response"""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = raw_json if raw_json is not None else {
        "data": data if data is not None else []
    }
    return resp


class TestZhihuCollectorPlatform:
    """测试 platform 属性（zhihu.py 20-22）"""

    def test_platform_is_zhihu(self, collector):
        assert collector.platform is Platform.ZHIHU
        assert collector.platform.value == "zhihu"


class TestZhihuCollectorParse:
    """测试 parse()（zhihu.py 24-25）"""

    def test_parse_returns_platform_content(self, collector):
        content = collector.parse(ANSWER_OBJECT)
        assert isinstance(content, PlatformContent)
        assert content.platform is Platform.ZHIHU
        assert content.content_id == "12345"
        assert content.author_id == "uid-1"
        assert content.author_name == "作者A"
        assert content.content == "这是回答摘要"
        assert content.like_count == 100
        assert content.comment_count == 10
        assert content.view_count == 1000
        assert content.url == "https://www.zhihu.com/answer/12345"
        assert content.content_type is ContentType.ANSWER

    def test_parse_missing_fields_defaults(self, collector):
        """缺失字段应使用默认值"""
        content = collector.parse({})
        assert content.content_id == ""
        assert content.author_id == ""
        assert content.author_name == ""
        assert content.content == ""
        assert content.like_count == 0
        assert content.comment_count == 0
        assert content.view_count == 0

    def test_parse_preserves_raw_data(self, collector):
        content = collector.parse(ANSWER_OBJECT)
        assert content.raw_data is ANSWER_OBJECT


class TestZhihuCollectorFetchData:
    """测试 _fetch_data() 全分支（zhihu.py 27-78）"""

    def test_fetch_disabled_by_default(self, collector, monkeypatch):
        """env 未设置时默认禁用，应抛 NotImplementedError"""
        monkeypatch.delenv("ZHIHU_COLLECTOR_ENABLED", raising=False)
        with pytest.raises(NotImplementedError, match="未启用"):
            collector._fetch_data("科技", 5)

    def test_fetch_disabled_when_false(self, collector, monkeypatch):
        monkeypatch.setenv("ZHIHU_COLLECTOR_ENABLED", "false")
        with pytest.raises(NotImplementedError, match="未启用"):
            collector._fetch_data("科技", 5)

    def test_fetch_disabled_when_other_value(self, collector, monkeypatch):
        """非 'true' 的任意值都应禁用"""
        monkeypatch.setenv("ZHIHU_COLLECTOR_ENABLED", "yes")
        with pytest.raises(NotImplementedError, match="未启用"):
            collector._fetch_data("科技", 5)

    def test_fetch_enabled_returns_answer(self, collector, monkeypatch):
        """启用 + 200 + answer 类型 → 返回 object 列表"""
        monkeypatch.setenv("ZHIHU_COLLECTOR_ENABLED", "true")
        resp = _make_response(
            200, data=[{"type": "search_result", "object": ANSWER_OBJECT}]
        )
        with patch(
            "services.platform_collectors.zhihu.requests.get", return_value=resp
        ) as mock_get:
            results = collector._fetch_data("AI", 5)
        assert results == [ANSWER_OBJECT]
        # 校验请求参数
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["q"] == "AI"
        assert kwargs["params"]["limit"] == 5
        assert kwargs["params"]["t"] == "general"
        assert kwargs["timeout"] == 30
        assert "User-Agent" in kwargs["headers"]

    def test_fetch_enabled_case_insensitive(self, collector, monkeypatch):
        """'True' / 'TRUE' / 'tRuE' 大小写不敏感地启用"""
        for val in ("True", "TRUE", "tRuE"):
            monkeypatch.setenv("ZHIHU_COLLECTOR_ENABLED", val)
            resp = _make_response(
                200, data=[{"type": "search_result", "object": ANSWER_OBJECT}]
            )
            with patch(
                "services.platform_collectors.zhihu.requests.get", return_value=resp
            ):
                results = collector._fetch_data("AI", 1)
            assert results == [ANSWER_OBJECT]

    def test_fetch_enabled_returns_article(self, collector, monkeypatch):
        """启用 + 200 + article 类型 → 返回 object"""
        monkeypatch.setenv("ZHIHU_COLLECTOR_ENABLED", "true")
        resp = _make_response(
            200, data=[{"type": "search_result", "object": ARTICLE_OBJECT}]
        )
        with patch(
            "services.platform_collectors.zhihu.requests.get", return_value=resp
        ):
            results = collector._fetch_data("AI", 5)
        assert results == [ARTICLE_OBJECT]

    def test_fetch_mixed_answer_and_article(self, collector, monkeypatch):
        """answer 与 article 同时存在时都应返回"""
        monkeypatch.setenv("ZHIHU_COLLECTOR_ENABLED", "true")
        resp = _make_response(
            200,
            data=[
                {"type": "search_result", "object": ANSWER_OBJECT},
                {"type": "search_result", "object": ARTICLE_OBJECT},
            ],
        )
        with patch(
            "services.platform_collectors.zhihu.requests.get", return_value=resp
        ):
            results = collector._fetch_data("AI", 5)
        assert results == [ANSWER_OBJECT, ARTICLE_OBJECT]

    def test_fetch_filters_non_search_result(self, collector, monkeypatch):
        """顶层 type 非 search_result 应被过滤"""
        monkeypatch.setenv("ZHIHU_COLLECTOR_ENABLED", "true")
        resp = _make_response(
            200,
            data=[
                {"type": "other_type", "object": ANSWER_OBJECT},
                {"type": "search_result", "object": ANSWER_OBJECT},
            ],
        )
        with patch(
            "services.platform_collectors.zhihu.requests.get", return_value=resp
        ):
            results = collector._fetch_data("AI", 5)
        assert results == [ANSWER_OBJECT]

    def test_fetch_filters_non_answer_article_object(self, collector, monkeypatch):
        """object 类型非 answer/article 应被过滤"""
        monkeypatch.setenv("ZHIHU_COLLECTOR_ENABLED", "true")
        resp = _make_response(
            200,
            data=[
                {"type": "search_result", "object": {"type": "question", "id": 1}},
                {"type": "search_result", "object": ANSWER_OBJECT},
            ],
        )
        with patch(
            "services.platform_collectors.zhihu.requests.get", return_value=resp
        ):
            results = collector._fetch_data("AI", 5)
        assert results == [ANSWER_OBJECT]

    def test_fetch_empty_data(self, collector, monkeypatch):
        """200 但 data 为空 → 返回空列表"""
        monkeypatch.setenv("ZHIHU_COLLECTOR_ENABLED", "true")
        resp = _make_response(200, data=[])
        with patch(
            "services.platform_collectors.zhihu.requests.get", return_value=resp
        ):
            results = collector._fetch_data("AI", 5)
        assert results == []

    def test_fetch_missing_data_key(self, collector, monkeypatch):
        """200 但响应无 data 键 → 返回空列表"""
        monkeypatch.setenv("ZHIHU_COLLECTOR_ENABLED", "true")
        resp = _make_response(200, raw_json={})  # 无 data 键
        with patch(
            "services.platform_collectors.zhihu.requests.get", return_value=resp
        ):
            results = collector._fetch_data("AI", 5)
        assert results == []

    def test_fetch_non_200_raises(self, collector, monkeypatch):
        """非 200 状态码 → 抛 NotImplementedError"""
        monkeypatch.setenv("ZHIHU_COLLECTOR_ENABLED", "true")
        resp = _make_response(403)
        with patch(
            "services.platform_collectors.zhihu.requests.get", return_value=resp
        ):
            with pytest.raises(NotImplementedError, match="知乎采集失败"):
                collector._fetch_data("AI", 5)

    def test_fetch_request_exception_raises(self, collector, monkeypatch):
        """请求异常 → 抛 NotImplementedError"""
        monkeypatch.setenv("ZHIHU_COLLECTOR_ENABLED", "true")
        with patch(
            "services.platform_collectors.zhihu.requests.get",
            side_effect=ConnectionError("timeout"),
        ):
            with pytest.raises(NotImplementedError, match="知乎采集失败"):
                collector._fetch_data("AI", 5)


class TestZhihuCollectorCollect:
    """测试 collect() 编排（base.py 165-192）"""

    def test_collect_uses_real_fetch_when_enabled(self, collector, monkeypatch):
        """启用时 collect 走真实 _fetch_data + parse"""
        monkeypatch.setenv("ZHIHU_COLLECTOR_ENABLED", "true")
        resp = _make_response(
            200, data=[{"type": "search_result", "object": ANSWER_OBJECT}]
        )
        with patch(
            "services.platform_collectors.zhihu.requests.get", return_value=resp
        ):
            results = collector.collect("AI", limit=5)
        assert len(results) == 1
        assert isinstance(results[0], PlatformContent)
        assert results[0].platform is Platform.ZHIHU
        assert results[0].author_name == "作者A"
        assert results[0].content_id == "12345"

    def test_collect_falls_back_to_demo_when_disabled(self, collector, monkeypatch):
        """未启用时 collect 回退到模拟数据"""
        monkeypatch.delenv("ZHIHU_COLLECTOR_ENABLED", raising=False)
        results = collector.collect("科技", limit=5)
        assert len(results) > 0
        assert all(r.platform is Platform.ZHIHU for r in results)
        assert all(isinstance(r, PlatformContent) for r in results)

    def test_collect_returns_empty_on_other_exception(self, collector, monkeypatch):
        """_fetch_data 抛非 NotImplementedError 异常时返回空列表"""
        def boom(keyword, limit):
            raise ValueError("network down")

        monkeypatch.setattr(collector, "_fetch_data", boom)
        results = collector.collect("科技", limit=5)
        assert results == []

    def test_collect_skips_unparseable_items(self, collector, monkeypatch):
        """parse 失败的条目应被跳过，其余正常返回"""
        good = collector.parse(ANSWER_OBJECT)
        with patch.object(
            collector,
            "parse",
            side_effect=[ValueError("bad"), good, ValueError("bad2"), good],
        ):
            with patch.object(
                collector,
                "_fetch_data",
                return_value=[{"i": 1}, {"i": 2}, {"i": 3}, {"i": 4}],
            ):
                results = collector.collect("AI", limit=4)
        assert len(results) == 2
        assert results[0] is good
        assert results[1] is good


class TestZhihuCollectorDemoData:
    """测试 _generate_demo_data()（zhihu.py 80-112）"""

    def test_demo_data_structure(self, collector):
        results = collector._generate_demo_data("AI", limit=5)
        assert len(results) == 5
        for r in results:
            assert r.platform is Platform.ZHIHU
            assert r.content_type is ContentType.ANSWER
            assert r.content_id.startswith("zhihu_")
            assert "AI" in r.keywords
            assert "知乎" in r.keywords
            assert "问答" in r.keywords
            assert r.url.startswith("https://www.zhihu.com/question/")
            assert r.author_name  # 非空

    def test_demo_data_capped_at_12(self, collector):
        """limit 超过 12 应被截断为 12"""
        results = collector._generate_demo_data("AI", limit=50)
        assert len(results) == 12

    def test_demo_data_limit_zero(self, collector):
        results = collector._generate_demo_data("AI", limit=0)
        assert len(results) == 0

    def test_demo_data_negative_limit(self, collector):
        """limit 为负数时 min(limit, 12) 为负，range 不产生条目"""
        results = collector._generate_demo_data("AI", limit=-3)
        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
