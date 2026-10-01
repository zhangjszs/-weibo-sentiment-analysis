"""Run Alembic migrations to head.

旧版用裸 pymysql 手工 CREATE TABLE audit_log（#28）：绕开迁移链、无视
TEST_DATABASE_URL，且 audit_log 已在 docs/database/init_database.sql 冻结
基线中（CI 预建）。本脚本只负责把库推进到 head。
"""

import subprocess
import sys


def main() -> int:
    cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
