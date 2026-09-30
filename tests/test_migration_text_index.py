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
    os.path.dirname(__file__), "..", "alembic", "versions",
    "451ad37a1950_add_missing_indexes.py",
)


def _load_migration():
    spec = importlib.util.spec_from_file_location("m451", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeDialect:
    def __init__(self, name):
        self.name = name


class FakeInspector:
    def __init__(self, columns):
        self._columns = columns

    def get_columns(self, table_name):
        return [{"name": name, "type": typ} for name, typ in self._columns.items()]


class FakeConnection:
    """最小替身：只需 dialect.name 与 inspect(conn) 两个入口。"""

    def __init__(self, dialect_name, columns):
        self.dialect = FakeDialect(dialect_name)
        self._columns = columns

    # pylint: disable=unused-argument
    def inspect(self, conn):
        return FakeInspector(self._columns)


def test_mysql_text_column_gets_prefix_length(monkeypatch):
    """TEXT 列必须产出 sa.text() 前缀表达式，而不是字符串。

    这是本用例的核心：alembic 收到普通 str 会当成列名处理
    （Column("authorName(100)")），SQL 渲染出来的不是前缀索引。
    """
    import sqlalchemy as sa

    mod = _load_migration()
    monkeypatch.setattr(
        "sqlalchemy.inspect",
        lambda conn: FakeInspector({"authorName": "TEXT", "likeNum": "INTEGER"}),
    )
    conn = FakeConnection("mysql", {"authorName": "TEXT"})
    result = mod._with_mysql_prefix_length(conn, "article", ["authorName"])
    assert len(result) == 1
    assert isinstance(result[0], sa.TextClause), "前缀必须用 sa.text()，否则被当列名"
    assert str(result[0]) == "authorName(100)"


def test_mysql_varchar_column_left_alone(monkeypatch):
    mod = _load_migration()
    monkeypatch.setattr(
        "sqlalchemy.inspect",
        lambda conn: FakeInspector({"authorName": "VARCHAR(100)"}),
    )
    conn = FakeConnection("mysql", {"authorName": "VARCHAR(100)"})
    assert mod._with_mysql_prefix_length(conn, "article", ["authorName"]) == [
        "authorName"
    ]


def test_mysql_mixed_columns(monkeypatch):
    mod = _load_migration()
    monkeypatch.setattr(
        "sqlalchemy.inspect",
        lambda conn: FakeInspector({"authorName": "TEXT", "commentsLen": "INTEGER"}),
    )
    conn = FakeConnection("mysql", {})
    result = mod._with_mysql_prefix_length(
        conn, "article", ["authorName", "commentsLen"]
    )
    assert str(result[0]) == "authorName(100)"
    assert result[1] == "commentsLen"


def test_prefix_renders_as_prefix_index_in_sql():
    """把前缀表达式交给 alembic 渲染出的 DDL 必须是 INDEX ... (`authorName`(100))。"""
    import sqlalchemy as sa
    from sqlalchemy.dialects import mysql
    from sqlalchemy.schema import CreateIndex

    md = sa.MetaData()
    table = sa.Table("article", md, sa.Column("authorName", sa.Text))
    idx = sa.Index("idx_author_name", sa.text("authorName(100)"), _table=table)
    ddl = str(CreateIndex(idx).compile(dialect=mysql.dialect()))
    # 渲染结果必须是 authorName(100) 这种带前缀长度的形式，
    # 而不是把 (100) 当成列名的一部分（那会报 unknown column）。
    assert "authorName(100)" in ddl, ddl
    assert "CREATE INDEX idx_author_name ON article (authorName(100))" in ddl, ddl


def test_sqlite_is_untouched(monkeypatch):
    """SQLite 支持对 TEXT 直接建索引，不应加前缀（否则列名解析失败）。"""
    mod = _load_migration()
    conn = FakeConnection("sqlite", {"authorName": "TEXT"})
    assert mod._with_mysql_prefix_length(conn, "article", ["authorName"]) == [
        "authorName"
    ]


def test_inspector_failure_degrades_gracefully(monkeypatch):
    """反射失败时退回原列名，不能让整条迁移炸掉。"""

    def _boom(conn):
        raise RuntimeError("no such table")

    monkeypatch.setattr("sqlalchemy.inspect", _boom)
    mod = _load_migration()
    conn = FakeConnection("mysql", {})
    assert mod._with_mysql_prefix_length(conn, "article", ["authorName"]) == [
        "authorName"
    ]


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
