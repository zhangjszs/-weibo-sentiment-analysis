#!/usr/bin/env python3
"""
Environment Check Script
Verifies Python version and installed dependencies.
"""

import os
import re
import sys

try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:
    print("❌ Python 3.11+ required for importlib.metadata")
    sys.exit(1)


def check_python_version():
    print(f"Checking Python version... {sys.version.split()[0]}")
    if sys.version_info < (3, 11):  # noqa: UP036 - 脚本可能被旧解释器直接执行，保留运行时防护
        print("❌ Python 3.11+ is required (与 pyproject.toml requires-python 对齐).")
        return False
    print("✅ Python version OK")
    return True


def check_dependencies():
    print("Checking dependencies from requirements.txt...")
    req_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "requirements", "requirements.txt"
    )
    if not os.path.exists(req_file):
        print(f"⚠️ {req_file} not found. Skipping dependency check.")
        return True

    with open(req_file) as f:
        required = f.read().splitlines()

    missing = []
    for req in required:
        if not req or req.startswith("#"):
            continue

        # Parse requirement (very basic)
        # Remove comments and whitespace
        req = req.split("#")[0].strip()
        if not req:
            continue

        # Split package name from version specifiers
        # e.g. "pandas>=1.0" -> "pandas"
        pkg_name = re.split(r"[=<>~!]", req)[0].strip()

        try:
            version(pkg_name)  # 仅验证存在性，不校验版本约束
        except PackageNotFoundError:
            missing.append(req)

    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Run: pip install -r requirements/requirements.txt")
        return False

    print("✅ All dependencies installed")
    return True


def check_env_file():
    print("Checking .env file...")
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_file):
        print("✅ .env file exists")
    else:
        print("⚠️ .env file missing. Please create one.")
    return True


def check_required_config():
    """校验必填环境配置（#28 对齐 config_validator：生产必须可过 validate）。"""
    print("Checking required config (via Config.validate)...")
    src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
    sys.path.insert(0, src_dir)

    try:
        from config.settings import Config
    except Exception as e:
        print(f"❌ 无法加载 config.settings: {e}")
        return False

    flask_env = os.getenv("FLASK_ENV", "development")
    try:
        Config.validate()
        print(f"✅ Config.validate() passed (FLASK_ENV={flask_env})")
        return True
    except Exception as e:
        if flask_env in getattr(Config, "PROTECTED_ENVS", {"production"}):
            print(f"❌ Config.validate() failed: {e}")
            return False
        print(f"⚠️ Config.validate() reported issues（非生产环境仅提示）: {e}")
        return True


if __name__ == "__main__":
    print("=== Environment Check ===")
    v = check_python_version()
    d = check_dependencies()
    e = check_env_file()
    c = check_required_config()

    if v and d and c:
        print("\n🎉 Environment is ready!")
        sys.exit(0)
    else:
        print("\n❌ Environment check failed.")
        sys.exit(1)
