#!/usr/bin/env python3
"""#7 回归：敏感信息处理（脱敏/密钥隔离/异常脱敏/日志掩码）。"""

import pytest

pytestmark = pytest.mark.unit


class TestGetAllUserDataDesensitized:
    def test_no_password_column(self, monkeypatch):
        import utils.getPublicData as m

        monkeypatch.setattr(
            m,
            "_user_repo",
            lambda: type(
                "R",
                (),
                {
                    "get_all_for_export": lambda self: [
                        {
                            "id": 1,
                            "username": "u",
                            "password": "hash-secret",
                            "create_time": "2026-01-01",
                            "nickname": "n",
                            "email": "e",
                            "bio": "b",
                            "avatar_color": "#fff",
                        }
                    ]
                },
            )(),
        )
        # 绕过缓存装饰器（如有）：直接调用底层函数
        fn = getattr(m.getAllUserData, "__wrapped__", m.getAllUserData)
        rows = fn()
        assert rows, "应返回用户行"
        flat = " ".join(str(c) for row in rows for c in row)
        assert "hash-secret" not in flat


class TestEncryptionFailsClosed:
    def test_encrypt_roundtrip(self):
        from utils.encryption import decrypt_value, encrypt_value

        token = encrypt_value("hello")
        assert token and token != "hello"
        assert decrypt_value(token) == "hello"

    def test_decrypt_invalid_raises_not_plaintext(self):
        from utils.encryption import decrypt_value

        with pytest.raises(ValueError):
            decrypt_value("not-a-valid-token-at-all-1234567890")

    def test_no_fallback_key_without_secret(self, monkeypatch):
        import utils.encryption as m

        monkeypatch.setenv("SECRET_KEY", "")
        monkeypatch.setattr("config.settings.Config.SECRET_KEY", None, raising=False)
        with pytest.raises(RuntimeError):
            m._get_key()

    def test_fernet_cache_rotates_with_key(self, monkeypatch):
        import utils.encryption as m

        monkeypatch.setattr("config.settings.Config.SECRET_KEY", "k1", raising=False)
        f1 = m._get_fernet()
        monkeypatch.setattr("config.settings.Config.SECRET_KEY", "k2", raising=False)
        f2 = m._get_fernet()
        assert f1 is not f2


class TestKeyIsolation:
    def test_production_requires_explicit_distinct_jwt_key(self, monkeypatch):
        from config.settings import Config

        monkeypatch.setattr(Config, "FLASK_ENV", "production")
        monkeypatch.setattr(Config, "SECRET_KEY", "s" * 32)
        monkeypatch.setattr(Config, "JWT_SECRET_KEY", "s" * 32)
        monkeypatch.setattr(Config, "JWT_SECRET_KEY_EXPLICIT", False)
        monkeypatch.setattr(Config, "ALLOWED_ORIGINS", ["https://x.example"])
        monkeypatch.setattr(Config, "ADMIN_USERS", {"admin"})
        with pytest.raises(RuntimeError):
            Config.validate()
        # 显式但相同同样拒绝
        monkeypatch.setattr(Config, "JWT_SECRET_KEY_EXPLICIT", True)
        with pytest.raises(RuntimeError):
            Config.validate()
        # 显式且不同则通过本项（其他项已满足）
        monkeypatch.setattr(Config, "JWT_SECRET_KEY", "j" * 32)
        Config.validate()


class TestRegisterErrorDesensitized:
    def test_register_db_error_not_leaked(self, monkeypatch):
        from services.auth_service import AuthService

        svc = AuthService()
        monkeypatch.setattr(
            svc.user_repo, "find_by_username", lambda username: None
        )
        monkeypatch.setattr(
            svc.user_repo,
            "create",
            lambda *a, **k: (_ for _ in ()).throw(Exception("UNIQUE constraint balabala")),
        )
        ok, msg = svc.register("newuser1", "StrongPass123!", "StrongPass123!")
        assert ok is False
        assert "UNIQUE" not in msg
        assert "balabala" not in msg


class TestCookieMasked:
    def test_sensitive_only_length(self):
        from utils.config_validator import ConfigValidator

        assert ConfigValidator.safe_config_value("WEIBO_COOKIE", "abcd1234EFGH") == (
            "[已设置 len=12]"
        )
        assert "abcd" not in ConfigValidator.safe_config_value(
            "WEIBO_COOKIE", "abcd1234EFGH"
        )
