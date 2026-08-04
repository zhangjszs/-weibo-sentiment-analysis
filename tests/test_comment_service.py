#!/usr/bin/env python3
"""
comment_service.py 单元测试

comment_service 是评论查询服务，封装分页查询与日期格式化，依赖
CommentRepository。此前无独立单元测试。

测试策略：
- offset 计算（page/limit 组合）
- find_with_filter 调用参数透传
- created_at 字符串化（truthy 转换、None/空/缺失 跳过）
- 返回结构（total / page / limit / list）

mock CommentRepository，不触碰真实 DB。
"""

import pytest

pytestmark = pytest.mark.unit

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.comment_service import CommentService


@pytest.fixture
def mock_comment_repo():
    """Patch CommentRepository，使 CommentService 使用 mock 仓储。"""
    with patch("services.comment_service.CommentRepository") as mock_class:
        repo = MagicMock()
        mock_class.return_value = repo
        yield repo


# ---------------------------------------------------------------------------
# get_comments
# ---------------------------------------------------------------------------


class TestGetComments:
    """get_comments 分页查询"""

    def test_returns_correct_structure(self, mock_comment_repo):
        """返回 {total, page, limit, list}"""
        mock_comment_repo.find_with_filter.return_value = ([], 0)
        service = CommentService()

        result = service.get_comments(1, 10, "", "", "", "", "")

        assert result == {"total": 0, "page": 1, "limit": 10, "list": []}

    def test_passes_through_list_and_total(self, mock_comment_repo):
        """list 与 total 应来自仓储返回"""
        comments = [{"id": 1}, {"id": 2}]
        mock_comment_repo.find_with_filter.return_value = (comments, 2)
        service = CommentService()

        result = service.get_comments(1, 10, "", "", "", "", "")

        assert result["total"] == 2
        assert result["list"] == comments

    def test_offset_calculation_first_page(self, mock_comment_repo):
        """page=1, limit=10 → offset=0"""
        mock_comment_repo.find_with_filter.return_value = ([], 0)
        service = CommentService()
        service.get_comments(1, 10, "", "", "", "", "")

        assert mock_comment_repo.find_with_filter.call_args[1]["offset"] == 0

    def test_offset_calculation_later_page(self, mock_comment_repo):
        """page=3, limit=20 → offset=40"""
        mock_comment_repo.find_with_filter.return_value = ([], 0)
        service = CommentService()
        service.get_comments(3, 20, "", "", "", "", "")

        assert mock_comment_repo.find_with_filter.call_args[1]["offset"] == 40

    def test_find_with_filter_called_with_all_kwargs(self, mock_comment_repo):
        """应将所有过滤参数以 kwargs 透传给 find_with_filter"""
        mock_comment_repo.find_with_filter.return_value = ([], 0)
        service = CommentService()

        service.get_comments(
            page=2,
            limit=15,
            keyword="AI",
            article_id="a1",
            user="alice",
            start_time="2026-01-01",
            end_time="2026-02-01",
        )

        kwargs = mock_comment_repo.find_with_filter.call_args[1]
        assert kwargs == {
            "keyword": "AI",
            "article_id": "a1",
            "user": "alice",
            "start_time": "2026-01-01",
            "end_time": "2026-02-01",
            "limit": 15,
            "offset": 15,  # (2-1)*15
        }

    def test_created_at_stringified(self, mock_comment_repo):
        """created_at 为 datetime 对象 → 转为字符串"""
        dt = datetime(2026, 7, 29, 10, 30, 0)
        mock_comment_repo.find_with_filter.return_value = (
            [{"id": 1, "created_at": dt}],
            1,
        )
        service = CommentService()

        result = service.get_comments(1, 10, "", "", "", "", "")

        assert result["list"][0]["created_at"] == str(dt)
        assert isinstance(result["list"][0]["created_at"], str)

    def test_created_at_string_already_string_unchanged(self, mock_comment_repo):
        """created_at 已是字符串 → str() 后仍为原值"""
        mock_comment_repo.find_with_filter.return_value = (
            [{"id": 1, "created_at": "2026-07-29"}],
            1,
        )
        service = CommentService()

        result = service.get_comments(1, 10, "", "", "", "", "")

        assert result["list"][0]["created_at"] == "2026-07-29"

    def test_created_at_none_skipped(self, mock_comment_repo):
        """created_at 为 None → 不转换（保持 None，因 `item["created_at"]` falsy）"""
        mock_comment_repo.find_with_filter.return_value = (
            [{"id": 1, "created_at": None}],
            1,
        )
        service = CommentService()

        result = service.get_comments(1, 10, "", "", "", "", "")

        assert result["list"][0]["created_at"] is None

    def test_created_at_empty_string_skipped(self, mock_comment_repo):
        """created_at 为空字符串 → 不转换（falsy）"""
        mock_comment_repo.find_with_filter.return_value = (
            [{"id": 1, "created_at": ""}],
            1,
        )
        service = CommentService()

        result = service.get_comments(1, 10, "", "", "", "", "")

        assert result["list"][0]["created_at"] == ""

    def test_missing_created_at_key_unchanged(self, mock_comment_repo):
        """item 无 created_at 键 → 不抛异常，item 不变"""
        mock_comment_repo.find_with_filter.return_value = ([{"id": 1}], 1)
        service = CommentService()

        result = service.get_comments(1, 10, "", "", "", "", "")

        assert "created_at" not in result["list"][0]

    def test_mixed_items_only_stringifies_truthy_created_at(self, mock_comment_repo):
        """混合列表：仅 truthy created_at 被转换"""
        dt = datetime(2026, 7, 29)
        items = [
            {"id": 1, "created_at": dt},  # truthy → 转
            {"id": 2, "created_at": None},  # falsy → 不转
            {"id": 3},  # 无键 → 不转
            {"id": 4, "created_at": ""},  # falsy → 不转
        ]
        mock_comment_repo.find_with_filter.return_value = (items, 4)
        service = CommentService()

        result = service.get_comments(1, 10, "", "", "", "", "")

        assert result["list"][0]["created_at"] == str(dt)
        assert result["list"][1]["created_at"] is None
        assert "created_at" not in result["list"][2]
        assert result["list"][3]["created_at"] == ""

    def test_does_not_mutate_unrelated_fields(self, mock_comment_repo):
        """其他字段不应被修改"""
        mock_comment_repo.find_with_filter.return_value = (
            [{"id": 1, "created_at": "2026-07-29", "content": "hi", "user": "bob"}],
            1,
        )
        service = CommentService()

        result = service.get_comments(1, 10, "", "", "", "", "")

        item = result["list"][0]
        assert item["content"] == "hi"
        assert item["user"] == "bob"
        assert item["id"] == 1

    def test_page_and_limit_echoed_in_result(self, mock_comment_repo):
        """返回的 page/limit 应为入参原值"""
        mock_comment_repo.find_with_filter.return_value = ([], 0)
        service = CommentService()

        result = service.get_comments(5, 25, "", "", "", "", "")

        assert result["page"] == 5
        assert result["limit"] == 25
