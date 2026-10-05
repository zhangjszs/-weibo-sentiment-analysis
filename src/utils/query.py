"""
数据库访问模块
唯一数据访问层：复用 database.py 的 SQLAlchemy engine
"""

from __future__ import annotations

import logging
import time
from typing import Any

import pandas as pd
from sqlalchemy import text

from database import engine

logger = logging.getLogger(__name__)


def _build_named_params(sql: str, params: list) -> tuple[str, dict[str, Any]]:
    """
    将 `%s` 占位符转换为 SQLAlchemy 命名参数。

    例如：
        SELECT * FROM t WHERE a=%s AND b=%s
    转换为：
        SELECT * FROM t WHERE a=:p0 AND b=:p1

    安全校验（单遍扫描，正确处理转义引号/双引号标识符/字面量内 %s）：
        - 单引号字面量内的 `%s` 不计数、不替换（支持 ``\\'`` 转义与 ``''`` 转义）
        - 双引号标识符内的 `%s` 不计数、不替换
        - 字面量外的 `%%` 视为转义的百分号，原样保留、不计数
        - 字面量外的 `%s` 数量必须与参数列表长度一致，否则抛 ValueError
    """
    if not params:
        return sql, {}

    out: list[str] = []
    named_params: dict[str, Any] = {}
    param_index = 0
    i = 0
    n = len(sql)

    while i < n:
        ch = sql[i]
        # 单引号字符串字面量：原样透传，支持 \' 与 '' 转义
        if ch == "'":
            out.append(ch)
            i += 1
            while i < n:
                c = sql[i]
                out.append(c)
                if c == "\\" and i + 1 < n:
                    out.append(sql[i + 1])
                    i += 2
                    continue
                if c == "'":
                    if i + 1 < n and sql[i + 1] == "'":
                        out.append(sql[i + 1])
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            continue
        # 双引号标识符：原样透传
        if ch == '"':
            out.append(ch)
            i += 1
            while i < n:
                c = sql[i]
                out.append(c)
                if c == "\\" and i + 1 < n:
                    out.append(sql[i + 1])
                    i += 2
                    continue
                i += 1
                if c == '"':
                    break
            continue
        # 占位符 / 转义百分号（仅字面量外）
        if ch == "%" and i + 1 < n:
            nxt = sql[i + 1]
            if nxt == "s":
                if param_index >= len(params):
                    raise ValueError(
                        f"SQL 占位符数量不匹配：参数仅 {len(params)} 个，"
                        f"但在字符串字面量外发现更多 %s。"
                    )
                param_name = f"p{param_index}"
                out.append(f":{param_name}")
                named_params[param_name] = params[param_index]
                param_index += 1
                i += 2
                continue
            if nxt == "%":
                # 转义的百分号：原样保留，不计数
                out.append("%%")
                i += 2
                continue
        out.append(ch)
        i += 1

    if param_index != len(params):
        raise ValueError(
            f"SQL 占位符数量不匹配：期望 {len(params)} 个参数，"
            f"在字符串字面量外找到 {param_index} 个 %s。"
            f"请确保 LIKE 等子句中的 % 使用 %% 转义，且参数占位符与参数数量一致。"
        )

    return "".join(out), named_params


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
        DataFrame
    """
    start = time.time()
    named_sql, named_params = _build_named_params(sql, params or [])
    df = pd.read_sql(text(named_sql), engine, params=named_params)
    logger.debug(
        "DataFrame 查询完成: %d 行, 耗时 %.3fs", len(df), time.time() - start
    )
    return df


def get_database_stats() -> dict:
    """返回连接池状态（兼容旧调用）"""
    pool = engine.pool

    def _stat(attr: str):
        # QueuePool 的 size/checkedin 等是方法，StaticPool 等轻量池上同名属性
        # 直接是数值（health/details 在测试引擎上曾因此 500，#44）
        val = getattr(pool, attr, None)
        return val() if callable(val) else val

    return {
        "pool_size": _stat("size"),
        "checked_in": _stat("checkedin"),
        "checked_out": _stat("checkedout"),
        "overflow": _stat("overflow"),
    }
