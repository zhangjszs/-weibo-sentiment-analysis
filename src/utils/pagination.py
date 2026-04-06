"""
分页工具模块
提供统一的分页参数处理功能
"""

from typing import Tuple


def get_pagination_params(
    request, default_limit: int = 10, max_limit: int = 100
) -> Tuple[int, int, int]:
    """
    从请求中获取分页参数

    Args:
        request: Flask request 对象
        default_limit: 默认每页数量
        max_limit: 最大每页数量

    Returns:
        Tuple[int, int, int]: (page, limit, offset)
    """
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        limit = min(max(1, int(request.args.get("limit", default_limit))), max_limit)
    except (ValueError, TypeError):
        limit = default_limit

    offset = (page - 1) * limit

    return page, limit, offset


def get_pagination_response(total: int, page: int, limit: int, items: list) -> dict:
    """
    生成分页响应数据

    Args:
        total: 总数量
        page: 当前页
        limit: 每页数量
        items: 数据列表

    Returns:
        dict: 分页响应字典
    """
    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    return {
        "items": items,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }


__all__ = ["get_pagination_params", "get_pagination_response"]
