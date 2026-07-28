#!/usr/bin/env python3
"""
auth_service.py 单元测试

auth_service 是认证服务，封装登录与注册业务逻辑，依赖 UserRepository、
JWT 工具、密码哈希工具。此前只有集成测试 test_auth_jwt.py，没有针对
service 层的单元测试。

测试策略：
- login：用户不存在 / 密码错误 / 登录成功 / is_admin 判定 / token 生成参数 /
  create_time 字符串化 / 缺失字段容错
- register：字段缺失 / 密码不一致 / 密码强度不足 / 用户名已存在 / 创建异常 /
  成功路径 / hash_password 与 repo.create 调用参数

mock 所有外部依赖（UserRepository、create_token、verify_password、hash_password、
check_password_strength），不触碰真实 DB / bcrypt / JWT。
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.settings import Config
from services.auth_service import AuthService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_user_repo():
    """Patch UserRepository，使 AuthService 使用 mock 仓储实例。"""
    with patch("services.auth_service.UserRepository") as mock_class:
        repo = MagicMock()
        mock_class.return_value = repo
        yield repo


@pytest.fixture
def patched_collaborators():
    """Patch JWT 与密码工具，返回各 mock 供单测配置返回值。

    默认行为：create_token 返回 'fake-token'，verify_password 返回 True，
    hash_password 返回 'hashed-pw'，check_password_strength 返回 valid=True。
    """
    with patch("services.auth_service.create_token") as mock_token, patch(
        "services.auth_service.verify_password"
    ) as mock_verify, patch(
        "services.auth_service.hash_password"
    ) as mock_hash, patch(
        "services.auth_service.check_password_strength"
    ) as mock_strength:
        mock_token.return_value = "fake-token"
        mock_verify.return_value = True
        mock_hash.return_value = "hashed-pw"
        mock_strength.return_value = {
            "valid": True,
            "strength": "strong",
            "score": 5,
            "suggestions": [],
        }
        yield {
            "create_token": mock_token,
            "verify_password": mock_verify,
            "hash_password": mock_hash,
            "check_password_strength": mock_strength,
        }


@pytest.fixture
def patched_admin_users(monkeypatch):
    """提供可配置的 Config.ADMIN_USERS，默认空（无管理员）。"""
    monkeypatch.setattr(Config, "ADMIN_USERS", "")
    return Config


def _make_user(
    user_id=1,
    username="alice",
    password="hashed_secret",
    create_time="2026-01-01 10:00:00",
):
    """构造模拟的 user dict（find_by_username 返回结构）"""
    return {
        "id": user_id,
        "username": username,
        "password": password,
        "create_time": create_time,
        "nickname": "",
        "email": "",
    }


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------


class TestLogin:
    """login 登录逻辑"""

    def test_success_returns_token_and_user(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """登录成功 → (True, '登录成功', {token, user})"""
        mock_user_repo.find_by_username.return_value = _make_user()
        service = AuthService()

        success, message, data = service.login("alice", "secret123")

        assert success is True
        assert message == "登录成功"
        assert data["token"] == "fake-token"
        assert data["user"]["id"] == 1
        assert data["user"]["username"] == "alice"

    def test_user_not_found_returns_generic_error(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """用户不存在 → (False, '用户名或密码错误', {})，不泄露用户是否存在"""
        mock_user_repo.find_by_username.return_value = None
        service = AuthService()

        success, message, data = service.login("nobody", "secret123")

        assert success is False
        assert message == "用户名或密码错误"
        assert data == {}

    def test_wrong_password_returns_generic_error(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """密码错误 → (False, '用户名或密码错误', {})，与用户不存在消息一致（防枚举）"""
        mock_user_repo.find_by_username.return_value = _make_user()
        patched_collaborators["verify_password"].return_value = False
        service = AuthService()

        success, message, data = service.login("alice", "wrong")

        assert success is False
        assert message == "用户名或密码错误"
        assert data == {}

    def test_verify_password_called_with_correct_args(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """应将明文密码与库存 hash 传给 verify_password"""
        mock_user_repo.find_by_username.return_value = _make_user(
            password="stored_hash"
        )
        service = AuthService()
        service.login("alice", "plaintext")

        patched_collaborators["verify_password"].assert_called_once_with(
            "plaintext", "stored_hash"
        )

    def test_create_token_called_with_user_id_and_username(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """应将 user.id 与 username 传给 create_token"""
        mock_user_repo.find_by_username.return_value = _make_user(user_id=42)
        service = AuthService()
        service.login("alice", "secret")

        patched_collaborators["create_token"].assert_called_once_with(42, "alice")

    def test_is_admin_true_when_username_in_admin_users(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """username 在 Config.ADMIN_USERS 中 → is_admin=True"""
        patched_admin_users.ADMIN_USERS = "alice,bob"
        mock_user_repo.find_by_username.return_value = _make_user(username="alice")
        service = AuthService()

        _, _, data = service.login("alice", "secret")

        assert data["user"]["is_admin"] is True

    def test_is_admin_false_when_username_not_in_admin_users(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """username 不在 Config.ADMIN_USERS 中 → is_admin=False"""
        patched_admin_users.ADMIN_USERS = "bob,carol"
        mock_user_repo.find_by_username.return_value = _make_user(username="alice")
        service = AuthService()

        _, _, data = service.login("alice", "secret")

        assert data["user"]["is_admin"] is False

    def test_is_admin_false_when_admin_users_empty(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """Config.ADMIN_USERS 为空 → is_admin=False（空字符串 falsy）"""
        patched_admin_users.ADMIN_USERS = ""
        mock_user_repo.find_by_username.return_value = _make_user(username="alice")
        service = AuthService()

        _, _, data = service.login("alice", "secret")

        assert data["user"]["is_admin"] is False

    def test_create_time_stringified_in_user_data(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """user.create_time 应被 str() 转换后放入返回数据"""
        mock_user_repo.find_by_username.return_value = _make_user(
            create_time="2026-01-01 10:00:00"
        )
        service = AuthService()

        _, _, data = service.login("alice", "secret")

        assert data["user"]["create_time"] == "2026-01-01 10:00:00"

    def test_missing_create_time_becomes_empty_string(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """user 无 create_time 字段 → 返回空字符串（.get 默认值 + str）"""
        user = _make_user()
        del user["create_time"]
        mock_user_repo.find_by_username.return_value = user
        service = AuthService()

        _, _, data = service.login("alice", "secret")

        assert data["user"]["create_time"] == ""

    def test_missing_password_field_treated_as_empty(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """user 无 password 字段 → verify_password 收到空串（不抛异常）"""
        user = _make_user()
        del user["password"]
        mock_user_repo.find_by_username.return_value = user
        service = AuthService()

        success, _, _ = service.login("alice", "secret")

        # verify_password 默认返回 True，故登录成功；关键是未抛异常
        assert success is True
        patched_collaborators["verify_password"].assert_called_once_with(
            "secret", ""
        )

    def test_user_id_in_data_from_repo(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """返回数据中的 user.id 应来自仓储返回的 user.id"""
        mock_user_repo.find_by_username.return_value = _make_user(user_id=99)
        service = AuthService()

        _, _, data = service.login("alice", "secret")

        assert data["user"]["id"] == 99

    def test_username_in_data_uses_login_input(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """返回数据中的 username 使用入参（而非仓储返回的 username）"""
        user = _make_user(username="repo_name")
        mock_user_repo.find_by_username.return_value = user
        service = AuthService()

        _, _, data = service.login("input_name", "secret")

        assert data["user"]["username"] == "input_name"


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------


class TestRegister:
    """register 注册逻辑"""

    def test_success_returns_true(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """注册成功 → (True, '注册成功')"""
        mock_user_repo.find_by_username.return_value = None
        service = AuthService()

        success, message = service.register("newbie", "Str0ng!pass", "Str0ng!pass")

        assert success is True
        assert message == "注册成功"

    def test_empty_username_rejected(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """username 为空 → (False, '所有字段都必须填写')，不查重不哈希"""
        service = AuthService()

        success, message = service.register("", "Str0ng!pass", "Str0ng!pass")

        assert success is False
        assert message == "所有字段都必须填写"
        mock_user_repo.find_by_username.assert_not_called()
        patched_collaborators["hash_password"].assert_not_called()

    def test_empty_password_rejected(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """password 为空 → (False, '所有字段都必须填写')"""
        service = AuthService()

        success, message = service.register("newbie", "", "")

        assert success is False
        assert message == "所有字段都必须填写"

    def test_empty_confirm_password_rejected(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """confirm_password 为空 → (False, '所有字段都必须填写')"""
        service = AuthService()

        success, message = service.register("newbie", "Str0ng!pass", "")

        assert success is False
        assert message == "所有字段都必须填写"

    def test_password_mismatch_rejected(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """两次密码不一致 → (False, '两次输入的密码不一致')"""
        service = AuthService()

        success, message = service.register("newbie", "AAA123!@#", "BBB456#$%")

        assert success is False
        assert message == "两次输入的密码不一致"
        # 密码不一致应在强度检查前就返回
        patched_collaborators["check_password_strength"].assert_not_called()

    def test_weak_password_rejected_with_suggestions(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """密码强度不足 → (False, '密码强度不足：...')，拼接建议"""
        patched_collaborators["check_password_strength"].return_value = {
            "valid": False,
            "strength": "weak",
            "score": 0,
            "suggestions": ["密码长度至少6位", "建议包含大写字母"],
        }
        service = AuthService()

        success, message = service.register("newbie", "abc", "abc")

        assert success is False
        assert message == "密码强度不足：密码长度至少6位, 建议包含大写字母"

    def test_username_already_exists_rejected(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """用户名已存在 → (False, '该用户名已被注册')"""
        mock_user_repo.find_by_username.return_value = _make_user(username="newbie")
        service = AuthService()

        success, message = service.register("newbie", "Str0ng!pass", "Str0ng!pass")

        assert success is False
        assert message == "该用户名已被注册"
        # 已存在时不应哈希/创建
        patched_collaborators["hash_password"].assert_not_called()
        mock_user_repo.create.assert_not_called()

    def test_repo_create_exception_returns_failure(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """仓储 create 抛异常 → 捕获并返回 (False, '注册失败: ...')"""
        mock_user_repo.find_by_username.return_value = None
        mock_user_repo.create.side_effect = RuntimeError("DB down")
        service = AuthService()

        success, message = service.register("newbie", "Str0ng!pass", "Str0ng!pass")

        assert success is False
        assert "注册失败" in message
        assert "DB down" in message

    def test_hash_password_called_with_plaintext(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """应将明文密码传给 hash_password"""
        mock_user_repo.find_by_username.return_value = None
        service = AuthService()

        service.register("newbie", "Str0ng!pass", "Str0ng!pass")

        patched_collaborators["hash_password"].assert_called_once_with("Str0ng!pass")

    def test_repo_create_called_with_username_hash_and_time(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """应将 (username, hashed_password, current_time) 传给 repo.create"""
        mock_user_repo.find_by_username.return_value = None
        service = AuthService()

        service.register("newbie", "Str0ng!pass", "Str0ng!pass")

        mock_user_repo.create.assert_called_once()
        call_args = mock_user_repo.create.call_args[0]
        assert call_args[0] == "newbie"
        assert call_args[1] == "hashed-pw"
        # create_time 形如 'YYYY-MM-DD'
        assert len(call_args[2]) == 10
        assert call_args[2][4] == "-" and call_args[2][7] == "-"

    def test_strength_check_skipped_when_field_missing(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """字段缺失时应在校验顺序中早返回，不触发强度检查"""
        service = AuthService()

        service.register("", "abc", "abc")

        patched_collaborators["check_password_strength"].assert_not_called()

    def test_find_by_username_called_with_input_username(
        self, mock_user_repo, patched_collaborators, patched_admin_users
    ):
        """应使用入参 username 查重"""
        mock_user_repo.find_by_username.return_value = None
        service = AuthService()

        service.register("newbie", "Str0ng!pass", "Str0ng!pass")

        mock_user_repo.find_by_username.assert_called_once_with("newbie")
