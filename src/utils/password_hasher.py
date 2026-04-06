#!/usr/bin/env python3
"""
密码哈希工具模块
功能：使用bcrypt进行密码哈希和验证
特性：安全的密码存储、自动加盐、防止彩虹表攻击
作者：微博舆情分析系统
"""

import logging

import bcrypt

logger = logging.getLogger(__name__)


class PasswordHasher:
    """密码哈希工具类"""

    # bcrypt工作因子，控制哈希计算时间
    # 值越大，计算时间越长，安全性越高
    # 推荐值：12（约250ms）或13（约500ms）
    ROUNDS = 12

    @staticmethod
    def hash_password(password: str) -> str:
        """
        哈希密码

        Args:
            password: 明文密码

        Returns:
            str: 哈希后的密码字符串

        Raises:
            ValueError: 如果密码为空或太短
            Exception: 哈希过程中的其他错误
        """
        if not password:
            raise ValueError("密码不能为空")

        if len(password) < 3:
            raise ValueError("密码长度至少3位")

        try:
            # 将密码编码为bytes
            password_bytes = password.encode("utf-8")

            # 生成salt并哈希密码
            salt = bcrypt.gensalt(rounds=PasswordHasher.ROUNDS)
            hashed_password = bcrypt.hashpw(password_bytes, salt)

            # 将bytes解码为字符串存储
            return hashed_password.decode("utf-8")

        except Exception as e:
            logger.error(f"密码哈希失败: {e}")
            raise Exception("密码哈希过程中发生错误") from e

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        验证密码

        Args:
            password: 明文密码
            hashed_password: 哈希后的密码字符串

        Returns:
            bool: 密码是否匹配

        Raises:
            ValueError: 如果参数为空
            Exception: 验证过程中的其他错误
        """
        if not password:
            raise ValueError("密码不能为空")

        if not hashed_password:
            raise ValueError("哈希密码不能为空")

        try:
            # 将密码和哈希密码编码为bytes
            password_bytes = password.encode("utf-8")
            hashed_bytes = hashed_password.encode("utf-8")

            # 验证密码
            return bcrypt.checkpw(password_bytes, hashed_bytes)

        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False

    @staticmethod
    def check_password_strength(password: str) -> dict:
        """
        检查密码强度

        Args:
            password: 待检查的密码

        Returns:
            dict: 包含强度信息和建议的字典
        """
        result = {"valid": True, "strength": "weak", "score": 0, "suggestions": []}

        # 长度检查
        if len(password) < 6:
            result["valid"] = False
            result["suggestions"].append("密码长度至少6位")
        elif len(password) < 8:
            result["score"] += 1
            result["suggestions"].append("建议密码长度至少8位")
        else:
            result["score"] += 2

        # 复杂度检查
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        if has_upper:
            result["score"] += 1
        else:
            result["suggestions"].append("建议包含大写字母")

        if has_lower:
            result["score"] += 1
        else:
            result["suggestions"].append("建议包含小写字母")

        if has_digit:
            result["score"] += 1
        else:
            result["suggestions"].append("建议包含数字")

        if has_special:
            result["score"] += 1
        else:
            result["suggestions"].append("建议包含特殊字符")

        # 判断强度
        if result["score"] >= 4:
            result["strength"] = "strong"
        elif result["score"] >= 2:
            result["strength"] = "medium"

        return result


def hash_password(password: str) -> str:
    """便捷函数：哈希密码"""
    return PasswordHasher.hash_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """便捷函数：验证密码"""
    return PasswordHasher.verify_password(password, hashed_password)


def check_password_strength(password: str) -> dict:
    """便捷函数：检查密码强度"""
    return PasswordHasher.check_password_strength(password)
