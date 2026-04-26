#!/usr/bin/env python3
"""
配置验证器测试
"""

import os
from unittest import mock

import pytest

from utils.config_validator import ConfigValidator


class TestConfigValidator:
    """测试配置验证器"""

    def test_validate_required_configs(self):
        """测试验证必需配置"""
        with mock.patch.dict(os.environ, {
            'SECRET_KEY': 'a' * 32,
            'DB_HOST': 'localhost',
            'DB_PORT': '3306',
            'DB_USER': 'root',
            'DB_PASSWORD': 'password',
            'DB_NAME': 'wb',
            'REDIS_URL': 'redis://localhost:6379/0',
        }):
            is_valid, messages = ConfigValidator.validate()
            assert is_valid is True

    def test_validate_missing_required_config(self):
        """测试缺少必需配置"""
        with mock.patch.dict(os.environ, {}, clear=True):
            is_valid, messages = ConfigValidator.validate()
            assert is_valid is False
            assert any("SECRET_KEY" in msg for msg in messages)

    def test_validate_weak_secret_key(self):
        """测试弱密钥检测"""
        with mock.patch.dict(os.environ, {
            'SECRET_KEY': '123456',
            'DB_HOST': 'localhost',
            'DB_PORT': '3306',
            'DB_USER': 'root',
            'DB_PASSWORD': 'password',
            'DB_NAME': 'wb',
            'REDIS_URL': 'redis://localhost:6379/0',
        }):
            is_valid, messages = ConfigValidator.validate()
            assert is_valid is False
            assert any("SECRET_KEY" in msg for msg in messages)

    def test_validate_invalid_db_port(self):
        """测试无效数据库端口"""
        with mock.patch.dict(os.environ, {
            'SECRET_KEY': 'a' * 32,
            'DB_HOST': 'localhost',
            'DB_PORT': 'invalid',
            'DB_USER': 'root',
            'DB_PASSWORD': 'password',
            'DB_NAME': 'wb',
            'REDIS_URL': 'redis://localhost:6379/0',
        }):
            is_valid, messages = ConfigValidator.validate()
            assert is_valid is False

    def test_safe_config_value(self):
        """测试安全配置值显示"""
        value = ConfigValidator.safe_config_value("SECRET_KEY", "my-secret-key")
        assert value == "my-s...-key"

    def test_safe_config_value_empty(self):
        """测试空值安全显示"""
        value = ConfigValidator.safe_config_value("SECRET_KEY", "")
        assert value == "[未设置]"

    def test_safe_config_value_non_sensitive(self):
        """测试非敏感配置值"""
        value = ConfigValidator.safe_config_value("LOG_LEVEL", "INFO")
        assert value == "INFO"


class TestSpiderConfigValidator:
    """测试爬虫配置验证"""

    def test_validate_without_cookie(self):
        """测试未配置Cookie"""
        with mock.patch.dict(os.environ, {}, clear=True):
            is_valid, messages = ConfigValidator.validate_spider_config()
            assert is_valid is False
            assert any("WEIBO_COOKIE" in msg for msg in messages)

    def test_validate_with_cookie(self):
        """测试配置了Cookie"""
        with mock.patch.dict(os.environ, {
            'WEIBO_COOKIE': 'SUB=_2Ak; SUBP=0033Wr; _T_WM=12345',
        }):
            is_valid, messages = ConfigValidator.validate_spider_config()
            assert is_valid is True

    def test_validate_invalid_timeout(self):
        """测试无效超时配置"""
        with mock.patch.dict(os.environ, {
            'WEIBO_COOKIE': 'valid_cookie',
            'SPIDER_TIMEOUT': 'invalid',
        }):
            is_valid, messages = ConfigValidator.validate_spider_config()
            assert is_valid is False
