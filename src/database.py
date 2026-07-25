import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

from config.settings import Config

logger = logging.getLogger(__name__)

engine = create_engine(
    Config.get_database_url(),
    pool_size=Config.DB_POOL_SIZE,
    max_overflow=20,
    pool_recycle=Config.DB_POOL_RECYCLE,
    pool_pre_ping=True,
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


# comments 表新增列（P1.2 双写补齐）。create_all 不会 ALTER 已有表，
# 因此需要显式幂等升级。DB 列名与 spiderComments.py 的 CSV header 一致。
_COMMENTS_NEW_COLUMNS = [
    ("comment_id", "VARCHAR(64)"),
    ("user_id", "VARCHAR(64)"),
    ("reply_count", "BIGINT"),
    ("comment_source", "VARCHAR(100)"),
    ("is_hot", "TINYINT(1)"),
    ("parent_id", "VARCHAR(64)"),
    ("reply_to_user", "VARCHAR(100)"),
    ("verified_type", "INT"),
    ("followers_count", "BIGINT"),
]
_comments_columns_ensured = False


def ensure_comments_columns() -> None:
    """幂等补齐 comments 表的新增列。

    首次调用检查 ``information_schema`` 并 ALTER 缺失列；之后进程内不再重复。
    任何异常都只记日志、不抛出——DB 写入失败时 spider 退化为仅写 CSV，
    不会因 schema 问题中断主流程。
    """
    global _comments_columns_ensured
    if _comments_columns_ensured:
        return

    try:
        # 确保 Comment 模型已注册到 metadata（惰性导入避免循环依赖）
        import models.comment  # noqa: F401

        with engine.connect() as conn:
            table_exists = conn.execute(
                text(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema = DATABASE() AND table_name = 'comments'"
                )
            ).fetchone()

            if not table_exists:
                # 表不存在：create_all 会按当前模型（含全部列）创建
                logger.info("comments 表不存在，调用 create_all 建表")
                Base.metadata.create_all(bind=engine, tables=[models.comment.Comment.__table__])
            else:
                for col_name, col_type in _COMMENTS_NEW_COLUMNS:
                    exists = conn.execute(
                        text(
                            "SELECT 1 FROM information_schema.columns "
                            "WHERE table_schema = DATABASE() "
                            "AND table_name = 'comments' AND column_name = :col"
                        ),
                        {"col": col_name},
                    ).fetchone()
                    if not exists:
                        conn.execute(
                            text(
                                f"ALTER TABLE comments ADD COLUMN {col_name} {col_type}"
                            )
                        )
                        conn.commit()
                        logger.info("comments 表新增列: %s", col_name)

        _comments_columns_ensured = True
    except Exception as e:
        # 不置 flag，下次调用会重试
        logger.warning("comments 表列升级失败（DB 写入将退化为仅 CSV）: %s", e)
