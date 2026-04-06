#!/usr/bin/env python3

"""
Project Entry Point
"""

import os
import sys

# Add 'src' directory to Python path
# This allows imports like 'from app import app' or 'from config.settings import Config'
# to work as if they were in the root, OR 'from src.app import app' if we prefer.
# Let's support 'from src.app' style generally, but for legacy code compatibility,
# adding 'src' to path is safer so 'from views import ...' works inside app.py.
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

from app import app

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=app.config.get('DEBUG', False),
        threaded=True
    )
