#!/usr/bin/env python3
"""
ECharts 数据查询优化测试

#14 重构后，utils.getEchartsData / utils.getHomeData 不再经过
utils.query_dataframe 裸 SQL，而是委托 ArticleRepository / CommentRepository
的聚合方法（#30：旧测试 patch 的 query_dataframe 符号已不存在）。
patch 点相应改为 Repository 的具体方法；直方图类查询改在 database.engine
边界注入假连接，让生产端的 CASE WHEN 分桶 + 标签构建逻辑真实执行。
测试意图不变：断言图表路径不做全表扫描。
"""

import pytest

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# 直方图假 engine：get_histogram / get_like_histogram 在函数体内
# `from database import engine`，替换该属性即可拦截，SQL 构建仍走生产代码。
# ---------------------------------------------------------------------------


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def __iter__(self):
        return iter(self._rows)


class _FakeConnection:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, statement, params=None):
        return _FakeResult(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _FakeEngine:
    def __init__(self, rows):
        self._rows = rows

    def connect(self):
        return _FakeConnection(self._rows)


def _patch_histogram_engine(monkeypatch, rows):
    import database

    monkeypatch.setattr(database, "engine", _FakeEngine(rows))


def _forbid(monkeypatch, module, name, message):
    monkeypatch.setattr(
        module, name, lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError(message))
    )


