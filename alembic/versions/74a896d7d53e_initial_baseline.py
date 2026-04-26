"""Initial baseline

数据库 schema 已由 database/init_database.sql 初始化。
当前 ORM 模型（src/models/）仅覆盖 article、comments、user 三张核心表，
与 init_database.sql 中的完整 schema 存在差异（如缺少 is_admin、comment_id 等字段）。
后续迁移将逐步对齐 ORM 与数据库 schema。

Revision ID: 74a896d7d53e
Revises:
Create Date: 2026-04-26 16:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "74a896d7d53e"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Baseline：数据库已由 init_database.sql 初始化，此处不执行 DDL。"""
    pass


def downgrade() -> None:
    """Baseline 无 downgrade 操作。"""
    pass
