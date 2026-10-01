"""Rename user.createTime to create_time

收 #16 留白：user 表其余列均为 snake_case（is_admin/nickname/email/bio/
avatar_color），仅 createTime 是 camelCase，迫使 ORM 写显式列名映射、
裸 SQL 写 ``AS`` 别名。本迁移将列改名为 create_time，命名对齐。

幂等性（沿用 b2d5a3f9c0e1 的 inspector 风格，跨 MySQL/SQLite 通用）：

- 全新库由新版 init_database.sql 建表（已是 create_time）→ 跳过；
- 旧部署库（列名仍为 createTime）→ 真改名；
- 表不存在（空库跑迁移链）→ 跳过。

MySQL 8.0 与 SQLite 3.25+ 均支持 ``ALTER TABLE ... RENAME COLUMN``
（compose 即 mysql:8.0）。

Revision ID: f6a7b8c9d0e1
Revises: c2a1b2c3d4e5
Create Date: 2026-10-01 16:40:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f6a7b8c9d0e1"
down_revision = "c2a1b2c3d4e5"
branch_labels = None
depends_on = None


def _user_columns() -> set:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    try:
        return {c["name"] for c in insp.get_columns("user")}
    except Exception:
        # 表不存在（空库）等情况：返回空集，由调用方跳过
        return set()


def upgrade() -> None:
    cols = _user_columns()
    if "createTime" in cols and "create_time" not in cols:
        op.alter_column("user", "createTime", new_column_name="create_time")


def downgrade() -> None:
    cols = _user_columns()
    if "create_time" in cols and "createTime" not in cols:
        op.alter_column("user", "create_time", new_column_name="createTime")
