#!/usr/bin/env python3
"""
日志脱敏工具模块
功能：对敏感信息进行脱敏处理，防止日志泄露
特性：密码脱敏、IP地址脱敏、邮箱脱敏、手机号脱敏
作者：微博舆情分析系统
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class LogSanitizer:
    """日志脱敏器类"""

    # 敏感信息模式
    PASSWORD_PATTERNS = [
        r'password["\']?\s*[:=]\s*["\']?[^"\']{8,}["\']?',  # password="xxx"
        r'pwd["\']?\s*[:=]\s*["\']?[^"\']{8,}["\']?',  # pwd="xxx"
        r'passwd["\']?\s*[:=]\s*["\']?[^"\']{8,}["\']?',  # passwd="xxx"
    ]

    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    PHONE_PATTERN = r"\b1[3-9]\d{9}\b"
    ID_CARD_PATTERN = r"\b\d{15,19}\b"

    # IP地址脱敏（保留前两段）
    IP_PATTERN = r"\b(\d{1,3}\.\d{1,3})\.\d+\.\d+\b"

    @staticmethod
    def sanitize_password(text: str) -> str:
        """
        脱敏密码信息

        Args:
            text: 包含密码的文本

        Returns:
            str: 脱敏后的文本
        """
        if not text:
            return text

        sanitized = text
        for pattern in LogSanitizer.PASSWORD_PATTERNS:
            sanitized = re.sub(pattern, "******", sanitized, flags=re.IGNORECASE)

        return sanitized

    @staticmethod
    def sanitize_email(text: str) -> str:
        """
        脱敏邮箱地址

        Args:
            text: 包含邮箱的文本

        Returns:
            str: 脱敏后的文本
        """
        if not text:
            return text

        def replace_email(match):
            email = match.group(0)
            if "@" in email:
                local, domain = email.split("@", 1)
                # 保留邮箱前缀的前3个字符和后缀
                local_hidden = local[:3] + "***" if len(local) > 3 else local
                domain_hidden = domain[:3] + "***" if len(domain) > 3 else domain
                return f"{local_hidden}@{domain_hidden}"
            return email

        return re.sub(LogSanitizer.EMAIL_PATTERN, replace_email, text)

    @staticmethod
    def sanitize_phone(text: str) -> str:
        """
        脱敏手机号

        Args:
            text: 包含手机号的文本

        Returns:
            str: 脱敏后的文本
        """
        if not text:
            return text

        def replace_phone(match):
            phone = match.group(0)
            if len(phone) >= 7:
                # 保留前3位和后2位，中间用***代替
                return phone[:3] + "***" + phone[-2:]
            return phone

        return re.sub(LogSanitizer.PHONE_PATTERN, replace_phone, text)

    @staticmethod
    def sanitize_id_card(text: str) -> str:
        """
        脱敏身份证号

        Args:
            text: 包含身份证号的文本

        Returns:
            str: 脱敏后的文本
        """
        if not text:
            return text

        def replace_id_card(match):
            id_card = match.group(0)
            if len(id_card) >= 10:
                # 保留前6位和后4位，中间用***代替
                return id_card[:6] + "***" + id_card[-4:]
            return id_card

        return re.sub(LogSanitizer.ID_CARD_PATTERN, replace_id_card, text)

    @staticmethod
    def sanitize_ip(text: str) -> str:
        """
        脱敏IP地址

        Args:
            text: 包含IP地址的文本

        Returns:
            str: 脱敏后的文本
        """
        if not text:
            return text

        def replace_ip(match):
            ip = match.group(0)
            parts = ip.split(".")
            if len(parts) == 4:
                # 保留前两段，后两段用***代替
                return f"{parts[0]}.{parts[1]}.***.***"
            return ip

        return re.sub(LogSanitizer.IP_PATTERN, replace_ip, text)

    @staticmethod
    def sanitize_all(text: str) -> str:
        """
        对所有敏感信息进行脱敏

        Args:
            text: 待脱敏的文本

        Returns:
            str: 脱敏后的文本
        """
        if not text:
            return text

        # 按优先级顺序进行脱敏
        sanitized = LogSanitizer.sanitize_password(text)
        sanitized = LogSanitizer.sanitize_email(sanitized)
        sanitized = LogSanitizer.sanitize_phone(sanitized)
        sanitized = LogSanitizer.sanitize_id_card(sanitized)
        sanitized = LogSanitizer.sanitize_ip(sanitized)

        return sanitized

    @staticmethod
    def sanitize_dict(data: dict, sensitive_keys: Optional[list] = None) -> dict:
        """
        对字典中的敏感信息进行脱敏

        Args:
            data: 待脱敏的字典
            sensitive_keys: 需要脱敏的键名列表

        Returns:
            dict: 脱敏后的字典
        """
        if not data:
            return data

        if sensitive_keys is None:
            sensitive_keys = [
                "password",
                "pwd",
                "passwd",
                "email",
                "phone",
                "id_card",
                "idcard",
            ]

        sanitized = data.copy()
        for key in sanitized:
            if key.lower() in [k.lower() for k in sensitive_keys]:
                if isinstance(sanitized[key], str):
                    if (
                        "password" in key.lower()
                        or "pwd" in key.lower()
                        or "passwd" in key.lower()
                    ):
                        sanitized[key] = "******"
                    elif "email" in key.lower():
                        sanitized[key] = LogSanitizer.sanitize_email(sanitized[key])
                    elif "phone" in key.lower():
                        sanitized[key] = LogSanitizer.sanitize_phone(sanitized[key])
                    elif "id_card" in key.lower() or "idcard" in key.lower():
                        sanitized[key] = LogSanitizer.sanitize_id_card(sanitized[key])

        return sanitized


class SafeLogger:
    """安全的日志记录器，自动进行脱敏处理"""

    def __init__(self, name: str, level: int = logging.INFO):
        """
        初始化安全日志记录器

        Args:
            name: 日志记录器名称
            level: 日志级别
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # 添加处理器
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def debug(self, msg: str, *args, **kwargs):
        """记录DEBUG级别日志（自动脱敏）"""
        sanitized_msg = LogSanitizer.sanitize_all(msg)
        self.logger.debug(sanitized_msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """记录INFO级别日志（自动脱敏）"""
        sanitized_msg = LogSanitizer.sanitize_all(msg)
        self.logger.info(sanitized_msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """记录WARNING级别日志（自动脱敏）"""
        sanitized_msg = LogSanitizer.sanitize_all(msg)
        self.logger.warning(sanitized_msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """记录ERROR级别日志（自动脱敏）"""
        sanitized_msg = LogSanitizer.sanitize_all(msg)
        self.logger.error(sanitized_msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """记录CRITICAL级别日志（自动脱敏）"""
        sanitized_msg = LogSanitizer.sanitize_all(msg)
        self.logger.critical(sanitized_msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        """记录异常信息（自动脱敏）"""
        sanitized_msg = LogSanitizer.sanitize_all(msg)
        self.logger.exception(sanitized_msg, *args, **kwargs)


def sanitize_password(text: str) -> str:
    """便捷函数：脱敏密码"""
    return LogSanitizer.sanitize_password(text)


def sanitize_email(text: str) -> str:
    """便捷函数：脱敏邮箱"""
    return LogSanitizer.sanitize_email(text)


def sanitize_phone(text: str) -> str:
    """便捷函数：脱敏手机号"""
    return LogSanitizer.sanitize_phone(text)


def sanitize_ip(text: str) -> str:
    """便捷函数：脱敏IP地址"""
    return LogSanitizer.sanitize_ip(text)


def sanitize_all(text: str) -> str:
    """便捷函数：对所有敏感信息进行脱敏"""
    return LogSanitizer.sanitize_all(text)
