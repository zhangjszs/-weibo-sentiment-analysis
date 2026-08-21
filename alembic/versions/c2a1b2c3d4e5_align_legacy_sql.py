"""align_legacy_sql

归档 docs/database/*.sql 与现行 Base.metadata 的对齐迁移。
幂等：仅在索引/表不存在时创建，兼容 MySQL 与 SQLite。

Revision ID: c2a1b2c3d4e5
Revises: b2d5a3f9c0e1
Create Date: 2026-08-21 23:30:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c2a1b2c3d4e5"
down_revision = "b2d5a3f9c0e1"
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
    conn = op.get_bind()
    if not _table_exists(conn, table_name):
        return
    if _index_exists(conn, table_name, index_name):
        return
    # MySQL content prefix index (255) 仅 MySQL 生效，SQLite 用全列
    if conn.dialect.name != "mysql" and index_name in ("idx_article_content", "idx_comments_content"):
        return
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
    # 来自 docs/database/database_indexes.sql 的剩余索引（451 已覆盖部分）
    _create_index_if_not_exists("idx_article_created_at", "article", ["created_at"])
    _create_index_if_not_exists("idx_article_like_num", "article", ["likeNum"])
    _create_index_if_not_exists("idx_article_type", "article", ["type"])
    _create_index_if_not_exists("idx_article_content", "article", ["content"])
    _create_index_if_not_exists("idx_comments_created_at", "comments", ["created_at"])
    _create_index_if_not_exists("idx_comments_article_id", "comments", ["articleId"])
    _create_index_if_not_exists("idx_comments_content", "comments", ["content"])
    _create_index_if_not_exists("idx_comments_author_name", "comments", ["authorName"])
    _create_index_if_not_exists("idx_article_type_created", "article", ["type", "created_at"])
    _create_index_if_not_exists("idx_comments_article_created_legacy", "comments", ["articleId", "created_at"])


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
    _drop_index_if_exists("idx_comments_article_created_legacy", "comments")
    _drop_index_if_exists("idx_article_type_created", "article")
    _drop_index_if_exists("idx_comments_author_name", "comments")
    _drop_index_if_exists("idx_comments_content", "comments")
    _drop_index_if_exists("idx_comments_article_id", "comments")
    _drop_index_if_exists("idx_comments_created_at", "comments")
    _drop_index_if_exists("idx_article_content", "article")
    _drop_index_if_exists("idx_article_type", "article")
    _drop_index_if_exists("idx_article_like_num", "article")
    _drop_index_if_exists("idx_article_created_at", "article")
