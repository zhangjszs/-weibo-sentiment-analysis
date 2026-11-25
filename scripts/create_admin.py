"""Create an allowlisted account with an interactive password prompt."""

import argparse
import getpass
import sys
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username")
    args = parser.parse_args()
    if not sys.stdin.isatty():
        parser.error("管理员密码必须在交互式终端输入")

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from services.admin_provisioning import create_admin_account

    password = getpass.getpass("管理员密码: ")
    if password != getpass.getpass("再次输入管理员密码: "):
        parser.error("两次输入的密码不一致")
    try:
        created = create_admin_account(args.username, password)
    except ValueError as exc:
        parser.error(str(exc))
    except SQLAlchemyError:
        print("数据库操作失败。请核对连接配置和当前 schema。", file=sys.stderr)
        return 1
    if not created:
        print("账号已存在。请核验其归属并按运维流程处理。", file=sys.stderr)
        return 1
    print("管理员账号已创建。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
