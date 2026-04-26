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


def _create_index_if_not_exists(index_name: str, table_name: str, columns: list[str]) -> None:
    """仅在索引不存在时创建（兼容 MySQL）。"""
    conn = op.get_bind()
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
    if result == 0:
        op.create_index(index_name, table_name, columns)


def upgrade() -> None:
    # article 表
    _create_index_if_not_exists("idx_author_name", "article", ["authorName"])
    _create_index_if_not_exists("idx_comments_len", "article", ["commentsLen"])
    _create_index_if_not_exists("idx_created_likes", "article", ["created_at", "likeNum"])

    # comments 表
    _create_index_if_not_exists("idx_like_counts", "comments", ["like_counts"])
    _create_index_if_not_exists("idx_article_created", "comments", ["articleId", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_article_created", table_name="comments")
    op.drop_index("idx_like_counts", table_name="comments")
    op.drop_index("idx_created_likes", table_name="article")
    op.drop_index("idx_comments_len", table_name="article")
    op.drop_index("idx_author_name", table_name="article")
