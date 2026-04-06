#!/usr/bin/env python3
"""
敏感数据加密工具
功能：对数据库中存储的敏感字段进行 AES 加密/解密
使用 Fernet 对称加密（基于 AES-128-CBC + HMAC-SHA256）
"""

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken


def _get_key():
    """
    从环境变量或 SECRET_KEY 生成加密密钥。
    Fernet 要求 32 bytes base64 编码的密钥。
    """
    try:
        from config.settings import Config

        secret = Config.SECRET_KEY
    except Exception:
        secret = os.environ.get("SECRET_KEY", "default-fallback-key")

    # Derive a 32-byte key from SECRET_KEY using SHA-256
    key_bytes = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(key_bytes)


_fernet = None


def _get_fernet():
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_get_key())
    return _fernet


def encrypt_value(plaintext):
    """
    加密明文字符串，返回 base64 编码的密文字符串。
    如果输入为空，返回空字符串。
    """
    if not plaintext:
        return ""
    try:
        f = _get_fernet()
        token = f.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")
    except Exception:
        return plaintext  # 加密失败时返回原文，不影响业务


def decrypt_value(ciphertext):
    """
    解密密文字符串，返回明文。
    如果解密失败（如数据未加密），返回原文。
    """
    if not ciphertext:
        return ""
    try:
        f = _get_fernet()
        plaintext = f.decrypt(ciphertext.encode("utf-8"))
        return plaintext.decode("utf-8")
    except (InvalidToken, Exception):
        return ciphertext  # 解密失败返回原文（兼容未加密数据）


def is_encrypted(value):
    """检查值是否已加密（Fernet token 格式）"""
    if not value or len(value) < 50:
        return False
    try:
        _get_fernet().decrypt(value.encode("utf-8"))
        return True
    except Exception:
        return False
