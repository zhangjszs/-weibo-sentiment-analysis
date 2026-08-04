#!/usr/bin/env python3
"""
spider_task_service.py 单元测试

spider_task_service 是 Spider 任务调度服务，支持本地 Celery 与独立 Spider
服务两种后端，被 spider_routes 的 /api/spider/tasks 端点调用。原测试仅 5
个用例，覆盖 submit/query 的主路径与一级回退，但未覆盖：
- 参数归一化与边界值（page_num / article_limit 钳制、crawl_type 大小写）
- _extract_remote_data / _default_task_label / _normalize_dispatch_result
  的各种字段缺失与 camelCase 兼容
- _remote_headers 在有/无 token 时的行为
- _submit_remote_task 的 HTTP 请求构造与 raise_for_status 行为
- _submit_local_task 的三种 crawl_type 分支与 search 缺关键词校验
- _query_remote_task / _query_local_task 的请求与异常路径
- submit_spider_task 在 SPIDER_SERVICE_ENABLED=True 但远程成功时不走 local
- query_spider_task_progress 在远程启用时直接返回远程结果

测试策略：mock requests.post / requests.get 与 Celery 任务对象，验证调用
参数、回退链路与字段归一化。不触碰真实 HTTP / Celery。
"""

import pytest

pytestmark = pytest.mark.unit

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.settings import Config
from services import spider_task_service
from services.spider_task_service import (
    _default_task_label,
    _extract_remote_data,
    _normalize_crawl_type,
    _normalize_dispatch_result,
    _query_local_task,
    _query_remote_task,
    _remote_headers,
    _submit_local_task,
    _submit_remote_task,
    query_spider_task_progress,
    submit_spider_task,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def patched_config(monkeypatch):
    """提供可配置的 Config 开关，默认禁用远程服务（走 local）"""
    monkeypatch.setattr(Config, "SPIDER_SERVICE_ENABLED", False)
    monkeypatch.setattr(Config, "SPIDER_SERVICE_FALLBACK_LOCAL", False)
    monkeypatch.setattr(Config, "SPIDER_SERVICE_BASE_URL", "http://spider.test")
    monkeypatch.setattr(Config, "SPIDER_SERVICE_TIMEOUT", 5)
    monkeypatch.setattr(Config, "SPIDER_SERVICE_TOKEN", "")
    return Config


def _make_response(payload=None, json_payload=None, raise_exc=None) -> MagicMock:
    """构造模拟的 requests.Response"""
    resp = MagicMock()
    resp.json.return_value = json_payload if json_payload is not None else (payload or {})
    if raise_exc is not None:
        resp.raise_for_status.side_effect = raise_exc
    else:
        resp.raise_for_status.return_value = None
    return resp


def _make_celery_task(task_id: str) -> MagicMock:
    """构造模拟的 Celery AsyncResult"""
    task = MagicMock()
    task.id = task_id
    return task


# ---------------------------------------------------------------------------
# _normalize_crawl_type
# ---------------------------------------------------------------------------


class TestNormalizeCrawlType:
    """crawl_type 归一化逻辑"""

    def test_hot_search_comments_pass_through(self):
        for valid in ("hot", "search", "comments"):
            assert _normalize_crawl_type(valid) == valid

    def test_uppercase_normalized_to_lower(self):
        assert _normalize_crawl_type("HOT") == "hot"
        assert _normalize_crawl_type("Search") == "search"
        assert _normalize_crawl_type("COMMENTS") == "comments"

    def test_whitespace_stripped(self):
        assert _normalize_crawl_type("  hot  ") == "hot"
        assert _normalize_crawl_type("\tsearch\n") == "search"

    def test_invalid_value_defaults_to_hot(self):
        assert _normalize_crawl_type("unknown") == "hot"
        assert _normalize_crawl_type("trending") == "hot"
        assert _normalize_crawl_type("123") == "hot"

    def test_empty_string_defaults_to_hot(self):
        assert _normalize_crawl_type("") == "hot"
        assert _normalize_crawl_type("   ") == "hot"

    def test_none_defaults_to_hot(self):
        assert _normalize_crawl_type(None) == "hot"


# ---------------------------------------------------------------------------
# _extract_remote_data
# ---------------------------------------------------------------------------


class TestExtractRemoteData:
    """远程响应 data 字段提取"""

    def test_dict_with_data_field_returns_inner(self):
        payload = {"code": 0, "data": {"task_id": "t1"}}
        assert _extract_remote_data(payload) == {"task_id": "t1"}

    def test_dict_without_data_returns_whole(self):
        payload = {"task_id": "t1", "status": "ok"}
        assert _extract_remote_data(payload) == payload

    def test_data_field_not_dict_returns_whole_payload(self):
        """data 字段存在但非 dict → 返回整个 payload"""
        payload = {"data": [1, 2, 3], "task_id": "t2"}
        assert _extract_remote_data(payload) == payload

    def test_data_field_none_returns_whole_payload(self):
        payload = {"data": None, "task_id": "t3"}
        assert _extract_remote_data(payload) == payload

    def test_non_dict_payload_raises(self):
        with pytest.raises(ValueError, match="Spider 服务返回格式无效"):
            _extract_remote_data([1, 2, 3])

    def test_non_dict_string_payload_raises(self):
        with pytest.raises(ValueError):
            _extract_remote_data("not a dict")

    def test_none_payload_raises(self):
        with pytest.raises(ValueError):
            _extract_remote_data(None)


# ---------------------------------------------------------------------------
# _default_task_label
# ---------------------------------------------------------------------------


class TestDefaultTaskLabel:
    """默认任务标签生成"""

    def test_search_includes_keyword(self):
        assert _default_task_label("search", "AI") == "关键词搜索: AI"

    def test_search_with_empty_keyword(self):
        assert _default_task_label("search", "") == "关键词搜索: "

    def test_comments_returns_fixed_label(self):
        assert _default_task_label("comments", "") == "爬取评论"

    def test_comments_ignores_keyword(self):
        assert _default_task_label("comments", "ignored") == "爬取评论"

    def test_hot_returns_fixed_label(self):
        assert _default_task_label("hot", "") == "刷新热门微博"

    def test_hot_ignores_keyword(self):
        assert _default_task_label("hot", "ignored") == "刷新热门微博"

    def test_unknown_type_falls_back_to_hot_label(self):
        assert _default_task_label("unknown", "") == "刷新热门微博"


# ---------------------------------------------------------------------------
# _normalize_dispatch_result
# ---------------------------------------------------------------------------


class TestNormalizeDispatchResult:
    """远程任务派发结果归一化"""

    def test_minimal_payload_uses_defaults(self):
        """仅有 task_id 时，其他字段从入参兜底"""
        result = _normalize_dispatch_result(
            {"task_id": "t1"},
            crawl_type="hot",
            keyword="",
            page_num=3,
            article_limit=50,
        )
        assert result == {
            "task_id": "t1",
            "task_label": "刷新热门微博",
            "crawl_type": "hot",
            "keyword": "",
            "page_num": 3,
            "article_limit": 50,
        }

    def test_task_id_converted_to_string(self):
        """task_id 数值应转为字符串"""
        result = _normalize_dispatch_result(
            {"task_id": 12345},
            crawl_type="hot",
            keyword="",
            page_num=1,
            article_limit=10,
        )
        assert result["task_id"] == "12345"
        assert isinstance(result["task_id"], str)

    def test_missing_task_id_raises(self):
        with pytest.raises(ValueError, match="Spider 服务未返回 task_id"):
            _normalize_dispatch_result(
                {"status": "ok"},
                crawl_type="hot",
                keyword="",
                page_num=1,
                article_limit=10,
            )

    def test_empty_task_id_raises(self):
        """task_id 为空字符串/None 都应抛错"""
        with pytest.raises(ValueError):
            _normalize_dispatch_result(
                {"task_id": ""},
                crawl_type="hot",
                keyword="",
                page_num=1,
                article_limit=10,
            )

    def test_camel_case_fields_preferred(self):
        """camelCase 字段优先于入参"""
        payload = {
            "taskId": "remote-1",
            "taskLabel": "关键词搜索: AI",
            "type": "search",
            "keyword": "AI",
            "pageNum": 5,
            "articleLimit": 88,
        }
        result = _normalize_dispatch_result(
            payload, crawl_type="hot", keyword="", page_num=3, article_limit=50
        )
        assert result["task_id"] == "remote-1"
        assert result["task_label"] == "关键词搜索: AI"
        assert result["crawl_type"] == "search"
        assert result["keyword"] == "AI"
        assert result["page_num"] == 5
        assert result["article_limit"] == 88

    def test_snake_case_fields_preferred(self):
        """snake_case 字段也应被识别"""
        payload = {
            "task_id": "remote-2",
            "task_label": "爬取评论",
            "crawl_type": "comments",
            "keyword": "kw",
            "page_num": 2,
            "article_limit": 20,
        }
        result = _normalize_dispatch_result(
            payload, crawl_type="hot", keyword="", page_num=3, article_limit=50
        )
        assert result["task_id"] == "remote-2"
        assert result["task_label"] == "爬取评论"
        assert result["crawl_type"] == "comments"
        assert result["page_num"] == 2
        assert result["article_limit"] == 20

    def test_crawl_type_normalized_when_invalid_in_payload(self):
        """payload 中 crawl_type 无效时归一化为 hot"""
        result = _normalize_dispatch_result(
            {"task_id": "t1", "crawl_type": "unknown_type"},
            crawl_type="hot",
            keyword="",
            page_num=1,
            article_limit=10,
        )
        assert result["crawl_type"] == "hot"

    def test_keyword_falls_back_to_input_when_missing(self):
        """payload 无 keyword 时回退到入参"""
        result = _normalize_dispatch_result(
            {"task_id": "t1"},
            crawl_type="search",
            keyword="fallback-kw",
            page_num=1,
            article_limit=10,
        )
        assert result["keyword"] == "fallback-kw"

    def test_keyword_stripped(self):
        """keyword 应被 strip"""
        result = _normalize_dispatch_result(
            {"task_id": "t1", "keyword": "  AI  "},
            crawl_type="search",
            keyword="",
            page_num=1,
            article_limit=10,
        )
        assert result["keyword"] == "AI"

    def test_task_label_falls_back_to_default(self):
        """payload 无 task_label 时使用 _default_task_label"""
        result = _normalize_dispatch_result(
            {"task_id": "t1", "crawl_type": "comments"},
            crawl_type="comments",
            keyword="",
            page_num=1,
            article_limit=10,
        )
        assert result["task_label"] == "爬取评论"

    def test_page_num_falls_back_to_input(self):
        result = _normalize_dispatch_result(
            {"task_id": "t1"},
            crawl_type="hot",
            keyword="",
            page_num=7,
            article_limit=10,
        )
        assert result["page_num"] == 7

    def test_page_num_converted_to_int(self):
        result = _normalize_dispatch_result(
            {"task_id": "t1", "page_num": "4"},
            crawl_type="hot",
            keyword="",
            page_num=3,
            article_limit=10,
        )
        assert result["page_num"] == 4
        assert isinstance(result["page_num"], int)

    def test_article_limit_falls_back_to_input(self):
        result = _normalize_dispatch_result(
            {"task_id": "t1"},
            crawl_type="hot",
            keyword="",
            page_num=1,
            article_limit=99,
        )
        assert result["article_limit"] == 99

    def test_article_limit_converted_to_int(self):
        result = _normalize_dispatch_result(
            {"task_id": "t1", "articleLimit": "60"},
            crawl_type="hot",
            keyword="",
            page_num=1,
            article_limit=50,
        )
        assert result["article_limit"] == 60
        assert isinstance(result["article_limit"], int)


# ---------------------------------------------------------------------------
# _remote_headers
# ---------------------------------------------------------------------------


class TestRemoteHeaders:
    """远程请求头构造"""

    def test_without_token(self, patched_config):
        patched_config.SPIDER_SERVICE_TOKEN = ""
        headers = _remote_headers()
        assert headers == {"Content-Type": "application/json"}

    def test_with_token_adds_authorization(self, patched_config):
        patched_config.SPIDER_SERVICE_TOKEN = "abc123"
        headers = _remote_headers()
        assert headers["Authorization"] == "Bearer abc123"
        assert headers["Content-Type"] == "application/json"

    def test_token_falsy_omits_authorization(self, patched_config):
        """token 为 None 时不应添加 Authorization"""
        patched_config.SPIDER_SERVICE_TOKEN = None
        headers = _remote_headers()
        assert "Authorization" not in headers


# ---------------------------------------------------------------------------
# _submit_remote_task
# ---------------------------------------------------------------------------


class TestSubmitRemoteTask:
    """远程任务提交"""

    def test_posts_to_correct_url_with_payload(self, patched_config):
        """应向 /api/spider/tasks POST 正确的 JSON"""
        with patch("services.spider_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(json_payload={"task_id": "r1"})
            _submit_remote_task("hot", "kw", 3, 50)

        mock_post.assert_called_once()
        call_args, call_kwargs = mock_post.call_args
        assert call_args[0] == "http://spider.test/api/spider/tasks"
        assert call_kwargs["json"] == {
            "type": "hot",
            "keyword": "kw",
            "page_num": 3,
            "article_limit": 50,
        }
        assert call_kwargs["headers"]["Content-Type"] == "application/json"
        assert call_kwargs["timeout"] == 5

    def test_returns_normalized_result(self, patched_config):
        """应返回归一化后的结果"""
        with patch("services.spider_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={
                    "task_id": "r2",
                    "task_label": "测试任务",
                    "crawl_type": "search",
                    "keyword": "AI",
                    "page_num": 2,
                    "article_limit": 20,
                }
            )
            result = _submit_remote_task("search", "AI", 2, 20)

        assert result["task_id"] == "r2"
        assert result["task_label"] == "测试任务"
        assert result["crawl_type"] == "search"

    def test_unwraps_data_envelope(self, patched_config):
        """应解开 {data: {...}} 包装"""
        with patch("services.spider_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"data": {"task_id": "r3"}}
            )
            result = _submit_remote_task("hot", "", 1, 10)

        assert result["task_id"] == "r3"

    def test_raises_on_http_error(self, patched_config):
        """raise_for_status 抛错应向上传播"""
        from requests import HTTPError

        with patch("services.spider_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(raise_exc=HTTPError("500 error"))
            with pytest.raises(HTTPError):
                _submit_remote_task("hot", "", 1, 10)

    def test_raises_when_task_id_missing(self, patched_config):
        """payload 无 task_id 时抛 ValueError"""
        with patch("services.spider_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(json_payload={"status": "ok"})
            with pytest.raises(ValueError, match="Spider 服务未返回 task_id"):
                _submit_remote_task("hot", "", 1, 10)

    def test_includes_token_header_when_configured(self, patched_config):
        """配置 token 时应发送 Authorization 头"""
        patched_config.SPIDER_SERVICE_TOKEN = "secret"
        with patch("services.spider_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(json_payload={"task_id": "r4"})
            _submit_remote_task("hot", "", 1, 10)

        headers = mock_post.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer secret"


# ---------------------------------------------------------------------------
# _submit_local_task
# ---------------------------------------------------------------------------


class TestSubmitLocalTask:
    """本地 Celery 任务提交"""

    @patch("services.spider_task_service.requests")  # 确保不发起 HTTP
    def test_hot_dispatches_spider_hot_task(self, _mock_req):
        """crawl_type=hot → spider_hot_task.delay(page_num)"""
        with patch("tasks.celery_spider.spider_hot_task") as mock_task:
            mock_task.delay.return_value = _make_celery_task("local-hot")
            result = _submit_local_task("hot", "", 3, 50)

        mock_task.delay.assert_called_once_with(3)
        assert result == {
            "task_id": "local-hot",
            "task_label": "刷新热门微博",
            "crawl_type": "hot",
            "keyword": "",
            "page_num": 3,
            "article_limit": 50,
        }

    @patch("services.spider_task_service.requests")
    def test_search_dispatches_spider_search_task(self, _mock_req):
        """crawl_type=search → spider_search_task.delay(keyword, page_num)"""
        with patch("tasks.celery_spider.spider_search_task") as mock_task:
            mock_task.delay.return_value = _make_celery_task("local-search")
            result = _submit_local_task("search", "  AI  ", 4, 50)

        mock_task.delay.assert_called_once_with("AI", 4)
        assert result["task_id"] == "local-search"
        assert result["task_label"] == "关键词搜索: AI"
        assert result["keyword"] == "AI"
        assert result["page_num"] == 4

    @patch("services.spider_task_service.requests")
    def test_comments_dispatches_spider_comments_task(self, _mock_req):
        """crawl_type=comments → spider_comments_task.delay(article_limit)"""
        with patch("tasks.celery_spider.spider_comments_task") as mock_task:
            mock_task.delay.return_value = _make_celery_task("local-cmt")
            result = _submit_local_task("comments", "", 3, 80)

        mock_task.delay.assert_called_once_with(80)
        assert result["task_id"] == "local-cmt"
        assert result["task_label"] == "爬取评论"
        assert result["article_limit"] == 80

    @patch("services.spider_task_service.requests")
    def test_search_with_empty_keyword_raises(self, _mock_req):
        """search 模式 keyword 为空应抛 ValueError"""
        with patch("tasks.celery_spider.spider_search_task") as mock_task:
            with pytest.raises(ValueError, match="keyword 不能为空"):
                _submit_local_task("search", "   ", 3, 50)
            mock_task.delay.assert_not_called()

    @patch("services.spider_task_service.requests")
    def test_search_keyword_stripped_before_dispatch(self, _mock_req):
        """search 模式 keyword 应在 delay 前被 strip"""
        with patch("tasks.celery_spider.spider_search_task") as mock_task:
            mock_task.delay.return_value = _make_celery_task("local-x")
            _submit_local_task("search", "  hello  ", 3, 50)

        # delay 第一参数应为已 strip 的 "hello"
        assert mock_task.delay.call_args[0][0] == "hello"


# ---------------------------------------------------------------------------
# submit_spider_task
# ---------------------------------------------------------------------------


class TestSubmitSpiderTask:
    """submit_spider_task 顶层调度"""

    def test_remote_disabled_uses_local(self, patched_config):
        """SPIDER_SERVICE_ENABLED=False → 直接走 local"""
        expected = {"task_id": "local-1", "task_label": "刷新热门微博"}
        with patch(
            "services.spider_task_service._submit_local_task", return_value=expected
        ) as mock_local, patch(
            "services.spider_task_service._submit_remote_task"
        ) as mock_remote:
            result = submit_spider_task("hot", page_num=3)

        assert result == expected
        mock_local.assert_called_once()
        mock_remote.assert_not_called()

    def test_remote_enabled_success_uses_remote(self, patched_config):
        """远程启用且成功 → 走 remote，不查 local"""
        patched_config.SPIDER_SERVICE_ENABLED = True
        remote_result = {"task_id": "r1", "task_label": "remote"}
        with patch(
            "services.spider_task_service._submit_remote_task",
            return_value=remote_result,
        ) as mock_remote, patch(
            "services.spider_task_service._submit_local_task"
        ) as mock_local:
            result = submit_spider_task("hot")

        assert result == remote_result
        mock_remote.assert_called_once()
        mock_local.assert_not_called()

    def test_remote_error_with_fallback_uses_local(self, patched_config):
        """远程失败 + FALLBACK_LOCAL=True → 回退 local"""
        patched_config.SPIDER_SERVICE_ENABLED = True
        patched_config.SPIDER_SERVICE_FALLBACK_LOCAL = True
        local_result = {"task_id": "local-fallback"}
        with patch(
            "services.spider_task_service._submit_remote_task",
            side_effect=RuntimeError("remote down"),
        ), patch(
            "services.spider_task_service._submit_local_task",
            return_value=local_result,
        ) as mock_local:
            result = submit_spider_task("hot")

        assert result == local_result
        mock_local.assert_called_once()

    def test_remote_error_without_fallback_raises(self, patched_config):
        """远程失败 + FALLBACK_LOCAL=False → 向上抛错"""
        patched_config.SPIDER_SERVICE_ENABLED = True
        patched_config.SPIDER_SERVICE_FALLBACK_LOCAL = False
        with patch(
            "services.spider_task_service._submit_remote_task",
            side_effect=RuntimeError("remote down"),
        ), patch(
            "services.spider_task_service._submit_local_task"
        ) as mock_local:
            with pytest.raises(RuntimeError, match="remote down"):
                submit_spider_task("hot")
        mock_local.assert_not_called()

    def test_remote_error_logs_warning_when_falling_back(
        self, patched_config, caplog
    ):
        """回退时应记 warning 日志"""
        import logging

        patched_config.SPIDER_SERVICE_ENABLED = True
        patched_config.SPIDER_SERVICE_FALLBACK_LOCAL = True
        with patch(
            "services.spider_task_service._submit_remote_task",
            side_effect=ConnectionError("refused"),
        ), patch(
            "services.spider_task_service._submit_local_task",
            return_value={"task_id": "x"},
        ):
            with caplog.at_level(
                logging.WARNING, logger="services.spider_task_service"
            ):
                submit_spider_task("hot")
        assert any("回退本地 Celery" in r.message for r in caplog.records)

    def test_clamps_page_num_to_valid_range(self, patched_config):
        """page_num 应被钳制到 [1, 10]"""
        captured = {}

        def fake_local(**kwargs):
            captured.update(kwargs)
            return {"task_id": "x"}

        with patch(
            "services.spider_task_service._submit_local_task", side_effect=fake_local
        ):
            submit_spider_task("hot", page_num=0)
            assert captured["page_num"] == 1

            submit_spider_task("hot", page_num=999)
            assert captured["page_num"] == 10

    def test_clamps_article_limit_to_valid_range(self, patched_config):
        """article_limit 应被钳制到 [1, 100]"""
        captured = {}

        def fake_local(**kwargs):
            captured.update(kwargs)
            return {"task_id": "x"}

        with patch(
            "services.spider_task_service._submit_local_task", side_effect=fake_local
        ):
            submit_spider_task("hot", article_limit=0)
            assert captured["article_limit"] == 1

            submit_spider_task("hot", article_limit=9999)
            assert captured["article_limit"] == 100

    def test_normalizes_crawl_type(self, patched_config):
        """crawl_type 应被归一化（大小写/空白/无效值）"""
        captured = {}

        def fake_local(**kwargs):
            captured.update(kwargs)
            return {"task_id": "x"}

        with patch(
            "services.spider_task_service._submit_local_task", side_effect=fake_local
        ):
            submit_spider_task("HOT")
            assert captured["crawl_type"] == "hot"

            submit_spider_task("  Search  ")
            assert captured["crawl_type"] == "search"

            submit_spider_task("invalid")
            assert captured["crawl_type"] == "hot"

    def test_strips_keyword(self, patched_config):
        """keyword 应被 strip"""
        captured = {}

        def fake_local(**kwargs):
            captured.update(kwargs)
            return {"task_id": "x"}

        with patch(
            "services.spider_task_service._submit_local_task", side_effect=fake_local
        ):
            submit_spider_task("search", keyword="  AI  ", page_num=1)

        assert captured["keyword"] == "AI"

    def test_none_keyword_becomes_empty(self, patched_config):
        """keyword=None 应被转为空字符串"""
        captured = {}

        def fake_local(**kwargs):
            captured.update(kwargs)
            return {"task_id": "x"}

        with patch(
            "services.spider_task_service._submit_local_task", side_effect=fake_local
        ):
            submit_spider_task("hot", keyword=None)

        assert captured["keyword"] == ""

    def test_passes_normalized_params_to_remote(self, patched_config):
        """远程路径同样应传递归一化后的参数"""
        patched_config.SPIDER_SERVICE_ENABLED = True
        captured = {}

        def fake_remote(**kwargs):
            captured.update(kwargs)
            return {"task_id": "r1"}

        with patch(
            "services.spider_task_service._submit_remote_task", side_effect=fake_remote
        ):
            submit_spider_task(
                "HOT", keyword="  AI  ", page_num=999, article_limit=9999
            )

        assert captured["crawl_type"] == "hot"
        assert captured["keyword"] == "AI"
        assert captured["page_num"] == 10
        assert captured["article_limit"] == 100

    def test_string_page_num_converted_to_int(self, patched_config):
        """字符串 page_num 应被转为 int 后钳制"""
        captured = {}

        def fake_local(**kwargs):
            captured.update(kwargs)
            return {"task_id": "x"}

        with patch(
            "services.spider_task_service._submit_local_task", side_effect=fake_local
        ):
            submit_spider_task("hot", page_num="5")

        assert captured["page_num"] == 5
        assert isinstance(captured["page_num"], int)


# ---------------------------------------------------------------------------
# _query_remote_task
# ---------------------------------------------------------------------------


class TestQueryRemoteTask:
    """远程任务状态查询"""

    def test_gets_correct_url(self, patched_config):
        with patch("services.spider_task_service.requests.get") as mock_get:
            mock_get.return_value = _make_response(json_payload={"task_id": "t1"})
            _query_remote_task("task-xyz")

        mock_get.assert_called_once()
        call_args, call_kwargs = mock_get.call_args
        assert call_args[0] == "http://spider.test/api/spider/tasks/task-xyz/status"
        assert call_kwargs["timeout"] == 5

    def test_returns_unwrapped_data(self, patched_config):
        with patch("services.spider_task_service.requests.get") as mock_get:
            mock_get.return_value = _make_response(
                json_payload={"data": {"task_id": "t1", "state": "SUCCESS"}}
            )
            result = _query_remote_task("t1")

        assert result == {"task_id": "t1", "state": "SUCCESS"}

    def test_returns_payload_when_no_data_envelope(self, patched_config):
        with patch("services.spider_task_service.requests.get") as mock_get:
            mock_get.return_value = _make_response(
                json_payload={"task_id": "t2", "state": "PENDING"}
            )
            result = _query_remote_task("t2")

        assert result["task_id"] == "t2"
        assert result["state"] == "PENDING"

    def test_raises_on_http_error(self, patched_config):
        from requests import HTTPError

        with patch("services.spider_task_service.requests.get") as mock_get:
            mock_get.return_value = _make_response(raise_exc=HTTPError("404"))
            with pytest.raises(HTTPError):
                _query_remote_task("missing")

    def test_includes_token_header(self, patched_config):
        patched_config.SPIDER_SERVICE_TOKEN = "tok"
        with patch("services.spider_task_service.requests.get") as mock_get:
            mock_get.return_value = _make_response(json_payload={"task_id": "t"})
            _query_remote_task("t")

        headers = mock_get.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer tok"

    def test_data_field_non_dict_returns_whole_payload(self, patched_config):
        """data 字段非 dict 时返回整个 payload。

        注意：_query_remote_task 中的 `if not isinstance(payload, dict)`
        检查实际上是死代码——_extract_remote_data 已经保证返回 dict 或抛
        ValueError，所以这条分支不可达。本测试记录实际行为：当 data 字段
        为 list 时，_extract_remote_data 返回整个 payload（而非 list），
        _query_remote_task 随后原样返回。
        """
        payload = {"data": [1, 2, 3], "task_id": "t"}
        with patch("services.spider_task_service.requests.get") as mock_get:
            mock_get.return_value = _make_response(json_payload=payload)
            result = _query_remote_task("t")

        assert result == payload

    def test_non_dict_top_level_raises(self, patched_config):
        """顶层 payload 非 dict 时 _extract_remote_data 抛 ValueError"""
        with patch("services.spider_task_service.requests.get") as mock_get:
            mock_get.return_value = _make_response(json_payload=[1, 2, 3])
            with pytest.raises(ValueError, match="Spider 服务返回格式无效"):
                _query_remote_task("t")


# ---------------------------------------------------------------------------
# _query_local_task
# ---------------------------------------------------------------------------


class TestQueryLocalTask:
    """本地任务状态查询（委托给 get_task_progress）"""

    def test_delegates_to_get_task_progress(self):
        """应调用 tasks.celery_spider.get_task_progress"""
        with patch(
            "tasks.celery_spider.get_task_progress",
            return_value={"task_id": "t1", "state": "SUCCESS"},
        ) as mock_progress:
            result = _query_local_task("t1")

        mock_progress.assert_called_once_with("t1")
        assert result == {"task_id": "t1", "state": "SUCCESS"}

    def test_propagates_errors_from_get_task_progress(self):
        """get_task_progress 抛错应向上传播"""
        with patch(
            "tasks.celery_spider.get_task_progress",
            side_effect=KeyError("missing task"),
        ):
            with pytest.raises(KeyError):
                _query_local_task("bad-id")


# ---------------------------------------------------------------------------
# query_spider_task_progress
# ---------------------------------------------------------------------------


class TestQuerySpiderTaskProgress:
    """query_spider_task_progress 后端选择"""

    def test_remote_disabled_uses_local(self, patched_config):
        """SPIDER_SERVICE_ENABLED=False → 走 local"""
        local_result = {"task_id": "t1", "state": "SUCCESS"}
        with patch(
            "services.spider_task_service._query_local_task",
            return_value=local_result,
        ) as mock_local, patch(
            "services.spider_task_service._query_remote_task"
        ) as mock_remote:
            result = query_spider_task_progress("t1")

        assert result == local_result
        mock_local.assert_called_once_with("t1")
        mock_remote.assert_not_called()

    def test_remote_enabled_uses_remote(self, patched_config):
        """SPIDER_SERVICE_ENABLED=True → 走 remote"""
        patched_config.SPIDER_SERVICE_ENABLED = True
        remote_result = {"task_id": "t2", "state": "PENDING"}
        with patch(
            "services.spider_task_service._query_remote_task",
            return_value=remote_result,
        ) as mock_remote, patch(
            "services.spider_task_service._query_local_task"
        ) as mock_local:
            result = query_spider_task_progress("t2")

        assert result == remote_result
        mock_remote.assert_called_once_with("t2")
        mock_local.assert_not_called()

    def test_remote_error_propagates_without_fallback(self, patched_config):
        """query_spider_task_progress 远程失败时直接抛错（无 fallback 逻辑）。

        注意：与 submit_spider_task 不同，query_spider_task_progress 不实现
        回退链——这是设计如此，回退链由 task_status_service.query_task_progress
        在更高层处理。
        """
        patched_config.SPIDER_SERVICE_ENABLED = True
        with patch(
            "services.spider_task_service._query_remote_task",
            side_effect=RuntimeError("remote down"),
        ), patch(
            "services.spider_task_service._query_local_task"
        ) as mock_local:
            with pytest.raises(RuntimeError, match="remote down"):
                query_spider_task_progress("t3")
        mock_local.assert_not_called()

    def test_passes_task_id_through(self, patched_config):
        """task_id 应原样传递给底层"""
        with patch(
            "services.spider_task_service._query_local_task",
            return_value={"task_id": "x"},
        ) as mock_local:
            query_spider_task_progress("complex-id-123")
        mock_local.assert_called_once_with("complex-id-123")
