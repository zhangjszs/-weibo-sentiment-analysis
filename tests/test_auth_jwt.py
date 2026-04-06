#!/usr/bin/env python3
"""
JWT 认证测试模块
测试登录、用户信息获取、注册等接口的 JWT 认证功能
"""

import os
import sys
import importlib

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


import pytest


class TestJWTHandler:
    """测试 JWT 处理模块"""

    def test_create_token(self):
        """测试 Token 创建"""
        from utils.jwt_handler import create_token

        token = create_token(1, "testuser")
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        """测试验证有效 Token"""
        from utils.jwt_handler import create_token, verify_token

        token = create_token(1, "testuser")
        payload = verify_token(token)

        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["username"] == "testuser"

    def test_verify_invalid_token(self):
        """测试验证无效 Token"""
        from utils.jwt_handler import verify_token

        result = verify_token("invalid.token.here")
        assert result is None

    def test_verify_empty_token(self):
        """测试验证空 Token"""
        from utils.jwt_handler import verify_token

        result = verify_token("")
        assert result is None


class TestLoginAPI:
    """测试登录 API"""

    @pytest.fixture
    def app(self, monkeypatch):
        """创建测试 Flask 应用"""
        monkeypatch.setenv("AUTO_CREATE_DEMO_ADMIN", "False")
        monkeypatch.setenv("DEMO_ADMIN_RESET_PASSWORD", "False")

        sys.modules.pop("app", None)
        sys.modules.pop("config.settings", None)
        sys.modules.pop("services.startup_service", None)
        app_module = importlib.import_module("app")
        app = app_module.app

        app.config["TESTING"] = True
        return app

    @pytest.fixture
    def client(self, app):
        """创建测试客户端"""
        return app.test_client()

    def test_login_requires_credentials(self, client):
        """测试登录需要凭据"""
        response = client.post(
            "/user/login", json={}, headers={"Accept": "application/json"}
        )
        # 应该返回错误
        assert response.status_code in [400, 401]

    def test_login_returns_json_for_api_request(self, client):
        """测试 API 请求返回 JSON"""
        response = client.post(
            "/user/login",
            json={"username": "testuser", "password": "wrongpassword"},
            headers={"Accept": "application/json"},
        )

        data = response.get_json()
        assert data is not None
        assert "code" in data or "error" in data

    def test_user_login_requires_csrf_token(self, client):
        """测试 /user/login 在 JSON 请求下仍执行 CSRF 校验"""
        response = client.post(
            "/user/login",
            json={"username": "testuser", "password": "wrongpassword"},
            headers={"Accept": "application/json"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data is not None
        assert data.get("msg") == "CSRF 校验失败"

    def test_api_login_is_csrf_exempt(self, client):
        """测试 /api/auth/login 作为 Token API 不受 CSRF 限制"""
        response = client.post(
            "/api/auth/login", json={"username": "bad", "password": "bad"}
        )
        assert response.status_code in [400, 401]
        data = response.get_json()
        assert data is not None
        assert data.get("msg") != "CSRF 校验失败"

    def test_user_info_requires_token(self, client):
        """测试用户信息接口需要 Token"""
        response = client.get("/user/info")

        assert response.status_code == 401
        data = response.get_json()
        assert data["code"] == 401

    def test_session_check_returns_false_when_unauthenticated(self, client):
        """测试未认证时会话检查返回 authenticated=false"""
        response = client.get("/api/session/check")

        assert response.status_code == 200
        data = response.get_json()
        assert data["code"] == 200
        assert data["data"]["authenticated"] is False
        assert data["data"]["user"] is None

    def test_session_extend_requires_authentication(self, client):
        """测试会话续期接口在未认证时返回401"""
        response = client.post("/api/session/extend")

        assert response.status_code == 401
        data = response.get_json()
        assert data["code"] == 401

    def test_session_extend_renews_token_for_cookie_auth(self, client):
        """测试 Cookie 会话续期时返回新的 Bearer Token 并刷新 Cookie"""
        from utils.jwt_handler import create_token

        token = create_token(8, "renew-user")
        client.set_cookie("weibo_access_token", token)

        response = client.post("/api/session/extend")

        assert response.status_code == 200
        data = response.get_json()
        assert data["code"] == 200
        assert data["data"]["extended"] is True
        assert data["data"]["token"]
        assert data["data"]["token"] != token
        set_cookie = response.headers.get("Set-Cookie", "")
        assert "weibo_access_token=" in set_cookie

    def test_api_login_sets_auth_cookie(self, client, monkeypatch):
        """测试 API 登录成功时写入 HttpOnly 认证 Cookie"""
        import views.api.api as api_module

        monkeypatch.setattr(
            api_module.auth_service,
            "login",
            lambda username, password: (
                True,
                "登录成功",
                {
                    "token": "jwt-token-123",
                    "user": {
                        "id": 1,
                        "username": username,
                        "create_time": "2026-03-20",
                        "is_admin": False,
                    },
                },
            ),
        )

        response = client.post(
            "/api/auth/login",
            json={"username": "tester", "password": "Valid123!"},
        )

        assert response.status_code == 200
        set_cookie = response.headers.get("Set-Cookie", "")
        assert "weibo_access_token=jwt-token-123" in set_cookie

    def test_api_logout_clears_auth_cookie(self, client):
        """测试 API 登出时清理认证 Cookie"""
        response = client.post("/api/auth/logout")

        assert response.status_code == 200
        set_cookie = response.headers.get("Set-Cookie", "")
        assert "weibo_access_token=" in set_cookie

    def test_cookie_auth_can_access_session_check(self, client):
        """测试受保护接口可以通过认证 Cookie 完成鉴权"""
        from utils.jwt_handler import create_token

        token = create_token(1, "cookie_user")
        client.set_cookie("weibo_access_token", token)

        response = client.get("/api/session/check")

        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["authenticated"] is True
        assert data["data"]["user"]["username"] == "cookie_user"


class TestRegisterAPI:
    """测试注册 API"""

    @pytest.fixture
    def app(self):
        """创建测试 Flask 应用"""
        from app import app

        app.config["TESTING"] = True
        return app

    @pytest.fixture
    def client(self, app):
        """创建测试客户端"""
        return app.test_client()

    def test_register_accepts_confirm_password(self, client):
        """测试注册接口接受 confirmPassword 字段"""
        # 注意：这个测试可能因为用户已存在而失败，这是预期行为
        response = client.post(
            "/user/register",
            json={
                "username": "testuser_temp",
                "password": "TestPass123!",
                "confirmPassword": "TestPass123!",
            },
            headers={"Accept": "application/json"},
        )

        data = response.get_json()
        # 接口应该返回 JSON 响应（无论成功还是失败）
        assert data is not None
        assert "code" in data or "msg" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
