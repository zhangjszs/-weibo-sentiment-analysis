#!/usr/bin/env python3
"""
nlp_task_service.py 单元测试

nlp_task_service 是 NLP 任务调度服务，支持本地 Celery 与独立 NLP 服务两种后端。
被 nlp_routes 的 /api/nlp/analyze、/api/nlp/predict/batch、/api/nlp/tasks/* 端点
调用。原测试仅 8 个用例，只覆盖 analyze_text 与 query_nlp_task_progress 的主路径
与一级回退，未覆盖：

- _extract_remote_data 的 data 解包与各种非 dict 输入
- _remote_headers 在有/无 token 时的行为
- _normalize_task_result 的 camelCase 兼容、字段缺失、类型转换
- _analyze_remote_text / _analyze_remote_batch 的 HTTP 请求构造与 raise_for_status
- _analyze_remote_batch 对 dict / list / 非法格式的多种返回解析
- _submit_remote_analyze_task / _submit_remote_retrain_task 的请求与归一化
- _submit_local_analyze_task / _submit_local_retrain_task 的 Celery 派发
- analyze_batch / submit_analyze_task / submit_retrain_task 的回退链路与日志
- _query_remote_task 的 GET 请求与异常路径
- _query_local_task 的 PENDING/PROGRESS/SUCCESS/FAILURE/未知状态映射
- mode 默认值差异（analyze_text 默认 "custom"，submit_analyze_task 默认 "smart"）
- total=0 时 progress 超 100% 的已知 bug 行为记录

测试策略：mock requests.post / requests.get 与 Celery AsyncResult，验证调用参数、
回退链路与字段归一化。不触碰真实 HTTP / Celery / SnowNLP。
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from requests import HTTPError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.settings import Config
from services import nlp_task_service
from services.nlp_task_service import (
    _analyze_local_batch,
    _analyze_local_text,
    _analyze_remote_batch,
    _analyze_remote_text,
    _extract_remote_data,
    _normalize_task_result,
    _query_local_task,
    _query_remote_task,
    _remote_headers,
    _submit_local_analyze_task,
    _submit_local_retrain_task,
    _submit_remote_analyze_task,
    _submit_remote_retrain_task,
    analyze_batch,
    analyze_text,
    query_nlp_task_progress,
    submit_analyze_task,
    submit_retrain_task,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def patched_config(monkeypatch):
    """提供可配置的 Config 开关，默认禁用远程服务（走 local）"""
    monkeypatch.setattr(Config, "NLP_SERVICE_ENABLED", False)
    monkeypatch.setattr(Config, "NLP_SERVICE_FALLBACK_LOCAL", True)
    monkeypatch.setattr(Config, "NLP_SERVICE_BASE_URL", "http://nlp.test")
    monkeypatch.setattr(Config, "NLP_SERVICE_TIMEOUT", 10)
    monkeypatch.setattr(Config, "NLP_SERVICE_TOKEN", "")
    return Config


def _make_response(
    payload=None, json_payload=None, raise_exc=None
) -> MagicMock:
    """构造模拟的 requests.Response"""
    resp = MagicMock()
    resp.json.return_value = (
        json_payload if json_payload is not None else (payload or {})
    )
    if raise_exc is not None:
        resp.raise_for_status.side_effect = raise_exc
    else:
        resp.raise_for_status.return_value = None
    return resp


def _make_async_result(
    state: str, info=None, result=None
) -> MagicMock:
    """构造模拟的 Celery AsyncResult 对象"""
    mock = MagicMock()
    mock.state = state
    mock.info = info
    mock.result = result
    return mock


def _make_celery_task(task_id: str) -> MagicMock:
    """构造模拟的 Celery 任务对象（带 .delay().id 链式调用）"""
    task = MagicMock()
    task.id = task_id
    task.delay.return_value = task
    return task


# ---------------------------------------------------------------------------
# _extract_remote_data
# ---------------------------------------------------------------------------


class TestExtractRemoteData:
    """远程响应 data 字段提取"""

    def test_dict_with_data_field_returns_inner(self):
        payload = {"code": 0, "data": {"label": "positive"}}
        assert _extract_remote_data(payload) == {"label": "positive"}

    def test_dict_without_data_returns_whole(self):
        payload = {"label": "positive", "score": 0.9}
        assert _extract_remote_data(payload) == payload

    def test_data_field_not_dict_returns_whole_payload(self):
        """data 字段存在但非 dict → 返回整个 payload（get 仍返回该值，但调用方会再校验）"""
        payload = {"data": [1, 2, 3], "task_id": "t1"}
        # _extract_remote_data 只做 dict 检查，data 是 list 时直接返回 list
        assert _extract_remote_data(payload) == [1, 2, 3]

    def test_data_field_none_returns_none(self):
        """data 字段为 None → 返回 None（get 返回 None）"""
        payload = {"data": None, "task_id": "t2"}
        assert _extract_remote_data(payload) is None

    def test_non_dict_payload_raises(self):
        with pytest.raises(ValueError, match="NLP 服务返回格式无效"):
            _extract_remote_data([1, 2, 3])

    def test_non_dict_string_payload_raises(self):
        with pytest.raises(ValueError):
            _extract_remote_data("not a dict")

    def test_non_dict_int_payload_raises(self):
        with pytest.raises(ValueError):
            _extract_remote_data(42)

    def test_none_payload_raises(self):
        with pytest.raises(ValueError):
            _extract_remote_data(None)


# ---------------------------------------------------------------------------
# _remote_headers
# ---------------------------------------------------------------------------


class TestRemoteHeaders:
    """远程请求头构造"""

    def test_without_token(self, patched_config):
        patched_config.NLP_SERVICE_TOKEN = ""
        headers = _remote_headers()
        assert headers == {"Content-Type": "application/json"}

    def test_with_token_adds_authorization(self, patched_config):
        patched_config.NLP_SERVICE_TOKEN = "abc123"
        headers = _remote_headers()
        assert headers["Authorization"] == "Bearer abc123"
        assert headers["Content-Type"] == "application/json"

    def test_token_falsy_omits_authorization(self, patched_config):
        """token 为 None 时不应添加 Authorization（if 判定为 falsy）"""
        patched_config.NLP_SERVICE_TOKEN = None
        headers = _remote_headers()
        assert "Authorization" not in headers

    def test_token_empty_string_omits_authorization(self, patched_config):
        """空字符串 token 同样不添加 Authorization"""
        patched_config.NLP_SERVICE_TOKEN = ""
        headers = _remote_headers()
        assert "Authorization" not in headers


# ---------------------------------------------------------------------------
# _normalize_task_result
# ---------------------------------------------------------------------------


class TestNormalizeTaskResult:
    """远程任务结果归一化"""

    def test_minimal_payload_uses_defaults(self):
        """仅有 task_id 时，其他字段从入参兜底"""
        result = _normalize_task_result(
            {"task_id": "t1"}, default_label="情感分析", mode="smart"
        )
        assert result == {
            "task_id": "t1",
            "task_label": "情感分析",
            "mode": "smart",
            "status": "PENDING",
        }

    def test_task_id_converted_to_string(self):
        """task_id 数值应转为字符串"""
        result = _normalize_task_result(
            {"task_id": 12345}, default_label="情感分析", mode="smart"
        )
        assert result["task_id"] == "12345"
        assert isinstance(result["task_id"], str)

    def test_missing_task_id_raises(self):
        with pytest.raises(ValueError, match="NLP 服务未返回 task_id"):
            _normalize_task_result(
                {"status": "ok"}, default_label="情感分析", mode="smart"
            )

    def test_empty_task_id_raises(self):
        """task_id 为空字符串（falsy）→ 抛错"""
        with pytest.raises(ValueError, match="NLP 服务未返回 task_id"):
            _normalize_task_result(
                {"task_id": ""}, default_label="情感分析", mode="smart"
            )

    def test_none_task_id_raises(self):
        with pytest.raises(ValueError):
            _normalize_task_result(
                {"task_id": None}, default_label="情感分析", mode="smart"
            )

    def test_camel_case_task_id_preferred(self):
        """camelCase taskId 字段也被识别"""
        payload = {
            "taskId": "remote-1",
            "taskLabel": "情感分析",
            "mode": "smart",
            "status": "SUCCESS",
        }
        result = _normalize_task_result(payload, default_label="兜底")
        assert result["task_id"] == "remote-1"
        assert result["task_label"] == "情感分析"
        assert result["status"] == "SUCCESS"

    def test_camel_case_task_label_preferred(self):
        """taskLabel 优先于 default_label"""
        result = _normalize_task_result(
            {"task_id": "t1", "taskLabel": "远程标签"}, default_label="兜底"
        )
        assert result["task_label"] == "远程标签"

    def test_task_label_falls_back_to_default(self):
        """payload 无 task_label/taskLabel 时使用 default_label"""
        result = _normalize_task_result(
            {"task_id": "t1"}, default_label="模型重训练"
        )
        assert result["task_label"] == "模型重训练"

    def test_mode_converted_to_string(self):
        """mode 应被转为字符串"""
        result = _normalize_task_result(
            {"task_id": "t1", "mode": 123}, default_label="情感分析"
        )
        assert result["mode"] == "123"
        assert isinstance(result["mode"], str)

    def test_mode_falls_back_to_param(self):
        """payload 无 mode 时回退到入参 mode"""
        result = _normalize_task_result(
            {"task_id": "t1"}, default_label="情感分析", mode="custom"
        )
        assert result["mode"] == "custom"

    def test_mode_none_falls_back_to_param(self):
        """payload mode=None（falsy）时回退到入参 mode"""
        result = _normalize_task_result(
            {"task_id": "t1", "mode": None}, default_label="情感分析", mode="smart"
        )
        assert result["mode"] == "smart"

    def test_status_falls_back_to_pending(self):
        """payload 无 status 时默认 PENDING"""
        result = _normalize_task_result(
            {"task_id": "t1"}, default_label="情感分析"
        )
        assert result["status"] == "PENDING"

    def test_status_none_falls_back_to_pending(self):
        """status=None（falsy）时回退到 PENDING"""
        result = _normalize_task_result(
            {"task_id": "t1", "status": None}, default_label="情感分析"
        )
        assert result["status"] == "PENDING"

    def test_default_mode_param_is_smart(self):
        """函数签名 mode 默认值为 'smart'"""
        result = _normalize_task_result(
            {"task_id": "t1"}, default_label="情感分析"
        )
        assert result["mode"] == "smart"


# ---------------------------------------------------------------------------
# _analyze_remote_text
# ---------------------------------------------------------------------------


class TestAnalyzeRemoteText:
    """远程单文本分析"""

    def test_posts_to_correct_url_with_payload(self, patched_config):
        """应向 /api/nlp/analyze POST 正确的 JSON"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"label": "positive", "score": 0.9}
            )
            _analyze_remote_text("测试文本", "smart")

        mock_post.assert_called_once()
        call_args, call_kwargs = mock_post.call_args
        assert call_args[0] == "http://nlp.test/api/nlp/analyze"
        assert call_kwargs["json"] == {"text": "测试文本", "mode": "smart"}
        assert call_kwargs["headers"]["Content-Type"] == "application/json"
        assert call_kwargs["timeout"] == 10

    def test_returns_payload_dict(self, patched_config):
        """应返回 dict 形式的分析结果"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"label": "negative", "score": 0.8}
            )
            result = _analyze_remote_text("文本", "custom")
        assert result == {"label": "negative", "score": 0.8}

    def test_unwraps_data_envelope(self, patched_config):
        """应解开 {data: {...}} 包装"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"data": {"label": "neutral"}}
            )
            result = _analyze_remote_text("文本", "smart")
        assert result == {"label": "neutral"}

    def test_raises_on_http_error(self, patched_config):
        """raise_for_status 抛错应向上传播"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(raise_exc=HTTPError("500"))
            with pytest.raises(HTTPError):
                _analyze_remote_text("文本", "smart")

    def test_raises_when_top_level_not_dict(self, patched_config):
        """顶层响应非 dict（如 list）→ _extract_remote_data 抛 'NLP 服务返回格式无效'"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(json_payload=[1, 2, 3])
            with pytest.raises(ValueError, match="NLP 服务返回格式无效"):
                _analyze_remote_text("文本", "smart")

    def test_raises_when_data_envelope_not_dict(self, patched_config):
        """data 字段为 list 时，_extract_remote_data 返回 list，再校验非 dict 抛 'NLP 分析返回格式无效'"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"data": [1, 2, 3]}
            )
            with pytest.raises(ValueError, match="NLP 分析返回格式无效"):
                _analyze_remote_text("文本", "smart")

    def test_includes_token_header_when_configured(self, patched_config):
        """配置 token 时应发送 Authorization 头"""
        patched_config.NLP_SERVICE_TOKEN = "secret"
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(json_payload={"label": "pos"})
            _analyze_remote_text("文本", "smart")
        assert mock_post.call_args[1]["headers"]["Authorization"] == "Bearer secret"


# ---------------------------------------------------------------------------
# _analyze_local_text
# ---------------------------------------------------------------------------


class TestAnalyzeLocalText:
    """本地单文本分析"""

    def test_delegates_to_sentiment_service(self):
        """应调用 SentimentService.analyze(text, mode)"""
        with patch.object(
            nlp_task_service.SentimentService, "analyze", return_value={"label": "pos"}
        ) as mock_analyze:
            result = _analyze_local_text("文本", "custom")
        mock_analyze.assert_called_once_with("文本", "custom")
        assert result == {"label": "pos"}


# ---------------------------------------------------------------------------
# analyze_text
# ---------------------------------------------------------------------------


class TestAnalyzeText:
    """analyze_text 顶层调度"""

    def test_remote_disabled_uses_local(self, patched_config):
        """NLP_SERVICE_ENABLED=False → 直接走 local"""
        expected = {"label": "neutral"}
        with patch(
            "services.nlp_task_service._analyze_local_text", return_value=expected
        ) as mock_local, patch(
            "services.nlp_task_service._analyze_remote_text"
        ) as mock_remote:
            result = analyze_text("文本", "custom")
        assert result == expected
        mock_local.assert_called_once_with(text="文本", mode="custom")
        mock_remote.assert_not_called()

    def test_remote_enabled_success_uses_remote(self, patched_config):
        """远程启用且成功 → 走 remote，不查 local"""
        patched_config.NLP_SERVICE_ENABLED = True
        remote_result = {"label": "positive"}
        with patch(
            "services.nlp_task_service._analyze_remote_text",
            return_value=remote_result,
        ) as mock_remote, patch(
            "services.nlp_task_service._analyze_local_text"
        ) as mock_local:
            result = analyze_text("文本", "smart")
        assert result == remote_result
        mock_remote.assert_called_once_with(text="文本", mode="smart")
        mock_local.assert_not_called()

    def test_remote_error_with_fallback_uses_local(self, patched_config):
        """远程失败 + FALLBACK_LOCAL=True → 回退 local"""
        patched_config.NLP_SERVICE_ENABLED = True
        patched_config.NLP_SERVICE_FALLBACK_LOCAL = True
        local_result = {"label": "fallback"}
        with patch(
            "services.nlp_task_service._analyze_remote_text",
            side_effect=RuntimeError("remote down"),
        ), patch(
            "services.nlp_task_service._analyze_local_text",
            return_value=local_result,
        ) as mock_local:
            result = analyze_text("文本", "smart")
        assert result == local_result
        mock_local.assert_called_once_with(text="文本", mode="smart")

    def test_remote_error_without_fallback_raises(self, patched_config):
        """远程失败 + FALLBACK_LOCAL=False → 向上抛错"""
        patched_config.NLP_SERVICE_ENABLED = True
        patched_config.NLP_SERVICE_FALLBACK_LOCAL = False
        with patch(
            "services.nlp_task_service._analyze_remote_text",
            side_effect=RuntimeError("remote down"),
        ), patch(
            "services.nlp_task_service._analyze_local_text"
        ) as mock_local:
            with pytest.raises(RuntimeError, match="remote down"):
                analyze_text("文本", "smart")
        mock_local.assert_not_called()

    def test_remote_error_logs_warning_when_falling_back(
        self, patched_config, caplog
    ):
        """回退时应记 warning 日志"""
        import logging

        patched_config.NLP_SERVICE_ENABLED = True
        patched_config.NLP_SERVICE_FALLBACK_LOCAL = True
        with patch(
            "services.nlp_task_service._analyze_remote_text",
            side_effect=ConnectionError("refused"),
        ), patch(
            "services.nlp_task_service._analyze_local_text",
            return_value={"label": "x"},
        ):
            with caplog.at_level(
                logging.WARNING, logger="services.nlp_task_service"
            ):
                analyze_text("文本", "smart")
        assert any("回退本地分析" in r.message for r in caplog.records)

    def test_default_mode_is_custom(self, patched_config):
        """未传 mode 时默认 'custom'（注意：与 submit_analyze_task 默认 'smart' 不同）"""
        captured = {}

        def fake_local(text, mode):
            captured["mode"] = mode
            return {"label": "x"}

        with patch(
            "services.nlp_task_service._analyze_local_text", side_effect=fake_local
        ):
            analyze_text("文本")
        assert captured["mode"] == "custom"

    def test_none_mode_normalized_to_custom(self, patched_config):
        """mode=None → 归一化为 'custom'"""
        captured = {}

        def fake_local(text, mode):
            captured["mode"] = mode
            return {"label": "x"}

        with patch(
            "services.nlp_task_service._analyze_local_text", side_effect=fake_local
        ):
            analyze_text("文本", None)
        assert captured["mode"] == "custom"

    def test_mode_stripped(self, patched_config):
        """mode 应被 strip"""
        captured = {}

        def fake_local(text, mode):
            captured["mode"] = mode
            return {"label": "x"}

        with patch(
            "services.nlp_task_service._analyze_local_text", side_effect=fake_local
        ):
            analyze_text("文本", "  smart  ")
        assert captured["mode"] == "smart"

    def test_passes_normalized_mode_to_remote(self, patched_config):
        """远程路径同样应传递归一化后的 mode"""
        patched_config.NLP_SERVICE_ENABLED = True
        captured = {}

        def fake_remote(text, mode):
            captured["mode"] = mode
            return {"label": "x"}

        with patch(
            "services.nlp_task_service._analyze_remote_text", side_effect=fake_remote
        ):
            analyze_text("文本", "  custom  ")
        assert captured["mode"] == "custom"


# ---------------------------------------------------------------------------
# _analyze_remote_batch
# ---------------------------------------------------------------------------


class TestAnalyzeRemoteBatch:
    """远程批量分析"""

    def test_posts_to_correct_url_with_payload(self, patched_config):
        """应向 /api/nlp/predict/batch POST 正确的 JSON"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"results": [{"label": "pos"}]}
            )
            _analyze_remote_batch(["a", "b"], "smart")

        call_args, call_kwargs = mock_post.call_args
        assert call_args[0] == "http://nlp.test/api/nlp/predict/batch"
        assert call_kwargs["json"] == {"texts": ["a", "b"], "mode": "smart"}
        assert call_kwargs["timeout"] == 10

    def test_returns_results_list_from_dict_envelope(self, patched_config):
        """dict 响应且 results 是 list → 返回 results"""
        results = [{"label": "pos"}, {"label": "neg"}]
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"results": results}
            )
            got = _analyze_remote_batch(["a", "b"], "smart")
        assert got == results

    def test_top_level_list_raises_extract_error(self, patched_config):
        """顶层响应是 list → _extract_remote_data 抛 'NLP 服务返回格式无效'。

        注意：源码中 `if isinstance(payload, list): return payload` 这条分支
        在顶层 list 响应下永远走不到，因为 _extract_remote_data 会先校验输入
        必须是 dict。该分支只在 {data: [...]} 包装时可达（见 test_unwraps_data_envelope_with_list）。
        """
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(json_payload=[{"label": "pos"}])
            with pytest.raises(ValueError, match="NLP 服务返回格式无效"):
                _analyze_remote_batch(["a"], "smart")

    def test_unwraps_data_envelope_with_results(self, patched_config):
        """{data: {results: [...]}} 包装也能解析"""
        results = [{"label": "neg"}]
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"data": {"results": results}}
            )
            got = _analyze_remote_batch(["a"], "smart")
        assert got == results

    def test_unwraps_data_envelope_with_list(self, patched_config):
        """{data: [...]} 包装，data 是 list → 直接返回"""
        results = [{"label": "neg"}]
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"data": results}
            )
            got = _analyze_remote_batch(["a"], "smart")
        assert got == results

    def test_dict_without_results_returns_empty_list(self, patched_config):
        """dict 响应但无 results 字段 → 返回 []（get 默认值）"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"status": "ok"}
            )
            got = _analyze_remote_batch(["a"], "smart")
        assert got == []

    def test_dict_with_non_list_results_raises(self, patched_config):
        """results 非 list（如 str）→ isinstance 检查失败，回退到 list 判断也失败 → 抛 ValueError"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"results": "not a list"}
            )
            with pytest.raises(ValueError, match="NLP 批量分析返回格式无效"):
                _analyze_remote_batch(["a"], "smart")

    def test_raises_when_payload_is_string(self, patched_config):
        """解包后是 str → 既非 dict 也非 list → 抛 ValueError"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"data": "invalid"}
            )
            with pytest.raises(ValueError, match="NLP 批量分析返回格式无效"):
                _analyze_remote_batch(["a"], "smart")

    def test_raises_when_payload_is_int(self, patched_config):
        """顶层响应是 int → _extract_remote_data 抛 'NLP 服务返回格式无效'"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(json_payload=42)
            with pytest.raises(ValueError, match="NLP 服务返回格式无效"):
                _analyze_remote_batch(["a"], "smart")

    def test_raises_on_http_error(self, patched_config):
        """raise_for_status 抛错应向上传播"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(raise_exc=HTTPError("500"))
            with pytest.raises(HTTPError):
                _analyze_remote_batch(["a"], "smart")

    def test_includes_token_header_when_configured(self, patched_config):
        """配置 token 时应发送 Authorization 头"""
        patched_config.NLP_SERVICE_TOKEN = "secret"
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(json_payload={"results": []})
            _analyze_remote_batch(["a"], "smart")
        assert mock_post.call_args[1]["headers"]["Authorization"] == "Bearer secret"


# ---------------------------------------------------------------------------
# _analyze_local_batch
# ---------------------------------------------------------------------------


class TestAnalyzeLocalBatch:
    """本地批量分析"""

    def test_delegates_to_sentiment_service(self):
        """应调用 SentimentService.analyze_batch(texts, mode)"""
        expected = [{"label": "pos"}, {"label": "neg"}]
        with patch.object(
            nlp_task_service.SentimentService,
            "analyze_batch",
            return_value=expected,
        ) as mock_batch:
            result = _analyze_local_batch(["a", "b"], "custom")
        mock_batch.assert_called_once_with(["a", "b"], "custom")
        assert result == expected


# ---------------------------------------------------------------------------
# analyze_batch
# ---------------------------------------------------------------------------


class TestAnalyzeBatch:
    """analyze_batch 顶层调度"""

    def test_remote_disabled_uses_local(self, patched_config):
        """NLP_SERVICE_ENABLED=False → 直接走 local"""
        expected = [{"label": "pos"}]
        with patch(
            "services.nlp_task_service._analyze_local_batch",
            return_value=expected,
        ) as mock_local, patch(
            "services.nlp_task_service._analyze_remote_batch"
        ) as mock_remote:
            result = analyze_batch(["a", "b"], "custom")
        assert result == expected
        mock_local.assert_called_once_with(texts=["a", "b"], mode="custom")
        mock_remote.assert_not_called()

    def test_remote_enabled_success_uses_remote(self, patched_config):
        """远程启用且成功 → 走 remote"""
        patched_config.NLP_SERVICE_ENABLED = True
        remote_result = [{"label": "pos"}]
        with patch(
            "services.nlp_task_service._analyze_remote_batch",
            return_value=remote_result,
        ) as mock_remote, patch(
            "services.nlp_task_service._analyze_local_batch"
        ) as mock_local:
            result = analyze_batch(["a"], "smart")
        assert result == remote_result
        mock_remote.assert_called_once_with(texts=["a"], mode="smart")
        mock_local.assert_not_called()

    def test_remote_error_with_fallback_uses_local(self, patched_config):
        """远程失败 + FALLBACK_LOCAL=True → 回退 local"""
        patched_config.NLP_SERVICE_ENABLED = True
        patched_config.NLP_SERVICE_FALLBACK_LOCAL = True
        local_result = [{"label": "fallback"}]
        with patch(
            "services.nlp_task_service._analyze_remote_batch",
            side_effect=RuntimeError("remote down"),
        ), patch(
            "services.nlp_task_service._analyze_local_batch",
            return_value=local_result,
        ) as mock_local:
            result = analyze_batch(["a"], "smart")
        assert result == local_result
        mock_local.assert_called_once_with(texts=["a"], mode="smart")

    def test_remote_error_without_fallback_raises(self, patched_config):
        """远程失败 + FALLBACK_LOCAL=False → 向上抛错"""
        patched_config.NLP_SERVICE_ENABLED = True
        patched_config.NLP_SERVICE_FALLBACK_LOCAL = False
        with patch(
            "services.nlp_task_service._analyze_remote_batch",
            side_effect=RuntimeError("remote down"),
        ), patch(
            "services.nlp_task_service._analyze_local_batch"
        ) as mock_local:
            with pytest.raises(RuntimeError, match="remote down"):
                analyze_batch(["a"], "smart")
        mock_local.assert_not_called()

    def test_remote_error_logs_warning_when_falling_back(
        self, patched_config, caplog
    ):
        """回退时应记 warning 日志"""
        import logging

        patched_config.NLP_SERVICE_ENABLED = True
        patched_config.NLP_SERVICE_FALLBACK_LOCAL = True
        with patch(
            "services.nlp_task_service._analyze_remote_batch",
            side_effect=ConnectionError("refused"),
        ), patch(
            "services.nlp_task_service._analyze_local_batch",
            return_value=[],
        ):
            with caplog.at_level(
                logging.WARNING, logger="services.nlp_task_service"
            ):
                analyze_batch(["a"], "smart")
        assert any("回退本地批量分析" in r.message for r in caplog.records)

    def test_default_mode_is_custom(self, patched_config):
        """未传 mode 时默认 'custom'"""
        captured = {}

        def fake_local(texts, mode):
            captured["mode"] = mode
            return []

        with patch(
            "services.nlp_task_service._analyze_local_batch", side_effect=fake_local
        ):
            analyze_batch(["a"])
        assert captured["mode"] == "custom"

    def test_none_mode_normalized_to_custom(self, patched_config):
        """mode=None → 归一化为 'custom'"""
        captured = {}

        def fake_local(texts, mode):
            captured["mode"] = mode
            return []

        with patch(
            "services.nlp_task_service._analyze_local_batch", side_effect=fake_local
        ):
            analyze_batch(["a"], None)
        assert captured["mode"] == "custom"

    def test_mode_stripped(self, patched_config):
        """mode 应被 strip"""
        captured = {}

        def fake_local(texts, mode):
            captured["mode"] = mode
            return []

        with patch(
            "services.nlp_task_service._analyze_local_batch", side_effect=fake_local
        ):
            analyze_batch(["a"], "  smart  ")
        assert captured["mode"] == "smart"


# ---------------------------------------------------------------------------
# _submit_remote_analyze_task
# ---------------------------------------------------------------------------


class TestSubmitRemoteAnalyzeTask:
    """远程异步分析任务提交"""

    def test_posts_to_correct_url_with_payload(self, patched_config):
        """应向 /api/nlp/tasks/analyze POST 正确的 JSON"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"task_id": "r1"}
            )
            _submit_remote_analyze_task("文本", "smart")

        call_args, call_kwargs = mock_post.call_args
        assert call_args[0] == "http://nlp.test/api/nlp/tasks/analyze"
        assert call_kwargs["json"] == {"text": "文本", "mode": "smart"}
        assert call_kwargs["timeout"] == 10

    def test_returns_normalized_result(self, patched_config):
        """应返回归一化后的结果（default_label='情感分析'）"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={
                    "task_id": "r2",
                    "task_label": "自定义标签",
                    "mode": "custom",
                    "status": "SUCCESS",
                }
            )
            result = _submit_remote_analyze_task("文本", "smart")
        assert result["task_id"] == "r2"
        assert result["task_label"] == "自定义标签"
        assert result["mode"] == "custom"
        assert result["status"] == "SUCCESS"

    def test_uses_default_label_when_missing(self, patched_config):
        """payload 无 task_label 时使用 '情感分析'"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"task_id": "r3"}
            )
            result = _submit_remote_analyze_task("文本", "smart")
        assert result["task_label"] == "情感分析"

    def test_uses_mode_param_when_missing(self, patched_config):
        """payload 无 mode 时回退到入参 mode"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"task_id": "r4"}
            )
            result = _submit_remote_analyze_task("文本", "custom")
        assert result["mode"] == "custom"

    def test_unwraps_data_envelope(self, patched_config):
        """应解开 {data: {...}} 包装"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"data": {"task_id": "r5"}}
            )
            result = _submit_remote_analyze_task("文本", "smart")
        assert result["task_id"] == "r5"

    def test_raises_on_http_error(self, patched_config):
        """raise_for_status 抛错应向上传播"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(raise_exc=HTTPError("500"))
            with pytest.raises(HTTPError):
                _submit_remote_analyze_task("文本", "smart")

    def test_raises_when_top_level_not_dict(self, patched_config):
        """顶层响应非 dict → _extract_remote_data 抛 'NLP 服务返回格式无效'"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(json_payload=[1, 2, 3])
            with pytest.raises(ValueError, match="NLP 服务返回格式无效"):
                _submit_remote_analyze_task("文本", "smart")

    def test_raises_when_data_envelope_not_dict(self, patched_config):
        """data 字段非 dict → 解包后校验失败，抛 'NLP 异步分析返回格式无效'"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"data": [1, 2, 3]}
            )
            with pytest.raises(ValueError, match="NLP 异步分析返回格式无效"):
                _submit_remote_analyze_task("文本", "smart")

    def test_raises_when_task_id_missing(self, patched_config):
        """payload 无 task_id 时抛 ValueError"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(json_payload={"status": "ok"})
            with pytest.raises(ValueError, match="NLP 服务未返回 task_id"):
                _submit_remote_analyze_task("文本", "smart")

    def test_includes_token_header_when_configured(self, patched_config):
        """配置 token 时应发送 Authorization 头"""
        patched_config.NLP_SERVICE_TOKEN = "secret"
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(json_payload={"task_id": "r6"})
            _submit_remote_analyze_task("文本", "smart")
        assert mock_post.call_args[1]["headers"]["Authorization"] == "Bearer secret"


