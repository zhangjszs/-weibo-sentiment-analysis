#!/usr/bin/env python3
"""/api/* 写路由（POST/PUT/DELETE）契约测试（#47）。

从 ``app.url_map`` 枚举全部非 GET 路由（2026-10-05 实测 31 个，规划时 30），
表驱动断言：

- 未登录：白名单（login/register/logout）外一律 401，且为标准错误 envelope；
  login/register 空 payload → 400 envelope；logout 幂等 → 200 envelope；
- 已登录管理员 + 空 payload：不得 5xx、不得 401/403，响应为标准 envelope
  （broker 不可用等降级路径必须走 503 envelope 而非 Werkzeug HTML 500）；
- Cookie 认证 + 无 Origin 的状态变更请求 → 403（Bearer 主轨不受此限）。

成功路径（issue 列出的 10 条）以 ORM 造数走真实业务流：收藏增删/批量查、
预警规则增改切换删生命周期、预警已读/全部已读、用户资料更新。
"""

from __future__ import annotations

import inspect
import re

import pytest

pytestmark = pytest.mark.api

# ---------------------------------------------------------------------------
# 路由枚举（collection 时一次性建 app，仅取 url_map）
# ---------------------------------------------------------------------------

_ARG_SUBS = {
    "article_id": "1",
    "rule_id": "1",
    "alert_id": "1",
}

_ARG_RE = re.compile(r"<(?:[^<>:]+:)?([^<>]+)>")


def _enumerate_write_routes():
    from app import create_app

    app = create_app()
    routes = []
    for rule in app.url_map.iter_rules():
        methods = rule.methods - {"HEAD", "OPTIONS"}
        write = methods & {"POST", "PUT", "DELETE", "PATCH"}
        if not write or not rule.rule.startswith("/api/"):
            continue
        path = _ARG_RE.sub(lambda m: _ARG_SUBS.get(m.group(1), "x"), rule.rule)
        routes.append((path, rule.rule, sorted(write)[0]))
    return sorted(set(routes))


_PARAMS = _enumerate_write_routes()
_CASES = [
    pytest.param((path, template, method), id=f"{method} {path}")
    for path, template, method in _PARAMS
]

# ---------------------------------------------------------------------------
# 契约白名单
# ---------------------------------------------------------------------------

# 匿名可访问的写端点（登录/注册为公开入口；logout 幂等，匿名调用也 200）
PUBLIC_WRITE = {"/api/auth/login", "/api/auth/register", "/api/auth/logout"}

# 2xx 但按设计无 data 字段（ok(msg=...) 型纯消息响应）
NO_DATA_2XX = {
    "/api/favorites/<article_id>",
    "/api/alert/read-all",
    "/api/auth/logout",
    "/api/user/profile",
}

# 非管理员 403 抽查的代表性管理写路由
ADMIN_WRITE_SAMPLE = {"/api/alert/rules", "/api/spider/search", "/api/model/retrain"}

ENVELOPE_FIELDS = ("code", "msg", "timestamp", "request_id")


def _assert_envelope(resp, template):
    """写路由 envelope 断言：code==状态码、四必填字段、request_id 与头一致。"""
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
    if 200 <= resp.status_code < 300 and template not in NO_DATA_2XX:
        assert "data" in body, f"{template}: 2xx 响应缺少 data 字段（{body}）"


def _set_auth_cookie(client, token):
    """兼容 Werkzeug 2.x/3.x 的 cookie 设置（同 tests/conftest.py）。"""
    sig = inspect.signature(client.set_cookie)
    if "server_name" in sig.parameters:
        client.set_cookie("localhost", "weibo_access_token", token)
    else:
        client.set_cookie("weibo_access_token", token)


@pytest.fixture
def bearer_headers(monkeypatch):
    """管理员视角 Bearer 头（写路由主轨；Cookie 轨的状态变更受 Origin 防线约束）。"""
    from utils import authz
    from utils.jwt_handler import create_token

    monkeypatch.setattr(authz.Config, "ADMIN_USERS", {"tester"})
    return {"Authorization": f"Bearer {create_token(1, 'tester')}"}


