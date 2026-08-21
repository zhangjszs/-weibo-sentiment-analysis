#!/usr/bin/env python3
"""
A2 认证单轨化回归测试（JWT 单轨，/page/* 收敛）

验收：
- GET /page/* 未认证 -> 401（非 302 重定向），前端接管
- GET /user/login, /user/register 未认证 -> 200 直出
- POST /api/* 未认证 -> 401 regardless of Origin
- src/app.py 无 startswith("/page") 分支
- SameSite+Origin 双层保留但收敛（已在 test_csrf_origin_check 覆盖，此处补充单轨行为）
"""

import pathlib

import pytest

pytestmark = pytest.mark.api


class TestPageJwtSingleTrack:
    """验证 /page/* 已从 session 重定向收敛为 JWT 401"""

    def test_page_home_without_jwt_returns_401_not_302(self, client):
        resp = client.get("/page/home")
        assert resp.status_code == 401, f"expected 401, got {resp.status_code} Location={resp.headers.get('Location')}"
        # 必须不是 302 重定向
        assert resp.status_code != 302
        assert resp.headers.get("Location") is None
        data = resp.get_json()
        assert data is not None
        assert data.get("code") == 401

    def test_page_dashboard_without_jwt_returns_401(self, client):
        # 通用 /page/* 路径，即使路由不存在也应被 before_request 拦截为 401
        resp = client.get("/page/dashboard")
        assert resp.status_code == 401
        assert resp.headers.get("Location") is None

    def test_page_tableData_without_jwt_returns_401(self, client):
        resp = client.get("/page/tableData")
        assert resp.status_code == 401

    def test_page_with_session_cookie_still_401(self, client):
        # session 登录不再被 before_request 认可，必须用 JWT
        with client.session_transaction() as sess:
            sess["username"] = "tester"
            sess["user_id"] = 1
        resp = client.get("/page/home")
        assert resp.status_code == 401, "session should no longer grant /page/* access"

    def test_page_with_jwt_returns_not_401(self, authed_client, monkeypatch):
        # 带 JWT 应通过鉴权，不应返回 401（具体页面可能因模板/DB 返回 200 或 500，但不应是 401/302）
        # Mock 数据以尽量让 /page/home 返回 200
        import views.page.page as page_module

        monkeypatch.setattr(page_module.getHomeData, "getHomeTopLikeCommentsData", lambda: [])
        monkeypatch.setattr(page_module.getHomeData, "getTagData", lambda: (0, "", ""))
        monkeypatch.setattr(page_module.getHomeData, "getCreatedNumEchartsData", lambda: ([], []))
        monkeypatch.setattr(page_module.getHomeData, "getTypeCharData", lambda: [])
        monkeypatch.setattr(page_module.getHomeData, "getCommentsUserCratedNumEchartsData", lambda: [])

        resp = authed_client.get("/page/home")
        assert resp.status_code != 401, f"authed /page/home should not be 401, got {resp.status_code}"
        assert resp.status_code != 302


class TestPublicPassthrough:
    """白名单直通"""

    def test_user_login_without_jwt_is_public(self, client):
        resp = client.get("/user/login")
        assert resp.status_code == 200

    def test_user_register_without_jwt_is_public(self, client):
        resp = client.get("/user/register")
        assert resp.status_code == 200

    def test_root_and_health_are_public(self, client):
        assert client.get("/").status_code in (200, 301, 302)
        assert client.get("/health").status_code == 200
        # /ready 亦应直通（探针）
        assert client.get("/ready").status_code in (200, 503)

    def test_api_auth_login_is_public(self, client):
        resp = client.post("/api/auth/login", json={"username": "x", "password": "y"})
        # 未认证但应通过 before_request（不返回 401 因缺少 token，而是由业务逻辑返回 400/401）
        # 关键是不能被 before_request 的 JWT 拦截为"缺少认证令牌"的 401，且不应被 Origin 拦截
        # 这里验证：带 evil Origin 仍应直达业务层（不被 403 拦截），且返回非 403
        resp_evil = client.post(
            "/api/auth/login",
            json={"username": "x", "password": "y"},
            headers={"Origin": "https://evil.com"},
        )
        assert resp_evil.status_code != 403
        assert resp.status_code != 403


