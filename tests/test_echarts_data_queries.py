#!/usr/bin/env python3
"""
ECharts 数据查询优化测试
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_article_chart_queries_do_not_call_full_article_scan(monkeypatch):
    import utils.getEchartsData as echarts
    import utils.getPublicData as public_data

    monkeypatch.setattr(
        public_data,
        "getAllData",
        lambda: (_ for _ in ()).throw(AssertionError("should not load full article rows")),
    )

    def fake_query_dataframe(sql, params=None):
        if "SELECT DISTINCT type" in sql:
            return pd.DataFrame([{"type": "news"}, {"type": "blog"}])
        return pd.DataFrame([{"bucket_index": 0, "count": 2}, {"bucket_index": 2, "count": 1}])

    monkeypatch.setattr(echarts, "query_dataframe", fake_query_dataframe)

    assert echarts.getTypeList() == ["news", "blog"]

    x_data, y_data = echarts.getArticleCharOneData("news")
    assert x_data[0] == "1000-2000"
    assert y_data[0] == 2
    assert y_data[2] == 1

    x_two, y_two = echarts.getArticleCharTwoData("news")
    assert x_two[0] == "1000-2000"
    assert y_two[0] == 2

    x_three, y_three = echarts.getArticleCharThreeData("news")
    assert x_three[0] == "50-100"
    assert y_three[0] == 2


def test_yuqing_distribution_uses_recent_text_queries(monkeypatch):
    import utils.getEchartsData as echarts
    import utils.getPublicData as public_data
    from services.sentiment_service import SentimentService

    monkeypatch.setattr(
        public_data,
        "getAllCommentsData",
        lambda: (_ for _ in ()).throw(AssertionError("should not load all comments")),
    )
    monkeypatch.setattr(
        public_data,
        "getAllData",
        lambda: (_ for _ in ()).throw(AssertionError("should not load all articles")),
    )

    def fake_query_dataframe(sql, params=None):
        if "FROM comments" in sql:
            return pd.DataFrame([{"content": "很好"}, {"content": "一般"}])
        if "FROM article" in sql:
            return pd.DataFrame([{"content": "积极"}, {"content": "消极"}])
        return pd.DataFrame()

    monkeypatch.setattr(echarts, "query_dataframe", fake_query_dataframe)
    monkeypatch.setattr(
        SentimentService,
        "analyze_distribution",
        lambda texts, mode="simple", sample_size=100: {
            "正面": 1,
            "中性": 1,
            "负面": max(len(texts) - 2, 0),
        },
    )

    comment_dist, article_dist = echarts.getYuQingCharDataTwo()

    assert comment_dist[0]["value"] == 1
    assert comment_dist[1]["value"] == 1
    assert article_dist[0]["value"] == 1
    assert article_dist[1]["value"] == 1


def test_home_data_queries_use_aggregations(monkeypatch):
    import utils.getHomeData as home_data
    import utils.getPublicData as public_data

    monkeypatch.setattr(
        public_data,
        "getArticleDataFrame",
        lambda: (_ for _ in ()).throw(AssertionError("should not load article dataframe")),
    )
    monkeypatch.setattr(
        public_data,
        "getCommentsDataFrame",
        lambda: (_ for _ in ()).throw(AssertionError("should not load comments dataframe")),
    )

    def fake_query_dataframe(sql, params=None):
        if "ORDER BY like_counts DESC" in sql:
            return pd.DataFrame(
                [{"articleId": "a1", "created_at": "2026-03-20 10:00:00", "like_counts": 9}]
            )
        if "COUNT(*) AS article_count" in sql:
            return pd.DataFrame(
                [{"article_count": 7, "maxLikeAuthorName": "作者A", "maxCity": "北京"}]
            )
        if "FROM article" in sql and "GROUP BY created_at" in sql:
            return pd.DataFrame(
                [{"created_at": "2026-03-20", "count": 4}, {"created_at": "2026-03-19", "count": 3}]
            )
        if "FROM article" in sql and "GROUP BY type" in sql:
            return pd.DataFrame([{"type": "news", "count": 5}, {"type": "blog", "count": 2}])
        if "FROM comments" in sql and "GROUP BY created_at" in sql:
            return pd.DataFrame(
                [{"created_at": "2026-03-20", "count": 6}, {"created_at": "2026-03-19", "count": 1}]
            )
        return pd.DataFrame()

    monkeypatch.setattr(home_data, "query_dataframe", fake_query_dataframe)

    top_comments = home_data.getHomeTopLikeCommentsData()
    assert top_comments[0][2] == 9

    article_len, max_like_author, max_city = home_data.getTagData()
    assert article_len == 7
    assert max_like_author == "作者A"
    assert max_city == "北京"

    x_data, y_data = home_data.getCreatedNumEchartsData()
    assert x_data == ["2026-03-20", "2026-03-19"]
    assert y_data == [4, 3]

    type_data = home_data.getTypeCharData()
    assert type_data == [{"name": "news", "value": 5}, {"name": "blog", "value": 2}]

    comment_time_data = home_data.getCommentsUserCratedNumEchartsData()
    assert comment_time_data == [
        {"name": "2026-03-20", "value": 6},
        {"name": "2026-03-19", "value": 1},
    ]


def test_home_data_does_not_fallback_to_full_scans_on_empty_results(monkeypatch):
    import utils.getHomeData as home_data
    import utils.getPublicData as public_data
    from utils.cache import clear_all_cache

    clear_all_cache()
    monkeypatch.setattr(
        public_data,
        "getAllCommentsData",
        lambda: (_ for _ in ()).throw(AssertionError("should not load all comments")),
    )
    monkeypatch.setattr(
        public_data,
        "getAllData",
        lambda: (_ for _ in ()).throw(AssertionError("should not load all articles")),
    )

    monkeypatch.setattr(home_data, "query_dataframe", lambda sql, params=None: pd.DataFrame())

    assert home_data.getHomeTopLikeCommentsData() == []
    assert home_data.getTagData() == (0, "", "")
    assert home_data.getCreatedNumEchartsData() == ([], [])
    assert home_data.getTypeCharData() == []
    assert home_data.getCommentsUserCratedNumEchartsData() == []


def test_user_name_word_cloud_does_not_fallback_to_full_comment_scan(monkeypatch):
    import utils.getHomeData as home_data
    import utils.getPublicData as public_data
    from utils.cache import clear_all_cache

    clear_all_cache()
    monkeypatch.setattr(
        public_data,
        "getCommentsDataFrame",
        lambda: (_ for _ in ()).throw(AssertionError("should not load comments dataframe")),
    )
    monkeypatch.setattr(
        public_data,
        "getAllCommentsData",
        lambda: (_ for _ in ()).throw(AssertionError("should not load all comments")),
    )

    generated_texts = []

    class FakeWordCloud:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def generate_from_text(self, text):
            generated_texts.append(text)

    monkeypatch.setattr(
        home_data,
        "query_dataframe",
        lambda sql, params=None: pd.DataFrame([{"authorName": "用户A"}, {"authorName": "用户B"}]),
    )
    monkeypatch.setattr(home_data, "stopwordslist", lambda: [])
    monkeypatch.setattr(home_data.jieba, "cut", lambda text: text.split())
    monkeypatch.setattr(home_data, "WordCloud", FakeWordCloud)
    monkeypatch.setattr(home_data.plt, "figure", lambda *args, **kwargs: None)
    monkeypatch.setattr(home_data.plt, "imshow", lambda *args, **kwargs: None)
    monkeypatch.setattr(home_data.plt, "axis", lambda *args, **kwargs: None)
    monkeypatch.setattr(home_data.plt, "savefig", lambda *args, **kwargs: None)
    monkeypatch.setattr(home_data.plt, "close", lambda *args, **kwargs: None)
    monkeypatch.setattr(home_data.os.path, "exists", lambda path: False)

    result = home_data.getUserNameWordCloud()

    assert result is not None
    assert generated_texts == ["用户A 用户B"]


def test_geo_data_queries_use_sql_grouping(monkeypatch):
    import utils.getEchartsData as echarts
    import utils.getPublicData as public_data

    monkeypatch.setattr(
        public_data,
        "getAllCommentsData",
        lambda: (_ for _ in ()).throw(AssertionError("should not load all comments")),
    )
    monkeypatch.setattr(
        public_data,
        "getAllData",
        lambda: (_ for _ in ()).throw(AssertionError("should not load all articles")),
    )

    def fake_query_dataframe(sql, params=None):
        if "FROM comments" in sql:
            return pd.DataFrame([{"name": "北京", "value": 3}])
        if "FROM article" in sql:
            return pd.DataFrame([{"name": "上海", "value": 2}])
        return pd.DataFrame()

    monkeypatch.setattr(echarts, "query_dataframe", fake_query_dataframe)

    assert echarts.getGeoCharDataOne() == [{"name": "北京", "value": 3}]
    assert echarts.getGeoCharDataTwo() == [{"name": "上海", "value": 2}]


def test_comment_chart_queries_do_not_call_full_comment_scan(monkeypatch):
    import utils.getEchartsData as echarts
    import utils.getPublicData as public_data

    monkeypatch.setattr(
        public_data,
        "getAllCommentsData",
        lambda: (_ for _ in ()).throw(AssertionError("should not load all comments")),
    )

    def fake_query_dataframe(sql, params=None):
        if "authorGender" in sql:
            return pd.DataFrame(
                [{"name": "女", "value": 4}, {"name": "男", "value": 2}]
            )
        return pd.DataFrame(
            [{"bucket_index": 0, "count": 3}, {"bucket_index": 2, "count": 1}]
        )

    monkeypatch.setattr(echarts, "query_dataframe", fake_query_dataframe)

    x_data, y_data = echarts.getCommetCharDataOne()
    assert x_data[0] == "20-40"
    assert y_data[0] == 3
    assert y_data[2] == 1

    gender_data = echarts.getCommetCharDataTwo()
    assert gender_data == [{"name": "女", "value": 4}, {"name": "男", "value": 2}]


def test_word_cloud_queries_do_not_call_full_scans(monkeypatch):
    import utils.getEchartsData as echarts
    import utils.getPublicData as public_data

    monkeypatch.setattr(
        public_data,
        "getAllData",
        lambda: (_ for _ in ()).throw(AssertionError("should not load all articles")),
    )
    monkeypatch.setattr(
        public_data,
        "getAllCommentsData",
        lambda: (_ for _ in ()).throw(AssertionError("should not load all comments")),
    )

    generated_texts = []

    class FakeWordCloud:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def generate_from_text(self, text):
            generated_texts.append(text)

    def fake_query_dataframe(sql, params=None):
        if "FROM article" in sql:
            return pd.DataFrame([{"content": "alpha"}, {"content": "beta"}])
        if "FROM comments" in sql:
            return pd.DataFrame([{"content": "gamma"}, {"content": "delta"}])
        return pd.DataFrame()

    monkeypatch.setattr(echarts, "query_dataframe", fake_query_dataframe)
    monkeypatch.setattr(echarts, "stopwordslist", lambda: [])
    monkeypatch.setattr(echarts.jieba, "cut", lambda text: text.split())
    monkeypatch.setattr(echarts.Image, "open", lambda path: object())
    monkeypatch.setattr(echarts.np, "array", lambda image: [])
    monkeypatch.setattr(echarts, "WordCloud", FakeWordCloud)
    monkeypatch.setattr(echarts.plt, "figure", lambda *args, **kwargs: None)
    monkeypatch.setattr(echarts.plt, "imshow", lambda *args, **kwargs: None)
    monkeypatch.setattr(echarts.plt, "axis", lambda *args, **kwargs: None)
    monkeypatch.setattr(echarts.plt, "savefig", lambda *args, **kwargs: None)
    monkeypatch.setattr(echarts.plt, "close", lambda *args, **kwargs: None)

    assert echarts.getContentCloud() == "/static/contentCloud.jpg"
    assert echarts.getCommentContentCloud() == "/static/commentCloud.jpg"
    assert generated_texts == ["alpha beta", "gamma delta"]
