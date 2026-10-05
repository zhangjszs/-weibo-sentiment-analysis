#!/usr/bin/env python3
"""/api/* GET 端点 envelope 契约测试（#44）。

从 ``app.url_map`` 枚举全部 GET 路由表驱动执行（2026-10-05 实测 51 个），
对每个端点的三种视角断言统一响应契约：

- 未登录：除白名单（/api/session/check）外一律 401，且 401 也是标准 envelope；
- 已登录非管理员：管理员端点一律 403（envelope），其余不得 401/403；
- 已登录管理员：管理员端点 200；
- 任意视角：``body.code == HTTP 状态码``；五字段 code/msg/timestamp/request_id/data
  规则成立；``request_id`` 与响应头 ``X-Request-Id`` 一致；无裸 5xx（豁免表除外）。

豁免表：任何 5xx 必须在此给出原因与后续 issue，否则测试失败。
"""

from __future__ import annotations

import re

import pytest

pytestmark = pytest.mark.api

from services.task_status_service import TaskStatusUnavailable  # noqa: E402

# ---------------------------------------------------------------------------
# 路由枚举（collection 时一次性建 app，仅取 url_map）
# ---------------------------------------------------------------------------

# path 参数替身：覆盖「存在性 404 / 参数校验 400」即可，envelope 断言不依赖业务成功
_ARG_SUBS = {
    "article_id": "1",
    "platform": "weibo",
    "filename": "x.docx",
    "task_id": "abc",
}

_ARG_RE = re.compile(r"<(?:[^<>:]+:)?([^<>]+)>")


def _enumerate_get_routes():
    from app import create_app

    app = create_app()
    routes = []
    for rule in app.url_map.iter_rules():
        if "GET" not in rule.methods or not rule.rule.startswith("/api/"):
            continue
        path = _ARG_RE.sub(lambda m: _ARG_SUBS.get(m.group(1), "x"), rule.rule)
        routes.append((path, rule.rule))
    return sorted(set(routes))


_PARAMS = _enumerate_get_routes()

# ---------------------------------------------------------------------------
# 契约白名单 / 豁免表（以实测为据，变更需有意识更新）
# ---------------------------------------------------------------------------

# 匿名可访问的 GET 端点（实测 2026-10-05：仅会话检查）
PUBLIC_GET = {"/api/session/check"}

# @admin_required 的 GET 端点（grep src/views/api + 非管理员 403 实测；非管理员访问 → 403）
ADMIN_GET = {
    "/api/audit/logs",
    "/api/alert/rules",
    "/api/alert/history",
    "/api/alert/stats",
    "/api/alert/unread-count",
    "/api/health/details",
    "/api/spider/overview",
    "/api/spider/status",
    "/api/spider/logs",
    "/api/startup/status",
    "/api/tasks/<task_id>/status",
}

# 成功时返回文件流而非 JSON 的端点（2xx 非 JSON 放行；4xx 仍走 envelope）
FILE_ENDPOINTS = {
    "/api/report/download/<filename>",
    "/api/report/preview/<filename>",
}

# 5xx 豁免表：{路由模板: (原因, 后续 issue)}。除此之外断言零 5xx。
EXEMPT_5XX = {
    "/api/getContentCloudData": (
        "空库时 wordcloud 抛 ValueError('We need at least 1 word...') → 500；"
        "envelope 完好。空数据应回 200 空态还是 4xx 属前端消费契约，由 #45 定夺",
        "#45",
    ),
}

ENVELOPE_FIELDS = ("code", "msg", "timestamp", "request_id")


# ---------------------------------------------------------------------------
# 断言助手
# ---------------------------------------------------------------------------


