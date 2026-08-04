#!/usr/bin/env python3
"""
audit_service.py 单元测试

audit_service 是安全审计日志写入服务，被 auth_routes（登录/注册）和
user_routes（改密）调用，记录关键用户操作。此前零单元测试覆盖。

测试策略：mock querys() 捕获调用参数，验证 SQL 正确性、字段截断、
类型转换、异常隔离。不触碰真实数据库。
"""

import pytest

pytestmark = pytest.mark.unit

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.audit_service import audit_log


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_querys():
    """Mock querys 并返回 capture 对象，用于断言调用参数。"""
    with patch("services.audit_service.querys") as mocked:
        yield mocked


@pytest.fixture
def captured_call(mock_querys):
    """便捷 fixture：调用 audit_log 后返回 (sql, params, type) 元组。"""
    calls = []

    def capture(*args, **kwargs):
        calls.append(args)
        return None

    mock_querys.side_effect = capture
    return calls


# ---------------------------------------------------------------------------
# 正常写入
# ---------------------------------------------------------------------------


class TestAuditLogHappyPath:
    """正常场景：成功写入审计日志"""

    def test_writes_correct_sql(self, mock_querys):
        """应使用正确的 INSERT SQL"""
        audit_log(1, "alice", "login", "登录成功", "127.0.0.1")
        sql = mock_querys.call_args[0][0]
        assert "INSERT INTO audit_log" in sql
        assert "user_id" in sql
        assert "username" in sql
        assert "action" in sql
        assert "detail" in sql
        assert "ip" in sql
        assert "VALUES (%s, %s, %s, %s, %s)" in sql

    def test_writes_correct_params(self, mock_querys):
        """参数列表应按顺序 [user_id, username, action, detail, ip]"""
        audit_log(42, "alice", "login", "登录成功", "10.0.0.1")
        params = mock_querys.call_args[0][1]
        assert params[0] == 42      # user_id 原样传递
        assert params[1] == "alice"
        assert params[2] == "login"
        assert params[3] == "登录成功"
        assert params[4] == "10.0.0.1"

    def test_writes_with_insert_type(self, mock_querys):
        """应传 type='insert'"""
        audit_log(1, "u", "login", "", "")
        assert mock_querys.call_args[0][2] == "insert"

    def test_call_count_is_one(self, mock_querys):
        """单次调用应只触发一次 querys"""
        audit_log(1, "u", "login", "ok", "1.2.3.4")
        assert mock_querys.call_count == 1


class TestAuditLogRealUsageScenarios:
    """真实生产调用场景（对照 auth_routes / user_routes 的实际调用）"""

    def test_login_success(self, mock_querys):
        """登录成功场景：user_id 为 int"""
        audit_log(1001, "张三", "login", "登录成功", "192.168.1.100")
        params = mock_querys.call_args[0][1]
        assert params[0] == 1001
        assert params[1] == "张三"
        assert params[2] == "login"

    def test_login_failed_with_none_user_id(self, mock_querys):
        """登录失败场景：user_id 为 None（未认证用户）"""
        audit_log(None, "bob", "login_failed", "登录失败", "10.0.0.5")
        params = mock_querys.call_args[0][1]
        assert params[0] is None  # None 原样传递，不转字符串

    def test_register_with_none_user_id(self, mock_querys):
        """注册场景：user_id 为 None"""
        audit_log(None, "newuser", "register", "注册成功", "10.0.0.6")
        params = mock_querys.call_args[0][1]
        assert params[0] is None

    def test_change_password(self, mock_querys):
        """改密场景：user_id 为 int，username 可能为空字符串"""
        audit_log(2002, "", "change_password", "密码修改成功", "10.0.0.7")
        params = mock_querys.call_args[0][1]
        assert params[0] == 2002
        assert params[1] == ""
        assert params[2] == "change_password"


# ---------------------------------------------------------------------------
# 字段截断
# ---------------------------------------------------------------------------


class TestAuditLogFieldTruncation:
    """超长字段应被截断到数据库列长度上限"""

    def test_username_truncated_to_50(self, mock_querys):
        """username 超过 50 字符应截断"""
        long_name = "x" * 100
        audit_log(1, long_name, "login", "", "")
        params = mock_querys.call_args[0][1]
        assert len(params[1]) == 50
        assert params[1] == "x" * 50

    def test_username_exactly_50_not_truncated(self, mock_querys):
        """username 恰好 50 字符不应截断"""
        name_50 = "y" * 50
        audit_log(1, name_50, "login", "", "")
        params = mock_querys.call_args[0][1]
        assert len(params[1]) == 50
        assert params[1] == name_50

    def test_action_truncated_to_50(self, mock_querys):
        """action 超过 50 字符应截断"""
        long_action = "a" * 80
        audit_log(1, "u", long_action, "", "")
        params = mock_querys.call_args[0][1]
        assert len(params[2]) == 50

    def test_detail_truncated_to_500(self, mock_querys):
        """detail 超过 500 字符应截断"""
        long_detail = "d" * 1000
        audit_log(1, "u", "login", long_detail, "")
        params = mock_querys.call_args[0][1]
        assert len(params[3]) == 500

    def test_detail_exactly_500_not_truncated(self, mock_querys):
        """detail 恰好 500 字符不应截断"""
        detail_500 = "e" * 500
        audit_log(1, "u", "login", detail_500, "")
        params = mock_querys.call_args[0][1]
        assert len(params[3]) == 500

    def test_ip_truncated_to_45(self, mock_querys):
        """ip 超过 45 字符应截断（IPv6 最长 45 字符）"""
        long_ip = "2" * 60
        audit_log(1, "u", "login", "", long_ip)
        params = mock_querys.call_args[0][1]
        assert len(params[4]) == 45

    def test_user_id_not_truncated(self, mock_querys):
        """user_id 不做截断（原样传递）"""
        audit_log(999999999999, "u", "login", "", "")
        params = mock_querys.call_args[0][1]
        assert params[0] == 999999999999

    def test_chinese_username_truncated_by_char(self, mock_querys):
        """中文 username 截断按字符数（非字节），50 个中文字符 = 50"""
        chinese_50 = "测" * 50
        audit_log(1, chinese_50, "login", "", "")
        params = mock_querys.call_args[0][1]
        assert len(params[1]) == 50


