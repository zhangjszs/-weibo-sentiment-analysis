"""迁移期共用的 DDL 小工具。

MySQL 不允许对 TEXT/BLOB 列直接建索引，必须给前缀长度，否则报
``1170 BLOB/TEXT column used in key specification without a key length``。
本仓库的 schema 存在「双真相」：ORM（``src/models/*.py``）多把字段声明成
``String(n)``，而冻结 SQL（``docs/database/init_database.sql``）声明成
``text``/``mediumtext``（见 issue #27）。迁移按列名建索引时，落到 TEXT 列上
就会触发 1170。

``mysql_index_columns()`` 让各迁移在调用 ``op.create_index`` 前把 TEXT/BLOB
列换成带前缀长度的表达式，使两种 schema 下都能建成索引。
"""

from __future__ import annotations

import sqlalchemy as sa

TEXT_TYPES = frozenset(
    {
        "TINYTEXT",
        "TEXT",
        "MEDIUMTEXT",
        "LONGTEXT",
        "TINYBLOB",
        "BLOB",
        "MEDIUMBLOB",
        "LONGBLOB",
    }
)

PREFIX_LENGTH = 100


def _text_column_types(conn, table_name: str) -> dict[str, str]:
    """返回 ``{列名大写: DATA_TYPE}``；查询失败时返回空字典（调用方按不加前缀处理）。"""
    try:
        rows = conn.execute(
            sa.text(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name = :table_name
                """
            ),
            {"table_name": table_name},
        ).fetchall()
    except Exception:
        return {}
    return {str(row[0]).upper(): str(row[1]).upper() for row in rows}


def mysql_index_columns(conn, table_name: str, columns: list[str]) -> list:
    """MySQL 上把 TEXT/BLOB 列换成 ``col(100)`` 前缀表达式；其他方言原样返回。

    两条容易踩的细节：

    1. 前缀必须用 ``sa.text("col(100)")``，不能用字符串 ``"col(100)"``。
       alembic 的 ``util.sqla_compat._textual_index_column`` 收到普通 str 会
       把它当成**列名**建出 ``Column("col(100)")``，渲染成 `` `col(100)` ``，
       MySQL 视为带引号的列名，照样报 1170；只有 TextClause 才会被原样渲染
       成前缀表达式。
    2. 列类型查 ``information_schema.columns.DATA_TYPE``，不要用
       ``inspect().get_columns()`` 里 ``str(col["type"])``——不同驱动对类型
       的字符串化结果不一致，实测在 MySQL 上会漏判 TEXT。
    """
    if conn.dialect.name != "mysql":
        return list(columns)

    data_types = _text_column_types(conn, table_name)
    if not data_types:
        return list(columns)

    result = []
    for column in columns:
        if data_types.get(column.upper(), "") in TEXT_TYPES:
            result.append(sa.text(f"{column}({PREFIX_LENGTH})"))
        else:
            result.append(column)
    return result