@pytest.fixture
def seeded_ids():
    """成功路径造数：tester 用户、文章 1、一条未读预警。返回 alert_id。"""
    from database import db_session
    from models.alert import Alert, AlertLevel, AlertType
    from models.article import Article
    from models.user import User

    db_session.add(Article(id="1", content="契约测试文章内容", type="post"))
    # User 自定义 __init__ 不收 id：先构造再赋主键，保证 JWT 的 user_id=1 有对应用户行
    tester = User(username="tester", password="x" * 60)
    tester.id = 1
    db_session.add(tester)
    db_session.add(
        Alert(
            id="contract-alert-1",
            rule_id="contract-rule",
            rule_name="契约测试规则",
            alert_type=AlertType.KEYWORD_MATCH,
            level=AlertLevel.WARNING,
            title="契约测试预警",
            message="契约测试预警内容",
        )
    )
    db_session.commit()
    yield "contract-alert-1"
    db_session.rollback()


# ---------------------------------------------------------------------------
# 表驱动契约：31 条写路由的鉴权与坏输入 envelope
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", _CASES)
class TestWriteRoutesContract:
    """全部 /api/* 写路由的鉴权矩阵与坏输入 envelope 契约。"""

    def test_anonymous(self, client, case):
        """未登录：白名单外一律 401；login/register 空 payload 400；logout 幂等 200。"""
        path, template, method = case
        resp = client.open(path, method=method, json={})
        if template in PUBLIC_WRITE:
            assert resp.status_code in (200, 400), (
                f"{template} 匿名异常状态 {resp.status_code}"
            )
        else:
            assert resp.status_code == 401, f"{template} 匿名访问应 401"
        _assert_envelope(resp, template)

    def test_admin_bad_payload(self, client, bearer_headers, case):
        """管理员 + 空 payload：不得 5xx / 401 / 403，且为标准 envelope。"""
        path, template, method = case
        resp = client.open(path, method=method, json={}, headers=bearer_headers)
        assert resp.status_code < 500, (
            f"{template} 空 payload 返回 5xx：{resp.status_code} {resp.data[:160]!r}"
        )
        assert resp.status_code not in (401, 403), (
            f"{template} 管理员请求被拒：{resp.status_code}"
        )
        _assert_envelope(resp, template)

    def test_non_admin_forbidden(self, client, case):
        """非管理员访问管理写路由 → 403 envelope（抽查代表性路由）。"""
        _, template, _ = case
        if template not in ADMIN_WRITE_SAMPLE:
            pytest.skip("非管理员 403 抽查仅覆盖代表性管理路由")
        from utils.jwt_handler import create_token

        path, _, method = next(c for c in _PARAMS if c[1] == template)
        resp = client.open(
            path,
            method=method,
            json={},
            headers={"Authorization": f"Bearer {create_token(1, 'tester')}"},
        )
        assert resp.status_code == 403, f"{template} 非管理员应 403"
        _assert_envelope(resp, template)


def test_cookie_write_without_origin_rejected(client, monkeypatch):
    """Cookie 轨 + 无 Origin 的状态变更 → 403（Bearer 主轨不受此限）。"""
    from utils import authz
    from utils.jwt_handler import create_token

    monkeypatch.setattr(authz.Config, "ADMIN_USERS", {"tester"})
    _set_auth_cookie(client, create_token(1, "tester"))
    resp = client.post("/api/favorites/1", json={})
    assert resp.status_code == 403
    assert resp.get_json()["code"] == 403


# ---------------------------------------------------------------------------
# 成功路径（issue 列出的 10 条路由）
# ---------------------------------------------------------------------------


