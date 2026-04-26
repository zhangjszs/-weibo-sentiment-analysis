#!/usr/bin/env python3
"""
API 契约测试
验证关键接口的响应结构，防止后端字段变更导致前端白屏。
"""

import pytest


class TestHealthContract:
    """健康检查接口契约"""

    def test_health_structure(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data


class TestSessionCheckContract:
    """会话检查接口契约"""

    def test_session_check_structure(self, client):
        response = client.get("/api/session/check")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["code"] == 200
        assert "data" in payload
        assert "authenticated" in payload["data"]

    def test_session_check_authenticated(self, authed_client):
        response = authed_client.get("/api/session/check")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["data"]["authenticated"] is True
        assert "user" in payload["data"]


class TestSpiderOverviewContract:
    """爬虫概览接口契约（需管理员权限）"""

    def test_overview_structure(self, authed_client, monkeypatch):
        from utils import authz
        monkeypatch.setattr(authz.Config, "ADMIN_USERS", {"tester"})
        response = authed_client.get("/api/spider/overview")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["code"] == 200
        data = payload["data"]

        # 核心统计字段
        assert "articleCount" in data
        assert "commentCount" in data
        assert "userCount" in data
        assert "latestArticleTime" in data

        # 状态字段
        assert "isRunning" in data
        assert "progress" in data
        assert "message" in data

        # 趋势与历史
        assert "dailyTrend" in data
        assert "history" in data


class TestApiResponseContract:
    """通用 API 响应格式契约"""

    @pytest.mark.parametrize(
        "path,method",
        [
            ("/api/session/check", "GET"),
            ("/api/spider/status", "GET"),
        ],
    )
    def test_common_response_fields(self, authed_client, path, method):
        func = getattr(authed_client, method.lower())
        response = func(path)
        payload = response.get_json()
        assert "code" in payload
        assert "msg" in payload
        assert "timestamp" in payload
