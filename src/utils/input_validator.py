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

    # 危险的SQL关键词
    SQL_INJECTION_PATTERNS = [
        r"(?i)\b(union|select|insert|update|delete|drop|alter|create|truncate|exec|execute)\b",
        r"(?i)\b(or|and|where|join|having|group|order|by)\b",
        r"(?i)(\-\-|\#|\/\*|;|\|)",
        r"(?i)(\'|\"|\\x00|\\n|\\r)",
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
        清理HTML标签，防止XSS

        Args:
            text: 待清理的文本

        Returns:
            str: 清理后的文本
        """
        if not text or not isinstance(text, str):
            return ""

        # 使用html模块转义HTML特殊字符
        sanitized = html.escape(text)

        # 移除危险的HTML标签
        dangerous_tags = [
            "<script",
            "</script>",
            "<iframe",
            "</iframe>",
            "<object",
            "</object>",
            "<embed",
            "</embed>",
        ]
        for tag in dangerous_tags:
            sanitized = sanitized.replace(tag, "")

        return sanitized

    @staticmethod
    def sanitize_sql(text: str) -> str:
        """
        清理SQL注入风险

        Args:
            text: 待清理的文本

        Returns:
            str: 清理后的文本
        """
        if not text or not isinstance(text, str):
            return ""

        # 移除危险的SQL字符
        sanitized = re.sub(r'[\'"\\;]', "", text)
        sanitized = re.sub(
            r"(?i)(union|select|insert|update|delete|drop|alter|create|truncate|exec|execute)",
            "",
            sanitized,
        )

        return sanitized

    @staticmethod
    def sanitize_input(text: str, max_length: int = 255) -> str:
        """
        综合清理输入（HTML和SQL）

        Args:
            text: 待清理的文本
            max_length: 最大长度

        Returns:
            str: 清理后的文本
        """
        if not text or not isinstance(text, str):
            return ""

        # 截断到最大长度
        sanitized = text[:max_length]

        # 清理HTML
        sanitized = InputValidator.sanitize_html(sanitized)

        # 清理SQL注入风险
        sanitized = InputValidator.sanitize_sql(sanitized)

        # 去除首尾空格
        sanitized = sanitized.strip()

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
