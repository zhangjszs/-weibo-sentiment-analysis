#!/usr/bin/env python3
"""
task_status_service.py 单元测试

task_status_service 是统一任务状态查询服务，实现 spider-remote → nlp-remote
→ local-celery 三级回退链。被 spider_routes 的 /api/tasks/<task_id>/status
端点调用。此前零单元测试覆盖。

测试策略：
- _is_not_found_error: 404 检测逻辑
- _query_local_task: mock AsyncResult 验证各 Celery 状态映射
- query_task_progress: mock 三个数据源 + Config 开关，验证回退链路

不触碰真实 Celery / 远程服务。
"""

import pytest

pytestmark = pytest.mark.unit

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from requests import HTTPError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.task_status_service import (
    _is_not_found_error,
    _query_local_task,
    query_task_progress,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_http_error(status_code: int) -> HTTPError:
    """构造带 response.status_code 的 HTTPError"""
    response = MagicMock()
    response.status_code = status_code
    return HTTPError(response=response)


def _make_async_result(
    state: str, info=None, result=None
) -> MagicMock:
    """构造模拟的 AsyncResult 对象"""
    mock = MagicMock()
    mock.state = state
    mock.info = info
    mock.result = result
    return mock


@pytest.fixture
def patched_config(monkeypatch):
    """提供可配置的 Config 开关，默认全部关闭（走 local）。

    必须改写服务实际引用的 Config 对象（``services.task_status_service.Config``），
    而非重新 ``from config.settings import Config``。原因：test_startup_service 与
    conftest 的 app fixture 会 ``importlib.reload(config.settings)``，reload 会替换
    ``Config`` 类对象——此时 ``task_status_service.Config``（导入时绑定）仍指向旧
    类，而重新 import 得到新类；patch 新类不影响服务读取的旧类（默认 False），
    导致服务跳过 spider/nlp 直接走 local，回退链测试全盘失配（评估 P0 #9）。
    """
    import services.task_status_service as tss

    monkeypatch.setattr(tss.Config, "SPIDER_SERVICE_ENABLED", False)
    monkeypatch.setattr(tss.Config, "NLP_SERVICE_ENABLED", False)
    return tss.Config


# ---------------------------------------------------------------------------
# _is_not_found_error
# ---------------------------------------------------------------------------


class TestIsNotFoundError:
    """404 错误检测逻辑"""

    def test_http_error_with_404_is_not_found(self):
        """HTTPError 且 status_code=404 → True"""
        exc = _make_http_error(404)
        assert _is_not_found_error(exc) is True

    def test_http_error_with_500_is_not_not_found(self):
        """HTTPError 且 status_code=500 → False"""
        exc = _make_http_error(500)
        assert _is_not_found_error(exc) is False

    def test_http_error_without_response_is_false(self):
        """HTTPError 但无 response → False"""
        exc = HTTPError("no response")
        assert _is_not_found_error(exc) is False

    def test_value_error_is_false(self):
        """非 HTTPError（ValueError）→ False"""
        assert _is_not_found_error(ValueError("not http")) is False

    def test_connection_error_is_false(self):
        """非 HTTPError（ConnectionError）→ False"""
        assert _is_not_found_error(ConnectionError("refused")) is False

    def test_none_response_is_false(self):
        """HTTPError 且 response=None → False（bool(None) is False）"""
        exc = HTTPError(response=None)
        assert _is_not_found_error(exc) is False


# ---------------------------------------------------------------------------
# _query_local_task
# ---------------------------------------------------------------------------


class TestQueryLocalTask:
    """本地 Celery 任务状态查询，各状态映射测试"""

    @patch("services.task_status_service.AsyncResult")
    def test_pending_state(self, mock_async):
        """PENDING → progress=0, message='任务等待中...'"""
        mock_async.return_value = _make_async_result("PENDING")
        result = _query_local_task("task-1")
        assert result["task_id"] == "task-1"
        assert result["state"] == "PENDING"
        assert result["progress"] == 0
        assert result["message"] == "任务等待中..."
        assert result["result"] == {}

    @patch("services.task_status_service.AsyncResult")
    def test_progress_state_calculates_percentage(self, mock_async):
        """PROGRESS → progress = current/total*100"""
        mock_async.return_value = _make_async_result(
            "PROGRESS", info={"current": 30, "total": 100, "status": "处理中"}
        )
        result = _query_local_task("task-2")
        assert result["progress"] == 30
        assert result["message"] == "处理中"

    @patch("services.task_status_service.AsyncResult")
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

    @patch("services.task_status_service.AsyncResult")
    def test_progress_state_none_info(self, mock_async):
        """PROGRESS 且 info=None → progress=0, message=''"""
        mock_async.return_value = _make_async_result("PROGRESS", info=None)
        result = _query_local_task("task-4")
        assert result["progress"] == 0
        assert result["message"] == ""

    @patch("services.task_status_service.AsyncResult")
    def test_progress_state_missing_fields(self, mock_async):
        """PROGRESS 且 info 缺少 current/total → 默认 0/1 → progress=0"""
        mock_async.return_value = _make_async_result(
            "PROGRESS", info={"status": "部分完成"}
        )
        result = _query_local_task("task-5")
        assert result["progress"] == 0  # int(0 / max(1,1) * 100) = 0
        assert result["message"] == "部分完成"

    @patch("services.task_status_service.AsyncResult")
    def test_success_state(self, mock_async):
        """SUCCESS → progress=100, result 填充, message='任务完成'"""
        mock_async.return_value = _make_async_result(
            "SUCCESS", result={"data": [1, 2, 3]}
        )
        result = _query_local_task("task-6")
        assert result["progress"] == 100
        assert result["result"] == {"data": [1, 2, 3]}
        assert result["message"] == "任务完成"

    @patch("services.task_status_service.AsyncResult")
    def test_success_state_none_result(self, mock_async):
        """SUCCESS 且 result=None → result={}（result.result or {}）"""
        mock_async.return_value = _make_async_result("SUCCESS", result=None)
        result = _query_local_task("task-7")
        assert result["result"] == {}
        assert result["progress"] == 100

    @patch("services.task_status_service.AsyncResult")
    def test_failure_state(self, mock_async):
        """FAILURE → message=str(result.info)"""
        mock_async.return_value = _make_async_result(
            "FAILURE", info="TaskError: something went wrong"
        )
        result = _query_local_task("task-8")
        assert result["state"] == "FAILURE"
        assert result["message"] == "TaskError: something went wrong"
        assert result["progress"] == 0

    @patch("services.task_status_service.AsyncResult")
    def test_unknown_state_defaults(self, mock_async):
        """未知状态（如 STARTED）→ 默认值 progress=0, message=''"""
        mock_async.return_value = _make_async_result("STARTED")
        result = _query_local_task("task-9")
        assert result["state"] == "STARTED"
        assert result["progress"] == 0
        assert result["message"] == ""
        assert result["result"] == {}

    @patch("services.task_status_service.AsyncResult")
    def test_uses_celery_app(self, mock_async):
        """应将 celery_app 传给 AsyncResult"""
        mock_async.return_value = _make_async_result("PENDING")
        _query_local_task("task-10")
        # AsyncResult(task_id, app=celery_app)
        call_kwargs = mock_async.call_args
        assert call_kwargs[0][0] == "task-10"
        assert "app" in call_kwargs[1]


# ---------------------------------------------------------------------------
# query_task_progress — 三级回退链
# ---------------------------------------------------------------------------


class TestQueryTaskProgressFallback:
    """query_task_progress 回退链路测试

    优先级：spider-remote → nlp-remote → local-celery
    404 错误静默降级，非 404 错误记 warning 后降级
    """

    def test_spider_enabled_returns_spider_result(self, patched_config, monkeypatch):
        """Spider 启用且成功 → 返回 spider 结果，不查 NLP / local"""
        monkeypatch.setattr(patched_config, "SPIDER_SERVICE_ENABLED", True)
        spider_result = {"task_id": "t1", "state": "SUCCESS", "progress": 100}
        with patch(
            "services.task_status_service.query_spider_remote",
            return_value=spider_result,
        ) as mock_spider, patch(
            "services.task_status_service.query_nlp_remote"
        ) as mock_nlp, patch(
            "services.task_status_service._query_local_task"
        ) as mock_local:
            result = query_task_progress("t1")
        assert result == spider_result
        mock_spider.assert_called_once_with("t1")
        mock_nlp.assert_not_called()
        mock_local.assert_not_called()

    def test_spider_404_falls_through_to_nlp(self, patched_config, monkeypatch):
        """Spider 返回 404 → 静默降级到 NLP（不记 warning）"""
        monkeypatch.setattr(patched_config, "SPIDER_SERVICE_ENABLED", True)
        monkeypatch.setattr(patched_config, "NLP_SERVICE_ENABLED", True)
        nlp_result = {"task_id": "t2", "state": "SUCCESS", "progress": 100}
        with patch(
            "services.task_status_service.query_spider_remote",
            side_effect=_make_http_error(404),
        ), patch(
            "services.task_status_service.query_nlp_remote",
            return_value=nlp_result,
        ) as mock_nlp:
            result = query_task_progress("t2")
        assert result == nlp_result
        mock_nlp.assert_called_once_with("t2")

    def test_spider_404_no_warning_logged(self, patched_config, monkeypatch, caplog):
        """Spider 404 不应记 warning（静默降级）"""
        import logging

        monkeypatch.setattr(patched_config, "SPIDER_SERVICE_ENABLED", True)
        with patch(
            "services.task_status_service.query_spider_remote",
            side_effect=_make_http_error(404),
        ), patch("services.task_status_service._query_local_task", return_value={}):
            with caplog.at_level(logging.WARNING, logger="services.task_status_service"):
                query_task_progress("t3")
        assert not any("Spider 远程" in r.message for r in caplog.records)

    def test_spider_non_404_logs_warning(self, patched_config, monkeypatch, caplog):
        """Spider 非 404 错误应记 warning"""
        import logging

        monkeypatch.setattr(patched_config, "SPIDER_SERVICE_ENABLED", True)
        with patch(
            "services.task_status_service.query_spider_remote",
            side_effect=_make_http_error(500),
        ), patch("services.task_status_service._query_local_task", return_value={}):
            with caplog.at_level(logging.WARNING, logger="services.task_status_service"):
                query_task_progress("t4")
        assert any("Spider 远程" in r.message for r in caplog.records)

    def test_spider_non_404_falls_through_to_local(self, patched_config, monkeypatch):
        """Spider 非 404 错误 → 记 warning 后降级到 local（NLP 未启用）"""
        monkeypatch.setattr(patched_config, "SPIDER_SERVICE_ENABLED", True)
        local_result = {"task_id": "t5", "state": "PENDING"}
        with patch(
            "services.task_status_service.query_spider_remote",
            side_effect=ConnectionError("refused"),
        ), patch(
            "services.task_status_service._query_local_task",
            return_value=local_result,
        ) as mock_local:
            result = query_task_progress("t5")
        assert result == local_result
        mock_local.assert_called_once_with("t5")

    def test_nlp_enabled_returns_nlp_result(self, patched_config, monkeypatch):
        """Spider 未启用 + NLP 启用且成功 → 返回 NLP 结果"""
        monkeypatch.setattr(patched_config, "NLP_SERVICE_ENABLED", True)
        nlp_result = {"task_id": "t6", "state": "PROGRESS", "progress": 50}
        with patch(
            "services.task_status_service.query_nlp_remote",
            return_value=nlp_result,
        ) as mock_nlp, patch(
            "services.task_status_service._query_local_task"
        ) as mock_local:
            result = query_task_progress("t6")
        assert result == nlp_result
        mock_nlp.assert_called_once_with("t6")
        mock_local.assert_not_called()

    def test_nlp_404_falls_through_to_local(self, patched_config, monkeypatch):
        """NLP 返回 404 → 静默降级到 local"""
        monkeypatch.setattr(patched_config, "NLP_SERVICE_ENABLED", True)
        local_result = {"task_id": "t7", "state": "SUCCESS"}
        with patch(
            "services.task_status_service.query_nlp_remote",
            side_effect=_make_http_error(404),
        ), patch(
            "services.task_status_service._query_local_task",
            return_value=local_result,
        ) as mock_local:
            result = query_task_progress("t7")
        assert result == local_result
        mock_local.assert_called_once_with("t7")

    def test_nlp_non_404_logs_warning(self, patched_config, monkeypatch, caplog):
        """NLP 非 404 错误应记 warning"""
        import logging

        monkeypatch.setattr(patched_config, "NLP_SERVICE_ENABLED", True)
        with patch(
            "services.task_status_service.query_nlp_remote",
            side_effect=_make_http_error(503),
        ), patch("services.task_status_service._query_local_task", return_value={}):
            with caplog.at_level(logging.WARNING, logger="services.task_status_service"):
                query_task_progress("t8")
        assert any("NLP 远程" in r.message for r in caplog.records)

    def test_both_disabled_goes_straight_to_local(self, patched_config):
        """Spider + NLP 均未启用 → 直接查 local"""
        local_result = {"task_id": "t9", "state": "PENDING"}
        with patch(
            "services.task_status_service._query_local_task",
            return_value=local_result,
        ) as mock_local, patch(
            "services.task_status_service.query_spider_remote"
        ) as mock_spider, patch(
            "services.task_status_service.query_nlp_remote"
        ) as mock_nlp:
            result = query_task_progress("t9")
        assert result == local_result
        mock_local.assert_called_once_with("t9")
        mock_spider.assert_not_called()
        mock_nlp.assert_not_called()

    def test_both_enabled_both_fail_falls_to_local(self, patched_config, monkeypatch):
        """Spider + NLP 均启用但都失败 → 降级到 local"""
        monkeypatch.setattr(patched_config, "SPIDER_SERVICE_ENABLED", True)
        monkeypatch.setattr(patched_config, "NLP_SERVICE_ENABLED", True)
        local_result = {"task_id": "t10", "state": "FAILURE"}
        with patch(
            "services.task_status_service.query_spider_remote",
            side_effect=_make_http_error(404),
        ), patch(
            "services.task_status_service.query_nlp_remote",
            side_effect=_make_http_error(404),
        ), patch(
            "services.task_status_service._query_local_task",
            return_value=local_result,
        ) as mock_local:
            result = query_task_progress("t10")
        assert result == local_result
        mock_local.assert_called_once_with("t10")

    def test_spider_success_skips_nlp(self, patched_config, monkeypatch):
        """Spider 成功 → NLP 完全不调用（短路）"""
        monkeypatch.setattr(patched_config, "SPIDER_SERVICE_ENABLED", True)
        monkeypatch.setattr(patched_config, "NLP_SERVICE_ENABLED", True)
        spider_result = {"task_id": "t11", "state": "SUCCESS", "progress": 100}
        with patch(
            "services.task_status_service.query_spider_remote",
            return_value=spider_result,
        ), patch(
            "services.task_status_service.query_nlp_remote"
        ) as mock_nlp, patch(
            "services.task_status_service._query_local_task"
        ) as mock_local:
            result = query_task_progress("t11")
        assert result == spider_result
        mock_nlp.assert_not_called()
        mock_local.assert_not_called()

    def test_spider_disabled_nlp_succeeds_skips_local(self, patched_config, monkeypatch):
        """Spider 未启用 + NLP 成功 → local 不调用"""
        monkeypatch.setattr(patched_config, "NLP_SERVICE_ENABLED", True)
        nlp_result = {"task_id": "t12", "state": "SUCCESS", "progress": 100}
        with patch(
            "services.task_status_service.query_nlp_remote",
            return_value=nlp_result,
        ), patch(
            "services.task_status_service._query_local_task"
        ) as mock_local:
            result = query_task_progress("t12")
        assert result == nlp_result
        mock_local.assert_not_called()

    def test_non_http_error_falls_through_with_warning(
        self, patched_config, monkeypatch, caplog
    ):
        """非 HTTPError（如 ValueError）应记 warning 并降级"""
        import logging

        monkeypatch.setattr(patched_config, "SPIDER_SERVICE_ENABLED", True)
        with patch(
            "services.task_status_service.query_spider_remote",
            side_effect=ValueError("bad response format"),
        ), patch("services.task_status_service._query_local_task", return_value={}):
            with caplog.at_level(logging.WARNING, logger="services.task_status_service"):
                query_task_progress("t13")
        assert any("Spider 远程" in r.message for r in caplog.records)
