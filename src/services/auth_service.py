import logging
import time
from typing import Any, Dict, Tuple

from config.settings import Config
from repositories.user_repository import UserRepository
from utils.jwt_handler import create_token
from utils.log_sanitizer import SafeLogger
from utils.password_hasher import (
    check_password_strength,
    hash_password,
    verify_password,
)

logger = SafeLogger("auth_service", logging.INFO)


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()

    def login(self, username: str, password: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Authenticate user.
        Returns: (success, message, data)
        """
        user = self.user_repo.find_by_username(username)
        if not user:
            return False, "用户名或密码错误", {}

        if not verify_password(password, user.get("password", "")):
            return False, "用户名或密码错误", {}

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
    ) -> Tuple[bool, str]:
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
            logger.error(f"Registration failed for {username}: {str(e)}")
            return False, f"注册失败: {str(e)}"