# ---------------------------------------------------------------------------
# _submit_local_analyze_task
# ---------------------------------------------------------------------------


class TestSubmitLocalAnalyzeTask:
    """本地异步分析任务提交"""

    @patch("services.nlp_task_service.requests")  # 确保不发起 HTTP
    def test_dispatches_analyze_single_with_fallback(self, _mock_req):
        """应调用 analyze_single_with_fallback.delay(text, mode)"""
        with patch(
            "tasks.celery_sentiment.analyze_single_with_fallback"
        ) as mock_task:
            mock_task.delay.return_value = _make_celery_task("local-analyze")
            result = _submit_local_analyze_task("文本", "smart")

        mock_task.delay.assert_called_once_with("文本", "smart")
        assert result == {
            "task_id": "local-analyze",
            "task_label": "情感分析",
            "mode": "smart",
            "status": "PENDING",
        }

    @patch("services.nlp_task_service.requests")
    def test_returns_task_id_from_celery(self, _mock_req):
        """task_id 应来自 Celery 任务的 .id"""
        with patch(
            "tasks.celery_sentiment.analyze_single_with_fallback"
        ) as mock_task:
            mock_task.delay.return_value = _make_celery_task("celery-xyz")
            result = _submit_local_analyze_task("文本", "custom")
        assert result["task_id"] == "celery-xyz"


