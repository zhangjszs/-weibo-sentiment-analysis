"""S10: 验证统一后的数据访问层"""

import inspect

import pytest

pytestmark = pytest.mark.unit


def test_query_dataframe_uses_engine():
    """query_dataframe 应使用 SQLAlchemy engine，不依赖 pymysql"""
    # 确保没有 DatabasePool 类
    import utils.query as q

    assert not hasattr(q, "DatabasePool"), "DatabasePool 应已删除"
    assert not hasattr(q, "db_pool"), "db_pool 应已删除"
    assert not hasattr(q, "_backup_connection"), "_backup_connection 应已删除"
    # 复用 database.py 的 SQLAlchemy engine（不是 pymysql 旧连接池）。
    # 注意：不再断言 re-export 的 db_session —— query.py 只需 engine，
    # 保留未使用的 db_session 导入会触发 ruff F401，调用方一律从 database 取。
    # 也不断言 `q.engine is database.engine`：database.reset() 会在测试
    # teardown 重建 engine，而 query.py 在 import 期就已绑定，两者可以不同。
    from sqlalchemy.engine import Engine

    assert isinstance(q.engine, Engine), "engine 应为 SQLAlchemy Engine"
    assert not hasattr(q, "pymysql"), "不应直接依赖 pymysql"


def test_querys_function_exists():
    """querys() 函数签名保持不变"""
    from utils.query import querys

    sig = inspect.signature(querys)
    params = list(sig.parameters.keys())
    assert "sql" in params
    assert "params" in params
