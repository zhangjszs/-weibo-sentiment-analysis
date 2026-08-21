#!/usr/bin/env python3
"""
A1 API 前缀收敛测试：/getAllData → /api 别名过渡
验收：
- 新前缀 /api/* 可用（需 JWT）
- 旧前缀 /getAllData/* 307 重定向到 /api/*（保留查询串，307 保持方法）
- 鉴权行为一致：新旧路径均需 JWT（旧路径重定向本身不鉴权，重定向目标鉴权）
- grep -r "Blueprint.*getAllData" src 仅剩别名一处（手动检查）
"""

import pytest

pytestmark = pytest.mark.api


EXPECTED_ROUTES = [
    ("getHomeData", "GET", "/getHomeData"),
    ("getTableData", "GET", "/getTableData"),
    ("getArticleData", "GET", "/getArticleData"),
    ("getCommentData", "GET", "/getCommentData"),
    ("getIPData", "GET", "/getIPData"),
    ("getYuqingData", "GET", "/getYuqingData"),
    ("getContentCloudData", "GET", "/getContentCloudData"),
    ("clearCache", "POST", "/clearCache"),
]


def test_data_blueprint_prefix_is_api():
    """src/views/data/data_api.py 的主蓝图 url_prefix 必须为 /api"""
    from views.data.data_api import db

    assert db.url_prefix == "/api", f"expected /api but got {db.url_prefix}"
    # 确保该蓝图没有残留 getAllData
    assert "getAllData" not in db.url_prefix


def test_only_alias_blueprint_contains_getAllData(app):
    """grep -r \"Blueprint.*getAllData\" src 仅剩别名一处"""
    # 通过检查已注册蓝图的 url_prefix 统计
    prefixes = [bp.url_prefix for bp in app.blueprints.values() if bp.url_prefix]
    count = sum(1 for p in prefixes if "getAllData" in p)
    # 允许 1 个别名蓝图，其余不应包含 getAllData
    assert count == 1, f"expected exactly 1 alias blueprint with getAllData, got {prefixes}"


