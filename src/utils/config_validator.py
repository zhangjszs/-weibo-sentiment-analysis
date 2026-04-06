#!/usr/bin/env python3
"""
配置验证模块
用于验证环境变量配置的正确性
"""

import logging
import os
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ConfigValidator:
    """配置验证器"""

    # 必需的配置项
    REQUIRED_CONFIGS = [
        "SECRET_KEY",
        "DB_HOST",
        "DB_PORT",
        "DB_USER",
        "DB_PASSWORD",
        "DB_NAME",
        "REDIS_URL",
    ]

    # 警告级别的配置项（推荐配置但非必需）
    RECOMMENDED_CONFIGS = [
        "JWT_SECRET_KEY",
        "LOG_LEVEL",
        "WEIBO_COOKIE",
    ]

    # 敏感配置项（不应在日志中显示）
    SENSITIVE_CONFIGS = [
        "SECRET_KEY",
        "JWT_SECRET_KEY",
        "DB_PASSWORD",
        "WEIBO_COOKIE",
        "LLM_API_KEY",
        "SPIDER_SERVICE_TOKEN",
        "NLP_SERVICE_TOKEN",
        "REDIS_PASSWORD",
        "MYSQL_ROOT_PASSWORD",
    ]

    @classmethod
    def validate(cls) -> Tuple[bool, List[str]]:
        """
        验证所有配置

        Returns:
            Tuple[bool, List[str]]: (是否通过, 错误/警告信息列表)
        """
        messages = []
        is_valid = True

        # 检查必需配置
        for config in cls.REQUIRED_CONFIGS:
            value = os.getenv(config)
            if not value:
                messages.append(f"❌ 缺少必需配置: {config}")
                is_valid = False

        # 检查推荐配置
        for config in cls.RECOMMENDED_CONFIGS:
            value = os.getenv(config)
            if not value:
                messages.append(f"⚠️  缺少推荐配置: {config}")

        # 验证特定配置格式
        # 验证数据库端口
        db_port = os.getenv("DB_PORT", "3306")
        try:
            port = int(db_port)
            if not (1 <= port <= 65535):
                messages.append(f"❌ DB_PORT 无效: {db_port}")
                is_valid = False
        except ValueError:
            messages.append(f"❌ DB_PORT 不是有效数字: {db_port}")
            is_valid = False

        # 验证日志级别
        log_level = os.getenv("LOG_LEVEL", "INFO")
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level.upper() not in valid_levels:
            messages.append(f"⚠️  LOG_LEVEL 无效: {log_level}，将使用 INFO")

        # 验证 WEIBO_COOKIE（如果配置了）
        weibo_cookie = os.getenv("WEIBO_COOKIE", "")
        if weibo_cookie:
            if len(weibo_cookie) < 100:
                messages.append("⚠️  WEIBO_COOKIE 可能不完整（长度<100）")
            if "SUB=" not in weibo_cookie and "_T_WM" not in weibo_cookie:
                messages.append("⚠️  WEIBO_COOKIE 格式可能不正确（缺少关键字段）")
        else:
            messages.append("⚠️  未配置 WEIBO_COOKIE，爬虫功能可能无法正常工作")

        # 验证 JWT 过期时间
        jwt_exp = os.getenv("JWT_EXPIRATION_HOURS", "24")
        try:
            exp = int(jwt_exp)
            if exp < 1:
                messages.append(f"⚠️  JWT_EXPIRATION_HOURS 过小: {exp}")
            elif exp > 168:  # 7天
                messages.append(f"⚠️  JWT_EXPIRATION_HOURS 过大: {exp}，存在安全风险")
        except ValueError:
            messages.append(f"❌ JWT_EXPIRATION_HOURS 不是有效数字: {jwt_exp}")
            is_valid = False

        # 验证 SECRET_KEY 强度
        secret_key = os.getenv("SECRET_KEY", "")
        if secret_key:
            if len(secret_key) < 32:
                messages.append("❌ SECRET_KEY 太短（建议>=32字符）")
                is_valid = False
            if secret_key in ["your-secret-key-here", "dev-secret-key", "123456", "admin"]:
                messages.append("❌ SECRET_KEY 使用了默认值，请修改！")
                is_valid = False

        return is_valid, messages

    @classmethod
    def validate_spider_config(cls) -> Tuple[bool, List[str]]:
        """验证爬虫相关配置"""
        messages = []
        is_valid = True

        weibo_cookie = os.getenv("WEIBO_COOKIE", "")
        if not weibo_cookie:
            messages.append("⚠️  未配置 WEIBO_COOKIE，爬虫可能无法访问微博")
            is_valid = False
        else:
            # 检查 Cookie 是否包含必要的字段
            required_fields = ["SUB", "SUBP", "_T_WM"]
            missing_fields = [f for f in required_fields if f not in weibo_cookie]
            if missing_fields:
                messages.append(f"⚠️  WEIBO_COOKIE 可能缺少字段: {missing_fields}")

        # 验证爬虫超时时间
        try:
            timeout = int(os.getenv("SPIDER_TIMEOUT", "45"))
            if timeout < 5:
                messages.append("⚠️  SPIDER_TIMEOUT 过小，可能导致频繁超时")
            elif timeout > 120:
                messages.append("⚠️  SPIDER_TIMEOUT 过大，可能影响性能")
        except ValueError:
            messages.append("❌ SPIDER_TIMEOUT 不是有效数字")
            is_valid = False

        # 验证爬虫延迟
        try:
            delay = int(os.getenv("SPIDER_DELAY", "15"))
            if delay < 5:
                messages.append("⚠️  SPIDER_DELAY 过小，可能触发反爬机制")
        except ValueError:
            messages.append("❌ SPIDER_DELAY 不是有效数字")
            is_valid = False

        return is_valid, messages

    @classmethod
    def safe_config_value(cls, key: str, value: Optional[str] = None) -> str:
        """
        获取安全的配置值显示（隐藏敏感信息）

        Args:
            key: 配置键
            value: 配置值（如不传则自动从环境变量获取）

        Returns:
            str: 安全的显示值
        """
        if value is None:
            value = os.getenv(key, "")

        if key in cls.SENSITIVE_CONFIGS:
            if not value:
                return "[未设置]"
            elif len(value) <= 8:
                return "***"
            else:
                return f"{value[:4]}...{value[-4:]}"
        return value or "[未设置]"

    @classmethod
    def print_config_summary(cls):
        """打印配置摘要（安全版本）"""
        logger.info("=" * 50)
        logger.info("配置验证摘要")
        logger.info("=" * 50)

        is_valid, messages = cls.validate()

        for msg in messages:
            if msg.startswith("❌"):
                logger.error(msg)
            elif msg.startswith("⚠️"):
                logger.warning(msg)
            else:
                logger.info(msg)

        # 显示关键配置（安全版本）
        logger.info("-" * 50)
        logger.info("关键配置:")
        configs_to_show = [
            "FLASK_ENV",
            "DB_HOST",
            "DB_NAME",
            "LOG_LEVEL",
            "WEIBO_COOKIE",
            "SPIDER_SERVICE_ENABLED",
            "NLP_SERVICE_ENABLED",
        ]
        for config in configs_to_show:
            value = cls.safe_config_value(config)
            logger.info(f"  {config}: {value}")

        logger.info("=" * 50)

        return is_valid