# ---------------------------------------------------------------------------
# submit_analyze_task
# ---------------------------------------------------------------------------


class TestSubmitAnalyzeTask:
    """submit_analyze_task 顶层调度"""

    def test_remote_disabled_uses_local(self, patched_config):
        """NLP_SERVICE_ENABLED=False → 直接走 local"""
        expected = {"task_id": "local-1", "task_label": "情感分析"}
        with patch(
            "services.nlp_task_service._submit_local_analyze_task",
            return_value=expected,
        ) as mock_local, patch(
            "services.nlp_task_service._submit_remote_analyze_task"
        ) as mock_remote:
            result = submit_analyze_task("文本", "smart")
        assert result == expected
        mock_local.assert_called_once_with(text="文本", mode="smart")
        mock_remote.assert_not_called()

    def test_remote_enabled_success_uses_remote(self, patched_config):
        """远程启用且成功 → 走 remote"""
        patched_config.NLP_SERVICE_ENABLED = True
        remote_result = {"task_id": "r1", "task_label": "remote"}
        with patch(
            "services.nlp_task_service._submit_remote_analyze_task",
            return_value=remote_result,
        ) as mock_remote, patch(
            "services.nlp_task_service._submit_local_analyze_task"
        ) as mock_local:
            result = submit_analyze_task("文本", "smart")
        assert result == remote_result
        mock_remote.assert_called_once_with(text="文本", mode="smart")
        mock_local.assert_not_called()

    def test_remote_error_with_fallback_uses_local(self, patched_config):
        """远程失败 + FALLBACK_LOCAL=True → 回退 local"""
        patched_config.NLP_SERVICE_ENABLED = True
        patched_config.NLP_SERVICE_FALLBACK_LOCAL = True
        local_result = {"task_id": "local-fallback"}
        with patch(
            "services.nlp_task_service._submit_remote_analyze_task",
            side_effect=RuntimeError("remote down"),
        ), patch(
            "services.nlp_task_service._submit_local_analyze_task",
            return_value=local_result,
        ) as mock_local:
            result = submit_analyze_task("文本", "smart")
        assert result == local_result
        mock_local.assert_called_once_with(text="文本", mode="smart")

    def test_remote_error_without_fallback_raises(self, patched_config):
        """远程失败 + FALLBACK_LOCAL=False → 向上抛错"""
        patched_config.NLP_SERVICE_ENABLED = True
        patched_config.NLP_SERVICE_FALLBACK_LOCAL = False
        with patch(
            "services.nlp_task_service._submit_remote_analyze_task",
            side_effect=RuntimeError("remote down"),
        ), patch(
            "services.nlp_task_service._submit_local_analyze_task"
        ) as mock_local:
            with pytest.raises(RuntimeError, match="remote down"):
                submit_analyze_task("文本", "smart")
        mock_local.assert_not_called()

    def test_remote_error_logs_warning_when_falling_back(
        self, patched_config, caplog
    ):
        """回退时应记 warning 日志"""
        import logging

        patched_config.NLP_SERVICE_ENABLED = True
        patched_config.NLP_SERVICE_FALLBACK_LOCAL = True
        with patch(
            "services.nlp_task_service._submit_remote_analyze_task",
            side_effect=ConnectionError("refused"),
        ), patch(
            "services.nlp_task_service._submit_local_analyze_task",
            return_value={"task_id": "x"},
        ):
            with caplog.at_level(
                logging.WARNING, logger="services.nlp_task_service"
            ):
                submit_analyze_task("文本", "smart")
        assert any("回退本地异步分析" in r.message for r in caplog.records)

    def test_default_mode_is_smart(self, patched_config):
        """未传 mode 时默认 'smart'（注意：与 analyze_text 默认 'custom' 不同）"""
        captured = {}

        def fake_local(text, mode):
            captured["mode"] = mode
            return {"task_id": "x"}

        with patch(
            "services.nlp_task_service._submit_local_analyze_task",
            side_effect=fake_local,
        ):
            submit_analyze_task("文本")
        assert captured["mode"] == "smart"

    def test_none_mode_normalized_to_smart(self, patched_config):
        """mode=None → 归一化为 'smart'"""
        captured = {}

        def fake_local(text, mode):
            captured["mode"] = mode
            return {"task_id": "x"}

        with patch(
            "services.nlp_task_service._submit_local_analyze_task",
            side_effect=fake_local,
        ):
            submit_analyze_task("文本", None)
        assert captured["mode"] == "smart"

    def test_mode_stripped(self, patched_config):
        """mode 应被 strip"""
        captured = {}

        def fake_local(text, mode):
            captured["mode"] = mode
            return {"task_id": "x"}

        with patch(
            "services.nlp_task_service._submit_local_analyze_task",
            side_effect=fake_local,
        ):
            submit_analyze_task("文本", "  smart  ")
        assert captured["mode"] == "smart"