class TestApiPrefixAlias:
    """新旧前缀行为"""

    def test_new_prefix_requires_auth(self, client):
        """未认证访问 /api/* 应 401"""
        resp = client.get("/api/getHomeData")
        assert resp.status_code == 401

    def test_new_prefix_returns_200_with_auth(self, authed_client, monkeypatch):
        """认证后访问 /api/getHomeData 应 200（mock 数据避免 DB）"""
        import views.data.data_api as data_api

        # mock 缓存
        monkeypatch.setattr(data_api, "get_cached_data", lambda k, t: None)
        monkeypatch.setattr(data_api, "set_cached_data", lambda k, d, t: None)
        monkeypatch.setattr(data_api.getHomeData, "getHomeTopLikeCommentsData", lambda: [])
        monkeypatch.setattr(data_api.getHomeData, "getTagData", lambda: (0, "", ""))
        monkeypatch.setattr(data_api.getHomeData, "getCreatedNumEchartsData", lambda: ([], []))
        monkeypatch.setattr(data_api.getHomeData, "getTypeCharData", lambda: [])
        monkeypatch.setattr(data_api.getHomeData, "getCommentsUserCratedNumEchartsData", lambda: [])

        resp = authed_client.get("/api/getHomeData")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload["code"] == 200
        assert "data" in payload

    def test_legacy_path_returns_307_without_auth(self, client):
        """未认证访问旧前缀应 307 重定向到新前缀（不直接 401）"""
        resp = client.get("/getAllData/getHomeData", follow_redirects=False)
        assert resp.status_code == 307
        loc = resp.headers.get("Location", "")
        assert "/api/getHomeData" in loc

    def test_legacy_path_returns_307_with_auth(self, authed_client):
        """认证访问旧前缀也应 307"""
        resp = authed_client.get("/getAllData/getHomeData", follow_redirects=False)
        assert resp.status_code == 307
        loc = resp.headers.get("Location", "")
        assert "/api/getHomeData" in loc

    def test_legacy_preserves_query_string(self, authed_client):
        """重定向应保留 query string"""
        resp = authed_client.get(
            "/getAllData/getTableData?hotWord=%E6%B5%8B%E8%AF%95&foo=bar",
            follow_redirects=False,
        )
        assert resp.status_code == 307
        loc = resp.headers.get("Location", "")
        assert "/api/getTableData" in loc
        assert "hotWord" in loc
        assert "foo=bar" in loc

    def test_legacy_post_clearCache_redirect(self, authed_client):
        """POST /getAllData/clearCache 应 307 到 /api/clearCache"""
        resp = authed_client.post("/getAllData/clearCache", follow_redirects=False)
        assert resp.status_code == 307
        loc = resp.headers.get("Location", "")
        assert "/api/clearCache" in loc

    def test_all_routes_have_alias(self, authed_client):
        """7+1 条路由均应有别名"""
        for _name, method, suffix in EXPECTED_ROUTES:
            if method == "GET":
                resp = authed_client.get(f"/getAllData{suffix}", follow_redirects=False)
            else:
                resp = authed_client.post(f"/getAllData{suffix}", follow_redirects=False)
            assert resp.status_code == 307, f"legacy {suffix} should 307"
            loc = resp.headers.get("Location", "")
            assert f"/api{suffix}" in loc, f"{suffix} redirect target mismatch: {loc}"

    def test_new_all_routes_exist(self, authed_client, monkeypatch):
        """所有新前缀路由存在且认证后不 404"""
        import views.data.data_api as data_api

        # 通用 mock：让所有处理函数尽量返回 200
        monkeypatch.setattr(data_api, "get_cached_data", lambda k, t: None)
        monkeypatch.setattr(data_api, "set_cached_data", lambda k, d, t: None)
        # home
        monkeypatch.setattr(data_api.getHomeData, "getHomeTopLikeCommentsData", lambda: [])
        monkeypatch.setattr(data_api.getHomeData, "getTagData", lambda: (0, "", ""))
        monkeypatch.setattr(data_api.getHomeData, "getCreatedNumEchartsData", lambda: ([], []))
        monkeypatch.setattr(data_api.getHomeData, "getTypeCharData", lambda: [])
        monkeypatch.setattr(data_api.getHomeData, "getCommentsUserCratedNumEchartsData", lambda: [])
        # table
        monkeypatch.setattr(data_api.getTableData, "getTableDataPageData", lambda: [["a", 1]])
        monkeypatch.setattr(data_api.getTableData, "getTableData", lambda w: [])
        monkeypatch.setattr(data_api.getTableData, "getTableDataEchartsData", lambda w: ([], []))
        monkeypatch.setattr(data_api, "_build_table_search_result", lambda w: ([], [], [], 0, ""))
        # article
        monkeypatch.setattr(data_api.getEchartsData, "getTypeList", lambda: [])
        monkeypatch.setattr(data_api.getEchartsData, "getArticleCharOneData", lambda t: [[], []])
        monkeypatch.setattr(data_api.getEchartsData, "getArticleCharTwoData", lambda t: [[], []])
        monkeypatch.setattr(data_api.getEchartsData, "getArticleCharThreeData", lambda t: [[], []])
        monkeypatch.setattr(data_api.getTableData, "getTableDataArticle", lambda _: [])
        monkeypatch.setattr(data_api, "_build_article_type_data", lambda: [])
        # comment
        monkeypatch.setattr(data_api.getEchartsData, "getCommetCharDataOne", lambda: ([], []))
        monkeypatch.setattr(data_api.getEchartsData, "getCommetCharDataTwo", lambda: [])
        monkeypatch.setattr(data_api, "_get_comment_hour_distribution", lambda: {"hours": [], "counts": []})
        monkeypatch.setattr(data_api, "_get_comment_user_activity", lambda limit=10: {"users": [], "counts": []})
        monkeypatch.setattr(data_api, "_get_hot_comments", lambda limit=5: [])
        monkeypatch.setattr(data_api, "_compute_comment_sentiment", lambda d: {"正面": 0, "中性": 0, "负面": 0})
        # ip
        monkeypatch.setattr(data_api.getEchartsData, "getGeoCharDataOne", lambda: [])
        monkeypatch.setattr(data_api.getEchartsData, "getGeoCharDataTwo", lambda: [])
        monkeypatch.setattr(data_api, "_build_ip_map_data", lambda d: ([], []))
        monkeypatch.setattr(data_api, "_build_ip_list", lambda: [])
        # yuqing
        monkeypatch.setattr(data_api.getEchartsData, "getYuQingCharDataOne", lambda: [])
        monkeypatch.setattr(data_api.getEchartsData, "getYuQingCharDataTwo", lambda: [[], []])
        monkeypatch.setattr(data_api.getEchartsData, "getYuQingCharDataThree", lambda: [[], []])
        monkeypatch.setattr(data_api, "_build_yuqing_summary", lambda d: {})
        monkeypatch.setattr(data_api, "_get_recent_comments", lambda limit=100: [])
        monkeypatch.setattr(data_api, "_build_yuqing_sentiment_and_trend", lambda c: ([], {}))
        monkeypatch.setattr(data_api, "_build_yuqing_trend", lambda c: {})
        monkeypatch.setattr(data_api, "_build_yuqing_keywords", lambda d, max_words=20: [])
        # cloud
        monkeypatch.setattr(data_api.getEchartsData, "getContentCloud", lambda: "")
        monkeypatch.setattr(data_api.getEchartsData, "getCommentContentCloud", lambda: "")
        monkeypatch.setattr(data_api.getHomeData, "getUserNameWordCloud", lambda: "")
        monkeypatch.setattr(data_api, "_build_word_stats", lambda: [])
        # clearCache admin
        monkeypatch.setattr(data_api, "is_admin_user", lambda u: True)

        for _name, method, suffix in EXPECTED_ROUTES:
            if method == "GET":
                resp = authed_client.get(f"/api{suffix}")
            else:
                resp = authed_client.post(f"/api{suffix}")
            assert resp.status_code == 200, f"new /api{suffix} should 200, got {resp.status_code} {resp.get_data(as_text=True)[:200]}"
            assert resp.headers.get("Location") is None

    def test_follow_redirect_gives_same_as_direct(self, authed_client, monkeypatch):
        """跟随 307 重定向后 payload 与直访新前缀一致"""
        import views.data.data_api as data_api

        monkeypatch.setattr(data_api, "get_cached_data", lambda k, t: None)
        monkeypatch.setattr(data_api, "set_cached_data", lambda k, d, t: None)
        monkeypatch.setattr(data_api.getHomeData, "getHomeTopLikeCommentsData", lambda: [["c1"]])
        monkeypatch.setattr(data_api.getHomeData, "getTagData", lambda: (5, "authorA", "BJ"))
        monkeypatch.setattr(data_api.getHomeData, "getCreatedNumEchartsData", lambda: (["2026"], [1]))
        monkeypatch.setattr(data_api.getHomeData, "getTypeCharData", lambda: [{"name": "a", "value": 1}])
        monkeypatch.setattr(data_api.getHomeData, "getCommentsUserCratedNumEchartsData", lambda: {"hours": [1], "counts": [2]})

        direct = authed_client.get("/api/getHomeData")
        assert direct.status_code == 200
        direct_json = direct.get_json()

        # legacy follow
        redirected = authed_client.get("/getAllData/getHomeData", follow_redirects=True)
        assert redirected.status_code == 200
        redirected_json = redirected.get_json()
        # timestamp / request_id differ per request, compare stable fields
        assert redirected_json["code"] == direct_json["code"]
        assert redirected_json["msg"] == direct_json["msg"]
        assert redirected_json["data"] == direct_json["data"]

    def test_legacy_307_preserves_method(self, authed_client):
        """307 应保持方法，POST 重定向后仍为 POST（验证 Location 即可，客户端需手动跟随）"""
        resp = authed_client.post("/getAllData/clearCache", follow_redirects=False)
        assert resp.status_code == 307
        # 确保新端点的 POST 也需要鉴权（未鉴权应 401）
        import app as app_module

        # 已有 authed_client 带 cookie，验证新端点 POST 需要 admin 权限但不 404
        # 若用无鉴权客户端访问新端点，应 401 而非 404，证明路由存在
        # 构造无鉴权客户端
        app = app_module.create_app()
        app.config["TESTING"] = True
        c2 = app.test_client()
        r2 = c2.post("/api/clearCache")
        assert r2.status_code == 401
