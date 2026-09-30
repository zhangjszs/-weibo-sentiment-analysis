#!/usr/bin/env python3
"""#27 回归：MySQL 上给 TEXT/BLOB 列建索引必须带前缀长度。

冻结 SQL（docs/database/init_database.sql）把 article.authorName、article.type、
article.content 等声明为 text/mediumtext，而 ORM（src/models/article.py）多声明成
String(n)——schema 双真相。迁移按列名建索引时落到 TEXT 列上就会报：

    1170 BLOB/TEXT column 'X' used in key specification without a key length

CI 的 integration job 跑 `alembic upgrade head` 时因此整条链失败。
本文件覆盖共享 helper 的行为，并钉死"相关迁移确实在用它"。
"""

import importlib.util
import os

import pytest

pytestmark = pytest.mark.unit

ALEMBIC_DIR = os.path.join(os.path.dirname(__file__), "..", "alembic")
HELPER_PATH = os.path.join(ALEMBIC_DIR, "index_helpers.py")

# 已知会在 TEXT 列上建索引的迁移
TEXT_INDEXING_MIGRATIONS = [
    "451ad37a1950_add_missing_indexes.py",  # article.authorName
    "c2a1b2c3d4e5_align_legacy_sql.py",  # article.type / content、comments.authorName/content
]


def _load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_helper():
    return _load(HELPER_PATH, "index_helpers")


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows

    def scalar(self):
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

    helper = _load_helper()
    conn = FakeConnection("mysql", rows=[("authorName", "text")])
    result = helper.mysql_index_columns(conn, "article", ["authorName"])
    assert len(result) == 1
    assert isinstance(result[0], sa.TextClause), "前缀必须用 sa.text()，否则被当列名"
    assert str(result[0]) == "authorName(100)"


def test_mysql_varchar_column_left_alone():
    helper = _load_helper()
    conn = FakeConnection("mysql", rows=[("authorName", "varchar")])
    assert helper.mysql_index_columns(conn, "article", ["authorName"]) == ["authorName"]


def test_mysql_mixed_columns():
    helper = _load_helper()
    conn = FakeConnection("mysql", rows=[("type", "TEXT"), ("created_at", "date")])
    result = helper.mysql_index_columns(conn, "article", ["type", "created_at"])
    assert str(result[0]) == "type(100)"
    assert result[1] == "created_at"


@pytest.mark.parametrize("col_type", ["tinytext", "mediumtext", "longtext", "blob"])
def test_all_text_and_blob_families_get_prefix(col_type):
    helper = _load_helper()
    conn = FakeConnection("mysql", rows=[("c", col_type)])
    result = helper.mysql_index_columns(conn, "t", ["c"])
    assert str(result[0]) == f"c({helper.PREFIX_LENGTH})"


def test_sqlite_is_untouched():
    """SQLite 支持对 TEXT 直接建索引，不应加前缀，也不该发起 information_schema 查询。"""
    helper = _load_helper()
    conn = FakeConnection("sqlite", rows=[("authorName", "TEXT")])
    assert helper.mysql_index_columns(conn, "article", ["authorName"]) == ["authorName"]
    assert conn.statements == []


def test_query_failure_degrades_gracefully():
    """查询失败时退回原列名，不能让整条迁移炸掉。"""

    class Boom(FakeConnection):
        def execute(self, statement, params=None):
            raise RuntimeError("no such table")

    helper = _load_helper()
    conn = Boom("mysql")
    assert helper.mysql_index_columns(conn, "article", ["authorName"]) == ["authorName"]


def test_unknown_column_left_alone():
    """information_schema 里没有的列不应被加前缀（避免造出坏 SQL）。"""
    helper = _load_helper()
    conn = FakeConnection("mysql", rows=[("other", "TEXT")])
    assert helper.mysql_index_columns(conn, "article", ["authorName"]) == ["authorName"]


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
    helper = _load_helper()
    assert helper.PREFIX_LENGTH == 100


@pytest.mark.parametrize("migration", TEXT_INDEXING_MIGRATIONS)
def test_migration_uses_shared_helper(migration):
    """钉死：这些迁移必须经由共享 helper 建索引，不能各自裸调 op.create_index。

    CI 曾在两个迁移上先后撞到 1170（article.authorName、article.type），
    说明这个坑会重复踩；本用例防止将来新增/修改迁移时又绕开 helper。
    """
    path = os.path.join(ALEMBIC_DIR, "versions", migration)
    with open(path, encoding="utf-8") as handle:
        source = handle.read()
    assert "mysql_index_columns" in source, f"{migration} 应使用共享 helper"
    # 不能直接把 columns 原样传给 create_index
    assert "op.create_index(index_name, table_name, columns)" not in source, (
        f"{migration} 仍把 TEXT 列裸传给 create_index，会在 MySQL 上报 1170"
    )
