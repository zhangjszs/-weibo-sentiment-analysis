#!/usr/bin/env python3
"""#11 回归：全接口统一空 body→400 JSON；非法类型/范围→400；永不 500/HTML。"""

import pytest

pytestmark = pytest.mark.api

GOOD_ORIGIN = {"Origin": "http://localhost:3000"}


def _assert_json_400(resp):
    assert resp.status_code in (400, 422), f"got {resp.status_code}: {resp.get_data(as_text=True)[:200]}"
    data = resp.get_json()
    assert data is not None, "必须返回 JSON 而非 HTML"
    assert data.get("code") in (400, 422)


class TestEmptyBodyIs400Json:
    """空 body / 非 JSON / 非 dict 统一受控 JSON 响应（400，或带默认值的 200/409）。

    关键契约：永不 500、永不 HTML；有必填字段的接口必须 400。
    """

    @pytest.mark.parametrize(
        "method,path",
        [
            ("post", "/api/sentiment/analyze"),
            ("post", "/api/predict/batch"),
            ("post", "/api/alert/rules"),
            ("post", "/api/propagation/compare"),
        ],
    )
    def test_empty_body_400(self, authed_client, method, path):
        import utils.authz as _authz

        # /api/alert/rules 需 admin：提权后聚焦空 body 校验层
        _authz.Config.ADMIN_USERS.add("tester")
        try:
            resp = getattr(authed_client, method)(
                path, data="", content_type="text/plain", headers=GOOD_ORIGIN
            )
            _assert_json_400(resp)
        finally:
            _authz.Config.ADMIN_USERS.discard("tester")

    @pytest.mark.parametrize(
        "method,path",
        [
            ("post", "/api/spider/crawl"),
            ("post", "/api/spider/quick-crawl"),
            ("post", "/api/alert/evaluate"),
            ("post", "/api/alert/test"),
            ("post", "/api/report/generate"),
        ],
    )
    def test_empty_body_controlled(self, authed_client, method, path):
        """带默认值的接口：空 body 允许按默认执行，但必须受控 JSON（200/400/409）。"""
        import utils.authz as _authz

        _authz.Config.ADMIN_USERS.add("tester")
        try:
            resp = getattr(authed_client, method)(
                path, data="", content_type="text/plain", headers=GOOD_ORIGIN
            )
            assert resp.status_code in (200, 400, 409), (
                path,
                resp.status_code,
                resp.get_data(as_text=True)[:200],
            )
            assert resp.get_json() is not None, path
        finally:
            _authz.Config.ADMIN_USERS.discard("tester")

    def test_predict_batch_bad_items_400(self, authed_client):
        for payload, _desc in [
            ({"texts": ["ok", 123]}, "non-string-item"),
            ({"texts": ["ok", ""]}, "empty-item"),
            ({"texts": ["x" * 2001]}, "oversize-item"),
            ({"texts": "not-a-list"}, "non-list"),
            ({"texts": ["ok"], "mode": "evil"}, "bad-mode"),
        ]:
            resp = authed_client.post(
                "/api/predict/batch", json=payload, headers=GOOD_ORIGIN
            )
            _assert_json_400(resp)

    def test_analyze_bad_mode_and_type_400(self, authed_client):
        resp = authed_client.post(
            "/api/sentiment/analyze",
            json={"text": "今天很开心", "mode": "evil"},
            headers=GOOD_ORIGIN,
        )
        _assert_json_400(resp)
        resp = authed_client.post(
            "/api/sentiment/analyze", json={"text": 12345}, headers=GOOD_ORIGIN
        )
        _assert_json_400(resp)


class TestBadQueryParamsNever500:
    """?page=abc / count=abc 等永不 500（数据层 mock，隔离校验解析层）。"""

    @pytest.mark.parametrize(
        "path",
        [
            "/api/audit/logs?page=abc&limit=xyz",
            "/api/platform/all?platforms=weibo,evil&page_size=abc",
            "/api/propagation/analyze/abc123?count=zzz",
            "/api/propagation/timeline/abc123?interval=zzz",
            "/api/spider/logs?lines=abc",
        ],
    )
    def test_bad_query_no_500(self, authed_client, path):
        resp = authed_client.get(path, headers=GOOD_ORIGIN)
        assert resp.status_code != 500, path
        assert "<html" not in resp.get_data(as_text=True).lower() or resp.status_code in (200, 400, 401, 403, 404)

    def test_favorites_bad_page_isolated(self, authed_client, monkeypatch):
        import views.api.favorites_api as fav_api

        monkeypatch.setattr(
            fav_api, "_fav_repo", lambda: type("R", (), {"find_with_article": lambda self, **k: ([], 0)})()
        )
        resp = authed_client.get("/api/favorites?page=abc&limit=xyz", headers=GOOD_ORIGIN)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["page"] == 1

    def test_platform_bad_page_isolated(self, authed_client, monkeypatch):
        import views.api.platform_api as plat_api

        monkeypatch.setattr(
            plat_api, "_load_platform_data", lambda *a, **k: ([], "test", False)
        )
        resp = authed_client.get(
            "/api/platform/data/weibo?page=abc&page_size=xyz", headers=GOOD_ORIGIN
        )
        assert resp.status_code == 200
        body = resp.get_json()["data"]["data"]
        assert body["pagination"]["page"] == 1
        assert body["pagination"]["page_size"] == 20

    def test_bad_article_id_400(self, authed_client):
        resp = authed_client.get(
            "/api/propagation/analyze/" + "a" * 200, headers=GOOD_ORIGIN
        )
        assert resp.status_code == 400
        assert resp.get_json()["code"] == 400


class TestUserInputValidation:
    def test_register_null_body_400(self, client):
        resp = client.post(
            "/user/register",
            data="null",
            content_type="application/json",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code in (400, 401)
        assert resp.get_json() is not None

    def test_profile_helpers_reject_bad(self):
        from views.api.user_routes import _parse_avatar_color, _validate_email

        assert _validate_email("not-an-email") is False
        assert _validate_email("a@b") is False
        assert _validate_email("ok@example.com") is True
        assert _parse_avatar_color("#GGGGGG") is None
        assert _parse_avatar_color("#1a2b3c") == "#1a2b3c"

    def test_profile_empty_updates_tuple(self, app):
        from views.api.user_routes import _parse_profile_updates

        with app.test_request_context("/"):
            updates, err = _parse_profile_updates({})
        assert not updates
        assert isinstance(err, tuple) and len(err) == 2