def test_article_chart_queries_do_not_call_full_article_scan(monkeypatch):
    import utils.getEchartsData as echarts
    import utils.getPublicData as public_data
    from repositories.article_repository import ArticleRepository

    _forbid(monkeypatch, public_data, "getAllData", "should not load full article rows")
    monkeypatch.setattr(
        ArticleRepository, "get_distinct_types", lambda self: ["news", "blog"]
    )
    # 聚合返回 (bucket_index, count)，标签与填零由生产代码完成
    _patch_histogram_engine(monkeypatch, [(0, 2), (2, 1)])

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
    from repositories.article_repository import ArticleRepository
    from repositories.comment_repository import CommentRepository
    from services.sentiment_service import SentimentService

    _forbid(monkeypatch, public_data, "getAllCommentsData", "should not load all comments")
    _forbid(monkeypatch, public_data, "getAllData", "should not load all articles")
    monkeypatch.setattr(
        CommentRepository, "get_recent_texts", lambda self, limit=200: ["很好", "一般"]
    )
    monkeypatch.setattr(
        ArticleRepository, "get_recent_texts", lambda self, limit=200: ["积极", "消极"]
    )
    monkeypatch.setattr(
        SentimentService,
        "analyze_distribution_cached",
        lambda texts, mode="simple", sample_size=200: {
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


def test_home_data_queries_use_aggregations(monkeypatch, request):
    import utils.getHomeData as home_data
    import utils.getPublicData as public_data
    from repositories.article_repository import ArticleRepository
    from repositories.comment_repository import CommentRepository
    from utils.cache import clear_all_cache

    # getHomeData 的函数带 @cache_result：进出各清一次，
    # 防止跨测试污染（fake 结果泄漏给后续用例 / 上个用例残留命中本用例）。
    clear_all_cache()
    request.addfinalizer(clear_all_cache)

    _forbid(monkeypatch, public_data, "getArticleDataFrame", "should not load article dataframe")
    _forbid(monkeypatch, public_data, "getCommentsDataFrame", "should not load comments dataframe")
    monkeypatch.setattr(
        CommentRepository,
        "get_top_liked_comments",
        lambda self, limit=4: [
            {
                "articleId": "a1",
                "created_at": "2026-03-20 10:00:00",
                "like_counts": 9,
                "region": "北京",
                "content": "很好",
                "authorName": "用户A",
                "authorGender": "女",
                "authorAddress": "北京",
                "authorAvatar": "a.png",
            }
        ],
    )
    monkeypatch.setattr(ArticleRepository, "count_total", lambda self: 7)
    monkeypatch.setattr(ArticleRepository, "get_top_liked_author", lambda self: "作者A")
    monkeypatch.setattr(
        ArticleRepository, "count_by_region", lambda self, limit=1: [{"region": "北京", "count": 7}]
    )
    monkeypatch.setattr(
        ArticleRepository,
        "count_by_date_range",
        lambda self: [{"created_at": "2026-03-20", "count": 4}, {"created_at": "2026-03-19", "count": 3}],
    )
    monkeypatch.setattr(
        ArticleRepository,
        "count_by_type",
        lambda self: [{"type": "news", "count": 5}, {"type": "blog", "count": 2}],
    )
    monkeypatch.setattr(
        CommentRepository,
        "count_by_date_range",
        lambda self: [{"created_at": "2026-03-20", "count": 6}, {"created_at": "2026-03-19", "count": 1}],
    )

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


def test_home_data_does_not_fallback_to_full_scans_on_empty_results(monkeypatch, request):
    import utils.getHomeData as home_data
    import utils.getPublicData as public_data
    from repositories.article_repository import ArticleRepository
    from repositories.comment_repository import CommentRepository
    from utils.cache import clear_all_cache

    clear_all_cache()
    request.addfinalizer(clear_all_cache)

    _forbid(monkeypatch, public_data, "getAllCommentsData", "should not load all comments")
    _forbid(monkeypatch, public_data, "getAllData", "should not load all articles")
    monkeypatch.setattr(CommentRepository, "get_top_liked_comments", lambda self, limit=4: [])
    monkeypatch.setattr(ArticleRepository, "count_total", lambda self: 0)
    monkeypatch.setattr(ArticleRepository, "get_top_liked_author", lambda self: None)
    monkeypatch.setattr(ArticleRepository, "count_by_region", lambda self, limit=1: [])
    monkeypatch.setattr(ArticleRepository, "count_by_date_range", lambda self: [])
    monkeypatch.setattr(ArticleRepository, "count_by_type", lambda self: [])
    monkeypatch.setattr(CommentRepository, "count_by_date_range", lambda self: [])

    assert home_data.getHomeTopLikeCommentsData() == []
    assert home_data.getTagData() == (0, "", "")
    assert home_data.getCreatedNumEchartsData() == ([], [])
    assert home_data.getTypeCharData() == []
    assert home_data.getCommentsUserCratedNumEchartsData() == []


def test_user_name_word_cloud_does_not_fallback_to_full_comment_scan(monkeypatch, request):
    import utils.getHomeData as home_data
    import utils.getPublicData as public_data
    from repositories.comment_repository import CommentRepository
    from utils.cache import clear_all_cache

    clear_all_cache()
    request.addfinalizer(clear_all_cache)

    _forbid(monkeypatch, public_data, "getCommentsDataFrame", "should not load comments dataframe")
    _forbid(monkeypatch, public_data, "getAllCommentsData", "should not load all comments")

    generated_texts = []

    class FakeWordCloud:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def generate_from_text(self, text):
            generated_texts.append(text)

    monkeypatch.setattr(
        CommentRepository,
        "get_all_for_export",
        lambda self: [{"authorName": "用户A"}, {"authorName": "用户B"}],
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
    from repositories.article_repository import ArticleRepository
    from repositories.comment_repository import CommentRepository

    _forbid(monkeypatch, public_data, "getAllCommentsData", "should not load all comments")
    _forbid(monkeypatch, public_data, "getAllData", "should not load all articles")
    monkeypatch.setattr(
        CommentRepository, "get_region_distribution", lambda self: [{"name": "北京", "value": 3}]
    )
    monkeypatch.setattr(
        ArticleRepository, "get_region_distribution", lambda self: [{"name": "上海", "value": 2}]
    )

    assert echarts.getGeoCharDataOne() == [{"name": "北京", "value": 3}]
    assert echarts.getGeoCharDataTwo() == [{"name": "上海", "value": 2}]


def test_comment_chart_queries_do_not_call_full_comment_scan(monkeypatch):
    import utils.getEchartsData as echarts
    import utils.getPublicData as public_data
    from repositories.comment_repository import CommentRepository

    _forbid(monkeypatch, public_data, "getAllCommentsData", "should not load all comments")
    _patch_histogram_engine(monkeypatch, [(0, 3), (2, 1)])
    monkeypatch.setattr(
        CommentRepository,
        "get_gender_distribution",
        lambda self: [{"name": "女", "value": 4}, {"name": "男", "value": 2}],
    )

    x_data, y_data = echarts.getCommetCharDataOne()
    assert x_data[0] == "20-40"
    assert y_data[0] == 3
    assert y_data[2] == 1

    gender_data = echarts.getCommetCharDataTwo()
    assert gender_data == [{"name": "女", "value": 4}, {"name": "男", "value": 2}]


def test_word_cloud_queries_do_not_call_full_scans(monkeypatch):
    import utils.getEchartsData as echarts
    import utils.getPublicData as public_data
    from repositories.article_repository import ArticleRepository
    from repositories.comment_repository import CommentRepository

    _forbid(monkeypatch, public_data, "getAllData", "should not load all articles")
    _forbid(monkeypatch, public_data, "getAllCommentsData", "should not load all comments")

    generated_texts = []

    class FakeWordCloud:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def generate_from_text(self, text):
            generated_texts.append(text)

    monkeypatch.setattr(
        ArticleRepository, "get_recent_texts", lambda self, limit=1000: ["alpha", "beta"]
    )
    monkeypatch.setattr(
        CommentRepository, "get_recent_texts", lambda self, limit=1000: ["gamma", "delta"]
    )
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
