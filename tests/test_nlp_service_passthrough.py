#!/usr/bin/env python3
"""
Phase 3.8: nlp_service HTTP 透传单元测试。

验证 nlp_service/app/tasks.py 不再做任何本地 NLP 计算，而是通过 requests
POST 到主后端的 /api/sentiment/analyze、/api/predict/batch、/api/model/retrain。

注意：nlp_service 的 `app` 包与 src/app.py 存在命名冲突，因此本测试文件
临时将 nlp_service/ 加入 sys.path 完成导入后立即移除；conftest.py 的 `app`
fixture 会清理 sys.modules["app*"]，其他测试不受影响。
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# 隔离导入 nlp_service.app.tasks（避免与 src/app.py 冲突）
# ---------------------------------------------------------------------------

_NLP_DIR = str(Path(__file__).resolve().parent.parent / "nlp_service")

# 清除可能存在的 src/app.py 缓存，确保 from app.tasks import ... 能找到 nlp_service/app/
_saved_app_mods: dict[str, object] = {}
for _mod in list(sys.modules):
    if _mod == "app" or _mod.startswith("app."):
        _saved_app_mods[_mod] = sys.modules.pop(_mod)

sys.path.insert(0, _NLP_DIR)
try:
    from app.tasks import (  # type: ignore[import-not-found]
        DEFAULT_BACKEND_URL,
        _auth_headers,
        _backend_url,
        _backend_timeout,
        _post,
        analyze_batch_sync,
        analyze_sequence_sync,
        analyze_text_sync,
    )
finally:
    # 移除 path，但保留 nlp_service 的 app.tasks 在 sys.modules 中
    # conftest.py 的 app fixture 会通过 del sys.modules["app*"] 清理
    if _NLP_DIR in sys.path:
        sys.path.remove(_NLP_DIR)


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


def _make_response(json_body: dict | None = None, status_code: int = 200, text: str = ""):
    """构造一个 mock requests.Response 对象。"""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if json_body is not None:
        resp.json.return_value = json_body
    else:
        resp.json.side_effect = ValueError("not json")
    return resp


# ---------------------------------------------------------------------------
# _backend_url / _backend_timeout / _auth_headers 配置测试
# ---------------------------------------------------------------------------


class TestBackendConfig:
    def test_default_backend_url(self, monkeypatch):
        monkeypatch.delenv("NLP_BACKEND_URL", raising=False)
        assert _backend_url() == DEFAULT_BACKEND_URL

    def test_custom_backend_url_from_env(self, monkeypatch):
        monkeypatch.setenv("NLP_BACKEND_URL", "http://custom-host:9999/")
        assert _backend_url() == "http://custom-host:9999"

    def test_empty_backend_url_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv("NLP_BACKEND_URL", "  ")
        assert _backend_url() == DEFAULT_BACKEND_URL

    def test_default_timeout(self, monkeypatch):
        monkeypatch.delenv("NLP_BACKEND_TIMEOUT", raising=False)
        assert _backend_timeout() == 20.0

    def test_custom_timeout(self, monkeypatch):
        monkeypatch.setenv("NLP_BACKEND_TIMEOUT", "5.5")
        assert _backend_timeout() == 5.5

    def test_invalid_timeout_falls_back(self, monkeypatch):
        monkeypatch.setenv("NLP_BACKEND_TIMEOUT", "not-a-number")
        assert _backend_timeout() == 20.0

    def test_auth_headers_empty_without_token(self, monkeypatch):
        monkeypatch.delenv("NLP_SERVICE_TOKEN", raising=False)
        headers = _auth_headers()
        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"

    def test_auth_headers_with_token(self, monkeypatch):
        monkeypatch.setenv("NLP_SERVICE_TOKEN", "secret-token")
        headers = _auth_headers()
        assert headers["Authorization"] == "Bearer secret-token"


# ---------------------------------------------------------------------------
# _post 透传核心测试
# ---------------------------------------------------------------------------


class TestPost:
    def test_returns_data_on_success(self):
        resp = _make_response({"code": 200, "msg": "ok", "data": {"label": "positive"}})
        with patch("app.tasks.requests.post", return_value=resp) as mock_post:
            data = _post("/api/sentiment/analyze", {"text": "hello"})
        assert data == {"label": "positive"}
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "/api/sentiment/analyze" in args[0]
        assert kwargs["json"] == {"text": "hello"}

    def test_returns_empty_dict_when_data_missing(self):
        resp = _make_response({"code": 200, "msg": "ok"})
        with patch("app.tasks.requests.post", return_value=resp):
            data = _post("/api/sentiment/analyze", {"text": "hello"})
        assert data == {}

    def test_raises_on_http_error_status(self):
        resp = _make_response({"code": 500, "msg": "server error"}, status_code=500)
        with patch("app.tasks.requests.post", return_value=resp):
            with pytest.raises(RuntimeError, match="server error"):
                _post("/api/sentiment/analyze", {"text": "hello"})

    def test_raises_on_api_error_code(self):
        """HTTP 200 但 body.code >= 400 也应报错。"""
        resp = _make_response({"code": 400, "msg": "bad request"}, status_code=200)
        with patch("app.tasks.requests.post", return_value=resp):
            with pytest.raises(RuntimeError, match="bad request"):
                _post("/api/sentiment/analyze", {"text": "hello"})

    def test_raises_on_request_exception(self):
        import requests as _requests

        with patch("app.tasks.requests.post", side_effect=_requests.ConnectionError("refused")):
            with pytest.raises(RuntimeError, match="主后端不可用"):
                _post("/api/sentiment/analyze", {"text": "hello"})

    def test_raises_on_non_json_response(self):
        resp = _make_response(status_code=200, text="<html>error</html>")
        with patch("app.tasks.requests.post", return_value=resp):
            with pytest.raises(RuntimeError, match="主后端响应解析失败"):
                _post("/api/sentiment/analyze", {"text": "hello"})


# ---------------------------------------------------------------------------
# analyze_text_sync 测试
# ---------------------------------------------------------------------------


class TestAnalyzeTextSync:
    def test_raises_on_empty_text(self):
        with pytest.raises(ValueError, match="text is required"):
            analyze_text_sync("", mode="custom")

    def test_raises_on_whitespace_only_text(self):
        with pytest.raises(ValueError, match="text is required"):
            analyze_text_sync("   ", mode="custom")

    def test_posts_correct_payload(self):
        resp = _make_response({"code": 200, "data": {"label": "positive", "score": 0.9}})
        with patch("app.tasks.requests.post", return_value=resp) as mock_post:
            result = analyze_text_sync("好开心", mode="custom")
        assert result == {"label": "positive", "score": 0.9}
        args, kwargs = mock_post.call_args
        assert args[0].endswith("/api/sentiment/analyze")
        assert kwargs["json"] == {"text": "好开心", "mode": "custom", "async": False}

    def test_strips_text_before_sending(self):
        resp = _make_response({"code": 200, "data": {}})
        with patch("app.tasks.requests.post", return_value=resp) as mock_post:
            analyze_text_sync("  hello  ", mode="simple")
        kwargs = mock_post.call_args.kwargs
        assert kwargs["json"]["text"] == "hello"


# ---------------------------------------------------------------------------
# analyze_batch_sync 测试
# ---------------------------------------------------------------------------


class TestAnalyzeBatchSync:
    def test_raises_on_empty_list(self):
        with pytest.raises(ValueError, match="texts 必须是非空数组"):
            analyze_batch_sync([], mode="custom")

    def test_raises_on_non_list(self):
        with pytest.raises(ValueError, match="texts 必须是非空数组"):
            analyze_batch_sync("not a list", mode="custom")  # type: ignore[arg-type]

    def test_raises_on_too_many_texts(self):
        texts = [f"text{i}" for i in range(101)]
        with pytest.raises(ValueError, match="单次最多预测100条文本"):
            analyze_batch_sync(texts, mode="custom")

    def test_returns_results_list(self):
        resp = _make_response(
            {"code": 200, "data": {"total": 2, "results": [{"label": "positive"}, {"label": "negative"}]}}
        )
        with patch("app.tasks.requests.post", return_value=resp) as mock_post:
            results = analyze_batch_sync(["好", "差"], mode="custom")
        assert len(results) == 2
        assert results[0]["label"] == "positive"
        args, kwargs = mock_post.call_args
        assert args[0].endswith("/api/predict/batch")
        assert kwargs["json"]["texts"] == ["好", "差"]
        assert kwargs["json"]["mode"] == "custom"

    def test_returns_empty_list_when_no_results(self):
        resp = _make_response({"code": 200, "data": {"total": 0}})
        with patch("app.tasks.requests.post", return_value=resp):
            results = analyze_batch_sync(["x"], mode="custom")
        assert results == []


# ---------------------------------------------------------------------------
# analyze_sequence_sync 测试
# ---------------------------------------------------------------------------


class TestAnalyzeSequenceSync:
    def test_empty_input_returns_neutral(self):
        result = analyze_sequence_sync([], mode="custom")
        assert result["analysis_count"] == 0
        assert result["overall_sentiment"]["label"] == "neutral"
        assert result["overall_sentiment"]["score"] == 0.5
        assert result["sequence_analysis"] == []
        assert result["sentiment_changes"] == []

    def test_analyzes_each_text_and_aggregates(self):
        responses = [
            _make_response({"code": 200, "data": {"score": 0.9, "label": "positive", "emotion": "喜悦"}}),
            _make_response({"code": 200, "data": {"score": 0.1, "label": "negative", "emotion": "愤怒"}}),
        ]
        with patch("app.tasks.requests.post", side_effect=responses):
            result = analyze_sequence_sync(["好开心", "太差了"], mode="custom")
        assert result["analysis_count"] == 2
        assert result["sequence_analysis"][0]["sentiment"]["label"] == "positive"
        assert result["sequence_analysis"][1]["sentiment"]["label"] == "negative"
        # 平均分 (0.9+0.1)/2 = 0.5 → neutral
        assert result["overall_sentiment"]["label"] == "neutral"

    def test_detects_sentiment_change(self):
        """分数差 > 0.3 应记录到 sentiment_changes。"""
        responses = [
            _make_response({"code": 200, "data": {"score": 0.9, "label": "positive", "emotion": "喜悦"}}),
            _make_response({"code": 200, "data": {"score": 0.1, "label": "negative", "emotion": "悲伤"}}),
        ]
        with patch("app.tasks.requests.post", side_effect=responses):
            result = analyze_sequence_sync(["好", "差"], mode="custom")
        assert len(result["sentiment_changes"]) == 1
        change = result["sentiment_changes"][0]
        assert change["from_index"] == 0
        assert change["to_index"] == 1
        assert change["from_score"] == 0.9
        assert change["to_score"] == 0.1
        assert change["change_score"] == pytest.approx(0.8)

    def test_detects_emotion_transition(self):
        responses = [
            _make_response({"code": 200, "data": {"score": 0.5, "label": "neutral", "emotion": "平静"}}),
            _make_response({"code": 200, "data": {"score": 0.5, "label": "neutral", "emotion": "焦虑"}}),
        ]
        with patch("app.tasks.requests.post", side_effect=responses):
            result = analyze_sequence_sync(["ok", "worried"], mode="custom")
        assert len(result["emotion_transitions"]) == 1
        assert result["emotion_transitions"][0]["from_emotion"] == "平静"
        assert result["emotion_transitions"][0]["to_emotion"] == "焦虑"
        # 分数差 = 0，无 sentiment_change
        assert result["sentiment_changes"] == []

    def test_fallback_on_analysis_error(self):
        """单条分析失败应回退中性，不中断序列。"""
        resp = _make_response({"code": 200, "data": {"score": 0.9, "label": "positive", "emotion": "喜悦"}})
        with patch("app.tasks.requests.post", side_effect=[RuntimeError("backend down"), resp]):
            result = analyze_sequence_sync(["fail", "ok"], mode="custom")
        assert result["analysis_count"] == 2
        assert result["sequence_analysis"][0]["sentiment"]["label"] == "neutral"
        assert result["sequence_analysis"][0]["sentiment"].get("error") is True
        assert result["sequence_analysis"][1]["sentiment"]["label"] == "positive"

    def test_overall_label_positive(self):
        resp = _make_response({"code": 200, "data": {"score": 0.9, "label": "positive", "emotion": "喜悦"}})
        with patch("app.tasks.requests.post", return_value=resp):
            result = analyze_sequence_sync(["好", "棒"], mode="custom")
        assert result["overall_sentiment"]["label"] == "positive"

    def test_overall_label_negative(self):
        resp = _make_response({"code": 200, "data": {"score": 0.1, "label": "negative", "emotion": "悲伤"}})
        with patch("app.tasks.requests.post", return_value=resp):
            result = analyze_sequence_sync(["差", "烂"], mode="custom")
        assert result["overall_sentiment"]["label"] == "negative"
