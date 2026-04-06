#!/usr/bin/env python3
"""
数据库连接测试脚本
"""

import os
import socket
import sys

import pytest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Config


def is_mysql_available(host=None, port=None, timeout=2):
    """检查MySQL服务是否可用"""
    host = host or Config.DB_HOST
    port = port or Config.DB_PORT
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.fixture
def db_connection():
    """数据库连接fixture"""
    if not is_mysql_available():
        pytest.skip("MySQL服务不可用，跳过数据库测试")
    from utils.query import querys
    return querys


def test_database(db_connection):
    """测试数据库连接和基本操作"""
    print("=== 数据库连接测试 ===")

    try:
        querys = db_connection

        # 测试基本连接
        print("1. 测试数据库连接...")
        result = querys("SELECT 1 as test", [], "select")
        print(f"   连接测试结果: {result}")
        assert result is not None
        assert len(result) > 0
        assert result[0].get('test') == 1

        # 查询用户表结构
        print("\n2. 查询用户表结构...")
        try:
            structure = querys("DESCRIBE user", [], "select")
            print("   用户表结构:")
            for col in structure:
                print(f"     {col}")
        except Exception as e:
            print(f"   查询表结构失败: {e}")

        # 查询所有用户
        print("\n3. 查询所有用户数据...")
        users = querys("SELECT * FROM user", [], "select")
        print(f"   总用户数: {len(users)}")

        for i, user in enumerate(users[:5]):  # 只显示前5个用户
            print(f"   用户{i + 1}:")
            print(f"     ID: {user.get('id')}")
            print(f"     用户名: '{user.get('username', '')}'")
            print(f"     创建时间: {user.get('createTime')}")
            print()

        # 测试特定用户查询
        print("4. 测试特定用户查询...")
        test_users = [("kerwin zhang", "123"), ("Alex", "123456"), ("Admin", "123456")]

        for username, password in test_users:
            print(f"\n   测试用户: '{username}' / '{password}'")
            result = querys(
                "SELECT * FROM user WHERE username = %s AND password = %s",
                [username, password],
                "select",
            )
            print(f"   查询结果: {len(result)} 个匹配")
            if result:
                user = result[0]
                print(
                    f"   匹配用户: ID={user.get('id')}, 用户名='{user.get('username', '')}'"
                )

        print("\n=== 测试完成 ===")
        assert True

    except Exception as e:
        print(f"数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        pytest.fail(f"数据库测试失败: {e}")


def test_mysql_connection():
    """测试MySQL连接是否可用"""
    if not is_mysql_available():
        pytest.skip("MySQL服务不可用")
    assert is_mysql_available() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
