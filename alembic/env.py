import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# 将项目 src 目录加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.settings import Config  # noqa: E402
from database import Base  # noqa: E402
from models import *  # noqa: E402,F403  确保所有 ORM 模型被加载到 Base.metadata

# Alembic Config 对象
config = context.config

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标 metadata
# 自动迁移时 Alembic 会比较 Base.metadata 与数据库实际结构
target_metadata = Base.metadata

# 从项目配置读取数据库 URL
def get_url():
    return Config.get_database_url()


def run_migrations_offline() -> None:
    """离线模式（生成 SQL 脚本）。"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式（直接操作数据库）。"""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
