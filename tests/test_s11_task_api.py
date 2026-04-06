"""S11: 验证任务状态 API 返回统一结构"""

import sys
from unittest.mock import MagicMock, patch

# Mock celery 依赖，使测试环境无需安装 celery
celery_mock = MagicMock()
celery_mock.current_task = MagicMock()
sys.modules.setdefault("celery", celery_mock)
sys.modules.setdefault("celery.result", MagicMock())


def _make_mock_result(state, info=None, result=None):
    r = MagicMock()
    r.state = state
    r.info = info
    r.result = result
    return r


def _call_get_task_progress(mock_result):
    """直接调用 _build_task_response 核心逻辑（不走 Celery）"""
    import importlib

    # 确保 tasks/__init__.py 不触发真实 celery 导入
    with patch.dict(
        sys.modules,
        {
            "tasks": MagicMock(),
            "tasks.celery_config": MagicMock(),
        },
    ):
        import importlib.util
        import os

        spec = importlib.util.spec_from_file_location(
            "celery_spider_mod",
            os.path.join(
                os.path.dirname(__file__), "..", "src", "tasks", "celery_spider.py"
            ),
        )
        mod = importlib.util.module_from_spec(spec)
        # Pre-populate sys.modules with mocks before exec
        sys.modules["tasks.celery_config"] = MagicMock()
        sys.modules["tasks.celery_spider"] = mod
        spec.loader.exec_module(mod)
        return mod._build_task_response(mock_result, "test-id-123")


def test_pending_has_all_fields():
    r = _make_mock_result("PENDING")
    resp = _call_get_task_progress(r)
    assert set(resp.keys()) >= {"task_id", "state", "progress", "message", "result"}
    assert resp["state"] == "PENDING"
    assert resp["progress"] == 0


def test_progress_has_all_fields():
    r = _make_mock_result(
        "PROGRESS", info={"current": 3, "total": 10, "status": "爬取中"}
    )
    resp = _call_get_task_progress(r)
    assert resp["state"] == "PROGRESS"
    assert resp["progress"] == 30
    assert "爬取中" in resp["message"]


def test_success_has_all_fields():
    r = _make_mock_result("SUCCESS", result={"crawled": 50})
    resp = _call_get_task_progress(r)
    assert resp["state"] == "SUCCESS"
    assert resp["progress"] == 100
    assert resp["result"] == {"crawled": 50}


def test_failure_has_all_fields():
    r = _make_mock_result("FAILURE", info=Exception("连接超时"))
    resp = _call_get_task_progress(r)
    assert resp["state"] == "FAILURE"
    assert "连接超时" in resp["message"]
