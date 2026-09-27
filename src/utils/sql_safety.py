"""SQL 安全小工具：LIKE 转义与原生 SQL 标识符白名单。"""

from __future__ import annotations


def escape_like(value: object) -> str:
    """转义 LIKE 通配符（``%``、``_`` 及转义符自身）。

    配合 ``column.like(pattern, escape="\\\\")`` 使用，防止用户输入中的
    通配符扩大匹配范围（LIKE 通配符注入）。

    Args:
        value: 用户输入的匹配片段。

    Returns:
        转义后的字符串（不含两侧 ``%``，由调用方拼接）。
    """
    if value is None:
        return ""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def validate_identifier(value: str, allowed: set[str], *, kind: str = "column") -> str:
    """校验原生 SQL 中的标识符（列名等）是否在白名单内。

    Raises:
        ValueError: 不在白名单时抛出（调用方应转为 400，而非拼入 SQL）。
    """
    if value not in allowed:
        raise ValueError(f"非法的{kind}参数: {value!r}")
    return value


def coerce_positive_int(value: object, default: int, *, maximum: int) -> int:
    """将分桶等数值参数收敛为有界正整数（防 f-string 注入/异常大内存）。"""
    try:
        number = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return max(1, min(number, maximum))
