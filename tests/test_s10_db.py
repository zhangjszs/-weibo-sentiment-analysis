"""S10: 验证统一后的数据访问层"""

import inspect


def test_query_dataframe_uses_engine():
    """query_dataframe 应使用 SQLAlchemy engine，不依赖 pymysql"""
    # 确保没有 DatabasePool 类
    import utils.query as q

    assert not hasattr(q, "DatabasePool"), "DatabasePool 应已删除"
    assert not hasattr(q, "db_pool"), "db_pool 应已删除"
    assert not hasattr(q, "_backup_connection"), "_backup_connection 应已删除"
    assert hasattr(q, "engine"), "engine 应存在"
    assert hasattr(q, "db_session"), "db_session 应存在"


def test_querys_function_exists():
    """querys() 函数签名保持不变"""
    from utils.query import querys

    sig = inspect.signature(querys)
    params = list(sig.parameters.keys())
    assert "sql" in params
    assert "params" in params
