"""请求输入校验共享工具（#11）：统一空 body→400、数值越界收敛、字符串截断。

各视图应使用本模块代替裸 ``request.json`` / ``int(...)`` / ``type=int``，
保证非法输入返回 400 JSON 而非 500/HTML。
"""

from __future__ import annotations

import html
import re
from typing import Any

from flask import request

from utils.api_response import error

ARTICLE_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


def get_json_body() -> dict:
    """静默解析 JSON body；缺失/非法/非 dict 时返回 ``{}``（不抛 500/HTML）。"""
    try:
        data = request.get_json(silent=True)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def require_json_body() -> tuple[dict, tuple | None]:
    """要求非空 JSON dict；失败返回 ``({}, (error400, 400))``。"""
    data = get_json_body()
    if not data:
        return {}, (error("请求体不能为空且必须为 JSON 对象", code=400), 400)
    return data, None


def get_int_arg(
    name: str, default: int, *, min_value: int = 1, max_value: int = 500
) -> int:
    """安全读取 query/form 整型参数，永不返回 None（非法→default，再钳制范围）。"""
    raw = request.args.get(name, None)
    if raw is None and request.form:
        raw = request.form.get(name, None)
    try:
        value = int(raw) if raw is not None else default
    except (TypeError, ValueError):
        value = default
    return max(min_value, min(value, max_value))


def get_bounded_str(value: Any, *, max_length: int, default: str = "") -> str:
    """将任意输入收敛为限长字符串（非标量→default，超长截断，去首尾空白）。"""
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return default
    text = str(value).strip()
    return text[:max_length] if len(text) > max_length else text


def sanitize_text(value: Any, *, max_length: int) -> str:
    """限长 + HTML 转义（用于回显到前端的消息/标题/昵称等，防存储型 XSS）。"""
    return html.escape(get_bounded_str(value, max_length=max_length), quote=True)


def is_valid_article_id(value: Any) -> bool:
    """article_id 长度/字符集校验（限 64 字符内字母数字/_/-）。"""
    return isinstance(value, str) and bool(ARTICLE_ID_RE.match(value))
