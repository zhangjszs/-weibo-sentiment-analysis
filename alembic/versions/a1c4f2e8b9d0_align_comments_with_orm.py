"""Align comments table with ORM model

对齐 comments 表与 ORM（src/models/comment.py）：

1. comment_id 由 ``INT AUTO_INCREMENT PRIMARY KEY`` 改为 ``VARCHAR(64) PRIMARY KEY``，
   以存储微博评论真实 ID（此前 AUTO_INCREMENT 会覆盖 spider 传入的微博 ID，导致
   comment_id 实际丢失、无法在 DB 层去重）。
   - 现有 int 数据安全转换为字符串（"1","2",...），微博 ID 为大数字字符串，无碰撞。
   - spiderComments.py 的 IntegrityError 兜底此前期望 (articleId, created_at) 复合
     PK 冲突，但 DB 无此约束 → 改为 comment_id PK 后，重爬同一评论可正确触发冲突。

2. 幂等补齐 P1.2 双写引入的 8 个列（user_id/reply_count/comment_source/is_hot/
   parent_id/reply_to_user/verified_type/followers_count）。此前由 database.py
   的 ensure_comments_columns() 运行时 ALTER 补齐——属临时 hack，本迁移落地后
   该 hack 移除，schema 改由 Alembic 单一管理。

幂等性：对已由 ensure_comments_columns() 补过列的开发库，或已由新版 init_database.sql
建表的全新库，均安全（先查 information_schema 再决定是否 ALTER）。

Revision ID: a1c4f2e8b9d0
Revises: 451ad37a1950
Create Date: 2026-07-30 16:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a1c4f2e8b9d0"
down_revision = "451ad37a1950"
branch_labels = None
depends_on = None


# (列名, DDL 类型) —— 与 src/database.py 旧 _COMMENTS_NEW_COLUMNS 一致，
# 与 src/models/comment.py 的 Column 类型对齐。
_NEW_COLUMNS = [
    ("user_id", "VARCHAR(64)"),
    ("reply_count", "BIGINT"),
    ("comment_source", "VARCHAR(100)"),
    ("is_hot", "TINYINT(1)"),
    ("parent_id", "VARCHAR(64)"),
    ("reply_to_user", "VARCHAR(100)"),
    ("verified_type", "INT"),
    ("followers_count", "BIGINT"),
]


def _get_column_type(table_name: str, column_name: str) -> str:
    """返回列的 DATA_TYPE（小写，如 'int'/'varchar'），不存在则返回空串。"""
    conn = op.get_bind()
    return conn.execute(
        sa.text(
            """
            SELECT DATA_TYPE FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = :table_name
              AND column_name = :column_name
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    ).scalar() or ""


def _column_exists(table_name: str, column_name: str) -> bool:
    return bool(_get_column_type(table_name, column_name))


def _convert_comment_id_to_varchar_pk() -> None:
    """将 comment_id 从 INT AUTO_INCREMENT PK 转为 VARCHAR(64) PK。

    MySQL 要求 AUTO_INCREMENT 列必须是键的一部分，故顺序：
      1. MODIFY 去掉 AUTO_INCREMENT 属性（保留 INT + NOT NULL + PK）
      2. DROP PRIMARY KEY
      3. MODIFY 改类型为 VARCHAR(64) NOT NULL
      4. ADD PRIMARY KEY
    """
    conn = op.get_bind()
    current_type = _get_column_type("comments", "comment_id")

    if current_type == "varchar":
        # 已是 VARCHAR（全新库或已迁移），跳过
        return

    if current_type != "int":
        # 未知类型，保守跳过，避免误伤
        print(
            f"[skip] comments.comment_id 类型为 {current_type!r}，"
            f"非 int/varchar，跳过 PK 类型转换，请人工核对"
        )
        return

    # 1. 去 AUTO_INCREMENT（保留 INT NOT NULL）
    conn.execute(sa.text("ALTER TABLE comments MODIFY COLUMN comment_id INT NOT NULL"))
    # 2. 删主键
    conn.execute(sa.text("ALTER TABLE comments DROP PRIMARY KEY"))
    # 3. 改类型为 VARCHAR(64)
    conn.execute(sa.text("ALTER TABLE comments MODIFY COLUMN comment_id VARCHAR(64) NOT NULL"))
    # 4. 重建主键
    conn.execute(sa.text("ALTER TABLE comments ADD PRIMARY KEY (comment_id)"))


def upgrade() -> None:
    # 1. comment_id PK 类型对齐（INT AUTO_INCREMENT → VARCHAR(64)）
    _convert_comment_id_to_varchar_pk()

    # 2. 幂等补齐 8 个双写列
    conn = op.get_bind()
    for col_name, col_type in _NEW_COLUMNS:
        if _column_exists("comments", col_name):
            continue
        conn.execute(
            sa.text(f"ALTER TABLE comments ADD COLUMN {col_name} {col_type}")
        )


def downgrade() -> None:
    """反向迁移（best-effort）。

    注意：comment_id 由 VARCHAR 回退为 INT AUTO_INCREMENT 时，若库中已存在
    非数字字符串的微博 ID，转换会失败。生产环境慎用 downgrade，建议前向修复。
    """
    conn = op.get_bind()

    # 1. 删除 8 个双写列（如存在）
    for col_name, _ in _NEW_COLUMNS:
        if _column_exists("comments", col_name):
            conn.execute(sa.text(f"ALTER TABLE comments DROP COLUMN {col_name}"))

    # 2. comment_id 回退为 INT AUTO_INCREMENT PK（仅当当前为 varchar 且值可转 int）
    if _get_column_type("comments", "comment_id") == "varchar":
        try:
            conn.execute(sa.text("ALTER TABLE comments DROP PRIMARY KEY"))
            conn.execute(
                sa.text("ALTER TABLE comments MODIFY COLUMN comment_id INT NOT NULL AUTO_INCREMENT")
            )
            conn.execute(sa.text("ALTER TABLE comments ADD PRIMARY KEY (comment_id)"))
        except Exception as e:
            # 回退失败（存在非数字 ID）：保留 VARCHAR，仅打印警告
            print(f"[warn] comment_id 回退 INT 失败，保留 VARCHAR(64): {e}")