# ---------------------------------------------------------------------------
# 类型转换
# ---------------------------------------------------------------------------


class TestAuditLogTypeCoercion:
    """非字符串字段应通过 str() 转换（user_id 除外）"""

    def test_username_int_coerced_to_str(self, mock_querys):
        """username 传 int 应转为字符串"""
        audit_log(1, 12345, "login", "", "")
        params = mock_querys.call_args[0][1]
        assert params[1] == "12345"

    def test_action_int_coerced_to_str(self, mock_querys):
        """action 传 int 应转为字符串"""
        audit_log(1, "u", 404, "", "")
        params = mock_querys.call_args[0][1]
        assert params[2] == "404"

    def test_detail_dict_coerced_to_str(self, mock_querys):
        """detail 传 dict 应转为字符串表示"""
        audit_log(1, "u", "login", {"key": "value"}, "")
        params = mock_querys.call_args[0][1]
        assert "key" in params[3]
        assert "value" in params[3]

    def test_ip_none_coerced_to_str_none(self, mock_querys):
        """ip 传 None 会转为字符串 'None'（已知行为，非 bug 但值得记录）"""
        audit_log(1, "u", "login", "", None)
        params = mock_querys.call_args[0][1]
        assert params[4] == "None"

    def test_username_none_coerced_to_str_none(self, mock_querys):
        """username 传 None 会转为字符串 'None'"""
        audit_log(1, None, "login", "", "")
        params = mock_querys.call_args[0][1]
        assert params[1] == "None"

    def test_user_id_none_preserved(self, mock_querys):
        """user_id 为 None 时原样传递 None（不转字符串）"""
        audit_log(None, "u", "login", "", "")
        params = mock_querys.call_args[0][1]
        assert params[0] is None

    def test_user_id_string_preserved(self, mock_querys):
        """user_id 为字符串时原样传递（不转 int）"""
        audit_log("abc-123", "u", "login", "", "")
        params = mock_querys.call_args[0][1]
        assert params[0] == "abc-123"


# ---------------------------------------------------------------------------
# 异常隔离
# ---------------------------------------------------------------------------


class TestAuditLogErrorIsolation:
    """审计日志写入失败不应影响业务流程"""

    def test_querys_exception_does_not_propagate(self, mock_querys):
        """querys 抛异常时 audit_log 不应向上抛"""
        mock_querys.side_effect = RuntimeError("DB connection lost")
        # 不应抛异常
        audit_log(1, "u", "login", "ok", "1.2.3.4")

    def test_querys_exception_logged(self, mock_querys, caplog):
        """querys 抛异常时应记录错误日志"""
        import logging

        mock_querys.side_effect = RuntimeError("DB connection lost")
        with caplog.at_level(logging.ERROR, logger="audit_service"):
            audit_log(1, "u", "login", "ok", "1.2.3.4")
        assert any("审计日志写入失败" in record.message for record in caplog.records)

    def test_querys_integrity_error_swallowed(self, mock_querys):
        """数据库约束异常（如主键冲突）也应被吞掉"""
        mock_querys.side_effect = Exception("Duplicate entry")
        audit_log(1, "u", "login", "ok", "1.2.3.4")  # 不抛异常

    def test_querys_called_even_if_will_fail(self, mock_querys):
        """即使会失败，querys 仍应被调用一次"""
        mock_querys.side_effect = RuntimeError("fail")
        audit_log(1, "u", "login", "ok", "1.2.3.4")
        assert mock_querys.call_count == 1


# ---------------------------------------------------------------------------
# 边界与空值
# ---------------------------------------------------------------------------


class TestAuditLogEdgeCases:
    """边界条件与空值处理"""

    def test_all_empty_strings(self, mock_querys):
        """所有字段为空字符串时应正常写入"""
        audit_log("", "", "", "", "")
        params = mock_querys.call_args[0][1]
        assert params[0] == ""       # user_id 空字符串原样传递
        assert params[1] == ""
        assert params[2] == ""
        assert params[3] == ""
        assert params[4] == ""

    def test_very_long_detail_mixed_chars(self, mock_querys):
        """混合字符的长 detail 应正确截断到 500"""
        mixed = "用户执行了敏感操作: " + "A" * 600
        audit_log(1, "u", "sensitive_action", mixed, "1.2.3.4")
        params = mock_querys.call_args[0][1]
        assert len(params[3]) == 500
        assert params[3].startswith("用户执行了敏感操作")

    def test_ipv6_address(self, mock_querys):
        """IPv6 地址（最长 39 字符）应在 45 上限内"""
        ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        audit_log(1, "u", "login", "", ipv6)
        params = mock_querys.call_args[0][1]
        assert params[4] == ipv6  # 不截断

    def test_ipv4_mapped_ipv6(self, mock_querys):
        """IPv4-mapped IPv6（最长 45 字符）应刚好不截断"""
        ipv4_mapped = "::ffff:192.168.100.228"  # 22 chars
        audit_log(1, "u", "login", "", ipv4_mapped)
        params = mock_querys.call_args[0][1]
        assert params[4] == ipv4_mapped
