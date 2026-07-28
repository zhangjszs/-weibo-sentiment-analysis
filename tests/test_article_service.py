#!/usr/bin/env python3
"""
article_service.py 单元测试

article_service 是文章查询服务，封装分页查询、日期格式化与统计汇总，依赖
ArticleRepository 与 utils.query.querys。此前无独立单元测试。

测试策略：
- get_articles：offset 计算、find_with_filter 位置参数透传、默认
  article_type/region、created_at 字符串化、返回结构
- get_stats_summary：article_repo.count + querys 取 comments/users 计数
- get_today_stats：today 日期、querys 调用、latest_update 字符串化、
  空结果回退 0、latest 为 None 时回退 None

mock ArticleRepository 与 utils.query.querys，不触碰真实 DB / SQL。
"""

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.article_service import ArticleService


@pytest.fixture
def mock_article_repo():
    """Patch ArticleRepository，使 ArticleService 使用 mock 仓储。"""
    with patch("services.article_service.ArticleRepository") as mock_class:
        repo = MagicMock()
        mock_class.return_value = repo
        yield repo


# ---------------------------------------------------------------------------
# get_articles
# ---------------------------------------------------------------------------


class TestGetArticles:
    """get_articles 分页查询"""

    def test_returns_correct_structure(self, mock_article_repo):
        """返回 {total, page, limit, list}"""
        mock_article_repo.find_with_filter.return_value = ([], 0)
        service = ArticleService()

        result = service.get_articles(1, 10, "", "", "")

        assert result == {"total": 0, "page": 1, "limit": 10, "list": []}

    def test_passes_through_list_and_total(self, mock_article_repo):
        """list 与 total 应来自仓储返回"""
        articles = [{"id": 1}, {"id": 2}]
        mock_article_repo.find_with_filter.return_value = (articles, 2)
        service = ArticleService()

        result = service.get_articles(1, 10, "", "", "")

        assert result["total"] == 2
        assert result["list"] == articles

    def test_offset_calculation_first_page(self, mock_article_repo):
        """page=1, limit=10 → offset=0"""
        mock_article_repo.find_with_filter.return_value = ([], 0)
        service = ArticleService()
        service.get_articles(1, 10, "", "", "")

        # find_with_filter 位置参数: (keyword, start_time, end_time, article_type, region, limit, offset)
        args = mock_article_repo.find_with_filter.call_args[0]
        assert args[6] == 0  # offset

    def test_offset_calculation_later_page(self, mock_article_repo):
        """page=3, limit=20 → offset=40"""
        mock_article_repo.find_with_filter.return_value = ([], 0)
        service = ArticleService()
        service.get_articles(3, 20, "", "", "")

        args = mock_article_repo.find_with_filter.call_args[0]
        assert args[6] == 40  # offset 位置（第 7 个位置参数）

    def test_find_with_filter_called_with_positional_args(self, mock_article_repo):
        """应以位置参数透传 (keyword, start_time, end_time, article_type, region, limit, offset)"""
        mock_article_repo.find_with_filter.return_value = ([], 0)
        service = ArticleService()

        service.get_articles(
            page=2,
            limit=15,
            keyword="AI",
            start_time="2026-01-01",
            end_time="2026-02-01",
            article_type="news",
            region="cn",
        )

        args = mock_article_repo.find_with_filter.call_args[0]
        assert args == ("AI", "2026-01-01", "2026-02-01", "news", "cn", 15, 15)

    def test_default_article_type_and_region_empty(self, mock_article_repo):
        """未传 article_type/region → 默认空字符串"""
        mock_article_repo.find_with_filter.return_value = ([], 0)
        service = ArticleService()

        service.get_articles(1, 10, "AI", "2026-01-01", "2026-02-01")

        args = mock_article_repo.find_with_filter.call_args[0]
        assert args[3] == ""  # article_type
        assert args[4] == ""  # region

    def test_created_at_stringified(self, mock_article_repo):
        """created_at 为 datetime 对象 → 转为字符串"""
        dt = datetime(2026, 7, 29, 10, 30, 0)
        mock_article_repo.find_with_filter.return_value = (
            [{"id": 1, "created_at": dt}],
            1,
        )
        service = ArticleService()

        result = service.get_articles(1, 10, "", "", "")

        assert result["list"][0]["created_at"] == str(dt)
        assert isinstance(result["list"][0]["created_at"], str)

    def test_created_at_none_skipped(self, mock_article_repo):
        """created_at 为 None → 不转换（falsy）"""
        mock_article_repo.find_with_filter.return_value = (
            [{"id": 1, "created_at": None}],
            1,
        )
        service = ArticleService()

        result = service.get_articles(1, 10, "", "", "")

        assert result["list"][0]["created_at"] is None

    def test_missing_created_at_key_unchanged(self, mock_article_repo):
        """item 无 created_at 键 → 不抛异常"""
        mock_article_repo.find_with_filter.return_value = ([{"id": 1}], 1)
        service = ArticleService()

        result = service.get_articles(1, 10, "", "", "")

        assert "created_at" not in result["list"][0]

    def test_page_and_limit_echoed_in_result(self, mock_article_repo):
        """返回的 page/limit 应为入参原值"""
        mock_article_repo.find_with_filter.return_value = ([], 0)
        service = ArticleService()

        result = service.get_articles(5, 25, "", "", "")

        assert result["page"] == 5
        assert result["limit"] == 25


