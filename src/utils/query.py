"""
数据库访问模块
唯一数据访问层：SQLAlchemy engine + scoped_session
"""

from __future__ import annotations

import logging
import time
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

from config.settings import Config

logger = logging.getLogger(__name__)

# ── 唯一连接池：SQLAlchemy engine ──────────────────────────────────────────
engine = create_engine(
    Config.get_database_url(),
    pool_size=Config.DB_POOL_SIZE,
    max_overflow=20,
    pool_recycle=Config.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    pool_timeout=Config.DB_POOL_TIMEOUT,
    echo=Config.IS_DEVELOPMENT,
)

db_session = scoped_session(sessionmaker(bind=engine))


# ── 兼容旧调用的查询函数 ───────────────────────────────────────────────────


def _build_named_params(sql: str, params: list) -> tuple[str, dict[str, Any]]:
    """
    将 `%s` 占位符转换为 SQLAlchemy 命名参数。

    例如：
        SELECT * FROM t WHERE a=%s AND b=%s
    转换为：
        SELECT * FROM t WHERE a=:p0 AND b=:p1
    """
    if not params:
        return sql, {}

    named_sql = sql
    named_params: dict[str, Any] = {}
    for idx, value in enumerate(params):
        param_name = f"p{idx}"
        named_sql = named_sql.replace("%s", f":{param_name}", 1)
        named_params[param_name] = value

    return named_sql, named_params


def querys(sql: str, params: list | None = None, type: str = "no_select") -> Any:
    """
    执行 SQL 语句，兼容旧调用签名。

    Args:
        sql: SQL 语句（支持 %s 占位符）
        params: 参数列表
        type: 'no_select' 表示写操作，其他值表示 SELECT

    Returns:
        SELECT 返回字典列表；写操作返回 '数据库语句执行成功'
    """
    if params is None:
        params = []

    start = time.time()
    named_sql, named_params = _build_named_params(sql, params)
    stmt = text(named_sql)

    query_type = (type or "").lower()
    is_select = query_type == "select"

    if is_select:
        with engine.connect() as conn:
            result = conn.execute(stmt, named_params)
            rows = [dict(row._mapping) for row in result]
        logger.debug(
            "查询完成: %d 条记录, 耗时 %.3fs", len(rows), time.time() - start
        )
        return rows

    # 非 select 类型统一按写操作处理（兼容 insert/update/delete/no_select）
    with engine.begin() as conn:
        result = conn.execute(stmt, named_params)

    logger.debug(
        "写操作完成: 影响 %d 行, 耗时 %.3fs",
        result.rowcount,
        time.time() - start,
    )
    return "数据库语句执行成功"


def query_dataframe(sql: str, params: list | None = None) -> pd.DataFrame:
    """
    执行查询并返回 pandas DataFrame。

    Args:
        sql: SQL 语句
        params: 参数列表

    Returns:
        DataFrame，失败时返回空 DataFrame
    """
    start = time.time()
    try:
        named_sql, named_params = _build_named_params(sql, params or [])
        df = pd.read_sql(text(named_sql), engine, params=named_params)
        logger.debug(
            "DataFrame 查询完成: %d 行, 耗时 %.3fs", len(df), time.time() - start
        )
        return df
    except Exception as e:
        logger.error("DataFrame 查询错误: %s", e, exc_info=True)
        return pd.DataFrame()


def get_database_stats() -> dict:
    """返回连接池状态（兼容旧调用）"""
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
    }
