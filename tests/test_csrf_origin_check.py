#!/usr/bin/env python3
"""
CSRF Origin 校验测试（P3 defense-in-depth）。

验证 _validate_origin_for_state_change 的行为：
- 同源 POST（Origin 在 ALLOWED_ORIGINS）→ 放行
- 跨源 POST（Origin 不在 ALLOWED_ORIGINS）→ 403
- 无 Origin 的 POST（curl 等非浏览器客户端）→ 放行
- GET 请求不校验 Origin
- Referer 回退校验
"""

import pytest

pytestmark = pytest.mark.unit

import sys

import pytest


@pytest.fixture
def csrf_app(monkeypatch):
    """隔离环境，避免触发完整 app 初始化的副作用。"""
    monkeypatch.setenv("AUTO_CREATE_DEMO_ADMIN", "False")
    monkeypatch.setenv("DEMO_ADMIN_RESET_PASSWORD", "False")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")

    # 清除已导入的模块缓存，确保用新环境变量
    for mod in list(sys.modules.keys()):
        if mod.startswith("app") or mod.startswith("config.settings"):
            del sys.modules[mod]

    from app import _validate_origin_for_state_change, create_app

    app = create_app()
    app.config["TESTING"] = True
    return app, _validate_origin_for_state_change


class TestOriginValidation:
    """_validate_origin_for_state_change 行为测试"""

    def test_get_requests_skip_check(self, csrf_app):
        """GET 请求不应触发 Origin 校验"""
        app, validate = csrf_app
        with app.test_request_context("/api/articles", method="GET"):
            assert validate() is None

    def test_same_origin_post_allowed(self, csrf_app):
        """同源 POST（Origin 在 ALLOWED_ORIGINS）应放行"""
        app, validate = csrf_app
        with app.test_request_context(
            "/api/spider/crawl",
            method="POST",
            json={"type": "hot"},
            headers={"Origin": "http://localhost:3000"},
        ):
            assert validate() is None

    def test_cross_origin_post_blocked(self, csrf_app):
        """跨源 POST（Origin 不在 ALLOWED_ORIGINS）应返回 403"""
        app, validate = csrf_app
        with app.test_request_context(
            "/api/spider/crawl",
            method="POST",
            json={"type": "hot"},
            headers={"Origin": "https://evil.com"},
        ):
            result = validate()
            assert result is not None
            response, status = result
            assert status == 403

    def test_no_origin_header_allows_non_browser(self, csrf_app):
        """无 Origin 头的 POST（curl/API SDK）应放行"""
        app, validate = csrf_app
        with app.test_request_context(
            "/api/spider/crawl",
            method="POST",
            json={"type": "hot"},
            # 不设 Origin 也不设 Referer
        ):
            assert validate() is None

    def test_referer_fallback_allowed(self, csrf_app):
        """Origin 缺失时，同源 Referer 应回退放行"""
        app, validate = csrf_app
        with app.test_request_context(
            "/api/auth/login",
            method="POST",
            json={"username": "x", "password": "y"},
            headers={"Referer": "http://localhost:3000/login"},
        ):
            assert validate() is None

    def test_referer_fallback_blocked(self, csrf_app):
        """Origin 缺失时，跨源 Referer 应回退拒绝"""
        app, validate = csrf_app
        with app.test_request_context(
            "/api/auth/login",
            method="POST",
            json={"username": "x", "password": "y"},
            headers={"Referer": "https://evil.com/fake-login"},
        ):
            result = validate()
            assert result is not None
            assert result[1] == 403

    def test_put_method_checked(self, csrf_app):
        """PUT 请求应触发 Origin 校验"""
        app, validate = csrf_app
        with app.test_request_context(
            "/api/user/profile",
            method="PUT",
            json={"nickname": "x"},
            headers={"Origin": "https://evil.com"},
        ):
            result = validate()
            assert result is not None
            assert result[1] == 403

    def test_delete_method_checked(self, csrf_app):
        """DELETE 请求应触发 Origin 校验"""
        app, validate = csrf_app
        with app.test_request_context(
            "/api/favorites/123",
            method="DELETE",
            headers={"Origin": "https://evil.com"},
        ):
            result = validate()
            assert result is not None
            assert result[1] == 403


class TestOriginCheckIntegration:
    """端到端集成：确认 before_request 真的拦截了跨源 POST"""

    def test_cross_origin_post_returns_403_via_before_request(self, csrf_app):
        """通过 test client 验证 before_request 链路完整拦截"""
        app, _ = csrf_app
        client = app.test_client()
        # 带 JWT cookie + 跨源 Origin → 应被 CSRF 校验拦截（403），不会到 401
        from utils.jwt_handler import create_token

        token = create_token(1, "tester")
        client.set_cookie("weibo_access_token", token)

        response = client.post(
            "/api/spider/crawl",
            json={"type": "hot"},
            headers={"Origin": "https://evil.com"},
        )
        assert response.status_code == 403

    def test_same_origin_post_passes_csrf_to_auth(self, csrf_app):
        """同源 POST 应通过 CSRF 校验，进入 JWT 鉴权层"""
        app, _ = csrf_app
        client = app.test_client()
        # 同源 Origin 但无认证 → 应通过 CSRF，被 JWT 拦截为 401（不是 403）
        response = client.post(
            "/api/spider/crawl",
            json={"type": "hot"},
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 401  # CSRF 通过，JWT 拦截

    def test_no_origin_post_passes_csrf_to_auth(self, csrf_app):
        """无 Origin 的 POST（非浏览器）应通过 CSRF，进入 JWT 鉴权"""
        app, _ = csrf_app
        client = app.test_client()
        response = client.post(
            "/api/spider/crawl",
            json={"type": "hot"},
            # 无 Origin、无 Referer、无 token
        )
        assert response.status_code == 401  # CSRF 通过，JWT 拦截

    def test_cookie_track_without_origin_is_rejected(self, csrf_app):
        """Cookie 副轨状态变更缺失 Origin/Referer → 403（浏览器必然带 Origin）"""
        app, _ = csrf_app
        client = app.test_client()
        from utils.jwt_handler import create_token

        token = create_token(1, "tester")
        client.set_cookie("weibo_access_token", token)
        response = client.post(
            "/api/spider/quick-crawl",
            json={"type": "hot"},
            # 无 Origin、无 Referer，但带认证 Cookie
        )
        assert response.status_code == 403
        assert response.get_json().get("code") == 403

    def test_bearer_track_without_origin_passes_csrf(self, csrf_app, monkeypatch):
        """Bearer 主轨无 Origin → 放行 CSRF（非 ambient 凭证，不受 CSRF 影响）"""
        import utils.authz as _authz
        import views.api.spider_api as spider_api

        # quick-crawl 仅 admin 可用：测试账号提权以便聚焦 Origin 校验层
        monkeypatch.setattr(_authz.Config, "ADMIN_USERS", {"tester"})

        monkeypatch.setattr(
            spider_api,
            "dispatch_spider_task",
            lambda *a, **k: {
                "task_id": "fake-bearer",
                "task_label": "fake",
                "crawl_type": "hot",
                "keyword": "",
                "page_num": 1,
                "article_limit": 50,
            },
        )
        monkeypatch.setattr(spider_api, "register_submitted_task", lambda r: None)
        app, _ = csrf_app
        client = app.test_client()
        from utils.jwt_handler import create_token

        token = create_token(1, "tester")
        response = client.post(
            "/api/spider/quick-crawl",
            json={"type": "hot"},
            headers={"Authorization": f"Bearer {token}"},
            # 无 Origin、无 Referer、无 Cookie
        )
        assert response.status_code not in (401, 403)
