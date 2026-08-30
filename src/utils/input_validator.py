#!/usr/bin/env python3
"""
输入验证和清理工具模块
功能：验证和清理用户输入，防止SQL注入和XSS攻击
特性：输入验证、HTML清理、SQL注入防护、长度限制
作者：微博舆情分析系统
"""

import html
import logging
import re

logger = logging.getLogger(__name__)


class InputValidator:
    """输入验证器类"""

    # 用户名验证规则
    USERNAME_MIN_LENGTH = 3
    USERNAME_MAX_LENGTH = 20
    USERNAME_PATTERN = r"^[a-zA-Z0-9_\u4e00-\u9fa5]+$"  # 允许字母、数字、下划线和中文

    # 密码验证规则
    PASSWORD_MIN_LENGTH = 6
    PASSWORD_MAX_LENGTH = 32

    # 关键词验证规则
    KEYWORD_MAX_LENGTH = 50
    KEYWORD_PATTERN = r"^[a-zA-Z0-9\u4e00-\u9fa5\s]+$"  # 允许字母、数字、中文和空格

    # 危险的SQL关键词 —— 仅命中高风险 DDL/DML，常见词 or/and/where 等不再误杀
    # 真正的防护由参数化查询承担，此处仅作纵深防御（--、;、/* 等 + 高危关键字组合）
    SQL_INJECTION_PATTERNS = [
        r"(?i)\b(union\s+select|select\s+.*\s+from|insert\s+into|update\s+.*\s+set|delete\s+from|drop\s+table|alter\s+table|create\s+table|truncate\s+table|exec\s*\(|execute\s*\()",
        r"(?i)(\-\-|\#|\/\*|\*\/|;\s*(select|insert|update|delete|drop|union))",
        r"(?i)(\'\s*or\s*\'|\'\s*or\s*\d|\"\s*or\s*\"|or\s+1\s*=\s*1|and\s+1\s*=\s*1)",
    ]

    # 危险的XSS模式
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"on\w+\s*=",
        r"javascript:",
        r"vbscript:",
        r"data:text/html",
    ]

    @staticmethod
    def validate_username(username: str) -> dict:
        """
        验证用户名

        Args:
            username: 用户名

        Returns:
            dict: {'valid': bool, 'message': str}
        """
        if not username:
            return {"valid": False, "message": "用户名不能为空"}

        if not isinstance(username, str):
            return {"valid": False, "message": "用户名格式错误"}

        username = username.strip()

        # 长度检查
        if len(username) < InputValidator.USERNAME_MIN_LENGTH:
            return {
                "valid": False,
                "message": f"用户名长度至少{InputValidator.USERNAME_MIN_LENGTH}位",
            }

        if len(username) > InputValidator.USERNAME_MAX_LENGTH:
            return {
                "valid": False,
                "message": f"用户名长度最多{InputValidator.USERNAME_MAX_LENGTH}位",
            }

        # 格式检查
        if not re.match(InputValidator.USERNAME_PATTERN, username):
            return {"valid": False, "message": "用户名只能包含字母、数字、下划线和中文"}

        return {"valid": True, "message": "用户名格式正确"}

    @staticmethod
    def validate_password(password: str) -> dict:
        """
        验证密码

        Args:
            password: 密码

        Returns:
            dict: {'valid': bool, 'message': str}
        """
        if not password:
            return {"valid": False, "message": "密码不能为空"}

        if not isinstance(password, str):
            return {"valid": False, "message": "密码格式错误"}

        # 长度检查
        if len(password) < InputValidator.PASSWORD_MIN_LENGTH:
            return {
                "valid": False,
                "message": f"密码长度至少{InputValidator.PASSWORD_MIN_LENGTH}位",
            }

        if len(password) > InputValidator.PASSWORD_MAX_LENGTH:
            return {
                "valid": False,
                "message": f"密码长度最多{InputValidator.PASSWORD_MAX_LENGTH}位",
            }

        return {"valid": True, "message": "密码格式正确"}

    @staticmethod
    def validate_keyword(keyword: str) -> dict:
        """
        验证搜索关键词

        Args:
            keyword: 搜索关键词

        Returns:
            dict: {'valid': bool, 'message': str}
        """
        if not keyword:
            return {"valid": False, "message": "关键词不能为空"}

        if not isinstance(keyword, str):
            return {"valid": False, "message": "关键词格式错误"}

        keyword = keyword.strip()

        # 长度检查
        if len(keyword) > InputValidator.KEYWORD_MAX_LENGTH:
            return {
                "valid": False,
                "message": f"关键词长度最多{InputValidator.KEYWORD_MAX_LENGTH}位",
            }

        # 格式检查
        if not re.match(InputValidator.KEYWORD_PATTERN, keyword):
            return {"valid": False, "message": "关键词只能包含字母、数字、中文和空格"}

        # SQL注入检查
        if InputValidator.detect_sql_injection(keyword):
            return {"valid": False, "message": "关键词包含危险字符"}

        return {"valid": True, "message": "关键词格式正确"}

    @staticmethod
    def detect_sql_injection(text: str) -> bool:
        """
        检测SQL注入

        Args:
            text: 待检测的文本

        Returns:
            bool: 是否检测到SQL注入
        """
        if not text or not isinstance(text, str):
            return False

        text_lower = text.lower()

        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                logger.warning(f"检测到SQL注入尝试: {text[:100]}")
                return True

        return False

    @staticmethod
    def detect_xss(text: str) -> bool:
        """
        检测XSS攻击

        Args:
            text: 待检测的文本

        Returns:
            bool: 是否检测到XSS
        """
        if not text or not isinstance(text, str):
            return False

        text_lower = text.lower()

        for pattern in InputValidator.XSS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(f"检测到XSS尝试: {text[:100]}")
                return True

        return False

    @staticmethod
    def sanitize_html(text: str) -> str:
        """
        清理HTML标签，防止XSS — html.escape 已足够，额外标签移除在转义后无意义，
        保留仅为防御未转义路径的纵深。
        """
        if not text or not isinstance(text, str):
            return ""

        sanitized = html.escape(text, quote=True)
        return sanitized

    @staticmethod
    def sanitize_sql(text: str) -> str:
        """
        清理SQL注入风险 — 已弱化为最小破坏式处理。

        真正防护依赖参数化查询；此处仅去除显式注释符与危险拼接，避免
        破坏正常文本（如 "select a book"）。
        """
        if not text or not isinstance(text, str):
            return ""

        # 仅移除显式 SQL 注释/拼接符，保留正常单词
        sanitized = re.sub(r"(--|#|/\*|\*/)", "", text)
        # 去除连续危险分隔符 ;|
        sanitized = re.sub(r"[;|]{2,}", "", sanitized)

        return sanitized

    @staticmethod
    def sanitize_input(text: str, max_length: int = 255) -> str:
        """
        综合清理输入（HTML转义 + 最小化 SQL 清理 + 截断）。

        说明：用户名等字段已通过正则白名单校验，此处不再二次破坏性替换
        正常单词；仅做长度截断与 HTML 转义。
        """
        if not text or not isinstance(text, str):
            return ""

        sanitized = text[:max_length].strip()
        sanitized = InputValidator.sanitize_html(sanitized)
        # SQL 清理已弱化，仅去注释符
        sanitized = InputValidator.sanitize_sql(sanitized).strip()

        return sanitized

    @staticmethod
    def validate_and_sanitize(text: str, input_type: str = "text") -> dict:
        """
        验证并清理输入

        Args:
            text: 待验证和清理的文本
            input_type: 输入类型 ('username', 'password', 'keyword', 'text')

        Returns:
            dict: {'valid': bool, 'message': str, 'sanitized': str}
        """
        result = {"valid": False, "message": "", "sanitized": ""}

        # 根据输入类型进行验证
        if input_type == "username":
            validation = InputValidator.validate_username(text)
        elif input_type == "password":
            validation = InputValidator.validate_password(text)
        elif input_type == "keyword":
            validation = InputValidator.validate_keyword(text)
        else:
            validation = {"valid": True, "message": "文本格式正确"}

        if not validation["valid"]:
            result["message"] = validation["message"]
            return result

        # 清理输入
        result["sanitized"] = InputValidator.sanitize_input(text)
        result["valid"] = True
        result["message"] = validation["message"]

        return result


def validate_username(username: str) -> dict:
    """便捷函数：验证用户名"""
    return InputValidator.validate_username(username)


def validate_password(password: str) -> dict:
    """便捷函数：验证密码"""
    return InputValidator.validate_password(password)


def validate_keyword(keyword: str) -> dict:
    """便捷函数：验证关键词"""
    return InputValidator.validate_keyword(keyword)


def sanitize_input(text: str, max_length: int = 255) -> str:
    """便捷函数：清理输入"""
    return InputValidator.sanitize_input(text, max_length)


def detect_sql_injection(text: str) -> bool:
    """便捷函数：检测SQL注入"""
    return InputValidator.detect_sql_injection(text)


def detect_xss(text: str) -> bool:
    """便捷函数：检测XSS"""
    return InputValidator.detect_xss(text)
