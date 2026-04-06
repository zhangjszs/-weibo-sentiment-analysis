#!/usr/bin/env python3
"""
用户认证模块
功能：处理用户登录、注册和登出操作
特性：密码哈希存储、输入验证、安全日志
作者：微博舆情分析系统
"""

import logging

from flask import Blueprint, redirect, render_template, request, session

from services.auth_service import AuthService
from utils.api_response import error, ok
from utils.errorResponse import errorResponse
from utils.input_validator import sanitize_input, validate_password, validate_username
from utils.jwt_handler import jwt_required
from utils.log_sanitizer import SafeLogger

logger = SafeLogger("user_auth", logging.INFO)
auth_service = AuthService()

# 创建用户蓝图，设置URL前缀和模板文件夹
ub = Blueprint("user", __name__, url_prefix="/user", template_folder="templates")


@ub.route("/login", methods=["GET", "POST"])
def login():
    """
    用户登录功能
    GET: 显示登录页面
    POST: 处理登录验证（使用密码哈希）
    """
    if request.method == "POST":
        is_api_request = request.is_json or request.headers.get(
            "Accept", ""
        ).startswith("application/json")
        # 支持 JSON 和表单两种格式
        if request.is_json:
            data = request.get_json() or {}
            username_raw = data.get("username", "").strip()
            password_raw = data.get("password", "").strip()
        else:
            request.form = dict(request.form)
            username_raw = request.form.get("username", "").strip()
            password_raw = request.form.get("password", "").strip()

        # 输入验证
        username_validation = validate_username(username_raw)
        if not username_validation["valid"]:
            if is_api_request:
                return error(username_validation["message"], code=400), 400
            return errorResponse(username_validation["message"]), 400

        password_validation = validate_password(password_raw)
        if not password_validation["valid"]:
            if is_api_request:
                return error(password_validation["message"], code=400), 400
            return errorResponse(password_validation["message"]), 400

        username = sanitize_input(username_raw, max_length=20)
        password = password_raw

        # 调用 Service 层
        success, msg, data = auth_service.login(username, password)

        if success:
            # Session 设置 (保持向后兼容)
            user_info = data["user"]
            session["username"] = user_info["username"]
            session["user_id"] = user_info["id"]
            session["create_time"] = user_info["create_time"]
            session.permanent = True

            if is_api_request:
                return ok(data, msg=msg), 200
            else:
                redirect_url = request.args.get("redirect", "/home")
                return redirect(
                    redirect_url if redirect_url.startswith("/") else "/home", 301
                )
        else:
            if is_api_request:
                return error(msg, code=401), 401
            return errorResponse(msg), 401

    else:
        return render_template("login.html")


@ub.route("/register", methods=["GET", "POST"])
def register():
    """
    用户注册功能
    GET: 显示注册页面
    POST: 处理用户注册（使用密码哈希）
    """
    if request.method == "POST":
        is_api_request = request.is_json or request.headers.get(
            "Accept", ""
        ).startswith("application/json")
        if request.is_json:
            data = request.get_json()
            username_raw = data.get("username", "").strip()
            password_raw = data.get("password", "").strip()
            confirm_raw = (
                data.get("confirmPassword", "") or data.get("passwordCheked", "")
            ).strip()
        else:
            request.form = dict(request.form)
            username_raw = request.form.get("username", "").strip()
            password_raw = request.form.get("password", "").strip()
            confirm_raw = (
                request.form.get("confirmPassword", "")
                or request.form.get("passwordCheked", "")
            ).strip()

        username = sanitize_input(username_raw, max_length=20)
        password = password_raw
        confirm = confirm_raw

        # 调用 Service 层
        success, msg = auth_service.register(username, password, confirm)

        if success:
            if is_api_request:
                return ok(None, msg=msg), 200
            return redirect("/user/login", 301)
        else:
            if is_api_request:
                return error(msg, code=400), 400
            return errorResponse(msg), 400

    else:
        return render_template("register.html")


@ub.route("/logOut", methods=["POST"])
def logOut():
    """
    用户登出功能
    清理会话信息并重定向到登录页面
    """
    current_user = session.get("username", "Unknown")
    session.clear()
    logger.info(f"用户登出: {current_user}")

    is_api_request = request.is_json or request.headers.get("Accept", "").startswith(
        "application/json"
    )

    if is_api_request:
        return ok(msg="登出成功"), 200
    return redirect("/user/login")


@ub.route("/info", methods=["GET"])
@jwt_required
def get_user_info():
    """
    获取当前登录用户信息
    需要 JWT Token 认证
    """
    user = request.current_user
    # 这里的 querys 也可以重构，但为了演示 Service 模式，暂且保留或稍后重构
    # 更好的做法是在 AuthService 中添加 get_user_by_id
    from utils.query import querys

    try:
        users = querys(
            "SELECT id, username, createTime AS create_time FROM user WHERE id = %s",
            [user["user_id"]],
            "select",
        )
        if users:
            user_info = users[0]
            return ok(data={
                        "id": user_info.get("id"),
                        "username": user_info.get("username"),
                        "create_time": str(user_info.get("create_time", "")),
                    }), 200
        else:
            return error("用户不存在", code=404), 404
    except Exception as e:
        logger.error(f"获取用户信息异常: {e}")
        return error("获取用户信息失败", code=500), 500
