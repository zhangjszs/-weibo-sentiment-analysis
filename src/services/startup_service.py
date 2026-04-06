#!/usr/bin/env python3
"""
启动阶段辅助服务
功能：开发环境管理员账号引导、核心接口预热
"""

from __future__ import annotations

import copy
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any

from config.settings import Config
from utils.jwt_handler import create_token
from utils.password_hasher import hash_password
from utils.query import querys

logger = logging.getLogger(__name__)

_STARTUP_STATE_LOCK = threading.Lock()
_STARTUP_STATE: dict[str, Any] = {
    "admin_bootstrap": {
        "enabled": False,
        "action": "not_run",
        "username": "",
        "timestamp": None,
    },
    "warmup": {
        "enabled": False,
        "running": False,
        "started_at": None,
        "finished_at": None,
        "duration_seconds": None,
        "paths_total": 0,
        "paths_done": 0,
        "results": [],
        "error": None,
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _set_admin_bootstrap_state(payload: dict[str, Any]) -> None:
    with _STARTUP_STATE_LOCK:
        _STARTUP_STATE["admin_bootstrap"] = {
            **payload,
            "timestamp": _now_iso(),
        }


def _warmup_start(paths_total: int) -> None:
    with _STARTUP_STATE_LOCK:
        _STARTUP_STATE["warmup"] = {
            "enabled": True,
            "running": True,
            "started_at": _now_iso(),
            "finished_at": None,
            "duration_seconds": None,
            "paths_total": paths_total,
            "paths_done": 0,
            "results": [],
            "error": None,
        }


def _warmup_record(path: str, status_code: int | None, duration: float, error_msg: str = ""):
    with _STARTUP_STATE_LOCK:
        warmup = _STARTUP_STATE["warmup"]
        warmup["paths_done"] = int(warmup.get("paths_done", 0)) + 1
        warmup["results"].append(
            {
                "path": path,
                "status_code": status_code,
                "duration_seconds": round(duration, 3),
                "error": error_msg or None,
            }
        )


def _warmup_finish(duration: float, error_msg: str = ""):
    with _STARTUP_STATE_LOCK:
        warmup = _STARTUP_STATE["warmup"]
        warmup["running"] = False
        warmup["finished_at"] = _now_iso()
        warmup["duration_seconds"] = round(duration, 3)
        warmup["error"] = error_msg or None


def get_startup_status() -> dict[str, Any]:
    """获取启动引导与预热状态快照。"""
    with _STARTUP_STATE_LOCK:
        return copy.deepcopy(_STARTUP_STATE)


def ensure_demo_admin() -> dict[str, Any]:
    """
    在开发环境确保演示管理员账号可用。

    行为：
    - 将 DEMO_ADMIN_USERNAME 注入 ADMIN_USERS
    - 用户不存在时自动创建
    - 用户存在但为非 bcrypt 密码时（可配置）重置为 DEMO_ADMIN_PASSWORD
    """
    result: dict[str, Any] = {
        "enabled": False,
        "action": "skipped",
        "username": "",
    }

    if not Config.IS_DEVELOPMENT or not Config.AUTO_CREATE_DEMO_ADMIN:
        _set_admin_bootstrap_state(result)
        return result

    username = (Config.DEMO_ADMIN_USERNAME or "").strip()
    password = Config.DEMO_ADMIN_PASSWORD or ""
    result["username"] = username

    if not username or not password:
        result["action"] = "invalid_config"
        _set_admin_bootstrap_state(result)
        return result

    try:
        Config.ADMIN_USERS.add(username)
        user_rows = querys(
            "SELECT id, password FROM user WHERE username = %s LIMIT 1",
            [username],
            "select",
        )
        hashed_password = hash_password(password)

        if not user_rows:
            querys(
                "INSERT INTO user (username, password, createTime) VALUES (%s, %s, NOW())",
                [username, hashed_password],
                "insert",
            )
            result["action"] = "created"
            result["enabled"] = True
            _set_admin_bootstrap_state(result)
            return result

        result["action"] = "exists"
        result["enabled"] = True

        if Config.DEMO_ADMIN_RESET_PASSWORD:
            user_id = user_rows[0].get("id")
            if user_id:
                querys(
                    "UPDATE user SET password = %s WHERE id = %s",
                    [hashed_password, user_id],
                    "update",
                )
                result["action"] = "reset_password"

        _set_admin_bootstrap_state(result)
        return result
    except Exception as exc:
        result["action"] = "error"
        result["error"] = str(exc)
        _set_admin_bootstrap_state(result)
        return result


def schedule_startup_warmup(app) -> bool:
    """
    异步预热高频数据接口缓存，降低首屏冷启动耗时。
    """
    if not Config.ENABLE_STARTUP_WARMUP:
        with _STARTUP_STATE_LOCK:
            _STARTUP_STATE["warmup"] = {
                "enabled": False,
                "running": False,
                "started_at": None,
                "finished_at": None,
                "duration_seconds": None,
                "paths_total": 0,
                "paths_done": 0,
                "results": [],
                "error": None,
            }
        return False

    warmup_paths = [
        "/getAllData/getHomeData",
        "/getAllData/getYuqingData",
        "/getAllData/getContentCloudData?type=article",
        "/api/report/data",
    ]

    def _warmup_worker():
        all_start = time.time()
        try:
            delay = max(float(Config.STARTUP_WARMUP_DELAY), 0.0)
            if delay:
                time.sleep(delay)

            username = (Config.DEMO_ADMIN_USERNAME or "system").strip() or "system"
            token = create_token(0, username, expires_hours=1)
            headers = {"Authorization": f"Bearer {token}"}

            with app.test_client() as client:
                for path in warmup_paths:
                    req_start = time.time()
                    try:
                        response = client.get(path, headers=headers)
                        duration = time.time() - req_start
                        _warmup_record(path, response.status_code, duration)
                        logger.info(
                            "启动预热: %s -> %s (%.3fs)",
                            path,
                            response.status_code,
                            duration,
                        )
                    except Exception as req_exc:
                        duration = time.time() - req_start
                        _warmup_record(path, None, duration, str(req_exc))
                        logger.warning(f"启动预热失败 {path}: {req_exc}")

            total = time.time() - all_start
            _warmup_finish(total)
            logger.info("启动预热完成，耗时 %.3fs", total)
        except Exception as exc:
            _warmup_finish(time.time() - all_start, str(exc))
            logger.warning(f"启动预热线程异常: {exc}")

    _warmup_start(len(warmup_paths))
    thread = threading.Thread(
        target=_warmup_worker, name="startup-warmup", daemon=True
    )
    thread.start()
    return True
