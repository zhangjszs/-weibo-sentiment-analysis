#!/usr/bin/env python3
"""#10 回归：LIKE 转义、直方图白名单/dict 参数、占位符解析器。"""

import pytest

pytestmark = pytest.mark.unit


class TestEscapeLike:
    def test_escapes_wildcards(self):
        from utils.sql_safety import escape_like

        assert escape_like("100%_x\\y") == "100\\%\\_x\\\\y"
        assert escape_like("") == ""
        assert escape_like(None) == ""

    def test_keyword_with_wildcards_does_not_expand(self, alert_db, monkeypatch):
        """含百分号/下划线的 keyword 不应扩大匹配（alert_db 提供隔离库）。"""
        import repositories.base_repository as _base_repo

        # Repository 在 base_repository 导入期绑定 db_session，
        # 需补丁该命名空间才能指向 alert_db 的隔离库
        monkeypatch.setattr(_base_repo, "db_session", alert_db)

        from models.article import Article
        from repositories.article_repository import ArticleRepository

        # 注：alert_db fixture 已建表；直接写入两行
        alert_db.add_all(
            [
                Article(id="a1", content="abc", region="BJ", type="t"),
                Article(id="a2", content="aXc", region="SH", type="t"),
            ]
        )
        alert_db.commit()

        repo = ArticleRepository()
        rows, total = repo.find_with_filter(keyword="a%c")
        assert total == 0, f"转义后 a%c 应无匹配，got {total}"
        assert rows == []

        rows, total = repo.find_with_filter(keyword="a_c")
        assert total == 0

    def test_histogram_rejects_bad_column(self):
        from repositories.article_repository import ArticleRepository

        with pytest.raises(ValueError):
            ArticleRepository().get_histogram("content; DROP TABLE article;--")


class TestNamedParams:
    def test_basic_conversion(self):
        from utils.query import _build_named_params

        sql, params = _build_named_params("SELECT * FROM t WHERE a=%s AND b=%s", [1, 2])
        assert sql == "SELECT * FROM t WHERE a=:p0 AND b=:p1"
        assert params == {"p0": 1, "p1": 2}

    def test_literal_percent_s_untouched(self):
        from utils.query import _build_named_params

        sql, params = _build_named_params(
            "SELECT * FROM t WHERE a=%s AND b LIKE '%s%'", ["x"]
        )
        assert sql == "SELECT * FROM t WHERE a=:p0 AND b LIKE '%s%'"
        assert params == {"p0": "x"}

    def test_escaped_quote_literal_untouched(self):
        from utils.query import _build_named_params

        sql, params = _build_named_params(
            r"SELECT * FROM t WHERE a=%s AND c='it\'s %s here'", ["x"]
        )
        assert ":p0" in sql
        assert "'it\\'s %s here'" in sql
        assert params == {"p0": "x"}

    def test_double_quoted_identifier_untouched(self):
        from utils.query import _build_named_params

        sql, params = _build_named_params(
            'SELECT "%s" FROM t WHERE a=%s', ["x"]
        )
        assert sql == 'SELECT "%s" FROM t WHERE a=:p0'

    def test_double_percent_passthrough(self):
        from utils.query import _build_named_params

        sql, params = _build_named_params(
            "SELECT * FROM t WHERE a=%s AND b LIKE '100%%'", ["x"]
        )
        assert params == {"p0": "x"}
        assert "100%%" in sql

    def test_mismatch_raises(self):
        from utils.query import _build_named_params

        with pytest.raises(ValueError):
            _build_named_params("SELECT %s, %s", [1])
        with pytest.raises(ValueError):
            _build_named_params("SELECT 1", [1])