class TestApiJwtRequiredRegardlessOfOrigin:
    """POST /api/* 未认证 -> 401 regardless of Origin（JWT 单轨）"""

    def test_post_api_without_jwt_without_origin_is_401(self, client):
        resp = client.post("/api/spider/crawl", json={"type": "hot"})
        assert resp.status_code == 401

    def test_post_api_without_jwt_with_evil_origin_is_still_401(self, client):
        resp = client.post(
            "/api/spider/crawl",
            json={"type": "hot"},
            headers={"Origin": "https://evil.com"},
        )
        assert resp.status_code == 401, f"without JWT should be 401 even with evil origin, got {resp.status_code}"

    def test_post_api_without_jwt_with_good_origin_is_still_401(self, client):
        resp = client.post(
            "/api/spider/crawl",
            json={"type": "hot"},
            headers={"Origin": "http://localhost:3000"},
        )
        assert resp.status_code == 401

    def test_post_api_with_jwt_and_evil_origin_is_403(self, client, monkeypatch):
        from utils.jwt_handler import create_token

        from tests.conftest import set_auth_cookie

        # 避免真实提交爬虫任务污染全局 _spider_state（会导致后续测试 409）
        import views.api.spider_api as spider_api

        monkeypatch.setattr(
            spider_api,
            "dispatch_spider_task",
            lambda *a, **k: {
                "task_id": "fake-1",
                "task_label": "fake",
                "crawl_type": "hot",
                "keyword": "",
                "page_num": 1,
                "article_limit": 50,
            },
        )
        monkeypatch.setattr(spider_api, "register_submitted_task", lambda r: None)

        token = create_token(1, "tester")
        set_auth_cookie(client, token)
        # /api/spider/quick-crawl 需要 JWT 但不需要 admin，适合测试 Origin 校验
        resp = client.post(
            "/api/spider/quick-crawl",
            json={"type": "hot"},
            headers={"Origin": "https://evil.com"},
        )
        assert resp.status_code == 403

    def test_post_api_with_jwt_and_good_origin_passes_csrf(self, client, monkeypatch):
        from utils.jwt_handler import create_token

        from tests.conftest import set_auth_cookie

        import views.api.spider_api as spider_api

        monkeypatch.setattr(
            spider_api,
            "dispatch_spider_task",
            lambda *a, **k: {
                "task_id": "fake-2",
                "task_label": "fake",
                "crawl_type": "hot",
                "keyword": "",
                "page_num": 1,
                "article_limit": 50,
            },
        )
        monkeypatch.setattr(spider_api, "register_submitted_task", lambda r: None)

        token = create_token(1, "tester")
        set_auth_cookie(client, token)
        resp = client.post(
            "/api/spider/quick-crawl",
            json={"type": "hot"},
            headers={"Origin": "http://localhost:3000"},
        )
        # 已通过 JWT 和 Origin，不应是 401/403（可能是 200 或业务错误，但不能是鉴权/跨站错误）
        assert resp.status_code not in (401, 403)


class TestNoPageBranchRemains:
    """源码层面：无 startswith("/page") 分支"""

    def test_app_py_has_no_page_startswith(self):
        content = pathlib.Path("src/app.py").read_text(encoding="utf-8")
        assert 'startswith("/page")' not in content, "src/app.py still contains startswith(\"/page\") branch"
        assert "startswith('/page')" not in content, "src/app.py still contains startswith('/page') branch"
        # 兼容部分实现可能使用单引号或双引号变体，统一检查
        assert '"/page' not in content or 'startswith' not in content.split('"/page')[0][-200:]  # fallback
        # 更严格：直接搜索子串
        assert "startswith(\"/page" not in content
        assert "startswith('/page" not in content
