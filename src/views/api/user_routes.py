"""用户资料与密码路由 ``/api/user/*``。

资料/密码相关辅助函数仅本模块使用，故就近放置。
"""

from flask import request

from services.audit_service import audit_log
from utils.api_response import error, ok
from utils.authz import is_admin_user
from utils.input_validator import validate_password

from ._shared import (
    _require_authenticated_user,
    bp,
    logger,
    user_repo,
)


# ---------------------------------------------------------------------------
# Profile / password helpers
# ---------------------------------------------------------------------------


def _validate_email(email):
    """Return True if *email* looks valid, False otherwise."""
    return not email or "@" in email


def _parse_avatar_color(raw):
    """Return a validated avatar_color string or None."""
    color = str(raw).strip()
    if len(color) == 7 and color.startswith("#"):
        return color
    return None


def _parse_profile_updates(data):
    """Extract and validate profile update fields from *data*.

    Returns (updates_dict, error_response).  On success error_response is None.
    """
    updates = {}

    nickname = data.get("nickname")
    if nickname is not None:
        updates["nickname"] = str(nickname).strip()[:50]

    email = data.get("email")
    if email is not None:
        email = str(email).strip()[:100]
        if not _validate_email(email):
            return None, (error("邮箱格式不正确", code=400), 400)
        updates["email"] = email

    bio = data.get("bio")
    if bio is not None:
        updates["bio"] = str(bio).strip()[:200]

    avatar_color = data.get("avatar_color")
    if avatar_color is not None:
        parsed = _parse_avatar_color(avatar_color)
        if parsed is not None:
            updates["avatar_color"] = parsed

    if not updates:
        return None, error("没有需要更新的字段", code=400), 400

    return updates, None


def _save_profile_updates(user_id, updates):
    """Persist profile *updates* and return the appropriate response."""
    success = user_repo.update_profile(user_id, **updates)
    if success:
        return ok(msg="资料更新成功"), 200
    return error("更新失败", code=500), 500


def _parse_password_change_data(data):
    """Extract and validate password-change inputs from *data*.

    Returns ((old_pw, new_pw), error_response).  On success error_response is None.
    """
    old_password = (data.get("oldPassword") or "").strip()
    new_password = (data.get("newPassword") or "").strip()
    confirm_password = (data.get("confirmPassword") or "").strip()

    if not old_password or not new_password:
        return None, error("请填写完整的密码信息", code=400), 400

    if new_password != confirm_password:
        return None, error("两次输入的新密码不一致", code=400), 400

    validation = validate_password(new_password)
    if not validation["valid"]:
        return None, error(validation["message"], code=400), 400

    return (old_password, new_password), None


def _execute_password_change(user, old_password, new_password):
    """Verify old password, hash new one, persist, and audit.

    Returns a response tuple.
    """
    from utils.password_hasher import hash_password, verify_password

    info = user_repo.find_by_id(user["user_id"])
    if not info:
        return error("用户不存在", code=404), 404

    if not verify_password(old_password, info.get("password", "")):
        return error("旧密码不正确", code=400), 400

    new_hash = hash_password(new_password)
    success = user_repo.update_password(user["user_id"], new_hash)
    if not success:
        return error("密码修改失败", code=500), 500

    logger.info("User %s changed password", user["user_id"])
    audit_log(
        user["user_id"],
        info.get("username", ""),
        "change_password",
        "密码修改成功",
        request.remote_addr,
    )
    return ok(msg="密码修改成功"), 200


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


@bp.route("/user/profile", methods=["GET"])
def get_user_profile():
    """获取用户完整个人资料"""
    user, err = _require_authenticated_user()
    if err is not None:
        return err

    try:
        info = user_repo.find_by_id(user["user_id"])
        if not info:
            return error("用户不存在", code=404), 404
        return ok(
            {
                "id": info.get("id"),
                "username": info.get("username"),
                "nickname": info.get("nickname") or "",
                "email": info.get("email") or "",
                "bio": info.get("bio") or "",
                "avatar_color": info.get("avatar_color") or "#2563EB",
                "create_time": str(info.get("create_time", "")),
                "is_admin": is_admin_user(info),
            }
        ), 200
    except (ValueError, KeyError, TypeError) as e:
        logger.error("获取用户资料参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("获取用户资料服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("获取用户资料异常: %s", e)
        return error("服务器内部错误", code=500), 500


@bp.route("/user/profile", methods=["PUT"])
def update_user_profile():
    """更新用户个人资料"""
    user, err = _require_authenticated_user()
    if err is not None:
        return err

    try:
        data = request.get_json(silent=True) or {}
        updates, err = _parse_profile_updates(data)
        if err is not None:
            return err
        return _save_profile_updates(user["user_id"], updates)
    except (ValueError, KeyError, TypeError) as e:
        logger.error("更新用户资料参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("更新用户资料服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("更新用户资料异常: %s", e)
        return error("服务器内部错误", code=500), 500


@bp.route("/user/password", methods=["PUT"])
def change_user_password():
    """修改用户密码"""
    user, err = _require_authenticated_user()
    if err is not None:
        return err

    try:
        data = request.get_json(silent=True) or {}
        creds, err = _parse_password_change_data(data)
        if err is not None:
            return err

        old_password, new_password = creds
        return _execute_password_change(user, old_password, new_password)
    except (ValueError, KeyError, TypeError) as e:
        logger.error("修改密码参数异常: %s", e)
        return error("请求参数错误", code=400), 400
    except ConnectionError as e:
        logger.error("修改密码服务不可用: %s", e)
        return error("服务暂时不可用", code=503), 503
    except RuntimeError as e:
        logger.error("修改密码异常: %s", e)
        return error("服务器内部错误", code=500), 500
