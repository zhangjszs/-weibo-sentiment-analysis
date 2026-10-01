import logging
import time
from typing import Any

from config.settings import Config
from repositories.user_repository import UserRepository
from utils.jwt_handler import create_token
from utils.log_sanitizer import SafeLogger
from utils.login_lockout import (
    clear_failures,
    is_locked,
    locked_message,
    record_failure,
)
from utils.password_hasher import (
    check_password_strength,
    hash_password,
    verify_password,
)

logger = SafeLogger("auth_service", logging.INFO)


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()

    def login(
        self, username: str, password: str, client_ip: str = ""
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Authenticate user.
        Returns: (success, message, data)

        client_ip 用于失败锁定（#15）：同一 username+IP 连续失败达阈值后
        临时锁定，缓解撞库。
        """
        if is_locked(username, client_ip):
            return False, locked_message(), {}

        user = self.user_repo.find_by_username(username)
        if not user:
            record_failure(username, client_ip)
            return False, "用户名或密码错误", {}

        if not verify_password(password, user.get("password", "")):
            record_failure(username, client_ip)
            return False, "用户名或密码错误", {}

        clear_failures(username, client_ip)

        # Generate Token
        token = create_token(user.get("id"), username)
        user_data = {
            "token": token,
            "user": {
                "id": user.get("id"),
                "username": username,
                "create_time": str(user.get("create_time", "")),
                "is_admin": bool(Config.ADMIN_USERS and username in Config.ADMIN_USERS),
            },
        }
        logger.info(f"User login success: {username}")
        return True, "登录成功", user_data

    def register(
        self, username: str, password: str, confirm_password: str
    ) -> tuple[bool, str]:
        """
        Register new user.
        Returns: (success, message)
        """
        if not username or not password or not confirm_password:
            return False, "所有字段都必须填写"

        if password != confirm_password:
            return False, "两次输入的密码不一致"

        strength = check_password_strength(password)
        if not strength["valid"]:
            return False, f"密码强度不足：{', '.join(strength['suggestions'])}"

        if self.user_repo.find_by_username(username):
            return False, "该用户名已被注册"

        try:
            hashed_password = hash_password(password)
            current_time = time.strftime("%Y-%m-%d", time.localtime())
            self.user_repo.create(username, hashed_password, current_time)
            logger.info(f"User registration success: {username}")
            return True, "注册成功"
        except Exception as e:
            logger.error(f"Registration failed for {username}: {type(e).__name__}")
            return False, "注册失败，请稍后重试"
