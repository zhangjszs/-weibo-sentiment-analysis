"""Create alert and alert_rules tables

P0 #5：预警数据持久化。新建两张表（与 ORM ``models/alert.py`` 对齐）：

- ``alert_rules``：预警规则（此前硬编码于 ``AlertRuleEngine._init_default_rules``，
  内存态、重启即丢、不可多 worker 共享）。
- ``alerts``：预警消息，兼作历史（``AlertHistory`` 已合并入此表，补 ``notes`` 列；
  ``alert_history_service.py`` 死代码已移除）。

幂等性：全新库可能已由新版 init_database.sql 建表，故先查 information_schema
再 create_table，避免 "Table already exists" 冲突（沿用 451ad37a1950 的幂等风格）。

Revision ID: b2d5a3f9c0e1
Revises: a1c4f2e8b9d0
Create Date: 2026-07-30 17:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b2d5a3f9c0e1"
down_revision = "a1c4f2e8b9d0"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        insp = sa.inspect(conn)
        try:
            return insp.has_table(table_name)
        except Exception:
            return False
    return bool(
        conn.execute(
            sa.text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = DATABASE() AND table_name = :t"
            ),
            {"t": table_name},
        ).scalar()
    )


def _create_alert_rules() -> None:
    if _table_exists("alert_rules"):
        return
    op.create_table(
        "alert_rules",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        # 枚举存 VARCHAR（与 ORM native_enum=False 一致），不建 MySQL ENUM 类型
        sa.Column("alert_type", sa.String(32), nullable=False),
        sa.Column("level", sa.String(16), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("priority", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("thresholds", sa.JSON, nullable=True),
        sa.Column("conditions", sa.JSON, nullable=True),
        sa.Column("cooldown_minutes", sa.Integer, nullable=False, server_default=sa.text("30")),
        sa.Column("max_alerts_per_hour", sa.Integer, nullable=False, server_default=sa.text("10")),
        sa.Column("notification_channels", sa.JSON, nullable=True),
        sa.Column("last_triggered", sa.DateTime, nullable=True),
        sa.Column("trigger_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("idx_alert_rules_enabled", "alert_rules", ["enabled"])
    op.create_index("idx_alert_rules_priority", "alert_rules", ["priority"])


def _create_alerts() -> None:
    if _table_exists("alerts"):
        return
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rule_id", sa.String(64), nullable=True),
        sa.Column("rule_name", sa.String(200), nullable=True),
        sa.Column("alert_type", sa.String(32), nullable=True),
        sa.Column("level", sa.String(16), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("data", sa.JSON, nullable=True),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("is_handled", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("handler", sa.String(255), nullable=True),
        sa.Column("handled_at", sa.DateTime, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    # 查询模式：历史列表 created_at desc、未读过滤、按 level / rule_id 过滤
    op.create_index("idx_alerts_created_at", "alerts", ["created_at"])
    op.create_index("idx_alerts_is_read", "alerts", ["is_read"])
    op.create_index("idx_alerts_level", "alerts", ["level"])
    op.create_index("idx_alerts_rule_id", "alerts", ["rule_id"])


def upgrade() -> None:
    _create_alert_rules()
    _create_alerts()


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("alert_rules")
