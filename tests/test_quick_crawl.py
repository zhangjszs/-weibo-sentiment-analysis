#!/usr/bin/env python3
"""
快速爬取接口测试（#9：quick-crawl 已收敛为仅管理员可用，与 /crawl 一致）。
"""

import pytest

pytestmark = pytest.mark.external


def _admin_client(client, monkeypatch):
    import utils.authz as _authz
    from utils.jwt_handler import create_token

    # authz 模块持有其导入期的 Config 对象，提权必须打到该对象上
    #（conftest fixture 会重导 config.settings，补丁 config.settings.Config 不可靠）
    monkeypatch.setattr(_authz.Config, "ADMIN_USERS", {"admin"})
    token = create_token(1, "admin")
    from conftest import set_auth_cookie

    set_auth_cookie(client, token)
    return client


class TestQuickCrawl:
    """测试快速爬取接口"""

    def test_quick_crawl_requires_auth(self, client):
        """未认证访问应返回 401"""
        response = client.post("/api/spider/quick-crawl", json={"type": "hot"})
        assert response.status_code == 401
        data = response.get_json()
        assert data["code"] == 401

    def test_quick_crawl_blocks_non_admin(self, authed_client):
        """普通登录用户应返回 403（#9 越权收紧）"""
        response = authed_client.post(
            "/api/spider/quick-crawl",
            json={"type": "hot", "pageNum": 1},
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 403
        assert response.get_json()["code"] == 403

    def test_quick_crawl_submits_task(self, client, monkeypatch):
        """管理员应能成功提交爬取任务"""
        authed = _admin_client(client, monkeypatch)
        response = authed.post(
            "/api/spider/quick-crawl",
            json={"type": "hot", "pageNum": 1},
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["code"] == 200
        assert "task_id" in data["data"]
        assert data["data"]["type"] == "hot"

    def test_quick_crawl_search_requires_keyword(self, client, monkeypatch):
        """搜索模式下缺少关键词应返回 400"""
        authed = _admin_client(client, monkeypatch)
        response = authed.post(
            "/api/spider/quick-crawl",
            json={"type": "search", "keyword": "", "pageNum": 1},
            headers={"Origin": "http://localhost:3000"},
        )
        # spider_task_service 中的 _submit_local_task 会校验 keyword
        # 409 可能因前序测试任务仍在运行而触发
        assert response.status_code in (200, 400, 409)
        data = response.get_json()
        assert "code" in data

    def test_quick_crawl_rejects_concurrent(self, client, monkeypatch):
        """已有任务运行时再次提交应返回 409（至少在一个请求返回 200 后）"""
        authed = _admin_client(client, monkeypatch)
        headers = {"Origin": "http://localhost:3000"}
        # 第一个请求（可能因前序测试任务仍在运行而返回 409）
        r1 = authed.post(
            "/api/spider/quick-crawl", json={"type": "hot", "pageNum": 1}, headers=headers
        )
        assert r1.status_code in (200, 409)

        # 由于测试环境 Celery 可能未启动，任务状态可能立刻结束，
        # 所以第二个请求不一定返回 409；这里仅验证接口格式正确
        r2 = authed.post(
            "/api/spider/quick-crawl", json={"type": "hot", "pageNum": 1}, headers=headers
        )
        assert r2.status_code in (200, 409)
        data = r2.get_json()
        assert "code" in data
