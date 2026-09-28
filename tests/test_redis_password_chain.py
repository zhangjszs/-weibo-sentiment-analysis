#!/usr/bin/env python3
"""#23 回归：REDIS_PASSWORD 必须到达 Celery broker/backend URL。"""

import importlib
import os

import pytest

pytestmark = pytest.mark.unit


class TestInjectRedisPassword:
    def test_injects_when_missing(self):
        from config.settings import _inject_redis_password

        assert (
            _inject_redis_password("redis://redis:6379/0", "s3cret")
            == "redis://:s3cret@redis:6379/0"
        )

    def test_no_password_no_change(self):
        from config.settings import _inject_redis_password

        assert (
            _inject_redis_password("redis://redis:6379/0", "")
            == "redis://redis:6379/0"
        )

    def test_explicit_password_wins(self):
        from config.settings import _inject_redis_password

        url = "redis://:explicit@redis:6379/0"
        assert _inject_redis_password(url, "other") == url

    def test_non_redis_scheme_untouched(self):
        from config.settings import _inject_redis_password

        assert _inject_redis_password("disabled", "s3cret") == "disabled"
        assert (
            _inject_redis_password("memory://", "s3cret") == "memory://"
        )

    def test_special_chars_quoted(self):
        from config.settings import _inject_redis_password

        assert (
            _inject_redis_password("redis://redis:6379/0", "p@ss:word")
            == "redis://:p%40ss%3Aword@redis:6379/0"
        )


class TestCeleryUrlComposition:
    KEYS = (
        "REDIS_URL",
        "REDIS_PASSWORD",
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
    )

    def _reload_with_env(self, monkeypatch, request, env: dict):
        import dotenv

        import config.settings as settings_mod

        # reload 会重跑 load_dotenv() 把工作区 .env 填回来，先禁掉，
        # 才能真正验证“未显式配置 CELERY_* 时继承 REDIS_URL”的回退链路。
        monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: None)
        snapshot = {key: os.environ.get(key) for key in self.KEYS}
        for key in self.KEYS:
            monkeypatch.delenv(key, raising=False)
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        reloaded = importlib.reload(settings_mod)

        def _restore():
            # 先恢复原始 environ 再 reload，否则模块残留测试值污染后续测试。
            for key in self.KEYS:
                if snapshot[key] is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = snapshot[key]
            importlib.reload(settings_mod)

        request.addfinalizer(_restore)
        return reloaded

    def test_password_reaches_broker_and_backend(self, monkeypatch, request):
        mod = self._reload_with_env(
            monkeypatch,
            request,
            {
                "REDIS_URL": "redis://redis:6379/0",
                "REDIS_PASSWORD": "s3cret",
            },
        )
        assert mod.Config.CELERY_BROKER_URL == "redis://:s3cret@redis:6379/0"
        assert mod.Config.CELERY_RESULT_BACKEND == "redis://:s3cret@redis:6379/0"
        # 直接客户端参数同样带密码
        assert mod.Config.get_redis_connection_params()["password"] == "s3cret"

    def test_empty_password_keeps_plain_urls(self, monkeypatch, request):
        mod = self._reload_with_env(
            monkeypatch,
            request,
            {"REDIS_URL": "redis://redis:6379/0", "REDIS_PASSWORD": ""},
        )
        assert mod.Config.CELERY_BROKER_URL == "redis://redis:6379/0"
        assert mod.Config.get_redis_connection_params()["password"] is None
