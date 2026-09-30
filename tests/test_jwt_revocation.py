#!/usr/bin/env python3
"""
JWT 撤销/旋转与安全修复测试（#15）

- aud/iss 声明：签发必须带，验签必须校验
- jti 黑名单：revoke 后 verify 拒绝；logout/extend 接口真正作废 token
- admin_required：未认证 401、无权限 403
- 登录重定向：//evil.com 开放重定向被拦
- X-Request-Id：客户端头消毒后才入日志
"""

import pytest

pytestmark = pytest.mark.api


import jwt as pyjwt  # noqa: E402
import pytest  # noqa: E402

from config.settings import Config  # noqa: E402
from utils.jwt_handler import (  # noqa: E402
    JWT_AUDIENCE,
    JWT_ISSUER,
    create_token,
    revoke_token,
    verify_token,
)


def _decode_unverified(token):
    return pyjwt.decode(token, options={"verify_signature": False})


# ---------------------------------------------------------------------------
# aud/iss 与撤销（纯函数级）
# ---------------------------------------------------------------------------


def test_create_token_carries_iss_and_aud():
    token = create_token(1, "tester")
    payload = _decode_unverified(token)
    assert payload["iss"] == JWT_ISSUER
    assert payload["aud"] == JWT_AUDIENCE
    assert payload["jti"]


def test_verify_rejects_token_without_aud_iss():
    """旧格式 token（无 aud/iss）必须被拒——用户重登一次属预期。"""
    now = __import__("datetime").datetime.now(__import__("datetime").UTC)
    legacy = pyjwt.encode(
        {
            "user_id": 1,
            "username": "tester",
            "jti": "legacy-jti",
            "iat": now,
            "exp": now + __import__("datetime").timedelta(hours=1),
        },
        Config.JWT_SECRET_KEY,
        algorithm="HS256",
    )
    assert verify_token(legacy) is None


def test_revoke_token_makes_verify_fail():
    token = create_token(1, "tester")
    assert verify_token(token) is not None

    assert revoke_token(token) is True
    assert verify_token(token) is None


def test_revoke_rejects_garbage_token():
    assert revoke_token("not-a-token") is False
    assert revoke_token("") is False


def test_revoke_other_token_does_not_affect_target():
    t1 = create_token(1, "tester")
    t2 = create_token(1, "tester")
    revoke_token(t1)
    assert verify_token(t1) is None
    assert verify_token(t2) is not None


# ---------------------------------------------------------------------------
# logout / extend 接口级行为
# ---------------------------------------------------------------------------


def test_api_logout_revokes_cookie_token(client, auth_cookie_setter):
    token = create_token(7, "alice")
    client_obj = client
    auth_cookie_setter(client_obj, token)

    resp = client_obj.post("/api/auth/logout")
    assert resp.status_code == 200
    # token 已进黑名单，即使原样重放也无法再通过校验
    assert verify_token(token) is None


def test_session_extend_rotates_old_token(client, auth_cookie_setter, monkeypatch):
    # extend 是 Cookie 副轨的 POST：按 CSRF 设计必须带 ALLOWED_ORIGINS 内的
    # Origin（缺 Origin 的 Cookie 状态变更请求会被 403，这是正确的防线）。
    # 注意必须在 fixture 之后导入：app fixture 会删 config* 模块并重导入，
    # 模块顶层拿到的 Config 是旧类
    import config.settings as settings

    monkeypatch.setattr(settings.Config, "ALLOWED_ORIGINS", ["http://testserver"], raising=False)
    token = create_token(7, "alice")
    auth_cookie_setter(client, token)

    resp = client.post("/api/session/extend", headers={"Origin": "http://testserver"})
    assert resp.status_code == 200
    body = resp.get_json()
    new_token = body["data"]["token"]
    assert new_token
    # 旧 token 已被旋转作废，新 token 可用
    assert verify_token(token) is None
    assert verify_token(new_token) is not None


# ---------------------------------------------------------------------------
# admin_required 的 401/403 区分
# ---------------------------------------------------------------------------


def test_admin_required_returns_401_when_unauthenticated(app):
    from utils.authz import admin_required

    with app.test_request_context("/_test_admin"):
        view = admin_required(lambda: "ok")
        resp, code = view()
    assert code == 401


def test_admin_required_returns_403_for_non_admin(app):
    from flask import g, request

    from utils.authz import admin_required

    with app.test_request_context("/whatever"):
        request.current_user = {"username": "norm", "user_id": 2}
        g.current_user = {"username": "norm", "user_id": 2}
        view = admin_required(lambda: "ok")
        resp, code = view()
    assert code == 403


# ---------------------------------------------------------------------------
# 登录重定向白名单（纯函数级）
# ---------------------------------------------------------------------------


def test_safe_redirect_url_rejects_protocol_relative():
    from views.user.user import _safe_redirect_url

    assert _safe_redirect_url("//evil.com") == "/home"
    assert _safe_redirect_url("https://evil.com") == "/home"
    assert _safe_redirect_url("/\\evil.com") == "/home"
    assert _safe_redirect_url("") == "/home"
    assert _safe_redirect_url("/analysis/sentiment") == "/analysis/sentiment"


# ---------------------------------------------------------------------------
# X-Request-Id 消毒
# ---------------------------------------------------------------------------


def test_request_id_sanitized_from_client_header(app):
    # after_request 会把 g.request_id 回显到响应头：超长/非法样例必须被换掉，
    # 合法样例原样回显。换行注入在 HTTP 解析层就被 Werkzeug 拒绝
    # （Header values must not contain newline），这里覆盖能穿过解析层的
    # 恶意输入：超长 ID（伪造超长日志字段）
    with app.test_client() as c:
        overlong = "r" * 200
        resp = c.get("/health", headers={"X-Request-Id": overlong})
        echoed = resp.headers.get("X-Request-Id") or ""
        assert echoed != overlong
        assert len(echoed) <= 64

        resp2 = c.get("/health", headers={"X-Request-Id": "abc-DEF_123"})
        assert resp2.headers.get("X-Request-Id") == "abc-DEF_123"