# ---------------------------------------------------------------------------
# _submit_remote_retrain_task
# ---------------------------------------------------------------------------


class TestSubmitRemoteRetrainTask:
    """远程重训练任务提交"""

    def test_posts_to_correct_url_with_payload(self, patched_config):
        """应向 /api/nlp/tasks/retrain POST {optimize: bool}"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"task_id": "r1"}
            )
            _submit_remote_retrain_task(optimize=True)

        call_args, call_kwargs = mock_post.call_args
        assert call_args[0] == "http://nlp.test/api/nlp/tasks/retrain"
        assert call_kwargs["json"] == {"optimize": True}
        assert call_kwargs["timeout"] == 10

    def test_optimize_coerced_to_bool(self, patched_config):
        """optimize 应被 bool() 转换"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(json_payload={"task_id": "r1"})
            _submit_remote_retrain_task(optimize=1)
        assert mock_post.call_args[1]["json"] == {"optimize": True}

        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(json_payload={"task_id": "r2"})
            _submit_remote_retrain_task(optimize=0)
        assert mock_post.call_args[1]["json"] == {"optimize": False}

    def test_returns_normalized_result(self, patched_config):
        """应返回归一化后的结果（default_label='模型重训练', mode='custom'）"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={
                    "task_id": "r2",
                    "status": "RUNNING",
                }
            )
            result = _submit_remote_retrain_task(optimize=False)
        assert result["task_id"] == "r2"
        assert result["task_label"] == "模型重训练"
        assert result["mode"] == "custom"
        assert result["status"] == "RUNNING"

    def test_uses_default_label_when_missing(self, patched_config):
        """payload 无 task_label 时使用 '模型重训练'"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"task_id": "r3"}
            )
            result = _submit_remote_retrain_task(optimize=True)
        assert result["task_label"] == "模型重训练"

    def test_payload_mode_overrides_param(self, patched_config):
        """_normalize_task_result 中 payload.mode 优先于入参 mode（"custom"）。

        调用方传入 mode="custom"，但 payload 带 mode="ignored" 时，归一化结果
        取 payload 的值。这是 _normalize_task_result 的既定行为（payload 优先）。
        """
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"task_id": "r4", "mode": "ignored"}
            )
            result = _submit_remote_retrain_task(optimize=True)
        assert result["mode"] == "ignored"

    def test_mode_falls_back_to_custom_when_missing(self, patched_config):
        """payload 无 mode 时回退到入参 'custom'"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"task_id": "r4"}
            )
            result = _submit_remote_retrain_task(optimize=True)
        assert result["mode"] == "custom"

    def test_unwraps_data_envelope(self, patched_config):
        """应解开 {data: {...}} 包装"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"data": {"task_id": "r5"}}
            )
            result = _submit_remote_retrain_task(optimize=False)
        assert result["task_id"] == "r5"

    def test_raises_on_http_error(self, patched_config):
        """raise_for_status 抛错应向上传播"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(raise_exc=HTTPError("500"))
            with pytest.raises(HTTPError):
                _submit_remote_retrain_task(optimize=True)

    def test_raises_when_top_level_not_dict(self, patched_config):
        """顶层响应非 dict → _extract_remote_data 抛 'NLP 服务返回格式无效'"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(json_payload=[1, 2])
            with pytest.raises(ValueError, match="NLP 服务返回格式无效"):
                _submit_remote_retrain_task(optimize=True)

    def test_raises_when_data_envelope_not_dict(self, patched_config):
        """data 字段非 dict → 解包后校验失败，抛 'NLP 重训练返回格式无效'"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(
                json_payload={"data": [1, 2]}
            )
            with pytest.raises(ValueError, match="NLP 重训练返回格式无效"):
                _submit_remote_retrain_task(optimize=True)

    def test_raises_when_task_id_missing(self, patched_config):
        """payload 无 task_id 时抛 ValueError"""
        with patch("services.nlp_task_service.requests.post") as mock_post:
            mock_post.return_value = _make_response(json_payload={"status": "ok"})
            with pytest.raises(ValueError, match="NLP 服务未返回 task_id"):
                _submit_remote_retrain_task(optimize=True)


# ---------------------------------------------------------------------------
# _submit_local_retrain_task
# ---------------------------------------------------------------------------


class TestSubmitLocalRetrainTask:
    """本地重训练任务提交"""

    @patch("services.nlp_task_service.requests")  # 确保不发起 HTTP
    def test_dispatches_retrain_model_task(self, _mock_req):
        """应调用 retrain_model_task.delay(optimize=bool)"""
        with patch("tasks.celery_sentiment.retrain_model_task") as mock_task:
            mock_task.delay.return_value = _make_celery_task("local-retrain")
            result = _submit_local_retrain_task(optimize=True)

        mock_task.delay.assert_called_once_with(optimize=True)
        assert result == {
            "task_id": "local-retrain",
            "task_label": "模型重训练",
            "mode": "custom",
            "status": "PENDING",
        }

    @patch("services.nlp_task_service.requests")
    def test_optimize_coerced_to_bool(self, _mock_req):
        """optimize 应被 bool() 转换后再传给 delay"""
        with patch("tasks.celery_sentiment.retrain_model_task") as mock_task:
            mock_task.delay.return_value = _make_celery_task("local-x")
            _submit_local_retrain_task(optimize=1)
        mock_task.delay.assert_called_once_with(optimize=True)


# ---------------------------------------------------------------------------
# submit_retrain_task
# ---------------------------------------------------------------------------


class TestSubmitRetrainTask:
    """submit_retrain_task 顶层调度"""

    def test_remote_disabled_uses_local(self, patched_config):
        """NLP_SERVICE_ENABLED=False → 直接走 local"""
        expected = {"task_id": "local-1", "task_label": "模型重训练"}
        with patch(
            "services.nlp_task_service._submit_local_retrain_task",
            return_value=expected,
        ) as mock_local, patch(
            "services.nlp_task_service._submit_remote_retrain_task"
        ) as mock_remote:
            result = submit_retrain_task(optimize=True)
        assert result == expected
        mock_local.assert_called_once_with(optimize=True)
        mock_remote.assert_not_called()

    def test_remote_enabled_success_uses_remote(self, patched_config):
        """远程启用且成功 → 走 remote"""
        patched_config.NLP_SERVICE_ENABLED = True
        remote_result = {"task_id": "r1", "task_label": "模型重训练"}
        with patch(
            "services.nlp_task_service._submit_remote_retrain_task",
            return_value=remote_result,
        ) as mock_remote, patch(
            "services.nlp_task_service._submit_local_retrain_task"
        ) as mock_local:
            result = submit_retrain_task(optimize=True)
        assert result == remote_result
        mock_remote.assert_called_once_with(optimize=True)
        mock_local.assert_not_called()

    def test_remote_error_with_fallback_uses_local(self, patched_config):
        """远程失败 + FALLBACK_LOCAL=True → 回退 local"""
        patched_config.NLP_SERVICE_ENABLED = True
        patched_config.NLP_SERVICE_FALLBACK_LOCAL = True
        local_result = {"task_id": "local-fallback"}
        with patch(
            "services.nlp_task_service._submit_remote_retrain_task",
            side_effect=RuntimeError("remote down"),
        ), patch(
            "services.nlp_task_service._submit_local_retrain_task",
            return_value=local_result,
        ) as mock_local:
            result = submit_retrain_task(optimize=True)
        assert result == local_result
        mock_local.assert_called_once_with(optimize=True)

    def test_remote_error_without_fallback_raises(self, patched_config):
        """远程失败 + FALLBACK_LOCAL=False → 向上抛错"""
        patched_config.NLP_SERVICE_ENABLED = True
        patched_config.NLP_SERVICE_FALLBACK_LOCAL = False
        with patch(
            "services.nlp_task_service._submit_remote_retrain_task",
            side_effect=RuntimeError("remote down"),
        ), patch(
            "services.nlp_task_service._submit_local_retrain_task"
        ) as mock_local:
            with pytest.raises(RuntimeError, match="remote down"):
                submit_retrain_task(optimize=True)
        mock_local.assert_not_called()

    def test_remote_error_logs_warning_when_falling_back(
        self, patched_config, caplog
    ):
        """回退时应记 warning 日志"""
        import logging

        patched_config.NLP_SERVICE_ENABLED = True
        patched_config.NLP_SERVICE_FALLBACK_LOCAL = True
        with patch(
            "services.nlp_task_service._submit_remote_retrain_task",
            side_effect=ConnectionError("refused"),
        ), patch(
            "services.nlp_task_service._submit_local_retrain_task",
            return_value={"task_id": "x"},
        ):
            with caplog.at_level(
                logging.WARNING, logger="services.nlp_task_service"
            ):
                submit_retrain_task(optimize=True)
        assert any("回退本地重训练" in r.message for r in caplog.records)

    def test_default_optimize_is_false(self, patched_config):
        """未传 optimize 时默认 False"""
        captured = {}

        def fake_local(optimize):
            captured["optimize"] = optimize
            return {"task_id": "x"}

        with patch(
            "services.nlp_task_service._submit_local_retrain_task",
            side_effect=fake_local,
        ):
            submit_retrain_task()
        assert captured["optimize"] is False

    def test_passes_bool_coerced_optimize_to_local(self, patched_config):
        """optimize 应被 bool() 转换后传给 local"""
        captured = {}

        def fake_local(optimize):
            captured["optimize"] = optimize
            return {"task_id": "x"}

        with patch(
            "services.nlp_task_service._submit_local_retrain_task",
            side_effect=fake_local,
        ):
            submit_retrain_task(optimize=1)
        assert captured["optimize"] is True


# ---------------------------------------------------------------------------
# _query_remote_task
# ---------------------------------------------------------------------------


class TestQueryRemoteTask:
    """远程任务状态查询"""

    def test_gets_correct_url(self, patched_config):
        """应向 /api/nlp/tasks/{task_id}/status 发起 GET"""
        with patch("services.nlp_task_service.requests.get") as mock_get:
            mock_get.return_value = _make_response(
                json_payload={"task_id": "t1", "state": "PENDING"}
            )
            _query_remote_task("t1")

        call_args, call_kwargs = mock_get.call_args
        assert call_args[0] == "http://nlp.test/api/nlp/tasks/t1/status"
        assert call_kwargs["timeout"] == 10

    def test_returns_payload_dict(self, patched_config):
        """应返回 dict 形式的状态"""
        payload = {"task_id": "t1", "state": "SUCCESS", "progress": 100}
        with patch("services.nlp_task_service.requests.get") as mock_get:
            mock_get.return_value = _make_response(json_payload=payload)
            result = _query_remote_task("t1")
        assert result == payload

    def test_unwraps_data_envelope(self, patched_config):
        """应解开 {data: {...}} 包装"""
        with patch("services.nlp_task_service.requests.get") as mock_get:
            mock_get.return_value = _make_response(
                json_payload={"data": {"task_id": "t2", "state": "PROGRESS"}}
            )
            result = _query_remote_task("t2")
        assert result == {"task_id": "t2", "state": "PROGRESS"}

    def test_raises_on_http_error(self, patched_config):
        """raise_for_status 抛错应向上传播"""
        with patch("services.nlp_task_service.requests.get") as mock_get:
            mock_get.return_value = _make_response(raise_exc=HTTPError("500"))
            with pytest.raises(HTTPError):
                _query_remote_task("t1")

    def test_raises_when_top_level_not_dict(self, patched_config):
        """顶层响应非 dict → _extract_remote_data 抛 'NLP 服务返回格式无效'"""
        with patch("services.nlp_task_service.requests.get") as mock_get:
            mock_get.return_value = _make_response(json_payload=[1, 2, 3])
            with pytest.raises(ValueError, match="NLP 服务返回格式无效"):
                _query_remote_task("t1")

    def test_raises_when_data_envelope_not_dict(self, patched_config):
        """data 字段非 dict → 解包后校验失败，抛 'NLP 任务状态返回格式无效'"""
        with patch("services.nlp_task_service.requests.get") as mock_get:
            mock_get.return_value = _make_response(
                json_payload={"data": [1, 2, 3]}
            )
            with pytest.raises(ValueError, match="NLP 任务状态返回格式无效"):
                _query_remote_task("t1")

    def test_includes_token_header_when_configured(self, patched_config):
        """配置 token 时应发送 Authorization 头"""
        patched_config.NLP_SERVICE_TOKEN = "secret"
        with patch("services.nlp_task_service.requests.get") as mock_get:
            mock_get.return_value = _make_response(json_payload={"task_id": "t1"})
            _query_remote_task("t1")
        assert mock_get.call_args[1]["headers"]["Authorization"] == "Bearer secret"


# ---------------------------------------------------------------------------
# _query_local_task
# ---------------------------------------------------------------------------


class TestQueryLocalTask:
    """本地 Celery 任务状态查询，各状态映射测试"""

    @patch("services.nlp_task_service.AsyncResult")
    def test_pending_state(self, mock_async):
        """PENDING → progress=0, message='任务等待中...'"""
        mock_async.return_value = _make_async_result("PENDING")
        result = _query_local_task("task-1")
        assert result["task_id"] == "task-1"
        assert result["state"] == "PENDING"
        assert result["progress"] == 0
        assert result["message"] == "任务等待中..."
        assert result["result"] == {}

    @patch("services.nlp_task_service.AsyncResult")
    def test_progress_state_calculates_percentage(self, mock_async):
        """PROGRESS → progress = current/total*100"""
        mock_async.return_value = _make_async_result(
            "PROGRESS", info={"current": 30, "total": 100, "status": "处理中"}
        )
        result = _query_local_task("task-2")
        assert result["progress"] == 30
        assert result["message"] == "处理中"

    @patch("services.nlp_task_service.AsyncResult")
    def test_progress_state_zero_total_no_division_error(self, mock_async):
        """PROGRESS 且 total=0 → progress=0（任务尚未开始），不抛除零也不超过 100%。

        历史 bug：源码 `int(info.get("total", 1) or 1)` 中 `0 or 1` 求值为 1
        （0 是 falsy），total=0 被当成 1，导致 current>0 时 progress 超过 100
        （如 5/1*100=500）。修复：total=0 时 progress 直接取 0。
        """
        mock_async.return_value = _make_async_result(
            "PROGRESS", info={"current": 5, "total": 0, "status": ""}
        )
        result = _query_local_task("task-3")
        # 修复后：total=0 → progress=0（不再超过 100%）
        assert result["progress"] == 0

    @patch("services.nlp_task_service.AsyncResult")
    def test_progress_state_none_info(self, mock_async):
        """PROGRESS 且 info=None → progress=0, message=''"""
        mock_async.return_value = _make_async_result("PROGRESS", info=None)
        result = _query_local_task("task-4")
        assert result["progress"] == 0
        assert result["message"] == ""

    @patch("services.nlp_task_service.AsyncResult")
    def test_progress_state_missing_fields(self, mock_async):
        """PROGRESS 且 info 缺少 current/total → 默认 0/1 → progress=0"""
        mock_async.return_value = _make_async_result(
            "PROGRESS", info={"status": "部分完成"}
        )
        result = _query_local_task("task-5")
        assert result["progress"] == 0  # int(0 / max(1,1) * 100) = 0
        assert result["message"] == "部分完成"

    @patch("services.nlp_task_service.AsyncResult")
    def test_success_state(self, mock_async):
        """SUCCESS → progress=100, result 填充, message='任务完成'"""
        mock_async.return_value = _make_async_result(
            "SUCCESS", result={"data": [1, 2, 3]}
        )
        result = _query_local_task("task-6")
        assert result["progress"] == 100
        assert result["result"] == {"data": [1, 2, 3]}
        assert result["message"] == "任务完成"

    @patch("services.nlp_task_service.AsyncResult")
    def test_success_state_none_result(self, mock_async):
        """SUCCESS 且 result=None → result={}（result.result or {}）"""
        mock_async.return_value = _make_async_result("SUCCESS", result=None)
        result = _query_local_task("task-7")
        assert result["result"] == {}
        assert result["progress"] == 100

    @patch("services.nlp_task_service.AsyncResult")
    def test_failure_state(self, mock_async):
        """FAILURE → message=str(result.info)"""
        mock_async.return_value = _make_async_result(
            "FAILURE", info="TaskError: something went wrong"
        )
        result = _query_local_task("task-8")
        assert result["state"] == "FAILURE"
        assert result["message"] == "TaskError: something went wrong"
        assert result["progress"] == 0

    @patch("services.nlp_task_service.AsyncResult")
    def test_unknown_state_defaults(self, mock_async):
        """未知状态（如 STARTED）→ 默认值 progress=0, message=''"""
        mock_async.return_value = _make_async_result("STARTED")
        result = _query_local_task("task-9")
        assert result["state"] == "STARTED"
        assert result["progress"] == 0
        assert result["message"] == ""
        assert result["result"] == {}

    @patch("services.nlp_task_service.AsyncResult")
    def test_uses_celery_app(self, mock_async):
        """应将 celery_app 传给 AsyncResult"""
        mock_async.return_value = _make_async_result("PENDING")
        _query_local_task("task-10")
        call_kwargs = mock_async.call_args
        assert call_kwargs[0][0] == "task-10"
        assert "app" in call_kwargs[1]


# ---------------------------------------------------------------------------
# query_nlp_task_progress
# ---------------------------------------------------------------------------


class TestQueryNlpTaskProgress:
    """query_nlp_task_progress 顶层调度"""

    def test_remote_disabled_uses_local(self, patched_config):
        """NLP_SERVICE_ENABLED=False → 直接走 local"""
        expected = {"task_id": "t1", "state": "SUCCESS"}
        with patch(
            "services.nlp_task_service._query_local_task",
            return_value=expected,
        ) as mock_local, patch(
            "services.nlp_task_service._query_remote_task"
        ) as mock_remote:
            result = query_nlp_task_progress("t1")
        assert result == expected
        mock_local.assert_called_once_with("t1")
        mock_remote.assert_not_called()

    def test_remote_enabled_success_uses_remote(self, patched_config):
        """远程启用且成功 → 走 remote，不查 local"""
        patched_config.NLP_SERVICE_ENABLED = True
        remote_result = {"task_id": "t2", "state": "PROGRESS", "progress": 50}
        with patch(
            "services.nlp_task_service._query_remote_task",
            return_value=remote_result,
        ) as mock_remote, patch(
            "services.nlp_task_service._query_local_task"
        ) as mock_local:
            result = query_nlp_task_progress("t2")
        assert result == remote_result
        mock_remote.assert_called_once_with("t2")
        mock_local.assert_not_called()

    def test_remote_error_with_fallback_uses_local(self, patched_config):
        """远程失败 + FALLBACK_LOCAL=True → 回退 local"""
        patched_config.NLP_SERVICE_ENABLED = True
        patched_config.NLP_SERVICE_FALLBACK_LOCAL = True
        local_result = {"task_id": "t3", "state": "SUCCESS"}
        with patch(
            "services.nlp_task_service._query_remote_task",
            side_effect=RuntimeError("remote down"),
        ), patch(
            "services.nlp_task_service._query_local_task",
            return_value=local_result,
        ) as mock_local:
            result = query_nlp_task_progress("t3")
        assert result == local_result
        mock_local.assert_called_once_with("t3")

    def test_remote_error_without_fallback_raises(self, patched_config):
        """远程失败 + FALLBACK_LOCAL=False → 向上抛错"""
        patched_config.NLP_SERVICE_ENABLED = True
        patched_config.NLP_SERVICE_FALLBACK_LOCAL = False
        with patch(
            "services.nlp_task_service._query_remote_task",
            side_effect=RuntimeError("remote down"),
        ), patch(
            "services.nlp_task_service._query_local_task"
        ) as mock_local:
            with pytest.raises(RuntimeError, match="remote down"):
                query_nlp_task_progress("t4")
        mock_local.assert_not_called()

    def test_remote_error_logs_warning_when_falling_back(
        self, patched_config, caplog
    ):
        """回退时应记 warning 日志"""
        import logging

        patched_config.NLP_SERVICE_ENABLED = True
        patched_config.NLP_SERVICE_FALLBACK_LOCAL = True
        with patch(
            "services.nlp_task_service._query_remote_task",
            side_effect=ConnectionError("refused"),
        ), patch(
            "services.nlp_task_service._query_local_task",
            return_value={"task_id": "x"},
        ):
            with caplog.at_level(
                logging.WARNING, logger="services.nlp_task_service"
            ):
                query_nlp_task_progress("t5")
        assert any("回退本地查询" in r.message for r in caplog.records)