# ---------------------------------------------------------------------------
# get_stats_summary
# ---------------------------------------------------------------------------


class TestGetStatsSummary:
    """get_stats_summary 全局计数汇总"""

    @patch("utils.query.querys")
    def test_returns_counts_from_repo_and_querys(self, mock_querys, mock_article_repo):
        """articles 来自 repo.count，comments/users 来自 querys"""
        mock_article_repo.count.return_value = 42
        mock_querys.side_effect = [
            [{"count": 100}],  # comments
            [{"count": 7}],  # users
        ]
        service = ArticleService()

        result = service.get_stats_summary()

        assert result == {"articles": 42, "comments": 100, "users": 7}

    @patch("utils.query.querys")
    def test_comments_query_sql(self, mock_querys, mock_article_repo):
        """comments 查询应使用 comments 表"""
        mock_article_repo.count.return_value = 0
        mock_querys.side_effect = [[{"count": 0}], [{"count": 0}]]
        service = ArticleService()

        service.get_stats_summary()

        comments_call = mock_querys.call_args_list[0]
        assert "comments" in comments_call.args[0]
        assert comments_call.kwargs.get("type") == "select"

    @patch("utils.query.querys")
    def test_users_query_sql(self, mock_querys, mock_article_repo):
        """users 查询应使用 user 表"""
        mock_article_repo.count.return_value = 0
        mock_querys.side_effect = [[{"count": 0}], [{"count": 0}]]
        service = ArticleService()

        service.get_stats_summary()

        users_call = mock_querys.call_args_list[1]
        assert "user" in users_call.args[0]

    @patch("utils.query.querys")
    def test_article_count_from_repo(self, mock_querys, mock_article_repo):
        """articles 计数应来自 article_repo.count()"""
        mock_article_repo.count.return_value = 99
        mock_querys.side_effect = [[{"count": 0}], [{"count": 0}]]
        service = ArticleService()

        result = service.get_stats_summary()

        mock_article_repo.count.assert_called_once()
        assert result["articles"] == 99


# ---------------------------------------------------------------------------
# get_today_stats
# ---------------------------------------------------------------------------


