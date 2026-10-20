#!/usr/bin/env python3
"""
日期时间工具模块

提供统一的 naive UTC 时间获取方法，替代已弃用的 datetime.utcnow()。
保持向后兼容及方言中立的数据库列默认值与时间计算语义。
"""

from datetime import UTC, datetime


def utcnow_naive() -> datetime:
    """返回当前时间的 naive UTC datetime 对象（无时区信息）。

    等价于已弃用的 datetime.utcnow()，但遵循 Python 3.12+ 推荐实践：
    通过 datetime.now(UTC).replace(tzinfo=None) 构造。
    可用作 SQLAlchemy Column(DateTime, default=utcnow_naive) 的默认值回调。
    """
    return datetime.now(UTC).replace(tzinfo=None)


__all__ = ["utcnow_naive"]
