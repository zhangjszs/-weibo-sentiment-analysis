#!/usr/bin/env python3
"""
JWT Token 处理模块
功能：JWT Token 的生成、验证和装饰器
特性：支持 Access Token，可配置过期时间
作者：微博舆情分析系统
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from functools import wraps

import jwt
from flask import g, request

from config.settings import Config

logger = logging.getLogger(__name__)

# JWT 配置 — 密钥与过期时间不在 import 时快照，避免测试/配置热重载时签名与验签不一致
JWT_ALGORITHM = "HS256"
# aud/iss（#15）：此前签发的 token 无任何受众/签发者声明，一份 token 可以
# 被任意接受方原样转发使用。注意：上线后旧 token（无 aud/iss）会验签失败，
# 用户需重新登录一次，属预期行为。
JWT_ISSUER = "weibo-sentiment-api"
JWT_AUDIENCE = "weibo-sentiment-web"


def _jwt_secret_key() -> str:
    return Config.JWT_SECRET_KEY


def _jwt_expiration_hours() -> int:
    return Config.JWT_EXPIRATION_HOURS


def create_token(user_id: int, username: str, expires_hours: int = None) -> str:
    """
    生成 JWT Token

    Args:
        user_id: 用户ID
        username: 用户名
        expires_hours: 过期时间（小时），默认使用配置值

    Returns:
        str: JWT Token 字符串
    """
    if expires_hours is None:
        expires_hours = _jwt_expiration_hours()

    now = datetime.now(UTC)
    payload = {
        "user_id": user_id,
        "username": username,
        "jti": uuid.uuid4().hex,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": now,  # 签发时间
        "exp": now + timedelta(hours=expires_hours),  # 过期时间
    }

    token = jwt.encode(payload, _jwt_secret_key(), algorithm=JWT_ALGORITHM)
    logger.info(f"为用户 {username} 生成 JWT Token")
    return token


def revoke_token(token: str) -> bool:
    """
    撤销一个 token（logout 作废 / extend 旋转旧 token 时调用）。

    签名仍需有效才撤销；已过期 token 无需撤销（验证层直接拒绝）。
    """
    try:
        payload = jwt.decode(
            token,
            _jwt_secret_key(),
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={"verify_exp": False},
        )
    except jwt.InvalidTokenError:
        return False

    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti:
        return False

    from utils.token_blacklist import revoke_jti

    ttl = max(int(exp - datetime.now(UTC).timestamp()), 0) if exp else 3600
    return revoke_jti(jti, ttl)


def verify_token(token: str) -> dict:
    """
    验证并解析 JWT Token

    Args:
        token: JWT Token 字符串

    Returns:
        dict: 解析后的用户信息，验证失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            _jwt_secret_key(),
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
    except jwt.ExpiredSignatureError:
        logger.warning("JWT Token 已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT Token 无效: {e}")
        return None

    # 撤销检查（#15）：jti 此前生成后从不校验，logout 只是删 Cookie，
    # token 在自然过期前始终有效
    from utils.token_blacklist import is_jti_revoked

    if is_jti_revoked(payload.get("jti")):
        logger.warning("JWT Token 已被撤销（jti 在黑名单）")
        return None

    return {
        "user_id": payload.get("user_id"),
        "username": payload.get("username"),
        "jti": payload.get("jti"),
        "exp": payload.get("exp"),
        "iat": payload.get("iat"),
    }


def _extract_token():
    """取请求 token：Bearer 头优先，回退认证 Cookie（#15 单轨统一）。

    此前 jwt_required 只认 Bearer，而 require_jwt / 中间件 _require_jwt_auth
    都认 Bearer+Cookie，三套实现错误结构还各不相同；现统一为本函数 + 统一
    错误 envelope。
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            return token
    return request.cookies.get(Config.AUTH_COOKIE_NAME)


def jwt_required(f):
    """
    JWT 认证装饰器（单轨标准实现，authz.require_jwt 为其别名）
    用于保护需要登录的 API 路由

    支持 ``Authorization: Bearer <token>`` 与 ``Config.AUTH_COOKIE_NAME``
    cookie 两条轨，与全局中间件 ``_require_jwt_auth`` 行为一致。

    Usage:
        @bp.route('/protected')
        @jwt_required
        def protected_route():
            user = request.current_user  # 获取当前用户信息
            return jsonify({'user': user})
    """
    from utils.api_response import error

    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return error("缺少认证令牌", code=401), 401

        user_info = verify_token(token)
        if not user_info:
            return error("认证令牌无效或已过期", code=401), 401

        # 将用户信息附加到 request 对象
        request.current_user = user_info
        g.current_user = user_info
        # rate_limiter 的 user 键读 g.user_id；此前从未设置，限流按 IP 走（#15）
        g.user_id = user_info.get("user_id")

        return f(*args, **kwargs)

    return decorated


def jwt_optional(f):
    """
    可选 JWT 认证装饰器
    如果提供了有效 token，则解析用户信息；否则继续执行

    Usage:
        @bp.route('/public')
        @jwt_optional
        def public_route():
            user = getattr(request, 'current_user', None)
            return jsonify({'user': user})
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()

        if token:
            user_info = verify_token(token)
            if user_info:
                request.current_user = user_info
                g.current_user = user_info
                g.user_id = user_info.get("user_id")

        return f(*args, **kwargs)

    return decorated
