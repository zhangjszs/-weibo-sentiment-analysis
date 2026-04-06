from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask import g, jsonify


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def ok(data: Any = None, msg: str = "success", code: int = 200):
    payload: dict[str, Any] = {"code": code, "msg": msg, "timestamp": _timestamp()}
    request_id = getattr(g, "request_id", None)
    if request_id:
        payload["request_id"] = request_id
    if data is not None:
        payload["data"] = data
    return jsonify(payload)


def error(msg: str = "error", code: int = 500, data: Any = None):
    payload: dict[str, Any] = {"code": code, "msg": msg, "timestamp": _timestamp()}
    request_id = getattr(g, "request_id", None)
    if request_id:
        payload["request_id"] = request_id
    if data is not None:
        payload["data"] = data
    return jsonify(payload)
