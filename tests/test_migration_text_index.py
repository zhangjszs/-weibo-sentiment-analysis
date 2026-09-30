#!/usr/bin/env python3
"""#27 回归：MySQL 上给 TEXT/BLOB 列建索引必须带前缀长度。

冻结 SQL（docs/database/init_database.sql）把 article.authorName 声明为
`text`，而 ORM（src/models/article.py）声明为 String(100)——schema 双真相。
迁移 451ad37a1950 对该列直接建索引，在 MySQL 上会报：

    1170 BLOB/TEXT column 'authorName' used in key specification without a key length

CI 的 integration job 跑 `alembic upgrade head` 时因此整条链失败。
"""

import importlib.util
import os

import pytest

pytestmark = pytest.mark.unit

MIGRATION_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "alembic",
    "versions",
    "451ad37a1950_add_missing_indexes.py",
)


def _load_migration():
    spec = importlib.util.spec_from_file_location("m451", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class FakeDialect:
    def __init__(self, name):
        self.name = name


class FakeConnection:
    """最小替身：dialect.name + execute(...) 返回 information_schema 行。"""

    def __init__(self, dialect_name, rows=()):
        self.dialect = FakeDialect(dialect_name)
        self._rows = list(rows)
        self.statements = []

    def execute(self, statement, params=None):
        self.statements.append(str(statement))
        if params is None:
            return FakeResult(self._rows)
        return FakeResult(self._rows)


def test_mysql_text_column_gets_prefix_length():
    """TEXT 列必须产出 sa.text() 前缀表达式，而不是字符串。

    这是核心：alembic 收到普通 str 会当成列名处理
    （Column("authorName(100)")），渲染成 `authorName(100)`，
    MySQL 会当成带引号的列名，仍报 1170。
    """
    import sqlalchemy as sa

    mod = _load_migration()
    conn = FakeConnection("mysql", rows=[("authorName", "text")])
    result = mod._with_mysql_prefix_length(conn, "article", ["authorName"])
    assert len(result) == 1
    assert isinstance(result[0], sa.TextClause), "前缀必须用 sa.text()，否则被当列名"
    assert str(result[0]) == "authorName(100)"


def test_mysql_varchar_column_left_alone():
    mod = _load_migration()
    conn = FakeConnection("mysql", rows=[("authorName", "varchar")])
    assert mod._with_mysql_prefix_length(conn, "article", ["authorName"]) == [
        "authorName"
    ]


def test_mysql_mixed_columns():
    mod = _load_migration()
    conn = FakeConnection(
        "mysql", rows=[("authorName", "TEXT"), ("commentsLen", "int")]
    )
    result = mod._with_mysql_prefix_length(
        conn, "article", ["authorName", "commentsLen"]
    )
    assert str(result[0]) == "authorName(100)"
    assert result[1] == "commentsLen"


@pytest.mark.parametrize("blob_type", ["tinytext", "mediumtext", "longtext", "blob"])
def test_all_text_and_blob_families_get_prefix(blob_type):
    mod = _load_migration()
    conn = FakeConnection("mysql", rows=[("col_a", blob_type)])
    result = mod._with_mysql_prefix_length(conn, "t", ["col_a"])
    assert str(result[0]) == f"col_a({mod._PREFIX_LENGTH})"


def test_sqlite_is_untouched():
    """SQLite 支持对 TEXT 直接建索引，不应加前缀（否则列名解析失败）。"""
    mod = _load_migration()
    conn = FakeConnection("sqlite", rows=[("authorName", "TEXT")])
    assert mod._with_mysql_prefix_length(conn, "article", ["authorName"]) == [
        "authorName"
    ]
    # 不该为非 MySQL 方言发起 information_schema 查询
    assert conn.statements == []


def test_query_failure_degrades_gracefully():
    """查询失败时退回原列名，不能让整条迁移炸掉。"""

    class Boom(FakeConnection):
        def execute(self, statement, params=None):
            raise RuntimeError("no such table")

    mod = _load_migration()
    conn = Boom("mysql")
    assert mod._with_mysql_prefix_length(conn, "article", ["authorName"]) == [
        "authorName"
    ]


def test_unknown_column_left_alone():
    """information_schema 里没有的列不应被加前缀（避免造出坏 SQL）。"""
    mod = _load_migration()
    conn = FakeConnection("mysql", rows=[("other", "TEXT")])
    assert mod._with_mysql_prefix_length(conn, "article", ["authorName"]) == [
        "authorName"
    ]


def test_prefix_renders_as_prefix_index_in_sql():
    """交给 alembic 渲染出的 DDL 必须是 authorName(100)，不能是被引号包住的列名。"""
    import sqlalchemy as sa
    from sqlalchemy.dialects import mysql
    from sqlalchemy.schema import CreateIndex

    md = sa.MetaData()
    table = sa.Table("article", md, sa.Column("authorName", sa.Text))
    idx = sa.Index("idx_author_name", sa.text("authorName(100)"), _table=table)
    ddl = str(CreateIndex(idx).compile(dialect=mysql.dialect()))
    assert "authorName(100)" in ddl, ddl
    assert "`authorName(100)`" not in ddl, ddl


def test_prefix_length_matches_frozen_sql_convention():
    """前缀长度与冻结 SQL 里 type/authorName 索引所用的 100 保持一致。"""
    sql_path = os.path.join(
        os.path.dirname(__file__), "..", "docs", "database", "init_database.sql"
    )
    with open(sql_path, encoding="utf-8") as handle:
        content = handle.read()
    assert "(`authorName`(100))" in content, "冻结 SQL 已为 authorName 索引标注前缀"
    mod = _load_migration()
    assert mod._PREFIX_LENGTH == 100
