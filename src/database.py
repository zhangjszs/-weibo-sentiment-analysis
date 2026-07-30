import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

from config.settings import Config

logger = logging.getLogger(__name__)

engine = create_engine(
    Config.get_database_url(),
    pool_size=Config.DB_POOL_SIZE,
    max_overflow=20,
    pool_recycle=Config.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    # MySQL 不可用时避免连接无限阻塞（评估 P0 #9）：5s 超时
    connect_args={"connect_timeout": 5},
)

db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


# SQLAlchemy 2.0 风格：用 DeclarativeBase 替代 declarative_base()
# 不再挂 Base.query（query_property 为 1.x 遗留，2.0 推荐显式 session 查询）
class Base(DeclarativeBase):
    pass


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    Base.metadata.create_all(bind=engine)


# P0 #4：comments 表 schema 此前由 ensure_comments_columns() 运行时 ALTER 补齐，
# 属临时 hack。现已改由 Alembic 迁移 a1c4f2e8b9d0 + init_database.sql 统一管理，
# 该函数及相关状态已移除。create_all 仍用于全新部署建表，但生产 schema 应以
# alembic upgrade head 为准。
