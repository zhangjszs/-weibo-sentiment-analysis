#!/usr/bin/env python3
"""
Simple Deployment Script
1. Install dependencies
2. Initialize directories
"""

import os
import subprocess
import sys


def install_dependencies():
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements/requirements.txt"]
        )
        print("✅ Dependencies installed.")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies.")
        sys.exit(1)


def init_directories():
    print("📂 Initializing directories...")
    # Add src to path to import Config
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_dir = os.path.join(root_dir, "src")
    sys.path.insert(0, src_dir)

    try:
        from config.settings import Config

        # Config automatically creates directories on import if using the updated settings.py
        # But we can force check here
        for _dir in [
            Config.DATA_DIR,
            Config.MODEL_DIR,
            Config.LOG_DIR,
            Config.CACHE_DIR,
        ]:
            if not os.path.exists(_dir):
                os.makedirs(_dir)
                print(f"Created {_dir}")
        print("✅ Directories initialized.")
    except ImportError:
        print("⚠️ Could not import Config to create directories. Skipping.")
    except Exception as e:
        print(f"❌ Error initializing directories: {e}")


if __name__ == "__main__":
    print("=== Deployment Start ===")
    install_dependencies()
    init_directories()
    print("\n🚀 Deployment tasks completed. You can now run 'python run.py'")
