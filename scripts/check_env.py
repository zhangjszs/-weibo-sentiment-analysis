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
    print("❌ Python 3.8+ required for importlib.metadata")
    sys.exit(1)


def check_python_version():
    print(f"Checking Python version... {sys.version.split()[0]}")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required.")
        return False
    print("✅ Python version OK")
    return True


def check_dependencies():
    print("Checking dependencies from requirements.txt...")
    req_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "requirements.txt"
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
            installed_ver = version(pkg_name)
            # We are not checking version constraints here for simplicity, just presence
        except PackageNotFoundError:
            missing.append(req)

    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
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


if __name__ == "__main__":
    print("=== Environment Check ===")
    v = check_python_version()
    d = check_dependencies()
    e = check_env_file()

    if v and d:
        print("\n🎉 Environment is ready!")
        sys.exit(0)
    else:
        print("\n❌ Environment check failed.")
        sys.exit(1)
