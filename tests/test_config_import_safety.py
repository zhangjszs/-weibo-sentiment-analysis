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
        "import dotenv; dotenv.load_dotenv = lambda: None;"
        "from config.settings import Config;"
        "print(Config.JWT_EXPIRATION_HOURS, Config.SPIDER_DELAY, Config.DB_PORT);"
        "Config.validate(); print('validate-ok');"
        "print(len(Config.SECRET_KEY), len(Config.JWT_SECRET_KEY), "
        "Config.SECRET_KEY != Config.JWT_SECRET_KEY)"
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
        # 必须显式清空密钥：子进程会继承 CI/本机的 SECRET_KEY、JWT_SECRET_KEY、
        # ALLOWED_ORIGINS（backend-fast job 正是这么设的），若不清理，staging 下
        # validate() 会合法通过，本用例的前提（staging 缺生产密钥应被阻断）就不成立。
        proc = _run_with_env(
            {
                "FLASK_ENV": "staging",
                "SECRET_KEY": "",
                "JWT_SECRET_KEY": "",
                "ALLOWED_ORIGINS": "",
                "ADMIN_USERS": "",
            }
        )
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


@pytest.mark.parametrize("environment", ["development", "production", "staging"])
@pytest.mark.parametrize(
    ("flask_key", "jwt_key", "error"),
    [
        ("s" * 64, "j" * 64, None),
        ("s" * 64, "s" * 64, "JWT_SECRET_KEY must differ from SECRET_KEY"),
        ("change-me-in-production", "j" * 64, "SECRET_KEY must be a random value"),
        ("s" * 64, "change-me-in-production", "JWT_SECRET_KEY must be a random value"),
        ("s" * 64, " " * 64, "JWT_SECRET_KEY must be a random value"),
        (
            "s" * 64,
            "your-jwt-secret-key-here-at-least-32-characters",
            "JWT_SECRET_KEY must be a random value",
        ),
    ],
)
def test_signing_key_validation(environment, flask_key, jwt_key, error):
    proc = _run_with_env(
        {
            "FLASK_ENV": environment,
            "SECRET_KEY": flask_key,
            "JWT_SECRET_KEY": jwt_key,
            "ALLOWED_ORIGINS": "https://example.test",
            "ADMIN_USERS": "existing-admin",
        }
    )

    if error is None:
        assert proc.returncode == 0, proc.stderr
    else:
        assert proc.returncode != 0
        assert error in proc.stderr


def test_local_development_generates_separate_keys_if_not_configured():
    proc = _run_with_env(
        {"FLASK_ENV": "development", "SECRET_KEY": "", "JWT_SECRET_KEY": ""}
    )

    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines()[-1] == "64 64 True"


@pytest.mark.parametrize("key", ["SECRET_KEY", "JWT_SECRET_KEY"])
def test_production_requires_both_keys_explicitly(key):
    env = {
        "FLASK_ENV": "production",
        "SECRET_KEY": "s" * 64,
        "JWT_SECRET_KEY": "j" * 64,
        "ALLOWED_ORIGINS": "https://example.test",
        "ADMIN_USERS": "existing-admin",
    }
    env[key] = ""
    proc = _run_with_env(env)

    assert proc.returncode != 0
    assert f"{key} must be set" in proc.stderr


@pytest.mark.parametrize(
    ("spider", "nlp", "error"),
    [
        ("", "b" * 64, "SPIDER_SERVICE_TOKEN"),
        ("a" * 64, "short", "NLP_SERVICE_TOKEN"),
        ("a" * 64, "a" * 64, "must be different"),
        ("a" * 64, "b" * 64, None),
    ],
)
def test_compose_requires_distinct_strong_service_tokens(spider, nlp, error):
    proc = _run_with_env(
        {
            "FLASK_ENV": "development",
            "COMPOSE_REQUIRE_SERVICE_TOKENS": "True",
            "SECRET_KEY": "s" * 64,
            "JWT_SECRET_KEY": "j" * 64,
            "SPIDER_SERVICE_TOKEN": spider,
            "NLP_SERVICE_TOKEN": nlp,
        },
    )
    if error is None:
        assert proc.returncode == 0, proc.stderr
    else:
        assert proc.returncode != 0
        assert error in proc.stderr