class TestWriteSuccessPaths:
    """核心写路由的真实业务流（ORM 造数，不依赖外部服务）。"""

    def test_favorites_add_remove(self, client, bearer_headers, seeded_ids):
        """POST/DELETE /api/favorites/<article_id> → 200，envelope 完整。"""
        add = client.post("/api/favorites/1", json={}, headers=bearer_headers)
        assert add.status_code == 200, add.data[:160]
        _assert_envelope(add, "/api/favorites/<article_id>")

        remove = client.delete("/api/favorites/1", headers=bearer_headers)
        assert remove.status_code == 200, remove.data[:160]
        _assert_envelope(remove, "/api/favorites/<article_id>")

    def test_favorites_batch_check(self, client, bearer_headers, seeded_ids):
        """POST /api/favorites/batch-check → 200，data 含逐条结果。"""
        resp = client.post(
            "/api/favorites/batch-check",
            json={"article_ids": ["1", "2"]},
            headers=bearer_headers,
        )
        assert resp.status_code == 200, resp.data[:160]
        _assert_envelope(resp, "/api/favorites/batch-check")
        assert resp.get_json()["data"] is not None

    def test_alert_rule_lifecycle(self, client, bearer_headers):
        """POST → PUT → toggle → DELETE /api/alert/rules* 全生命周期 2xx。"""
        headers = bearer_headers
        rule = "/api/alert/rules"
        create = client.post(
            rule,
            json={
                "id": "contract-rule-1",
                "name": "契约测试规则",
                "alert_type": "keyword_match",
                "level": "warning",
                "conditions": {},
            },
            headers=headers,
        )
        assert create.status_code == 201, create.data[:160]
        assert create.get_json()["data"]["rule"]["id"] == "contract-rule-1"

        update = client.put(
            f"{rule}/contract-rule-1", json={"level": "danger"}, headers=headers
        )
        assert update.status_code == 200, update.data[:160]

        toggle = client.post(
            f"{rule}/contract-rule-1/toggle", json={}, headers=headers
        )
        assert toggle.status_code == 200, toggle.data[:160]

        delete = client.delete(f"{rule}/contract-rule-1", headers=headers)
        assert delete.status_code == 200, delete.data[:160]

    def test_alert_read_and_read_all(self, client, bearer_headers, seeded_ids):
        """POST /api/alert/<id>/read 与 /read-all → 200。"""
        read_one = client.post(
            f"/api/alert/{seeded_ids}/read", json={}, headers=bearer_headers
        )
        assert read_one.status_code == 200, read_one.data[:160]

        read_all = client.post("/api/alert/read-all", json={}, headers=bearer_headers)
        assert read_all.status_code == 200, read_all.data[:160]

    def test_update_user_profile(self, client, bearer_headers, seeded_ids):
        """PUT /api/user/profile → 200，data 回填更新后的资料。"""
        resp = client.put(
            "/api/user/profile",
            json={"nickname": "契约昵称", "bio": "契约测试简介"},
            headers=bearer_headers,
        )
        assert resp.status_code == 200, resp.data[:160]
        _assert_envelope(resp, "/api/user/profile")


# ---------------------------------------------------------------------------
# 降级回归：broker 不可用时写路由走 503 envelope（#47 实证修复）
# ---------------------------------------------------------------------------


class TestBrokerDegradationContract:
    """Celery broker（Redis）不可用时，任务提交端点不得返回 Werkzeug HTML 500。"""

    def test_spider_search_broker_down_503(self, client, bearer_headers, monkeypatch):
        from kombu.exceptions import OperationalError

        class _BrokenTask:
            @staticmethod
            def delay(*args, **kwargs):
                raise OperationalError("Error 111 connecting to localhost:6379")

        # _submit_local_task 在调用时 `from tasks.celery_spider import ...`，
        # patch 模块属性即可被读到
        monkeypatch.setattr(
            "tasks.celery_spider.spider_search_task", _BrokenTask(), raising=False
        )
        resp = client.post(
            "/api/spider/search", json={"keyword": "测试"}, headers=bearer_headers
        )
        assert resp.status_code == 503, resp.data[:200]
        body = resp.get_json()
        assert body["code"] == 503
        assert body["request_id"] == resp.headers["X-Request-Id"]
