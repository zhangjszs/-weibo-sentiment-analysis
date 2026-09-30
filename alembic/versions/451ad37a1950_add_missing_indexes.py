"""Add missing indexes

补充 init_database.sql 中未包含的常用查询索引：
- article: authorName, commentsLen, created_at+likeNum 复合索引
- comments: like_counts, articleId+created_at 复合索引

Revision ID: 451ad37a1950
Revises: 74a896d7d53e
Create Date: 2026-04-26 16:05:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "451ad37a1950"
down_revision = "74a896d7d53e"
branch_labels = None
depends_on = None


def _index_exists(conn, table_name: str, index_name: str) -> bool:
    insp = sa.inspect(conn)
    try:
        indexes = insp.get_indexes(table_name)
    except Exception:
        return False
    return any(idx.get("name") == index_name for idx in indexes)


def _table_exists(conn, table_name: str) -> bool:
    insp = sa.inspect(conn)
    try:
        return insp.has_table(table_name)
    except Exception:
        return False


def _create_index_if_not_exists(index_name: str, table_name: str, columns: list[str]) -> None:
    """仅在索引不存在时创建（兼容 MySQL 与 SQLite）。"""
    conn = op.get_bind()
    # 若表不存在则跳过（空库由后续 align 迁移通过 Base.metadata.create_all 补齐）
    if not _table_exists(conn, table_name):
        return
    if _index_exists(conn, table_name, index_name):
        return
    # MySQL 上 information_schema 仍可用作双重检查（可选）
    if conn.dialect.name == "mysql":
        try:
            result = conn.execute(
                sa.text(
                    """
                    SELECT COUNT(*) FROM information_schema.statistics
                    WHERE table_schema = DATABASE()
                      AND table_name = :table_name
                      AND index_name = :index_name
                    """
                ),
                {"table_name": table_name, "index_name": index_name},
            ).scalar()
            if result and result != 0:
                return
        except Exception:
            pass
    op.create_index(index_name, table_name, _with_mysql_prefix_length(conn, table_name, columns))


# MySQL 不允许对 TEXT/BLOB 列直接建索引，必须给前缀长度，否则报 1170
# "BLOB/TEXT column used in key specification without a key length"。
# ORM（src/models/article.py）把 authorName 声明为 String(100)，而冻结 SQL
# （docs/database/init_database.sql）声明为 text —— schema 双真相，见 #27。
# 此处按实际列类型决定是否加前缀，使两种 schema 下都能建成索引。
_TEXT_TYPES = {"TEXT", "TINYTEXT", "MEDIUMTEXT", "LONGTEXT", "BLOB", "TINYBLOB", "MEDIUMBLOB", "LONGBLOB"}
_PREFIX_LENGTH = 100


def _with_mysql_prefix_length(conn, table_name: str, columns: list[str]) -> list:
    """MySQL 上把 TEXT/BLOB 列换成 ``col(100)`` 前缀形式；其他方言原样返回。

    注意必须用 ``sa.text("col(100)")`` 而不是字符串 ``"col(100)"``：
    alembic 的 ``_textual_index_column`` 收到普通 str 时会把它当成**列名**
    建成 ``Column("authorName(100)")``，渲染出 `` `authorName(100)` ``，
    MySQL 会当成一个带引号的列名而非前缀索引；只有 TextClause 才会被
    原样渲染成 ``authorName(100)``。

    列类型直接查 information_schema：不同 dialect / 驱动对
    ``inspect().get_columns()`` 里 ``type`` 的字符串化结果不一致
    （实测 MySQL 上按 ``str(type)`` 判断会漏掉 TEXT 列，导致前缀没加上、
    仍报 1170），而 DATA_TYPE 是权威且稳定的。
    """
    if conn.dialect.name != "mysql":
        return list(columns)

    data_types: dict[str, str] = {}
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
        data_types = {str(r[0]).upper(): str(r[1]).upper() for r in rows}
    except Exception:
        return list(columns)

    result = []
    for column in columns:
        if data_types.get(column.upper(), "") in _TEXT_TYPES:
            result.append(sa.text(f"{column}({_PREFIX_LENGTH})"))
        else:
            result.append(column)
    return result


def upgrade() -> None:
    # article 表
    _create_index_if_not_exists("idx_author_name", "article", ["authorName"])
    _create_index_if_not_exists("idx_comments_len", "article", ["commentsLen"])
    _create_index_if_not_exists("idx_created_likes", "article", ["created_at", "likeNum"])

    # comments 表
    _create_index_if_not_exists("idx_like_counts", "comments", ["like_counts"])
    _create_index_if_not_exists("idx_article_created", "comments", ["articleId", "created_at"])


def _drop_index_if_exists(index_name: str, table_name: str) -> None:
    conn = op.get_bind()
    if not _table_exists(conn, table_name):
        return
    if not _index_exists(conn, table_name, index_name):
        return
    try:
        op.drop_index(index_name, table_name=table_name)
    except Exception:
        pass


def downgrade() -> None:
    _drop_index_if_exists("idx_article_created", "comments")
    _drop_index_if_exists("idx_like_counts", "comments")
    _drop_index_if_exists("idx_created_likes", "article")
    _drop_index_if_exists("idx_comments_len", "article")
    _drop_index_if_exists("idx_author_name", "article")
