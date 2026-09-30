#!/usr/bin/env python3
"""
正式数据模式接口测试
"""


import pytest


@pytest.mark.external
def test_platform_data_does_not_silent_demo_fallback(authed_client, monkeypatch):
    import views.api.platform_api as platform_api

    monkeypatch.setattr(
        platform_api,
        "querys",
        lambda sql, params, query_type: [],
    )

    response = authed_client.get("/api/platform/data/weibo")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data"]["demo_mode"] is False
    assert payload["data"]["data_source"] == "article_table_empty"
    assert payload["data"]["data"] == []


@pytest.mark.api
def test_platform_stats_use_loaded_data(authed_client, monkeypatch):
    import views.api.platform_api as platform_api

    sample_rows = [
        {
            "like_count": 10,
            "comment_count": 2,
            "repost_count": 1,
            "view_count": 100,
            "sentiment": "positive",
            "keywords": ["人工智能", "科技"],
        },
        {
            "like_count": 30,
            "comment_count": 4,
            "repost_count": 3,
            "view_count": 300,
            "sentiment": "negative",
            "keywords": ["人工智能"],
        },
    ]

    monkeypatch.setattr(
        platform_api,
        "_load_platform_data",
        lambda platform, count, demo_mode: (sample_rows, "article_table", False),
    )

    response = authed_client.get("/api/platform/stats/weibo")

    assert response.status_code == 200
    payload = response.get_json()["data"]["weibo"]
    assert payload["total_content"] == 2
    assert payload["total_likes"] == 40
    assert payload["total_comments"] == 6
    assert payload["total_views"] == 400
    assert payload["sentiment_distribution"]["positive"] == 1
    assert payload["sentiment_distribution"]["negative"] == 1
    assert payload["top_keywords"][0]["name"] == "人工智能"
    assert payload["top_keywords"][0]["count"] == 2


@pytest.mark.api
def test_propagation_analyze_returns_404_without_real_data(authed_client, monkeypatch):
    import views.api.propagation_api as propagation_api

    monkeypatch.setattr(
        propagation_api,
        "_load_reposts",
        lambda article_id, count, demo_mode: ([], "reposts_empty", False),
    )

    response = authed_client.get("/api/propagation/analyze/article-1")

    assert response.status_code == 404
    payload = response.get_json()
    assert payload["code"] == 404


@pytest.mark.api
def test_get_article_data_uses_aggregated_type_query(authed_client, monkeypatch):
    import utils.getPublicData as public_data
    import views.data.data_api as data_api

    monkeypatch.setattr(data_api.getEchartsData, "getTypeList", lambda: ["news", "blog"])
    monkeypatch.setattr(
        data_api.getEchartsData, "getArticleCharOneData", lambda default_type: [[], []]
    )
    monkeypatch.setattr(
        data_api.getEchartsData, "getArticleCharTwoData", lambda default_type: [[], []]
    )
    monkeypatch.setattr(
        data_api.getEchartsData, "getArticleCharThreeData", lambda default_type: [[], []]
    )
    monkeypatch.setattr(data_api.getTableData, "getTableDataArticle", lambda _: [])
    monkeypatch.setattr(
        public_data,
        "getAllData",
        lambda: (_ for _ in ()).throw(AssertionError("should not full scan article table")),
    )
    monkeypatch.setattr(data_api, "get_cached_data", lambda cache_key, timeout: None)
    monkeypatch.setattr(
        data_api, "set_cached_data", lambda cache_key, data, timeout: None
    )
    monkeypatch.setattr(
        data_api,
        "_build_article_type_data",
        lambda: [{"name": "news", "value": 3}, {"name": "blog", "value": 1}],
    )

    response = authed_client.get("/api/getArticleData")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data"]["typeData"] == [
        {"name": "news", "value": 3},
        {"name": "blog", "value": 1},
    ]


@pytest.mark.api
def test_get_ip_data_does_not_invent_private_ips(authed_client, monkeypatch):
    import views.data.data_api as data_api

    monkeypatch.setattr(
        data_api.getEchartsData,
        "getGeoCharDataOne",
        lambda: [{"name": "北京", "value": 3}],
    )
    monkeypatch.setattr(data_api.getEchartsData, "getGeoCharDataTwo", lambda: [])
    monkeypatch.setattr(data_api, "get_cached_data", lambda cache_key, timeout: None)
    monkeypatch.setattr(
        data_api, "set_cached_data", lambda cache_key, data, timeout: None
    )
    monkeypatch.setattr(
        data_api,
        "_build_ip_list",
        lambda: [
            {
                "ip": "",
                "location": "北京",
                "count": 3,
                "lastTime": "2026-03-20 10:00:00",
                "user": "测试用户",
            }
        ],
    )

    response = authed_client.get("/api/getIPData")

    assert response.status_code == 200
    ip_list = response.get_json()["data"]["ipList"]
    assert ip_list[0]["ip"] == ""
    assert ip_list[0]["location"] == "北京"