class TestGetTodayStats:
    """get_today_stats 今日新增统计"""

    @patch("utils.query.querys")
    def test_returns_today_counts_and_latest(self, mock_querys, mock_article_repo):
        """返回 today_articles / today_comments / latest_update"""
        mock_querys.side_effect = [
            [{"count": 5}],  # articles today
            [{"count": 8}],  # comments today
        ]
        mock_article_repo.get_latest_update_time.return_value = "2026-07-29 10:00:00"
        service = ArticleService()

        result = service.get_today_stats()

        assert result["today_articles"] == 5
        assert result["today_comments"] == 8
        assert result["latest_update"] == "2026-07-29 10:00:00"

    @patch("utils.query.querys")
    def test_today_date_passed_to_article_query(self, mock_querys, mock_article_repo):
        """article 查询应传入今日日期字符串（YYYY-MM-DD）"""
        mock_querys.side_effect = [[{"count": 0}], [{"count": 0}]]
        mock_article_repo.get_latest_update_time.return_value = None
        service = ArticleService()

        service.get_today_stats()

        article_call = mock_querys.call_args_list[0]
        date_arg = article_call.args[1][0]
        # 形如 YYYY-MM-DD
        assert len(date_arg) == 10
        assert date_arg[4] == "-" and date_arg[7] == "-"

    @patch("utils.query.querys")
    def test_today_date_passed_to_comment_query(self, mock_querys, mock_article_repo):
        """comment 查询也应传入今日日期"""
        mock_querys.side_effect = [[{"count": 0}], [{"count": 0}]]
        mock_article_repo.get_latest_update_time.return_value = None
        service = ArticleService()

        service.get_today_stats()

        comment_call = mock_querys.call_args_list[1]
        date_arg = comment_call.args[1][0]
        assert len(date_arg) == 10

    @patch("utils.query.querys")
    def test_empty_article_rows_falls_back_to_zero(self, mock_querys, mock_article_repo):
        """article_rows 为空列表 → today_articles=0"""
        mock_querys.side_effect = [
            [],  # 无行
            [{"count": 3}],
        ]
        mock_article_repo.get_latest_update_time.return_value = None
        service = ArticleService()

        result = service.get_today_stats()

        assert result["today_articles"] == 0

    @patch("utils.query.querys")
    def test_empty_comment_rows_falls_back_to_zero(
        self, mock_querys, mock_article_repo
    ):
        """comment_rows 为空列表 → today_comments=0"""
        mock_querys.side_effect = [
            [{"count": 3}],
            [],
        ]
        mock_article_repo.get_latest_update_time.return_value = None
        service = ArticleService()

        result = service.get_today_stats()

        assert result["today_comments"] == 0

    @patch("utils.query.querys")
    def test_count_value_coerced_to_int(self, mock_querys, mock_article_repo):
        """count 值为字符串数字时应被 int() 转换"""
        mock_querys.side_effect = [
            [{"count": "12"}],  # 字符串
            [{"count": "34"}],
        ]
        mock_article_repo.get_latest_update_time.return_value = None
        service = ArticleService()

        result = service.get_today_stats()

        assert result["today_articles"] == 12
        assert result["today_comments"] == 34
        assert isinstance(result["today_articles"], int)
        assert isinstance(result["today_comments"], int)

    @patch("utils.query.querys")
    def test_missing_count_key_falls_back_to_zero(
        self, mock_querys, mock_article_repo
    ):
        """行存在但无 count 键 → .get('count', 0) 回退 0"""
        mock_querys.side_effect = [
            [{"other": "x"}],
            [{"other": "y"}],
        ]
        mock_article_repo.get_latest_update_time.return_value = None
        service = ArticleService()

        result = service.get_today_stats()

        assert result["today_articles"] == 0
        assert result["today_comments"] == 0

    @patch("utils.query.querys")
    def test_latest_update_none_when_repo_returns_none(
        self, mock_querys, mock_article_repo
    ):
        """仓储返回 None → latest_update=None"""
        mock_querys.side_effect = [[{"count": 0}], [{"count": 0}]]
        mock_article_repo.get_latest_update_time.return_value = None
        service = ArticleService()

        result = service.get_today_stats()

        assert result["latest_update"] is None

    @patch("utils.query.querys")
    def test_latest_update_stringified_when_present(
        self, mock_querys, mock_article_repo
    ):
        """仓储返回非 None → latest_update=str(latest)"""
        mock_querys.side_effect = [[{"count": 0}], [{"count": 0}]]
        mock_article_repo.get_latest_update_time.return_value = "2026-07-29 12:00:00"
        service = ArticleService()

        result = service.get_today_stats()

        assert result["latest_update"] == "2026-07-29 12:00:00"

    @patch("utils.query.querys")
    def test_article_query_uses_date_function(self, mock_querys, mock_article_repo):
        """article 查询应使用 DATE(created_at) 过滤"""
        mock_querys.side_effect = [[{"count": 0}], [{"count": 0}]]
        mock_article_repo.get_latest_update_time.return_value = None
        service = ArticleService()

        service.get_today_stats()

        article_sql = mock_querys.call_args_list[0].args[0]
        assert "DATE(created_at)" in article_sql
        assert "article" in article_sql

    @patch("utils.query.querys")
    def test_comment_query_uses_date_function(self, mock_querys, mock_article_repo):
        """comment 查询应使用 DATE(created_at) 过滤"""
        mock_querys.side_effect = [[{"count": 0}], [{"count": 0}]]
        mock_article_repo.get_latest_update_time.return_value = None
        service = ArticleService()

        service.get_today_stats()

        comment_sql = mock_querys.call_args_list[1].args[0]
        assert "DATE(created_at)" in comment_sql
        assert "comments" in comment_sql
