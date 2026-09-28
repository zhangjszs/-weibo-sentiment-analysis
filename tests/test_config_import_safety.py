#!/usr/bin/env python3
"""#13 回归：import 期数值解析永不崩溃；validate 汇总；校验语义统一；cookie 走 Config。"""

import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.unit

SRC = os.path.join(os.path.dirname(__file__), "..", "src")


def _run_with_env(env: dict) -> subprocess.CompletedProcess:
    code = (
        f"import sys; sys.path.insert(0, {SRC!r});"
        "from config.settings import Config;"
        "print(Config.JWT_EXPIRATION_HOURS, Config.SPIDER_DELAY, Config.DB_PORT);"
        "Config.validate(); print('validate-ok')"
    )
    merged = dict(os.environ)
    merged.update(env)
    # 避免真实 .env 干扰断言
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=merged,
        timeout=60,
    )


class TestImportNeverCrashes:
    def test_garbage_numerics_fall_back(self):
        proc = _run_with_env(
            {
                "JWT_EXPIRATION_HOURS": "abc",
                "SPIDER_DELAY": "not-a-number",
                "DB_PORT": "zzz",
                "FLASK_ENV": "development",
            }
        )
        assert proc.returncode == 0, proc.stderr
        assert "validate-ok" in proc.stdout
        first = proc.stdout.strip().splitlines()[0]
        assert first == "24 15.0 3306"

    def test_production_aggregates_errors(self):
        proc = _run_with_env(
            {
                "JWT_EXPIRATION_HOURS": "abc",
                "DB_PORT": "zzz",
                "FLASK_ENV": "production",
                "SECRET_KEY": "x" * 40,
                "JWT_SECRET_KEY": "y" * 40,
                "ALLOWED_ORIGINS": "https://x.example",
                "ADMIN_USERS": "admin",
            }
        )
        assert proc.returncode != 0
        assert "JWT_EXPIRATION_HOURS" in proc.stderr
        assert "DB_PORT" in proc.stderr

    def test_staging_is_protected(self):
        proc = _run_with_env({"FLASK_ENV": "staging"})
        # staging 无生产密钥 → validate 应阻断（与 production 一致）
        assert proc.returncode != 0
        assert "SECRET_KEY" in proc.stderr


class TestValidatorSemantics:
    def test_spider_delay_float_accepted(self, monkeypatch):
        from utils.config_validator import ConfigValidator

        monkeypatch.setenv("SPIDER_DELAY", "1.5")
        monkeypatch.setenv("SPIDER_TIMEOUT", "45")
        monkeypatch.setenv("WEIBO_COOKIE", "")
        valid, messages = ConfigValidator.validate_spider_config()
        assert not any("SPIDER_DELAY 不是有效数字" in m for m in messages)

    def test_cookie_flows_through_config(self):
        import pathlib

        src = pathlib.Path("src/tasks/celery_spider.py").read_text(encoding="utf-8")
        assert 'os.getenv("WEIBO_COOKIE"' not in src
        assert "Config.WEIBO_COOKIE" in src
