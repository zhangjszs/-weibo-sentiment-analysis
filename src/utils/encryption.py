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
    从 SECRET_KEY 生成加密密钥。
    Fernet 要求 32 bytes base64 编码的密钥。
    无可用密钥时抛异常（禁止回退到硬编码默认密钥，避免加密旁路）。
    """
    try:
        from config.settings import Config

        secret = Config.SECRET_KEY
    except Exception:
        secret = os.environ.get("SECRET_KEY")

    if not secret:
        raise RuntimeError("加密密钥不可用：SECRET_KEY 未设置")

    # Derive a 32-byte key from SECRET_KEY using SHA-256
    key_bytes = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(key_bytes)


_fernet_cache: dict[bytes, Fernet] = {}


def _get_fernet():
    """按派生密钥缓存 Fernet 实例，密钥轮换时自动使用新实例。"""
    key = _get_key()
    fernet = _fernet_cache.get(key)
    if fernet is None:
        fernet = Fernet(key)
        _fernet_cache[key] = fernet
    return fernet


def encrypt_value(plaintext):
    """
    加密明文字符串，返回 base64 编码的密文字符串。
    如果输入为空，返回空字符串。
    加密失败时抛异常（禁止静默返回明文，避免加密旁路）。
    """
    if not plaintext:
        return ""
    f = _get_fernet()
    token = f.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_value(ciphertext):
    """
    解密密文字符串，返回明文。
    解密失败时抛 ValueError（禁止静默返回原文，避免加密旁路）。
    """
    if not ciphertext:
        return ""
    try:
        f = _get_fernet()
        plaintext = f.decrypt(ciphertext.encode("utf-8"))
        return plaintext.decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("解密失败：密文无效或密钥不匹配") from exc


def is_encrypted(value):
    """检查值是否已加密（Fernet token 格式）"""
    if not value or len(value) < 50:
        return False
    try:
        _get_fernet().decrypt(value.encode("utf-8"))
        return True
    except Exception:
        return False
