#!/usr/bin/env python3
"""
JWT Token 处理模块
功能：JWT Token 的生成、验证和装饰器
特性：支持 Access Token，可配置过期时间
作者：微博舆情分析系统
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import g, jsonify, request

from config.settings import Config

logger = logging.getLogger(__name__)

# JWT 配置
JWT_SECRET_KEY = Config.JWT_SECRET_KEY
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = Config.JWT_EXPIRATION_HOURS


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
        expires_hours = JWT_EXPIRATION_HOURS

    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "username": username,
        "jti": uuid.uuid4().hex,
        "iat": now,  # 签发时间
        "exp": now + timedelta(hours=expires_hours),  # 过期时间
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    logger.info(f"为用户 {username} 生成 JWT Token")
    return token


def verify_token(token: str) -> dict:
    """
    验证并解析 JWT Token

    Args:
        token: JWT Token 字符串

    Returns:
        dict: 解析后的用户信息，验证失败返回 None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return {
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "exp": payload.get("exp"),
        }
    except jwt.ExpiredSignatureError:
        logger.warning("JWT Token 已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT Token 无效: {e}")
        return None


def jwt_required(f):
    """
    JWT 认证装饰器
    用于保护需要登录的 API 路由

    Usage:
        @bp.route('/protected')
        @jwt_required
        def protected_route():
            user = request.current_user  # 获取当前用户信息
            return jsonify({'user': user})
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # 从 Authorization header 获取 token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # 去掉 'Bearer ' 前缀

        if not token:
            return jsonify(
                {
                    "code": 401,
                    "msg": "缺少认证令牌",
                    "error": "Authorization header missing or invalid",
                }
            ), 401

        # 验证 token
        user_info = verify_token(token)
        if not user_info:
            return jsonify(
                {
                    "code": 401,
                    "msg": "认证令牌无效或已过期",
                    "error": "Invalid or expired token",
                }
            ), 401

        # 将用户信息附加到 request 对象
        request.current_user = user_info
        g.current_user = user_info

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
        token = None

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

        if token:
            user_info = verify_token(token)
            if user_info:
                request.current_user = user_info
                g.current_user = user_info

        return f(*args, **kwargs)

    return decorated
