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
    op.create_index(index_name, table_name, columns)


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
