# tests/test_collaboration.py
"""
TDD: 团队协作功能 - 多角色权限、数据分享、操作日志、评论批注
"""

import pytest

from services.collaboration_service import (
    Annotation,
    AnnotationService,
    OperationLog,
    OperationLogger,
    Permission,
    Role,
    RoleManager,
    ShareRecord,
    ShareService,
)

# --- RoleManager ---


def test_role_manager_has_default_roles():
    rm = RoleManager()
    roles = rm.list_roles()
    assert "admin" in roles
    assert "analyst" in roles
    assert "viewer" in roles


def test_admin_has_all_permissions():
    rm = RoleManager()
    admin = rm.get_role("admin")
    assert admin.has_permission(Permission.READ)
    assert admin.has_permission(Permission.WRITE)
    assert admin.has_permission(Permission.DELETE)
    assert admin.has_permission(Permission.MANAGE_USERS)


def test_viewer_has_only_read():
    rm = RoleManager()
    viewer = rm.get_role("viewer")
    assert viewer.has_permission(Permission.READ)
    assert not viewer.has_permission(Permission.WRITE)
    assert not viewer.has_permission(Permission.DELETE)
    assert not viewer.has_permission(Permission.MANAGE_USERS)


def test_analyst_has_read_write():
    rm = RoleManager()
    analyst = rm.get_role("analyst")
    assert analyst.has_permission(Permission.READ)
    assert analyst.has_permission(Permission.WRITE)
    assert not analyst.has_permission(Permission.MANAGE_USERS)


def test_role_manager_get_unknown_raises():
    rm = RoleManager()
    with pytest.raises(KeyError):
        rm.get_role("nonexistent_role")


def test_role_manager_register_custom_role():
    rm = RoleManager()
    custom = Role(name="reporter", permissions={Permission.READ})
    rm.register(custom)
    assert "reporter" in rm.list_roles()
    assert rm.get_role("reporter").has_permission(Permission.READ)
    assert not rm.get_role("reporter").has_permission(Permission.WRITE)


# --- ShareService ---


def test_share_service_create_share_returns_record():
    svc = ShareService()
    record = svc.create_share(
        resource_type="report",
        resource_id="rpt001",
        owner_id="user1",
        share_to=["user2", "user3"],
        permission="read",
    )
    assert isinstance(record, ShareRecord)
    assert record.resource_id == "rpt001"
    assert record.owner_id == "user1"
    assert "user2" in record.share_to


def test_share_service_get_shares_for_user():
    svc = ShareService()
    svc.create_share("report", "rpt001", "user1", ["user2"], "read")
    svc.create_share("report", "rpt002", "user1", ["user2", "user3"], "write")
    shares = svc.get_shares_for_user("user2")
    assert len(shares) == 2


def test_share_service_revoke_share():
    svc = ShareService()
    record = svc.create_share("report", "rpt001", "user1", ["user2"], "read")
    svc.revoke_share(record.share_id)
    shares = svc.get_shares_for_user("user2")
    assert len(shares) == 0


def test_share_service_check_access():
    svc = ShareService()
    svc.create_share("report", "rpt001", "user1", ["user2"], "read")
    assert svc.check_access("user2", "report", "rpt001")
    assert not svc.check_access("user3", "report", "rpt001")


# --- OperationLogger ---


def test_operation_logger_log_returns_entry():
    logger = OperationLogger()
    entry = logger.log(
        user_id="user1",
        action="view_report",
        resource_type="report",
        resource_id="rpt001",
    )
    assert isinstance(entry, OperationLog)
    assert entry.user_id == "user1"
    assert entry.action == "view_report"


def test_operation_logger_get_logs_by_user():
    logger = OperationLogger()
    logger.log("user1", "view_report", "report", "rpt001")
    logger.log("user1", "edit_report", "report", "rpt001")
    logger.log("user2", "view_report", "report", "rpt002")
    logs = logger.get_logs(user_id="user1")
    assert len(logs) == 2


def test_operation_logger_get_logs_by_resource():
    logger = OperationLogger()
    logger.log("user1", "view", "report", "rpt001")
    logger.log("user2", "view", "report", "rpt001")
    logger.log("user1", "view", "report", "rpt002")
    logs = logger.get_logs(resource_id="rpt001")
    assert len(logs) == 2


def test_operation_logger_clear():
    logger = OperationLogger()
    logger.log("user1", "view", "report", "rpt001")
    logger.clear()
    assert len(logger.get_logs()) == 0


# --- AnnotationService ---


def test_annotation_service_add_returns_annotation():
    svc = AnnotationService()
    ann = svc.add(
        resource_type="article",
        resource_id="art001",
        user_id="user1",
        content="这篇文章情感分析有误",
        position={"paragraph": 2},
    )
    assert isinstance(ann, Annotation)
    assert ann.resource_id == "art001"
    assert ann.content == "这篇文章情感分析有误"


def test_annotation_service_get_by_resource():
    svc = AnnotationService()
    svc.add("article", "art001", "user1", "批注1", {})
    svc.add("article", "art001", "user2", "批注2", {})
    svc.add("article", "art002", "user1", "批注3", {})
    anns = svc.get_by_resource("article", "art001")
    assert len(anns) == 2


def test_annotation_service_delete():
    svc = AnnotationService()
    ann = svc.add("article", "art001", "user1", "批注", {})
    svc.delete(ann.annotation_id)
    assert len(svc.get_by_resource("article", "art001")) == 0


def test_annotation_service_reply():
    svc = AnnotationService()
    parent = svc.add("article", "art001", "user1", "原始批注", {})
    reply = svc.reply(parent.annotation_id, "user2", "回复批注")
    assert reply.parent_id == parent.annotation_id