def _assert_envelope(resp, template):
    """统一 envelope 断言：code==状态码、字段齐备、request_id 与响应头一致。

    不变量对任意状态码成立；``data`` 仅要求 2xx JSON 响应必含（4xx/5xx 的
    data 属可选扩展，如 propagation 404 附带 article_id）。
    """
    if resp.status_code >= 500:
        reason = EXEMPT_5XX.get(template)
        assert reason, f"{template} 返回未豁免的 5xx：{resp.status_code}"

    if (
        200 <= resp.status_code < 300
        and template in FILE_ENDPOINTS
        and not resp.is_json
    ):
        return  # 文件流成功响应，envelope 不适用

    assert resp.is_json, f"{template} 返回非 JSON：{resp.status_code} {resp.data[:120]!r}"
    body = resp.get_json()
    assert body["code"] == resp.status_code, (
        f"{template}: body.code={body['code']} != HTTP {resp.status_code}"
    )
    for field in ENVELOPE_FIELDS:
        assert field in body, f"{template}: envelope 缺字段 {field}（{body}）"
    assert body["request_id"] == resp.headers.get("X-Request-Id"), (
        f"{template}: request_id 与 X-Request-Id 头不一致"
    )
    if 200 <= resp.status_code < 300:
        assert "data" in body, f"{template}: 2xx 响应缺少 data 字段（{body}）"


# ---------------------------------------------------------------------------
# 表驱动契约
# ---------------------------------------------------------------------------


_CASES = [pytest.param((path, template), id=path) for path, template in _PARAMS]


@pytest.mark.parametrize("case", _CASES)
class TestGetEndpointsEnvelope:
    """全部 /api/* GET 端点的三视角 envelope 契约。"""

    def test_anonymous(self, client, case):
        """未登录：白名单 200，其余 401，且均为标准 envelope。"""
        path, template = case
        resp = client.get(path)
        if template in PUBLIC_GET:
            assert resp.status_code == 200
            _assert_envelope(resp, template)
        else:
            assert resp.status_code == 401, f"{template} 匿名访问应 401"
            _assert_envelope(resp, template)

    def test_authenticated_non_admin(self, authed_client, case):
        """已登录非管理员：管理员端点 403，其余 2xx/4xx（不得 401，且非 5xx）。"""
        path, template = case
        resp = authed_client.get(path)
        if template in ADMIN_GET:
            assert resp.status_code == 403, f"{template} 非管理员应 403"
            _assert_envelope(resp, template)
        else:
            assert resp.status_code != 401, f"{template} 已登录仍 401"
            _assert_envelope(resp, template)

    def test_authenticated_admin(self, authed_client, monkeypatch, case):
        """已登录管理员：管理员端点必须 200（envelope 完整）。"""
        path, template = case
        if template not in ADMIN_GET:
            pytest.skip("仅管理员端点需要管理员视角断言")
        from utils import authz

        monkeypatch.setattr(authz.Config, "ADMIN_USERS", {"tester"})
        resp = authed_client.get(path)
        assert resp.status_code == 200, f"{template} 管理员访问应 200"
        _assert_envelope(resp, template)


# ---------------------------------------------------------------------------
# 5xx 修复回归：任务状态端点在后端不可用时转 503 envelope（#44 实证修复）
# ---------------------------------------------------------------------------


class TestTaskStatusDegradationContract:
    """Redis 不可用时 /api/tasks/<id>/status 不得返回 Werkzeug HTML 500。"""

    def test_backend_down_returns_503_envelope(self, authed_client, monkeypatch):
        from utils import authz

        monkeypatch.setattr(authz.Config, "ADMIN_USERS", {"tester"})
        # 路由模块 `from ... import query_task_progress` 直引，须 patch 路由命名空间
        def _raise(task_id):
            raise TaskStatusUnavailable("redis down")

        monkeypatch.setattr("views.api.spider_routes.query_task_progress", _raise)
        resp = authed_client.get("/api/tasks/abc/status")
        assert resp.status_code == 503
        body = resp.get_json()
        assert body["code"] == 503
        assert body["request_id"] == resp.headers["X-Request-Id"]