@pytest.mark.api
def test_get_yuqing_data_uses_real_batch_sentiment_results(authed_client, monkeypatch):
    import services.sentiment_service as sentiment_service
    import views.data.data_api as data_api

    monkeypatch.setattr(data_api, "get_cached_data", lambda cache_key, timeout: None)
    monkeypatch.setattr(data_api, "set_cached_data", lambda cache_key, data, timeout: None)
    monkeypatch.setattr(data_api.getEchartsData, "getYuQingCharDataOne", lambda: [])
    monkeypatch.setattr(
        data_api.getEchartsData,
        "getYuQingCharDataTwo",
        lambda: [[{"name": "正面", "value": 1}, {"name": "中性", "value": 1}, {"name": "负面", "value": 1}], []],
    )
    monkeypatch.setattr(
        data_api.getEchartsData,
        "getYuQingCharDataThree",
        lambda: [[], []],
    )
    monkeypatch.setattr(
        data_api,
        "_get_recent_comments",
        lambda limit=100: [
            ("2026-03-20 10:00:00", "很好"),
            ("2026-03-20 11:00:00", "一般"),
            ("2026-03-19 09:00:00", "很差"),
        ],
    )
    monkeypatch.setattr(
        sentiment_service.SentimentService,
        "analyze_batch_cached",
        lambda texts, mode="simple": [
            {"label": "positive", "score": 0.9},
            {"label": "neutral", "score": 0.5},
            {"label": "negative", "score": 0.1},
        ][: len(texts)],
    )

    response = authed_client.get("/api/getYuqingData")

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["list"][0]["sentiment"] == "正面"
    assert payload["list"][0]["score"] == 0.9
    assert payload["list"][2]["sentiment"] == "负面"
    assert payload["trend"]["positive"] == [0, 1]
    assert payload["trend"]["neutral"] == [0, 1]
    assert payload["trend"]["negative"] == [1, 0]


@pytest.mark.api
def test_get_yuqing_data_does_not_full_scan_comments(authed_client, monkeypatch):
    import services.sentiment_service as sentiment_service
    import utils.getPublicData as public_data
    import views.data.data_api as data_api

    monkeypatch.setattr(data_api, "get_cached_data", lambda cache_key, timeout: None)
    monkeypatch.setattr(data_api, "set_cached_data", lambda cache_key, data, timeout: None)
    monkeypatch.setattr(
        public_data,
        "getAllCommentsData",
        lambda: (_ for _ in ()).throw(AssertionError("should not load all comments")),
    )
    monkeypatch.setattr(data_api.getEchartsData, "getYuQingCharDataOne", lambda: [])
    monkeypatch.setattr(
        data_api.getEchartsData,
        "getYuQingCharDataTwo",
        lambda: [[{"name": "正面", "value": 1}, {"name": "中性", "value": 1}, {"name": "负面", "value": 1}], []],
    )
    monkeypatch.setattr(data_api.getEchartsData, "getYuQingCharDataThree", lambda: [[], []])
    monkeypatch.setattr(
        data_api,
        "_get_recent_comments",
        lambda limit=100: [
            ("2026-03-20 10:00:00", "很好"),
            ("2026-03-20 11:00:00", "一般"),
            ("2026-03-19 09:00:00", "很差"),
        ],
    )
    monkeypatch.setattr(
        sentiment_service.SentimentService,
        "analyze_batch_cached",
        lambda texts, mode="simple": [
            {"label": "positive", "score": 0.9},
            {"label": "neutral", "score": 0.5},
            {"label": "negative", "score": 0.1},
        ],
    )

    response = authed_client.get("/api/getYuqingData")

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["list"][0]["sentiment"] == "正面"
    assert payload["list"][2]["sentiment"] == "负面"


@pytest.mark.api
def test_get_comment_data_uses_query_aggregations(authed_client, monkeypatch):
    import services.sentiment_service as sentiment_service
    import utils.getPublicData as public_data
    import views.data.data_api as data_api

    monkeypatch.setattr(data_api, "get_cached_data", lambda cache_key, timeout: None)
    monkeypatch.setattr(data_api, "set_cached_data", lambda cache_key, data, timeout: None)
    monkeypatch.setattr(
        public_data,
        "getAllCommentsData",
        lambda: (_ for _ in ()).throw(AssertionError("should not load all comments")),
    )
    monkeypatch.setattr(data_api.getEchartsData, "getCommetCharDataOne", lambda: (["20-40"], [3]))
    monkeypatch.setattr(
        data_api.getEchartsData,
        "getCommetCharDataTwo",
        lambda: [{"name": "女", "value": 2}],
    )

    def fake_hour_distribution():
        counts = [0] * 24
        counts[9] = 2
        counts[13] = 1
        return {"hours": [f"{h}:00" for h in range(24)], "counts": counts}

    monkeypatch.setattr(data_api, "_get_comment_hour_distribution", fake_hour_distribution)
    monkeypatch.setattr(
        data_api,
        "_get_comment_user_activity",
        lambda limit=10: {"users": ["用户A", "用户B"], "counts": [5, 3]},
    )
    monkeypatch.setattr(
        data_api, "_get_recent_comment_texts", lambda limit=200: ["很好", "一般", "较差"]
    )
    monkeypatch.setattr(
        data_api,
        "_get_hot_comments",
        lambda limit=5: [
            {
                "user": "用户A",
                "time": "2026-03-20 10:00:00",
                "content": "评论一",
                "likes": 12,
                "replies": 0,
            },
            {
                "user": "用户B",
                "time": "2026-03-20 08:00:00",
                "content": "评论二",
                "likes": 8,
                "replies": 0,
            },
        ],
    )
    monkeypatch.setattr(
        sentiment_service.SentimentService,
        "analyze_distribution_cached",
        lambda texts, mode="simple", sample_size=100: {"正面": 1, "中性": 1, "负面": 1},
    )

    response = authed_client.get("/api/getCommentData")

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["timeDistribution"]["counts"][9] == 2
    assert payload["timeDistribution"]["counts"][13] == 1
    assert payload["userActivity"]["users"] == ["用户A", "用户B"]
    assert payload["userActivity"]["counts"] == [5, 3]
    assert payload["sentimentData"] == [
        {"name": "正面", "value": 1},
        {"name": "中性", "value": 1},
        {"name": "负面", "value": 1},
    ]
    assert payload["hotComments"][0]["user"] == "用户A"
    assert payload["hotComments"][0]["likes"] == 12
